from __future__ import annotations

import unittest

import numpy as np
import torch

from ecowatt_ml.models import SGNApplianceModel
from ecowatt_ml.refit import (
    REFIT_CHANNELS,
    build_input_features,
    extract_windows,
)
from ecowatt_ml.refit_metadata import (
    APPLIANCE_DISPLAY_NAMES_ES,
    REFIT_HOUSE8_APPLIANCES,
)


class RefitPipelineTests(unittest.TestCase):
    def test_house8_has_complete_official_metadata(self) -> None:
        self.assertEqual(
            REFIT_HOUSE8_APPLIANCES,
            {
                "Appliance1": "fridge",
                "Appliance2": "freezer",
                "Appliance3": "washer_dryer",
                "Appliance4": "washing_machine",
                "Appliance5": "toaster",
                "Appliance6": "computer",
                "Appliance7": "television",
                "Appliance8": "microwave",
                "Appliance9": "kettle",
            },
        )
        self.assertEqual(
            APPLIANCE_DISPLAY_NAMES_ES["washing_machine"],
            "Lavadora",
        )

    def test_house8_uses_real_appliance_channels(self) -> None:
        self.assertEqual(
            REFIT_CHANNELS[8],
            {
                "washing_machine": ("Appliance4",),
                "microwave": ("Appliance8",),
                "kettle": ("Appliance9",),
            },
        )

    def test_extract_windows_is_centered(self) -> None:
        aggregate = np.arange(20, dtype=np.float32)
        windows = extract_windows(aggregate, np.asarray([5, 10]), window_size=5)
        np.testing.assert_array_equal(windows[0], [3, 4, 5, 6, 7])
        np.testing.assert_array_equal(windows[1], [8, 9, 10, 11, 12])

    def test_features_are_finite_and_train_only_scalable(self) -> None:
        raw = np.asarray([[0, 10, 20], [30, 40, 50]], dtype=np.float32)
        features, mean, std = build_input_features(raw)
        transformed, _, _ = build_input_features(raw, mean, std)
        self.assertEqual(features.shape, (2, 3, 3))
        self.assertTrue(np.isfinite(transformed).all())

    def test_sgn_output_is_power_times_state_probability(self) -> None:
        model = SGNApplianceModel()
        inputs = torch.randn(4, 3, 127)
        power, state_logit, gated = model(inputs)
        torch.testing.assert_close(gated, power * torch.sigmoid(state_logit))


if __name__ == "__main__":
    unittest.main()
