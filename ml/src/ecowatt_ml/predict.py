from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import torch

from .config import FEATURE_COLUMNS, WindowConfig
from .data import load_measurements
from .models import SGNClassifier


def predict_appliance(input_path: str | Path, model_path: str | Path) -> dict[str, object]:
    checkpoint = torch.load(model_path, map_location="cpu")
    sidecar = joblib.load(Path(model_path).with_suffix(".joblib"))
    data = load_measurements(input_path)
    window_size = int(checkpoint["window_size"])
    latest = data.tail(window_size)
    if len(latest) < window_size:
        raise ValueError(f"Need at least {window_size} rows for SGN prediction.")

    scaler = sidecar["scaler"]
    features = scaler.transform(latest[FEATURE_COLUMNS].astype(float))
    batch = torch.from_numpy(features.astype(np.float32)).unsqueeze(0)

    model = SGNClassifier(
        input_features=int(checkpoint["input_features"]),
        classes=len(checkpoint["classes"]),
    )
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    with torch.no_grad():
        probabilities = torch.softmax(model(batch), dim=1).squeeze(0)
        confidence, index = torch.max(probabilities, dim=0)

    return {
        "detected_appliance": checkpoint["classes"][int(index)],
        "confidence": round(float(confidence), 4),
    }


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
    args = parser.parse_args()

    result = {
        **predict_appliance(args.input, args.sgn_model),
        **predict_monthly_cost(args.input, args.cost_model),
    }
    print(result)


if __name__ == "__main__":
    main()
