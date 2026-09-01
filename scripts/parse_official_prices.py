"""Official price parsing — absolute fixtures, or monthly adjustment announcements.

Production sources (gov.za HTML or CEF press-release PDF) publish the monthly
cents change, not a full coastal/inland table. We apply that signed change to
the last known pump prices when the effective date is new.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


PRICE_RE = re.compile(
    r"(?P<label>petrol\s*95|95\s*ulp|petrol\s*93|93\s*ulp|diesel\s*50\s*ppm|50\s*ppm\s*diesel).*?"
    r"(?P<coastal>\d{1,4}(?:[.,]\d{1,2})?)\D+"
    r"(?P<inland>\d{1,4}(?:[.,]\d{1,2})?)",
    re.IGNORECASE | re.DOTALL,
)
DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2}|(?:\d{1,2}\s+\w+\s+20\d{2}))")

# gov.za: "Petrol 95 (ULP &LRP): Fifty-two cents per litre (52.00 c/l) decrease."
GOVZA_ADJUST_RE = re.compile(
    r"(?P<label>Petrol\s*95|Petrol\s*93|Diesel\s*\(0\.005%\s*sulphur\)|Diesel\s*\(0\.05%\s*sulphur\))"
    r".{0,160}?\((?P<cents>\d+(?:[.,]\d+)?)?\s*c/l\)\s*(?P<direction>decrease|increase)",
    re.IGNORECASE | re.DOTALL,
)

# CEF press release section 1:
#   "Both grades of Petrol 93 & 95 (LRP & ULP) ( 134.000) cents per litre increase"
#   "Diesel 0.005% Sulphur ( 314.900) cents per litre increase"
# Parentheses around the cents are optional — August 2026 omitted them on petrol
# (`52.000 cents`) while September 2026 wrapped them (`( 134.000) cents`).
CEF_PETROL_ADJUST_RE = re.compile(
    r"Petrol\s*93\s*&\s*95.{0,120}?\(?\s*(?P<cents>\d+(?:[.,]\d+)?)\)?\s*cents\s+per\s+litre\s+"
    r"(?P<direction>decrease|increase)",
    re.IGNORECASE | re.DOTALL,
)
CEF_DIESEL_ADJUST_RE = re.compile(
    r"Diesel\s*0\.005%\s*Sulphur\s*\(?\s*(?P<cents>\d+(?:[.,]\d+)?)\)?\s*cents\s+per\s+litre\s+"
    r"(?P<direction>decrease|increase)",
    re.IGNORECASE,
)

EFFECTIVE_DATE_RE = re.compile(
    r"(?:effective\s+from|effected\s+on|price\s+changes\s+to\s+be\s+effected\s+on)\s+"
    r"(?:wednesday\s+|monday\s+|tuesday\s+|thursday\s+|friday\s+)?"
    r"(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?P<month>[A-Za-z]+)\s+(?P<year>20\d{2})",
    re.IGNORECASE,
)
EFFECTIVE_SLASH_RE = re.compile(
    r"(?:FOR THE PERIOD|effective)\s+(\d{2})/(\d{2})/(\d{4})",
    re.IGNORECASE,
)

MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

# Seed used only when there is no previous published payload yet.
BOOTSTRAP_PRICES = {
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


@dataclass
class OfficialPrices:
    effective_date: str | None
    publication_date: str | None
    prices: dict[str, dict[str, int | str]]
    source_url: str
    parser_used: str
    snippet: str
    adjustments: dict[str, int] | None = None


@dataclass
class PriceAdjustments:
    effective_date: str | None
    changes: dict[str, int]
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


def _strip_html(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", without_tags)


def _month_name_to_iso(day: int, month_name: str, year: int) -> str:
    month = MONTH_NAMES.get(month_name.lower())
    if not month:
        raise ValueError(f"unknown month {month_name!r}")
    return f"{year:04d}-{month:02d}-{day:02d}"


def _signed_cents(cents_raw: str, direction: str) -> int:
    cents = int(Decimal(cents_raw.replace(",", ".")).quantize(Decimal("1")))
    if direction.lower().startswith("decrease"):
        return -cents
    return cents


def parse_price_adjustments_text(text: str) -> PriceAdjustments:
    """Extract monthly cents changes from a DMPR/gov.za or CEF announcement."""

    cleaned = _strip_html(text)
    changes: dict[str, int] = {}

    for match in GOVZA_ADJUST_RE.finditer(cleaned):
        label = match.group("label").lower()
        cents_raw = match.group("cents")
        if not cents_raw:
            continue
        signed = _signed_cents(cents_raw, match.group("direction"))
        if "95" in label:
            changes["petrol_95"] = signed
        elif "93" in label:
            changes["petrol_93"] = signed
        elif "0.005" in label:
            changes["diesel_50ppm"] = signed
        elif "0.05" in label:
            changes["diesel_500ppm"] = signed

    petrol_match = CEF_PETROL_ADJUST_RE.search(cleaned)
    if petrol_match and "petrol_95" not in changes:
        signed = _signed_cents(petrol_match.group("cents"), petrol_match.group("direction"))
        changes["petrol_95"] = signed
        changes["petrol_93"] = signed

    diesel_match = CEF_DIESEL_ADJUST_RE.search(cleaned)
    if diesel_match and "diesel_50ppm" not in changes:
        changes["diesel_50ppm"] = _signed_cents(
            diesel_match.group("cents"),
            diesel_match.group("direction"),
        )

    effective_date: str | None = None
    date_match = EFFECTIVE_DATE_RE.search(cleaned)
    if date_match:
        effective_date = _month_name_to_iso(
            int(date_match.group("day")),
            date_match.group("month"),
            int(date_match.group("year")),
        )
    else:
        slash_match = EFFECTIVE_SLASH_RE.search(cleaned)
        if slash_match:
            day, month, year = map(int, slash_match.groups())
            effective_date = f"{year:04d}-{month:02d}-{day:02d}"

    parser_used = "adjustment"
    if not changes:
        raise ValueError("no fuel price adjustments found in announcement")

    return PriceAdjustments(
        effective_date=effective_date,
        changes=changes,
        parser_used=parser_used,
        snippet=cleaned[:500],
    )


def apply_adjustments_to_prices(
    previous_prices: dict[str, dict] | None,
    adjustments: PriceAdjustments,
) -> dict[str, dict[str, int | str]]:
    """Apply a monthly cents change to the last coastal/inland values.

    SA adjustments are the same cents in every zone, so coastal and inland
    both move by the signed change. If the announcement effective date already
    matches the published prices, keep them (mid-month re-runs).
    """

    base = previous_prices or BOOTSTRAP_PRICES
    effective = adjustments.effective_date

    # Already applied this month — do not double-count the delta.
    sample = next(iter(base.values()), {})
    if effective and sample.get("effective_date") == effective:
        return {
            fuel_key: {
                "coastal_cents_per_litre": int(values["coastal_cents_per_litre"]),
                "inland_cents_per_litre": int(values["inland_cents_per_litre"]),
                "effective_date": values.get("effective_date") or effective,
            }
            for fuel_key, values in base.items()
            if fuel_key in {"petrol_95", "diesel_50ppm"}
        }

    updated: dict[str, dict[str, int | str]] = {}
    for fuel_key in ("petrol_95", "diesel_50ppm"):
        prior = base.get(fuel_key) or BOOTSTRAP_PRICES[fuel_key]
        delta = adjustments.changes.get(fuel_key)
        if delta is None:
            # No delta for this grade — keep prior absolute values.
            coastal = int(prior["coastal_cents_per_litre"])
            inland = int(prior["inland_cents_per_litre"])
        else:
            coastal = int(prior["coastal_cents_per_litre"]) + delta
            inland = int(prior["inland_cents_per_litre"]) + delta
        updated[fuel_key] = {
            "coastal_cents_per_litre": coastal,
            "inland_cents_per_litre": inland,
            "effective_date": effective or prior.get("effective_date") or "",
        }
    return updated


def looks_like_adjustment_announcement(text: str) -> bool:
    cleaned = _strip_html(text).lower()
    return ("c/l" in cleaned or "cents per litre" in cleaned) and (
        "decrease" in cleaned or "increase" in cleaned
    )


def extract_text(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    head = path.read_bytes()[:8]

    # Magic-byte detection beats a missing / wrong URL extension.
    if head.startswith(b"%PDF") or suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ModuleNotFoundError as exc:
            raise ValueError("pypdf is required for PDF parsing") from exc
        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages), "pypdf"

    if suffix in {".html", ".htm", ".txt"} or head.lstrip().startswith((b"<", b"<!")):
        return path.read_text(encoding="utf-8"), "text"

    # Last resort: treat as UTF-8 text (gov.za pages sometimes lack an extension).
    try:
        return path.read_text(encoding="utf-8"), "text"
    except UnicodeDecodeError as exc:
        raise ValueError(f"unsupported official source: {path}") from exc


def parse_official_prices_text(text: str, source_url: str) -> OfficialPrices:
    prices: dict[str, dict[str, int | str]] = {}
    for match in PRICE_RE.finditer(text):
        label = match.group("label").lower()
        if "diesel" in label:
            key = "diesel_50ppm"
        else:
            key = "petrol_95" if "95" in label else "petrol_93"
        prices[key] = {
            "coastal_cents_per_litre": normalize_price_to_cents(match.group("coastal")),
            "inland_cents_per_litre": normalize_price_to_cents(match.group("inland")),
        }
    date_match = DATE_RE.search(text)
    effective_date = date_match.group(1) if date_match else None

    # Normalize "1 July 2026" → ISO when possible.
    if effective_date and not re.match(r"20\d{2}-\d{2}-\d{2}", effective_date):
        try:
            effective_date = datetime.strptime(effective_date, "%d %B %Y").date().isoformat()
        except ValueError:
            try:
                effective_date = datetime.strptime(effective_date, "%d %b %Y").date().isoformat()
            except ValueError:
                pass

    return OfficialPrices(
        effective_date=effective_date,
        publication_date=effective_date,
        prices=prices,
        source_url=source_url,
        parser_used="regex",
        snippet=text[:500],
    )


def parse_official_prices(
    path: Path,
    source_url: str,
    previous_prices: dict[str, dict] | None = None,
) -> OfficialPrices:
    text, parser_used = extract_text(path)

    if looks_like_adjustment_announcement(text):
        adjustments = parse_price_adjustments_text(text)
        prices = apply_adjustments_to_prices(previous_prices, adjustments)
        return OfficialPrices(
            effective_date=adjustments.effective_date,
            publication_date=adjustments.effective_date,
            prices=prices,
            source_url=source_url,
            parser_used=f"{parser_used}+adjustment",
            snippet=adjustments.snippet,
            adjustments=adjustments.changes,
        )

    parsed = parse_official_prices_text(text, source_url)
    parsed.parser_used = parser_used
    return parsed
