from __future__ import annotations


def calculate_recommendation(forecast: dict) -> dict[str, str]:
    change = forecast.get("petrol_95_estimated_change_cents")
    if change is None:
        return {
            "action": "unknown",
            "headline": "Forecast unavailable",
            "body": "Current price is available. Next-month movement is still unclear.",
            "reason": "No recent forecast could be parsed.",
        }
    if change <= -30:
        return {
            "action": "wait",
            "headline": "Likely cheaper next month",
            "body": "Top up only if you need to.",
            "reason": f"Petrol 95 is currently estimated to decrease by about {abs(change)}c/L.",
        }
    if change >= 30:
        return {
            "action": "fill_now",
            "headline": "Likely more expensive next month",
            "body": "Fill up before the next adjustment.",
            "reason": f"Petrol 95 is currently estimated to increase by about {change}c/L.",
        }
    return {
        "action": "fill_normally",
        "headline": "No big move expected",
        "body": "Fill up when convenient.",
        "reason": "The current estimate is within 30c/L of flat.",
    }
