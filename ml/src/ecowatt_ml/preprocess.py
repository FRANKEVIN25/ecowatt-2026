from __future__ import annotations

import numpy as np
import pandas as pd
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
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not 0 < validation_ratio < 1:
        raise ValueError("validation_ratio must be between 0 and 1.")

    split_at = max(1, int(len(x_values) * (1 - validation_ratio)))
    if split_at >= len(x_values):
        split_at = len(x_values) - 1

    return (
        x_values[:split_at],
        x_values[split_at:],
        y_values[:split_at],
        y_values[split_at:],
    )
