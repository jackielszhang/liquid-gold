from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


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
