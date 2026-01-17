"""
Backend factory for persistence layer.

Provides centralized backend management with configurable switching:
- SQLiteBackend (default for new profiles)
- JSONBackend (legacy fallback for migration)

Usage:
    from data.persistence.factory import get_backend, set_backend_type

    # Get default backend (SQLite)
    backend = get_backend()
    profile = backend.get_profile("kafka")

    # Switch to legacy JSON backend (for migration testing)
    set_backend_type("json")
    backend = get_backend()
"""

import logging
from typing import Literal, Optional
from pathlib import Path

from data.persistence import PersistenceBackend
from data.persistence.sqlite_backend import SQLiteBackend
from data.persistence.json_backend import JSONBackend
from data.installation_context import get_installation_context

logger = logging.getLogger(__name__)

# Global backend instance (singleton per backend type)
_backend_instance: Optional[PersistenceBackend] = None
_backend_type: Literal["sqlite", "json"] = "sqlite"

# Default paths - use installation context for database path
_installation_context = get_installation_context()
DEFAULT_SQLITE_PATH = str(_installation_context.database_path)
DEFAULT_JSON_PATH = str(_installation_context.database_path.parent)


def get_backend(
    backend_type: Optional[Literal["sqlite", "json"]] = None,
    db_path: Optional[str] = None,
) -> PersistenceBackend:
    """
    Get persistence backend instance (singleton pattern).

    Args:
        backend_type: Backend type ("sqlite" or "json"). Uses global default if None.
        db_path: Custom database path. Uses defaults if None.

    Returns:
        PersistenceBackend: Configured backend instance

    Example:
        >>> # Get default SQLite backend
        >>> backend = get_backend()

        >>> # Get JSON backend for migration
        >>> legacy_backend = get_backend(backend_type="json")

        >>> # Get SQLite backend with custom path
        >>> backend = get_backend(backend_type="sqlite", db_path="custom/path.db")
    """
    global _backend_instance, _backend_type

    # Use global type if not specified
    requested_type = backend_type or _backend_type

    # Return existing instance if type matches and no custom path
    if (
        _backend_instance is not None
        and _backend_type == requested_type
        and db_path is None
    ):
        return _backend_instance

    # Create new backend instance
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
    """
    Set global default backend type.

    Args:
        backend_type: Backend type to use as default

    Example:
        >>> # Switch to JSON backend for migration testing
        >>> set_backend_type("json")
        >>> backend = get_backend()  # Returns JSONBackend

        >>> # Switch back to SQLite
        >>> set_backend_type("sqlite")
        >>> backend = get_backend()  # Returns SQLiteBackend
    """
    global _backend_type, _backend_instance

    if backend_type not in ("sqlite", "json"):
        raise ValueError(
            f"Invalid backend type: {backend_type}. Use 'sqlite' or 'json'."
        )

    if _backend_type != backend_type:
        logger.info(f"Switching backend type from {_backend_type} to {backend_type}")
        _backend_type = backend_type
        _backend_instance = None  # Force recreation on next get_backend()


def reset_backend() -> None:
    """
    Reset backend instance (for testing).

    Clears cached backend instance, forcing recreation on next get_backend() call.

    Example:
        >>> # In test setup
        >>> reset_backend()
        >>> backend = get_backend(backend_type="sqlite", db_path=":memory:")
    """
    global _backend_instance
    _backend_instance = None
    logger.debug("Backend instance reset")


def get_current_backend_type() -> Literal["sqlite", "json"]:
    """
    Get current default backend type.

    Returns:
        str: Current backend type ("sqlite" or "json")

    Example:
        >>> backend_type = get_current_backend_type()
        >>> print(f"Using {backend_type} backend")
    """
    return _backend_type


def is_sqlite_available() -> bool:
    """
    Check if SQLite database exists.

    Returns:
        bool: True if SQLite database file exists

    Example:
        >>> if is_sqlite_available():
        ...     backend = get_backend("sqlite")
        ... else:
        ...     backend = get_backend("json")  # Fallback to legacy
    """
    from data.database import database_exists

    return database_exists(Path(DEFAULT_SQLITE_PATH))


def is_json_available() -> bool:
    """
    Check if legacy JSON profiles exist.

    Returns:
        bool: True if profiles directory exists with JSON files

    Example:
        >>> if is_json_available() and not is_sqlite_available():
        ...     print("Migration needed")
    """
    profiles_path = Path(DEFAULT_JSON_PATH)
    if not profiles_path.exists():
        return False

    # Check for at least one profile directory with profile.json
    for child in profiles_path.iterdir():
        if child.is_dir() and (child / "profile.json").exists():
            return True

    return False
