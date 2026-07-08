# Petrol Timing Widget Data Pipeline

Free, repo-only fuel data generation for an iOS app and WidgetKit extension.

## What it does

- Downloads official and forecast source files when URLs are configured.
- Falls back to local fixtures so the pipeline still runs in a fresh repo.
- Parses official prices into integer cents.
- Parses a simple forecast feed into a directional estimate.
- Validates values before publishing.
- Preserves the last known-good `public/fuel-data.json` by failing instead of overwriting on bad data.
- Supports manual override via `data/manual-override.json`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_fuel_data.py
python -m unittest discover -s tests -p 'test_*.py'
```

Optional environment variables:

- `OFFICIAL_PRICES_URL`
- `FORECAST_URL`
- `SECONDARY_VALIDATION_URL`

If they are unset or unreachable, the script uses `data/fixtures/`.

## Update source URLs

Set the three environment variables in GitHub Actions repository variables, or hardcode defaults in [scripts/update_fuel_data.py](/Users/jackiez/Documents/GitHub/Liquid%20Gold/liquid-gold/scripts/update_fuel_data.py:1).

## Inspect workflow failures

- Open the `Update fuel data` workflow in GitHub Actions.
- Read the failing parser or validation message from the `Update fuel data` step.
- Check `data/raw/` for the downloaded source that failed.

## Manual override

Edit [data/manual-override.json](/Users/jackiez/Documents/GitHub/Liquid%20Gold/liquid-gold/data/manual-override.json:1) and set `enabled` to `true`.

- `prices` replaces parsed prices.
- `forecast` overrides parsed forecast fields.
- The script still attempts normal parsing and logs failures.

## Parsing rules

Official parsing is label-based, not table-position-based.

- It looks for `Petrol 95` / `95 ULP` and `Petrol 93` / `93 ULP`.
- It accepts `25.23`, `25,23`, and already-cent-based values like `2523.0`.
- If a PDF layout changes, adjust the regex in [scripts/parse_official_prices.py](/Users/jackiez/Documents/GitHub/Liquid%20Gold/liquid-gold/scripts/parse_official_prices.py:1) or swap the adapter in `scripts/sources/`.

## JSON contract

The app should fetch:

`https://raw.githubusercontent.com/<owner>/<repo>/main/public/fuel-data.json`

Important fields:

- `schema_version`
- `last_updated`
- `status`
- `manual_override`
- `next_adjustment_date`
- `source_status`
- `prices`
- `forecast`
- `recommendation`
- `sources`

All prices are integer cents per litre.

## App behavior

- Cache the last successful JSON locally.
- Show cached data when offline.
- Treat data older than 48 hours as stale in the UI.
- If `status != "ok"`, keep using the cached last known-good payload.

## Limitations

- Forecasts are informational only and not guaranteed.
- The forecast logic is deliberately simple in v1: it trusts the latest directional cents movement from the configured source.
- For production accuracy, point the adapters at real official sources and tighten the source-specific parsers when you have stable sample files.
