from pathlib import Path
from unittest.mock import Mock

import pytest
from streamlit.testing.v1 import AppTest

from himalayaiq import database, favorites, ui
from himalayaiq.weather import Forecast, WeatherError

APP = str(Path(__file__).resolve().parent.parent / 'app.py')


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    db = tmp_path / 'app.sqlite3'
    load, ids, save, remove = database.load_treks, favorites.favorite_ids, favorites.save_favorite, favorites.remove_favorite
    monkeypatch.setattr(database, 'load_treks', lambda: load(db))
    monkeypatch.setattr(favorites, 'favorite_ids', lambda: ids(db))
    monkeypatch.setattr(ui, 'save_favorite', lambda key: save(key, db))
    monkeypatch.setattr(ui, 'remove_favorite', lambda key: remove(key, db))
    ui.cached_forecast.clear()
    yield
    ui.cached_forecast.clear()


def app_test():
    return AppTest.from_file(APP, default_timeout=30).run()


def submit(app):
    next(b for b in app.button if b.label == 'Find my treks').click().run()


def test_questionnaire_results_and_no_match():
    app=app_test()
    assert not app.exception
    submit(app)
    assert not app.exception
    assert len(app.metric)==5
    assert len(app.warning)==4
    app.number_input(key='days').set_value(7)
    submit(app)
    assert not app.exception
    assert len(app.metric)==0
    assert any('No curated itinerary' in element.value for element in app.info)


def test_weather_failure_preserves_results(monkeypatch):
    monkeypatch.setattr(ui,'fetch_forecast',Mock(side_effect=WeatherError('Test connection failure')))
    app=app_test();submit(app)
    app.radio(key='navigation').set_value('Weather').run()
    app.button(key='load_weather').click().run()
    assert not app.exception
    assert any('Test connection failure' in element.value for element in app.warning)
    app.radio(key='navigation').set_value('Explore').run()
    assert len(app.metric)==5


def test_favorites_survive_session_and_remove():
    app=app_test()
    app.button(key='explore_langtang-valley').click().run()
    assert not app.exception
    other=app_test()
    other.radio(key='navigation').set_value('Favorites').run()
    assert other.button(key='favorite_langtang-valley').label=='Remove favorite'
    other.button(key='favorite_langtang-valley').click().run()
    assert not other.exception
    assert any('No favorites yet' in e.value for e in other.info)


def test_comparison_empty_and_budget_recalculate():
    app=app_test()
    app.radio(key='navigation').set_value('Compare').run()
    assert not app.exception
    app.multiselect(key='comparison').set_value([]).run()
    assert any('Select at least one' in e.value for e in app.info)
    app.radio(key='navigation').set_value('Budget').run()
    assert not app.exception
    original=app.metric[0].value
    next(e for e in app.number_input if e.label=='Daily extras / person').set_value(10.0).run()
    assert app.metric[0].value != original


def test_weather_success_and_route_switch(monkeypatch):
    fake=Forecast([{'Date':'2026-11-20','Low (°C)':None,'High (°C)':12,'Precipitation (mm)':0}],
                  'test fixture','Asia/Kathmandu',True)
    monkeypatch.setattr(ui,'fetch_forecast',Mock(return_value=fake))
    app=app_test();app.radio(key='navigation').set_value('Weather').run()
    app.button(key='load_weather').click().run()
    assert not app.exception
    assert len(app.dataframe)==1
    assert any('Missing values' in e.value for e in app.info)
    app.selectbox(key='weather_trek').set_value('langtang-valley').run()
    assert len(app.dataframe)==0  # Never show another route's cached weather.
