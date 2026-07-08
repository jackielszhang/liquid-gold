import unittest

from scripts.calculate_recommendation import calculate_recommendation
from scripts.update_fuel_data import apply_manual_override, build_dataset


class RecommendationTests(unittest.TestCase):
    def test_wait_threshold(self) -> None:
        recommendation = calculate_recommendation({"petrol_95_estimated_change_cents": -30})
        self.assertEqual(recommendation["action"], "wait")

    def test_fill_now_threshold(self) -> None:
        recommendation = calculate_recommendation({"petrol_95_estimated_change_cents": 30})
        self.assertEqual(recommendation["action"], "fill_now")

    def test_unknown_without_forecast(self) -> None:
        recommendation = calculate_recommendation({"petrol_95_estimated_change_cents": None})
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
                    }
                },
                "forecast": {"petrol_95_estimated_change_cents": 50, "direction": "up"},
            },
        )
        self.assertTrue(merged["manual_override"])
        self.assertEqual(merged["forecast"]["petrol_95_estimated_change_cents"], 50)


if __name__ == "__main__":
    unittest.main()
