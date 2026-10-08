import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, cast

from data.schema import validate_query_profile
from data.types import QueryProfile

logger = logging.getLogger(__name__)

QUERY_PROFILES_FILE = "jira_query_profiles.json"


def _load_profiles_from_disk() -> list[dict[str, Any]]:

    if not os.path.exists(QUERY_PROFILES_FILE):
        return []

    try:
        with open(QUERY_PROFILES_FILE, encoding="utf-8") as f:
            profiles = json.load(f)
            return profiles if isinstance(profiles, list) else []
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error loading query profiles: {e}")
        return []


def _save_profiles_to_disk(profiles: list[dict[str, Any]]) -> bool:

    try:
        with open(QUERY_PROFILES_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        logger.error(f"Error saving query profiles: {e}")
        return False


def load_query_profiles() -> list[QueryProfile]:

    return cast(list[QueryProfile], _load_profiles_from_disk())


def get_query_profile_by_id(profile_id: str) -> QueryProfile | None:

    all_profiles = load_query_profiles()

    for profile in all_profiles:
        if profile.get("id") == profile_id:
            return profile

    return None


def _build_query_profile(
    name: str,
    jql: str,
    description: str,
    created_at: str,
    last_used: str,
    profile_id: str | None = None,
) -> QueryProfile:
    return {
        "id": profile_id or str(uuid.uuid4()),
        "name": name.strip(),
        "jql": jql.strip(),
        "description": description.strip(),
        "created_at": created_at,
        "last_used": last_used,
        "is_default": False,
    }


def save_query_profile(
    name: str, jql: str, description: str = "", profile_id: str | None = None
) -> dict[str, Any] | None:

    if not name or not name.strip():
        logger.error("Query profile name cannot be empty")
        return None

    if not isinstance(jql, str):
        logger.error("JQL query must be a string")
        return None

    user_profiles = _load_profiles_from_disk()

    for profile in user_profiles:
        if profile.get("name") == name.strip():
            if profile_id is None or profile.get("id") != profile_id:
                logger.error(f"Query profile with name '{name}' already exists")
                return None

    now = datetime.now().isoformat()

    if profile_id:
        for i, profile in enumerate(user_profiles):
            if profile.get("id") == profile_id:
                user_profiles[i].update(
                    {
                        "name": name.strip(),
                        "jql": jql.strip(),
                        "description": description.strip(),
                        "last_used": now,
                    }
                )
                updated_profile = user_profiles[i]
                break
        else:
            logger.error(f"Profile with ID '{profile_id}' not found")
            return None
    else:
        updated_profile = cast(
            dict[str, Any],
            _build_query_profile(
                name=name,
                jql=jql,
                description=description,
                created_at=now,
                last_used=now,
            ),
        )
        user_profiles.append(updated_profile)

    if not validate_query_profile(updated_profile):
        logger.error("Invalid query profile structure")
        return None

    if _save_profiles_to_disk(user_profiles):
        logger.info(f"Saved query profile: {name}")
        return updated_profile
    else:
        return None


def delete_query_profile(profile_id: str) -> bool:

    if profile_id.startswith("default-"):
        logger.error("Cannot delete default query profiles")
        return False

    user_profiles = _load_profiles_from_disk()

    updated_profiles = [p for p in user_profiles if p.get("id") != profile_id]

    if len(updated_profiles) == len(user_profiles):
        logger.error(f"Profile with ID '{profile_id}' not found")
        return False

    if _save_profiles_to_disk(updated_profiles):
        logger.info(f"Deleted query profile: {profile_id}")
        return True
    else:
        return False


def update_query_profile(
    profile_id: str, name: str, jql: str, description: str = ""
) -> dict[str, Any] | None:

    return save_query_profile(name, jql, description, profile_id)


def update_profile_last_used(profile_id: str) -> bool:

    if profile_id.startswith("default-"):
        return True

    user_profiles = _load_profiles_from_disk()

    for profile in user_profiles:
        if profile.get("id") == profile_id:
            profile["last_used"] = datetime.now().isoformat()
            return _save_profiles_to_disk(user_profiles)

    return False


def get_profile_names() -> list[str]:

    profiles = load_query_profiles()
    return [p.get("name", "") for p in profiles if p.get("name")]


def validate_profile_name_unique(name: str, exclude_id: str | None = None) -> bool:

    profiles = load_query_profiles()

    for profile in profiles:
        if profile.get("name") == name.strip():
            if exclude_id is None or profile.get("id") != exclude_id:
                return False

    return True


def set_default_query(profile_id: str) -> bool:

    profiles = _load_profiles_from_disk()

    for profile in profiles:
        profile["is_default"] = False

    for profile in profiles:
        if profile.get("id") == profile_id:
            profile["is_default"] = True
            profile["last_used"] = datetime.now().isoformat()

            success = _save_profiles_to_disk(profiles)
            if success:
                logger.info(f"Set query profile '{profile['name']}' as default")
            return success

    logger.error(f"Query profile with ID '{profile_id}' not found")
    return False


def get_default_query() -> dict[str, Any] | None:

    profiles = _load_profiles_from_disk()

    for profile in profiles:
        if profile.get("is_default", False):
            return profile

    return None


def remove_default_query() -> bool:

    profiles = _load_profiles_from_disk()

    changed = False
    for profile in profiles:
        if profile.get("is_default", False):
            profile["is_default"] = False
            changed = True

    if changed:
        success = _save_profiles_to_disk(profiles)
        if success:
            logger.info("Removed default query setting")
        return success

    return True
