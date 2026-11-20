"""Small data records shared by the UI, storage, and recommendation engine."""

from dataclasses import dataclass, field

EXPERIENCE_LEVELS = ("Beginner", "Intermediate", "Experienced")
INTERESTS = ("Mountain views", "Local culture", "Forests", "Monasteries", "Hot springs")


@dataclass(frozen=True)
class Preferences:
    days: int
    budget: float
    experience: str
    month: int
    interests: tuple[str, ...] = ()


@dataclass(frozen=True)
class Trek:
    id: str
    name: str
    region: str
    days_min: int
    days_max: int
    cost_min: float
    cost_max: float
    difficulty: str
    experience: str
    max_altitude_m: int
    altitude_note: str
    preferred_months: list[int]
    interests: list[str]
    summary: str
    itinerary_note: str
    cost_note: str
    weather_location: str
    latitude: float
    longitude: float
    sources: list[dict[str, str]]


@dataclass
class Recommendation:
    trek: Trek
    score: float
    factors: dict[str, float]
    weights: dict[str, float]
    explanations: list[str]
    warnings: list[str] = field(default_factory=list)


@dataclass
class RecommendationReport:
    matches: list[Recommendation]
    excluded: dict[str, list[str]]
