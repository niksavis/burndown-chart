import logging
from typing import Any

from configuration.metrics_config import get_metrics_config
from data.persistence import load_app_settings

logger = logging.getLogger(__name__)


def _get_completed_date_field():

    settings = load_app_settings()
    field_mappings = settings.get("field_mappings", {})

    general_mappings = field_mappings.get("general", {})
    completed_date_field = general_mappings.get("completed_date")

    if completed_date_field:
        return completed_date_field

    flow_mappings = field_mappings.get("flow", {})
    completed_date_field = flow_mappings.get("completed_date")

    if completed_date_field:
        logger.warning(
            "completed_date found in flow mappings (deprecated location). "
            "Please move to General Fields section in field mapping UI."
        )
        return completed_date_field

    return "resolutiondate"


def _get_field_mappings():

    app_settings = load_app_settings()
    field_mappings = app_settings.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})

    default_flow_end_statuses = ["Done", "Resolved", "Closed"]
    default_flow_start_statuses = ["In Progress", "In Review"]
    default_wip_statuses = ["In Progress", "In Review", "In Development"]

    flow_end = app_settings.get("flow_end_statuses")
    flow_start = app_settings.get("flow_start_statuses")
    wip = app_settings.get("wip_statuses")

    project_classification = {
        "flow_end_statuses": flow_end if flow_end else default_flow_end_statuses,
        "active_statuses": app_settings.get("active_statuses", []),
        "wip_statuses": wip if wip else default_wip_statuses,
        "flow_start_statuses": flow_start
        if flow_start
        else default_flow_start_statuses,
        "bug_types": app_settings.get("bug_types", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "production_environment_values": app_settings.get(
            "production_environment_values", []
        ),
    }

    logger.debug(
        f"[Flow Metrics] Loaded status configuration: "
        f"flow_start={project_classification['flow_start_statuses']}, "
        f"flow_end={project_classification['flow_end_statuses']}"
    )

    return flow_mappings, project_classification


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
        target_status = parts[1].replace(".DateTime", "")

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

    fields = issue.get("fields", {})
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


def _find_first_transition_to_statuses(
    changelog: list[dict], status_list: list[str]
) -> str | None:

    if not changelog or not status_list:
        return None

    sorted_changelog = sorted(changelog, key=lambda h: h.get("created", ""))

    for history in sorted_changelog:
        for item in history.get("items", []):
            if item.get("field") == "status" and item.get("toString") in status_list:
                return history.get("created")

    return None


def _is_issue_completed(
    issue: dict[str, Any],
    completed_date_field: str,
    changelog: list | None = None,
    flow_end_statuses: list[str] | None = None,
) -> bool:

    completed_date = _extract_datetime_from_field_mapping(
        issue, completed_date_field, changelog
    )
    if completed_date is not None:
        return True

    if flow_end_statuses and changelog:
        completion_timestamp = _find_first_transition_to_statuses(
            changelog, flow_end_statuses
        )
        if completion_timestamp is not None:
            return True

    return False


def _is_issue_in_progress(issue: dict[str, Any], wip_statuses: list[str]) -> bool:

    status = issue.get("fields", {}).get("status", {}).get("name", "")

    if not status:
        status = issue.get("status", "")

    issue_key = issue.get("key") or issue.get("issue_key", "unknown")
    is_wip = status in wip_statuses
    logger.debug(
        f"[WIP Check] {issue_key}: status='{status}', is_wip={is_wip}, "
        f"wip_statuses={wip_statuses[:3]}..."
    )

    return is_wip


def _get_work_type_for_issue(
    issue: dict[str, Any], flow_mappings: dict, flow_type_mappings: dict
) -> str:

    fields = issue.get("fields", {})

    if not fields:
        fields = issue

    flow_type_field = flow_mappings.get("flow_item_type", "issuetype")

    issue_type_value = fields.get(flow_type_field)

    if not issue_type_value and flow_type_field == "issuetype":
        issue_type_value = fields.get("issue_type")

    if isinstance(issue_type_value, dict):
        issue_type = issue_type_value.get("name") or issue_type_value.get("value", "")
    else:
        issue_type = str(issue_type_value) if issue_type_value else ""

    effort_category = None
    effort_category_field = flow_mappings.get("effort_category")
    if effort_category_field:
        effort_value = fields.get(effort_category_field)
        if isinstance(effort_value, dict):
            effort_category = effort_value.get("value") or effort_value.get("name")
        else:
            effort_category = str(effort_value) if effort_value else None

    config = get_metrics_config()
    flow_type = config.get_flow_type_for_issue(issue_type, effort_category)
    return flow_type if flow_type else "Feature"


FLOW_DISTRIBUTION_RECOMMENDATIONS = {
    "Feature": {"min": 40, "max": 70, "unit": "%", "label": "Product value"},
    "Bug": {"min": 0, "max": 10, "unit": "%", "label": "Defect resolution"},
    "Technical Debt": {"min": 10, "max": 20, "unit": "%", "label": "Sustainability"},
    "Risk": {"min": 10, "max": 20, "unit": "%", "label": "Risk reduction"},
}


def _calculate_trend(
    current_value: float, previous_value: float | None
) -> dict[str, Any]:

    if previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    if abs(percentage_change) < 5:
        return {"trend_direction": "stable", "trend_percentage": percentage_change}

    direction = "up" if percentage_change > 0 else "down"
    return {"trend_direction": direction, "trend_percentage": percentage_change}


def _normalize_work_type(work_type: Any) -> str:

    if isinstance(work_type, dict):
        return "Feature"

    if not isinstance(work_type, str):
        return "Feature"

    work_type_lower = work_type.lower()

    if "feature" in work_type_lower or "story" in work_type_lower:
        return "Feature"
    elif "bug" in work_type_lower or "defect" in work_type_lower:
        return "Bug"
    elif "debt" in work_type_lower or "technical" in work_type_lower:
        return "Technical Debt"
    elif "risk" in work_type_lower:
        return "Risk"
    else:
        return "Feature"
