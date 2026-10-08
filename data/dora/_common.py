import logging
from typing import Any

from data.performance_utils import log_performance

logger = logging.getLogger(__name__)


def _get_field_mappings():

    from data.persistence import load_app_settings  # noqa: PLC0415

    app_settings = load_app_settings()
    field_mappings = app_settings.get("field_mappings", {})
    dora_mappings = field_mappings.get("dora", {})

    default_flow_end_statuses = ["Done", "Resolved", "Closed"]
    default_flow_start_statuses = ["In Progress", "In Review"]
    default_wip_statuses = ["In Progress", "In Review", "In Development"]

    project_classification = {
        "flow_end_statuses": app_settings.get("flow_end_statuses")
        or default_flow_end_statuses,
        "active_statuses": app_settings.get("active_statuses", []),
        "wip_statuses": app_settings.get("wip_statuses") or default_wip_statuses,
        "flow_start_statuses": app_settings.get("flow_start_statuses")
        or default_flow_start_statuses,
        "bug_types": app_settings.get("bug_types", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "production_environment_values": app_settings.get(
            "production_environment_values", []
        ),
    }

    return dora_mappings, project_classification


def _is_issue_completed(issue: dict[str, Any], flow_end_statuses: list[str]) -> bool:

    if "fields" in issue and isinstance(issue.get("fields"), dict):
        status = issue["fields"].get("status", {}).get("name", "")
    else:
        status = issue.get("status", "")
    return status in flow_end_statuses


def _extract_datetime_from_field_mapping(
    issue: dict[str, Any], field_mapping: str, changelog: list | None = None
) -> str | None:

    if not field_mapping:
        return None

    if ":" in field_mapping and ".DateTime" in field_mapping:
        parts = field_mapping.split(":")
        if len(parts) != 2:
            return None

        field_name = parts[0]
        status_datetime = parts[1]
        target_status = status_datetime.replace(".DateTime", "")

        if changelog is None:
            changelog = issue.get("changelog", {}).get("histories", [])

        if not isinstance(changelog, list):
            return None

        for history in changelog:
            for item in history.get("items", []):
                if (
                    item.get("field") == field_name
                    and item.get("toString") == target_status
                ):
                    return history.get("created")

        return None

    if field_mapping == "fixVersions":
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fix_versions = issue["fields"].get("fixVersions", [])
        else:
            import json  # noqa: PLC0415

            fix_versions_raw = issue.get("fixversions", "[]")
            try:
                fix_versions = (
                    json.loads(fix_versions_raw)
                    if isinstance(fix_versions_raw, str)
                    else fix_versions_raw
                )
            except json.JSONDecodeError, TypeError:
                fix_versions = []

        for fv in fix_versions:
            release_date = fv.get("releaseDate")
            if release_date:
                return release_date
        return None

    if "fields" in issue and isinstance(issue.get("fields"), dict):
        fields = issue["fields"]
    else:
        fields = issue

    if "." in field_mapping:
        parts = field_mapping.split(".")
        value = fields
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value if isinstance(value, str) else None
    else:
        return fields.get(field_mapping)


def parse_field_value_filter(field_mapping: str) -> tuple:

    if not field_mapping:
        return None, None

    if "=" in field_mapping:
        parts = field_mapping.split("=", 1)
        field_id = parts[0].strip()
        value_str = parts[1].strip()
        filter_values = [v.strip() for v in value_str.split("|") if v.strip()]
        return field_id, filter_values if filter_values else None
    else:
        return field_mapping, None


def check_field_value_match(
    issue: dict[str, Any], field_id: str, filter_values: list[str]
) -> bool:

    if not filter_values:
        return True

    if "fields" in issue and isinstance(issue.get("fields"), dict):
        field_value = issue["fields"].get(field_id)
        if field_value is None and "customfield" in field_id:
            field_value = issue["fields"].get("customfields", {}).get(field_id)
    else:
        field_value = issue.get(field_id)
        if field_value is None and "customfield" in field_id:
            custom_fields = issue.get("custom_fields", {})
            if isinstance(custom_fields, dict):
                field_value = custom_fields.get(field_id)

    if field_value is None:
        return False

    filter_values_lower = [v.lower() for v in filter_values]

    if isinstance(field_value, str):
        return field_value.lower() in filter_values_lower

    if isinstance(field_value, dict):
        value_str = field_value.get("value", "") or field_value.get("name", "")
        return value_str.lower() in filter_values_lower

    if isinstance(field_value, list):
        for item in field_value:
            if isinstance(item, str):
                if item.lower() in filter_values_lower:
                    return True
            elif isinstance(item, dict):
                item_str = item.get("value", "") or item.get("name", "")
                if item_str.lower() in filter_values_lower:
                    return True

    return False


def is_production_environment(
    issue: dict[str, Any],
    affected_environment_mapping: str,
    fallback_values: list[str] | None = None,
) -> bool:

    if not affected_environment_mapping:
        return True

    field_id, filter_values = parse_field_value_filter(affected_environment_mapping)

    if field_id is None:
        return True

    if filter_values:
        return check_field_value_match(issue, field_id, filter_values)

    if fallback_values:
        return check_field_value_match(issue, field_id, fallback_values)

    return True


DEPLOYMENT_FREQUENCY_TIERS = {
    "elite": {"threshold": 0.9, "unit": "per day", "label": "Multiple deploys per day"},
    "high": {"threshold": 0.13, "unit": "per day", "label": "Daily to weekly"},
    "medium": {"threshold": 0.033, "unit": "per day", "label": "Weekly to monthly"},
    "low": {"threshold": 0, "unit": "per day", "label": "Less than monthly"},
}

LEAD_TIME_TIERS = {
    "elite": {"threshold": 1, "unit": "days", "label": "Less than 1 day"},
    "high": {"threshold": 7, "unit": "days", "label": "1-7 days"},
    "medium": {"threshold": 30, "unit": "days", "label": "1 week to 1 month"},
    "low": {"threshold": float("inf"), "unit": "days", "label": "More than 1 month"},
}

CHANGE_FAILURE_RATE_TIERS = {
    "elite": {"threshold": 15, "unit": "%", "label": "0-15%"},
    "high": {"threshold": 30, "unit": "%", "label": "16-30%"},
    "medium": {"threshold": 45, "unit": "%", "label": "31-45%"},
    "low": {"threshold": 100, "unit": "%", "label": "More than 45%"},
}

MTTR_TIERS = {
    "elite": {"threshold": 1, "unit": "hours", "label": "Less than 1 hour"},
    "high": {"threshold": 24, "unit": "hours", "label": "Less than 1 day"},
    "medium": {"threshold": 168, "unit": "hours", "label": "1-7 days"},
    "low": {"threshold": float("inf"), "unit": "hours", "label": "More than 1 week"},
}


def _classify_performance_tier(
    value: float, tiers: dict, higher_is_better: bool = True
) -> str:

    if higher_is_better:
        if value >= tiers["elite"]["threshold"]:
            return "elite"
        elif value >= tiers["high"]["threshold"]:
            return "high"
        elif value >= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"
    else:
        if value <= tiers["elite"]["threshold"]:
            return "elite"
        elif value <= tiers["high"]["threshold"]:
            return "high"
        elif value <= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"


def _determine_performance_tier(value: float | None, tiers: dict) -> dict[str, str]:

    if value is None:
        return {"tier": "Unknown", "color": "secondary"}

    higher_is_better = tiers["elite"]["threshold"] > tiers["low"]["threshold"]

    tier = _classify_performance_tier(value, tiers, higher_is_better)

    tier_colors = {
        "elite": "green",
        "high": "blue",
        "medium": "yellow",
        "low": "orange",
    }

    return {
        "tier": tier.capitalize(),
        "color": tier_colors.get(tier, "secondary"),
    }


def _calculate_trend(
    current_value: float, previous_value: float | None
) -> dict[str, Any]:

    if previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    if abs(percentage_change) < 5.0:
        return {"trend_direction": "stable", "trend_percentage": percentage_change}

    return {
        "trend_direction": "up" if percentage_change > 0 else "down",
        "trend_percentage": percentage_change,
    }


__all__ = [
    "CHANGE_FAILURE_RATE_TIERS",
    "DEPLOYMENT_FREQUENCY_TIERS",
    "LEAD_TIME_TIERS",
    "MTTR_TIERS",
    "_calculate_trend",
    "_classify_performance_tier",
    "_determine_performance_tier",
    "_extract_datetime_from_field_mapping",
    "_get_field_mappings",
    "_is_issue_completed",
    "check_field_value_match",
    "is_production_environment",
    "log_performance",
    "parse_field_value_filter",
]
