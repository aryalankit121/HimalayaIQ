from dataclasses import replace

import pytest

from himalayaiq.budget import BudgetAssumptions, estimate_budget


def test_cost_categories_contingency_and_party_total():
    result = estimate_budget(BudgetAssumptions(1000, 10, daily_extras=20, flights=800,
        visa=50, insurance=100, equipment=50, tips=100, extra_nights=2,
        nightly_cost=50, contingency_percent=10, travelers=2))
    assert result.subtotal == 2400
    assert result.contingency == 240
    assert result.per_person == 2640
    assert result.group_total == 5280


def test_zero_extras_do_not_double_count_package():
    result = estimate_budget(BudgetAssumptions(890, 10))
    assert result.per_person == 890
    assert result.group_total == 890


@pytest.mark.parametrize("changes", [{"days": 0}, {"days": True}, {"travelers": 0},
    {"extra_nights": -1}, {"flights": float("nan")}, {"daily_extras": -1},
    {"package_price": float("inf")}, {"contingency_percent": 101}])
def test_invalid_assumptions(changes):
    with pytest.raises(ValueError):
        estimate_budget(replace(BudgetAssumptions(1000, 10), **changes))
