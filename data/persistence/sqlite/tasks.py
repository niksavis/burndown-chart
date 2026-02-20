"""Task progress operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from data.database import get_db_connection
from data.persistence import ValidationError

logger = logging.getLogger(__name__)


class TasksMixin:
    """Mixin for task progress and state operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_task_progress(self, task_name: str) -> dict | None:
        """Get task progress state."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM task_progress WHERE task_name = ?", (task_name,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(
                f"Failed to get task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:
        """Update task progress."""
        if not 0.0 <= progress_percent <= 100.0:
            raise ValidationError(
                f"progress_percent must be 0-100, got {progress_percent}"
            )

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO task_progress (task_name, progress_percent, status, message, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(task_name) DO UPDATE SET
                        progress_percent = excluded.progress_percent,
                        status = excluded.status,
                        message = excluded.message,
                        updated_at = excluded.updated_at
                """,
                    (
                        task_name,
                        progress_percent,
                        status,
                        message,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.debug(
                    f"Task progress: {task_name} - {progress_percent}% {status}"
                )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to save task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def clear_task_progress(self, task_name: str) -> None:
        """Remove task progress entry."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM task_progress WHERE task_name = ?", (task_name,)
                )
                conn.commit()
                logger.debug(f"Cleared task progress: {task_name}")
        except Exception as e:
            logger.error(
                f"Failed to clear task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_task_state(self) -> dict | None:
        """
        Get full task state (supports complex nested structures).
        Retrieves the first (and only) task progress row and returns full state.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT message FROM task_progress LIMIT 1")
                result = cursor.fetchone()
                if not result or not result["message"]:
                    return None
                # Parse JSON from message field
                return json.loads(result["message"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task state JSON: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get task state: {e}",
                extra={"error_type": type(e).__name__},
            )
            return None

    def save_task_state(self, state: dict) -> None:
        """
        Save full task state (supports complex nested structures).
        Stores state as JSON in message field.
        """
        try:
            # Serialize state to JSON
            state_json = json.dumps(state)

            # Extract key fields for indexing
            task_name = state.get("task_id", "unknown")
            status = state.get("status", "in_progress")

            # Calculate progress percent (try multiple fields for compatibility)
            progress_percent = 0.0
            if "percent" in state:
                progress_percent = state["percent"]
            elif "fetch_progress" in state:
                progress_percent = state["fetch_progress"].get("percent", 0.0)
            elif "report_progress" in state:
                progress_percent = state["report_progress"].get("percent", 0.0)

            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO task_progress (task_name, progress_percent, status, message, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(task_name) DO UPDATE SET
                        progress_percent = excluded.progress_percent,
                        status = excluded.status,
                        message = excluded.message,
                        updated_at = excluded.updated_at
                """,
                    (
                        task_name,
                        progress_percent,
                        status,
                        state_json,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.debug(
                    f"Task state saved: {task_name} - {progress_percent}% {status}"
                )
        except Exception as e:
            logger.error(
                f"Failed to save task state: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def clear_task_state(self) -> None:
        """Clear all task progress state."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM task_progress")
                conn.commit()
                logger.debug("Cleared all task progress state")
        except Exception as e:
            logger.error(
                f"Failed to clear task state: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise
