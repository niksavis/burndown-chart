"""Profile CRUD operations.

Extracted from profile_manager.py to respect file-size limits.
Functions that need module-level limits (MAX_PROFILES) lazy-import
data.profile_manager so test patches propagate correctly.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from data.exceptions import PersistenceError

logger = logging.getLogger(__name__)


def create_profile(name: str, settings: dict) -> str:
    """
    Create a new profile with initial settings.

    Args:
        name: Human-readable profile name (e.g., "Apache Kafka")
        settings: Profile configuration (pert_factor, deadline, data_points_count, etc.)

    Returns:
        str: Generated profile_id (UUID format: p_a1b2c3d4e5f6)

    Raises:
        ValueError: If name invalid, duplicate, or max profiles reached
        OSError: If directory creation fails

    Example:
        >>> profile_id = create_profile("Apache Kafka", {
        ...     "pert_factor": 1.2,
        ...     "deadline": "2025-12-31",
        ...     "data_points_count": 20
        ... })
        >>> assert profile_id.startswith("p_") and len(profile_id) == 14
    """
    import data.profile_manager as _pm
    from data._profile_model import Profile, _generate_unique_profile_id
    from data.persistence.factory import get_backend

    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Profile name cannot be empty")

    name = name.strip()
    if len(name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    backend = get_backend()

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    existing_names = [p["name"].lower() for p in all_profiles]
    if name.lower() in existing_names:
        raise ValueError(f"Profile name '{name}' already exists")

    # Check max profiles limit
    if len(all_profiles) >= _pm.MAX_PROFILES:
        raise ValueError(f"Maximum {_pm.MAX_PROFILES} profiles allowed")

    profile_id = _generate_unique_profile_id()

    try:
        profile = Profile(
            id=profile_id,
            name=name,
            description=settings.get("description", ""),
            jira_config=settings.get("jira_config", {}),
            field_mappings=settings.get("field_mappings", {}),
            forecast_settings={
                "pert_factor": settings.get("pert_factor", 1.2),
                "deadline": settings.get("deadline"),
                "data_points_count": settings.get("data_points_count", 12),
            },
            project_classification=settings.get("project_classification", {}),
            flow_type_mappings=settings.get("flow_type_mappings", {}),
            queries=settings.get("queries", []),
            show_milestone=settings.get("show_milestone", False),
            show_points=settings.get("show_points", False),
        )

        backend.save_profile(profile.to_dict())
        logger.info(f"[Profiles] Created profile: {name} ({profile_id})")
        return profile_id

    except (PersistenceError, KeyError, TypeError, ValueError) as e:
        try:
            backend.delete_profile(profile_id)
        except (PersistenceError, KeyError, TypeError, ValueError):
            pass
        logger.error(f"[Profiles] Error creating profile '{name}': {e}")
        raise OSError(f"Failed to create profile: {e}") from e


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
    from data.persistence.factory import get_backend

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    # Update last_used timestamp
    profile["last_used"] = datetime.now(UTC).isoformat()
    backend.save_profile(profile)

    backend.set_app_state("active_profile_id", profile_id)

    # Find most recently used query in this profile
    queries = backend.list_queries(profile_id)
    if queries:
        most_recent_query = max(
            queries, key=lambda q: q.get("last_used", q.get("created_at", ""))
        )
        backend.set_app_state("active_query_id", most_recent_query["id"])
    else:
        backend.set_app_state("active_query_id", "")

    logger.info(
        f"[Profiles] Switched to profile: {profile.get('name', profile_id)} "
        f"({profile_id})"
    )


def delete_profile(profile_id: str) -> None:
    """
    Delete a profile and all its queries with cascade deletion.

    This performs cascade deletion:
    1. Deletes all queries in the profile (using allow_cascade=True)
    2. Removes profile from database

    Args:
        profile_id: Profile to delete

    Raises:
        ValueError: If profile doesn't exist
        OSError: If deletion fails

    Example:
        >>> delete_profile("old-project")
        >>> # Removes profile and all associated queries from database
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    profile_name = profile.get("name", profile_id)

    # If deleting active profile, switch to another one first
    active_profile_id = backend.get_app_state("active_profile_id")
    if profile_id == active_profile_id:
        all_profiles = backend.list_profiles()
        other_profile = next((p for p in all_profiles if p["id"] != profile_id), None)
        if other_profile:
            logger.info(
                f"[Profiles] Auto-switching from '{profile_id}' to "
                f"'{other_profile['id']}' before deletion"
            )
            switch_profile(other_profile["id"])
        else:
            logger.info(
                f"[Profiles] Deleting last profile '{profile_id}' - "
                "clearing active_profile_id"
            )
            backend.set_app_state("active_profile_id", "")

    # CASCADE DELETE: Database backend automatically handles query deletion
    backend.delete_profile(profile_id)
    logger.info(f"[Profiles] Deleted profile: {profile_name} ({profile_id})")


