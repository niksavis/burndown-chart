import logging
from datetime import datetime

from data.jira.config import get_jira_config, validate_jira_config
from data.jira.main_fetch import fetch_jira_issues
from data.jira.scope_calculator import calculate_jira_project_scope
from data.jira.scope_sync import sync_jira_scope_and_data
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)

logger = logging.getLogger(__name__)


def get_project_statistics():

    unified_data = load_unified_project_data()
    return unified_data.get("statistics", [])


def get_project_scope():

    unified_data = load_unified_project_data()
    return unified_data.get("project_scope", {})


def update_project_scope(scope_data):

    unified_data = load_unified_project_data()

    has_statistics = bool(unified_data.get("statistics"))
    source = unified_data.get("metadata", {}).get("source", "")

    if not has_statistics and source == "manual":
        logger.debug(
            "[Cache] update_project_scope: No statistics but source=manual, "
            "proceeding with scope update"
        )

    unified_data["project_scope"].update(scope_data)
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_unified_project_data(unified_data)


def update_project_scope_from_jira(
    jql_query: str | None = None, ui_config: dict | None = None
):

    try:
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)

        if not success:
            return success, message

        if scope_data:
            scope_data["source"] = "jira"
            scope_data["last_jira_sync"] = datetime.now().isoformat()
            update_project_scope(scope_data)

        return True, f"Project scope updated from JIRA: {message}"

    except Exception as e:
        logger.error(f"[JIRA] Error updating project scope: {e}")
        return False, f"Failed to update scope from JIRA: {e}"


def calculate_project_scope_from_jira(
    jql_query: str | None = None, ui_config: dict | None = None
):

    try:
        if ui_config:
            config = ui_config.copy()
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        fetch_success, issues = fetch_jira_issues(config)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        points_field = config.get("story_points_field", "").strip()
        if not points_field:
            points_field = ""

        scope_data = calculate_jira_project_scope(issues, points_field, config)
        if not scope_data:
            return False, "Failed to calculate JIRA project scope", {}

        return True, "Project scope calculated successfully", scope_data

    except Exception as e:
        logger.error(f"[JIRA] Error calculating project scope: {e}")
        return False, f"Failed to calculate scope from JIRA: {e}", {}


def add_project_statistic(stat_data):

    unified_data = load_unified_project_data()
    unified_data["statistics"].append(stat_data)
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_unified_project_data(unified_data)


__all__ = [
    "get_project_statistics",
    "get_project_scope",
    "update_project_scope",
    "update_project_scope_from_jira",
    "calculate_project_scope_from_jira",
    "add_project_statistic",
]
