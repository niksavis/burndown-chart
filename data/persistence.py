"""
Data Persistence Module

This module handles saving and loading application data to/from disk.
It provides functions for managing settings and statistics using JSON files.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Third-party library imports
import pandas as pd

# Application imports
from configuration import (
    DEFAULT_DATA_POINTS_COUNT,
    DEFAULT_DEADLINE,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_ITEMS,
    DEFAULT_TOTAL_POINTS,
    PROJECT_DATA_FILE,
    logger,
)

# File locking to prevent race conditions during concurrent writes
_file_locks: Dict[str, threading.Lock] = {}
_lock_manager = threading.Lock()


def _get_file_lock(file_path: str) -> threading.Lock:
    """Get or create a lock for a specific file path."""
    with _lock_manager:
        if file_path not in _file_locks:
            _file_locks[file_path] = threading.Lock()
        return _file_locks[file_path]


#######################################################################
# JSON SERIALIZATION HELPERS
#######################################################################


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and pandas Timestamp objects."""

    def default(self, o):
        """Convert non-serializable objects to JSON-compatible formats."""
        # Handle pandas Timestamp
        if hasattr(o, "isoformat"):
            return o.isoformat()
        # Handle pandas NaT (Not a Time)
        if pd.isna(o):
            return None
        # Handle numpy integers
        if hasattr(o, "item"):
            return o.item()
        return super().default(o)


def convert_timestamps_to_strings(data: Any) -> Any:
    """
    Recursively convert pandas Timestamp objects to ISO format strings.

    Args:
        data: Data structure that may contain Timestamp objects

    Returns:
        Data with all Timestamps converted to strings
    """
    if isinstance(data, dict):
        return {k: convert_timestamps_to_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_timestamps_to_strings(item) for item in data]
    elif hasattr(data, "isoformat"):
        # pandas Timestamp or datetime
        return data.isoformat()
    elif pd.isna(data):
        # pandas NaT or NaN
        return None
    elif hasattr(data, "item"):
        # numpy scalar types
        return data.item()
    return data


#######################################################################
# DATA PERSISTENCE FUNCTIONS
#######################################################################


def should_sync_jira() -> bool:
    """
    Check if JIRA sync should be performed based on configuration.

    Returns:
        bool: True if JIRA is enabled and configured
    """
    import os

    # Check if JIRA is enabled via environment variables
    jira_url = os.getenv("JIRA_URL", "")
    jira_default_jql = os.getenv("JIRA_DEFAULT_JQL", "")

    return bool(
        jira_url and (jira_default_jql or True)
    )  # Always true if URL exists, JQL has default


