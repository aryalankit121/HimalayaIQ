from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from himalayaiq.weather import UNITS, WeatherError, fetch_forecast, parse_forecast


@pytest.fixture
def payload():
    # Explicit synthetic fixture for parser tests only; never used by the app.
    return {"timezone": "Asia/Kathmandu", "daily_units": UNITS.copy(), "daily": {
        "time": ["2026-11-20", "2026-11-21"],
        "temperature_2m_min": [2.0, None], "temperature_2m_max": [10.0, 11.0],
        "precipitation_sum": [0.0, 1.5],
    }}


def test_real_request_contract_with_mock(monkeypatch, payload):
    response = Mock()
    response.json.return_value = payload
    get = Mock(return_value=response)
    monkeypatch.setattr("himalayaiq.weather.requests.get", get)
    result = fetch_forecast(28.1, 85.3)
    assert len(result.rows) == 2 and result.missing_values
    assert result.rows[1]["Low (°C)"] is None
    response.raise_for_status.assert_called_once()
    assert get.call_args.kwargs["timeout"] == (5, 15)
    assert get.call_args.kwargs["params"]["timezone"] == "Asia/Kathmandu"


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError(), requests.HTTPError()])
def test_network_errors(monkeypatch, error):
    monkeypatch.setattr("himalayaiq.weather.requests.get", Mock(side_effect=error))
    with pytest.raises(WeatherError):
        fetch_forecast(28, 85)


def test_http_error_and_bad_json(monkeypatch):
    response = Mock()
    monkeypatch.setattr("himalayaiq.weather.requests.get", Mock(return_value=response))
    response.raise_for_status.side_effect = requests.HTTPError("503")
    with pytest.raises(WeatherError):
        fetch_forecast(28, 85)
    response.raise_for_status.side_effect = None
    response.json.side_effect = ValueError("bad JSON")
    with pytest.raises(WeatherError):
        fetch_forecast(28, 85)


@pytest.mark.parametrize("mutation", [
    lambda p: p.pop("daily"),
    lambda p: p["daily"].update(time=[]),
    lambda p: p["daily"].update(temperature_2m_max=[10]),
    lambda p: p["daily_units"].update(precipitation_sum="inch"),
    lambda p: p["daily"].update(precipitation_sum=[-1, 0]),
    lambda p: p["daily"].update(temperature_2m_min=[float("nan"), 0]),
    lambda p: p["daily"].update(time=["bad", "date"]),
    lambda p: p["daily"].update(time=["2026-11-20", "2026-11-20"]),
    lambda p: p["daily"].update(temperature_2m_min=[20, 20]),
])
def test_bad_payloads(payload, mutation):
    data = deepcopy(payload)
    mutation(data)
    with pytest.raises(WeatherError):
        parse_forecast(data)


def test_invalid_coordinates_never_request(monkeypatch):
    get = Mock()
    monkeypatch.setattr("himalayaiq.weather.requests.get", get)
    with pytest.raises(WeatherError):
        fetch_forecast(float("nan"), 85)
    get.assert_not_called()
