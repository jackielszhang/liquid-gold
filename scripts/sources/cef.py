"""Central Energy Fund-style forecast adapter.

This is the only adapter that currently supplies next-month cents estimates.
If the CSV layout changes, keep the public Forecast fields the same and
change only this mapping.
"""

from __future__ import annotations

from pathlib import Path

from scripts.parse_forecast_data import parse_forecast_csv
from scripts.sources.base import AdapterResult


def parse(path: Path, source_url: str) -> AdapterResult:
    try:
        parsed = parse_forecast_csv(path, source_url)
        return AdapterResult(
            ok=True,
            payload={
                "as_of_date": parsed.as_of_date,
                "petrol_95_estimated_change_cents": parsed.petrol_95_estimated_change_cents,
                "diesel_50ppm_estimated_change_cents": parsed.diesel_50ppm_estimated_change_cents,
                "direction": parsed.direction,
                "diesel_50ppm_direction": parsed.diesel_50ppm_direction,
                "confidence": parsed.confidence,
                "source_url": parsed.source_url,
            },
            source_url=source_url,
            path=path,
        )
    except Exception as exc:
        return AdapterResult(ok=False, payload=None, error=str(exc), source_url=source_url, path=path)