def rename_profile(profile_id: str, new_name: str) -> None:
    """
    Rename an existing profile (updates name in metadata only).

    This is a lightweight operation that only updates the profile name
    in profile.json and the profiles registry. The profile ID remains
    unchanged, so all queries and data files stay in place.

    Args:
        profile_id: ID of profile to rename
        new_name: New name for the profile

    Raises:
        ValueError: If profile doesn't exist, name is empty/invalid, or duplicate
        OSError: If metadata update fails

    Example:
        >>> rename_profile("p_abc123", "Production Environment")
        >>> # Updates name in both profile.json and profiles registry
    """
    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    from data.persistence.factory import get_backend

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    current_name = profile["name"]

    if new_name.lower() == current_name.lower():
        logger.info(
            f"[Profiles] Rename skipped - new name '{new_name}' same as current"
        )
        return

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    for p in all_profiles:
        if p["id"] != profile_id and p["name"].lower() == new_name.lower():
            raise ValueError(f"Profile name '{new_name}' already exists")

    profile["name"] = new_name
    backend.save_profile(profile)
    logger.info(
        f"[Profiles] Renamed profile '{current_name}' to '{new_name}' ({profile_id})"
    )


def duplicate_profile(
    source_profile_id: str, new_name: str, description: str = ""
) -> str:
    """
    Duplicate a profile with all its settings and queries from database.

    Creates a complete copy of the source profile including:
    - All profile settings (JIRA config, field mappings, forecast settings, etc.)
    - All queries with their metadata and JQL strings
    - All query data (JIRA cache, statistics, metrics snapshots, etc.)

    Args:
        source_profile_id: Profile ID to duplicate
        new_name: Name for the new profile
        description: Optional description for the new profile

    Returns:
        str: New profile ID

    Raises:
        ValueError: If source profile doesn't exist,
            name is invalid/duplicate, or max profiles reached
        OSError: If database operations fail

    Example:
        >>> new_id = duplicate_profile(
        ...     "p_abc123", "Production Copy", "Backup of production"
        ... )
        >>> # Creates complete copy with new ID and timestamps
    """
    import data.profile_manager as _pm
    from data._profile_model import _generate_unique_profile_id
    from data.persistence.factory import get_backend

    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    backend = get_backend()

    source_profile = backend.get_profile(source_profile_id)
    if not source_profile:
        raise ValueError(f"Source profile '{source_profile_id}' does not exist")

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    existing_names = [p["name"].lower() for p in all_profiles]
    if new_name.lower() in existing_names:
        raise ValueError(f"Profile name '{new_name}' already exists")

    if len(all_profiles) >= _pm.MAX_PROFILES:
        raise ValueError(f"Maximum {_pm.MAX_PROFILES} profiles allowed")

    new_profile_id = _generate_unique_profile_id()

    try:
        now = datetime.now(UTC).isoformat()
        new_profile_data = source_profile.copy()
        new_profile_data["id"] = new_profile_id
        new_profile_data["name"] = new_name
        new_profile_data["description"] = description
        new_profile_data["created_at"] = now
        new_profile_data["last_used"] = now

        backend.save_profile(new_profile_data)

        # Duplicate all queries from source profile
        source_queries = backend.list_queries(source_profile_id)
        new_query_ids = []

        for source_query in source_queries:
            from data.query_manager import _generate_unique_query_id

            new_query_id = _generate_unique_query_id()
            query_data = backend.get_query(source_profile_id, source_query["id"])
            if query_data:
                query_data["id"] = new_query_id
                query_data["created_at"] = now
                query_data["last_used"] = now
                backend.save_query(new_profile_id, query_data)

            new_query_ids.append(new_query_id)
            logger.debug(
                f"[Profiles] Duplicated query '{source_query['id']}' "
                f"to '{new_query_id}'"
            )

        logger.info(
            f"[Profiles] Duplicated profile '{source_profile_id}' to "
            f"'{new_name}' ({new_profile_id}) with {len(new_query_ids)} queries"
        )
        return new_profile_id

    except (PersistenceError, KeyError, TypeError, ValueError) as e:
        try:
            backend.delete_profile(new_profile_id)
        except (PersistenceError, KeyError, TypeError, ValueError):
            pass
        logger.error(f"[Profiles] Error duplicating profile: {e}")
        raise OSError(f"Failed to duplicate profile: {e}") from e


def list_profiles() -> list[dict]:
    """
    List all available profiles from database.

    Returns:
        List[Dict]: Profile summaries with id, name, query_count, created_at

    Example:
        >>> profiles = list_profiles()
        >>> for p in profiles:
        ...     print(f"{p['name']} ({p['query_count']} queries)")
    """
    from data.persistence.factory import get_backend

    backend = get_backend()
    profiles = backend.list_profiles()

    for profile in profiles:
        profile_id = profile["id"]
        queries = backend.list_queries(profile_id)
        profile["query_count"] = len(queries)

    profiles.sort(key=lambda p: p["last_used"], reverse=True)
    return profiles


def get_profile(profile_id: str) -> dict:
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
    from data._profile_metadata import load_profiles_metadata

    metadata = load_profiles_metadata()

    for profile_data in metadata.get("profiles", []):
        if profile_data["id"] == profile_id:
            return profile_data

    raise FileNotFoundError(f"Profile '{profile_id}' does not exist")
