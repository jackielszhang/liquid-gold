"""DMPR / gov.za / CEF press-release adapter for official pump prices."""

from __future__ import annotations

from pathlib import Path

from scripts.parse_official_prices import parse_official_prices
from scripts.sources.base import AdapterResult


def parse(
    path: Path,
    source_url: str,
    previous_prices: dict[str, dict] | None = None,
) -> AdapterResult:
    try:
        parsed = parse_official_prices(path, source_url, previous_prices=previous_prices)
        return AdapterResult(
            ok=True,
            payload={
                "effective_date": parsed.effective_date,
                "publication_date": parsed.publication_date,
                "prices": parsed.prices,
                "source_url": parsed.source_url,
                "parser_used": parsed.parser_used,
                "snippet": parsed.snippet,
                "adjustments": parsed.adjustments,
            },
            source_url=source_url,
            path=path,
        )
    except Exception as exc:
        return AdapterResult(ok=False, payload=None, error=str(exc), source_url=source_url, path=path)
