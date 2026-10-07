"""DMPR workbook adapter for official pump prices."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

from scripts.fetch_sources import fetch_text
from scripts.parse_official_prices import parse_official_prices
from scripts.sources.base import AdapterResult

FUEL_PRICES_PAGE = "https://www.dmpr.gov.za/Branches/Petroleum-Resources/Fuel-Prices"


class _LatestScheduleLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.latest_section = False
        self.seen_schedule_heading = False
        self.heading: list[str] | None = None
        self.card_title: list[str] | None = None
        self.is_archive_card = False
        self.anchor: tuple[str, list[str]] | None = None
        self.download_url: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "h3":
            self.latest_section = False
            self.is_archive_card = False
            self.heading = []
        elif tag == "h4" and self.latest_section:
            self.card_title = []
            self.is_archive_card = False
        elif tag == "a" and self.latest_section and self.is_archive_card:
            self.anchor = (attrs_dict.get("href", "") or "", [])

    def handle_data(self, data: str) -> None:
        if self.heading is not None:
            self.heading.append(data)
        if self.card_title is not None:
            self.card_title.append(data)
        if self.anchor is not None:
            self.anchor[1].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self.heading is not None:
            title = " ".join(" ".join(self.heading).split()).casefold()
            if not self.seen_schedule_heading:
                self.latest_section = title.startswith("fuel prices effective from")
                self.seen_schedule_heading = self.latest_section
            self.heading = None
        elif tag == "h4" and self.card_title is not None:
            title = " ".join(" ".join(self.card_title).split()).casefold()
            self.is_archive_card = self.latest_section and "fuel price adjustment documents" in title and "zip" in title
            self.card_title = None
        elif tag == "a" and self.anchor is not None:
            href, label = self.anchor
            if self.is_archive_card and "download" in " ".join(label).casefold():
                self.download_url = href
            self.anchor = None


def extract_current_schedule_url(html: str, page_url: str = FUEL_PRICES_PAGE) -> str:
    parser = _LatestScheduleLinkParser()
    parser.feed(html)
    if not parser.download_url:
        raise ValueError("DMPR fuel prices page has no current schedule ZIP link")
    return urljoin(page_url, parser.download_url)


def current_schedule_url() -> str:
    html, page_url = fetch_text(FUEL_PRICES_PAGE)
    return extract_current_schedule_url(html, page_url)


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
