from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


TARGET_APPLIANCES = ("washing_machine", "microwave", "kettle")
APPLIANCE_THRESHOLDS_W = {
    "washing_machine": 20.0,
    "microwave": 200.0,
    "kettle": 2_000.0,
}

# REFIT IAM channel names differ by house. The mapping follows the REFIT
# metadata maintained by NILMTK:
# https://github.com/nilmtk/nilmtk/tree/master/nilmtk/dataset_converters/refit/metadata
REFIT_CHANNELS: dict[int, dict[str, tuple[str, ...]]] = {
    2: {
        "washing_machine": ("Appliance2",),
        "microwave": ("Appliance5",),
        "kettle": ("Appliance8",),
    },
    3: {
        "washing_machine": ("Appliance6",),
        "microwave": ("Appliance8",),
        "kettle": ("Appliance9",),
    },
    4: {
        "washing_machine": ("Appliance5", "Appliance6"),
        "microwave": ("Appliance8",),
        "kettle": ("Appliance9",),
    },
    5: {
        "washing_machine": ("Appliance3",),
        "microwave": ("Appliance7",),
        "kettle": ("Appliance8",),
    },
    6: {
        "washing_machine": ("Appliance2",),
        "microwave": ("Appliance6",),
        "kettle": ("Appliance7",),
    },
    8: {
        "washing_machine": ("Appliance4",),
        "microwave": ("Appliance8",),
        "kettle": ("Appliance9",),
    },
    9: {
        "washing_machine": ("Appliance3",),
        "microwave": ("Appliance6",),
        "kettle": ("Appliance7",),
    },
    13: {
        "washing_machine": ("Appliance3",),
        "microwave": ("Appliance7", "Appliance8"),
        "kettle": ("Appliance9",),
    },
    17: {
        "washing_machine": ("Appliance4",),
        "microwave": ("Appliance7",),
        "kettle": ("Appliance8",),
    },
    19: {
        "washing_machine": ("Appliance2",),
        "microwave": ("Appliance4",),
        "kettle": ("Appliance5",),
    },
    20: {
        "washing_machine": ("Appliance4",),
        "microwave": ("Appliance8",),
        "kettle": ("Appliance9",),
    },
}


@dataclass(frozen=True)
class RefitHouseData:
    aggregate: np.ndarray
    appliance_power: dict[str, np.ndarray]
    unix: np.ndarray
    issues: np.ndarray


def refit_house_path(root: str | Path, house: int) -> Path:
    path = Path(root) / f"CLEAN_House{house}.csv"
    if not path.exists():
        raise FileNotFoundError(f"REFIT House {house} not found: {path}")
    return path


def load_refit_house(
    root: str | Path,
    house: int,
    appliances: tuple[str, ...] = TARGET_APPLIANCES,
) -> RefitHouseData:
    mapping = REFIT_CHANNELS.get(house)
    if mapping is None:
        raise ValueError(f"No REFIT appliance mapping configured for House {house}.")
    missing = [appliance for appliance in appliances if appliance not in mapping]
    if missing:
        raise ValueError(
            f"House {house} does not map appliances: {', '.join(missing)}"
        )

    appliance_columns = sorted(
        {
            column
            for appliance in appliances
            for column in mapping[appliance]
        }
    )
    columns = ["Unix", "Aggregate", "Issues", *appliance_columns]
    dtypes = {column: np.float32 for column in columns}
    dtypes["Unix"] = np.float64
    data = pd.read_csv(
        refit_house_path(root, house),
        usecols=columns,
        dtype=dtypes,
    )

    appliance_power = {
        appliance: (
            data[list(mapping[appliance])]
            .fillna(0)
            .clip(lower=0)
            .sum(axis=1)
            .to_numpy(dtype=np.float32)
        )
        for appliance in appliances
    }
    return RefitHouseData(
        aggregate=data["Aggregate"].fillna(0).clip(lower=0).to_numpy(np.float32),
        appliance_power=appliance_power,
        unix=data["Unix"].to_numpy(np.float64),
        issues=data["Issues"].fillna(0).to_numpy(np.float32),
    )


