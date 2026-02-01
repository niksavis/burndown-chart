"""Data persistence adapters - Project scope and statistics operations."""

# Standard library imports
from datetime import datetime

# Application imports
from configuration.settings import logger
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)


def get_project_statistics():
    """
    Get statistics from unified data structure.

    Returns:
        List[Dict]: Statistics array
    """
    unified_data = load_unified_project_data()
    return unified_data.get("statistics", [])


def get_project_scope():
    """
    Get project scope from unified data structure.

    Returns:
        Dict: Project scope data
    """
    unified_data = load_unified_project_data()
    return unified_data.get("project_scope", {})


def update_project_scope(scope_data):
    """
    Update project scope in unified data structure.

    CRITICAL: This function only updates project_scope, NOT statistics.
    If unified data fails to load (returns defaults with empty statistics),
    we must NOT save and overwrite any existing statistics.

    Args:
        scope_data: Dictionary with scope fields to update
    """
    unified_data = load_unified_project_data()

    # CRITICAL SAFETY CHECK: If we loaded defaults (empty statistics) but the
    # file exists, there might be data in it. Don't overwrite with empty data.
    # Only proceed if we have statistics OR if this is a new file.
    has_statistics = bool(unified_data.get("statistics"))
    source = unified_data.get("metadata", {}).get("source", "")

    # After migration, all data is in database - no file checks needed
    if not has_statistics and source == "manual":
        # If we have no statistics but source is manual, this might be a new query
        # Safe to proceed with save since we're only updating project_scope
        logger.debug(
            "[Cache] update_project_scope: No statistics but source=manual, proceeding with scope update"
        )

    unified_data["project_scope"].update(scope_data)
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
    save_unified_project_data(unified_data)


def update_project_scope_from_jira(
    jql_query: str | None = None, ui_config: dict | None = None
):
    """
    Update project scope using JIRA scope calculation.

    Args:
        jql_query: Optional JQL query to use for JIRA sync
        ui_config: Optional UI configuration to use

    Returns:
        Tuple (success: bool, message: str)
    """
    try:
        from data.jira import sync_jira_scope_and_data

        # Get JIRA scope data
        success, message, scope_data = sync_jira_scope_and_data(jql_query, ui_config)

        if not success:
            return success, message

        # Update project scope with JIRA data
        if scope_data:
            # Add metadata to indicate JIRA source
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
    """
    Calculate project scope from JIRA without saving to file.
    This is used for "Calculate Scope" action which should only display results.

    Args:
        jql_query: Optional JQL query to use for JIRA sync
        ui_config: Optional UI configuration to use

    Returns:
        Tuple (success: bool, message: str, scope_data: dict)
    """
    try:
        from data.jira import (
            get_jira_config,
            validate_jira_config,
            fetch_jira_issues,
        )
        from data.jira.scope_calculator import calculate_jira_project_scope

        # Load configuration
        if ui_config:
            config = ui_config.copy()
            if jql_query:
                config["jql_query"] = jql_query
        else:
            config = get_jira_config(jql_query)

        # Validate configuration
        is_valid, message = validate_jira_config(config)
        if not is_valid:
            return False, f"Configuration invalid: {message}", {}

        # Fetch issues from JIRA (or cache)
        fetch_success, issues = fetch_jira_issues(config)
        if not fetch_success:
            return False, "Failed to fetch JIRA data", {}

        # Calculate scope (no saving to file!)
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
    """
    Add a new statistic entry to unified data structure.

    Args:
        stat_data: Dictionary with statistic fields
    """
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
