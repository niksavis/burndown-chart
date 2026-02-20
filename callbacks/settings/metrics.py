"""
Metrics Calculation Callbacks

Handles automatic DORA/Flow metrics calculation after JIRA data fetch.
"""

import re
import threading
from datetime import datetime

from dash import Input, Output
from dash.exceptions import PreventUpdate

from configuration import logger


def register(app):
    """Register metrics calculation callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [
            Output("trigger-auto-metrics-calc", "data", allow_duplicate=True),
            Output("metrics-refresh-trigger", "data", allow_duplicate=True),
        ],
        Input("trigger-auto-metrics-calc", "data"),
        prevent_initial_call=True,
    )
    def auto_calculate_metrics_after_fetch(trigger_timestamp):
        """
        Automatically calculate DORA/Flow metrics after data fetch completes.

        This runs in a separate callback to allow the Update Data callback to return quickly,
        enabling progress bar updates during the calculation phase.

        Args:
            trigger_timestamp: Timestamp when metrics calculation was triggered

        Returns:
            Tuple: (trigger reset, metrics refresh trigger)
        """
        logger.info(
            f"[Metrics] Auto-metrics callback triggered with timestamp: {trigger_timestamp}"
        )

        # Import TaskProgress before checking trigger
        from data.task_progress import TaskProgress

        # Check if there's actually an active task in calculate phase
        active_task = TaskProgress.get_active_task()
        if not active_task or active_task.get("task_id") != "update_data":
            logger.info(
                "[Metrics] No active update_data task, ignoring metrics trigger"
            )
            raise PreventUpdate

        # Check if metrics calculation already started
        calc_progress = active_task.get("calculate_progress", {})
        calc_message = calc_progress.get("message", "")
        allowed_messages = ["", "Fetch complete, starting metrics calculation..."]
        if calc_message not in allowed_messages:
            logger.info(
                f"[Metrics] Metrics already started (message='{calc_message[:50]}'), ignoring duplicate trigger"
            )
            raise PreventUpdate

        if trigger_timestamp is None:
            # None means no trigger - initial store state
            logger.info(
                "[Metrics] Trigger timestamp is None (initial store state), ignoring"
            )
            return None, None

        if trigger_timestamp == 0:
            # 0 means fetch completed but explicitly skipped metrics
            logger.info(
                "[Metrics] Trigger timestamp is 0 - fetch completed, no metrics calculation needed"
            )
            TaskProgress.complete_task(
                "update_data",
                "✓ Data updated (no metrics recalculation needed)",
            )
            return None, None

        logger.info(
            "[Metrics] Auto-metrics calculation triggered by data fetch completion"
        )

        try:
            # Load statistics to verify fetch completed successfully
            from data.persistence.adapters.statistics import load_statistics

            statistics, _ = load_statistics()

            if not statistics or len(statistics) == 0:
                logger.error(
                    "[Metrics] No statistics found - fetch was likely interrupted"
                )
                TaskProgress.fail_task(
                    "update_data",
                    "Fetch incomplete - please restart the Update Data operation",
                )
                return None, None

            # Calculate total weeks for accurate progress
            total_weeks, custom_weeks = _calculate_weeks_from_statistics(statistics)

            # Update progress with correct total
            TaskProgress.update_progress(
                "update_data",
                "calculate",
                0,
                total_weeks,
                "Starting metrics calculation...",
            )

            # Clear existing metrics to force fresh calculation
            _clear_existing_metrics()

            # Start background calculation
            _start_background_metrics_calculation(custom_weeks, total_weeks)

        except Exception as e:
            logger.error(f"[Metrics] Auto-metrics setup failed: {e}", exc_info=True)
            TaskProgress.fail_task(
                "update_data", "⚠ Data updated, metrics calculation failed"
            )

        # Return immediately - background thread will complete the task
        return None, None


def _calculate_weeks_from_statistics(statistics: list) -> tuple[int, list]:
    """Calculate weeks from statistics date range.

    Args:
        statistics: List of statistics dictionaries with 'date' field

    Returns:
        Tuple of (total_weeks, custom_weeks list)
    """
    from data.iso_week_bucketing import get_weeks_from_date_range

    # Extract date range from statistics
    dates = [datetime.fromisoformat(stat["date"]) for stat in statistics]
    start_date = min(dates)
    end_date = max(dates)
    now = datetime.now()
    if end_date < now:
        end_date = now

    # Get weeks covering the actual data range
    custom_weeks = get_weeks_from_date_range(start_date, end_date)
    total_weeks = len(custom_weeks)

    logger.info(
        f"[Metrics] Calculated {total_weeks} weeks from {start_date.date()} to {end_date.date()}"
    )

    return total_weeks, custom_weeks


def _clear_existing_metrics() -> None:
    """Clear existing metrics for active query to force fresh calculation."""
    logger.info(
        "[Metrics] Clearing existing metrics for active query to force fresh calculation"
    )

    from data.persistence.factory import get_backend

    backend = get_backend()
    active_profile_id = backend.get_app_state("active_profile_id")
    active_query_id = backend.get_app_state("active_query_id")

    if active_profile_id and active_query_id:
        try:
            # Delete metrics for this specific profile/query combination
            backend.delete_metrics(active_profile_id, active_query_id)

            # Clear in-memory snapshots cache (used by Flow/DORA tabs)
            from data.metrics_snapshots import clear_snapshots_cache

            clear_snapshots_cache()
            logger.info(
                f"[Metrics] Deleted existing metrics and cleared snapshots cache for {active_profile_id}/{active_query_id}"
            )
        except Exception as e:
            logger.warning(f"[Metrics] Failed to clear metrics cache: {e}")


def _start_background_metrics_calculation(custom_weeks: list, total_weeks: int) -> None:
    """Start background thread for metrics calculation.

    Args:
        custom_weeks: List of ISO weeks to calculate metrics for
        total_weeks: Total number of weeks for progress tracking
    """
    from data.metrics_calculator import calculate_metrics_for_last_n_weeks
    from data.task_progress import TaskProgress

    def metrics_progress_callback(message: str):
        """Update TaskProgress during metrics calculation."""
        logger.debug(f"[Metrics Progress] {message}")

        # Extract week number from message (e.g., "Week 2025-W51")
        week_match = re.search(r"Week (\d{4}-W\d{2})", message)
        if week_match:
            current_week = week_match.group(1)
            for idx, week in enumerate(custom_weeks, start=1):
                if week == current_week:
                    TaskProgress.update_progress(
                        "update_data",
                        "calculate",
                        idx,
                        total_weeks,
                        message,
                    )
                    break

    def background_metrics():
        """Background thread for metrics calculation."""
        try:
            metrics_success, metrics_message = calculate_metrics_for_last_n_weeks(
                custom_weeks=custom_weeks,
                progress_callback=metrics_progress_callback,
            )

            if metrics_success:
                logger.info(f"[Metrics] Auto-calculated metrics: {metrics_message}")
                TaskProgress.start_postprocess(
                    "update_data", "Data and metrics updated successfully"
                )
            else:
                logger.warning(
                    f"[Metrics] Metrics calculation had issues: {metrics_message}"
                )
                TaskProgress.start_postprocess(
                    "update_data",
                    "Data updated, metrics calculation had issues",
                )
        except Exception as e:
            logger.error(
                f"[Metrics] Background metrics calculation failed: {e}",
                exc_info=True,
            )
            TaskProgress.fail_task(
                "update_data", "⚠ Data updated, metrics calculation failed"
            )

    thread = threading.Thread(target=background_metrics, daemon=True)
    thread.start()
    logger.info("[Metrics] Metrics calculation started in background thread")
