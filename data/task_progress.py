"""Task progress tracking for long-running operations.

This module provides functionality to track and persist progress of long-running
tasks (like Calculate Metrics) so that progress indicators can be restored
after page refresh or app restart.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Task state file location
TASK_STATE_FILE = Path("task_progress.json")

# Task timeout (if task takes longer than this, assume it failed)
TASK_TIMEOUT_MINUTES = 30


class TaskProgress:
    """Track progress of long-running background tasks."""

    @staticmethod
    def is_task_running() -> Tuple[bool, Optional[str]]:
        """Check if a task is currently running.

        Returns:
            Tuple of (is_running, task_name)
            - Checks for orphaned tasks (started > TASK_TIMEOUT_MINUTES ago)
            - Returns False if task is stale/orphaned
        """
        if not TASK_STATE_FILE.exists():
            return False, None

        try:
            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            status = state.get("status")
            if status != "in_progress":
                return False, None

            # Check if task is orphaned (started too long ago)
            start_time_str = state.get("start_time")
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                elapsed = datetime.now() - start_time
                if elapsed > timedelta(minutes=TASK_TIMEOUT_MINUTES):
                    logger.warning(
                        f"Orphaned task detected: {state.get('task_name')} "
                        f"(started {elapsed.total_seconds() / 60:.1f} minutes ago)"
                    )
                    # Mark as failed and return False
                    TaskProgress._mark_task_failed(
                        state.get("task_id", "unknown"),
                        f"Task timed out after {TASK_TIMEOUT_MINUTES} minutes",
                    )
                    return False, None

            return True, state.get("task_name")
        except Exception as e:
            logger.error(f"Failed to check task status: {e}")
            return False, None

    @staticmethod
    def is_task_cancelled() -> bool:
        """Check if current task has been cancelled.

        Returns:
            True if cancel flag is set in task state
        """
        if not TASK_STATE_FILE.exists():
            logger.debug("[TaskProgress] is_task_cancelled: state file does not exist")
            return False

        try:
            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)
            cancelled = state.get("cancelled", False)
            logger.debug(
                f"[TaskProgress] is_task_cancelled: cancelled={cancelled}, state={state}"
            )
            return cancelled
        except Exception as e:
            logger.debug(f"[TaskProgress] is_task_cancelled: exception {e}")
            return False

    @staticmethod
    def cancel_task() -> bool:
        """Request cancellation of the running task.

        Returns:
            True if cancellation flag was set successfully
        """
        if not TASK_STATE_FILE.exists():
            return False

        try:
            with open(TASK_STATE_FILE, "r") as f:
                state = json.load(f)

            state["cancelled"] = True
            state["cancel_time"] = datetime.now().isoformat()

            logger.info(
                f"[TaskProgress] Setting cancelled=True for task: {state.get('task_name')}"
            )
            logger.debug(f"[TaskProgress] State before write: {state}")

            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())

            logger.info(
                f"[TaskProgress] Cancellation flag written to disk for task: {state.get('task_name')}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task: {e}")
            return False

    @staticmethod
    def fail_task(task_id: str, error_message: str) -> None:
        """Mark a task as failed (used for cancellations and errors).

        Args:
            task_id: Task identifier
            error_message: Error description
        """
        try:
            if TASK_STATE_FILE.exists():
                with open(TASK_STATE_FILE, "r") as f:
                    state = json.load(f)
            else:
                state = {"task_id": task_id}

            state["status"] = "error"
            state["error_time"] = datetime.now().isoformat()
            state["message"] = error_message
            # Update UI state to show Update Data button (operation failed/cancelled)
            state["ui_state"] = {  # type: ignore[assignment]
                "operation_in_progress": False,
            }

            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())

            logger.error(f"Task failed: {error_message}")
        except Exception as e:
            logger.error(f"Failed to mark task as failed: {e}")

    @staticmethod
    def _mark_task_failed(task_id: str, error_message: str) -> None:
        """Internal wrapper for backwards compatibility."""
        TaskProgress.fail_task(task_id, error_message)

    @staticmethod
    def start_task(task_id: str, task_name: str, **metadata) -> bool:
        """Mark a task as started and save state.

        Args:
            task_id: Unique identifier for the task (e.g., "calculate_metrics")
            task_name: Human-readable task name
            **metadata: Additional task metadata to store

        Returns:
            True if task started successfully, False if another task is running
        """
        # Check if another task is already running
        is_running, existing_task_name = TaskProgress.is_task_running()
        if is_running:
            logger.warning(
                f"Cannot start '{task_name}' - task already running: {existing_task_name}"
            )
            return False

        # Delete any existing file to clear stale state
        if TASK_STATE_FILE.exists():
            try:
                TASK_STATE_FILE.unlink()
                logger.debug("Cleared previous task progress file")
            except Exception as e:
                logger.warning(f"Failed to clear previous progress file: {e}")

        state = {
            "task_id": task_id,
            "task_name": task_name,
            "status": "in_progress",
            "phase": "fetch",
            "start_time": datetime.now().isoformat(),
            "cancelled": False,
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
            "ui_state": {
                "operation_in_progress": True,
            },
        }

        try:
            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())  # Force immediate write to disk
            logger.info(f"Task started: {task_name} (ID: {task_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to save task progress: {e}")
            return False

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

            # CRITICAL: Only mark complete if actually done
            # Do NOT complete if still in fetch phase with incomplete progress
            phase = state.get("phase", "fetch")
            fetch_progress = state.get("fetch_progress", {})
            fetch_percent = fetch_progress.get("percent", 0)

            if phase == "fetch" and fetch_percent < 100:
                logger.warning(
                    f"Attempted to complete task {task_id} while fetch still in progress "
                    f"(phase={phase}, progress={fetch_percent:.1f}%). Ignoring completion request."
                )
                return

            # Update to complete status
            state["status"] = "complete"
            state["complete_time"] = datetime.now().isoformat()
            state["message"] = message
            # Update UI state to show Update Data button (operation complete)
            state["ui_state"] = {  # type: ignore[assignment]
                "operation_in_progress": False,
            }

            with open(TASK_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                f.flush()
                import os

                os.fsync(f.fileno())  # Force immediate write to disk

            logger.info(f"Task completed: {task_id} (phase={phase})")
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
