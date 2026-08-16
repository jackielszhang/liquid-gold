"""Parser tests for absolute fixtures and real CEF / gov.za samples."""

from pathlib import Path
import unittest

from scripts.parse_official_prices import (
    apply_adjustments_to_prices,
    normalize_price_to_cents,
    parse_official_prices,
    parse_official_prices_text,
    parse_price_adjustments_text,
)


class ParseOfficialPricesTests(unittest.TestCase):
    def test_parse_representative_text(self) -> None:
        fixture = Path("data/fixtures/official-price-sample.txt").read_text(encoding="utf-8")
        parsed = parse_official_prices_text(fixture, "fixture")
        self.assertEqual(parsed.prices["petrol_95"]["coastal_cents_per_litre"], 2523)
        self.assertEqual(parsed.prices["petrol_93"]["inland_cents_per_litre"], 2579)
        self.assertEqual(parsed.prices["diesel_50ppm"]["coastal_cents_per_litre"], 2345)

    def test_normalizes_common_decimal_formats(self) -> None:
        self.assertEqual(normalize_price_to_cents("25.23"), 2523)
        self.assertEqual(normalize_price_to_cents("25,23"), 2523)
        self.assertEqual(normalize_price_to_cents("2523.0"), 2523)

    def test_malformed_text_returns_missing_prices(self) -> None:
        parsed = parse_official_prices_text("noise only", "fixture")
        self.assertEqual(parsed.prices, {})

    def test_govza_announcement_adjustments(self) -> None:
        path = Path("data/fixtures/govza-fuel-prices-august-2026.html")
        adjustments = parse_price_adjustments_text(path.read_text(encoding="utf-8"))
        self.assertEqual(adjustments.effective_date, "2026-08-05")
        self.assertEqual(adjustments.changes["petrol_95"], -52)
        self.assertEqual(adjustments.changes["diesel_50ppm"], 123)

    def test_govza_applies_delta_to_previous_prices(self) -> None:
        previous = {
            "petrol_95": {
                "coastal_cents_per_litre": 2523,
                "inland_cents_per_litre": 2587,
                "effective_date": "2026-07-01",
            },
            "diesel_50ppm": {
                "coastal_cents_per_litre": 2345,
                "inland_cents_per_litre": 2410,
                "effective_date": "2026-07-01",
            },
        }
        parsed = parse_official_prices(
            Path("data/fixtures/govza-fuel-prices-august-2026.html"),
            "govza",
            previous_prices=previous,
        )
        self.assertEqual(parsed.prices["petrol_95"]["coastal_cents_per_litre"], 2471)
        self.assertEqual(parsed.prices["diesel_50ppm"]["coastal_cents_per_litre"], 2468)
        self.assertEqual(parsed.effective_date, "2026-08-05")

    def test_already_applied_effective_date_keeps_prices(self) -> None:
        previous = {
            "petrol_95": {
                "coastal_cents_per_litre": 2471,
                "inland_cents_per_litre": 2558,
                "effective_date": "2026-08-05",
            },
            "diesel_50ppm": {
                "coastal_cents_per_litre": 2564,
                "inland_cents_per_litre": 2690,
                "effective_date": "2026-08-05",
            },
        }
        adjustments = parse_price_adjustments_text(
            Path("data/fixtures/govza-fuel-prices-august-2026.html").read_text(encoding="utf-8")
        )
        prices = apply_adjustments_to_prices(previous, adjustments)
        self.assertEqual(prices["petrol_95"]["inland_cents_per_litre"], 2558)
        self.assertEqual(prices["diesel_50ppm"]["inland_cents_per_litre"], 2690)

    def test_cef_press_release_pdf_adjustments(self) -> None:
        previous = {
            "petrol_95": {
                "coastal_cents_per_litre": 2523,
                "inland_cents_per_litre": 2587,
                "effective_date": "2026-07-01",
            },
            "diesel_50ppm": {
                "coastal_cents_per_litre": 2345,
                "inland_cents_per_litre": 2410,
                "effective_date": "2026-07-01",
            },
        }
        parsed = parse_official_prices(
            Path("data/fixtures/cef-press-release-august-2026.pdf"),
            "cef-press",
            previous_prices=previous,
        )
        self.assertEqual(parsed.adjustments["petrol_95"], -52)
        self.assertEqual(parsed.adjustments["diesel_50ppm"], 123)
        self.assertEqual(parsed.effective_date, "2026-08-05")


if __name__ == "__main__":
    unittest.main()
