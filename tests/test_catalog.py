from dataclasses import replace

import pytest

from himalayaiq.catalog import comparison_rows, image_credits, photo_path
from himalayaiq.database import read_seed
from himalayaiq.models import Preferences
from himalayaiq.recommender import recommend
from himalayaiq.validation import validate_trek


def test_six_distinct_sourced_profiles_and_images():
    treks = read_seed()
    assert len(treks) == 6
    assert {t.experience for t in treks} == {"Beginner", "Intermediate", "Experienced"}
    assert min(t.days_min for t in treks) == 8
    assert max(t.days_min for t in treks) == 16
    credits = image_credits()
    for trek in treks:
        assert photo_path(trek.id, credits) is not None
        assert trek.elevation_points and trek.cultural_highlights
        assert all(credits[trek.id][key] for key in ("author","license","license_url","source_url","caption"))


def test_new_recommendation_profiles():
    treks = read_seed()
    report = recommend(treks,Preferences(8,860,"Beginner",1,("Forests",)))
    assert [r.trek.id for r in report.matches] == ["poon-hill"]
    assert report.matches[0].score == 100
    assert not report.matches[0].warnings
    report = recommend(treks,Preferences(16,2000,"Experienced",10,("Monasteries",)))
    assert {r.trek.id for r in report.matches} == {t.id for t in treks}
    assert not any(r.warnings for r in report.matches)
    beginner = recommend(treks,Preferences(16,2000,"Beginner",10,("Monasteries",)))
    assert next(r for r in beginner.matches if r.trek.id=='manaslu-circuit').warnings


def test_comparison_empty_and_complete():
    assert comparison_rows([]) == []
    row = comparison_rows(read_seed()[:1])[0]
    assert {'Region','Interests','Experience (editorial)','Max altitude (m, approx.)'} <= row.keys()


def test_missing_corrupt_and_escaping_photo_fallback(tmp_path):
    assert photo_path('missing',{}) is None
    (tmp_path/'assets').mkdir()
    (tmp_path/'assets'/'bad.jpg').write_text('not an image')
    assert photo_path('bad',{'bad':{'file':'assets/bad.jpg'}},tmp_path) is None
    assert photo_path('bad',{'bad':{'file':'../outside.jpg'}},tmp_path) is None
    assert image_credits(tmp_path/'missing.json') == {}


@pytest.mark.parametrize('point',[{'place':'X','altitude_m':-1},{'place':'X','altitude_m':float('nan')},{'place':'','altitude_m':1000}])
def test_invalid_elevation_points(point):
    with pytest.raises(ValueError):
        validate_trek(replace(read_seed()[0],elevation_points=[point]))
