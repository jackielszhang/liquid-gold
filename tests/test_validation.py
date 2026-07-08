from copy import deepcopy
import unittest

from scripts.validate_data import validate_dataset


BASE = {
    "prices": {
        "petrol_95": {
            "coastal_cents_per_litre": 2523,
            "inland_cents_per_litre": 2587,
        },
        "petrol_93": {
            "coastal_cents_per_litre": 2515,
            "inland_cents_per_litre": 2579,
        },
    },
    "forecast": {
        "petrol_95_estimated_change_cents": -80,
        "direction": "down",
        "confidence": "low",
        "as_of_date": "2026-07-01",
    },
}


class ValidationTests(unittest.TestCase):
    def test_missing_petrol_95_side_fails(self) -> None:
        payload = deepcopy(BASE)
        del payload["prices"]["petrol_95"]["coastal_cents_per_litre"]
        errors = validate_dataset(payload, None)
        self.assertTrue(any("petrol_95 coastal" in error for error in errors))

    def test_wildly_incorrect_value_fails(self) -> None:
        payload = deepcopy(BASE)
        payload["prices"]["petrol_95"]["coastal_cents_per_litre"] = 25230
        errors = validate_dataset(payload, None)
        self.assertTrue(any("outside expected range" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
