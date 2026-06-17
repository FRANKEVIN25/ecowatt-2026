from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import torch
from sklearn.metrics import accuracy_score, f1_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from .config import FEATURE_COLUMNS, WindowConfig
from .data import load_measurements
from .models import SGNClassifier
from .preprocess import build_windows, split_train_validation


def train(
    input_path: str | Path,
    output_path: str | Path,
    epochs: int,
    batch_size: int,
    window_size: int,
    stride: int,
) -> dict[str, float]:
    data = load_measurements(input_path)
    windows, labels, encoder, scaler = build_windows(
        data,
        WindowConfig(size=window_size, stride=stride),
    )
    x_train, x_val, y_train, y_val = split_train_validation(windows, labels)

    model = SGNClassifier(input_features=len(FEATURE_COLUMNS), classes=len(encoder.classes_))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

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

    metrics = {
        "accuracy": float(accuracy_score(y_val, predictions)),
        "macro_f1": float(f1_score(y_val, predictions, average="macro")),
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
            "metrics": metrics,
        },
        output,
    )
    joblib.dump({"label_encoder": encoder, "scaler": scaler}, output.with_suffix(".joblib"))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_measurements.csv")
    parser.add_argument("--output", default="models/sgn_mock.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--window-size", type=int, default=60)
    parser.add_argument("--stride", type=int, default=15)
    args = parser.parse_args()

    metrics = train(
        input_path=args.input,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        window_size=args.window_size,
        stride=args.stride,
    )
    print(metrics)


if __name__ == "__main__":
    main()