def valid_window_centers(
    data: RefitHouseData,
    window_size: int,
    stride: int,
    max_gap_seconds: float = 30.0,
) -> np.ndarray:
    if window_size <= 0 or window_size % 2 == 0:
        raise ValueError("window_size must be a positive odd number.")
    if stride <= 0:
        raise ValueError("stride must be greater than zero.")

    half = window_size // 2
    centers = np.arange(half, len(data.aggregate) - half, stride, dtype=np.int64)
    invalid = (
        ~np.isfinite(data.aggregate)
        | ~np.isfinite(data.unix)
        | (data.issues != 0)
    )
    for values in data.appliance_power.values():
        invalid |= ~np.isfinite(values)

    deltas = np.diff(data.unix, prepend=data.unix[0])
    invalid |= (deltas < 0) | (deltas > max_gap_seconds)
    cumulative = np.concatenate(([0], np.cumsum(invalid, dtype=np.int64)))
    starts = centers - half
    ends = centers + half + 1
    return centers[(cumulative[ends] - cumulative[starts]) == 0]


def extract_windows(
    aggregate: np.ndarray,
    centers: np.ndarray,
    window_size: int,
) -> np.ndarray:
    offsets = np.arange(-(window_size // 2), window_size // 2 + 1)
    return aggregate[centers[:, None] + offsets].astype(np.float32, copy=False)


def build_input_features(
    aggregate_windows: np.ndarray,
    mean: np.ndarray | None = None,
    std: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    log_power = np.log1p(np.clip(aggregate_windows, 0, 20_000))
    difference = np.diff(log_power, axis=1, prepend=log_power[:, :1])
    local_baseline = np.median(log_power, axis=1, keepdims=True)
    relative_power = log_power - local_baseline
    features = np.stack(
        (log_power, relative_power, difference),
        axis=1,
    ).astype(np.float32)

    if mean is None or std is None:
        mean = features.mean(axis=(0, 2), dtype=np.float64).astype(np.float32)
        std = features.std(axis=(0, 2), dtype=np.float64).astype(np.float32)
        std = np.maximum(std, 1e-6)
    normalized = (features - mean[None, :, None]) / std[None, :, None]
    return normalized.astype(np.float32), mean, std


def sample_balanced_centers(
    centers: np.ndarray,
    aggregate: np.ndarray,
    appliance_power: np.ndarray,
    threshold_w: float,
    per_class: int,
    rng: np.random.Generator,
) -> np.ndarray:
    states = appliance_power[centers] > threshold_w
    positives = centers[states]
    negatives = centers[~states]
    positive_count = min(per_class, len(positives))
    negative_count = min(per_class, len(negatives))
    if positive_count == 0 or negative_count == 0:
        raise ValueError("Both on and off samples are required for SGN training.")
    selected_positives = rng.choice(
        positives,
        size=positive_count,
        replace=False,
    )
    hard_count = min(int(round(negative_count * 0.7)), negative_count)
    random_count = negative_count - hard_count
    hard_cutoff = np.quantile(aggregate[negatives], 0.75)
    hard_pool = negatives[aggregate[negatives] >= hard_cutoff]
    hard_count = min(hard_count, len(hard_pool))
    selected_hard = rng.choice(hard_pool, size=hard_count, replace=False)
    remaining_pool = np.setdiff1d(negatives, selected_hard, assume_unique=False)
    selected_random = rng.choice(
        remaining_pool,
        size=negative_count - hard_count,
        replace=False,
    )
    selected = np.concatenate(
        (selected_positives, selected_hard, selected_random)
    )
    rng.shuffle(selected)
    return selected


def uniformly_limit_centers(
    centers: np.ndarray,
    maximum: int | None,
) -> np.ndarray:
    if maximum is None or len(centers) <= maximum:
        return centers
    positions = np.linspace(0, len(centers) - 1, num=maximum, dtype=np.int64)
    return centers[positions]
