from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from .config import FEATURE_COLUMNS, WindowConfig
from .data import load_measurements
from .models import SGNClassifier
from .preprocess import split_train_validation


def train(
    input_path: str | Path,
    output_path: str | Path,
    epochs: int,
    batch_size: int,
    window_size: int,
    stride: int,
    validation_ratio: float = 0.2,
    seed: int = 42,
) -> dict[str, Any]:
    np.random.seed(seed)
    torch.manual_seed(seed)

    data = load_measurements(input_path)
    config = WindowConfig(size=window_size, stride=stride)
    (
        x_train,
        x_val,
        y_train,
        y_val,
        encoder,
        scaler,
        split_metadata,
    ) = split_train_validation(
        data,
        config,
        validation_ratio=validation_ratio,
    )

    model = SGNClassifier(input_features=len(FEATURE_COLUMNS), classes=len(encoder.classes_))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    class_counts = np.bincount(y_train, minlength=len(encoder.classes_)).clip(min=1)
    class_weights = class_counts.sum() / (len(class_counts) * class_counts)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(class_weights, dtype=torch.float32))

    train_loader = DataLoader(
        TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train)),
        batch_size=batch_size,
        shuffle=True,
    )

    model.train()
    for _ in tqdm(range(epochs), desc="Training SGN"):
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()

    model.eval()
    with torch.no_grad():
        logits = model(torch.from_numpy(x_val))
        predictions = logits.argmax(dim=1).numpy()

    per_class_support = {
        class_name: int(np.sum(y_val == class_index))
        for class_index, class_name in enumerate(encoder.classes_)
    }
    accuracy = float(accuracy_score(y_val, predictions))
    macro_f1 = float(
        f1_score(y_val, predictions, average="macro", zero_division=0)
    )
    metrics: dict[str, Any] = {
        "model": Path(output_path).stem,
        "training_data": Path(input_path).as_posix(),
        "data_type": "refit_real" if "refit" in Path(input_path).name.lower() else "unknown",
        "samples": len(data),
        "epochs": epochs,
        "batch_size": batch_size,
        "window_size": window_size,
        "stride": stride,
        "seed": seed,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "macro_f1_all_classes": float(
            f1_score(
                y_val,
                predictions,
                labels=list(range(len(encoder.classes_))),
                average="macro",
                zero_division=0,
            )
        ),
        "rnf_02_passed": accuracy >= 0.80,
        "classes": encoder.classes_.tolist(),
        "validation_support": per_class_support,
        "split": split_metadata,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "input_features": len(FEATURE_COLUMNS),
            "classes": encoder.classes_.tolist(),
            "window_size": window_size,
            "stride": stride,
            "metrics": {
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
            },
        },
        output,
    )
    joblib.dump({"label_encoder": encoder, "scaler": scaler}, output.with_suffix(".joblib"))
    metrics_path = output.with_name(f"{output.stem}_metrics.json")
    metrics_path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_measurements.csv")
    parser.add_argument("--output", default="models/sgn_mock.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--window-size", type=int, default=60)
    parser.add_argument("--stride", type=int, default=15)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    metrics = train(
        input_path=args.input,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        window_size=args.window_size,
        stride=args.stride,
        validation_ratio=args.validation_ratio,
        seed=args.seed,
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
