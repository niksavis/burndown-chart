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
        state = {
            "task_id": task_id,
            "task_name": task_name,
            "status": "in_progress",
            "start_time": datetime.now().isoformat(),
            "metadata": metadata,
        }

        try:
            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
            logger.info(f"Task started: {task_name} (ID: {task_id})")
        except Exception as e:
            logger.error(f"Failed to save task progress: {e}")

    @staticmethod
    def complete_task(task_id: str) -> None:
        """Mark a task as completed and clear state.

        Args:
            task_id: Task identifier
        """
        try:
            if TASK_STATE_FILE.exists():
                TASK_STATE_FILE.unlink()
                logger.info(f"Task completed: {task_id}")
        except Exception as e:
            logger.error(f"Failed to clear task progress: {e}")

    @staticmethod
    def get_active_task() -> Optional[Dict]:
        """Get currently active task if any.

        Returns:
            Task state dict if task is active, None otherwise
        """
        if not TASK_STATE_FILE.exists():
            return None

        try:
            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            # Check if task has timed out
            start_time = datetime.fromisoformat(state["start_time"])
            elapsed = datetime.now() - start_time

            if elapsed > timedelta(minutes=TASK_TIMEOUT_MINUTES):
                logger.warning(
                    f"Task {state['task_id']} timed out after {elapsed.total_seconds():.0f}s"
                )
                TaskProgress.complete_task(state["task_id"])
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
