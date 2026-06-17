from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

from .config import FEATURE_COLUMNS, LABEL_COLUMN, WindowConfig


def build_windows(
    data: pd.DataFrame,
    config: WindowConfig = WindowConfig(),
) -> tuple[np.ndarray, np.ndarray, LabelEncoder, StandardScaler]:
    scaler = StandardScaler()
    encoder = LabelEncoder()

    features = scaler.fit_transform(data[FEATURE_COLUMNS].astype(float))
    labels = encoder.fit_transform(data[LABEL_COLUMN].astype(str))

    x_windows: list[np.ndarray] = []
    y_labels: list[int] = []

    for start in range(0, len(data) - config.size + 1, config.stride):
        end = start + config.size
        x_windows.append(features[start:end])
        values, counts = np.unique(labels[start:end], return_counts=True)
        y_labels.append(int(values[np.argmax(counts)]))

    if not x_windows:
        raise ValueError(
            f"Not enough rows ({len(data)}) for window size {config.size}."
        )

    return (
        np.stack(x_windows).astype(np.float32),
        np.asarray(y_labels, dtype=np.int64),
        encoder,
        scaler,
    )


def split_train_validation(
    x_values: np.ndarray,
    y_values: np.ndarray,
    validation_ratio: float = 0.2,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not 0 < validation_ratio < 1:
        raise ValueError("validation_ratio must be between 0 and 1.")

    unique, counts = np.unique(y_values, return_counts=True)
    stratify = y_values if len(unique) > 1 and counts.min() > 1 else None
    return train_test_split(
        x_values,
        y_values,
        test_size=validation_ratio,
        random_state=random_state,
        stratify=stratify,
    )
