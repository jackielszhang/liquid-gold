import unittest

from scripts.calculate_recommendation import calculate_recommendation
from scripts.update_fuel_data import apply_manual_override, build_dataset


class RecommendationTests(unittest.TestCase):
    def test_wait_threshold(self) -> None:
        recommendation = calculate_recommendation(
            "petrol_95",
            {"coastal_cents_per_litre": 2523, "inland_cents_per_litre": 2587},
            {"petrol_95_estimated_change_cents": -30},
            "2026-08-05",
        )
        self.assertEqual(recommendation["action"], "wait")
        self.assertEqual(recommendation["best_fill_up_date"], "2026-08-05")

    def test_fill_now_threshold(self) -> None:
        recommendation = calculate_recommendation(
            "petrol_95",
            {"coastal_cents_per_litre": 2523, "inland_cents_per_litre": 2587},
            {"petrol_95_estimated_change_cents": 30},
            "2026-08-05",
        )
        self.assertEqual(recommendation["action"], "fill_now")
        self.assertEqual(recommendation["best_fill_up_date"], "2026-08-04")

    def test_unknown_without_forecast(self) -> None:
        recommendation = calculate_recommendation(
            "diesel_50ppm",
            {"coastal_cents_per_litre": 2345, "inland_cents_per_litre": 2410},
            {"diesel_50ppm_estimated_change_cents": None},
            "2026-08-05",
        )
        self.assertEqual(recommendation["action"], "unknown")

    def test_manual_override_wins(self) -> None:
        dataset, _ = build_dataset(None)
        merged = apply_manual_override(
            dataset,
            {
                "enabled": True,
                "prices": {
                    "petrol_95": {
                        "coastal_cents_per_litre": 3000,
                        "inland_cents_per_litre": 3100,
                        "effective_date": "2026-07-01",
                    },
                    "diesel_50ppm": {
                        "coastal_cents_per_litre": 2800,
                        "inland_cents_per_litre": 2900,
                        "effective_date": "2026-07-01",
                    }
                },
                "forecast": {
                    "petrol_95_estimated_change_cents": 50,
                    "direction": "up",
                    "diesel_50ppm_estimated_change_cents": -20,
                    "diesel_50ppm_direction": "down",
                },
            },
        )
        self.assertTrue(merged["manual_override"])
        self.assertEqual(merged["forecast"]["petrol_95_estimated_change_cents"], 50)
        self.assertEqual(merged["recommendation"]["petrol_95"]["next_price_cents_per_litre"]["inland_cents_per_litre"], 3150)


if __name__ == "__main__":
    unittest.main()
