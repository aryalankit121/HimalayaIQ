"""Validation also runs outside Streamlit, so tests and future callers are protected."""

import math

from .models import EXPERIENCE_LEVELS, INTERESTS, Preferences, Trek


def finite_number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def validate_preferences(preferences: Preferences) -> None:
    errors = []
    if type(preferences.days) is not int or not 1 <= preferences.days <= 60:
        errors.append("Available days must be a whole number from 1 to 60.")
    if not finite_number(preferences.budget) or not 1 <= preferences.budget <= 50000:
        errors.append("Package budget must be between $1 and $50,000 USD per person.")
    if preferences.experience not in EXPERIENCE_LEVELS:
        errors.append("Choose a listed experience level.")
    if type(preferences.month) is not int or not 1 <= preferences.month <= 12:
        errors.append("Choose a valid travel month.")
    if not isinstance(preferences.interests, (list, tuple)) or any(
        interest not in INTERESTS for interest in preferences.interests
    ):
        errors.append("Choose interests from the listed options.")
    if errors:
        raise ValueError(" ".join(errors))


def validate_trek(trek: Trek) -> None:
    """Reject invalid seed records before replacing the database contents."""
    for name in ("id", "name", "region", "difficulty", "summary", "altitude_note",
                 "itinerary_note", "cost_note", "weather_location"):
        if not isinstance(getattr(trek, name), str) or not getattr(trek, name).strip():
            raise ValueError(f"Missing trek field: {name}")
    for name in ("cultural_highlights", "considerations"):
        values = getattr(trek, name)
        if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError(f"Invalid {name}: {trek.name}")
    if not isinstance(trek.elevation_points, list):
        raise ValueError(f"Invalid elevation points: {trek.name}")
    for point in trek.elevation_points:
        if (not isinstance(point, dict) or not isinstance(point.get("place"), str)
                or not point["place"].strip() or not finite_number(point.get("altitude_m"))
                or not 0 < point["altitude_m"] < 9000):
            raise ValueError(f"Invalid elevation point: {trek.name}")
    if not (type(trek.days_min) is int and type(trek.days_max) is int
            and 1 <= trek.days_min <= trek.days_max <= 60):
        raise ValueError(f"Invalid duration: {trek.name}")
    if not (finite_number(trek.cost_min) and finite_number(trek.cost_max)
            and 0 < trek.cost_min <= trek.cost_max):
        raise ValueError(f"Invalid cost range: {trek.name}")
    if type(trek.max_altitude_m) is not int or not 0 < trek.max_altitude_m < 9000:
        raise ValueError(f"Invalid altitude: {trek.name}")
    if trek.experience not in EXPERIENCE_LEVELS:
        raise ValueError(f"Invalid experience: {trek.name}")
    if not isinstance(trek.preferred_months, list) or not trek.preferred_months or any(
        type(month) is not int or not 1 <= month <= 12 for month in trek.preferred_months
    ):
        raise ValueError(f"Invalid months: {trek.name}")
    if not isinstance(trek.interests, list) or not trek.interests or any(
        interest not in INTERESTS for interest in trek.interests
    ):
        raise ValueError(f"Invalid interests: {trek.name}")
    if not (finite_number(trek.latitude) and -90 <= trek.latitude <= 90
            and finite_number(trek.longitude) and -180 <= trek.longitude <= 180):
        raise ValueError(f"Invalid coordinates: {trek.name}")
    if not isinstance(trek.sources, list) or not trek.sources or any(
        not isinstance(source, dict) or not all(
            isinstance(source.get(key), str) and source[key]
            for key in ("title", "url", "accessed", "supports")
        ) or not source["url"].startswith("https://") for source in trek.sources
    ):
        raise ValueError(f"Missing source references: {trek.name}")
