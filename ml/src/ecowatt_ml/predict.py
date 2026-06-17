from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from .config import FEATURE_COLUMNS, WindowConfig
from .data import load_measurements
from .models import SGNClassifier


def _load_sgn(model_path: str | Path) -> tuple[SGNClassifier, dict, dict]:
    checkpoint = torch.load(model_path, map_location="cpu")
    sidecar = joblib.load(Path(model_path).with_suffix(".joblib"))
    model = SGNClassifier(
        input_features=int(checkpoint["input_features"]),
        classes=len(checkpoint["classes"]),
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model, checkpoint, sidecar


def predict_appliance_from_window(
    feature_rows: list[list[float]] | np.ndarray,
    model_path: str | Path,
) -> dict[str, object]:
    model, checkpoint, sidecar = _load_sgn(model_path)
    features = np.asarray(feature_rows, dtype=np.float32)
    if features.ndim != 2 or features.shape[1] != len(FEATURE_COLUMNS):
        raise ValueError(
            "feature_rows must have shape [window, 7] for "
            "[V, I, phi, P, Q, S, fp]."
        )

    scaler = sidecar["scaler"]
    feature_frame = pd.DataFrame(features, columns=FEATURE_COLUMNS)
    scaled = scaler.transform(feature_frame)
    batch = torch.from_numpy(scaled.astype(np.float32)).unsqueeze(0)

    with torch.no_grad():
        probabilities = torch.softmax(model(batch), dim=1).squeeze(0)
        confidence, index = torch.max(probabilities, dim=0)

    return {
        "detected_appliance": checkpoint["classes"][int(index)],
        "confidence": round(float(confidence), 4),
    }


def predict_appliance_from_features(
    features: list[float] | np.ndarray,
    model_path: str | Path,
) -> dict[str, object]:
    checkpoint = torch.load(model_path, map_location="cpu")
    values = np.asarray(features, dtype=np.float32)
    if values.shape != (len(FEATURE_COLUMNS),):
        raise ValueError("features must be [V, I, phi, P, Q, S, fp].")
    window = np.tile(values, (int(checkpoint["window_size"]), 1))
    return predict_appliance_from_window(window, model_path)


def predict_appliance(input_path: str | Path, model_path: str | Path) -> dict[str, object]:
    _, checkpoint, _ = _load_sgn(model_path)
    data = load_measurements(input_path)
    window_size = int(checkpoint["window_size"])
    latest = data.tail(window_size)
    if len(latest) < window_size:
        raise ValueError(f"Need at least {window_size} rows for SGN prediction.")

    return predict_appliance_from_window(
        latest[FEATURE_COLUMNS].astype(float).to_numpy(),
        model_path,
    )


def predict_monthly_cost(input_path: str | Path, model_path: str | Path) -> dict[str, float]:
    bundle = joblib.load(model_path)
    data = load_measurements(input_path)
    latest = data.iloc[-1]
    elapsed_hours = max(
        (data["timestamp"].max() - data["timestamp"].min()).total_seconds() / 3600,
        1 / 3600,
    )
    features = np.asarray(
        [
            [
                latest["energy_kwh"],
                elapsed_hours,
                data["active_power_w"].tail(60).mean(),
                latest["tariff_soles_kwh"],
            ]
        ]
    )
    cost = float(bundle["model"].predict(features)[0])
    return {"predicted_monthly_cost_soles": round(max(cost, 0), 2)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_measurements.csv")
    parser.add_argument("--sgn-model", default="models/sgn_mock.pt")
    parser.add_argument("--cost-model", default="models/cost_regression.joblib")
    parser.add_argument(
        "--features",
        help="Comma-separated [V,I,phi,P,Q,S,fp] for direct SGN prediction.",
    )
    args = parser.parse_args()

    if args.features:
        features = [float(value.strip()) for value in args.features.split(",")]
        print(predict_appliance_from_features(features, args.sgn_model))
        return

    result = {
        **predict_appliance(args.input, args.sgn_model),
        **predict_monthly_cost(args.input, args.cost_model),
    }
    print(result)


if __name__ == "__main__":
    main()
