import logging
import sqlite3
from datetime import datetime
from typing import Any

from data.exceptions import PersistenceError
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


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

    from configuration.settings import (  # noqa: PLC0415
        DEFAULT_DATA_POINTS_COUNT,
        DEFAULT_PERT_FACTOR,
    )

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
        else "JIRA",
        "active_jql_profile_id": active_jql_profile_id
        if active_jql_profile_id is not None
        else "",
    }

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

    if cache_metadata is not None:
        settings["cache_metadata"] = cache_metadata

    try:
        existing_settings = load_app_settings()
        logger.debug(
            "[Config] Loading existing settings. Keys: "
            f"{list(existing_settings.keys())}"
        )

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
            "production_environment_value",
            "flow_end_statuses",
            "active_statuses",
            "flow_start_statuses",
            "wip_statuses",
            "flow_type_mappings",
            "field_mapping_notes",
            "cache_metadata",
        ]

        for key in preserve_keys:
            if key in existing_settings and key not in settings:
                settings[key] = existing_settings[key]
                logger.debug(f"[Config] Preserved existing {key}")
                if key == "field_mappings":
                    logger.debug(
                        f"[Config] Preserving field_mappings: {existing_settings[key]}"
                    )

        logger.debug(
            f"[Config] Final settings keys before write: {list(settings.keys())}"
        )
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Config] Could not load existing settings")
        persistence_error = PersistenceError("Failed to load existing app settings")
        logger.debug("[Config] %s: %s", type(persistence_error).__name__, e)

    try:
        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        if not active_profile_id:
            logger.error("[Config] No active profile to save settings to")
            return

        existing_profile = backend.get_profile(active_profile_id) or {}

        profile_data = {
            "id": existing_profile.get("id", active_profile_id),
            "name": existing_profile.get("name", "Default"),
            "description": existing_profile.get("description", ""),
            "created_at": existing_profile.get(
                "created_at", datetime.now().isoformat()
            ),
            "last_used": datetime.now().isoformat(),
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

        backend.save_profile(profile_data)
        logger.info(
            f"[Config] Settings saved to database. Profile: {profile_data['name']}"
        )
        logger.debug(
            "[Config] Saved forecast_settings: "
            f"pert_factor={profile_data['forecast_settings'].get('pert_factor')}, "
            f"deadline={profile_data['forecast_settings'].get('deadline')}, "
            "data_points_count="
            f"{profile_data['forecast_settings'].get('data_points_count')}, "
            f"milestone={profile_data['forecast_settings'].get('milestone')}"
        )
        logger.debug(
            "[Config] Saved UI settings: "
            f"show_milestone={profile_data.get('show_milestone')}, "
            f"show_points={profile_data.get('show_points')}"
        )
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Config] Error saving app settings")
        persistence_error = PersistenceError("Failed to save app settings")
        logger.debug("[Config] %s: %s", type(persistence_error).__name__, e)


def load_app_settings() -> dict[str, Any]:

    from configuration.settings import (  # noqa: PLC0415
        DEFAULT_DATA_POINTS_COUNT,
        DEFAULT_DEADLINE,
        DEFAULT_PERT_FACTOR,
    )

    default_settings = {
        "pert_factor": DEFAULT_PERT_FACTOR,
        "deadline": DEFAULT_DEADLINE,
        "data_points_count": DEFAULT_DATA_POINTS_COUNT,
        "show_milestone": False,
        "milestone": None,
        "show_points": False,
        "jql_query": "project = JRASERVER",
        "last_used_data_source": "JIRA",
        "active_jql_profile_id": "",
        "cache_metadata": {
            "last_cache_key": None,
            "last_cache_timestamp": None,
            "cache_config_hash": None,
        },
    }

    try:
        backend = get_backend()

        active_id = backend.get_app_state("active_profile_id")

        if not active_id:
            logger.info("[Config] No active profile, using defaults")
            return default_settings

        profile_data = backend.get_profile(active_id)

        if not profile_data:
            logger.info(f"[Config] Profile {active_id} not found, using defaults")
            return default_settings

        logger.info(f"[Config] Settings loaded via backend for profile {active_id}")

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
            "jql_query": "project = JRASERVER",
            "last_used_data_source": "JIRA",
            "active_jql_profile_id": "",
            "cache_metadata": {
                "last_cache_key": None,
                "last_cache_timestamp": None,
                "cache_config_hash": None,
            },
            "jira_config": profile_data.get("jira_config", {}),
            "field_mappings": profile_data.get("field_mappings", {}),
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
            "flow_type_mappings": profile_data.get("flow_type_mappings", {}),
        }

        for key, default_value in default_settings.items():
            if key not in settings:
                settings[key] = default_value

        logger.debug(
            "[Config] Loaded forecast_settings: "
            f"pert_factor={settings.get('pert_factor')}, "
            f"deadline={settings.get('deadline')}, "
            f"data_points_count={settings.get('data_points_count')}, "
            f"milestone={settings.get('milestone')}"
        )
        logger.debug(
            "[Config] Loaded UI settings: "
            f"show_milestone={settings.get('show_milestone')}, "
            f"show_points={settings.get('show_points')}"
        )

        return settings

    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Config] Error loading app settings via backend")
        persistence_error = PersistenceError("Failed to load app settings via backend")
        logger.debug("[Config] %s: %s", type(persistence_error).__name__, e)
        return default_settings
