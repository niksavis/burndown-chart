"""App state operations mixin for SQLiteBackend."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from data.database import get_db_connection
from data.exceptions import PersistenceError
from data.persistence.sqlite.helpers import retry_on_db_lock

logger = logging.getLogger(__name__)


class AppStateMixin:
    """Mixin for application state operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_app_state(self, key: str) -> str | None:
        """Get application state value from app_state table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result["value"] if result else None
        except (
            sqlite3.Error,
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            AttributeError,
            PersistenceError,
        ) as e:
            logger.exception(
                f"Failed to get app_state key '{key}'",
                extra={"error_type": type(e).__name__, "key": key},
            )
            raise PersistenceError(f"Failed to load app state key '{key}'") from e

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def set_app_state(self, key: str, value: str | None) -> None:
        """Set application state value in app_state table.

        Args:
            key: State key to set
            value: State value (if None, deletes the key)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if value is None:
                    # Delete key if value is None
                    cursor.execute("DELETE FROM app_state WHERE key = ?", (key,))
                    logger.debug(f"Deleted app_state key: {key}")
                else:
                    # Insert or update key-value pair
                    cursor.execute(
                        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                        (key, value),
                    )
                    logger.debug(f"Set app_state: {key} = {value}")
                conn.commit()
        except (
            sqlite3.Error,
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            AttributeError,
            PersistenceError,
        ) as e:
            logger.exception(
                f"Failed to set app_state key '{key}'",
                extra={"error_type": type(e).__name__, "key": key},
            )
            raise PersistenceError(f"Failed to save app state key '{key}'") from e
