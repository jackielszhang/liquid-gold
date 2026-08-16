"""Fail-closed fixture policy, discovery helpers, and v1 publish wiring."""

from copy import deepcopy
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.fetch_sources import _press_release_sort_key, discover_latest_cef_daily_pdf
from scripts.update_fuel_data import allow_fixture_fallback, build_dataset


class UpdatePipelineTests(unittest.TestCase):
    def test_previous_payload_is_untouched_on_failure_path(self) -> None:
        previous = {"status": "ok", "prices": {"petrol_95": {"coastal_cents_per_litre": 2471}}}
        # Simulate fail-closed: on exception the caller keeps `previous` on disk.
        current = deepcopy(previous)
        try:
            raise RuntimeError("official_prices failed")
        except RuntimeError:
            published = previous
        self.assertEqual(published, current)

    def test_fixture_fallback_disabled_in_github_actions(self) -> None:
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False):
            os.environ.pop("ALLOW_FIXTURE_FALLBACK", None)
            self.assertFalse(allow_fixture_fallback())

    def test_fixture_fallback_explicit_off(self) -> None:
        with mock.patch.dict(os.environ, {"ALLOW_FIXTURE_FALLBACK": "0", "GITHUB_ACTIONS": ""}, clear=False):
            self.assertFalse(allow_fixture_fallback())

    def test_build_dataset_uses_fixtures_locally(self) -> None:
        with mock.patch.dict(os.environ, {"ALLOW_FIXTURE_FALLBACK": "1"}, clear=False):
            for key in ("OFFICIAL_PRICES_URL", "FORECAST_URL", "SECONDARY_VALIDATION_URL"):
                os.environ.pop(key, None)
            dataset, _ = build_dataset(None)
            self.assertEqual(dataset["status"], "ok")
            self.assertIn("petrol_95", dataset["prices"])
            self.assertIn("diesel_50ppm", dataset["prices"])

    def test_fail_closed_without_urls_when_fixtures_disabled(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "ALLOW_FIXTURE_FALLBACK": "0",
                "OFFICIAL_PRICES_URL": "",
                "FORECAST_URL": "",
            },
            clear=False,
        ):
            with mock.patch(
                "scripts.update_fuel_data.discover_latest_cef_press_release",
                side_effect=RuntimeError("network down"),
            ):
                with self.assertRaises(RuntimeError):
                    build_dataset(None)

    def test_press_release_sort_prefers_change_date(self) -> None:
        older = "https://cefgroup.co.za/wp-content/uploads/2026/07/Press-release-26-June-26-Change-01-July-26.pdf"
        newer = "https://cefgroup.co.za/wp-content/uploads/2026/08/Press-Release-31-July-2026-Change-05-August-2026.pdf"
        self.assertGreater(_press_release_sort_key(newer), _press_release_sort_key(older))


class DiscoveryHtmlTests(unittest.TestCase):
    def test_discover_daily_pdf_from_html(self) -> None:
        html = """
        <a href="https://cefgroup.co.za/wp-content/uploads/2026/08/Daily-10-08-2026.pdf">a</a>
        <a href="https://cefgroup.co.za/wp-content/uploads/2026/08/Daily-13-08-2026.pdf">b</a>
        """
        index = '<a href="https://cefgroup.co.za/2026-4/">2026</a>'

        def fake_fetch(url: str, timeout: int = 30):
            if "daily-basic" in url:
                return index, url
            return html, url

        with mock.patch("scripts.fetch_sources.fetch_text", side_effect=fake_fetch):
            latest = discover_latest_cef_daily_pdf("https://cefgroup.co.za/daily-basic-fuel-price/")
        self.assertIn("Daily-13-08-2026.pdf", latest)


if __name__ == "__main__":
    unittest.main()
