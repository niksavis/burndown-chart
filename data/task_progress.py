"""Task progress tracking for long-running operations.

This module provides functionality to track and persist progress of long-running
tasks (like Calculate Metrics) so that progress indicators can be restored
after page refresh or app restart.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Task state file location
TASK_STATE_FILE = Path("task_progress.json")

# Task timeout (if task takes longer than this, assume it failed)
TASK_TIMEOUT_MINUTES = 30


class TaskProgress:
    """Track progress of long-running background tasks."""

    @staticmethod
    def start_task(task_id: str, task_name: str, **metadata) -> None:
        """Mark a task as started and save state.

        Args:
            task_id: Unique identifier for the task (e.g., "calculate_metrics")
            task_name: Human-readable task name
            **metadata: Additional task metadata to store
        """
        # Delete any existing file first to clear stale state
        if TASK_STATE_FILE.exists():
            try:
                TASK_STATE_FILE.unlink()
                logger.debug("Cleared stale task progress file")
            except Exception as e:
                logger.warning(f"Failed to clear stale progress file: {e}")

        state = {
            "task_id": task_id,
            "task_name": task_name,
            "status": "in_progress",
            "phase": "fetch",
            "start_time": datetime.now().isoformat(),
            "metadata": metadata,
            "fetch_progress": {
                "current": 0,
                "total": 0,
                "percent": 0,
                "message": "Preparing...",
            },
            "calculate_progress": {
                "current": 0,
                "total": 0,
                "percent": 0,
                "message": "Waiting...",
            },
        }

        try:
            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())  # Force immediate write to disk
            logger.info(f"Task started: {task_name} (ID: {task_id})")
        except Exception as e:
            logger.error(f"Failed to save task progress: {e}")

    @staticmethod
    def complete_task(task_id: str, message: str = "Task completed") -> None:
        """Mark a task as completed with success message.

        Args:
            task_id: Task identifier
            message: Success message to display
        """
        try:
            if not TASK_STATE_FILE.exists():
                logger.warning(f"Task file not found for {task_id}")
                return

            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            # Update to complete status
            state["status"] = "complete"
            state["complete_time"] = datetime.now().isoformat()
            state["message"] = message

            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())  # Force immediate write to disk

            logger.info(f"Task completed: {task_id}")
        except Exception as e:
            logger.error(f"Failed to mark task complete: {e}")

    @staticmethod
    def get_active_task() -> Optional[Dict]:
        """Get currently active task if any.

        Returns:
            Task state dict if task is in_progress, None otherwise
        """
        if not TASK_STATE_FILE.exists():
            return None

        try:
            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            # Only return if status is in_progress (fixes button stuck bug)
            if state.get("status") != "in_progress":
                return None

            # Check if task has timed out
            start_time = datetime.fromisoformat(state["start_time"])
            elapsed = datetime.now() - start_time

            if elapsed > timedelta(minutes=TASK_TIMEOUT_MINUTES):
                logger.warning(
                    f"Task {state['task_id']} timed out after {elapsed.total_seconds():.0f}s"
                )
                # Delete stale file
                if TASK_STATE_FILE.exists():
                    TASK_STATE_FILE.unlink()
                return None

            return state

        except Exception as e:
            logger.error(f"Failed to read task progress: {e}")
            return None

    @staticmethod
    def is_task_running(task_id: str) -> bool:
        """Check if a specific task is currently running.

        Args:
            task_id: Task identifier

        Returns:
            True if task is running, False otherwise
        """
        active_task = TaskProgress.get_active_task()
        return active_task is not None and active_task.get("task_id") == task_id

    @staticmethod
    def get_task_status_message(task_id: str) -> Optional[str]:
        """Get status message for a task if it's running.

        Args:
            task_id: Task identifier

        Returns:
            Status message string or None
        """
        active_task = TaskProgress.get_active_task()
        if active_task and active_task.get("task_id") == task_id:
            elapsed = datetime.now() - datetime.fromisoformat(active_task["start_time"])
            elapsed_str = f"{int(elapsed.total_seconds())}s"
            return f"{active_task['task_name']} in progress... ({elapsed_str})"
        return None

    @staticmethod
    def update_progress(
        task_id: str,
        phase: str,
        current: int = 0,
        total: int = 0,
        message: str = "",
    ) -> None:
        """Update progress information for a running task.

        Args:
            task_id: Task identifier
            phase: Current phase ('fetch' or 'calculate')
            current: Current progress value
            total: Total items to process
            message: Optional progress message
        """
        try:
            # Read current state
            if not TASK_STATE_FILE.exists():
                logger.warning(
                    f"Task progress file not found for {task_id}, cannot update progress"
                )
                return

            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            # Only update if task IDs match
            if state.get("task_id") != task_id:
                logger.warning(
                    f"Task ID mismatch: expected {task_id}, got {state.get('task_id')}"
                )
                return

            # Calculate percentage
            percent = (current / total * 100) if total > 0 else 0

            # Update phase-specific progress
            progress_key = f"{phase}_progress"
            state[progress_key] = {
                "current": current,
                "total": total,
                "percent": percent,
                "message": message,
            }
            state["phase"] = phase

            # Write updated state with explicit flush to ensure immediate visibility
            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()  # Ensure data is written to disk immediately
                import os

                os.fsync(f.fileno())  # Force OS to write to disk (not just buffer)

        except Exception as e:
            logger.error(f"Failed to update task progress: {e}")
