"""
Profile and query workspace management.

This module provides path abstraction for profile-based data organization.
It manages the two-level hierarchy: Profile → Query.

Architecture:
- Profiles: Named workspaces with shared settings (PERT factor, deadline, data_points_count)
- Queries: Named JQL queries within a profile, each with dedicated cache
- Backward Compatibility: Default profile "default" maps to current root-level behavior

Directory Structure:
    profiles/
    ├── profiles.json          # Registry: active profile/query IDs, profile metadata
    ├── default/               # Default profile (migration target)
    │   ├── profile.json       # Profile settings (PERT, deadline, data_points_count)
    │   └── queries/
    │       ├── main/          # Default query (migration target)
    │       │   ├── query.json # Query metadata (JQL string)
    │       │   ├── jira_cache.json
    │       │   └── jira_changelog_cache.json
    │       └── bugs/          # Additional queries
    │           ├── query.json
    │           └── jira_cache.json
    └── kafka/                 # Another profile
        ├── profile.json
        └── queries/...

Constants:
    PROFILES_DIR: Path to profiles/ directory
    PROFILES_FILE: Path to profiles.json registry
    DEFAULT_PROFILE_ID: ID for default profile ("default")
    DEFAULT_QUERY_ID: ID for default query ("main")

Path Resolution Functions:
    get_active_profile_workspace() -> Path: Current profile directory
    get_active_query_workspace() -> Path: Current query directory
    get_profile_file_path(profile_id) -> Path: Path to profile.json
    get_query_file_path(profile_id, query_id) -> Path: Path to query.json
    get_jira_cache_path(profile_id, query_id) -> Path: Path to jira_cache.json

Profile Operations:
    create_profile(name, settings) -> str: Create new profile
    list_profiles() -> List[Dict]: List all profiles
    get_profile(profile_id) -> Dict: Load profile config
    switch_profile(profile_id) -> None: Set active profile
    delete_profile(profile_id) -> None: Delete profile and all queries

Query Operations:
    create_query(profile_id, name, jql) -> str: Create new query
    list_queries(profile_id) -> List[Dict]: List queries in profile
    get_query(profile_id, query_id) -> Dict: Load query config
    switch_query(profile_id, query_id) -> None: Set active query
    delete_query(profile_id, query_id) -> None: Delete query and cache

Migration:
    migrate_root_to_default_profile() -> None: One-time migration of root-level data

Test Support:
    PROFILES_DIR is a module-level constant that can be patched in tests
"""

import json  # noqa: F401 - Used in future implementations
import os  # noqa: F401 - Used in future implementations
from pathlib import Path
from typing import Dict, List, Optional  # noqa: F401 - Used in future implementations

# Module-level constants (patchable in tests via unittest.mock.patch)
# Note: PROFILES_DIR must be absolute Path for correct patching behavior
PROFILES_DIR = Path("profiles").absolute()
PROFILES_FILE = PROFILES_DIR / "profiles.json"
DEFAULT_PROFILE_ID = "default"
DEFAULT_QUERY_ID = "main"


# ============================================================================
# Path Resolution Functions (CRITICAL - blocks all user stories)
# ============================================================================


def get_active_profile_workspace() -> Path:
    """
    Get the workspace directory for the currently active profile.

    Returns:
        Path: Absolute path to active profile directory (e.g., profiles/default/)

    Raises:
        ValueError: If profiles.json missing or active_profile_id invalid

    Example:
        >>> workspace = get_active_profile_workspace()
        >>> profile_config = workspace / "profile.json"
    """
    # Check if profiles.json exists
    if not PROFILES_FILE.exists():
        raise ValueError(
            "profiles.json not found - migration may not have been completed"
        )

    # Load profiles registry
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)

    # Get active profile ID
    active_profile_id = profiles_data.get("active_profile_id")
    if not active_profile_id:
        raise ValueError("No active_profile_id in profiles.json")

    # Validate profile exists in registry
    profiles = profiles_data.get("profiles", {})
    if active_profile_id not in profiles:
        raise ValueError(f"Profile '{active_profile_id}' not found in registry")

    # Return profile workspace directory
    return PROFILES_DIR / active_profile_id


