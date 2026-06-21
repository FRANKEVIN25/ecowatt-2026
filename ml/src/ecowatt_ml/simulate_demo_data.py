from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ApplianceProfile:
    active_power_w: float
    power_std_w: float
    power_factor: float
    reactive_sign: float = 1.0


PROFILES = {
    "standby": ApplianceProfile(8, 5, 0.72),
    # Low-cost CT sensors make low-power resistive loads intentionally hard
    # to separate; these overlapping profiles model that demo constraint.
    "foco_25w": ApplianceProfile(36, 13, 0.98),
    "foco_100w": ApplianceProfile(88, 22, 0.98),
    "refrigeradora": ApplianceProfile(135, 30, 0.72),
    "microondas": ApplianceProfile(1_250, 150, 0.91),
    "hervidor": ApplianceProfile(1_850, 130, 0.99),
    "lavadora": ApplianceProfile(620, 330, 0.70),
}


def _session_signal(
    profile: ApplianceProfile,
    length: int,
    rng: np.random.Generator,
) -> np.ndarray:
    phase = np.linspace(0, rng.uniform(1.5, 4.0) * np.pi, length)
    envelope = 1 + rng.normal(0, 0.025) + 0.04 * np.sin(phase)
    signal = rng.normal(
        profile.active_power_w * envelope,
        profile.power_std_w,
    )
    if profile.active_power_w > 300:
        ramp = np.minimum(np.arange(length) / max(length * 0.08, 1), 1)
        signal *= 0.55 + 0.45 * ramp
    return np.clip(signal, 0, None)


def generate_demo_measurements(
    sessions_per_class: int = 80,
    samples_per_session: int = 90,
    seed: int = 42,
    sensor_noise: float = 0.14,
    overlap_probability: float = 0.75,
    standby_session_multiplier: float = 2.0,
) -> pd.DataFrame:
    """Generate an honest hardware-substitute benchmark for demonstrations.

    This is not REFIT and must not be reported as measured hardware data. It
    intentionally models noisy sensors, transitions and overlapping loads.
    """
    rng = np.random.default_rng(seed)
    rows: list[pd.DataFrame] = []
    timestamp = pd.Timestamp("2026-06-01T00:00:00Z")
    session_id = 0

    labels = list(PROFILES)
    for label in labels:
        profile = PROFILES[label]
        session_count = (
            int(round(sessions_per_class * standby_session_multiplier))
            if label == "standby"
            else sessions_per_class
        )
        for _ in range(session_count):
            session_id += 1
            length = int(
                np.clip(
                    rng.normal(samples_per_session, samples_per_session * 0.18),
                    45,
                    samples_per_session * 1.6,
                )
            )
            voltage = rng.normal(220 + rng.normal(0, 3.2), 1.4, length)
            active = _session_signal(profile, length, rng)

            overlap_label = "none"
            if label != "standby" and rng.random() < overlap_probability:
                candidates = [
                    name
                    for name in labels
                    if name not in {label, "standby", "hervidor"}
                ]
                overlap_label = str(rng.choice(candidates))
                overlap = _session_signal(PROFILES[overlap_label], length, rng)
                active += overlap * rng.uniform(0.12, 0.55)

            transition_count = max(2, int(length * 0.12))
            transition_positions = np.r_[
                np.arange(transition_count),
                np.arange(length - transition_count, length),
            ]
            active[transition_positions] *= rng.uniform(0.25, 0.85)

            active += rng.normal(0, np.maximum(active * sensor_noise, 3))
            active = np.clip(active, 0, None)
            pf = np.clip(
                rng.normal(profile.power_factor, 0.035 + sensor_noise * 0.25, length),
                0.45,
                1.0,
            )
            apparent = active / pf
            reactive = (
                profile.reactive_sign
                * np.sqrt(np.maximum(apparent**2 - active**2, 0))
            )
            current = apparent / np.maximum(voltage, 1)
            phase_angle = np.degrees(np.arccos(pf))
            time_values = pd.date_range(
                timestamp,
                periods=length,
                freq="1s",
            )
            energy = np.cumsum(active / 3_600_000)

            rows.append(
                pd.DataFrame(
                    {
                        "timestamp": time_values,
                        "session_id": session_id,
                        "source": "synthetic_hardware_substitute",
                        "voltage_rms": voltage,
                        "current_rms": current,
                        "phase_angle": phase_angle,
                        "active_power_w": active,
                        "reactive_power_var": reactive,
                        "apparent_power_va": apparent,
                        "power_factor": pf,
                        "energy_kwh": energy,
                        "appliance_label": label,
                        "overlap_appliance": overlap_label,
                        "tariff_soles_kwh": 0.60,
                    }
                )
            )
            timestamp = time_values[-1] + pd.Timedelta(
                seconds=int(rng.integers(5, 35))
            )

    data = pd.concat(rows, ignore_index=True)
    data["active_power_delta_w"] = (
        data.groupby("session_id")["active_power_w"].diff().fillna(0)
    )
    data["active_power_rolling_std"] = (
        data.groupby("session_id")["active_power_w"]
        .rolling(7, min_periods=1)
        .std()
        .reset_index(level=0, drop=True)
        .fillna(0)
    )
    data["timestamp"] = data["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/demo_hardware_simulated.csv")
    parser.add_argument("--sessions-per-class", type=int, default=80)
    parser.add_argument("--samples-per-session", type=int, default=90)
    parser.add_argument("--sensor-noise", type=float, default=0.14)
    parser.add_argument("--overlap-probability", type=float, default=0.75)
    parser.add_argument("--standby-session-multiplier", type=float, default=2.0)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data = generate_demo_measurements(
        sessions_per_class=args.sessions_per_class,
        samples_per_session=args.samples_per_session,
        sensor_noise=args.sensor_noise,
        overlap_probability=args.overlap_probability,
        standby_session_multiplier=args.standby_session_multiplier,
        seed=args.seed,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    summary = {
        "rows": len(data),
        "sessions": int(data["session_id"].nunique()),
        "labels": data["appliance_label"].value_counts().to_dict(),
        "source": "synthetic_hardware_substitute",
        "disclosure": "Simulated data; not REFIT and not measured by EcoWatt hardware.",
    }
    output.with_suffix(".json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
