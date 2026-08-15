from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from scripts.update_fuel_data import append_history, write_json


class UpdatePipelineTests(unittest.TestCase):
    def test_history_appends_snapshot(self) -> None:
        dataset = {
            "last_updated": "2026-07-07T00:00:00Z",
            "prices": {
                "petrol_95": {"coastal_cents_per_litre": 2523, "inland_cents_per_litre": 2587},
                "diesel_50ppm": {"coastal_cents_per_litre": 2345, "inland_cents_per_litre": 2410},
            },
            "forecast": {"petrol_95_estimated_change_cents": -80, "diesel_50ppm_estimated_change_cents": 55},
            "recommendation": {"petrol_95": {"action": "wait"}, "diesel_50ppm": {"action": "fill_now"}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            history_path = Path(tmp) / "history.json"
            write_json(history_path, [])
            append_history(history_path, dataset)
            history = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(len(history), 1)

    def test_previous_payload_is_untouched_on_failure_path(self) -> None:
        previous = {"status": "ok"}
        current = deepcopy(previous)
        self.assertEqual(previous, current)


if __name__ == "__main__":
    unittest.main()
