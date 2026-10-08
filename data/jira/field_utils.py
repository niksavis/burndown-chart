import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_jira_field_id(field_mapping: str) -> str:

    if not field_mapping or not isinstance(field_mapping, str):
        return ""

    field_mapping = field_mapping.strip()

    if ":" in field_mapping and ".DateTime" in field_mapping:
        return ""

    if "=" in field_mapping:
        return field_mapping.split("=")[0].strip()

    return field_mapping


def extract_story_points_value(story_points_value: Any, field_name: str = "") -> float:

    if story_points_value is None:
        return 0.0

    if isinstance(story_points_value, (int, float)):
        return float(story_points_value)

    if isinstance(story_points_value, str):
        try:
            return float(story_points_value.strip())
        except ValueError:
            field_info = f" (field: {field_name})" if field_name else ""
            logger.warning(
                f"[JIRA] Story points string cannot be converted to number: "
                f"'{story_points_value}'{field_info}"
            )
            return 0.0

    if isinstance(story_points_value, dict):
        if "value" in story_points_value:
            return extract_story_points_value(story_points_value["value"], field_name)
        else:
            field_info = f" (field: {field_name})" if field_name else ""
            logger.warning(
                f"[JIRA] Story points dict missing 'value' key: "
                f"{story_points_value}{field_info}"
            )
            return 0.0

    if isinstance(story_points_value, list):
        if len(story_points_value) > 0:
            return extract_story_points_value(story_points_value[0], field_name)
        else:
            return 0.0

    field_info = f" (field: {field_name})" if field_name else ""
    logger.warning(
        f"[JIRA] Unexpected story points format: "
        f"{type(story_points_value).__name__}{field_info}"
    )
    return 0.0
