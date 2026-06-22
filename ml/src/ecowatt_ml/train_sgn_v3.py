from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
)
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from .models import SGNDisaggregator
from .refit import (
    APPLIANCE_THRESHOLDS_W,
    REFIT_CHANNELS,
    TARGET_APPLIANCES,
    build_input_features,
    extract_windows,
    load_refit_house,
    sample_balanced_centers,
    uniformly_limit_centers,
    valid_window_centers,
)
from .refit_metadata import (
    APPLIANCE_DISPLAY_NAMES_ES,
    REFIT_HOUSE8_METADATA_SOURCE,
)


DEFAULT_TRAIN_HOUSES = (2, 4, 5, 6, 9, 13, 17, 19, 20)
DEFAULT_VALIDATION_HOUSE = 3
DEFAULT_TEST_HOUSE = 8


def _parse_houses(value: str) -> tuple[int, ...]:
    return tuple(int(item.strip()) for item in value.split(",") if item.strip())


def _collect_training_data(
    refit_root: str | Path,
    houses: tuple[int, ...],
    appliances: tuple[str, ...],
    window_size: int,
    stride: int,
    samples_per_class_house: int,
    thresholds_w: dict[str, float],
    seed: int,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, Any]]:
    rng = np.random.default_rng(seed)
    windows: dict[str, list[np.ndarray]] = {name: [] for name in appliances}
    targets: dict[str, list[np.ndarray]] = {name: [] for name in appliances}
    house_summary: dict[str, Any] = {}

    for house in houses:
        data = load_refit_house(refit_root, house, appliances)
        centers = valid_window_centers(data, window_size, stride)
        summary: dict[str, Any] = {"valid_centers": len(centers)}
        for appliance in appliances:
            selected = sample_balanced_centers(
                centers,
                data.aggregate,
                data.appliance_power[appliance],
                thresholds_w[appliance],
                samples_per_class_house,
                rng,
            )
            windows[appliance].append(
                extract_windows(data.aggregate, selected, window_size)
            )
            targets[appliance].append(
                data.appliance_power[appliance][selected].astype(np.float32)
            )
            summary[appliance] = {
                "samples": len(selected),
                "on_samples": int(
                    np.sum(
                        data.appliance_power[appliance][selected]
                        > thresholds_w[appliance]
                    )
                ),
            }
        house_summary[str(house)] = summary
        del data

    return (
        {name: np.concatenate(values) for name, values in windows.items()},
        {name: np.concatenate(values) for name, values in targets.items()},
        house_summary,
    )


def _collect_evaluation_data(
    refit_root: str | Path,
    house: int,
    appliances: tuple[str, ...],
    window_size: int,
    stride: int,
    maximum_windows: int | None,
) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, Any]]:
    data = load_refit_house(refit_root, house, appliances)
    centers = valid_window_centers(data, window_size, stride)
    centers = uniformly_limit_centers(centers, maximum_windows)
    windows = extract_windows(data.aggregate, centers, window_size)
    targets = {
        appliance: data.appliance_power[appliance][centers].astype(np.float32)
        for appliance in appliances
    }
    metadata = {
        "house": house,
        "windows": len(centers),
        "first_unix": float(data.unix[centers[0]]),
        "last_unix": float(data.unix[centers[-1]]),
        "stride_rows": stride,
        "uniformly_limited": maximum_windows is not None,
    }
    return windows, targets, metadata


def _predict(
    model: nn.Module,
    features: np.ndarray,
    power_scale: float,
    batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    probabilities: list[np.ndarray] = []
    powers: list[np.ndarray] = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(features), batch_size):
            batch = torch.from_numpy(features[start : start + batch_size])
            power, logits, _ = model(batch)
            probabilities.append(torch.sigmoid(logits).cpu().numpy())
            powers.append((power.cpu().numpy() * power_scale))
    return np.concatenate(probabilities), np.concatenate(powers)


def _best_threshold(labels: np.ndarray, probabilities: np.ndarray) -> float:
    best = (float("-inf"), 0.5)
    for threshold in np.linspace(0.05, 0.95, 91):
        predictions = probabilities >= threshold
        score = f1_score(labels, predictions, zero_division=0)
        candidate = (float(score), float(threshold))
        if candidate > best:
            best = candidate
    return best[1]


