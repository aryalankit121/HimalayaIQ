"""Real Open-Meteo forecasts, with explicit errors and no synthetic fallback."""

from dataclasses import dataclass
from datetime import date, datetime, timezone
import requests

from .validation import finite_number

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FIELDS = ("temperature_2m_min", "temperature_2m_max", "precipitation_sum")
UNITS = {"temperature_2m_min": "°C", "temperature_2m_max": "°C", "precipitation_sum": "mm"}


class WeatherError(Exception):
    """A readable forecast failure that the interface can handle locally."""


@dataclass
class Forecast:
    rows: list[dict]
    fetched_at: str
    timezone: str
    missing_values: bool


def parse_forecast(payload: dict) -> Forecast:
    try:
        daily = payload["daily"]
        dates = daily["time"]
        if not isinstance(dates, list) or not dates:
            raise ValueError("No forecast dates")
        if payload["timezone"] != "Asia/Kathmandu":
            raise ValueError("Unexpected timezone")
        for key in FIELDS:
            if (not isinstance(daily[key], list) or len(daily[key]) != len(dates)
                    or payload["daily_units"][key] != UNITS[key]):
                raise ValueError("Unexpected series or units")
        parsed_dates = [date.fromisoformat(day) for day in dates]
        if parsed_dates != sorted(set(parsed_dates)):
            raise ValueError("Invalid date order")
        rows, missing = [], False
        for index, day in enumerate(dates):
            row = {"Date": day}
            for key, label in zip(FIELDS, ("Low (°C)", "High (°C)", "Precipitation (mm)")):
                value = daily[key][index]
                if value is not None and not finite_number(value):
                    raise ValueError("Invalid weather value")
                missing = missing or value is None
                row[label] = value
            if row["Precipitation (mm)"] is not None and row["Precipitation (mm)"] < 0:
                raise ValueError("Negative precipitation")
            if row["Low (°C)"] is not None and row["High (°C)"] is not None and row["Low (°C)"] > row["High (°C)"]:
                raise ValueError("Invalid temperature range")
            rows.append(row)
        if all(row[label] is None for row in rows for label in row if label != "Date"):
            raise ValueError("No forecast values")
        return Forecast(rows, datetime.now(timezone.utc).isoformat(timespec="seconds"),
                        payload["timezone"], missing)
    except (KeyError, TypeError, ValueError, AttributeError) as error:
        raise WeatherError("Open-Meteo returned incomplete or unexpected forecast data. Please retry.") from error


def fetch_forecast(latitude: float, longitude: float) -> Forecast:
    if not (finite_number(latitude) and -90 <= latitude <= 90
            and finite_number(longitude) and -180 <= longitude <= 180):
        raise WeatherError("The weather location has invalid coordinates.")
    try:
        response = requests.get(FORECAST_URL, params={
            "latitude": latitude, "longitude": longitude, "daily": ",".join(FIELDS),
            "timezone": "Asia/Kathmandu", "forecast_days": 3,
            "temperature_unit": "celsius", "precipitation_unit": "mm",
        }, timeout=(5, 15))
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as error:
        raise WeatherError("The weather request timed out. Please retry.") from error
    except requests.RequestException as error:
        raise WeatherError("Cannot reach Open-Meteo or the service returned an error. Check your connection and retry.") from error
    except ValueError as error:
        raise WeatherError("Open-Meteo returned an unreadable response. Please retry.") from error
    return parse_forecast(payload)
