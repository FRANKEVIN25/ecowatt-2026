from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import (
    ENERGY_COLUMN,
    FEATURE_COLUMNS,
    LABEL_COLUMN,
    TARIFF_COLUMN,
    TIMESTAMP_COLUMN,
)


REQUIRED_COLUMNS = [
    TIMESTAMP_COLUMN,
    *FEATURE_COLUMNS,
    ENERGY_COLUMN,
    LABEL_COLUMN,
    TARIFF_COLUMN,
]


def load_measurements(path: str | Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    missing = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    data[TIMESTAMP_COLUMN] = pd.to_datetime(data[TIMESTAMP_COLUMN], utc=True)
    data = data.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)
    return data


def save_measurements(data: pd.DataFrame, path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
