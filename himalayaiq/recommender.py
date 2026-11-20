"""Deterministic preference compatibility. These rules do not assess safety."""

from .models import EXPERIENCE_LEVELS, Preferences, Recommendation, RecommendationReport, Trek
from .validation import finite_number, validate_preferences

DEFAULT_WEIGHTS = {"Duration": 0.25, "Budget": 0.20, "Travel month": 0.15,
                   "Interests": 0.20, "Experience": 0.20}


def range_compatibility(available: float, minimum: float, maximum: float) -> float:
    """0 below minimum; 0.5 to 1 across a range; 1 when the full range fits."""
    if available < minimum:
        return 0.0
    if available >= maximum:
        return 1.0
    return 0.5 + 0.5 * (available - minimum) / (maximum - minimum)


def month_compatibility(month: int, preferred: list[int]) -> float:
    return 1.0 if month in preferred else 0.25


def interest_compatibility(selected: tuple[str, ...], available: list[str]) -> float:
    chosen = set(selected)
    return len(chosen.intersection(available)) / len(chosen) if chosen else 0.0


def experience_compatibility(actual: str, suggested: str) -> float:
    gap = EXPERIENCE_LEVELS.index(suggested) - EXPERIENCE_LEVELS.index(actual)
    return max(0.0, 1.0 - 0.5 * max(0, gap))


def experience_warnings(preferences: Preferences, trek: Trek) -> list[str]:
    """Warnings do not depend on weights or the aggregate score."""
    if EXPERIENCE_LEVELS.index(preferences.experience) < EXPERIENCE_LEVELS.index(trek.experience):
        return [f"Experience mismatch: you selected {preferences.experience}; our editorial "
                f"profile suggests {trek.experience} experience. Review the route demands with "
                "a qualified local guide. Compatibility does not establish trekking safety."]
    return []


def recommend(treks: list[Trek], preferences: Preferences,
              weights: dict[str, float] | None = None) -> RecommendationReport:
    validate_preferences(preferences)
    active = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(active) != set(DEFAULT_WEIGHTS) or any(
        not finite_number(value) or value < 0 for value in active.values()
    ):
        raise ValueError("Weights must contain all five factors with finite, nonnegative values.")
    if not preferences.interests:
        active["Interests"] = 0.0
    total = sum(active.values())
    if total <= 0:
        raise ValueError("At least one active scoring weight must be positive.")
    active = {key: value / total for key, value in active.items()}
    matches, excluded = [], {}
    for trek in treks:
        reasons = []
        if preferences.days < trek.days_min:
            reasons.append(f"Needs at least {trek.days_min} days; you have {preferences.days}.")
        if preferences.budget < trek.cost_min:
            reasons.append(f"Package starts around USD {trek.cost_min:,.0f}; your budget is USD {preferences.budget:,.0f}.")
        if reasons:
            excluded[trek.name] = reasons
            continue
        factors = {
            "Duration": range_compatibility(preferences.days, trek.days_min, trek.days_max),
            "Budget": range_compatibility(preferences.budget, trek.cost_min, trek.cost_max),
            "Travel month": month_compatibility(preferences.month, trek.preferred_months),
            "Interests": interest_compatibility(preferences.interests, trek.interests),
            "Experience": experience_compatibility(preferences.experience, trek.experience),
        }
        explanations = [
            "Your available days cover the full curated itinerary." if factors["Duration"] == 1
            else "Only the shorter end of the duration range fits your available days.",
            "Your package budget covers the full listed price range; excluded expenses are extra."
            if factors["Budget"] == 1 else
            "Your budget covers only part of the listed package range; lower prices depend on group size.",
            "Your month is in the source's preferred season." if factors["Travel month"] == 1
            else "Your month is outside the source's preferred season; this is a seasonal preference rule.",
        ]
        matched = set(preferences.interests).intersection(trek.interests)
        explanations.append(
            f"Matches {len(matched)} of {len(set(preferences.interests))} interests"
            + (f": {', '.join(sorted(matched))}." if matched else ".")
            if preferences.interests else "No interests selected; other scoring weights are normalized."
        )
        explanations.append("Experience meets our editorial profile expectation."
                            if factors["Experience"] == 1 else "Experience is below our editorial profile expectation.")
        score = 100 * sum(factors[key] * active[key] for key in active)
        matches.append(Recommendation(trek, score, factors, active.copy(), explanations,
                                      experience_warnings(preferences, trek)))
    matches.sort(key=lambda result: (-result.score, result.trek.name))
    return RecommendationReport(matches, excluded)