def get_active_query_workspace() -> Path:
    """
    Get the workspace directory for the currently active query.

    Returns:
        Path: Absolute path to active query directory (e.g., profiles/default/queries/main/)

    Raises:
        ValueError: If profiles.json missing or active_query_id invalid

    Example:
        >>> workspace = get_active_query_workspace()
        >>> cache_file = workspace / "jira_cache.json"
    """
    # Check if profiles.json exists
    if not PROFILES_FILE.exists():
        raise ValueError(
            "profiles.json not found - migration may not have been completed"
        )

    # Load profiles registry
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)

    # Get active profile and query IDs
    active_profile_id = profiles_data.get("active_profile_id")
    active_query_id = profiles_data.get("active_query_id")

    if not active_profile_id:
        raise ValueError("No active_profile_id in profiles.json")
    if not active_query_id:
        raise ValueError("No active_query_id in profiles.json")

    # Validate profile exists
    profiles = profiles_data.get("profiles", {})
    if active_profile_id not in profiles:
        raise ValueError(f"Profile '{active_profile_id}' not found in registry")

    # Validate query exists in profile's query list
    profile_data = profiles[active_profile_id]
    queries = profile_data.get("queries", [])
    if active_query_id not in queries:
        raise ValueError(
            f"Query '{active_query_id}' not found in profile '{active_profile_id}'"
        )

    # Return query workspace directory
    return PROFILES_DIR / active_profile_id / "queries" / active_query_id


def get_profile_file_path(profile_id: str) -> Path:
    """
    Get the path to profile.json for a specific profile.

    Args:
        profile_id: Profile identifier (e.g., "default", "kafka")

    Returns:
        Path: Absolute path to profile.json (e.g., profiles/kafka/profile.json)

    Example:
        >>> path = get_profile_file_path("kafka")
        >>> with open(path) as f:
        ...     settings = json.load(f)
    """
    return PROFILES_DIR / profile_id / "profile.json"


def get_query_file_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to query.json for a specific query.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier (e.g., "main", "bugs")

    Returns:
        Path: Absolute path to query.json (e.g., profiles/kafka/queries/bugs/query.json)

    Example:
        >>> path = get_query_file_path("kafka", "12w")
        >>> with open(path) as f:
        ...     query = json.load(f)
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "query.json"


def get_jira_cache_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to jira_cache.json for a specific query.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Path: Absolute path to jira_cache.json (e.g., profiles/kafka/queries/bugs/jira_cache.json)

    Example:
        >>> cache_path = get_jira_cache_path("kafka", "main")
        >>> if cache_path.exists():
        ...     with open(cache_path) as f:
        ...         cache = json.load(f)
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "jira_cache.json"


# ============================================================================
# Backward Compatibility Helpers (T005 - Legacy Mode Support)
# ============================================================================


def is_profiles_mode_enabled() -> bool:
    """
    Check if profiles mode is enabled (profiles.json exists).

    Returns:
        bool: True if profiles.json exists, False for legacy mode

    Example:
        >>> if is_profiles_mode_enabled():
        ...     path = get_active_query_workspace() / "jira_cache.json"
        ... else:
        ...     path = Path("jira_cache.json")  # Legacy root-level
    """
    return PROFILES_FILE.exists()


def get_data_file_path(filename: str) -> Path:
    """
    Get path to a data file with backward compatibility.

    If profiles.json exists: Returns path in active query workspace
    If profiles.json missing: Returns path in project root (legacy mode)

    Args:
        filename: Data file name (e.g., "jira_cache.json", "app_settings.json")

    Returns:
        Path: Absolute path to data file

    Example:
        >>> # In profiles mode: profiles/default/queries/main/jira_cache.json
        >>> # In legacy mode: jira_cache.json (root level)
        >>> cache_path = get_data_file_path("jira_cache.json")
    """
    if is_profiles_mode_enabled():
        try:
            # Profile mode: use active query workspace
            return get_active_query_workspace() / filename
        except ValueError:
            # profiles.json exists but is malformed - fall back to legacy
            return Path(filename).absolute()
    else:
        # Legacy mode: use root directory
        return Path(filename).absolute()


def get_settings_file_path(filename: str) -> Path:
    """
    Get path to a settings file with backward compatibility.

    Settings files (app_settings.json, project_data.json) are stored at:
    - Profile mode: profiles/{profile_id}/queries/{query_id}/{filename}
    - Legacy mode: {filename} (root level)

    Args:
        filename: Settings file name (e.g., "app_settings.json")

    Returns:
        Path: Absolute path to settings file

    Example:
        >>> settings_path = get_settings_file_path("app_settings.json")
    """
    return get_data_file_path(filename)  # Same logic as data files


# ============================================================================
# Profile Operations (T008-T009)
# ============================================================================


def create_profile(name: str, settings: Dict) -> str:
    """
    Create a new profile with initial settings.

    Args:
        name: Human-readable profile name (e.g., "Apache Kafka")
        settings: Profile configuration (pert_factor, deadline, data_points_count, etc.)

    Returns:
        str: Generated profile_id (slugified name)

    Example:
        >>> profile_id = create_profile("Apache Kafka", {
        ...     "pert_factor": 1.2,
        ...     "deadline": "2025-12-31",
        ...     "data_points_count": 20
        ... })
        >>> assert profile_id == "apache-kafka"
    """
    raise NotImplementedError("T008 - to be implemented")


