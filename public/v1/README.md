# Liquid Gold Fuel API (v1)

Unofficial, best-effort South African fuel prices. Free static JSON.

**Base URL:** `https://jackielszhang.github.io/liquid-gold/v1`

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | [`/latest.json`](./latest.json) | Current pump prices + latest CEF forecast + recommendation |
| GET | [`/months/current.json`](./months/current.json) | This calendar month (official + daily forecasts) |
| GET | [`/months/previous.json`](./months/previous.json) | Last calendar month |
| GET | [`/months/{yyyy-mm}.json`](./months/) | Specific month pack |
| GET | [`/index.json`](./index.json) | Discovery + attribution |
| GET | [`/openapi.json`](./openapi.json) | OpenAPI 3 description |

## Retention

Only **current month** and **previous month** are kept. Older month files are deleted by the daily scraper.

## Units

All prices are **integer cents per litre** (e.g. `2558` = R25.58).

`diesel_50ppm` maps to CEF/DMPR **0.005% sulphur** diesel.

## Disclaimer

This is **not** government data. Figures are scraped from public CEF / DMPR sources and may lag or break if upstream layouts change. Always check `status` and `source_status`.

## Example

```bash
curl -s https://jackielszhang.github.io/liquid-gold/v1/latest.json | jq .prices
curl -s https://jackielszhang.github.io/liquid-gold/v1/months/previous.json | jq .official
```