def save_app_settings(
    pert_factor,
    deadline,
    data_points_count=None,
    show_milestone=None,
    milestone=None,
    show_points=None,
    jql_query=None,
    last_used_data_source=None,
    active_jql_profile_id=None,
    jira_config=None,
    field_mappings=None,
    development_projects=None,
    devops_projects=None,
    devops_task_types=None,
    bug_types=None,
    story_types=None,
    task_types=None,
    production_environment_values=None,
    flow_end_statuses=None,
    active_statuses=None,
    flow_start_statuses=None,
    wip_statuses=None,
    flow_type_mappings=None,
    cache_metadata=None,
):
    """
    Save app-level settings to JSON file.

    Note: JIRA configuration is now managed separately via save_jira_configuration().
    This function no longer handles individual JIRA settings.

    Args:
        pert_factor: PERT factor value
        deadline: Deadline date string
        data_points_count: Number of data points to use for calculations
        show_milestone: Whether to show milestone on charts
        milestone: Milestone date string
        show_points: Whether to show points tracking and forecasting
        jql_query: JQL query for JIRA integration
        last_used_data_source: Last selected data source (JIRA or CSV)
        active_jql_profile_id: ID of the currently active JQL query profile
        jira_config: JIRA configuration dictionary
        field_mappings: Field mappings configuration
        development_projects: List of development project keys
        devops_projects: List of devops project keys
        devops_task_types: List of DevOps task type names
        bug_types: List of bug type names
        story_types: List of story type names
        task_types: List of task type names
        production_environment_values: List of production environment identifiers
        flow_end_statuses: List of completion status names
        active_statuses: List of active status names
        flow_start_statuses: List of flow start status names
        wip_statuses: List of WIP status names
        flow_type_mappings: Dict with Flow type classifications (Feature, Defect, etc.)
        cache_metadata: Dict with cache tracking info (last_cache_key, last_cache_timestamp, cache_config_hash)
    """
    settings = {
        "pert_factor": pert_factor,
        "deadline": deadline,
        "data_points_count": data_points_count
        if data_points_count is not None
        else max(DEFAULT_DATA_POINTS_COUNT, pert_factor * 2),
        "show_milestone": show_milestone if show_milestone is not None else False,
        "milestone": milestone,
        "show_points": show_points if show_points is not None else False,
        "jql_query": jql_query if jql_query is not None else "project = JRASERVER",
        "last_used_data_source": last_used_data_source
        if last_used_data_source is not None
        else "JIRA",  # Default to JIRA (swapped order)
        "active_jql_profile_id": active_jql_profile_id
        if active_jql_profile_id is not None
        else "",
    }

    # Add comprehensive mappings configuration if provided
    if jira_config is not None:
        settings["jira_config"] = jira_config
    if field_mappings is not None:
        settings["field_mappings"] = field_mappings
    if development_projects is not None:
        settings["development_projects"] = development_projects
    if devops_projects is not None:
        settings["devops_projects"] = devops_projects
    if devops_task_types is not None:
        settings["devops_task_types"] = devops_task_types
    if bug_types is not None:
        settings["bug_types"] = bug_types
    if story_types is not None:
        settings["story_types"] = story_types
    if task_types is not None:
        settings["task_types"] = task_types
    if production_environment_values is not None:
        settings["production_environment_values"] = production_environment_values
    if flow_end_statuses is not None:
        settings["flow_end_statuses"] = flow_end_statuses
    if active_statuses is not None:
        settings["active_statuses"] = active_statuses
    if flow_start_statuses is not None:
        settings["flow_start_statuses"] = flow_start_statuses
    if wip_statuses is not None:
        settings["wip_statuses"] = wip_statuses
    if flow_type_mappings is not None:
        settings["flow_type_mappings"] = flow_type_mappings

    # Add cache metadata for audit trail (Feature 008 - T057)
    if cache_metadata is not None:
        settings["cache_metadata"] = cache_metadata

    # Preserve DORA/Flow configuration and other settings if they exist
    try:
        existing_settings = load_app_settings()
        logger.debug(
            f"[Config] Loading existing settings. Keys: {list(existing_settings.keys())}"
        )

        # Keys to preserve from existing settings (if not explicitly provided)
        preserve_keys = [
            "jira_config",
            "field_mappings",
            "devops_projects",
            "development_projects",
            "devops_task_types",
            "bug_types",
            "story_types",
            "task_types",
            "production_environment_values",
            "production_environment_value",  # Legacy support
            "flow_end_statuses",
            "active_statuses",
            "flow_start_statuses",
            "wip_statuses",
            "flow_type_mappings",
            "field_mapping_notes",
            "cache_metadata",  # Feature 008 - T057
        ]

        for key in preserve_keys:
            if key in existing_settings and key not in settings:
                settings[key] = existing_settings[key]
                logger.debug(f"[Config] Preserved existing {key}")
                # Extra logging for field_mappings to debug config reversion issue
                if key == "field_mappings":
                    logger.debug(
                        f"[Config] Preserving field_mappings: {existing_settings[key]}"
                    )

        logger.debug(
            f"[Config] Final settings keys before write: {list(settings.keys())}"
        )
    except Exception as e:
        logger.error(f"[Config] Could not load existing settings: {e}")

    try:
        # Use repository pattern - get backend and save via database
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Get active profile ID
        active_profile_id = backend.get_app_state("active_profile_id")
        if not active_profile_id:
            logger.error("[Config] No active profile to save settings to")
            return

        # Load existing profile to preserve metadata and merge settings
        existing_profile = backend.get_profile(active_profile_id) or {}

        # Build complete profile structure
        profile_data = {
            # Profile metadata (preserve existing values)
            "id": existing_profile.get("id", active_profile_id),
            "name": existing_profile.get("name", "Default"),
            "description": existing_profile.get("description", ""),
            "created_at": existing_profile.get(
                "created_at", datetime.now().isoformat()
            ),
            "last_used": datetime.now().isoformat(),  # Always update last_used
            # Settings (merged from function parameters)
            "jira_config": settings.get(
                "jira_config", existing_profile.get("jira_config", {})
            ),
            "field_mappings": settings.get(
                "field_mappings", existing_profile.get("field_mappings", {})
            ),
            "forecast_settings": {
                "pert_factor": settings.get(
                    "pert_factor",
                    existing_profile.get("forecast_settings", {}).get(
                        "pert_factor", DEFAULT_PERT_FACTOR
                    ),
                ),
                # Use 'in' check for deadline/milestone to allow explicit None (clearing the value)
                "deadline": settings["deadline"]
                if "deadline" in settings
                else existing_profile.get("forecast_settings", {}).get("deadline"),
                "milestone": settings["milestone"]
                if "milestone" in settings
                else existing_profile.get("forecast_settings", {}).get("milestone"),
                "data_points_count": settings.get(
                    "data_points_count",
                    existing_profile.get("forecast_settings", {}).get(
                        "data_points_count", DEFAULT_DATA_POINTS_COUNT
                    ),
                ),
            },
            "project_classification": {
                "devops_projects": settings.get(
                    "devops_projects",
                    existing_profile.get("project_classification", {}).get(
                        "devops_projects", []
                    ),
                ),
                "development_projects": settings.get(
                    "development_projects",
                    existing_profile.get("project_classification", {}).get(
                        "development_projects", []
                    ),
                ),
                "devops_task_types": settings.get(
                    "devops_task_types",
                    existing_profile.get("project_classification", {}).get(
                        "devops_task_types", ["Task", "Sub-task"]
                    ),
                ),
                "bug_types": settings.get(
                    "bug_types",
                    existing_profile.get("project_classification", {}).get(
                        "bug_types", ["Bug"]
                    ),
                ),
                "production_environment_values": settings.get(
                    "production_environment_values",
                    existing_profile.get("project_classification", {}).get(
                        "production_environment_values", []
                    ),
                ),
                "flow_end_statuses": settings.get(
                    "flow_end_statuses",
                    existing_profile.get("project_classification", {}).get(
                        "flow_end_statuses", ["Resolved", "Closed"]
                    ),
                ),
                "active_statuses": settings.get(
                    "active_statuses",
                    existing_profile.get("project_classification", {}).get(
                        "active_statuses", ["In Progress", "In Review"]
                    ),
                ),
                "flow_start_statuses": settings.get(
                    "flow_start_statuses",
                    existing_profile.get("project_classification", {}).get(
                        "flow_start_statuses", ["In Progress"]
                    ),
                ),
                "wip_statuses": settings.get(
                    "wip_statuses",
                    existing_profile.get("project_classification", {}).get(
                        "wip_statuses", ["In Progress", "In Review", "Testing"]
                    ),
                ),
            },
            "flow_type_mappings": settings.get(
                "flow_type_mappings", existing_profile.get("flow_type_mappings", {})
            ),
            "queries": existing_profile.get("queries", []),
            "active_query_id": existing_profile.get("active_query_id"),
            "show_milestone": settings.get(
                "show_milestone", existing_profile.get("show_milestone", False)
            ),
            "show_points": settings.get(
                "show_points", existing_profile.get("show_points", False)
            ),
        }

        # Save via backend (database) - profile_data already contains 'id' field
        backend.save_profile(profile_data)
        logger.info(
            f"[Config] Settings saved to database. Profile: {profile_data['name']}"
        )
        logger.debug(
            f"[Config] Saved forecast_settings: pert_factor={profile_data['forecast_settings'].get('pert_factor')}, "
            f"deadline={profile_data['forecast_settings'].get('deadline')}, "
            f"data_points_count={profile_data['forecast_settings'].get('data_points_count')}, "
            f"milestone={profile_data['forecast_settings'].get('milestone')}"
        )
        logger.debug(
            f"[Config] Saved UI settings: show_milestone={profile_data.get('show_milestone')}, "
            f"show_points={profile_data.get('show_points')}"
        )
    except Exception as e:
        logger.error(f"[Config] Error saving app settings: {e}")


