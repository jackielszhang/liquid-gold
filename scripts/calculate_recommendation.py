from __future__ import annotations

from datetime import date, datetime, timedelta


def _change_key(fuel_key: str) -> str:
    return f"{fuel_key}_estimated_change_cents"


def _fuel_label(fuel_key: str) -> str:
    labels = {
        "petrol_95": "Petrol 95",
        "diesel_50ppm": "Diesel 50ppm",
    }
    return labels.get(fuel_key, fuel_key.replace("_", " ").title())


def _day_before(iso_date: str) -> str:
    return (datetime.strptime(iso_date, "%Y-%m-%d").date() - timedelta(days=1)).isoformat()


def calculate_recommendation(
    fuel_key: str,
    current_prices: dict[str, int | str],
    forecast: dict,
    next_adjustment_date: str,
) -> dict[str, str | int | None]:
    change = forecast.get(_change_key(fuel_key))
    fuel_label = _fuel_label(fuel_key)
    if change is None:
        return {
            "action": "unknown",
            "headline": "Forecast unavailable",
            "body": "Current price is available, but the next adjustment is still unclear.",
            "reason": f"No recent {fuel_label.lower()} forecast could be parsed.",
            "best_fill_up_date": None,
            "next_price_cents_per_litre": None,
            "change_cents_per_litre": None,
        }
    next_price = {
        "coastal_cents_per_litre": int(current_prices["coastal_cents_per_litre"]) + change,
        "inland_cents_per_litre": int(current_prices["inland_cents_per_litre"]) + change,
    }
    if change <= -30:
        return {
            "action": "wait",
            "headline": "Wait if you can",
            "body": "A lower price is currently estimated for the next adjustment.",
            "reason": f"{fuel_label} is currently estimated to decrease by about {abs(change)}c/L.",
            "best_fill_up_date": next_adjustment_date,
            "next_price_cents_per_litre": next_price,
            "change_cents_per_litre": change,
        }
    if change >= 30:
        return {
            "action": "fill_now",
            "headline": "Fill before the next change",
            "body": "A higher price is currently estimated for the next adjustment.",
            "reason": f"{fuel_label} is currently estimated to increase by about {change}c/L.",
            "best_fill_up_date": _day_before(next_adjustment_date),
            "next_price_cents_per_litre": next_price,
            "change_cents_per_litre": change,
        }
    return {
        "action": "fill_normally",
        "headline": "No strong price signal",
        "body": "The next adjustment currently looks close enough to flat.",
        "reason": f"The current {fuel_label.lower()} estimate is within 30c/L of flat.",
        "best_fill_up_date": next_adjustment_date,
        "next_price_cents_per_litre": next_price,
        "change_cents_per_litre": change,
    }
