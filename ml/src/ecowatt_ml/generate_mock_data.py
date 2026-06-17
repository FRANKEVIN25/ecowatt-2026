from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd

from .data import save_measurements


PROFILES = {
    "standby": (8, 0.05, 0.70),
    "foco_25w": (25, 0.12, 0.95),
    "foco_100w": (100, 0.46, 0.96),
    "refrigeradora": (150, 0.85, 0.82),
    "hervidor": (1200, 5.45, 0.99),
}


def generate_mock_measurements(seconds: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = datetime.now(UTC).replace(microsecond=0)
    labels = list(PROFILES)
    rows = []
    energy_kwh = 0.0

    for index in range(seconds):
        if index % 300 == 0:
            current_label = str(rng.choice(labels, p=[0.35, 0.20, 0.18, 0.20, 0.07]))

        base_power, base_current, base_pf = PROFILES[current_label]
        voltage = 220 + rng.normal(0, 1.8)
        active_power = max(0, base_power + rng.normal(0, base_power * 0.05 + 1))
        current = max(0, base_current + rng.normal(0, 0.03))
        power_factor = float(np.clip(base_pf + rng.normal(0, 0.015), 0.1, 1.0))
        apparent_power = voltage * current
        reactive_power = max(0, np.sqrt(max(apparent_power**2 - active_power**2, 0)))
        phase_angle = float(np.degrees(np.arccos(np.clip(power_factor, -1, 1))))
        energy_kwh += active_power / 1000 / 3600

        rows.append(
            {
                "timestamp": (start + timedelta(seconds=index)).isoformat(),
                "voltage_rms": round(voltage, 3),
                "current_rms": round(current, 4),
                "phase_angle": round(phase_angle, 3),
                "active_power_w": round(active_power, 3),
                "reactive_power_var": round(reactive_power, 3),
                "apparent_power_va": round(apparent_power, 3),
                "power_factor": round(power_factor, 4),
                "energy_kwh": round(energy_kwh, 8),
                "appliance_label": current_label,
                "tariff_soles_kwh": 0.6,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/sample_measurements.csv")
    parser.add_argument("--seconds", type=int, default=3600)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data = generate_mock_measurements(seconds=args.seconds, seed=args.seed)
    save_measurements(data, args.output)
    print(f"Saved {len(data)} rows to {args.output}")


if __name__ == "__main__":
    main()
