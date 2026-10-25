from math import isfinite
from typing import Any


def parse_story_points_value(
    story_points_value: Any, field_name: str = ""
) -> float | None:
    if story_points_value is None or story_points_value == "":
        return None
    if isinstance(story_points_value, dict):
        for key in ("value", "count", "total", "points", "votes"):
            if key in story_points_value:
                return parse_story_points_value(story_points_value[key], field_name)
        raise ValueError(f"Invalid story points in {field_name or 'points field'}")
    if isinstance(story_points_value, list):
        if not story_points_value:
            return None
        return parse_story_points_value(story_points_value[0], field_name)
    if isinstance(story_points_value, bool) or not isinstance(
        story_points_value, (int, float, str)
    ):
        raise ValueError(f"Invalid story points in {field_name or 'points field'}")
    try:
        points = float(story_points_value)
    except (ValueError, OverflowError) as error:
        raise ValueError(
            f"Invalid story points in {field_name or 'points field'}"
        ) from error
    if not isfinite(points) or points < 0:
        raise ValueError(f"Invalid story points in {field_name or 'points field'}")
    return points


def extract_story_points_value(story_points_value: Any, field_name: str = "") -> float:
    points = parse_story_points_value(story_points_value, field_name)
    return points if points is not None else 0.0
