"""
Profile and query workspace management.

This module is the public API for profile-based data organization.
Implementation is split into focused sub-modules:

    _profile_model.py    -- Profile class and ID generation
    _profile_paths.py    -- Path resolution (workspace, file paths)
    _profile_metadata.py -- Metadata load/save, active state helpers
    _profile_crud.py     -- Profile CRUD (create/switch/delete/rename/duplicate)

Constants are defined here (not in sub-modules) so test fixtures can patch
data.profile_manager.PROFILES_DIR in a single place.

Test Support:
    PROFILES_DIR is a module-level constant that can be patched in tests.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level constants (patchable in tests via unittest.mock.patch)
# Note: PROFILES_DIR must be absolute Path for correct patching behavior
PROFILES_DIR = Path("profiles").absolute()
PROFILES_FILE = PROFILES_DIR / "profiles.json"
DEFAULT_PROFILE_ID = "default"
DEFAULT_QUERY_ID = "main"

# Profile limits
MAX_PROFILES = 50
MAX_QUERIES_PER_PROFILE = 100

# ---------------------------------------------------------------------------
# Re-exports from sub-modules (public API - import sites unchanged)
# ---------------------------------------------------------------------------
from data._profile_crud import (  # noqa: E402
    create_profile,
    delete_profile,
    duplicate_profile,
    get_profile,
    list_profiles,
    rename_profile,
    switch_profile,
)
from data._profile_metadata import (  # noqa: E402
    get_active_profile,
    get_active_profile_and_query_display_names,
    get_data_file_path,
    get_settings_file_path,
    is_profiles_mode_enabled,
    load_profiles_metadata,
    save_profiles_metadata,
)
from data._profile_model import Profile, _generate_unique_profile_id  # noqa: E402
from data._profile_paths import (  # noqa: E402
    get_active_profile_workspace,
    get_active_query_workspace,
    get_jira_cache_path,
    get_profile_file_path,
    get_query_file_path,
)

__all__ = [
    # Constants
    "PROFILES_DIR",
    "PROFILES_FILE",
    "DEFAULT_PROFILE_ID",
    "DEFAULT_QUERY_ID",
    "MAX_PROFILES",
    "MAX_QUERIES_PER_PROFILE",
    # Model
    "Profile",
    "_generate_unique_profile_id",
    # Paths
    "get_active_profile_workspace",
    "get_active_query_workspace",
    "get_profile_file_path",
    "get_query_file_path",
    "get_jira_cache_path",
    # Metadata / state
    "load_profiles_metadata",
    "save_profiles_metadata",
    "get_active_profile",
    "is_profiles_mode_enabled",
    "get_data_file_path",
    "get_settings_file_path",
    "get_active_profile_and_query_display_names",
    # CRUD
    "create_profile",
    "switch_profile",
    "delete_profile",
    "rename_profile",
    "duplicate_profile",
    "list_profiles",
    "get_profile",
    # Stubs (T010 / T011)
    "create_query",
    "list_queries",
    "get_query",
    "switch_query",
    "delete_query",
    "migrate_root_to_default_profile",
]


# ============================================================================
# Query Operations (T010) - stubs pending implementation
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


def list_queries(profile_id: str) -> list[dict]:
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


def get_query(profile_id: str, query_id: str) -> dict:
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
# Migration (T011) - stub pending implementation
# ============================================================================


def migrate_root_to_default_profile() -> None:
    """
    One-time migration: Move root-level data to default profile structure.

    Migrates:
                - app_settings.json → profiles/default/profile.json
                    (forecast_settings, jira_config, field_mappings)
        - jira_cache.json → profiles/default/queries/main/jira_cache.json
                - jira_changelog_cache.json →
                    profiles/default/queries/main/jira_changelog_cache.json
                - project_data.json → profiles/default/queries/main/query.json
                    (extracts JQL from project_data)

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
