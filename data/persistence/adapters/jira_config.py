"""Data persistence adapters - JIRA configuration management."""

# Standard library imports
import os
from datetime import datetime
from typing import Any

# Third-party library imports
# Application imports
from configuration.settings import logger
from data.persistence.adapters.app_settings import load_app_settings
from data.persistence.adapters.project_data import load_project_data
from data.persistence.adapters.statistics import load_statistics
from data.persistence.adapters.unified_data import save_unified_project_data


def migrate_csv_to_json() -> dict[str, Any]:
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


def get_default_jira_config() -> dict[str, Any]:
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


def migrate_jira_config(app_settings: dict[str, Any]) -> dict[str, Any]:
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


def cleanup_legacy_jira_fields(app_settings: dict[str, Any]) -> dict[str, Any]:
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


def load_jira_configuration() -> dict[str, Any]:
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


def validate_jira_config(config: dict[str, Any]) -> tuple[bool, str]:
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

    # Points field validation (optional, but must be valid field name if provided)
    points_field = config.get("points_field", "")
    if points_field:
        # Allow standard JIRA fields (timeoriginalestimate, aggregatetimeoriginalestimate, etc.)
        # and custom fields (customfield_XXXXX format)

        # Basic validation: field name should be alphanumeric with underscores
        if not points_field.replace("_", "").isalnum():
            return (
                False,
                "Points field must contain only letters, numbers, and underscores",
            )

        # If it's a custom field, validate the format
        if points_field.startswith("customfield_"):
            # Check if the part after customfield_ is numeric
            try:
                field_id = points_field.replace("customfield_", "")
                int(field_id)
            except ValueError:
                return (
                    False,
                    "Custom field must be in format 'customfield_XXXXX' where XXXXX is numeric",
                )

    return (True, "")


def save_jira_configuration(config: dict[str, Any]) -> bool:
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
