"""Profile metadata and active state management.

Extracted from profile_manager.py to respect file-size limits.
Functions that need module-level constants (PROFILES_DIR, DEFAULT_PROFILE_ID,
DEFAULT_QUERY_ID) lazy-import data.profile_manager so test patches propagate.
"""

from __future__ import annotations

import logging
from pathlib import Path

from data._profile_model import Profile
from data._profile_paths import get_active_query_workspace
from data.exceptions import PersistenceError
from data.persistence.factory import get_backend
from data.query_manager import get_active_query_id

logger = logging.getLogger(__name__)


def load_profiles_metadata() -> dict:
    """
    Load profiles registry from database with schema validation.

    Returns:
        Dict: Profiles metadata with active_profile_id, active_query_id, profiles list

    Example:
        >>> meta = load_profiles_metadata()
        >>> print(meta["active_profile_id"])  # "default"
        >>> print(len(meta["profiles"]))      # Number of profiles
    """
    import data.profile_manager as _pm  # noqa: PLC0415

    backend = get_backend()

    try:
        # Get active IDs from app_state
        active_profile_id = (
            backend.get_app_state("active_profile_id") or _pm.DEFAULT_PROFILE_ID
        )
        active_query_id = (
            backend.get_app_state("active_query_id") or _pm.DEFAULT_QUERY_ID
        )

        # Get all profiles
        profiles_list = backend.list_profiles()
        profiles_dict = {p["profile_id"]: p for p in profiles_list}

        return {
            "version": "3.0",
            "active_profile_id": active_profile_id,
            "active_query_id": active_query_id,
            "profiles": profiles_dict,
        }

    except (PersistenceError, KeyError, TypeError, ValueError) as e:
        import data.profile_manager as _pm  # noqa: PLC0415 (already imported above but guard)

        logger.error(f"[Profiles] Error loading metadata from database: {e}")
        return {
            "version": "3.0",
            "active_profile_id": _pm.DEFAULT_PROFILE_ID,
            "active_query_id": _pm.DEFAULT_QUERY_ID,
            "profiles": {},
            "_error": f"Error loading from database: {e}",
        }


def save_profiles_metadata(metadata: dict) -> bool:
    """
    Save profiles registry to database (no longer writes profiles.json).

    Args:
        metadata: Profiles registry to save

    Returns:
        bool: True if successful, False on error

    Example:
        >>> meta = load_profiles_metadata()
        >>> meta["active_profile_id"] = "new-profile"
        >>> save_profiles_metadata(meta)
    """

    backend = get_backend()

    try:
        active_profile_id = metadata.get("active_profile_id")
        active_query_id = metadata.get("active_query_id")

        if active_profile_id:
            backend.set_app_state("active_profile_id", active_profile_id)
        if active_query_id:
            backend.set_app_state("active_query_id", active_query_id)

        logger.debug("[Profiles] Metadata saved to database")
        return True

    except (PersistenceError, KeyError, TypeError, ValueError) as e:
        logger.error(f"[Profiles] Error saving metadata to database: {e}")
        return False


def get_active_profile() -> Profile | None:
    """
    Get currently active profile object from database.

    Returns:
        Profile object if found, None if active profile doesn't exist

    Example:
        >>> profile = get_active_profile()
        >>> if profile:
        ...     print(f"Active: {profile.name}")
    """

    backend = get_backend()
    active_id = backend.get_app_state("active_profile_id")

    if not active_id:
        return None

    profile_data = backend.get_profile(active_id)
    if profile_data:
        profile_data["id"] = active_id
        return Profile.from_dict(profile_data)

    logger.warning(f"[Profiles] Active profile '{active_id}' not found in database")
    return None


def is_profiles_mode_enabled() -> bool:
    """
    Check if profiles mode is enabled (database exists).

    After database migration, we check if the SQLite database exists instead
    of checking for profiles.json.

    Returns:
        bool: True if database exists, False for legacy mode

    Example:
        >>> if is_profiles_mode_enabled():
        ...     # Use database backend
        ... else:
        ...     # Legacy file-based mode
    """
    import data.profile_manager as _pm  # noqa: PLC0415

    db_path = _pm.PROFILES_DIR / "burndown.db"
    return db_path.exists()


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
            return get_active_query_workspace() / filename
        except ValueError:
            return Path(filename).absolute()
    else:
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
    return get_data_file_path(filename)


def get_active_profile_and_query_display_names() -> dict:
    """
    Get display names for currently active profile and query via repository pattern.

    Returns:
        dict: Dictionary with profile_name and query_name
            (or None if not in profiles mode)
            Example: {
                "profile_name": "Apache Kafka",
                "query_name": "Development Sprint",
            }

    Example:
        >>> names = get_active_profile_and_query_display_names()
        >>> if names["profile_name"]:
        ...     print(f"Profile: {names['profile_name']}, Query: {names['query_name']}")
    """
    if not is_profiles_mode_enabled():
        return {"profile_name": None, "query_name": None}

    try:
        profile = get_active_profile()
        profile_name = profile.name if profile else None

        query_id = get_active_query_id()
        query_name = None

        if profile and query_id:
            backend = get_backend()
            query_data = backend.get_query(profile.id, query_id)

            if query_data:
                query_name = query_data.get("name", query_id.replace("_", " ").title())
            else:
                query_name = query_id.replace("_", " ").title()

        return {"profile_name": profile_name, "query_name": query_name}

    except (
        PersistenceError,
        KeyError,
        TypeError,
        ValueError,
        AttributeError,
    ) as e:
        logger.warning(f"Failed to get active profile/query names: {e}")
        return {"profile_name": None, "query_name": None}
