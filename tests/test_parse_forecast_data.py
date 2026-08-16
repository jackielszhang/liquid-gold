"""Forecast parsing uses CSV fixtures in tests and CEF daily PDFs in production."""

from pathlib import Path
import unittest

from scripts.parse_forecast_data import parse_cef_daily_pdf, parse_forecast, parse_forecast_csv


class ParseForecastTests(unittest.TestCase):
    def test_parse_csv_fixture(self) -> None:
        parsed = parse_forecast_csv(Path("data/fixtures/forecast-sample.csv"), "fixture")
        self.assertEqual(parsed.petrol_95_estimated_change_cents, -80)
        self.assertEqual(parsed.diesel_50ppm_estimated_change_cents, 55)
        self.assertEqual(parsed.direction, "down")

    def test_parse_cef_daily_pdf_fixture(self) -> None:
        # Over-recovery of 126.420 on petrol 95 → estimated change -126c.
        # Diesel 0.005% recovery 74.072 → diesel_50ppm change -74c.
        parsed = parse_cef_daily_pdf(Path("data/fixtures/cef-daily-14-07-2026.pdf"), "fixture-pdf")
        self.assertEqual(parsed.as_of_date, "2026-07-14")
        self.assertEqual(parsed.petrol_95_estimated_change_cents, -126)
        self.assertEqual(parsed.diesel_50ppm_estimated_change_cents, -74)
        self.assertEqual(parsed.direction, "down")
        self.assertEqual(parsed.diesel_50ppm_direction, "down")

    def test_parse_forecast_routes_pdf(self) -> None:
        parsed = parse_forecast(Path("data/fixtures/cef-daily-14-07-2026.pdf"), "fixture-pdf")
        self.assertEqual(parsed.petrol_95_estimated_change_cents, -126)


if __name__ == "__main__":
    unittest.main()