def _classification_metrics(
    power_truth: np.ndarray,
    power_prediction: np.ndarray,
    probabilities: np.ndarray,
    threshold_w: float,
    probability_threshold: float,
) -> dict[str, float | int]:
    labels = power_truth > threshold_w
    predictions = probabilities >= probability_threshold
    hard_gated_power = np.where(predictions, power_prediction, 0)
    return {
        "support": len(labels),
        "on_support": int(labels.sum()),
        "on_prevalence": float(labels.mean()),
        "accuracy": float(accuracy_score(labels, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "mae_w": float(mean_absolute_error(power_truth, hard_gated_power)),
        "always_off_accuracy": float(accuracy_score(labels, np.zeros_like(labels))),
        "always_off_f1": 0.0,
        "always_off_mae_w": float(
            mean_absolute_error(power_truth, np.zeros_like(power_truth))
        ),
    }


def train(
    refit_root: str | Path,
    output_path: str | Path,
    train_houses: tuple[int, ...] = DEFAULT_TRAIN_HOUSES,
    validation_house: int = DEFAULT_VALIDATION_HOUSE,
    test_house: int = DEFAULT_TEST_HOUSE,
    appliances: tuple[str, ...] = TARGET_APPLIANCES,
    epochs: int = 30,
    batch_size: int = 256,
    window_size: int = 127,
    training_stride: int = 8,
    evaluation_stride: int = 15,
    samples_per_class_house: int = 1_000,
    maximum_evaluation_windows: int = 120_000,
    thresholds_w: dict[str, float] | None = None,
    learning_rate: float = 3e-4,
    seed: int = 42,
) -> dict[str, Any]:
    if validation_house in train_houses or test_house in train_houses:
        raise ValueError("Validation and test houses must be unseen during training.")
    if validation_house == test_house:
        raise ValueError("Validation and test houses must differ.")
    configured = {*train_houses, validation_house, test_house}
    missing = [house for house in configured if house not in REFIT_CHANNELS]
    if missing:
        raise ValueError(f"Missing channel mappings for houses: {missing}")

    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.set_num_threads(max(torch.get_num_threads(), 1))

    thresholds_w = dict(thresholds_w or APPLIANCE_THRESHOLDS_W)
    missing_thresholds = set(appliances) - set(thresholds_w)
    if missing_thresholds:
        raise ValueError(f"Missing thresholds for: {sorted(missing_thresholds)}")

    raw_train, train_targets, training_summary = _collect_training_data(
        refit_root,
        train_houses,
        appliances,
        window_size,
        training_stride,
        samples_per_class_house,
        thresholds_w,
        seed,
    )
    raw_validation, validation_targets, validation_metadata = (
        _collect_evaluation_data(
            refit_root,
            validation_house,
            appliances,
            window_size,
            evaluation_stride,
            maximum_evaluation_windows,
        )
    )
    raw_test, test_targets, test_metadata = _collect_evaluation_data(
        refit_root,
        test_house,
        appliances,
        window_size,
        evaluation_stride,
        maximum_evaluation_windows,
    )

    all_training_windows = np.concatenate(list(raw_train.values()))
    _, feature_mean, feature_std = build_input_features(all_training_windows)
    del all_training_windows
    validation_features, _, _ = build_input_features(
        raw_validation,
        feature_mean,
        feature_std,
    )
    test_features, _, _ = build_input_features(
        raw_test,
        feature_mean,
        feature_std,
    )

    model = SGNDisaggregator(appliances)
    power_scales: dict[str, float] = {}
    probability_thresholds: dict[str, float] = {}
    histories: dict[str, list[dict[str, float]]] = {}
    validation_metrics: dict[str, Any] = {}
    test_metrics: dict[str, Any] = {}

    for appliance_index, appliance in enumerate(appliances):
        appliance_model = model.models[appliance]
        train_features, _, _ = build_input_features(
            raw_train[appliance],
            feature_mean,
            feature_std,
        )
        target_power = train_targets[appliance]
        appliance_threshold = thresholds_w[appliance]
        power_scale = float(
            max(
                np.percentile(
                    target_power[target_power > appliance_threshold],
                    99,
                ),
                1.0,
            )
        )
        power_scales[appliance] = power_scale
        target_normalized = np.clip(target_power / power_scale, 0, 2).astype(
            np.float32
        )
        target_state = (target_power > appliance_threshold).astype(np.float32)

        generator = torch.Generator().manual_seed(seed + appliance_index)
        loader = DataLoader(
            TensorDataset(
                torch.from_numpy(train_features),
                torch.from_numpy(target_normalized),
                torch.from_numpy(target_state),
            ),
            batch_size=batch_size,
            shuffle=True,
            generator=generator,
        )
        optimizer = torch.optim.AdamW(
            appliance_model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4,
        )
        regression_loss = nn.MSELoss()
        state_loss = nn.BCEWithLogitsLoss()
        labels_validation = validation_targets[appliance] > appliance_threshold
        validation_rng = np.random.default_rng(seed + 10_000 + appliance_index)
        validation_positive = np.flatnonzero(labels_validation)
        validation_negative = np.flatnonzero(~labels_validation)
        balanced_validation_indices = np.concatenate(
            (
                validation_rng.choice(
                    validation_positive,
                    size=min(5_000, len(validation_positive)),
                    replace=False,
                ),
                validation_rng.choice(
                    validation_negative,
                    size=min(5_000, len(validation_negative)),
                    replace=False,
                ),
            )
        )

        best_state = deepcopy(appliance_model.state_dict())
        best_f1 = -1.0
        stale_epochs = 0
        history: list[dict[str, float]] = []
        progress = tqdm(
            range(epochs),
            desc=f"Training SGN v3: {appliance}",
        )
        for epoch in progress:
            appliance_model.train()
            epoch_losses: list[float] = []
            for batch_x, batch_power, batch_state in loader:
                optimizer.zero_grad()
                _, state_logits, gated_power = appliance_model(batch_x)
                loss = regression_loss(gated_power, batch_power) + state_loss(
                    state_logits,
                    batch_state,
                )
                loss.backward()
                optimizer.step()
                epoch_losses.append(float(loss.detach()))

            val_probabilities, _ = _predict(
                appliance_model,
                validation_features[balanced_validation_indices],
                power_scale,
                batch_size,
            )
            val_f1 = float(
                f1_score(
                    labels_validation[balanced_validation_indices],
                    val_probabilities >= 0.5,
                    zero_division=0,
                )
            )
            mean_loss = float(np.mean(epoch_losses))
            history.append(
                {"epoch": epoch + 1, "loss": mean_loss, "validation_f1": val_f1}
            )
            progress.set_postfix(loss=f"{mean_loss:.4f}", val_f1=f"{val_f1:.3f}")
            if val_f1 > best_f1 + 1e-4:
                best_f1 = val_f1
                best_state = deepcopy(appliance_model.state_dict())
                stale_epochs = 0
            else:
                stale_epochs += 1
                if stale_epochs >= 6:
                    break

        appliance_model.load_state_dict(best_state)
        histories[appliance] = history
        validation_probabilities, validation_power = _predict(
            appliance_model,
            validation_features,
            power_scale,
            batch_size,
        )
        probability_threshold = _best_threshold(
            labels_validation,
            validation_probabilities,
        )
        probability_thresholds[appliance] = probability_threshold
        validation_metrics[appliance] = _classification_metrics(
            validation_targets[appliance],
            validation_power,
            validation_probabilities,
            appliance_threshold,
            probability_threshold,
        )

        test_probabilities, test_power = _predict(
            appliance_model,
            test_features,
            power_scale,
            batch_size,
        )
        test_metrics[appliance] = _classification_metrics(
            test_targets[appliance],
            test_power,
            test_probabilities,
            appliance_threshold,
            probability_threshold,
        )

        del train_features

    macro_f1 = float(np.mean([item["f1"] for item in test_metrics.values()]))
    macro_balanced_accuracy = float(
        np.mean([item["balanced_accuracy"] for item in test_metrics.values()])
    )
    mean_accuracy = float(
        np.mean([item["accuracy"] for item in test_metrics.values()])
    )
    mean_mae = float(np.mean([item["mae_w"] for item in test_metrics.values()]))
    metrics: dict[str, Any] = {
        "model": Path(output_path).stem,
        "version": "sgn_v3",
        "architecture": "subtask_gated_sequence_to_point",
        "source": {
            "dataset": "REFIT Electrical Load Measurements (Cleaned)",
            "dataset_doi": "10.15129/9ab14b0e-19ac-4279-938f-27f643078cec",
            "sgn_paper": "Shin et al. (2018), Subtask Gated Networks for NILM",
            "sgn_paper_url": "https://arxiv.org/abs/1811.06692",
        },
        "appliances": list(appliances),
        "appliance_display_names_es": {
            appliance: APPLIANCE_DISPLAY_NAMES_ES[appliance]
            for appliance in appliances
        },
        "appliance_metadata_source": REFIT_HOUSE8_METADATA_SOURCE,
        "train_houses": list(train_houses),
        "validation_house": validation_house,
        "test_house": test_house,
        "split_strategy": "house_holdout",
        "test_house_seen_during_training": False,
        "epochs_max": epochs,
        "epochs_trained": {
            appliance: len(histories[appliance]) for appliance in appliances
        },
        "batch_size": batch_size,
        "window_size": window_size,
        "training_stride": training_stride,
        "evaluation_stride": evaluation_stride,
        "thresholds_w": thresholds_w,
        "probability_thresholds": probability_thresholds,
        "power_scales": power_scales,
        "training_summary": training_summary,
        "validation_sampling": validation_metadata,
        "test_sampling": test_metadata,
        "validation": validation_metrics,
        "test": test_metrics,
        "accuracy": mean_accuracy,
        "macro_f1": macro_f1,
        "macro_balanced_accuracy": macro_balanced_accuracy,
        "mean_mae_w": mean_mae,
        "rnf_02_passed": macro_f1 >= 0.77 and macro_balanced_accuracy >= 0.80,
        "primary_metric": "macro_f1_on_unseen_house",
        "seed": seed,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "version": "sgn_v3",
            "state_dict": model.state_dict(),
            "appliances": list(appliances),
            "appliance_display_names_es": {
                appliance: APPLIANCE_DISPLAY_NAMES_ES[appliance]
                for appliance in appliances
            },
            "input_channels": 3,
            "window_size": window_size,
            "thresholds_w": thresholds_w,
            "probability_thresholds": probability_thresholds,
            "power_scales": power_scales,
            "metrics": {
                "accuracy": mean_accuracy,
                "macro_f1": macro_f1,
                "macro_balanced_accuracy": macro_balanced_accuracy,
                "mean_mae_w": mean_mae,
            },
        },
        output,
    )
    joblib.dump(
        {
            "feature_mean": feature_mean,
            "feature_std": feature_std,
            "probability_thresholds": probability_thresholds,
            "power_scales": power_scales,
        },
        output.with_suffix(".joblib"),
    )
    output.with_name(f"{output.stem}_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refit-root", required=True)
    parser.add_argument("--output", default="models/sgn_v3.pt")
    parser.add_argument(
        "--train-houses",
        default=",".join(str(value) for value in DEFAULT_TRAIN_HOUSES),
    )
    parser.add_argument("--validation-house", type=int, default=3)
    parser.add_argument("--test-house", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--window-size", type=int, default=127)
    parser.add_argument("--training-stride", type=int, default=8)
    parser.add_argument("--evaluation-stride", type=int, default=15)
    parser.add_argument("--samples-per-class-house", type=int, default=1_000)
    parser.add_argument("--maximum-evaluation-windows", type=int, default=120_000)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metrics = train(
        refit_root=args.refit_root,
        output_path=args.output,
        train_houses=_parse_houses(args.train_houses),
        validation_house=args.validation_house,
        test_house=args.test_house,
        epochs=args.epochs,
        batch_size=args.batch_size,
        window_size=args.window_size,
        training_stride=args.training_stride,
        evaluation_stride=args.evaluation_stride,
        samples_per_class_house=args.samples_per_class_house,
        maximum_evaluation_windows=args.maximum_evaluation_windows,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
