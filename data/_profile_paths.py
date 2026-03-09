"""Path resolution functions for profile and query workspaces.

Extracted from profile_manager.py to respect file-size limits.
All functions lazy-import data.profile_manager to read PROFILES_DIR so
that test fixtures patching data.profile_manager.PROFILES_DIR take effect.
"""

import logging
from pathlib import Path

from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def get_active_profile_workspace() -> Path:
    """
    Get the workspace directory for the currently active profile.

    Returns:
        Path: Absolute path to active profile directory (e.g., profiles/default/)

    Raises:
        ValueError: If database not found or active_profile_id invalid

    Example:
        >>> workspace = get_active_profile_workspace()
        >>> profile_config = workspace / "profile.json"
    """
    import data.profile_manager as _pm

    backend = get_backend()

    # Get active profile ID from app_state
    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("No active_profile_id in database")

    # Validate profile exists
    profile = backend.get_profile(active_profile_id)
    if not profile:
        raise ValueError(f"Profile '{active_profile_id}' not found in database")

    return _pm.PROFILES_DIR / active_profile_id


def get_active_query_workspace() -> Path:
    """
    Get the workspace directory for the currently active query.

    Returns:
        Path: Absolute path to active query directory
            (e.g., profiles/default/queries/main/)

    Raises:
        ValueError: If database not found or active_query_id invalid

    Example:
        >>> workspace = get_active_query_workspace()
        >>> cache_file = workspace / "jira_cache.json"
    """
    import data.profile_manager as _pm

    backend = get_backend()

    # Get active profile and query IDs from app_state
    active_profile_id = backend.get_app_state("active_profile_id")
    active_query_id = backend.get_app_state("active_query_id")

    if not active_profile_id:
        raise ValueError("No active_profile_id in database")
    if not active_query_id:
        raise ValueError("No active_query_id in database")

    # Validate query exists in database
    query = backend.get_query(active_profile_id, active_query_id)
    if not query:
        raise ValueError(f"Query '{active_query_id}' not found in database")

    return _pm.PROFILES_DIR / active_profile_id / "queries" / active_query_id


def get_profile_file_path(profile_id: str) -> Path:
    """
    Get the path to profile.json for a specific profile.

    DEPRECATED: Profile data is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier (e.g., "default", "kafka")

    Returns:
        Path: Absolute path to profile.json (e.g., profiles/kafka/profile.json)

    Example:
        >>> path = get_profile_file_path("kafka")  # For exports only
    """
    import data.profile_manager as _pm

    return _pm.PROFILES_DIR / profile_id / "profile.json"


def get_query_file_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to query.json for a specific query.

    DEPRECATED: Query data is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier (e.g., "main", "bugs")

    Returns:
        Path: Absolute path to query.json
            (e.g., profiles/kafka/queries/bugs/query.json)

    Example:
        >>> path = get_query_file_path("kafka", "12w")  # For exports only
    """
    import data.profile_manager as _pm

    return _pm.PROFILES_DIR / profile_id / "queries" / query_id / "query.json"


def get_jira_cache_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to jira_cache.json for a specific query.

    DEPRECATED: JIRA cache is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Path: Absolute path to jira_cache.json
            (e.g., profiles/kafka/queries/bugs/jira_cache.json)

    Example:
        >>> cache_path = get_jira_cache_path("kafka", "main")  # For exports only
    """
    import data.profile_manager as _pm

    return _pm.PROFILES_DIR / profile_id / "queries" / query_id / "jira_cache.json"