def load_app_settings() -> Dict[str, Any]:
    """
    Load app-level settings via repository pattern (database-first).

    Returns:
        Dictionary containing app settings or default values if not found
    """
    default_settings = {
        "pert_factor": DEFAULT_PERT_FACTOR,
        "deadline": DEFAULT_DEADLINE,
        "data_points_count": DEFAULT_DATA_POINTS_COUNT,
        "show_milestone": False,
        "milestone": None,
        "show_points": False,
        "jql_query": "project = JRASERVER",
        "last_used_data_source": "JIRA",  # Default to JIRA
        "active_jql_profile_id": "",  # Empty means use custom query
        "cache_metadata": {  # Feature 008 - T057: Cache audit trail
            "last_cache_key": None,
            "last_cache_timestamp": None,
            "cache_config_hash": None,
        },
    }

    try:
        # Use repository pattern - backend abstracts storage
        from data.persistence.factory import get_backend

        backend = get_backend()  # Returns SQLiteBackend by default

        # Get active profile ID from app state
        active_id = backend.get_app_state("active_profile_id")

        if not active_id:
            logger.info("[Config] No active profile, using defaults")
            return default_settings

        # Load profile from backend (handles SQLite/JSON/in-memory)
        profile_data = backend.get_profile(active_id)

        if not profile_data:
            logger.info(f"[Config] Profile {active_id} not found, using defaults")
            return default_settings

        logger.info(f"[Config] Settings loaded via backend for profile {active_id}")

        # Transform backend data to legacy app_settings format for backward compatibility
        settings = {
            "pert_factor": profile_data.get("forecast_settings", {}).get(
                "pert_factor", DEFAULT_PERT_FACTOR
            ),
            "deadline": profile_data.get("forecast_settings", {}).get(
                "deadline", DEFAULT_DEADLINE
            ),
            "milestone": profile_data.get("forecast_settings", {}).get("milestone"),
            "data_points_count": profile_data.get("forecast_settings", {}).get(
                "data_points_count", DEFAULT_DATA_POINTS_COUNT
            ),
            "show_milestone": profile_data.get("show_milestone", False),
            "show_points": profile_data.get("show_points", False),
            "jql_query": "project = JRASERVER",  # Placeholder
            "last_used_data_source": "JIRA",
            "active_jql_profile_id": "",
            "cache_metadata": {
                "last_cache_key": None,
                "last_cache_timestamp": None,
                "cache_config_hash": None,
            },
            # JIRA configuration
            "jira_config": profile_data.get("jira_config", {}),
            # Field mappings
            "field_mappings": profile_data.get("field_mappings", {}),
            # Project classification
            "devops_projects": profile_data.get("project_classification", {}).get(
                "devops_projects", []
            ),
            "development_projects": profile_data.get("project_classification", {}).get(
                "development_projects", []
            ),
            "devops_task_types": profile_data.get("project_classification", {}).get(
                "devops_task_types", []
            ),
            "bug_types": profile_data.get("project_classification", {}).get(
                "bug_types", []
            ),
            "production_environment_values": profile_data.get(
                "project_classification", {}
            ).get("production_environment_values", []),
            "flow_end_statuses": profile_data.get("project_classification", {}).get(
                "flow_end_statuses", []
            ),
            "active_statuses": profile_data.get("project_classification", {}).get(
                "active_statuses", []
            ),
            "flow_start_statuses": profile_data.get("project_classification", {}).get(
                "flow_start_statuses", []
            ),
            "wip_statuses": profile_data.get("project_classification", {}).get(
                "wip_statuses", []
            ),
            # Flow type mappings
            "flow_type_mappings": profile_data.get("flow_type_mappings", {}),
        }

        # Add default values for any missing fields
        for key, default_value in default_settings.items():
            if key not in settings:
                settings[key] = default_value

        logger.debug(
            f"[Config] Loaded forecast_settings: pert_factor={settings.get('pert_factor')}, "
            f"deadline={settings.get('deadline')}, "
            f"data_points_count={settings.get('data_points_count')}, "
            f"milestone={settings.get('milestone')}"
        )
        logger.debug(
            f"[Config] Loaded UI settings: show_milestone={settings.get('show_milestone')}, "
            f"show_points={settings.get('show_points')}"
        )

        return settings

    except Exception as e:
        logger.error(f"[Config] Error loading app settings via backend: {e}")
        return default_settings


def save_project_data(
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    metadata=None,
):
    """
    DEPRECATED: Use save_unified_project_data() instead.
    Save project-specific data via repository pattern.

    Args:
        total_items: Total number of items
        total_points: Total number of points
        estimated_items: Number of items that have been estimated
        estimated_points: Number of points for the estimated items
        metadata: Additional project metadata (e.g., JIRA sync info)
    """
    logger.warning(
        "[Deprecated] save_project_data() called - use save_unified_project_data() instead"
    )

    try:
        from data.persistence.factory import get_backend

        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.error("[Cache] No active profile/query to save project data to")
            return

        scope_data = {
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items
            if estimated_items is not None
            else DEFAULT_ESTIMATED_ITEMS,
            "estimated_points": estimated_points
            if estimated_points is not None
            else DEFAULT_ESTIMATED_POINTS,
            "metadata": metadata if metadata is not None else {},
        }

        backend.save_scope(active_profile_id, active_query_id, scope_data)
        logger.info("[Cache] Project data saved to database")
    except Exception as e:
        logger.error(f"[Cache] Error saving project data: {e}")


def load_project_data() -> Dict[str, Any]:
    """
    Load project-specific data via repository pattern (database).

    Returns:
        Dictionary containing project data or default values if not found
    """
    default_data = {
        "total_items": DEFAULT_TOTAL_ITEMS,
        "total_points": DEFAULT_TOTAL_POINTS,
        "estimated_items": DEFAULT_ESTIMATED_ITEMS,
        "estimated_points": DEFAULT_ESTIMATED_POINTS,
        "metadata": {},
    }

    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return default_data

        scope = backend.get_scope(active_profile_id, active_query_id)
        if not scope:
            return default_data

        return {
            "total_items": scope.get("total_items", DEFAULT_TOTAL_ITEMS),
            "total_points": scope.get("total_points", DEFAULT_TOTAL_POINTS),
            "estimated_items": scope.get("estimated_items", DEFAULT_ESTIMATED_ITEMS),
            "estimated_points": scope.get("estimated_points", DEFAULT_ESTIMATED_POINTS),
            "metadata": {},
        }
    except Exception as e:
        logger.error(f"[Cache] Error loading project data: {e}")
        return default_data


def save_settings(
    pert_factor,
    deadline,
    total_items,
    total_points,
    estimated_items=None,
    estimated_points=None,
    data_points_count=None,
    show_milestone=None,
    milestone=None,
    show_points=None,
):
    """
    DEPRECATED: Legacy function for single-file mode (not used with profiles).
    Use save_app_settings() instead for profile-based persistence.

    This function is kept for backward compatibility only.
    """
    logger.warning(
        "[Deprecated] save_settings() called - use save_app_settings() for profile-based storage"
    )

    # Delegate to save_app_settings with proper structure
    settings_dict = {
        "forecast_settings": {
            "pert_factor": pert_factor,
            "deadline": deadline,
            "data_points_count": data_points_count
            if data_points_count is not None
            else max(DEFAULT_DATA_POINTS_COUNT, pert_factor * 2),
            "milestone": milestone,
        },
        "project_scope": {
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items
            if estimated_items is not None
            else DEFAULT_ESTIMATED_ITEMS,
            "estimated_points": estimated_points
            if estimated_points is not None
            else DEFAULT_ESTIMATED_POINTS,
        },
        "show_milestone": show_milestone if show_milestone is not None else False,
        "show_points": show_points if show_points is not None else False,
    }
    save_app_settings(**settings_dict)


