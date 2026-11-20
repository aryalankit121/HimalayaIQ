"""Presentation-ready catalog data without a dependency on Streamlit."""

import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .database import ROOT
from .models import Trek


def comparison_rows(treks: list[Trek]) -> list[dict]:
    return [{"Trek": t.name, "Region": t.region, "Days in Nepal": t.days_min,
             "Package USD (approx.)": f"{t.cost_min:,.0f}–{t.cost_max:,.0f}",
             "Difficulty": t.difficulty, "Experience (editorial)": t.experience,
             "Max altitude (m, approx.)": t.max_altitude_m,
             "Interests": ", ".join(t.interests)} for t in treks]


def image_credits(path: Path = ROOT / "assets" / "image-credits.json") -> dict:
    try:
        records = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(records, dict):
            return {}
        required = ("file", "caption", "author", "license", "license_url", "source_url")
        return {key: record for key, record in records.items()
                if isinstance(record, dict) and all(isinstance(record.get(field), str)
                and record[field] for field in required)
                and record["license_url"].startswith("https://")
                and record["source_url"].startswith("https://")}
    except (OSError, ValueError):
        return {}


def photo_path(trek_id: str, credits: dict, root: Path = ROOT) -> Path | None:
    """A missing or corrupt image cannot take down the application."""
    try:
        path = (root / credits[trek_id]["file"]).resolve()
        if not path.is_relative_to((root / "assets").resolve()):
            return None
        with Image.open(path) as image:
            image.verify()
        return path
    except (OSError, ValueError, KeyError, TypeError, UnidentifiedImageError):
        return None
