# Petrol Timing Widget Data Pipeline

Free, repo-only fuel data generation for an iOS app and WidgetKit extension.

## What it does

- Discovers the latest CEF daily Basic Fuel Price PDF and monthly press release.
- Parses the CEF over/under-recovery row into a directional forecast (cents).
- Applies the official monthly cents adjustment to the last known coastal/inland pump prices.
- Validates values before publishing.
- Preserves the last known-good `public/fuel-data.json` by failing instead of overwriting on bad data.
- Supports manual override via `data/manual-override.json`.
- Runs daily on GitHub Actions (`06:15 UTC`) and commits updated JSON.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_fuel_data.py
python -m unittest discover -s tests -p 'test_*.py'
```

By default, local runs may fall back to `data/fixtures/` when discovery or download fails.

To force a live scrape locally (same as CI):

```bash
ALLOW_FIXTURE_FALLBACK=0 python scripts/update_fuel_data.py
```

Optional environment variables:

- `OFFICIAL_PRICES_URL` — pin a press-release PDF / gov.za HTML URL (skips discovery)
- `FORECAST_URL` — pin a CEF daily PDF URL (skips discovery)
- `SECONDARY_VALIDATION_URL` — unused for validation today (AA placeholder)
- `CEF_DAILY_INDEX_URL` / `CEF_MONTHLY_INDEX_URL` — override listing pages
- `ALLOW_FIXTURE_FALLBACK` — `1` allow fixtures, `0` fail closed

## Sources

Hardcoded listing pages (not secrets):

- Forecast: [CEF Daily Basic Fuel Price](https://cefgroup.co.za/daily-basic-fuel-price/) → newest `Daily-DD-MM-YYYY.pdf`
- Official adjustment: [CEF Monthly Press Release](https://cefgroup.co.za/monthly-press-release/) → newest press-release PDF (same figures as the DMPR/gov.za statement)

Diesel **0.005% sulphur** maps to `diesel_50ppm`. Do not use the 0.05% column.

## Inspect workflow failures

- Open the `Update fuel data` workflow in GitHub Actions.
- Read the failing parser or validation message from the `Update fuel data` step.
- Download the `fuel-data-raw-sources` artifact for the downloaded PDF/HTML that failed.
- Raw files are **not** committed (they change daily and would bloat the repo).

## Manual override

Edit [data/manual-override.json](data/manual-override.json) and set `enabled` to `true`.

- `prices` replaces parsed prices.
- `forecast` overrides parsed forecast fields.
- The script still attempts normal parsing and logs failures.

## Parsing rules

Official announcements are delta-based:

- Parse `52.00 c/l decrease` / `123.44 c/l increase` style lines.
- If the announcement effective date is new, add that signed change to the last coastal and inland values.
- If the effective date already matches the published JSON, keep prices (mid-month re-runs).

Forecast parsing inverts CEF recovery:

- Over-recovery `+126.4` → estimated change `-126c`
- Under-recovery is expected to raise pump prices

Absolute label parsing (`Petrol 95 Coastal … Inland …`) remains for the small HTML/TXT fixtures used in unit tests.

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
- The forecast logic trusts CEF’s average unit over/under-recovery for the current review period.
- The GitHub repo must be **public** for the iOS app’s raw.githubusercontent.com URL to work without auth.
- Scheduled Actions only run from the remote default branch — push the workflow, then use **Run workflow** once to verify.