def load_settings():
    """
    DEPRECATED: Legacy function for single-file mode (not used with profiles).
    Use load_app_settings() instead for profile-based persistence.

    This function is kept for backward compatibility only.
    """
    logger.warning(
        "[Deprecated] load_settings() called - use load_app_settings() for profile-based storage"
    )

    # Delegate to load_app_settings and flatten the structure
    app_settings = load_app_settings()
    forecast = app_settings.get("forecast_settings", {})

    return {
        "pert_factor": forecast.get("pert_factor", DEFAULT_PERT_FACTOR),
        "deadline": forecast.get("deadline", DEFAULT_DEADLINE),
        "total_items": app_settings.get("total_items", DEFAULT_TOTAL_ITEMS),
        "total_points": app_settings.get("total_points", DEFAULT_TOTAL_POINTS),
        "estimated_items": app_settings.get("estimated_items", DEFAULT_ESTIMATED_ITEMS),
        "estimated_points": app_settings.get(
            "estimated_points", DEFAULT_ESTIMATED_POINTS
        ),
        "data_points_count": forecast.get(
            "data_points_count", DEFAULT_DATA_POINTS_COUNT
        ),
        "show_milestone": app_settings.get("show_milestone", False),
        "milestone": forecast.get("milestone"),
    }


def save_statistics(data: List[Dict[str, Any]]) -> None:
    """
    Save statistics data to unified JSON file.

    Args:
        data: List of dictionaries containing statistics data
    """
    from data.iso_week_bucketing import get_week_label
    from datetime import datetime

    try:
        df = pd.DataFrame(data)

        # Ensure date column is in proper datetime format for sorting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Sort by date in ascending order (oldest first)
        df = df.sort_values("date", ascending=True)

        # Convert back to string format for storage
        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        # CRITICAL FIX: Ensure week_label exists for all statistics
        # This prevents NULL week_labels in database
        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = datetime.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not calculate week_label for date {stat.get('date')}: {e}"
                        )

        # Ensure any remaining Timestamp objects are converted to strings
        statistics_data = convert_timestamps_to_strings(statistics_data)

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata - preserve existing source and jira_query unless explicitly overriding
        unified_data["metadata"].update(
            {
                "last_updated": datetime.now().isoformat(),
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info(f"[Cache] Statistics saved to {PROJECT_DATA_FILE}")
    except Exception as e:
        logger.error(f"[Cache] Error saving statistics: {e}")


def save_statistics_from_csv_import(data: List[Dict[str, Any]]) -> None:
    """
    Save statistics data from CSV import to unified JSON file.
    This function specifically handles CSV imports and sets appropriate metadata.

    Args:
        data: List of dictionaries containing statistics data
    """
    from data.iso_week_bucketing import get_week_label
    from datetime import datetime as dt_module

    try:
        df = pd.DataFrame(data)

        # Ensure date column is in proper datetime format for sorting
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Sort by date in ascending order (oldest first)
        df = df.sort_values("date", ascending=True)

        # Convert back to string format for storage
        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        # Convert back to list of dictionaries
        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        # CRITICAL FIX: Ensure week_label exists for all statistics from CSV import
        # This prevents NULL week_labels in database
        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = dt_module.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            f"Could not calculate week_label for date {stat.get('date')}: {e}"
                        )

        # Load current unified data
        unified_data = load_unified_project_data()

        # Update statistics in unified data
        unified_data["statistics"] = statistics_data

        # Update metadata specifically for CSV import
        unified_data["metadata"].update(
            {
                "source": "csv_import",  # Set proper source for CSV uploads
                "last_updated": datetime.now().isoformat(),
                "jira_query": "",  # Clear JIRA-specific fields for CSV import
            }
        )

        # Save the unified data
        save_unified_project_data(unified_data)

        logger.info(f"[Cache] Statistics from CSV import saved to {PROJECT_DATA_FILE}")
    except Exception as e:
        logger.error(f"[Cache] Error saving CSV import statistics: {e}")


def load_statistics() -> tuple:
    """
    Load statistics data via repository pattern (database).

    Returns:
        Tuple (data, is_sample) where:
        - data: List of dictionaries containing statistics data
        - is_sample: Boolean indicating if sample data is being used
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return [], False

        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        if not stats_rows:
            return [], False

        # Convert to DataFrame for processing
        statistics_df = pd.DataFrame(stats_rows)

        # Rename stat_date to date for compatibility
        if "stat_date" in statistics_df.columns:
            statistics_df["date"] = statistics_df["stat_date"]

        # Parse dates once for consistency
        statistics_df["date"] = pd.to_datetime(
            statistics_df["date"], errors="coerce", format="mixed"
        )

        # CRITICAL FIX: Remove duplicate dates from legacy data
        # Normalize dates and keep only the most recent entry per date
        if "date" in statistics_df.columns and not statistics_df.empty:
            # Normalize dates to YYYY-MM-DD format using apply to avoid type checker issues
            statistics_df["date_normalized"] = statistics_df["date"].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None
            )

            # Sort by date descending and drop duplicates, keeping the first (most recent)
            statistics_df = statistics_df.sort_values("date", ascending=False)
            statistics_df = statistics_df.drop_duplicates(
                subset=["date_normalized"], keep="first"
            )
            statistics_df = statistics_df.sort_values("date", ascending=True)

            # Clean up temporary column
            statistics_df = statistics_df.drop(columns=["date_normalized"])
        statistics_df = statistics_df.sort_values("date", ascending=True)
        statistics_df["date"] = (
            statistics_df["date"]
            .apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
            .astype(str)
        )

        data = statistics_df.to_dict("records")  # type: ignore[assignment]
        data = convert_timestamps_to_strings(data)
        logger.info(f"[Cache] Statistics loaded from database: {len(data)} rows")
        return data, False
    except Exception as e:
        logger.error(f"[Cache] Error loading statistics: {e}")
        return [], False


def generate_realistic_sample_data():
    """
    Generate realistic sample data that spans multiple weeks for better visualization.
    This provides a more comprehensive dataset when no real data is available.

    Returns:
        DataFrame with sample data
    """
    # Start date will be 12 weeks ago
    end_date = datetime.now()
    start_date = end_date - timedelta(days=12 * 7)  # 12 weeks

    # Generate dates for each day in the range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        # Skip weekends to simulate real work patterns
        if current_date.weekday() < 5:  # Monday to Friday
            dates.append(current_date)
        current_date += timedelta(days=1)

    # Generate realistic data with trends and variations
    n_dates = len(dates)

    # Create a base velocity with some randomness
    base_items = 3  # Base number of items per day
    base_points = 30  # Base number of points per day

    # Scope creep - base numbers (slightly lower than completion rate)
    base_created_items = 2  # Base number of items created per day
    base_created_points = 20  # Base number of points created per day

    # Generate data with realistic patterns:
    # 1. General improvement trend over time
    # 2. Occasional spikes and dips
    # 3. Correlation between items and points

    completed_items = []
    completed_points = []
    created_items = []
    created_points = []

    for i in range(n_dates):
        # Calculate progress factor (increases slightly over time)
        progress_factor = 1.0 + (i / n_dates) * 0.5

        # Weekly pattern (more productive mid-week)
        day_of_week = dates[i].weekday()
        day_factor = 0.8 + (1.4 - abs(day_of_week - 2) * 0.15)

        # Random factor (daily variation)
        random_factor = 0.5 + (1.0 * (i % 3)) if i % 10 < 8 else 0

        # Calculate completed items and points
        day_items = max(
            0, round(base_items * progress_factor * day_factor * random_factor)
        )

        # Points are correlated with items but have more variation
        points_per_item = base_points / base_items * (0.8 + random_factor * 0.4)
        day_points = max(0, round(day_items * points_per_item))

        completed_items.append(day_items)
        completed_points.append(day_points)

        # Calculate created items and points (scope creep)
        # Simulate realistic scope creep - higher in early and middle phases
        project_phase = i / n_dates  # 0 to 1 representing project timeline
        scope_creep_factor = (
            1.2 if project_phase < 0.7 else 0.6
        )  # More scope changes early/mid project

        # Occasional scope change spikes
        scope_spike = 3 if i % 14 == 0 else 1  # Occasional planning meetings add scope

        # Calculate created items and points
        day_created_items = max(
            0,
            round(
                base_created_items * scope_creep_factor * scope_spike * random_factor
            ),
        )

        # Points for created items
        created_points_per_item = (
            base_created_points / base_created_items * (0.9 + random_factor * 0.3)
        )
        day_created_points = max(0, round(day_created_items * created_points_per_item))

        created_items.append(day_created_items)
        created_points.append(day_created_points)

    # Create the dataframe
    sample_df = pd.DataFrame(
        {
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "completed_items": completed_items,
            "completed_points": completed_points,
            "created_items": created_items,
            "created_points": created_points,
        }
    )

    return sample_df


def read_and_clean_data(df):
    """
    Clean and validate statistics data.

    Args:
        df: Pandas DataFrame containing raw statistics data

    Returns:
        DataFrame with cleaned and formatted data
    """
    # Ensure required columns exist
    required_columns = ["date", "completed_items", "completed_points"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in data")

    # Check for scope tracking columns and add them if missing
    if "created_items" not in df.columns:
        df["created_items"] = 0
    if "created_points" not in df.columns:
        df["created_points"] = 0

    # Convert date to datetime format
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Drop rows with invalid dates
    df = df.dropna(subset=["date"])

    # Ensure all numeric columns are properly formatted
    numeric_columns = [
        "completed_items",
        "completed_points",
        "created_items",
        "created_points",
    ]
    for col in numeric_columns:
        if col in df.columns:  # Only process columns that exist
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Sort by date
    df = df.sort_values("date", ascending=True)

    # Convert date back to string format
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Include all valid columns (required + scope tracking)
    valid_columns = required_columns + ["created_items", "created_points"]

    # Filter to only include columns that exist in the dataframe
    existing_columns = [col for col in valid_columns if col in df.columns]
    df = df[existing_columns]

    return df


#######################################################################
# UNIFIED DATA FUNCTIONS (v2.0)
#######################################################################


def load_unified_project_data() -> Dict[str, Any]:
    """
    Load unified project data via repository pattern (database).

    QUERY-LEVEL DATA: Statistics and project scope are query-specific.

    Returns:
        Dict: Unified project data structure
    """
    from data.schema import get_default_unified_data

    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return get_default_unified_data()

        # Build unified data from backend
        data = get_default_unified_data()

        # Load project scope
        scope = backend.get_scope(active_profile_id, active_query_id)
        if scope:
            data["project_scope"].update(scope)
            logger.info(
                f"[Cache] Loaded scope from DB - Total: {scope.get('total_items')}, "
                f"Completed: {scope.get('completed_items')}, "
                f"Remaining: {scope.get('remaining_items')}"
            )

        # Load statistics
        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        statistics = []
        if stats_rows:
            for row in stats_rows:
                stat = dict(row)
                if "stat_date" in stat:
                    stat["date"] = stat["stat_date"]
                statistics.append(stat)
            data["statistics"] = statistics

        logger.info(
            f"[Cache] Loaded unified data from database for {active_profile_id}/{active_query_id}: {len(statistics)} stats"
        )
        if statistics:
            logger.info(
                f"[Cache] First stat: date={statistics[0].get('date')}, items={statistics[0].get('remaining_items')}, points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                f"[Cache] Last stat: date={statistics[-1].get('date')}, items={statistics[-1].get('remaining_items')}, points={statistics[-1].get('remaining_total_points')}"
            )
        return data

    except Exception as e:
        logger.error(f"[Cache] Error loading unified project data: {e}")
        return get_default_unified_data()


def save_unified_project_data(data: Dict[str, Any]) -> None:
    """
    Save unified project data via repository pattern (database).

    QUERY-LEVEL DATA: Statistics and project scope are query-specific.

    Args:
        data: Unified project data dictionary
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("[Cache] Cannot save - no active profile/query")
            return

        # Save project scope
        if "project_scope" in data:
            backend.save_scope(
                active_profile_id, active_query_id, data["project_scope"]
            )

        # Save statistics as batch (list)
        if "statistics" in data and data["statistics"]:
            stat_list = []
            for stat in data["statistics"]:
                stat_data = dict(stat)
                # Convert "date" to "stat_date" for database compatibility
                if "date" in stat_data:
                    if "stat_date" not in stat_data or not stat_data["stat_date"]:
                        stat_data["stat_date"] = stat_data["date"]

                # CRITICAL FIX: Normalize stat_date to YYYY-MM-DD format to prevent duplicates
                # Issue: Dates with timestamps (YYYY-MM-DD-HHMMSS) vs plain dates (YYYY-MM-DD)
                # created duplicate database entries because ON CONFLICT only works with exact string match
                if stat_data.get("stat_date"):
                    try:
                        # Parse date in any format and normalize to YYYY-MM-DD
                        parsed_date = pd.to_datetime(
                            stat_data["stat_date"], format="mixed", errors="coerce"
                        )
                        if pd.notna(parsed_date):
                            stat_data["stat_date"] = parsed_date.strftime("%Y-%m-%d")
                        else:
                            logger.warning(
                                f"[Cache] Could not parse date: {stat_data['stat_date']}"
                            )
                            continue
                    except Exception as e:
                        logger.warning(
                            f"[Cache] Error normalizing date {stat_data.get('stat_date')}: {e}"
                        )
                        continue

                # Ensure stat_date exists (required field)
                if not stat_data.get("stat_date"):
                    logger.warning(
                        f"[Cache] Skipping statistic with no date: {stat_data}"
                    )
                    continue
                stat_list.append(stat_data)
            if stat_list:
                backend.save_statistics_batch(
                    active_profile_id, active_query_id, stat_list
                )
                logger.info(f"[Cache] Saved {len(stat_list)} statistics to database")
            else:
                logger.warning(
                    "[Cache] No valid statistics to save (all missing dates)"
                )

        logger.info("[Cache] Saved unified project data to database")
    except Exception as e:
        logger.error(f"[Cache] Error saving unified project data: {e}")
        raise


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
        from data.jira_simple import sync_jira_scope_and_data

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
        from data.jira_simple import (
            get_jira_config,
            validate_jira_config,
            fetch_jira_issues,
        )
        from data.jira_scope_calculator import calculate_jira_project_scope

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
    statistics_data: List[Dict[str, Any]],
    project_scope_data: Dict[str, Any],
    jira_config: Dict[str, Any] | None = None,
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


def migrate_csv_to_json() -> Dict[str, Any]:
    """
    Migrate existing CSV data to unified JSON format.

    Returns:
        Dict: The migrated unified data structure
    """
    # Load existing data
    csv_data, is_sample = load_statistics()
    project_data = load_project_data()

    # Convert CSV to statistics array
    statistics = []
    if csv_data and isinstance(csv_data, list):
        for row in csv_data:
            statistics.append(
                {
                    "date": str(row.get("date", "")),
                    "completed_items": int(row.get("completed_items", 0)),
                    "completed_points": int(row.get("completed_points", 0)),
                    "created_items": int(row.get("created_items", 0)),
                    "created_points": int(row.get("created_points", 0)),
                    "velocity_items": int(
                        row.get("completed_items", 0)
                    ),  # Use completed as velocity
                    "velocity_points": int(row.get("completed_points", 0)),
                }
            )

    # Create unified structure
    unified_data = {
        "project_scope": {
            "total_items": project_data.get("total_items", 0),
            "total_points": project_data.get("total_points", 0),
            "estimated_items": project_data.get("estimated_items", 0),
            "estimated_points": project_data.get("estimated_points", 0),
            "remaining_items": project_data.get(
                "remaining_items", project_data.get("total_items", 0)
            ),
            "remaining_points": project_data.get(
                "remaining_points", project_data.get("total_points", 0)
            ),
        },
        "statistics": statistics,
        "metadata": {
            "source": "csv_import" if not is_sample else "sample_data",
            "last_updated": datetime.now().isoformat(),
            "version": "2.0",
            "jira_query": "",
        },
    }

    # Save unified data
    save_unified_project_data(unified_data)

    # Create backup of old files if not sample data
    if not is_sample:
        _backup_legacy_files()

    return unified_data


def _backup_legacy_files() -> None:
    """Create backup copies of CSV and old JSON files."""
    import shutil

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if os.path.exists("forecast_statistics.csv"):
        backup_name = f"backup_forecast_statistics_{timestamp}.csv"
        shutil.copy2("forecast_statistics.csv", backup_name)
        logger.info(f"[Backup] Created backup: {backup_name}")

    # Note: Don't backup project_data.json as we're updating it in place
    # The legacy migration preserves existing data


#######################################################################
# JIRA CONFIGURATION FUNCTIONS (Feature 003-jira-config-separation)
#######################################################################


def get_default_jira_config() -> Dict[str, Any]:
    """
    Get default JIRA configuration structure.

    Returns:
        Dictionary containing default JIRA configuration
    """
    return {
        "base_url": "",
        "api_version": "v3",
        "token": "",
        "cache_size_mb": 100,
        "max_results_per_call": 100,
        "points_field": "",
        "configured": False,
        "last_test_timestamp": None,
        "last_test_success": None,
    }


def migrate_jira_config(app_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy JIRA settings to new jira_config structure.

    Preserves existing values from legacy fields:
    - jira_token → jira_config.token
    - JIRA_URL env var → jira_config.base_url
    - jira_api_endpoint → extract base_url and api_version
    - jira_story_points_field → jira_config.points_field
    - jira_cache_max_size → jira_config.cache_size_mb
    - jira_max_results → jira_config.max_results_per_call

    Args:
        app_settings: Current app settings dictionary

    Returns:
        Updated app settings with jira_config structure
    """
    import os

    # Start with default configuration
    jira_config = get_default_jira_config()

    # Migrate legacy token field
    legacy_token = app_settings.get("jira_token", "")
    if legacy_token:
        jira_config["token"] = legacy_token
        jira_config["configured"] = True

    # Migrate base URL from environment variable or endpoint
    jira_url_env = os.getenv("JIRA_URL", "")
    if jira_url_env:
        jira_config["base_url"] = jira_url_env.rstrip("/")
        jira_config["configured"] = True

    # Try to extract base URL from legacy jira_api_endpoint
    legacy_endpoint = app_settings.get("jira_api_endpoint", "")
    if legacy_endpoint and not jira_config["base_url"]:
        # Extract base URL from endpoint like "https://company.atlassian.net/rest/api/2/search"
        if "/rest/api/" in legacy_endpoint:
            base_url = legacy_endpoint.split("/rest/api/")[0]
            jira_config["base_url"] = base_url

            # Detect API version from endpoint
            if "/rest/api/3/" in legacy_endpoint:
                jira_config["api_version"] = "v3"
            elif "/rest/api/2/" in legacy_endpoint:
                jira_config["api_version"] = "v2"

    # Migrate other legacy fields
    if "jira_story_points_field" in app_settings:
        points_field = app_settings.get("jira_story_points_field", "")
        if points_field:
            jira_config["points_field"] = points_field

    if "jira_cache_max_size" in app_settings:
        cache_size = app_settings.get("jira_cache_max_size")
        if cache_size is not None:
            jira_config["cache_size_mb"] = int(cache_size)

    if "jira_max_results" in app_settings:
        max_results = app_settings.get("jira_max_results")
        if max_results is not None:
            jira_config["max_results_per_call"] = int(max_results)

    # Add jira_config to settings
    app_settings["jira_config"] = jira_config

    logger.info("[Config] Migrated legacy JIRA settings to jira_config structure")

    return app_settings


def cleanup_legacy_jira_fields(app_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove legacy JIRA fields from app_settings after migration to jira_config.

    Removes these fields that are now in jira_config:
    - jira_api_endpoint (replaced by base_url + api_version)
    - jira_token (replaced by jira_config.token)
    - jira_story_points_field (replaced by jira_config.points_field)
    - jira_cache_max_size (replaced by jira_config.cache_size_mb)
    - jira_max_results (replaced by jira_config.max_results_per_call)

    Args:
        app_settings: Current app settings dictionary

    Returns:
        Cleaned app settings without legacy fields
    """
    legacy_fields = [
        "jira_api_endpoint",
        "jira_token",
        "jira_story_points_field",
        "jira_cache_max_size",
        "jira_max_results",
    ]

    removed_fields = []
    for field in legacy_fields:
        if field in app_settings:
            del app_settings[field]
            removed_fields.append(field)

    if removed_fields:
        logger.info(f"[Config] Removed legacy JIRA fields: {', '.join(removed_fields)}")

    return app_settings


def load_jira_configuration() -> Dict[str, Any]:
    """
    Load JIRA configuration from profile.json.
    Automatically migrates legacy configuration if needed.

    Returns:
        Dictionary containing JIRA configuration with all fields
    """
    app_settings = load_app_settings()

    # Check if migration is needed
    if "jira_config" not in app_settings:
        # Preserve field_mappings before migration
        field_mappings = app_settings.get("field_mappings", {})

        app_settings = migrate_jira_config(app_settings)

        # Restore field_mappings after migration
        if field_mappings:
            app_settings["field_mappings"] = field_mappings

        # Save migrated settings via backend
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            if active_profile_id:
                backend.save_profile(app_settings)
                logger.info("[Config] Saved migrated JIRA configuration to database")
        except Exception as e:
            logger.error(f"[Config] Error saving migrated JIRA configuration: {e}")

    # Cleanup legacy fields after migration if they still exist
    if any(
        field in app_settings
        for field in [
            "jira_api_endpoint",
            "jira_token",
            "jira_story_points_field",
            "jira_cache_max_size",
            "jira_max_results",
        ]
    ):
        # Preserve field_mappings before cleanup
        field_mappings = app_settings.get("field_mappings", {})

        app_settings = cleanup_legacy_jira_fields(app_settings)

        # Restore field_mappings after cleanup
        if field_mappings:
            app_settings["field_mappings"] = field_mappings

        # Save cleaned settings via backend
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            if active_profile_id:
                backend.save_profile(app_settings)
                logger.info("[Config] Removed legacy JIRA fields from database")
        except Exception as e:
            logger.error(f"[Config] Error saving cleaned JIRA configuration: {e}")

    return app_settings.get("jira_config", get_default_jira_config())


def validate_jira_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate JIRA configuration fields.

    Args:
        config: Configuration dictionary with JIRA settings

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Base URL validation
    if not config.get("base_url"):
        return (False, "Base URL is required")

    base_url = config["base_url"]
    if not base_url.startswith(("http://", "https://")):
        return (False, "Base URL must start with http:// or https://")

    # Remove trailing slash for validation
    clean_url = base_url.rstrip("/")
    if not clean_url:
        return (False, "Base URL cannot be empty after removing trailing slash")

    # API version validation
    api_version = config.get("api_version", "v2")
    if api_version not in ["v2", "v3"]:
        return (False, "API version must be 'v2' or 'v3'")

    # Token validation (optional - not required for public JIRA servers)
    # Token can be empty string for anonymous access to public instances
    token = config.get("token", "")
    if token and not token.strip():
        # If token is provided but only whitespace, that's invalid
        return (False, "Personal access token cannot be only whitespace")

    # Cache size validation
    cache_size = config.get("cache_size_mb", 100)
    try:
        cache_size = int(cache_size)
        if not (10 <= cache_size <= 1000):
            return (False, "Cache size must be between 10 and 1000 MB")
    except (ValueError, TypeError):
        return (False, "Cache size must be a valid integer")

    # Max results validation
    max_results = config.get("max_results_per_call", 100)
    try:
        max_results = int(max_results)
        if not (10 <= max_results <= 1000):
            return (False, "Max results must be between 10 and 1000 (JIRA API limit)")
    except (ValueError, TypeError):
        return (False, "Max results must be a valid integer")

    # Points field validation (optional, but must match pattern if provided)
    points_field = config.get("points_field", "")
    if points_field:
        # Basic pattern validation for JIRA custom field format
        if not points_field.startswith("customfield_"):
            return (
                False,
                "Points field must start with 'customfield_' (e.g., 'customfield_10016')",
            )

        # Check if the part after customfield_ is numeric
        try:
            field_id = points_field.replace("customfield_", "")
            int(field_id)
        except ValueError:
            return (
                False,
                "Points field must be in format 'customfield_XXXXX' where XXXXX is numeric",
            )

    return (True, "")


def save_jira_configuration(config: Dict[str, Any]) -> bool:
    """
    Save JIRA configuration to profile.json (shared across all queries in profile).

    Args:
        config: Configuration dictionary with JIRA settings

    Returns:
        True if save successful, False otherwise
    """
    try:
        # Validate configuration first
        is_valid, error_msg = validate_jira_config(config)
        if not is_valid:
            logger.error(f"[Config] Invalid JIRA configuration: {error_msg}")
            return False

        # Use repository pattern - save via backend
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Get active profile ID
        active_profile_id = backend.get_app_state("active_profile_id")
        if not active_profile_id:
            logger.error("[Config] No active profile to save JIRA config to")
            return False

        # Load current profile data
        profile_data = backend.get_profile(active_profile_id) or {
            "forecast_settings": {},
            "show_milestone": False,
            "show_points": False,
            "jira_config": {},
            "field_mappings": {},
            "project_classification": {},
            "flow_type_mappings": {},
        }

        # Update jira_config section
        profile_data["jira_config"] = config
        # Ensure id is in profile_data
        profile_data["id"] = active_profile_id

        # Save via backend
        backend.save_profile(profile_data)
        logger.info("[Config] JIRA configuration saved to database")
        return True

    except Exception as e:
        logger.error(f"[Config] Error saving JIRA configuration: {e}")
        # Database operations don't create temp files - no cleanup needed
        return False


#######################################################################
# DORA/FLOW METRICS HISTORICAL DATA PERSISTENCE (Feature 007)
#######################################################################


def load_metrics_history() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load historical DORA and Flow metrics data from unified project data.

    Returns:
        Dictionary with 'dora_metrics' and 'flow_metrics' keys, each containing
        a list of historical metric snapshots with timestamps.

    Example structure:
        {
            "dora_metrics": [
                {
                    "timestamp": "2025-10-29T10:00:00Z",
                    "time_period_days": 30,
                    "deployment_frequency": {"value": 5.2, "unit": "deployments/month", ...},
                    "lead_time_for_changes": {"value": 2.5, "unit": "days", ...},
                    ...
                }
            ],
            "flow_metrics": [
                {
                    "timestamp": "2025-10-29T10:00:00Z",
                    "time_period_days": 30,
                    "flow_velocity": {"value": 45, "unit": "items/month", ...},
                    ...
                }
            ]
        }
    """
    try:
        unified_data = load_unified_project_data()

        # Return metrics history or empty structure if not found
        return unified_data.get(
            "metrics_history", {"dora_metrics": [], "flow_metrics": []}
        )

    except Exception as e:
        logger.error(f"[Metrics] Error loading metrics history: {e}")
        return {"dora_metrics": [], "flow_metrics": []}


def save_metrics_snapshot(
    metric_type: str, metrics_data: Dict[str, Any], time_period_days: int
) -> bool:
    """
    Save a snapshot of current DORA or Flow metrics to historical data.

    This enables trend analysis by storing metric values over time. Snapshots are
    automatically deduplicated based on timestamp (same day).

    Args:
        metric_type: Either 'dora_metrics' or 'flow_metrics'
        metrics_data: Dictionary containing all calculated metrics for the type
        time_period_days: Time period used for the calculation (e.g., 30, 90)

    Returns:
        True if save successful, False otherwise

    Example:
        >>> dora_data = {
        ...     "deployment_frequency": {"value": 5.2, "unit": "deployments/month"},
        ...     "lead_time_for_changes": {"value": 2.5, "unit": "days"},
        ... }
        >>> save_metrics_snapshot('dora_metrics', dora_data, 30)
        True
    """
    try:
        if metric_type not in ["dora_metrics", "flow_metrics"]:
            logger.error(f"[Metrics] Invalid metric type: {metric_type}")
            return False

        # Load current unified data
        unified_data = load_unified_project_data()

        # Initialize metrics_history if not present
        if "metrics_history" not in unified_data:
            unified_data["metrics_history"] = {
                "dora_metrics": [],
                "flow_metrics": [],
            }

        # Create snapshot with timestamp
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "time_period_days": time_period_days,
            **metrics_data,  # Include all metric calculations
        }

        # Get existing history for this metric type
        history = unified_data["metrics_history"][metric_type]

        # Check if we already have a snapshot from today (deduplicate)
        today_date = datetime.now().date().isoformat()
        existing_today = [
            i
            for i, s in enumerate(history)
            if s.get("timestamp", "")[:10] == today_date
            and s.get("time_period_days") == time_period_days
        ]

        if existing_today:
            # Replace existing snapshot from today with same time period
            history[existing_today[0]] = snapshot
            logger.debug(
                f"[Metrics] Updated {metric_type} snapshot for {time_period_days}d period"
            )
        else:
            # Add new snapshot
            history.append(snapshot)
            logger.debug(
                f"[Metrics] Added {metric_type} snapshot for {time_period_days}d period"
            )

        # Limit history to last 90 days to prevent file bloat
        cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
        history[:] = [s for s in history if s.get("timestamp", "") >= cutoff_date]

        # Sort by timestamp (oldest first)
        history.sort(key=lambda x: x.get("timestamp", ""))

        # Save updated data
        unified_data["metrics_history"][metric_type] = history
        unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
        save_unified_project_data(unified_data)

        logger.info(f"[Metrics] History saved: {len(history)} {metric_type} snapshots")
        return True

    except Exception as e:
        logger.error(f"[Metrics] Error saving snapshot: {e}")
        return False


def get_metric_trend_data(
    metric_type: str, metric_name: str, time_period_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get historical trend data for a specific metric.

    Args:
        metric_type: Either 'dora_metrics' or 'flow_metrics'
        metric_name: Name of the specific metric (e.g., 'deployment_frequency', 'flow_velocity')
        time_period_days: Filter for specific time period (default: 30)

    Returns:
        List of data points with 'date' and 'value' keys for trend visualization

    Example:
        >>> trend = get_metric_trend_data('dora_metrics', 'deployment_frequency', 30)
        >>> print(trend)
        [
            {"date": "2025-10-01", "value": 4.8},
            {"date": "2025-10-08", "value": 5.2},
            {"date": "2025-10-15", "value": 5.5},
        ]
    """
    try:
        history = load_metrics_history()

        if metric_type not in history:
            return []

        metric_history = history[metric_type]

        # Extract trend data for specific metric
        trend_data = []
        for snapshot in metric_history:
            # Filter by time period
            if snapshot.get("time_period_days") != time_period_days:
                continue

            # Extract metric value
            metric_data = snapshot.get(metric_name, {})
            if isinstance(metric_data, dict) and "value" in metric_data:
                trend_data.append(
                    {
                        "date": snapshot.get("timestamp", "")[:10],  # YYYY-MM-DD only
                        "value": metric_data["value"],
                        "unit": metric_data.get("unit", ""),
                    }
                )

        # Sort by date
        trend_data.sort(key=lambda x: x["date"])

        return trend_data

    except Exception as e:
        logger.error(f"[Metrics] Error getting trend data: {e}")
        return []


#######################################################################
# PARAMETER PANEL STATE PERSISTENCE (User Story 1)
#######################################################################


def load_parameter_panel_state() -> dict:
    """
    Load parameter panel state from app settings.

    This function supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    The parameter panel state is stored in localStorage via dcc.Store on the client side,
    but this function provides a server-side default state for initialization.

    Returns:
        dict: Parameter panel state with keys:
            - is_open (bool): Whether panel is expanded
            - last_updated (str): ISO 8601 timestamp
            - user_preference (bool): Whether state was manually set by user

    Example:
        >>> state = load_parameter_panel_state()
        >>> print(state['is_open'])
        False
    """
    from data.schema import get_default_parameter_panel_state

    try:
        app_settings = load_app_settings()

        # Check if parameter_panel_state exists in settings
        if "parameter_panel_state" in app_settings:
            panel_state = app_settings["parameter_panel_state"]

            # Validate required fields
            if isinstance(panel_state, dict) and "is_open" in panel_state:
                return panel_state

        # Return default state if not found or invalid
        return dict(get_default_parameter_panel_state())

    except Exception as e:
        logger.warning(f"[Config] Error loading parameter panel state: {e}")
        return dict(get_default_parameter_panel_state())


def save_parameter_panel_state(is_open: bool, user_preference: bool = True) -> bool:
    """
    Save parameter panel state to app settings.

    This function supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    The parameter panel state is primarily managed client-side via dcc.Store,
    but this function persists the state to profile.json for session continuity.

    Args:
        is_open: Whether the parameter panel should be expanded
        user_preference: Whether this state was explicitly set by the user (vs. default)

    Returns:
        bool: True if save successful, False otherwise

    Example:
        >>> save_parameter_panel_state(is_open=True, user_preference=True)
        True
    """
    try:
        # Create parameter panel state dict
        panel_state = {
            "is_open": bool(is_open),
            "last_updated": datetime.now().isoformat(),
            "user_preference": bool(user_preference),
        }

        # Update app settings via backend
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Store panel state in app_state table (UI preference) as JSON string
        import json

        backend.set_app_state("parameter_panel_state", json.dumps(panel_state))

        logger.debug(
            f"[Config] Parameter panel state saved to database: is_open={is_open}"
        )
        return True

    except Exception as e:
        logger.error(f"[Config] Error saving parameter panel state: {e}")
        return False
