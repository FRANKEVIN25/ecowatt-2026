from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from ecowatt_ml.config import FEATURE_COLUMNS, LABEL_COLUMN, WindowConfig
from ecowatt_ml.preprocess import split_train_validation


class SplitTrainValidationTests(unittest.TestCase):
    def test_split_is_chronological_purged_and_scaler_uses_train_only(self) -> None:
        rows = 200
        data = pd.DataFrame(
            {
                column: np.arange(rows, dtype=float) + index
                for index, column in enumerate(FEATURE_COLUMNS)
            }
        )
        data[LABEL_COLUMN] = np.where(np.arange(rows) % 2 == 0, "a", "b")
        config = WindowConfig(size=20, stride=5)

        x_train, x_val, _, _, _, scaler, metadata = split_train_validation(
            data,
            config,
            validation_ratio=0.2,
        )

        self.assertGreater(len(x_train), 0)
        self.assertGreater(len(x_val), 0)
        self.assertEqual(metadata["overlap_rows"], 0)
        self.assertGreater(
            metadata["validation_row_start"],
            metadata["train_row_end"],
        )
        expected_train_mean = data.iloc[:160][FEATURE_COLUMNS].mean().to_numpy()
        np.testing.assert_allclose(scaler.mean_, expected_train_mean)


if __name__ == "__main__":
    unittest.main()
