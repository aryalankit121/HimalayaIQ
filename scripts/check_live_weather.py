"""Explicit network smoke test: no mocks and no saved weather fixtures."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from himalayaiq.database import read_seed
from himalayaiq.weather import WeatherError, fetch_forecast


def main() -> int:
    failures = 0
    seen = set()
    for trek in read_seed():
        coordinates = (trek.latitude, trek.longitude)
        if coordinates in seen:
            continue
        seen.add(coordinates)
        try:
            forecast = fetch_forecast(*coordinates)
            print(f"PASS {trek.weather_location}: {len(forecast.rows)} daily rows; "
                  f"{forecast.rows[0]['Date']} to {forecast.rows[-1]['Date']}; "
                  f"retrieved {forecast.fetched_at}")
        except WeatherError as error:
            failures += 1
            print(f"FAIL {trek.weather_location}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
