# Liquid Gold

South African fuel-timing app: **fill now, or wait for the next adjustment**.

The repo is two parts that share one JSON contract:

1. A Python pipeline that publishes `public/fuel-data.json`
2. An iOS app + widget that fetches that file and answers for Petrol 95 or Diesel 50ppm, coastal or inland

The published payload is:

`https://raw.githubusercontent.com/jackielszhang/liquid-gold/main/public/fuel-data.json`

All prices are **integer cents per litre**. Formatting to rands happens in the app, not in the pipeline.

## Repo layout

```text
scripts/                 pipeline: fetch, parse, recommend, validate, publish
data/fixtures/           offline samples used when source URLs are unset
data/manual-override.json  operator fallback; keep enabled=false unless you mean it
public/fuel-data.json    current payload the app downloads
public/fuel-data-history.json  last ~90 successful publishes
LiquidGoldApple/         iOS app, widget, and shared models
Package.swift            Swift tests for the shared models
```

## Recommendation rules

The official SA price usually changes on the **first Wednesday of the month**. The pipeline computes that date itself instead of scraping a calendar.

| Estimated move | Action | Best fill day |
| --- | --- | --- |
| down 30c/L or more | `wait` | adjustment Wednesday |
| up 30c/L or more | `fill_now` | day before Wednesday |
| inside 30c/L | `fill_normally` | adjustment Wednesday |
| no forecast | `unknown` | none |

30c/L is the product cutoff, not a rounding artifact. Smaller moves are treated as noise relative to a tank of fuel.

Petrol 93 can still appear in a source file. It is parsed, then dropped. The app only offers petrol 95 and diesel 50ppm.

## Data pipeline

GitHub Actions runs [`.github/workflows/update-fuel-data.yml`](.github/workflows/update-fuel-data.yml) daily at 06:15 UTC.

```text
download or fixture
        │
        ├─ DMRE adapter  → official coastal / inland cents
        ├─ CEF adapter   → estimated next-month cents move
        └─ AA adapter    → stored snippet only in v1
        │
        ├─ skip publish if official prices fail
        ├─ keep a <3-day-old forecast if the live scrape is blank
        ├─ apply data/manual-override.json if enabled
        ├─ validate ranges, jumps, and forecast sign
        └─ write public/*.json  (or exit 1 and leave the old file)
```

Source URLs are optional environment variables / GitHub Actions variables:

- `OFFICIAL_PRICES_URL`
- `FORECAST_URL`
- `SECONDARY_VALIDATION_URL`

If they are unset or unreachable, the pipeline uses `data/fixtures/` so a fresh clone still produces JSON.

Official parsing is **label-based**, not table-column-based. It looks for `Petrol 95` / `95 ULP` and `Diesel 50ppm`, and accepts `25.23`, `25,23`, or already-cent values like `2523.0`.

### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/update_fuel_data.py
python -m unittest discover -s tests -p 'test_*.py'
```

### Manual override

Edit [`data/manual-override.json`](data/manual-override.json) and set `enabled` to `true`.

- `prices` replaces parsed prices for the supported fuels
- `forecast` overlays the parsed forecast fields
- Parsers still run and failures are logged; override is the last word

Use this when a source layout broke and you already know the correct cents. Turn it off again once the adapter is fixed.

### Inspect workflow failures

- Open the `Update fuel data` workflow in GitHub Actions
- Read the parser or validation message from the `Update fuel data` step
- Check `data/raw/` for the downloaded source that failed
- A failed run must not commit a new `public/fuel-data.json`

## iOS app

`LiquidGoldApple/` is the client:

- **App** asks for region, fuel, and tank size once
- **Shared models** decode the published JSON and build a snapshot
- **Widget** shows the same snapshot from the same app-group cache
- Fetch order is **remote → cache → bundled sample**
- Data older than 48 hours is marked stale in the UI

Shared library tests:

```bash
swift test
```

The widget refreshes about every six hours. Official prices do not move faster than that, so polling more often would not change the answer.

Remote URL and app group are in [`LiquidGoldApple/Shared/AppConfig.swift`](LiquidGoldApple/Shared/AppConfig.swift). If the GitHub owner or default branch changes, update that URL.

Visual language: near-white field, 2px black hardware edges, LCD numerals, and one signal-orange accent. See [`design.md`](design.md).

## JSON contract

Important fields in `public/fuel-data.json`:

- `schema_version`
- `last_updated`
- `status`
- `manual_override`
- `next_adjustment_date`
- `source_status`
- `prices.petrol_95` / `prices.diesel_50ppm`
- `forecast` including `petrol_95_estimated_change_cents` and `diesel_50ppm_estimated_change_cents`
- `recommendation` keyed by fuel
- `sources`

`recommendation.<fuel>.action` is one of `wait`, `fill_now`, `fill_normally`, `unknown`.

## Limitations

- Forecasts are informational. The v1 CEF path trusts the latest directional cents in a CSV; it is not a model.
- The AA adapter does not yet cross-check prices.
- Until `OFFICIAL_PRICES_URL` and `FORECAST_URL` are set, published JSON is fixture-based.
- For production, point those adapters at live official sources and tighten the parsers against real sample files.
