"""Shared utilities for DORA metrics calculations.

Provides field-mapping helpers, completion checks, performance tier
classification, and trend calculation used across all four DORA metrics.

Reference: docs/dora_metrics_spec.md
"""

import logging
from typing import Any

from data.performance_utils import log_performance

logger = logging.getLogger(__name__)


def _get_field_mappings():
    """Load field mappings from app settings.

    Returns:
        Tuple of (dora_mappings, project_classification)
    """
    from data.persistence import load_app_settings

    app_settings = load_app_settings()
    field_mappings = app_settings.get("field_mappings", {})
    dora_mappings = field_mappings.get("dora", {})

    # Project classification is flattened to root level by load_app_settings
    # Reconstruct the nested structure for backward compatibility
    # Provide sensible defaults if not configured (for testing and new installations)
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
    """Check if issue is in a completed status.

    Args:
        issue: JIRA issue dictionary
        flow_end_statuses: List of status names that indicate completion

    Returns:
        True if issue status is in flow_end_statuses
    """
    # Handle both nested (JIRA API) and flat (database) formats
    if "fields" in issue and isinstance(issue.get("fields"), dict):
        status = issue["fields"].get("status", {}).get("name", "")
    else:
        status = issue.get("status", "")
    return status in flow_end_statuses


def _extract_datetime_from_field_mapping(
    issue: dict[str, Any], field_mapping: str, changelog: list | None = None
) -> str | None:
    """Extract datetime value from issue based on field mapping configuration.

    Supports multiple field mapping formats:
    - Simple field: "created", "resolutiondate"
    - Nested field: "status.name"
        - Changelog transition: "status:In Progress.DateTime" (extracts timestamp
            when status changed to "In Progress")
    - fixVersions: "fixVersions" (extracts releaseDate from first fixVersion)

    Args:
        issue: JIRA issue dictionary
        field_mapping: Field mapping string from profile.json
            (e.g., "status:Done.DateTime")
        changelog: Optional changelog history for transition timestamp extraction

    Returns:
        ISO datetime string if found, None otherwise
    """
    if not field_mapping:
        return None

    # Handle changelog transition format: "status:StatusName.DateTime"
    if ":" in field_mapping and ".DateTime" in field_mapping:
        # Extract field name and target status
        # Format: "status:In Progress.DateTime"
        parts = field_mapping.split(":")
        if len(parts) != 2:
            return None

        field_name = parts[0]  # "status"
        status_datetime = parts[1]  # "In Progress.DateTime"
        target_status = status_datetime.replace(".DateTime", "")  # "In Progress"

        # Search changelog for transition to target status
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
                    return history.get("created")  # Return transition timestamp

        return None

    # Handle fixVersions special case
    if field_mapping == "fixVersions":
        # Handle both nested (JIRA API) and flat (database) formats
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fix_versions = issue["fields"].get("fixVersions", [])
        else:
            # In flat format, fixVersions is JSON string - need to parse
            import json

            fix_versions_raw = issue.get("fixversions", "[]")
            try:
                fix_versions = (
                    json.loads(fix_versions_raw)
                    if isinstance(fix_versions_raw, str)
                    else fix_versions_raw
                )
            except (json.JSONDecodeError, TypeError):
                fix_versions = []

        for fv in fix_versions:
            release_date = fv.get("releaseDate")
            if release_date:
                return release_date
        return None

    # Handle simple and nested field paths
    # Support both nested (JIRA API) and flat (database) formats
    if "fields" in issue and isinstance(issue.get("fields"), dict):
        fields = issue["fields"]
    else:
        fields = issue  # Flat format: fields are at root level

    if "." in field_mapping:
        # Nested field like "status.name"
        parts = field_mapping.split(".")
        value = fields
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value if isinstance(value, str) else None
    else:
        # Simple field like "created", "resolutiondate"
        return fields.get(field_mapping)


def parse_field_value_filter(field_mapping: str) -> tuple:
    """Parse field=Value syntax from field mapping.

    Supports:
    - Simple field: "customfield_11309" -> ("customfield_11309", None)
    - Single value: "customfield_11309=PROD" -> ("customfield_11309", ["PROD"])
        - Multiple values: "customfield_11309=PROD|Production" ->
            ("customfield_11309", ["PROD", "Production"])

    Args:
        field_mapping: Field mapping string, optionally with =Value filter

    Returns:
        Tuple of (field_id, filter_values)
        - field_id: The field ID to check
        - filter_values: List of values to match, or None if no filter
    """
    if not field_mapping:
        return None, None

    if "=" in field_mapping:
        parts = field_mapping.split("=", 1)
        field_id = parts[0].strip()
        value_str = parts[1].strip()
        # Support | separator for multiple values
        filter_values = [v.strip() for v in value_str.split("|") if v.strip()]
        return field_id, filter_values if filter_values else None
    else:
        return field_mapping, None


