from pathlib import Path
import unittest

from scripts.parse_official_prices import normalize_price_to_cents, parse_official_prices_text


class ParseOfficialPricesTests(unittest.TestCase):
    def test_parse_representative_text(self) -> None:
        fixture = Path("data/fixtures/official-price-sample.txt").read_text(encoding="utf-8")
        parsed = parse_official_prices_text(fixture, "fixture")
        self.assertEqual(parsed.prices["petrol_95"]["coastal_cents_per_litre"], 2523)
        self.assertEqual(parsed.prices["petrol_93"]["inland_cents_per_litre"], 2579)

    def test_normalizes_common_decimal_formats(self) -> None:
        self.assertEqual(normalize_price_to_cents("25.23"), 2523)
        self.assertEqual(normalize_price_to_cents("25,23"), 2523)
        self.assertEqual(normalize_price_to_cents("2523.0"), 2523)

    def test_malformed_text_returns_missing_prices(self) -> None:
        parsed = parse_official_prices_text("noise only", "fixture")
        self.assertEqual(parsed.prices, {})


if __name__ == "__main__":
    unittest.main()
