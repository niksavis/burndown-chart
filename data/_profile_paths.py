import logging
from pathlib import Path

from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def get_active_profile_workspace() -> Path:

    import data.profile_manager as _pm  # noqa: PLC0415

    backend = get_backend()

    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("No active_profile_id in database")

    profile = backend.get_profile(active_profile_id)
    if not profile:
        raise ValueError(f"Profile '{active_profile_id}' not found in database")

    return _pm.PROFILES_DIR / active_profile_id


def get_active_query_workspace() -> Path:

    import data.profile_manager as _pm  # noqa: PLC0415

    backend = get_backend()

    active_profile_id = backend.get_app_state("active_profile_id")
    active_query_id = backend.get_app_state("active_query_id")

    if not active_profile_id:
        raise ValueError("No active_profile_id in database")
    if not active_query_id:
        raise ValueError("No active_query_id in database")

    query = backend.get_query(active_profile_id, active_query_id)
    if not query:
        raise ValueError(f"Query '{active_query_id}' not found in database")

    return _pm.PROFILES_DIR / active_profile_id / "queries" / active_query_id


def get_profile_file_path(profile_id: str) -> Path:

    import data.profile_manager as _pm  # noqa: PLC0415

    return _pm.PROFILES_DIR / profile_id / "profile.json"


def get_query_file_path(profile_id: str, query_id: str) -> Path:

    import data.profile_manager as _pm  # noqa: PLC0415

    return _pm.PROFILES_DIR / profile_id / "queries" / query_id / "query.json"


def get_jira_cache_path(profile_id: str, query_id: str) -> Path:

    import data.profile_manager as _pm  # noqa: PLC0415

    return _pm.PROFILES_DIR / profile_id / "queries" / query_id / "jira_cache.json"