def list_profiles() -> List[Dict]:
    """
    List all available profiles.

    Returns:
        List[Dict]: Profile summaries with id, name, query_count, created_at

    Example:
        >>> profiles = list_profiles()
        >>> for p in profiles:
        ...     print(f"{p['name']} ({p['query_count']} queries)")
    """
    raise NotImplementedError("T008 - to be implemented")


def get_profile(profile_id: str) -> Dict:
    """
    Load profile configuration.

    Args:
        profile_id: Profile identifier

    Returns:
        Dict: Profile config (forecast_settings, jira_config, field_mappings, etc.)

    Raises:
        FileNotFoundError: If profile doesn't exist

    Example:
        >>> config = get_profile("kafka")
        >>> print(config["forecast_settings"]["pert_factor"])
    """
    raise NotImplementedError("T008 - to be implemented")


def switch_profile(profile_id: str) -> None:
    """
    Switch to a different profile.

    Args:
        profile_id: Target profile identifier

    Raises:
        ValueError: If profile doesn't exist

    Example:
        >>> switch_profile("kafka")
        >>> # App now uses kafka profile settings and queries
    """
    raise NotImplementedError("T009 - to be implemented")


def delete_profile(profile_id: str) -> None:
    """
    Delete a profile and all its queries.

    Args:
        profile_id: Profile to delete

    Raises:
        ValueError: If trying to delete active profile or default profile

    Example:
        >>> delete_profile("old-project")
        >>> # Removes profiles/old-project/ directory entirely
    """
    raise NotImplementedError("T009 - to be implemented")


# ============================================================================
# Query Operations (T010)
# ============================================================================


def create_query(profile_id: str, name: str, jql: str) -> str:
    """
    Create a new query within a profile.

    Args:
        profile_id: Parent profile identifier
        name: Human-readable query name (e.g., "Last 12 Weeks")
        jql: JQL query string

    Returns:
        str: Generated query_id (slugified name)

    Example:
        >>> query_id = create_query("kafka", "Last 12 Weeks",
        ...     "project = KAFKA AND created >= -12w ORDER BY created DESC")
        >>> assert query_id == "last-12-weeks"
    """
    raise NotImplementedError("T010 - to be implemented")


def list_queries(profile_id: str) -> List[Dict]:
    """
    List all queries in a profile.

    Args:
        profile_id: Profile identifier

    Returns:
        List[Dict]: Query summaries with id, name, jql_preview, created_at

    Example:
        >>> queries = list_queries("kafka")
        >>> for q in queries:
        ...     print(f"{q['name']}: {q['jql_preview']}")
    """
    raise NotImplementedError("T010 - to be implemented")


def get_query(profile_id: str, query_id: str) -> Dict:
    """
    Load query configuration.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Dict: Query config (jql_query, created_at, last_used_at)

    Raises:
        FileNotFoundError: If query doesn't exist

    Example:
        >>> config = get_query("kafka", "12w")
        >>> print(config["jql_query"])
    """
    raise NotImplementedError("T010 - to be implemented")


def switch_query(profile_id: str, query_id: str) -> None:
    """
    Switch to a different query within the current profile.

    Args:
        profile_id: Profile identifier (must match active profile)
        query_id: Target query identifier

    Raises:
        ValueError: If query doesn't exist or profile mismatch

    Example:
        >>> switch_query("kafka", "bugs")
        >>> # App now loads data from profiles/kafka/queries/bugs/jira_cache.json
    """
    raise NotImplementedError("T010 - to be implemented")


def delete_query(profile_id: str, query_id: str) -> None:
    """
    Delete a query and its cache.

    Args:
        profile_id: Profile identifier
        query_id: Query to delete

    Raises:
        ValueError: If trying to delete active query or only query in profile

    Example:
        >>> delete_query("kafka", "old-query")
        >>> # Removes profiles/kafka/queries/old-query/ directory
    """
    raise NotImplementedError("T010 - to be implemented")


# ============================================================================
# Migration (T011)
# ============================================================================


def migrate_root_to_default_profile() -> None:
    """
    One-time migration: Move root-level data to default profile structure.

    Migrates:
        - app_settings.json → profiles/default/profile.json (forecast_settings, jira_config, field_mappings)
        - jira_cache.json → profiles/default/queries/main/jira_cache.json
        - jira_changelog_cache.json → profiles/default/queries/main/jira_changelog_cache.json
        - project_data.json → profiles/default/queries/main/query.json (extracts JQL from project_data)

    Creates:
        - profiles/profiles.json with default profile and main query active
        - profiles/default/profile.json with migrated settings
        - profiles/default/queries/main/query.json with JQL string

    Preserves:
        - All cache data (100% preservation requirement - SC-005)
        - All settings values unchanged
        - Original files left intact as backup

    Performance:
        - Must complete <5s for 50MB jira_cache.json (SC-012)

    Example:
        >>> migrate_root_to_default_profile()
        >>> # Root files still exist, but app now uses profiles/ structure
    """
    raise NotImplementedError("T011 - to be implemented")
