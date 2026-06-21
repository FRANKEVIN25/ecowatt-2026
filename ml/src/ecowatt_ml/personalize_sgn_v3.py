from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from sklearn.metrics import f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from .models import SGNDisaggregator
from .refit import (
    build_input_features,
    extract_windows,
    load_refit_house,
    sample_balanced_centers,
    uniformly_limit_centers,
    valid_window_centers,
)
from .train_sgn_v3 import (
    _best_threshold,
    _classification_metrics,
    _predict,
)


def _segment_centers(
    centers: np.ndarray,
    start: int,
    end: int,
    half_window: int,
) -> np.ndarray:
    return centers[
        (centers >= start + half_window)
        & (centers < end - half_window)
    ]


def personalize(
    base_model_path: str | Path,
    refit_root: str | Path,
    output_path: str | Path,
    house: int = 8,
    train_ratio: float = 0.6,
    validation_ratio: float = 0.2,
    epochs: int = 15,
    batch_size: int = 256,
    training_stride: int = 8,
    evaluation_stride: int = 15,
    samples_per_class: int = 2_000,
    maximum_evaluation_windows: int | None = None,
    learning_rate: float = 1e-4,
    seed: int = 42,
) -> dict[str, Any]:
    if not 0 < train_ratio < 1:
        raise ValueError("train_ratio must be between zero and one.")
    if not 0 < validation_ratio < 1 - train_ratio:
        raise ValueError("validation_ratio leaves no chronological test segment.")

    base_path = Path(base_model_path)
    checkpoint = torch.load(base_path, map_location="cpu")
    if checkpoint.get("version") != "sgn_v3":
        raise ValueError("Personalization requires an SGN v3 checkpoint.")
    sidecar = joblib.load(base_path.with_suffix(".joblib"))
    appliances = tuple(checkpoint["appliances"])
    window_size = int(checkpoint["window_size"])
    half_window = window_size // 2
    thresholds_w = dict(checkpoint["thresholds_w"])
    feature_mean = np.asarray(sidecar["feature_mean"], dtype=np.float32)
    feature_std = np.asarray(sidecar["feature_std"], dtype=np.float32)
    power_scales = dict(checkpoint["power_scales"])

    np.random.seed(seed)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)

    data = load_refit_house(refit_root, house, appliances)
    train_end = int(len(data.aggregate) * train_ratio)
    validation_end = int(
        len(data.aggregate) * (train_ratio + validation_ratio)
    )

    training_centers = _segment_centers(
        valid_window_centers(data, window_size, training_stride),
        0,
        train_end,
        half_window,
    )
    evaluation_centers = valid_window_centers(
        data,
        window_size,
        evaluation_stride,
    )
    validation_centers = uniformly_limit_centers(
        _segment_centers(
            evaluation_centers,
            train_end,
            validation_end,
            half_window,
        ),
        maximum_evaluation_windows,
    )
    test_centers = uniformly_limit_centers(
        _segment_centers(
            evaluation_centers,
            validation_end,
            len(data.aggregate),
            half_window,
        ),
        maximum_evaluation_windows,
    )
    if not len(training_centers) or not len(validation_centers) or not len(
        test_centers
    ):
        raise ValueError("The chronological personalization split is empty.")

    raw_validation = extract_windows(
        data.aggregate,
        validation_centers,
        window_size,
    )
    raw_test = extract_windows(data.aggregate, test_centers, window_size)
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

    model = SGNDisaggregator(
        appliances,
        input_channels=int(checkpoint["input_channels"]),
    )
    model.load_state_dict(checkpoint["state_dict"])
    histories: dict[str, list[dict[str, float]]] = {}
    thresholds: dict[str, float] = {}
    validation_metrics: dict[str, Any] = {}
    test_metrics: dict[str, Any] = {}
    training_summary: dict[str, Any] = {}

    for appliance_index, appliance in enumerate(appliances):
        selected = sample_balanced_centers(
            training_centers,
            data.aggregate,
            data.appliance_power[appliance],
            thresholds_w[appliance],
            samples_per_class,
            rng,
        )
        raw_training = extract_windows(
            data.aggregate,
            selected,
            window_size,
        )
        training_features, _, _ = build_input_features(
            raw_training,
            feature_mean,
            feature_std,
        )
        target_power = data.appliance_power[appliance][selected].astype(
            np.float32
        )
        appliance_threshold = thresholds_w[appliance]
        target_state = (target_power > appliance_threshold).astype(np.float32)
        target_normalized = np.clip(
            target_power / power_scales[appliance],
            0,
            2,
        ).astype(np.float32)
        training_summary[appliance] = {
            "samples": len(selected),
            "on_samples": int(target_state.sum()),
        }

        loader = DataLoader(
            TensorDataset(
                torch.from_numpy(training_features),
                torch.from_numpy(target_normalized),
                torch.from_numpy(target_state),
            ),
            batch_size=batch_size,
            shuffle=True,
            generator=torch.Generator().manual_seed(seed + appliance_index),
        )
        appliance_model = model.models[appliance]
        optimizer = torch.optim.AdamW(
            appliance_model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4,
        )
        regression_loss = nn.MSELoss()
        state_loss = nn.BCEWithLogitsLoss()
        validation_truth = (
            data.appliance_power[appliance][validation_centers]
            > appliance_threshold
        )
        positive = np.flatnonzero(validation_truth)
        negative = np.flatnonzero(~validation_truth)
        early_stop_indices = np.concatenate(
            (
                rng.choice(
                    positive,
                    size=min(5_000, len(positive)),
                    replace=False,
                ),
                rng.choice(
                    negative,
                    size=min(5_000, len(negative)),
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
            desc=f"Personalizing SGN v3: {appliance}",
        )
        for epoch in progress:
            appliance_model.train()
            losses: list[float] = []
            for batch_x, batch_power, batch_state in loader:
                optimizer.zero_grad()
                _, state_logits, gated_power = appliance_model(batch_x)
                loss = regression_loss(gated_power, batch_power) + state_loss(
                    state_logits,
                    batch_state,
                )
                loss.backward()
                optimizer.step()
                losses.append(float(loss.detach()))

            probabilities, _ = _predict(
                appliance_model,
                validation_features[early_stop_indices],
                power_scales[appliance],
                batch_size,
            )
            validation_f1 = float(
                f1_score(
                    validation_truth[early_stop_indices],
                    probabilities >= 0.5,
                    zero_division=0,
                )
            )
            mean_loss = float(np.mean(losses))
            history.append(
                {
                    "epoch": epoch + 1,
                    "loss": mean_loss,
                    "validation_f1": validation_f1,
                }
            )
            progress.set_postfix(
                loss=f"{mean_loss:.4f}",
                val_f1=f"{validation_f1:.3f}",
            )
            if validation_f1 > best_f1 + 1e-4:
                best_f1 = validation_f1
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
            power_scales[appliance],
            batch_size,
        )
        probability_threshold = _best_threshold(
            validation_truth,
            validation_probabilities,
        )
        thresholds[appliance] = probability_threshold
        validation_metrics[appliance] = _classification_metrics(
            data.appliance_power[appliance][validation_centers],
            validation_power,
            validation_probabilities,
            appliance_threshold,
            probability_threshold,
        )
        test_probabilities, test_power = _predict(
            appliance_model,
            test_features,
            power_scales[appliance],
            batch_size,
        )
        test_metrics[appliance] = _classification_metrics(
            data.appliance_power[appliance][test_centers],
            test_power,
            test_probabilities,
            appliance_threshold,
            probability_threshold,
        )

    macro_f1 = float(np.mean([item["f1"] for item in test_metrics.values()]))
    macro_balanced_accuracy = float(
        np.mean([item["balanced_accuracy"] for item in test_metrics.values()])
    )
    accuracy = float(
        np.mean([item["accuracy"] for item in test_metrics.values()])
    )
    mean_mae = float(np.mean([item["mae_w"] for item in test_metrics.values()]))
    base_metrics_path = base_path.with_name(f"{base_path.stem}_metrics.json")
    base_metrics = (
        json.loads(base_metrics_path.read_text(encoding="utf-8"))
        if base_metrics_path.exists()
        else checkpoint.get("metrics", {})
    )
    metrics: dict[str, Any] = {
        "model": Path(output_path).stem,
        "version": "sgn_v3_personalized",
        "base_model": base_path.as_posix(),
        "personalized_house": house,
        "split_strategy": "chronological_60_20_20_with_purged_windows",
        "rows": {
            "total": len(data.aggregate),
            "training_end_exclusive": train_end,
            "validation_end_exclusive": validation_end,
            "training_windows": len(training_centers),
            "validation_windows": len(validation_centers),
            "test_windows": len(test_centers),
            "window_overlap_between_splits": 0,
        },
        "appliances": list(appliances),
        "epochs_max": epochs,
        "epochs_trained": {
            appliance: len(histories[appliance]) for appliance in appliances
        },
        "training_summary": training_summary,
        "probability_thresholds": thresholds,
        "validation": validation_metrics,
        "test": test_metrics,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "macro_balanced_accuracy": macro_balanced_accuracy,
        "mean_mae_w": mean_mae,
        "rnf_02_passed": macro_f1 >= 0.77 and macro_balanced_accuracy >= 0.80,
        "primary_metric": "macro_f1_on_future_chronological_holdout",
        "external_generalization_before_personalization": {
            "accuracy": base_metrics.get("accuracy"),
            "macro_f1": base_metrics.get("macro_f1"),
            "macro_balanced_accuracy": base_metrics.get(
                "macro_balanced_accuracy"
            ),
        },
        "seed": seed,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "version": "sgn_v3",
            "personalized": True,
            "personalized_house": house,
            "state_dict": model.state_dict(),
            "appliances": list(appliances),
            "input_channels": int(checkpoint["input_channels"]),
            "window_size": window_size,
            "thresholds_w": thresholds_w,
            "probability_thresholds": thresholds,
            "power_scales": power_scales,
            "metrics": {
                "accuracy": accuracy,
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
            "probability_thresholds": thresholds,
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
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--refit-root", required=True)
    parser.add_argument("--output", default="models/sgn_v3.pt")
    parser.add_argument("--house", type=int, default=8)
    parser.add_argument("--train-ratio", type=float, default=0.6)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--training-stride", type=int, default=8)
    parser.add_argument("--evaluation-stride", type=int, default=15)
    parser.add_argument("--samples-per-class", type=int, default=2_000)
    parser.add_argument("--maximum-evaluation-windows", type=int)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metrics = personalize(
        base_model_path=args.base_model,
        refit_root=args.refit_root,
        output_path=args.output,
        house=args.house,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        epochs=args.epochs,
        batch_size=args.batch_size,
        training_stride=args.training_stride,
        evaluation_stride=args.evaluation_stride,
        samples_per_class=args.samples_per_class,
        maximum_evaluation_windows=args.maximum_evaluation_windows,
        learning_rate=args.learning_rate,
        seed=args.seed,
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
