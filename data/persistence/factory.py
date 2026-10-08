import logging
from pathlib import Path
from typing import Literal

from data.database import database_exists
from data.installation_context import get_installation_context
from data.persistence import PersistenceBackend
from data.persistence.json_backend import JSONBackend
from data.persistence.sqlite_backend import SQLiteBackend

logger = logging.getLogger(__name__)

_backend_instance: PersistenceBackend | None = None
_backend_type: Literal["sqlite", "json"] = "sqlite"

_installation_context = get_installation_context()
DEFAULT_SQLITE_PATH = str(_installation_context.database_path)
DEFAULT_JSON_PATH = str(_installation_context.database_path.parent)


def get_backend(
    backend_type: Literal["sqlite", "json"] | None = None,
    db_path: str | None = None,
) -> PersistenceBackend:

    global _backend_instance, _backend_type

    requested_type = backend_type or _backend_type

    if (
        _backend_instance is not None
        and _backend_type == requested_type
        and db_path is None
    ):
        return _backend_instance

    if requested_type == "sqlite":
        path = db_path or DEFAULT_SQLITE_PATH
        logger.info(f"Creating SQLiteBackend with path: {path}")
        _backend_instance = SQLiteBackend(path)
    elif requested_type == "json":
        path = db_path or DEFAULT_JSON_PATH
        logger.warning(f"Creating JSONBackend (LEGACY) with path: {path}")
        _backend_instance = JSONBackend(path)
    else:
        raise ValueError(
            f"Unknown backend type: {requested_type}. Use 'sqlite' or 'json'."
        )

    _backend_type = requested_type
    return _backend_instance


def set_backend_type(backend_type: Literal["sqlite", "json"]) -> None:

    global _backend_type, _backend_instance

    if backend_type not in ("sqlite", "json"):
        raise ValueError(
            f"Invalid backend type: {backend_type}. Use 'sqlite' or 'json'."
        )

    if _backend_type != backend_type:
        logger.info(f"Switching backend type from {_backend_type} to {backend_type}")
        _backend_type = backend_type
        _backend_instance = None


def reset_backend() -> None:

    global _backend_instance
    _backend_instance = None
    logger.debug("Backend instance reset")


def get_current_backend_type() -> Literal["sqlite", "json"]:

    return _backend_type


def is_sqlite_available() -> bool:

    return database_exists(Path(DEFAULT_SQLITE_PATH))


def is_json_available() -> bool:

    profiles_path = Path(DEFAULT_JSON_PATH)
    if not profiles_path.exists():
        return False

    for child in profiles_path.iterdir():
        if child.is_dir() and (child / "profile.json").exists():
            return True

    return False
