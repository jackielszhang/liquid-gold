"""Build and publish public/fuel-data.json from CEF + DMPR sources.

In CI we fail closed: a download/parse miss leaves the last known-good JSON
untouched. Locally, fixtures keep the pipeline runnable without the network.
"""

from __future__ import annotations

import json
import os
import sys
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.calculate_recommendation import calculate_recommendation
from scripts.fetch_sources import (
    CEF_DAILY_INDEX_URL,
    CEF_MONTHLY_INDEX_URL,
    discover_latest_cef_daily_pdf,
    discover_latest_cef_press_release,
    safe_download,
)
from scripts.sources import aa, cef, dmre
from scripts.validate_data import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
RAW_DIR = ROOT / "data" / "raw"
FIXTURES_DIR = ROOT / "data" / "fixtures"
SUPPORTED_FUELS = {"petrol_95", "diesel_50ppm"}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def allow_fixture_fallback() -> bool:
    """Fixtures are for local/dev only. CI must never publish sample prices."""

    explicit = os.getenv("ALLOW_FIXTURE_FALLBACK")
    if explicit == "0":
        return False
    if explicit == "1":
        return True
    return os.getenv("GITHUB_ACTIONS") != "true"


def next_adjustment_date(today: date) -> str:
    month = today.month + 1
    year = today.year
    if month == 13:
        month = 1
        year += 1
    probe = date(year, month, 1)
    while probe.weekday() != 2:
        probe += timedelta(days=1)
    return probe.isoformat()


def load_manual_override() -> dict:
    return load_json(ROOT / "data" / "manual-override.json", {"enabled": False, "reason": "", "prices": {}, "forecast": {}})


def _fallback_file(name: str) -> Path:
    mapping = {
        "official": FIXTURES_DIR / "official-price-sample.html",
        "forecast": FIXTURES_DIR / "forecast-sample.csv",
        "secondary": FIXTURES_DIR / "secondary-source-sample.txt",
    }
    return mapping[name]


def _resolve_source_url(explicit: str, kind: str) -> str:
    """Env override wins; otherwise discover the latest CEF file from a listing."""

    if explicit:
        return explicit
    if kind == "forecast":
        return discover_latest_cef_daily_pdf(os.getenv("CEF_DAILY_INDEX_URL", CEF_DAILY_INDEX_URL))
    if kind == "official":
        return discover_latest_cef_press_release(os.getenv("CEF_MONTHLY_INDEX_URL", CEF_MONTHLY_INDEX_URL))
    return ""


def _download_or_fixture(url: str | None, bucket: str) -> Path:
    download = safe_download(url, RAW_DIR)
    if download:
        return download.path
    if allow_fixture_fallback():
        return _fallback_file(bucket)
    raise RuntimeError(f"{bucket} download failed for url={url!r} and fixture fallback is disabled")


def _merge_forecast(candidate: dict, previous: dict | None) -> dict:
    if any(candidate.get(key) is not None for key in ("petrol_95_estimated_change_cents", "diesel_50ppm_estimated_change_cents")):
        return candidate
    previous_forecast = (previous or {}).get("forecast", {})
    if previous_forecast.get("as_of_date"):
        age = (date.today() - datetime.strptime(previous_forecast["as_of_date"], "%Y-%m-%d").date()).days
        if age < 3:
            return deepcopy(previous_forecast)
    return {
        "petrol_95_estimated_change_cents": None,
        "diesel_50ppm_estimated_change_cents": None,
        "direction": "unknown",
        "diesel_50ppm_direction": "unknown",
        "confidence": "unknown",
        "as_of_date": None,
    }


def _build_recommendations(dataset: dict) -> dict[str, dict]:
    recommendations: dict[str, dict] = {}
    for fuel_key, prices in dataset["prices"].items():
        if fuel_key not in SUPPORTED_FUELS:
            continue
        recommendations[fuel_key] = calculate_recommendation(
            fuel_key=fuel_key,
            current_prices=prices,
            forecast=dataset["forecast"],
            next_adjustment_date=dataset["next_adjustment_date"],
        )
    return recommendations


