"""Data persistence adapters - Legacy data migration and loaders."""

# Standard library imports
from datetime import datetime
from typing import Any

# Third-party library imports
# Application imports
from configuration.settings import logger
from data.persistence.adapters.project_data import load_project_data
from data.persistence.adapters.statistics import load_statistics
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)


def _migrate_legacy_project_data(data):
    """
    Migrate legacy project data format to v2.0.

    Args:
        data: Legacy project data structure

    Returns:
        Dict: Migrated v2.0 data structure
    """
    from data.schema import get_default_unified_data

    unified_data = get_default_unified_data()

    # Migrate existing project scope data if present
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

        # Preserve any existing metadata
        if "metadata" in data:
            unified_data["metadata"].update(data["metadata"])

    unified_data["metadata"]["source"] = "legacy_migration"
    unified_data["metadata"]["version"] = "2.0"
    unified_data["metadata"]["last_updated"] = datetime.now().isoformat()

    return unified_data


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
            fetch_jira_issues,
            get_jira_config,
            validate_jira_config,
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


#######################################################################
# LEGACY COMPATIBILITY LAYER
#######################################################################


def load_statistics_legacy():
    """
    Legacy function that loads statistics in old format for backward compatibility.

    Returns:
        Tuple (data, is_sample): Statistics data and sample flag
    """
    # First try to load from unified format
    try:
        statistics = get_project_statistics()
        if statistics:
            # Convert unified format back to legacy format
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

    # Fall back to original CSV loading
    return load_statistics()


def load_project_data_legacy():
    """
    Legacy function that loads project data in old format for backward compatibility.

    Returns:
        Dict: Project data in legacy format
    """
    # First try to load from unified format
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

    # Fall back to original project data loading
    return load_project_data()


def save_jira_data_unified(
    statistics_data: list[dict[str, Any]],
    project_scope_data: dict[str, Any],
    jira_config: dict[str, Any] | None = None,
) -> bool:
    """
    Save both JIRA statistics and project scope to unified data structure.

    This replaces the old CSV-based approach with unified JSON storage.

    Args:
        statistics_data: List of dictionaries containing statistics data
        project_scope_data: Dictionary containing project scope data
        jira_config: Optional JIRA configuration dictionary for metadata

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics
        unified_data["statistics"] = statistics_data

        # Update project scope
        unified_data["project_scope"] = project_scope_data

        logger.info(
            f"[Cache] Saving scope - Total: {project_scope_data.get('total_items')}, "
            f"Completed: {project_scope_data.get('completed_items')}, "
            f"Remaining: {project_scope_data.get('remaining_items')}"
        )

        # Extract JQL query from config or fallback
        jql_query = ""
        if jira_config is not None:
            jql_query = jira_config.get(
                "jql_query", ""
            )  # Update metadata with proper JIRA information
        unified_data["metadata"].update(
            {
                "source": "jira_calculated",  # Correct source for JIRA data
                "last_updated": datetime.now().isoformat(),
                "version": "2.0",
                "jira_query": jql_query,
                # Remove calculation_method - it's redundant with project_scope.calculation_metadata.method
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info("[Cache] JIRA data saved to unified project data structure")
        return True

    except Exception as e:
        logger.error(f"[Cache] Error saving JIRA data to unified structure: {e}")
        return False
