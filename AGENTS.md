# Agent guide

## Data flow

`scripts/update_fuel_data.py` is the live pipeline entry point. It discovers and downloads DMPR and CEF sources through `scripts/sources/`, uses the parsers in `scripts/`, validates the dataset, then writes `public/` JSON. Keep `public/` unchanged when required source parsing or validation fails.

The iOS app and widget share models and data loading under `LiquidGoldApple/Shared/`. The app reads `public/v1/latest.json`; integer cents per litre are the price contract across Python and Swift.

## Safe checks

- Python unit tests must use fixtures or mocks. Do not fetch live sources from a unit test.
- `python -m unittest discover -s tests -p 'test_*.py'` runs the Python suite.
- `swift test` runs the shared Swift package tests; it does not build the Xcode app or widget.
- `python scripts/update_fuel_data.py` fetches live sources and writes published data. Run it only when a live update is intended.

See `README.md` for source rules, manual overrides, API details, and app behavior.
