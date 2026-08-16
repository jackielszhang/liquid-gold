"""Publish the free public static API under public/v1/.

Endpoints (GitHub Pages root = public/):
  /v1/latest.json
  /v1/months/{yyyy-mm}.json
  /v1/months/current.json
  /v1/months/previous.json
  /v1/index.json

Retention: current calendar month + previous calendar month only.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path


DISCLAIMER = (
    "Unofficial scrape of public CEF/DMPR figures. Not government data. "
    "Best-effort; may lag or fail if upstream layouts change."
)

SUPPORTED_FUELS = ("petrol_95", "diesel_50ppm")
MONTH_FILE_RE = re.compile(r"^(\d{4})-(\d{2})\.json$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def month_key(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def previous_month_key(value: date) -> str:
    year = value.year
    month = value.month - 1
    if month == 0:
        month = 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def _strip_price_fields(prices: dict) -> dict:
    cleaned: dict[str, dict] = {}
    for fuel_key in SUPPORTED_FUELS:
        raw = prices.get(fuel_key) or {}
        cleaned[fuel_key] = {
            "coastal_cents_per_litre": int(raw["coastal_cents_per_litre"]),
            "inland_cents_per_litre": int(raw["inland_cents_per_litre"]),
        }
    return cleaned


def _forecast_row(forecast: dict) -> dict | None:
    if not forecast or not forecast.get("as_of_date"):
        return None
    return {
        "as_of_date": forecast.get("as_of_date"),
        "petrol_95_estimated_change_cents": forecast.get("petrol_95_estimated_change_cents"),
        "diesel_50ppm_estimated_change_cents": forecast.get("diesel_50ppm_estimated_change_cents"),
        "direction": forecast.get("direction", "unknown"),
        "diesel_50ppm_direction": forecast.get("diesel_50ppm_direction", "unknown"),
        "confidence": forecast.get("confidence", "unknown"),
        "source_url": forecast.get("source_url") or "",
    }


def _effective_date(prices: dict, fallback: str | None = None) -> str | None:
    for fuel_key in SUPPORTED_FUELS:
        value = (prices.get(fuel_key) or {}).get("effective_date")
        if value:
            return value
    return fallback


def build_latest_payload(dataset: dict) -> dict:
    """App-facing latest snapshot — keeps the fuel-data.json field names for clients."""

    return {
        "schema_version": 2,
        "api_version": "v1",
        "disclaimer": DISCLAIMER,
        "last_updated": dataset.get("last_updated") or _utc_now_iso(),
        "generated_at": dataset.get("last_updated") or _utc_now_iso(),
        "status": dataset.get("status", "ok"),
        "manual_override": bool(dataset.get("manual_override")),
        "next_adjustment_date": dataset.get("next_adjustment_date"),
        "source_status": dataset.get("source_status", {}),
        "prices": dataset.get("prices", {}),
        "forecast": dataset.get("forecast", {}),
        "recommendation": dataset.get("recommendation", {}),
        "sources": dataset.get("sources", {}),
    }


def build_month_payload(
    month: str,
    *,
    dataset: dict,
    existing: dict | None = None,
) -> dict:
    """Month pack: official schedule + daily CEF forecast series for that month."""

    existing = existing or {}
    prices = dataset.get("prices") or {}
    forecast = dataset.get("forecast") or {}
    sources = dataset.get("sources") or {}
    adjustments = dataset.get("adjustments") or existing.get("official", {}).get("adjustment_cents") or {}

    official = {
        "effective_date": _effective_date(prices, existing.get("official", {}).get("effective_date")),
        "adjustment_cents": {
            fuel_key: int(adjustments[fuel_key])
            for fuel_key in SUPPORTED_FUELS
            if fuel_key in adjustments and adjustments[fuel_key] is not None
        },
        "prices": _strip_price_fields(prices),
        "source_url": sources.get("official_prices_url") or existing.get("official", {}).get("source_url") or "",
    }

    # Keep prior daily rows, then upsert today's forecast by as_of_date.
    daily: list[dict] = list(existing.get("daily_forecasts") or [])
    row = _forecast_row(forecast)
    if row and str(row["as_of_date"]).startswith(month):
        daily = [item for item in daily if item.get("as_of_date") != row["as_of_date"]]
        daily.append(row)
        daily.sort(key=lambda item: item.get("as_of_date") or "")

    return {
        "schema_version": 2,
        "api_version": "v1",
        "month": month,
        "generated_at": _utc_now_iso(),
        "disclaimer": DISCLAIMER,
        "official": official,
        "daily_forecasts": daily,
    }


def build_index_payload(
    *,
    current_month: str,
    previous_month: str,
    available_months: list[str],
    generated_at: str,
) -> dict:
    return {
        "schema_version": 2,
        "api_version": "v1",
        "generated_at": generated_at,
        "disclaimer": DISCLAIMER,
        "available_months": available_months,
        "current_month": current_month,
        "previous_month": previous_month,
        "links": {
            "latest": "./latest.json",
            "current_month": "./months/current.json",
            "previous_month": "./months/previous.json",
            "openapi": "./openapi.json",
            "months": {
                month: f"./months/{month}.json"
                for month in available_months
            },
        },
        "attribution": {
            "official_adjustments": "Department of Mineral and Petroleum Resources / CEF monthly press releases",
            "daily_forecasts": "Central Energy Fund (CEF) Daily Basic Fuel Price PDFs",
        },
    }


def list_month_files(months_dir: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not months_dir.exists():
        return found
    for path in months_dir.iterdir():
        if not path.is_file():
            continue
        match = MONTH_FILE_RE.match(path.name)
        if match:
            found[f"{match.group(1)}-{match.group(2)}"] = path
    return found


def enforce_two_month_retention(months_dir: Path, keep: set[str]) -> list[str]:
    """Delete month packs older than the rolling 2-month window."""

    removed: list[str] = []
    for month, path in list_month_files(months_dir).items():
        if month not in keep:
            path.unlink(missing_ok=True)
            removed.append(month)
    return removed


def publish_v1_api(public_dir: Path, dataset: dict, today: date | None = None) -> dict:
    """Write all v1 endpoints and prune history beyond current+previous month."""

    today = today or date.today()
    current = month_key(today)
    previous = previous_month_key(today)

    v1_dir = public_dir / "v1"
    months_dir = v1_dir / "months"
    months_dir.mkdir(parents=True, exist_ok=True)

    latest = build_latest_payload(dataset)
    write_json(v1_dir / "latest.json", latest)

    existing_current = load_json(months_dir / f"{current}.json", None)
    current_payload = build_month_payload(current, dataset=dataset, existing=existing_current)
    write_json(months_dir / f"{current}.json", current_payload)

    # Previous month: keep on disk if present; otherwise leave a stub only when
    # we can infer official prices from an already-applied prior effective date.
    previous_path = months_dir / f"{previous}.json"
    previous_payload = load_json(previous_path, None)
    if previous_payload is None:
        # Do not invent a previous month. Other builders see it missing from index.
        pass
    else:
        write_json(previous_path, previous_payload)

    write_json(months_dir / "current.json", current_payload)
    if previous_payload is not None:
        write_json(months_dir / "previous.json", previous_payload)
    elif (months_dir / "previous.json").exists():
        # Alias would be stale after a month roll — remove it.
        (months_dir / "previous.json").unlink()

    removed = enforce_two_month_retention(months_dir, {current, previous})

    available = sorted(list_month_files(months_dir))
    index = build_index_payload(
        current_month=current,
        previous_month=previous,
        available_months=available,
        generated_at=latest["generated_at"],
    )
    write_json(v1_dir / "index.json", index)

    return {
        "current_month": current,
        "previous_month": previous,
        "available_months": available,
        "removed_months": removed,
    }
