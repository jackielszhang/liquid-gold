from __future__ import annotations

from datetime import date, datetime


def validate_current_prices(current: dict, previous: dict | None) -> list[str]:
    errors: list[str] = []
    prices = current.get("prices", {})
    for grade_name, values in current.get("prices", {}).items():
        for key in ("coastal_cents_per_litre", "inland_cents_per_litre"):
            cents = values.get(key)
            if not isinstance(cents, int):
                errors.append(f"{grade_name}.{key} must be an int")
                continue
            if cents <= 0:
                errors.append(f"{grade_name}.{key} cannot be zero")
            if not 1000 <= cents <= 5000:
                errors.append(f"{grade_name}.{key} outside expected range")
            if previous:
                prior = previous.get("prices", {}).get(grade_name, {}).get(key)
                if isinstance(prior, int):
                    delta = abs(cents - prior)
                    if delta > 500:
                        errors.append(f"{grade_name}.{key} changed by more than R5.00/L")
                    if prior and delta / prior > 0.25:
                        errors.append(f"{grade_name}.{key} changed by more than 25%")
    for required_grade in ("petrol_95", "diesel_50ppm"):
        values = prices.get(required_grade, {})
        if not values.get("coastal_cents_per_litre") or not values.get("inland_cents_per_litre"):
            errors.append(f"{required_grade} coastal and inland values are required")
    return errors


def validate_forecast(current: dict, previous: dict | None) -> list[str]:
    forecast = current.get("forecast", {})
    errors: list[str] = []
    for change_key, direction_key in (
        ("petrol_95_estimated_change_cents", "direction"),
        ("diesel_50ppm_estimated_change_cents", "diesel_50ppm_direction"),
    ):
        change = forecast.get(change_key)
        direction = forecast.get(direction_key)
        if change is None:
            continue
        if not -500 <= change <= 500:
            errors.append(f"{change_key} outside expected range")
        expected = "flat"
        if change > 0:
            expected = "up"
        elif change < 0:
            expected = "down"
        if direction != expected:
            errors.append(f"{direction_key} does not match sign")
    if forecast.get("as_of_date"):
        age = (date.today() - datetime.strptime(forecast["as_of_date"], "%Y-%m-%d").date()).days
        if age >= 3 and forecast.get("confidence") != "low":
            errors.append("stale forecast must have low confidence")
    elif previous is None:
        errors.append("forecast date missing")
    return errors


def validate_dataset(current: dict, previous: dict | None) -> list[str]:
    return validate_current_prices(current, previous) + validate_forecast(current, previous)
