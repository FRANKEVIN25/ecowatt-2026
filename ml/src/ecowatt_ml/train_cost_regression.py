from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .config import ENERGY_COLUMN, TARIFF_COLUMN
from .data import load_measurements


def train(input_path: str | Path, output_path: str | Path) -> dict[str, float]:
    data = load_measurements(input_path)
    elapsed_hours = (
        data["timestamp"] - data["timestamp"].min()
    ).dt.total_seconds().clip(lower=1) / 3600
    avg_power_kw = data["active_power_w"].expanding().mean() / 1000
    projected_monthly_kwh = avg_power_kw * 24 * 30
    target_cost = projected_monthly_kwh * data[TARIFF_COLUMN]

    features = np.column_stack(
        [
            data[ENERGY_COLUMN].to_numpy(),
            elapsed_hours.to_numpy(),
            data["active_power_w"].rolling(60, min_periods=1).mean().to_numpy(),
            data[TARIFF_COLUMN].to_numpy(),
        ]
    )

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target_cost.to_numpy(),
        test_size=0.2,
        random_state=42,
    )
    model = LinearRegression()
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    metrics = {
        "mae_soles": float(mean_absolute_error(y_test, predictions)),
        "r2": float(r2_score(y_test, predictions)),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "metrics": metrics}, output)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/sample_measurements.csv")
    parser.add_argument("--output", default="models/cost_regression.joblib")
    args = parser.parse_args()

    metrics = train(args.input, args.output)
    print(metrics)


if __name__ == "__main__":
    main()
