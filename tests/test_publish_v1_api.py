"""Public v1 static API publisher + rolling two-month retention."""

from datetime import date
from pathlib import Path
import tempfile
import unittest

from scripts.publish_v1_api import (
    build_latest_payload,
    build_month_payload,
    enforce_two_month_retention,
    publish_v1_api,
    write_json,
)


def _sample_dataset(**overrides) -> dict:
    payload = {
        "last_updated": "2026-08-16T14:21:48Z",
        "status": "ok",
        "manual_override": False,
        "next_adjustment_date": "2026-09-02",
        "source_status": {"official_prices": "ok", "forecast": "ok"},
        "prices": {
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
        },
        "adjustments": {"petrol_95": -52, "diesel_50ppm": 123},
        "forecast": {
            "as_of_date": "2026-08-13",
            "petrol_95_estimated_change_cents": 74,
            "diesel_50ppm_estimated_change_cents": 289,
            "direction": "up",
            "diesel_50ppm_direction": "up",
            "confidence": "low",
            "source_url": "https://example.test/Daily-13-08-2026.pdf",
        },
        "recommendation": {"petrol_95": {"action": "fill_now"}},
        "sources": {
            "official_prices_url": "https://example.test/press.pdf",
            "forecast_url": "https://example.test/Daily-13-08-2026.pdf",
            "validation_url": "",
        },
    }
    payload.update(overrides)
    return payload


class PublishV1ApiTests(unittest.TestCase):
    def test_latest_keeps_app_compatible_fields(self) -> None:
        latest = build_latest_payload(_sample_dataset())
        self.assertEqual(latest["schema_version"], 2)
        self.assertEqual(latest["last_updated"], "2026-08-16T14:21:48Z")
        self.assertIn("disclaimer", latest)
        self.assertEqual(latest["prices"]["petrol_95"]["coastal_cents_per_litre"], 2471)

    def test_month_upserts_daily_forecast_by_as_of_date(self) -> None:
        existing = {
            "official": {"prices": {}, "adjustment_cents": {}, "effective_date": "2026-08-05", "source_url": ""},
            "daily_forecasts": [
                {
                    "as_of_date": "2026-08-12",
                    "petrol_95_estimated_change_cents": 80,
                    "diesel_50ppm_estimated_change_cents": 300,
                    "direction": "up",
                    "diesel_50ppm_direction": "up",
                    "confidence": "low",
                    "source_url": "",
                },
                {
                    "as_of_date": "2026-08-13",
                    "petrol_95_estimated_change_cents": 70,
                    "diesel_50ppm_estimated_change_cents": 280,
                    "direction": "up",
                    "diesel_50ppm_direction": "up",
                    "confidence": "low",
                    "source_url": "",
                },
            ],
        }
        month = build_month_payload("2026-08", dataset=_sample_dataset(), existing=existing)
        self.assertEqual(month["official"]["adjustment_cents"]["petrol_95"], -52)
        dates = [row["as_of_date"] for row in month["daily_forecasts"]]
        self.assertEqual(dates, ["2026-08-12", "2026-08-13"])
        self.assertEqual(month["daily_forecasts"][-1]["petrol_95_estimated_change_cents"], 74)

    def test_publish_writes_aliases_and_prunes_old_months(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            public_dir = Path(tmp) / "public"
            months_dir = public_dir / "v1" / "months"
            months_dir.mkdir(parents=True)
            write_json(months_dir / "2026-06.json", {"month": "2026-06", "daily_forecasts": []})
            write_json(
                months_dir / "2026-07.json",
                {
                    "schema_version": 2,
                    "month": "2026-07",
                    "official": {
                        "effective_date": "2026-07-01",
                        "adjustment_cents": {},
                        "prices": {
                            "petrol_95": {"coastal_cents_per_litre": 2523, "inland_cents_per_litre": 2587},
                            "diesel_50ppm": {"coastal_cents_per_litre": 2345, "inland_cents_per_litre": 2410},
                        },
                        "source_url": "",
                    },
                    "daily_forecasts": [],
                },
            )

            info = publish_v1_api(public_dir, _sample_dataset(), today=date(2026, 8, 16))
            self.assertEqual(info["current_month"], "2026-08")
            self.assertEqual(info["previous_month"], "2026-07")
            self.assertIn("2026-06", info["removed_months"])
            self.assertTrue((public_dir / "v1" / "latest.json").exists())
            self.assertTrue((months_dir / "2026-08.json").exists())
            self.assertTrue((months_dir / "current.json").exists())
            self.assertTrue((months_dir / "previous.json").exists())
            self.assertFalse((months_dir / "2026-06.json").exists())
            index = (public_dir / "v1" / "index.json").read_text(encoding="utf-8")
            self.assertIn("2026-08", index)
            self.assertIn("2026-07", index)

    def test_retention_helper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            months_dir = Path(tmp)
            write_json(months_dir / "2026-05.json", {"month": "2026-05"})
            write_json(months_dir / "2026-07.json", {"month": "2026-07"})
            removed = enforce_two_month_retention(months_dir, {"2026-07", "2026-08"})
            self.assertEqual(removed, ["2026-05"])


if __name__ == "__main__":
    unittest.main()
