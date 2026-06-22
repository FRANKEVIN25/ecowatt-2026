from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from .data import save_measurements
from .refit_metadata import REFIT_HOUSE8_APPLIANCES


APPLIANCE_COLUMNS = [f"Appliance{i}" for i in range(1, 10)]
DEFAULT_APPLIANCE_NAMES = REFIT_HOUSE8_APPLIANCES


def convert_refit_house(
    input_path: str | Path,
    output_path: str | Path,
    samples: int = 50_000,
    every_n_rows: int = 1,
    voltage_rms: float = 230.0,
    assumed_power_factor: float = 0.95,
    activation_threshold_w: float = 10.0,
    tariff_soles_kwh: float = 0.60,
) -> pd.DataFrame:
    if samples <= 0:
        raise ValueError("samples must be greater than zero.")
    if every_n_rows <= 0:
        raise ValueError("every_n_rows must be greater than zero.")

    input_file = Path(input_path)
    chunks: list[pd.DataFrame] = []
    remaining = samples
    previous_unix: float | None = None
    energy_kwh = 0.0
    source_rows_seen = 0

    for chunk in pd.read_csv(input_file, chunksize=100_000):
        if "Issues" in chunk.columns:
            chunk = chunk[chunk["Issues"].fillna(0).astype(float) == 0]
        filtered_rows = len(chunk)
        if every_n_rows > 1:
            positions = np.arange(source_rows_seen, source_rows_seen + len(chunk))
            chunk = chunk[(positions % every_n_rows) == 0]
        source_rows_seen += filtered_rows
        if chunk.empty:
            continue

        if len(chunk) > remaining:
            chunk = chunk.head(remaining)

        aggregate = chunk["Aggregate"].astype(float).clip(lower=0)
        appliance_power = chunk[APPLIANCE_COLUMNS].astype(float).clip(lower=0)
        max_appliance = appliance_power.idxmax(axis=1)
        max_power = appliance_power.max(axis=1)
        labels = max_appliance.map(DEFAULT_APPLIANCE_NAMES).where(
            max_power >= activation_threshold_w,
            "standby",
        )

        unix_values = chunk["Unix"].astype(float)
        deltas = unix_values.diff()
        if previous_unix is not None and not unix_values.empty:
            deltas.iloc[0] = max(unix_values.iloc[0] - previous_unix, 0)
        deltas = deltas.fillna(8).clip(lower=1, upper=900)
        previous_unix = float(unix_values.iloc[-1])
        energy_kwh_series = (aggregate / 1000 * deltas / 3600).cumsum() + energy_kwh
        energy_kwh = float(energy_kwh_series.iloc[-1])

        power_factor = np.full(len(chunk), assumed_power_factor)
        apparent_power = aggregate / power_factor
        current_rms = apparent_power / voltage_rms
        reactive_power = np.sqrt(np.maximum(apparent_power**2 - aggregate**2, 0))
        phase_angle = np.degrees(np.arccos(np.clip(power_factor, -1, 1)))

        converted = pd.DataFrame(
            {
                "timestamp": pd.to_datetime(chunk["Time"], utc=True).dt.strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
                "voltage_rms": round(voltage_rms, 3),
                "current_rms": current_rms.round(4),
                "phase_angle": round(float(phase_angle[0]), 3),
                "active_power_w": aggregate.round(3),
                "reactive_power_var": reactive_power.round(3),
                "apparent_power_va": apparent_power.round(3),
                "power_factor": round(assumed_power_factor, 4),
                "energy_kwh": energy_kwh_series.round(8),
                "appliance_label": labels,
                "tariff_soles_kwh": tariff_soles_kwh,
            }
        )
        chunks.append(converted)
        remaining -= len(converted)
        if remaining <= 0:
            break

    if not chunks:
        raise ValueError("No REFIT rows were converted.")

    data = pd.concat(chunks, ignore_index=True)
    save_measurements(data, output_path)
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="data/refit_house8_training.csv")
    parser.add_argument("--samples", type=int, default=50_000)
    parser.add_argument("--every-n-rows", type=int, default=1)
    parser.add_argument("--voltage-rms", type=float, default=230.0)
    parser.add_argument("--power-factor", type=float, default=0.95)
    parser.add_argument("--activation-threshold-w", type=float, default=10.0)
    parser.add_argument("--tariff-soles-kwh", type=float, default=0.60)
    args = parser.parse_args()

    data = convert_refit_house(
        input_path=args.input,
        output_path=args.output,
        samples=args.samples,
        every_n_rows=args.every_n_rows,
        voltage_rms=args.voltage_rms,
        assumed_power_factor=args.power_factor,
        activation_threshold_w=args.activation_threshold_w,
        tariff_soles_kwh=args.tariff_soles_kwh,
    )
    print(f"Converted {len(data)} REFIT rows to {args.output}")
    print(data["appliance_label"].value_counts().to_dict())


if __name__ == "__main__":
    main()
