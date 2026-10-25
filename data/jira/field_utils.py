from data.story_points import extract_story_points_value

__all__ = ["extract_jira_field_id", "extract_story_points_value"]


def extract_jira_field_id(field_mapping: str) -> str:

    if not field_mapping or not isinstance(field_mapping, str):
        return ""

    field_mapping = field_mapping.strip()

    if ":" in field_mapping and ".DateTime" in field_mapping:
        return ""

    if "=" in field_mapping:
        return field_mapping.split("=")[0].strip()

    return field_mapping
