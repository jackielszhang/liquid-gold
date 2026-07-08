from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


PRICE_RE = re.compile(
    r"(?P<label>petrol\s*95|95\s*ulp|petrol\s*93|93\s*ulp).*?"
    r"(?P<coastal>\d{1,4}(?:[.,]\d{1,2})?)\D+"
    r"(?P<inland>\d{1,4}(?:[.,]\d{1,2})?)",
    re.IGNORECASE | re.DOTALL,
)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2}|(?:\d{1,2}\s+\w+\s+20\d{2}))")


@dataclass
class OfficialPrices:
    effective_date: str | None
    publication_date: str | None
    prices: dict[str, dict[str, int | str]]
    source_url: str
    parser_used: str
    snippet: str


def normalize_price_to_cents(raw: str) -> int:
    text = raw.strip().replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"invalid price {raw!r}") from exc
    if value > 1000:
        return int(value.quantize(Decimal("1")))
    return int((value * 100).quantize(Decimal("1")))


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm", ".txt"}:
        return path.read_text(encoding="utf-8"), "text"
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise ValueError("pypdf is required for PDF parsing") from exc
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages), "pypdf"
    raise ValueError(f"unsupported official source: {path}")


def parse_official_prices_text(text: str, source_url: str) -> OfficialPrices:
    prices: dict[str, dict[str, int | str]] = {}
    for match in PRICE_RE.finditer(text):
        label = match.group("label").lower()
        key = "petrol_95" if "95" in label else "petrol_93"
        prices[key] = {
            "coastal_cents_per_litre": normalize_price_to_cents(match.group("coastal")),
            "inland_cents_per_litre": normalize_price_to_cents(match.group("inland")),
        }
    date_match = DATE_RE.search(text)
    effective_date = date_match.group(1) if date_match else None
    return OfficialPrices(
        effective_date=effective_date,
        publication_date=effective_date,
        prices=prices,
        source_url=source_url,
        parser_used="regex",
        snippet=text[:500],
    )


def parse_official_prices(path: Path, source_url: str) -> OfficialPrices:
    text, parser_used = extract_text(path)
    parsed = parse_official_prices_text(text, source_url)
    parsed.parser_used = parser_used
    return parsed
