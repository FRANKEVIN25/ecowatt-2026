from __future__ import annotations

import unittest

from ecowatt_ml.simulate_demo_data import generate_demo_measurements


class DemoSimulationTests(unittest.TestCase):
    def test_simulation_is_disclosed_and_contains_sessions(self) -> None:
        data = generate_demo_measurements(
            sessions_per_class=2,
            samples_per_session=50,
            seed=7,
        )
        self.assertEqual(
            set(data["source"]),
            {"synthetic_hardware_substitute"},
        )
        self.assertGreater(data["session_id"].nunique(), 5)
        self.assertTrue(data["active_power_w"].ge(0).all())
        self.assertTrue(data["appliance_label"].nunique() >= 7)


if __name__ == "__main__":
    unittest.main()
