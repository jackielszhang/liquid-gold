# Petrol Timing Widget Data Pipeline

Free, repo-only fuel data generation for an iOS app and WidgetKit extension — plus a public static JSON API.

## Public API (v1)

Base URL (GitHub Pages):

`https://jackielszhang.github.io/liquid-gold/v1`

| Endpoint | What it returns |
|---|---|
| [`/latest.json`](public/v1/latest.json) | Current prices + forecast + recommendation |
| [`/months/current.json`](public/v1/months/current.json) | This calendar month |
| [`/months/previous.json`](public/v1/months/previous.json) | Last calendar month |
| `/months/{yyyy-mm}.json` | Specific month pack |
| [`/index.json`](public/v1/index.json) | Discovery + attribution |
| [`/openapi.json`](public/v1/openapi.json) | OpenAPI 3 |

**Retention:** current month + previous month only. No long history.

Docs: [public/v1/README.md](public/v1/README.md)

## What the scraper does

- Discovers the current DMPR fuel schedule ZIP and latest CEF daily Basic Fuel Price PDF.
- Parses the CEF over/under-recovery row into a directional forecast (cents).
- Reads Petrol 95 pump prices and Diesel 50ppm wholesale prices from labeled workbook tables.
- Publishes `public/v1/*` and a compat copy at `public/fuel-data.json`.
- Preserves the last known-good files by failing instead of overwriting on bad data.
- Supports manual override via `data/manual-override.json`.
- Runs daily on GitHub Actions (`06:15 UTC`) and commits updated JSON.
- Deploys `public/` to GitHub Pages on pushes to `main`.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_fuel_data.py
python -m unittest discover -s tests -p 'test_*.py'
```

Every pipeline run uses live sources and fails without publishing if discovery, download, parsing, or validation fails. Fixtures are only parser test inputs.

Optional environment variables:

- `OFFICIAL_PRICES_URL` — pin a DMPR schedule ZIP URL (skips discovery)
- `FORECAST_URL` — pin a CEF daily PDF URL (skips discovery)
- `SECONDARY_VALIDATION_URL` — unused for validation today (AA placeholder)
- `CEF_DAILY_INDEX_URL` — override the CEF daily listing page

## Sources

Hardcoded listing pages (not secrets):

- Prices: [DMPR fuel prices](https://www.dmpr.gov.za/Branches/Petroleum-Resources/Fuel-Prices) → current schedule ZIP
- Forecast: [CEF Daily Basic Fuel Price](https://cefgroup.co.za/daily-basic-fuel-price/) → newest `Daily-DD-MM-YYYY.pdf`

Diesel **0.005% sulphur** maps to `diesel_50ppm`. Do not use the 0.05% column.

## Inspect workflow failures

- Open the `Update fuel data` workflow in GitHub Actions.
- Read the failing parser or validation message from the `Update fuel data` step.
- Download the `fuel-data-raw-sources` artifact for the downloaded ZIP or PDF that failed.
- Raw files are **not** committed (they change daily and would bloat the repo).

## Manual override

Edit [data/manual-override.json](data/manual-override.json) and set `enabled` to `true`.

- `prices` replaces parsed prices.
- `forecast` overrides parsed forecast fields.
- The script still attempts normal parsing and logs failures.

## Parsing rules

The official workbook parser checks the sheet, labeled product section, price-column header, and zone code. Zone 1A maps to coastal and zone 9C maps to inland.

Forecast parsing inverts CEF recovery:

- Over-recovery `+126.4` → estimated change `-126c`
- Under-recovery is expected to raise pump prices

Absolute label parsing (`Petrol 95 Coastal … Inland …`) remains for parser fixtures.

## App contract

The iOS app fetches:

`https://jackielszhang.github.io/liquid-gold/v1/latest.json`

Important fields (integer cents per litre):

- `schema_version`, `last_updated`, `status`
- `prices`, `forecast`, `recommendation`, `sources`

Compat copy still written to `public/fuel-data.json` for older clients.

## App behavior

- Cache the last successful JSON locally.
- Show cached data when offline.
- Treat data older than 48 hours as stale in the UI.
- If `status != "ok"`, keep using the cached last known-good payload.

## Limitations

- Forecasts are informational only and not guaranteed.
- The forecast logic trusts CEF’s average unit over/under-recovery for the current review period.
- The GitHub repo must be **public**, and GitHub Pages must be enabled (Actions source), for the public API URL to work.
- Scheduled Actions only run from the remote default branch — push the workflow, then use **Run workflow** once to verify.
