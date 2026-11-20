from pathlib import Path
from unittest.mock import Mock

from streamlit.testing.v1 import AppTest

from himalayaiq.weather import WeatherError

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_questionnaire_results_and_no_match():
    app = AppTest.from_file(APP, default_timeout=15).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 3
    assert len(app.warning) == 3  # Beginner warnings, independent of ranking.
    app.number_input[0].set_value(8)
    app.button[0].click().run()
    assert not app.exception
    assert len(app.metric) == 0
    assert any("No curated itinerary" in element.value for element in app.info)


def test_weather_failure_preserves_results(monkeypatch):
    monkeypatch.setattr("himalayaiq.weather.fetch_forecast", Mock(side_effect=WeatherError("Test connection failure")))
    app = AppTest.from_file(APP, default_timeout=15).run()
    app.button[0].click().run()
    app.button[1].click().run()
    assert not app.exception
    assert len(app.metric) == 3
    assert any("Test connection failure" in element.value for element in app.warning)
