from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GroupShuffleSplit


FEATURES = [
    "voltage_rms",
    "current_rms",
    "phase_angle",
    "active_power_w",
    "reactive_power_var",
    "apparent_power_va",
    "power_factor",
    "active_power_delta_w",
    "active_power_rolling_std",
]


def train_demo_benchmark(
    input_path: str | Path,
    output_path: str | Path,
    seed: int = 42,
) -> dict[str, Any]:
    data = pd.read_csv(input_path)
    if set(data["source"].unique()) != {"synthetic_hardware_substitute"}:
        raise ValueError("This trainer only accepts disclosed synthetic demo data.")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.22,
        random_state=seed,
    )
    train_index, test_index = next(
        splitter.split(
            data[FEATURES],
            data["appliance_label"],
            groups=data["session_id"],
        )
    )
    train = data.iloc[train_index]
    test = data.iloc[test_index]
    train_sessions = set(train["session_id"])
    test_sessions = set(test["session_id"])
    overlap = train_sessions & test_sessions
    if overlap:
        raise RuntimeError("Session leakage detected in synthetic benchmark.")

    model = RandomForestClassifier(
        n_estimators=260,
        max_depth=13,
        min_samples_leaf=8,
        max_features=0.75,
        class_weight="balanced_subsample",
        n_jobs=1,
        random_state=seed,
    )
    model.fit(train[FEATURES], train["appliance_label"])
    predictions = model.predict(test[FEATURES])

    labels = sorted(data["appliance_label"].unique())
    accuracy = float(accuracy_score(test["appliance_label"], predictions))
    macro_f1 = float(
        f1_score(test["appliance_label"], predictions, average="macro")
    )
    metrics: dict[str, Any] = {
        "model": Path(output_path).stem,
        "benchmark": "synthetic_hardware_substitute",
        "disclosure": (
            "These metrics describe a controlled simulation. They are not "
            "REFIT metrics and not measurements from EcoWatt hardware."
        ),
        "purpose": "demo_continuity_while_hardware_is_unavailable",
        "rows": len(data),
        "train_rows": len(train),
        "test_rows": len(test),
        "train_sessions": len(train_sessions),
        "test_sessions": len(test_sessions),
        "session_overlap": len(overlap),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "balanced_accuracy": float(
            balanced_accuracy_score(test["appliance_label"], predictions)
        ),
        "labels": labels,
        "classification_report": classification_report(
            test["appliance_label"],
            predictions,
            labels=labels,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(
            test["appliance_label"],
            predictions,
            labels=labels,
        ).tolist(),
        "target_band": {
            "accuracy": [0.82, 0.90],
            "macro_f1": [0.72, 0.82],
        },
        "inside_target_band": (
            0.82 <= accuracy <= 0.90 and 0.72 <= macro_f1 <= 0.82
        ),
        "seed": seed,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "features": FEATURES,
            "labels": labels,
            "source": "synthetic_hardware_substitute",
        },
        output,
        compress=3,
    )
    output.with_name(f"{output.stem}_metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/demo_hardware_simulated.csv")
    parser.add_argument("--output", default="models/demo_nilm_benchmark.joblib")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    print(
        json.dumps(
            train_demo_benchmark(args.input, args.output, args.seed),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
