from __future__ import annotations

import logging
from datetime import UTC, datetime

from data._profile_metadata import load_profiles_metadata
from data._profile_model import Profile, _generate_unique_profile_id
from data.exceptions import PersistenceError
from data.persistence.factory import get_backend
from data.query_manager import _generate_unique_query_id

logger = logging.getLogger(__name__)


def create_profile(name: str, settings: dict) -> str:

    import data.profile_manager as _pm  # noqa: PLC0415

    if not name or not name.strip():
        raise ValueError("Profile name cannot be empty")

    name = name.strip()
    if len(name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    backend = get_backend()

    all_profiles = backend.list_profiles()
    existing_names = [p["name"].lower() for p in all_profiles]
    if name.lower() in existing_names:
        raise ValueError(f"Profile name '{name}' already exists")

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
        except PersistenceError, KeyError, TypeError, ValueError:
            pass
        logger.error(f"[Profiles] Error creating profile '{name}': {e}")
        raise OSError(f"Failed to create profile: {e}") from e


def switch_profile(profile_id: str) -> None:

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    profile["last_used"] = datetime.now(UTC).isoformat()
    backend.save_profile(profile)

    backend.set_app_state("active_profile_id", profile_id)

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

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    profile_name = profile.get("name", profile_id)

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

    backend.delete_profile(profile_id)
    logger.info(f"[Profiles] Deleted profile: {profile_name} ({profile_id})")


def rename_profile(profile_id: str, new_name: str) -> None:

    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

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

    import data.profile_manager as _pm  # noqa: PLC0415

    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    backend = get_backend()

    source_profile = backend.get_profile(source_profile_id)
    if not source_profile:
        raise ValueError(f"Source profile '{source_profile_id}' does not exist")

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

        source_queries = backend.list_queries(source_profile_id)
        new_query_ids = []

        for source_query in source_queries:
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
        except PersistenceError, KeyError, TypeError, ValueError:
            pass
        logger.error(f"[Profiles] Error duplicating profile: {e}")
        raise OSError(f"Failed to duplicate profile: {e}") from e


def list_profiles() -> list[dict]:

    backend = get_backend()
    profiles = backend.list_profiles()

    for profile in profiles:
        profile_id = profile["id"]
        queries = backend.list_queries(profile_id)
        profile["query_count"] = len(queries)

    profiles.sort(key=lambda p: p["last_used"], reverse=True)
    return profiles


def get_profile(profile_id: str) -> dict:

    metadata = load_profiles_metadata()

    for profile_data in metadata.get("profiles", []):
        if profile_data["id"] == profile_id:
            return profile_data

    raise FileNotFoundError(f"Profile '{profile_id}' does not exist")
