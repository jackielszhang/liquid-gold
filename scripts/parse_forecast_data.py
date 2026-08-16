"""Forecast parsing — fixture CSV for tests, CEF daily PDF for production.

CEF publishes a daily Basic Fuel Price PDF. The row we care about is
AVERAGE UNIT OVER/(UNDER) RECOVERY. Over-recovery means pump prices are too
high relative to the basic fuel price, so the next adjustment is expected to
cut prices. We invert the sign: recovery +126.4 → estimated change -126c.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


# Columns on the CEF daily table, left to right after the label.
CEF_COLUMN_KEYS = (
    "petrol_95",
    "petrol_93",
    "diesel_0_05",
    "diesel_0_005",
    "illuminating_paraffin",
)

# 50ppm diesel is the 0.005% sulphur grade — not 0.05%.
DIESEL_50PPM_COLUMN = "diesel_0_005"

# Skip the DD/MM/YYYY – DD/MM/YYYY date window; only keep decimal recoveries.
AVERAGE_RECOVERY_RE = re.compile(
    r"AVERAGE\s+UNIT\s+OVER/\(UNDER\)\s+RECOVERY\s+"
    r"\d{2}/\d{2}/\d{4}\s*[-–]\s*\d{2}/\d{2}/\d{4}\s+"
    r"(?P<values>[^\n]+)",
    re.IGNORECASE,
)
# Recoveries always include a fractional part (e.g. 126.420 or (60.040)).
RECOVERY_NUMBER_RE = re.compile(r"\(?-?\d{1,4}\.\d+\)?")
DAILY_FILENAME_DATE_RE = re.compile(r"Daily-(\d{2})-(\d{2})-(\d{4})", re.IGNORECASE)
BASIC_FUEL_DATE_RE = re.compile(r"BASIC\s+FUEL\s+PRICE\s*[-–]\s*(\d{2})/(\d{2})/(\d{4})", re.IGNORECASE)


@dataclass
class Forecast:
    as_of_date: str | None
    petrol_95_estimated_change_cents: int | None
    diesel_50ppm_estimated_change_cents: int | None
    direction: str
    diesel_50ppm_direction: str
    confidence: str
    source_url: str


def _direction(change: int | None) -> str:
    if change is None:
        return "unknown"
    if change > 0:
        return "up"
    if change < 0:
        return "down"
    return "flat"


def _parse_decimal(raw: str) -> Decimal:
    try:
        return Decimal(raw.strip().replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"invalid decimal {raw!r}") from exc


def _confidence(latest: date, prior: list[Decimal]) -> str:
    age = (date.today() - latest).days
    if age >= 3:
        return "low"
    direction = {0 if value == 0 else (1 if value > 0 else -1) for value in prior}
    if len(direction) == 1:
        return "high"
    if age <= 2:
        return "medium"
    return "low"


def _parse_cef_number(raw: str) -> Decimal:
    """CEF wraps negatives in parentheses: (60.040) → -60.040."""

    text = raw.strip().replace(" ", "").replace(",", "")
    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1]
    value = _parse_decimal(text)
    return -value if negative else value


def _recovery_to_change_cents(recovery: Decimal) -> int:
    # Over-recovery → price cut; under-recovery → price hike.
    return int((-recovery).quantize(Decimal("1")))


def _as_of_from_path_or_text(path: Path, text: str) -> date:
    filename_match = DAILY_FILENAME_DATE_RE.search(path.name)
    if filename_match:
        day, month, year = map(int, filename_match.groups())
        return date(year, month, day)

    text_match = BASIC_FUEL_DATE_RE.search(text)
    if text_match:
        day, month, year = map(int, text_match.groups())
        return date(year, month, day)

    raise ValueError(f"could not determine CEF as-of date from {path}")


def _extract_pdf_text(path: Path) -> str:
    try:
        import pdfplumber
    except ModuleNotFoundError as exc:
        raise ValueError("pdfplumber is required for CEF PDF parsing") from exc

    chunks: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            chunks.append(page.extract_text() or "")
    text = "\n".join(chunks)
    if not text.strip():
        raise ValueError(f"empty text extracted from {path}")
    return text


def parse_cef_daily_pdf(path: Path, source_url: str) -> Forecast:
    """Parse AVERAGE UNIT OVER/(UNDER) RECOVERY from a CEF daily PDF."""

    text = _extract_pdf_text(path)
    match = AVERAGE_RECOVERY_RE.search(text)
    if not match:
        raise ValueError("AVERAGE UNIT OVER/(UNDER) RECOVERY row not found")

    numbers = [_parse_cef_number(raw) for raw in RECOVERY_NUMBER_RE.findall(match.group("values"))]
    if len(numbers) < 4:
        raise ValueError(f"expected at least 4 recovery values, got {numbers!r}")

    by_column = dict(zip(CEF_COLUMN_KEYS, numbers))
    petrol_recovery = by_column["petrol_95"]
    diesel_recovery = by_column[DIESEL_50PPM_COLUMN]
    petrol_change = _recovery_to_change_cents(petrol_recovery)
    diesel_change = _recovery_to_change_cents(diesel_recovery)
    as_of = _as_of_from_path_or_text(path, text)

    return Forecast(
        as_of_date=as_of.isoformat(),
        petrol_95_estimated_change_cents=petrol_change,
        diesel_50ppm_estimated_change_cents=diesel_change,
        direction=_direction(petrol_change),
        diesel_50ppm_direction=_direction(diesel_change),
        confidence=_confidence(as_of, [petrol_recovery, diesel_recovery]),
        source_url=source_url,
    )


def parse_forecast_csv(path: Path, source_url: str) -> Forecast:
    rows: list[tuple[date, Decimal, Decimal | None]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                (
                    datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    _parse_decimal(row["petrol_95_change_cents"]),
                    _parse_decimal(row["diesel_50ppm_change_cents"]) if row.get("diesel_50ppm_change_cents") else None,
                )
            )
    if not rows:
        return Forecast(None, None, None, "unknown", "unknown", "unknown", source_url)
    rows.sort(key=lambda item: item[0])
    latest_date, latest_petrol, latest_diesel = rows[-1]
    recent_values = [value for _, value, _ in rows[-3:]]
    petrol_change = int(latest_petrol.quantize(Decimal("1")))
    diesel_change = int(latest_diesel.quantize(Decimal("1"))) if latest_diesel is not None else None
    return Forecast(
        as_of_date=latest_date.isoformat(),
        petrol_95_estimated_change_cents=petrol_change,
        diesel_50ppm_estimated_change_cents=diesel_change,
        direction=_direction(petrol_change),
        diesel_50ppm_direction=_direction(diesel_change),
        confidence=_confidence(latest_date, recent_values),
        source_url=source_url,
    )


def parse_forecast(path: Path, source_url: str) -> Forecast:
    """Route by file type: PDF → CEF daily, otherwise fixture CSV."""

    if path.suffix.lower() == ".pdf" or path.read_bytes()[:4] == b"%PDF":
        return parse_cef_daily_pdf(path, source_url)
    return parse_forecast_csv(path, source_url)
