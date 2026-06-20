from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

from .config import FEATURE_COLUMNS, LABEL_COLUMN, WindowConfig


def build_windows(
    data: pd.DataFrame,
    config: WindowConfig = WindowConfig(),
    *,
    scaler: StandardScaler | None = None,
    encoder: LabelEncoder | None = None,
    fit_preprocessors: bool = True,
) -> tuple[np.ndarray, np.ndarray, LabelEncoder, StandardScaler]:
    if scaler is None:
        scaler = StandardScaler()
    if encoder is None:
        encoder = LabelEncoder()

    raw_features = data[FEATURE_COLUMNS].astype(float)
    raw_labels = data[LABEL_COLUMN].astype(str)
    if fit_preprocessors:
        features = scaler.fit_transform(raw_features)
        labels = encoder.fit_transform(raw_labels)
    else:
        if not hasattr(scaler, "mean_") or not hasattr(encoder, "classes_"):
            raise ValueError("Preprocessors must be fitted before transforming data.")
        unknown_labels = sorted(set(raw_labels) - set(encoder.classes_))
        if unknown_labels:
            raise ValueError(
                "Validation data contains labels absent from training: "
                + ", ".join(unknown_labels)
            )
        features = scaler.transform(raw_features)
        labels = encoder.transform(raw_labels)

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
    data: pd.DataFrame,
    config: WindowConfig = WindowConfig(),
    validation_ratio: float = 0.2,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    LabelEncoder,
    StandardScaler,
    dict[str, int | float | str],
]:
    """Create a chronological, purged split before window generation.

    Splitting rows first prevents overlapping windows from appearing in both
    partitions. The purge gap also keeps the boundary windows from being
    near-duplicates. Preprocessors are fitted exclusively on training rows.
    """
    if not 0 < validation_ratio < 1:
        raise ValueError("validation_ratio must be between 0 and 1.")
    if config.size <= 0 or config.stride <= 0:
        raise ValueError("Window size and stride must be greater than zero.")

    split_index = int(len(data) * (1 - validation_ratio))
    purge_rows = config.size - 1
    validation_start = split_index + purge_rows
    train_data = data.iloc[:split_index].copy()
    validation_data = data.iloc[validation_start:].copy()

    if len(train_data) < config.size or len(validation_data) < config.size:
        raise ValueError(
            "Not enough rows for a purged train/validation split with "
            f"window size {config.size}."
        )

    x_train, y_train, encoder, scaler = build_windows(train_data, config)
    x_val, y_val, _, _ = build_windows(
        validation_data,
        config,
        scaler=scaler,
        encoder=encoder,
        fit_preprocessors=False,
    )
    metadata: dict[str, int | float | str] = {
        "strategy": "chronological_purged",
        "validation_ratio": validation_ratio,
        "train_rows": len(train_data),
        "validation_rows": len(validation_data),
        "purge_rows": purge_rows,
        "train_row_end": split_index - 1,
        "validation_row_start": validation_start,
        "overlap_rows": 0,
        "train_windows": len(x_train),
        "validation_windows": len(x_val),
    }
    return (
        x_train,
        x_val,
        y_train,
        y_val,
        encoder,
        scaler,
        metadata,
    )
