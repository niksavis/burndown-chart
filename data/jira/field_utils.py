"""
JIRA Field Utilities

Handles field extraction and mapping transformations.
"""

from typing import Any


def extract_jira_field_id(field_mapping: str) -> str:
    """Extract clean JIRA field ID from a field mapping string.

    Field mappings may include filter syntax that JIRA API doesn't understand:
    - "customfield_11309=PROD" -> "customfield_11309" (strip =Value filter)
    - "status:In Progress.DateTime" -> "" (changelog extraction, not a field)
    - "customfield_10002" -> "customfield_10002" (no change needed)
    - "fixVersions" -> "fixVersions" (standard field)

    Args:
        field_mapping: Field mapping string from profile configuration

    Returns:
        Clean field ID for JIRA API, or empty string if not a fetchable field
    """
    if not field_mapping or not isinstance(field_mapping, str):
        return ""

    field_mapping = field_mapping.strip()

    # Skip changelog extraction syntax (e.g., "status:In Progress.DateTime")
    # These are extracted from changelog, not fetched as fields
    if ":" in field_mapping and ".DateTime" in field_mapping:
        return ""

    # Strip =Value filter syntax (e.g., "customfield_11309=PROD" -> "customfield_11309")
    # The =Value part is our internal filter syntax, not understood by JIRA
    if "=" in field_mapping:
        return field_mapping.split("=")[0].strip()

    return field_mapping


def extract_story_points_value(story_points_value: Any, field_name: str = "") -> float:
    """Extract numeric story points value from various JIRA field formats.

    JIRA story points fields can have different formats depending on field type:
    - Number field: Direct numeric value (5, 3.5)
    - Text field: String that needs parsing ("5", "3.5")
    - Object field: Nested structure with 'value' key
    - Array field: List with first element containing value

    Args:
        story_points_value: Raw story points value from JIRA
        field_name: Optional field name for logging

    Returns:
        Float value of story points, or 0.0 if unable to parse
    """
    from configuration import logger

    if story_points_value is None:
        return 0.0

    # Case 1: Already a number (int or float)
    if isinstance(story_points_value, (int, float)):
        return float(story_points_value)

    # Case 2: String that can be converted to number
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

    # Case 3: Dictionary with 'value' key (some custom fields)
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

    # Case 4: List/array (take first element)
    if isinstance(story_points_value, list):
        if len(story_points_value) > 0:
            return extract_story_points_value(story_points_value[0], field_name)
        else:
            return 0.0

    # Unknown format
    field_info = f" (field: {field_name})" if field_name else ""
    logger.warning(
        f"[JIRA] Unexpected story points format: "
        f"{type(story_points_value).__name__}{field_info}"
    )
    return 0.0
