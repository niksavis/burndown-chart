import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROFILES_DIR = Path("profiles").absolute()
PROFILES_FILE = PROFILES_DIR / "profiles.json"
DEFAULT_PROFILE_ID = "default"
DEFAULT_QUERY_ID = "main"

MAX_PROFILES = 50
MAX_QUERIES_PER_PROFILE = 100

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
    "PROFILES_DIR",
    "PROFILES_FILE",
    "DEFAULT_PROFILE_ID",
    "DEFAULT_QUERY_ID",
    "MAX_PROFILES",
    "MAX_QUERIES_PER_PROFILE",
    "Profile",
    "_generate_unique_profile_id",
    "get_active_profile_workspace",
    "get_active_query_workspace",
    "get_profile_file_path",
    "get_query_file_path",
    "get_jira_cache_path",
    "load_profiles_metadata",
    "save_profiles_metadata",
    "get_active_profile",
    "is_profiles_mode_enabled",
    "get_data_file_path",
    "get_settings_file_path",
    "get_active_profile_and_query_display_names",
    "create_profile",
    "switch_profile",
    "delete_profile",
    "rename_profile",
    "duplicate_profile",
    "list_profiles",
    "get_profile",
    "create_query",
    "list_queries",
    "get_query",
    "switch_query",
    "delete_query",
    "migrate_root_to_default_profile",
]


def create_query(profile_id: str, name: str, jql: str) -> str:

    raise NotImplementedError("T010 - to be implemented")


def list_queries(profile_id: str) -> list[dict]:

    raise NotImplementedError("T010 - to be implemented")


def get_query(profile_id: str, query_id: str) -> dict:

    raise NotImplementedError("T010 - to be implemented")


def switch_query(profile_id: str, query_id: str) -> None:

    raise NotImplementedError("T010 - to be implemented")


def delete_query(profile_id: str, query_id: str) -> None:

    raise NotImplementedError("T010 - to be implemented")


def migrate_root_to_default_profile() -> None:

    raise NotImplementedError("T011 - to be implemented")
