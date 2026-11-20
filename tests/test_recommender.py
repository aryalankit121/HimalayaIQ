from dataclasses import replace

import pytest

from himalayaiq.database import read_seed as read_full_seed
from himalayaiq.models import Preferences
from himalayaiq.recommender import DEFAULT_WEIGHTS, range_compatibility, recommend


def read_seed():
    """Retain the original three-route regression scenarios as the catalog grows."""
    original_ids = {"langtang-valley", "mardi-himal", "annapurna-base-camp"}
    return [trek for trek in read_full_seed() if trek.id in original_ids]


def profile(**changes):
    return replace(Preferences(14, 1200, "Intermediate", 10, ("Mountain views",)), **changes)


def test_published_routes_and_boundaries():
    treks = read_seed()
    assert len(treks) == 3
    assert not recommend(treks, profile(days=8)).matches
    result = recommend(treks, profile(days=9, budget=790))
    assert [r.trek.id for r in result.matches] == ["mardi-himal"]
    assert result.matches[0].factors["Budget"] == 0.5
    assert len(result.excluded) == 2
    assert not recommend(treks, profile(budget=749)).matches


def test_known_weighted_score_and_independent_warning():
    trek = read_seed()[0]
    result = recommend([trek], profile(experience="Beginner", month=7)).matches[0]
    assert result.score == pytest.approx(78.75)  # 25 + 20 + 3.75 + 20 + 10
    assert result.warnings
    result = recommend([trek], profile(experience="Beginner"),
                       {**DEFAULT_WEIGHTS, "Experience": 0}).matches[0]
    assert result.score == pytest.approx(100)
    assert result.warnings  # A high score cannot suppress the mismatch.


def test_interests_change_ranking_and_no_interests_normalize():
    treks = read_seed()
    assert recommend(treks, profile(interests=("Monasteries",))).matches[0].trek.id == "langtang-valley"
    assert recommend(treks, profile(interests=("Hot springs",))).matches[0].trek.id == "annapurna-base-camp"
    results = recommend(treks, profile(interests=())).matches
    assert all(r.score == pytest.approx(100) and r.weights["Interests"] == 0 for r in results)
    assert [r.trek.name for r in results] == sorted(r.trek.name for r in results)


def test_duplicate_interests_do_not_change_score():
    treks = read_seed()
    assert recommend(treks, profile()).matches[0].score == recommend(
        treks, profile(interests=("Mountain views", "Mountain views"))).matches[0].score


@pytest.mark.parametrize("available,minimum,maximum,expected", [
    (8, 9, 9, 0), (9, 9, 9, 1), (10, 9, 9, 1),
    (10, 10, 14, 0.5), (12, 10, 14, 0.75), (14, 10, 14, 1),
])
def test_range_scoring(available, minimum, maximum, expected):
    assert range_compatibility(available, minimum, maximum) == expected


@pytest.mark.parametrize("weights", [{}, {**DEFAULT_WEIGHTS, "Budget": -1},
    {**DEFAULT_WEIGHTS, "Duration": float("nan")}, dict.fromkeys(DEFAULT_WEIGHTS, 0)])
def test_invalid_weights(weights):
    with pytest.raises(ValueError):
        recommend(read_seed(), profile(), weights)


def test_increasing_resources_never_reduces_score():
    treks = read_seed()
    low = {r.trek.id: r.score for r in recommend(treks, profile(days=10, budget=900)).matches}
    high = {r.trek.id: r.score for r in recommend(treks, profile(days=14, budget=1300)).matches}
    assert all(high[key] >= value for key, value in low.items())
