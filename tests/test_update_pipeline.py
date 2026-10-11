"""Fail-closed publishing and source discovery."""

from contextlib import redirect_stderr
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts import update_fuel_data
from scripts.fetch_sources import discover_latest_cef_daily_pdf
from scripts.update_fuel_data import build_dataset


class UpdatePipelineTests(unittest.TestCase):
    def test_previous_payload_is_untouched_on_failure_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            public_dir = Path(tmp)
            payload_path = public_dir / "fuel-data.json"
            original = '{"status":"ok","prices":{}}\n'
            payload_path.write_text(original, encoding="utf-8")

            with (
                mock.patch.object(update_fuel_data, "PUBLIC_DIR", public_dir),
                mock.patch.object(update_fuel_data, "load_manual_override", return_value={"enabled": False}),
                mock.patch.object(update_fuel_data, "build_dataset", side_effect=RuntimeError("source failed")),
                redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(update_fuel_data.main(), 1)

            self.assertEqual(payload_path.read_text(encoding="utf-8"), original)

    def test_live_source_failure_does_not_use_sample_fallback(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"OFFICIAL_PRICES_URL": "", "FORECAST_URL": ""},
            clear=False,
        ):
            with mock.patch(
                "scripts.update_fuel_data.dmre.current_schedule_url",
                return_value="https://dmpr.example/current.zip",
            ), mock.patch(
                "scripts.update_fuel_data.discover_latest_cef_daily_pdf",
                return_value="https://cef.example/current.pdf",
            ), mock.patch(
                "scripts.update_fuel_data.safe_download",
                return_value=None,
            ):
                with self.assertRaisesRegex(RuntimeError, "refusing to publish sample data"):
                    build_dataset(None)


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