def check_field_value_match(
    issue: dict[str, Any], field_id: str, filter_values: list[str]
) -> bool:
    """Check if issue field value matches any of the filter values.

    Handles various JIRA field types:
    - String: Direct comparison
    - Dict (select): Check 'value' or 'name' keys
    - List (multi-select): Check if any item matches

    Args:
        issue: JIRA issue dictionary
        field_id: Field ID to check (e.g., "customfield_11309")
        filter_values: List of values to match (e.g., ["PROD", "Production"])

    Returns:
        True if any filter value matches the field value
    """
    if not filter_values:
        return True  # No filter means all pass

    # Handle both nested (JIRA API) and flat (database) formats
    if "fields" in issue and isinstance(issue.get("fields"), dict):
        # Nested format: check fields first, then custom_fields
        field_value = issue["fields"].get(field_id)
        if field_value is None and "customfield" in field_id:
            # Check in nested custom_fields
            field_value = issue["fields"].get("customfields", {}).get(field_id)
    else:
        # Flat format: check root level first, then custom_fields dict
        field_value = issue.get(field_id)
        if field_value is None and "customfield" in field_id:
            # Check in flat custom_fields dict
            custom_fields = issue.get("custom_fields", {})
            if isinstance(custom_fields, dict):
                field_value = custom_fields.get(field_id)

    if field_value is None:
        return False

    # Normalize filter values to lowercase for case-insensitive matching
    filter_values_lower = [v.lower() for v in filter_values]

    # Handle string field
    if isinstance(field_value, str):
        return field_value.lower() in filter_values_lower

    # Handle dict field (single select)
    if isinstance(field_value, dict):
        value_str = field_value.get("value", "") or field_value.get("name", "")
        return value_str.lower() in filter_values_lower

    # Handle list field (multi-select)
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
    """Check if issue is from production environment.

    Uses the =Value syntax in affected_environment field mapping.
    Falls back to production_environment_values if no =Value specified.

    Args:
        issue: JIRA issue dictionary
        affected_environment_mapping: Field mapping (e.g., "customfield_11309=PROD")
        fallback_values: Fallback list of production values
            (from project_classification)

    Returns:
        True if issue is from production environment
    """
    if not affected_environment_mapping:
        return True  # No filter configured, include all

    field_id, filter_values = parse_field_value_filter(affected_environment_mapping)

    if field_id is None:
        return True

    # If =Value syntax used, apply that filter
    if filter_values:
        return check_field_value_match(issue, field_id, filter_values)

    # Fallback to production_environment_values list
    if fallback_values:
        return check_field_value_match(issue, field_id, fallback_values)

    # No filter values at all - include all
    return True


# DORA performance tier thresholds (based on industry research)
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
    """Classify metric value into DORA performance tier.

    Args:
        value: Metric value to classify
        tiers: Tier definitions with thresholds
        higher_is_better: True if higher values = better performance
            (e.g., deployment frequency)
                         False if lower values = better (e.g., lead time, MTTR)

    Returns:
        Performance tier: "elite", "high", "medium", or "low"
    """
    if higher_is_better:
        # Higher values are better (deployment frequency)
        if value >= tiers["elite"]["threshold"]:
            return "elite"
        elif value >= tiers["high"]["threshold"]:
            return "high"
        elif value >= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"
    else:
        # Lower values are better (lead time, CFR, MTTR)
        if value <= tiers["elite"]["threshold"]:
            return "elite"
        elif value <= tiers["high"]["threshold"]:
            return "high"
        elif value <= tiers["medium"]["threshold"]:
            return "medium"
        else:
            return "low"


def _determine_performance_tier(value: float | None, tiers: dict) -> dict[str, str]:
    """Determine performance tier with color for UI display (legacy compatibility).

    This function maintains backward compatibility with existing callback code.

    Args:
        value: Metric value to classify (None = unknown)
        tiers: Tier definitions with thresholds

    Returns:
        Dictionary with tier and color:
        {
            "tier": "Elite" | "High" | "Medium" | "Low" | "Unknown",
            "color": "green" | "blue" | "yellow" | "orange" | "red" | "secondary"
        }

    Note:
        Returns semantic color names (green/blue/yellow/orange/red) which are mapped
        to Bootstrap classes in ui/metric_cards.py tier_color_map. This matches the
        pattern used by Flow metrics for consistent badge rendering.
    """
    if value is None:
        return {"tier": "Unknown", "color": "secondary"}

    # Determine if higher is better by checking tier thresholds
    higher_is_better = tiers["elite"]["threshold"] > tiers["low"]["threshold"]

    tier = _classify_performance_tier(value, tiers, higher_is_better)

    # Map tier to semantic color names (matches Flow metrics pattern)
    # These are mapped to Bootstrap classes in ui/metric_cards.py:
    #   green -> success, blue -> tier-high, yellow -> tier-medium,
    #   orange -> tier-orange, red -> danger
    tier_colors = {
        "elite": "green",  # Elite performance -> green badge
        "high": "blue",  # High performance -> cyan/blue badge
        "medium": "yellow",  # Medium performance -> yellow badge
        "low": "orange",  # Low performance -> orange badge
        # (not red to distinguish from errors)
    }

    return {
        "tier": tier.capitalize(),
        "color": tier_colors.get(tier, "secondary"),
    }


def _calculate_trend(
    current_value: float, previous_value: float | None
) -> dict[str, Any]:
    """Calculate trend direction and percentage change.

    Args:
        current_value: Current period metric value
        previous_value: Previous period metric value (None if unavailable)

    Returns:
        Dictionary with trend information:
        {
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float (percentage change)
        }
    """
    if previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    # Consider changes < 5% as "stable"
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
