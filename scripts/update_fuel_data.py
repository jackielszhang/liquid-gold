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
from scripts.fetch_sources import safe_download
from scripts.sources import aa, cef, dmre
from scripts.validate_data import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
RAW_DIR = ROOT / "data" / "raw"
FIXTURES_DIR = ROOT / "data" / "fixtures"


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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


def _download_or_fixture(url: str | None, bucket: str) -> Path:
    download = safe_download(url, RAW_DIR)
    return download.path if download else _fallback_file(bucket)


def _merge_forecast(candidate: dict, previous: dict | None) -> dict:
    if candidate.get("petrol_95_estimated_change_cents") is not None:
        return candidate
    previous_forecast = (previous or {}).get("forecast", {})
    if previous_forecast.get("as_of_date"):
        age = (date.today() - datetime.strptime(previous_forecast["as_of_date"], "%Y-%m-%d").date()).days
        if age < 3:
            return deepcopy(previous_forecast)
    return {
        "petrol_95_estimated_change_cents": None,
        "direction": "unknown",
        "confidence": "unknown",
        "as_of_date": None,
    }


def build_dataset(previous: dict | None = None) -> tuple[dict, list[str]]:
    logs: list[str] = []
    official_url = os.getenv("OFFICIAL_PRICES_URL", "")
    forecast_url = os.getenv("FORECAST_URL", "")
    secondary_url = os.getenv("SECONDARY_VALIDATION_URL", "")

    official_path = _download_or_fixture(official_url, "official")
    forecast_path = _download_or_fixture(forecast_url, "forecast")
    secondary_path = _download_or_fixture(secondary_url, "secondary")

    official_result = dmre.parse(official_path, official_url or official_path.name)
    forecast_result = cef.parse(forecast_path, forecast_url or forecast_path.name)
    secondary_result = aa.parse(secondary_path, secondary_url or secondary_path.name)

    if not official_result.ok:
        logs.append(f"official_prices failed: {official_result.error}")
        raise RuntimeError("\n".join(logs))

    forecast_payload = forecast_result.payload if forecast_result.ok else {}
    if not forecast_result.ok:
        logs.append(f"forecast failed: {forecast_result.error}")

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
        "prices": official_result.payload["prices"],
        "forecast": _merge_forecast(forecast_payload, previous),
        "recommendation": {},
        "sources": {
            "official_prices_url": official_result.source_url,
            "forecast_url": forecast_result.source_url or "",
            "validation_url": secondary_result.source_url or "",
        },
    }
    for values in dataset["prices"].values():
        values["effective_date"] = official_result.payload["effective_date"]
    dataset["recommendation"] = calculate_recommendation(dataset["forecast"])
    return dataset, logs


def apply_manual_override(dataset: dict, override: dict) -> dict:
    if not override.get("enabled"):
        return dataset
    merged = deepcopy(dataset)
    if override.get("prices"):
        merged["prices"] = override["prices"]
    if override.get("forecast"):
        merged["forecast"].update(override["forecast"])
    merged["manual_override"] = True
    merged["recommendation"] = calculate_recommendation(merged["forecast"])
    return merged


def append_history(history_path: Path, dataset: dict) -> None:
    history = load_json(history_path, [])
    history.append(
        {
            "last_updated": dataset["last_updated"],
            "prices": dataset["prices"],
            "forecast": dataset["forecast"],
            "recommendation": dataset["recommendation"]["action"],
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