def build_dataset(previous: dict | None = None) -> tuple[dict, list[str]]:
    logs: list[str] = []
    official_url_env = os.getenv("OFFICIAL_PRICES_URL", "")
    forecast_url_env = os.getenv("FORECAST_URL", "")
    secondary_url = os.getenv("SECONDARY_VALIDATION_URL", "")

    # Discover live CEF URLs unless the caller pinned a fixture/path via env.
    try:
        official_url = _resolve_source_url(official_url_env, "official") if (official_url_env or not allow_fixture_fallback()) else official_url_env
        forecast_url = _resolve_source_url(forecast_url_env, "forecast") if (forecast_url_env or not allow_fixture_fallback()) else forecast_url_env
    except Exception as exc:
        if allow_fixture_fallback():
            logs.append(f"source discovery failed, using fixtures: {exc}")
            official_url = official_url_env
            forecast_url = forecast_url_env
        else:
            raise RuntimeError(f"source discovery failed: {exc}") from exc

    official_path = _download_or_fixture(official_url, "official")
    forecast_path = _download_or_fixture(forecast_url, "forecast")
    secondary_path = _download_or_fixture(secondary_url, "secondary") if secondary_url else (
        _fallback_file("secondary") if allow_fixture_fallback() else None
    )

    previous_prices = (previous or {}).get("prices")
    official_result = dmre.parse(official_path, official_url or official_path.name, previous_prices=previous_prices)
    forecast_result = cef.parse(forecast_path, forecast_url or forecast_path.name)

    if secondary_path is not None:
        secondary_result = aa.parse(secondary_path, secondary_url or secondary_path.name)
    else:
        secondary_result = aa.parse(_fallback_file("secondary"), "")
        secondary_result.source_url = ""

    if not official_result.ok:
        logs.append(f"official_prices failed: {official_result.error}")
        raise RuntimeError("\n".join(logs))

    forecast_payload = forecast_result.payload if forecast_result.ok else {}
    if not forecast_result.ok:
        logs.append(f"forecast failed: {forecast_result.error}")
        if not allow_fixture_fallback() and not ((previous or {}).get("forecast") or {}).get("as_of_date"):
            # In CI, a brand-new forecast miss with no prior forecast is fatal.
            raise RuntimeError("\n".join(logs + ["forecast required when fixture fallback is disabled"]))

    dataset = {
        "schema_version": 1,
        "last_updated": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "ok",
        "manual_override": False,
        "next_adjustment_date": next_adjustment_date(date.today()),
        "source_status": {
            "official_prices": "ok" if official_result.ok else "error",
            "forecast": "ok" if forecast_result.ok else "error",
        },
        "prices": {
            fuel_key: prices
            for fuel_key, prices in official_result.payload["prices"].items()
            if fuel_key in SUPPORTED_FUELS
        },
        "forecast": _merge_forecast(forecast_payload, previous),
        "recommendation": {},
        "sources": {
            "official_prices_url": official_result.source_url,
            "forecast_url": forecast_result.source_url or "",
            "validation_url": secondary_result.source_url or "",
        },
    }
    for values in dataset["prices"].values():
        if not values.get("effective_date"):
            values["effective_date"] = official_result.payload["effective_date"]
    dataset["recommendation"] = _build_recommendations(dataset)
    return dataset, logs


def apply_manual_override(dataset: dict, override: dict) -> dict:
    if not override.get("enabled"):
        return dataset
    merged = deepcopy(dataset)
    if override.get("prices"):
        merged["prices"] = {
            fuel_key: prices
            for fuel_key, prices in override["prices"].items()
            if fuel_key in SUPPORTED_FUELS
        }
    if override.get("forecast"):
        merged["forecast"].update(override["forecast"])
    merged["manual_override"] = True
    merged["recommendation"] = _build_recommendations(merged)
    return merged


def append_history(history_path: Path, dataset: dict) -> None:
    history = load_json(history_path, [])
    history.append(
        {
            "last_updated": dataset["last_updated"],
            "prices": dataset["prices"],
            "forecast": dataset["forecast"],
            "recommendation": {fuel_key: value["action"] for fuel_key, value in dataset["recommendation"].items()},
        }
    )
    write_json(history_path, history[-90:])


def main() -> int:
    fuel_data_path = PUBLIC_DIR / "fuel-data.json"
    history_path = PUBLIC_DIR / "fuel-data-history.json"
    previous = load_json(fuel_data_path, None)
    manual_override = load_manual_override()
    try:
        dataset, logs = build_dataset(previous)
        dataset = apply_manual_override(dataset, manual_override)
        errors = validate_dataset(dataset, previous)
        if errors:
            raise RuntimeError("\n".join(errors))
        write_json(fuel_data_path, dataset)
        append_history(history_path, dataset)
        for line in logs:
            print(line)
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
