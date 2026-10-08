import logging
from datetime import datetime
from typing import Any

from data.jira import (
    fetch_jira_issues,
    get_jira_config,
    sync_jira_scope_and_data,
    validate_jira_config,
)
from data.jira.scope_calculator import calculate_jira_project_scope
from data.persistence.adapters.project_data import load_project_data
from data.persistence.adapters.statistics import load_statistics
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)
from data.schema import get_default_unified_data

logger = logging.getLogger(__name__)


def _migrate_legacy_project_data(data):

    unified_data = get_default_unified_data()

    if isinstance(data, dict):
        unified_data["project_scope"].update(
            {
                "total_items": data.get("total_items", 0),
                "total_points": data.get("total_points", 0),
                "estimated_items": data.get("estimated_items", 0),
                "estimated_points": data.get("estimated_points", 0),
                "remaining_items": data.get(
                    "remaining_items", data.get("total_items", 0)
                ),
                "remaining_points": data.get(
                    "remaining_points", data.get("total_points", 0)
                ),
            }
        )

        if "metadata" in data:
            unified_data["metadata"].update(data["metadata"])

    unified_data["metadata"]["source"] = "legacy_migration"
    unified_data["metadata"]["version"] = "2.0"
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()

    return unified_data


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


def load_statistics_legacy():

    try:
        statistics = get_project_statistics()
        if statistics:
            legacy_data = []
            for stat in statistics:
                legacy_data.append(
                    {
                        "date": stat.get("date", ""),
                        "completed_items": stat.get("completed_items", 0),
                        "completed_points": stat.get("completed_points", 0),
                        "created_items": stat.get("created_items", 0),
                        "created_points": stat.get("created_points", 0),
                    }
                )
            return legacy_data, False
    except Exception as e:
        logger.warning(f"[Cache] Could not load from unified format: {e}")

    return load_statistics()


def load_project_data_legacy():

    try:
        scope = get_project_scope()
        if scope:
            return {
                "total_items": scope.get("total_items", 0),
                "total_points": scope.get("total_points", 0),
                "estimated_items": scope.get("estimated_items", 0),
                "estimated_points": scope.get("estimated_points", 0),
            }
    except Exception as e:
        logger.warning(f"[Cache] Could not load from unified format: {e}")

    return load_project_data()


def save_jira_data_unified(
    statistics_data: list[dict[str, Any]],
    project_scope_data: dict[str, Any],
    jira_config: dict[str, Any] | None = None,
) -> bool:

    try:
        unified_data = load_unified_project_data()

        unified_data["statistics"] = statistics_data

        unified_data["project_scope"] = project_scope_data

        logger.info(
            f"[Cache] Saving scope - Total: {project_scope_data.get('total_items')}, "
            f"Completed: {project_scope_data.get('completed_items')}, "
            f"Remaining: {project_scope_data.get('remaining_items')}"
        )

        jql_query = ""
        if jira_config is not None:
            jql_query = jira_config.get("jql_query", "")
        unified_data["metadata"].update(
            {
                "source": "jira_calculated",
                "last_updated": datetime.now().isoformat(),
                "version": "2.0",
                "jira_query": jql_query,
            }
        )

        save_unified_project_data(unified_data)

        logger.info("[Cache] JIRA data saved to unified project data structure")
        return True

    except Exception as e:
        logger.error(f"[Cache] Error saving JIRA data to unified structure: {e}")
        return False
