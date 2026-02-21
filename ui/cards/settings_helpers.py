"""
Settings Helper Functions for Card Components

This module provides helper functions to retrieve default values from
application settings. These functions are used by card components to
initialize their state with persisted user preferences.

All functions follow a consistent pattern:
1. Try to load from persistence layer
2. Return sensible default on failure
3. Never raise exceptions to caller
"""


def _get_default_data_source() -> str:
    """
    Determine the default data source based on persisted settings.

    Returns:
        str: "JIRA" (default) or "CSV" based on last_used_data_source setting
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        # Use persisted value, default to JIRA (swapped order)
        data_source = app_settings.get("last_used_data_source", "JIRA")
        # Return JIRA if the value is empty or None
        return data_source if data_source else "JIRA"
    except (ImportError, Exception):
        return "JIRA"  # Default to JIRA if import fails or any other error


def _get_default_jql_query() -> str:
    """
    Get the default JQL query from app settings.

    Returns:
        str: JQL query from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jql_profile_id() -> str:
    """
    Get the active JQL profile ID from app settings.

    Returns:
        str: Profile ID from settings or empty string if none
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("active_jql_profile_id", "")
    except (ImportError, Exception):
        return ""


def _get_default_jira_story_points_field() -> str:
    """
    Get the default JIRA story points field from app settings.

    Returns:
        str: Story points field from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_story_points_field", "")
    except ImportError:
        return ""


def _get_default_jira_cache_max_size() -> int:
    """
    Get the default JIRA cache max size from app settings.

    Returns:
        int: Cache max size from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_cache_max_size", 100)
    except ImportError:
        return 100


def _get_default_jira_max_results() -> int:
    """
    Get the default JIRA max results from app settings.

    Returns:
        int: Max results from settings or default value
    """
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jira_max_results", 1000)
    except ImportError:
        return 1000


def _get_query_profile_options() -> list[dict[str, str]]:
    """
    Get options for the query profile dropdown.

    Returns:
        List of option dictionaries for the dropdown in format
        [{"label": str, "value": str}]
    """
    try:
        from data.jira.query_profiles import load_query_profiles

        profiles = load_query_profiles()
        options = []

        # Add saved query profiles only (no default profiles)
        for profile in profiles:
            label = profile["name"]
            if profile.get("is_default", False):
                label += " [Default]"  # Add indicator for default
            options.append(
                {
                    "label": label,
                    "value": profile["id"],
                }
            )

        # Don't add "New Query" option - keep dropdown for saved queries only
        return options

    except (ImportError, Exception):
        # Return empty list if query manager fails
        return []
