"""Validation is the last fence before public JSON is overwritten.

These cases check the failure modes we actually expect from a bad scrape:
a missing coastal/inland cell, or a rands value treated as cents.
"""

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
        "diesel_50ppm": {
            "coastal_cents_per_litre": 2345,
            "inland_cents_per_litre": 2410,
        },
    },
    "forecast": {
        "petrol_95_estimated_change_cents": -80,
        "direction": "down",
        "diesel_50ppm_estimated_change_cents": 55,
        "diesel_50ppm_direction": "up",
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

    def test_missing_diesel_side_fails(self) -> None:
        payload = deepcopy(BASE)
        del payload["prices"]["diesel_50ppm"]["inland_cents_per_litre"]
        errors = validate_dataset(payload, None)
        self.assertTrue(any("diesel_50ppm coastal and inland values are required" in error for error in errors))

    def test_fixture_baseline_does_not_block_first_live_schedule(self) -> None:
        previous = deepcopy(BASE)
        previous["sources"] = {"official_prices_url": "official-price-sample.html"}
        current = deepcopy(BASE)
        current["prices"]["diesel_50ppm"].update(
            coastal_cents_per_litre=2868,
            inland_cents_per_litre=2956,
        )
        self.assertFalse(validate_dataset(current, previous))

    def test_large_jump_from_live_baseline_still_fails(self) -> None:
        previous = deepcopy(BASE)
        previous["sources"] = {"official_prices_url": "https://dmpr.example/old-schedule.zip"}
        current = deepcopy(BASE)
        current["prices"]["diesel_50ppm"].update(
            coastal_cents_per_litre=2868,
            inland_cents_per_litre=2956,
        )
        errors = validate_dataset(current, previous)
        self.assertEqual(sum("changed by more than R5.00/L" in error for error in errors), 2)


if __name__ == "__main__":
    unittest.main()
