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

    import data.profile_manager as _pm  # noqa: PLC0415

    backend = get_backend()

    try:
        active_profile_id = (
            backend.get_app_state("active_profile_id") or _pm.DEFAULT_PROFILE_ID
        )
        active_query_id = (
            backend.get_app_state("active_query_id") or _pm.DEFAULT_QUERY_ID
        )

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

    import data.profile_manager as _pm  # noqa: PLC0415

    db_path = _pm.PROFILES_DIR / "burndown.db"
    return db_path.exists()


def get_data_file_path(filename: str) -> Path:

    if is_profiles_mode_enabled():
        try:
            return get_active_query_workspace() / filename
        except ValueError:
            return Path(filename).absolute()
    else:
        return Path(filename).absolute()


def get_settings_file_path(filename: str) -> Path:

    return get_data_file_path(filename)


def get_active_profile_and_query_display_names() -> dict:

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
