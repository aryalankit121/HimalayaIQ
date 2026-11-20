from dataclasses import replace

import pytest

from himalayaiq.models import Preferences
from himalayaiq.validation import validate_preferences


@pytest.mark.parametrize("changes", [
    {"days": 0}, {"days": 61}, {"days": 3.5}, {"days": True},
    {"budget": -1}, {"budget": float("nan")}, {"budget": float("inf")},
    {"budget": "1000"}, {"month": 13}, {"month": True},
    {"experience": "Expert"}, {"interests": ("Unknown",)}, {"interests": None},
])
def test_invalid_preferences(changes):
    with pytest.raises(ValueError):
        validate_preferences(replace(Preferences(14, 1200, "Beginner", 10), **changes))
