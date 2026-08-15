from pathlib import Path
import unittest

from scripts.parse_forecast_data import parse_forecast_csv


class ParseForecastTests(unittest.TestCase):
    def test_parse_csv_fixture(self) -> None:
        parsed = parse_forecast_csv(Path("data/fixtures/forecast-sample.csv"), "fixture")
        self.assertEqual(parsed.petrol_95_estimated_change_cents, -80)
        self.assertEqual(parsed.diesel_50ppm_estimated_change_cents, 55)
        self.assertEqual(parsed.direction, "down")
        self.assertEqual(parsed.diesel_50ppm_direction, "up")


if __name__ == "__main__":
    unittest.main()
