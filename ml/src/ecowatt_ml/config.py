from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ML_ROOT = PACKAGE_ROOT.parent
DATA_DIR = ML_ROOT / "data"
MODELS_DIR = ML_ROOT / "models"


FEATURE_COLUMNS = [
    "voltage_rms",
    "current_rms",
    "phase_angle",
    "active_power_w",
    "reactive_power_var",
    "apparent_power_va",
    "power_factor",
]

LABEL_COLUMN = "appliance_label"
TIMESTAMP_COLUMN = "timestamp"
ENERGY_COLUMN = "energy_kwh"
TARIFF_COLUMN = "tariff_soles_kwh"

APPLIANCE_LABELS = [
    "standby",
    "foco_25w",
    "foco_100w",
    "refrigeradora",
    "hervidor",
]


@dataclass(frozen=True)
class WindowConfig:
    size: int = 60
    stride: int = 15
