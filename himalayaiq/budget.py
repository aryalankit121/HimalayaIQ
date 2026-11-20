"""Editable planning scenarios, not quotes. Package extras avoid double counting."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from .validation import finite_number


@dataclass(frozen=True)
class BudgetAssumptions:
    package_price: float
    days: int
    daily_extras: float = 0
    flights: float = 0
    visa: float = 0
    insurance: float = 0
    equipment: float = 0
    tips: float = 0
    extra_nights: int = 0
    nightly_cost: float = 0
    contingency_percent: float = 0
    travelers: int = 1


@dataclass(frozen=True)
class BudgetEstimate:
    categories: dict[str, float]
    subtotal: float
    contingency: float
    per_person: float
    group_total: float


def estimate_budget(assumptions: BudgetAssumptions) -> BudgetEstimate:
    """All inputs are per person except party size. Round money at category level."""
    for name, lower, upper in (("days", 1, 60), ("extra_nights", 0, 60), ("travelers", 1, 50)):
        value = getattr(assumptions, name)
        if type(value) is not int or not lower <= value <= upper:
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be a whole number from {lower} to {upper}.")
    for name in ("package_price", "daily_extras", "flights", "visa", "insurance", "equipment",
                 "tips", "nightly_cost", "contingency_percent"):
        value = getattr(assumptions, name)
        upper = 100 if name == "contingency_percent" else 100000
        if not finite_number(value) or not 0 <= value <= upper:
            raise ValueError(f"{name.replace('_', ' ').capitalize()} must be between 0 and {upper}.")
    def money(value):
        return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    categories = {
        "Guided package": money(assumptions.package_price),
        "Daily extras": money(Decimal(str(assumptions.daily_extras)) * assumptions.days),
        "International flights": money(assumptions.flights),
        "Visa": money(assumptions.visa),
        "Insurance": money(assumptions.insurance),
        "Personal equipment": money(assumptions.equipment),
        "Tips": money(assumptions.tips),
        "Extra nights": money(Decimal(str(assumptions.nightly_cost)) * assumptions.extra_nights),
    }
    subtotal = sum(categories.values())
    contingency = money(subtotal * Decimal(str(assumptions.contingency_percent)) / 100)
    per_person = subtotal + contingency
    return BudgetEstimate({key: float(value) for key, value in categories.items()},
                          float(subtotal), float(contingency), float(per_person),
                          float(per_person * assumptions.travelers))
