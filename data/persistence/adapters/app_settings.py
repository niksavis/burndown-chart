"""Data persistence adapters - App settings save/load operations."""

# Standard library imports
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Third-party library imports
import pandas as pd

# Application imports
from configuration.settings import logger

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
    # Lazy import to avoid circular dependency
    from configuration.settings import DEFAULT_DATA_POINTS_COUNT, DEFAULT_PERT_FACTOR

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
    # Lazy import to avoid circular dependency
    from configuration.settings import (
        DEFAULT_PERT_FACTOR,
        DEFAULT_DEADLINE,
        DEFAULT_DATA_POINTS_COUNT,
    )

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


