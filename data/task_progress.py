"""Task progress tracking for long-running operations.

This module provides functionality to track and persist progress of long-running
tasks (like Calculate Metrics) so that progress indicators can be restored
after page refresh or app restart.

Now uses SQLite database for persistence instead of task_progress.json file.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Task timeout (if task takes longer than this, assume it failed)
TASK_TIMEOUT_MINUTES = 30


def _get_backend():
    """Get persistence backend instance."""
    from data.persistence.factory import get_backend

    return get_backend()


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
        try:
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                return False, None

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
        try:
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                logger.debug("[TaskProgress] is_task_cancelled: state not found")
                return False

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
        try:
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                return False

            state["cancelled"] = True
            state["cancel_time"] = datetime.now().isoformat()

            logger.info(
                f"[TaskProgress] Setting cancelled=True for task: {state.get('task_name')}"
            )
            logger.debug(f"[TaskProgress] State before write: {state}")

            backend.save_task_state(state)

            logger.info(
                f"[TaskProgress] Cancellation flag written to database for task: {state.get('task_name')}"
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
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                state = {"task_id": task_id}

            state["status"] = "error"
            state["error_time"] = datetime.now().isoformat()
            state["message"] = error_message
            # Update UI state to show Update Data button (operation failed/cancelled)
            state["ui_state"] = {  # type: ignore[assignment]
                "operation_in_progress": False,
            }

            backend.save_task_state(state)

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

        # Clear any existing state
        try:
            backend = _get_backend()
            backend.clear_task_state()
            logger.debug("Cleared previous task progress")
        except Exception as e:
            logger.warning(f"Failed to clear previous progress: {e}")

        state = {
            "task_id": task_id,
            "task_name": task_name,
            "status": "in_progress",
            "start_time": datetime.now().isoformat(),
            "cancelled": False,
            "metadata": metadata,
            "ui_state": {
                "operation_in_progress": True,
            },
        }

        # Add task-specific progress structures
        if task_id == "generate_report":
            # Report generation uses simple report_progress object
            state["report_progress"] = {
                "percent": 0,
                "message": "Preparing...",
            }
        else:
            # Update data uses fetch/calculate phases
            state["phase"] = "fetch"
            state["fetch_progress"] = {
                "current": 0,
                "total": 0,
                "percent": 0,
                "message": "Preparing...",
            }
            state["calculate_progress"] = {
                "current": 0,
                "total": 0,
                "percent": 0,
                "message": "Waiting...",
            }

        try:
            backend = _get_backend()
            backend.save_task_state(state)
            logger.info(f"Task started: {task_name} (ID: {task_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to save task progress: {e}")
            return False

    @staticmethod
    def complete_task(
        task_id: str, message: str = "Task completed", **metadata
    ) -> None:
        """Mark a task as completed with success message.

        Args:
            task_id: Task identifier
            message: Success message to display
            **metadata: Additional data to store (e.g., report_file for report generation)
        """
        try:
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                logger.warning(f"Task state not found for {task_id}")
                return

            # CRITICAL: Only mark complete if actually done
            # Do NOT complete if still in fetch phase with incomplete progress
            # This validation only applies to tasks with fetch/calculate phases (e.g., update_data)
            phase = state.get("phase")
            fetch_progress = state.get("fetch_progress", {})
            fetch_percent = fetch_progress.get("percent", 0)

            if phase == "fetch" and fetch_percent < 100:
                logger.warning(
                    f"Attempted to complete task {task_id} while fetch still in progress "
                    f"(phase={phase}, progress={fetch_percent:.1f}%). Ignoring completion request."
                )
                return

            # Update to complete status
            state["status"] = "complete"  # Must match progress_bar.py check
            complete_time = datetime.now().isoformat()

            # Encapsulate completion data based on task type
            if state.get("task_id") == "generate_report":
                # For report tasks, keep everything in report_progress object
                if "report_progress" not in state:
                    state["report_progress"] = {}
                state["report_progress"]["percent"] = 100
                state["report_progress"]["message"] = message
                state["report_progress"]["complete_time"] = complete_time
                # Add metadata (e.g., report_file) to report_progress
                state["report_progress"].update(metadata)
                logger.info(
                    f"Task {task_id} completing with report_progress: {state['report_progress']}"
                )
            else:
                # For other tasks (update_data), use root level fields
                state["complete_time"] = complete_time
                state["message"] = message
                state["percent"] = 100
                state.update(metadata)
                logger.info(f"Task {task_id} completing with metadata: {metadata}")

            # Update UI state to show Update Data button (operation complete)
            state["ui_state"] = {  # type: ignore[assignment]
                "operation_in_progress": False,
            }

            backend.save_task_state(state)

            logger.info(
                f"Task completed: {task_id} (phase={phase}, report_file={state.get('report_file')})"
            )
        except Exception as e:
            logger.error(f"Failed to mark task complete: {e}")

    @staticmethod
    def get_active_task() -> Optional[Dict]:
        """Get currently active task if any.

        Returns:
            Task state dict if task is in_progress, None otherwise
        """
        try:
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                return None

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
                # Clear stale state
                backend.clear_task_state()
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
            backend = _get_backend()
            state = backend.get_task_state()

            if state is None:
                logger.warning(
                    f"Task progress state not found for {task_id}, cannot update progress"
                )
                return

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

            # CRITICAL: Ensure ui_state is preserved and defaults to operation_in_progress=True
            # This prevents buttons from flipping during long calculations
            if "ui_state" not in state:
                state["ui_state"] = {"operation_in_progress": True}

            # Write updated state
            backend.save_task_state(state)

        except Exception as e:
            logger.error(f"Failed to update task progress: {e}")
