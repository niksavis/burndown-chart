"""Progress bar callback for tracking Update Data operations."""

import logging
import json
from pathlib import Path
from dash import callback, Output, Input
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


@callback(
    [
        Output("update-data-progress-container", "style"),
        Output("progress-label", "children"),
        Output("progress-bar", "value"),
        Output("progress-bar", "color"),
        Output("progress-bar", "animated"),
        Output("progress-poll-interval", "disabled", allow_duplicate=True),
        Output("update-data-unified", "style", allow_duplicate=True),
        Output("cancel-operation-btn", "style", allow_duplicate=True),
    ],
    [Input("progress-poll-interval", "n_intervals")],
    prevent_initial_call=True,
)
def update_progress_bars(n_intervals):
    """
    Poll task_progress.json and update progress bar.

    Args:
        n_intervals: Number of intervals elapsed (polling trigger)

    Returns:
        Tuple of (container_style, label, value, color, animated, interval_disabled)
    """
    # Read task progress file
    progress_file = Path("task_progress.json")

    if not progress_file.exists():
        # No progress file - hide progress bar and disable polling
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
            {},  # Show Update Data button
            {"display": "none"},  # Hide Cancel button
        )

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            progress_data = json.load(f)

        status = progress_data.get("status", "idle")
        phase = progress_data.get("phase", "fetch")
        fetch_progress = progress_data.get("fetch_progress", {})
        calc_progress = progress_data.get("calculate_progress", {})
        complete_time = progress_data.get("complete_time")
        logger.info(
            f"[Progress] Polling: status={status}, phase={phase}, "
            f"fetch={fetch_progress.get('percent', 0):.0f}%, "
            f"calc={calc_progress.get('percent', 0):.0f}%, "
            f"complete_time={complete_time}, "
            f"n_intervals={n_intervals}"
        )

        # Handle complete status - show success for 3 seconds then hide
        if status == "complete":
            from datetime import datetime

            complete_time = progress_data.get("complete_time")
            if complete_time:
                # CRITICAL: Check if this is a stale completion from an old task
                # If complete_time is > 10 seconds old, treat as stale and hide immediately
                elapsed = (
                    datetime.now() - datetime.fromisoformat(complete_time)
                ).total_seconds()

                if elapsed > 10:
                    # Very old completion - hide immediately without showing message
                    logger.info(
                        f"[Progress] Stale completion detected ({elapsed:.0f}s old), hiding immediately"
                    )
                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},  # Show Update Data button
                        {"display": "none"},  # Hide Cancel button
                    )
                elif elapsed >= 3:
                    # 3 seconds elapsed - hide progress bar but DON'T delete file
                    # Let the next task's start_task() handle cleanup to avoid race condition
                    logger.info("[Progress] Auto-hiding progress bar after 3s")
                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},  # Show Update Data button
                        {"display": "none"},  # Hide Cancel button
                    )
                else:
                    # Show success message
                    message = progress_data.get("message", "✓ Complete")
                    logger.info(
                        f"[Progress] Task complete: {message}, hiding in {3 - elapsed:.1f}s"
                    )
                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        100,
                        "success",
                        False,  # Not animated when complete
                        False,  # Keep polling to hide after 3s
                        {},  # Show Update Data button
                        {"display": "none"},  # Hide Cancel button
                    )
            # No complete_time, hide immediately
            logger.info("[Progress] Task complete (no timestamp), hiding immediately")
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                {"display": "none"},  # Hide Cancel button
            )

        # Handle error status - show error message briefly then hide
        if status == "error":
            error_time = progress_data.get("error_time")
            if error_time:
                from datetime import datetime

                elapsed = (
                    datetime.now() - datetime.fromisoformat(error_time)
                ).total_seconds()

                if elapsed >= 3:
                    # Hide after 3 seconds
                    logger.info("[Progress] Auto-hiding error message after 3s")
                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},  # Show Update Data button
                        {"display": "none"},  # Hide Cancel button
                    )
                else:
                    # Show error message
                    message = progress_data.get("message", "Operation failed")
                    logger.info(
                        f"[Progress] Showing error: {message}, hiding in {3 - elapsed:.1f}s"
                    )
                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        0,
                        "danger",  # Red color for errors/cancellations
                        False,
                        False,  # Keep polling to hide after 3s
                        {},  # Show Update Data button
                        {"display": "none"},  # Hide Cancel button
                    )
            # No error time, hide immediately
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                {"display": "none"},  # Hide Cancel button
            )

        # If task is idle, hide progress bar
        if status == "idle":
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                {"display": "none"},  # Hide Cancel button
            )

        # Show progress container with fixed height
        container_style = {"display": "block", "minHeight": "60px"}

        # Get current phase
        phase = progress_data.get("phase", "fetch")

        # Get both progress objects
        fetch_progress = progress_data.get("fetch_progress", {})
        calc_progress = progress_data.get("calculate_progress", {})

        # Each phase shows 0-100% independently
        # Fetch phase = 0-100% (blue bar)
        # Calculate phase = 0-100% (green bar, resets from fetch)
        if phase == "fetch":
            phase_label = "Fetching"
            color = "primary"  # Blue
            phase_percent = fetch_progress.get("percent", 0)
            current = fetch_progress.get("current", 0)
            total = fetch_progress.get("total", 0)
            message = fetch_progress.get("message", "")
        else:  # calculate
            phase_label = "Calculating"
            color = "success"  # Green
            phase_percent = calc_progress.get("percent", 0)
            current = calc_progress.get("current", 0)
            total = calc_progress.get("total", 0)
            message = calc_progress.get("message", "")

        if total > 0:
            label = f"{phase_label}: {current}/{total} ({phase_percent:.0f}%)"
            if message:
                label += f" - {message}"
        else:
            label = f"{phase_label}: {message or 'Preparing...'}"

        # Read button visibility from ui_state (persisted across page refreshes)
        # operation_in_progress=True -> Show Cancel, Hide Update Data
        # operation_in_progress=False -> Show Update Data, Hide Cancel
        ui_state = progress_data.get("ui_state", {})
        operation_in_progress = ui_state.get(
            "operation_in_progress", True
        )  # Default to in-progress for safety

        update_data_style = {"display": "none"} if operation_in_progress else {}
        cancel_button_style = {} if operation_in_progress else {"display": "none"}

        return (
            container_style,
            label,
            phase_percent,  # Show phase-specific percentage (0-100 for each phase)
            color,
            True,  # Animated during progress
            False,  # Keep polling enabled
            update_data_style,  # Button visibility from ui_state
            cancel_button_style,  # Button visibility from ui_state
        )

    except json.JSONDecodeError as e:
        logger.warning(
            f"[Progress] JSON parse error (file may be mid-write): {e} - keeping progress visible"
        )
        # Don't hide progress bar on JSON errors - file is being written
        # Return a generic "Processing..." state to avoid flickering
        raise PreventUpdate
    except Exception as e:
        logger.error(f"[Progress] Error reading progress file: {e}")
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
            {},  # Show Update Data button
            {"display": "none"},  # Hide Cancel button
        )


@callback(
    Output("progress-poll-interval", "disabled", allow_duplicate=True),
    Input("update-data-unified", "n_clicks"),
    prevent_initial_call=True,
)
def start_progress_polling(n_clicks):
    """
    Enable progress polling when Update Data is clicked.

    Button visibility is automatically managed by the polling callback
    reading ui_state from task_progress.json.

    Args:
        n_clicks: Number of button clicks

    Returns:
        bool: False to enable polling
    """
    if not n_clicks:
        raise PreventUpdate

    logger.info("[Progress] Update Data clicked - enabling progress polling")
    return False  # Enable polling


@callback(
    Output("progress-label", "children", allow_duplicate=True),
    Input("cancel-operation-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_operation(n_clicks):
    """
    Cancel the running operation when Cancel button is clicked.

    Args:
        n_clicks: Number of button clicks

    Returns:
        Cancellation message
    """
    if not n_clicks:
        raise PreventUpdate

    from data.task_progress import TaskProgress

    logger.info("[Progress] Cancel button clicked")

    if TaskProgress.cancel_task():
        logger.info("[Progress] Cancellation request sent successfully")
        # Just update the progress label text
        # Progress polling will continue to update this
        return "Cancelling operation..."
    else:
        logger.warning("[Progress] Failed to cancel task")
        raise PreventUpdate


@callback(
    Output("progress-poll-interval", "disabled"),
    Input("url", "pathname"),
    prevent_initial_call="initial_duplicate",
)
def cleanup_stale_tasks_on_load(pathname):
    """
    Check for stale task progress on page load and enable polling if needed.
    This ensures orphaned/cancelled tasks get cleaned up after page refresh.

    Args:
        pathname: URL pathname (triggers on initial page load)

    Returns:
        bool: False to enable polling if stale task exists, True to keep disabled
    """
    from datetime import datetime

    progress_file = Path("task_progress.json")

    if not progress_file.exists():
        # No task file, keep polling disabled
        return True

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        status = state.get("status", "idle")

        # If task is in error or complete status, check if it's stale
        if status in ["error", "complete"]:
            time_key = "error_time" if status == "error" else "complete_time"
            timestamp = state.get(time_key)

            if timestamp:
                elapsed = (
                    datetime.now() - datetime.fromisoformat(timestamp)
                ).total_seconds()

                if elapsed > 10:
                    # Very stale task - delete file immediately
                    logger.info(
                        f"[Progress] Deleting stale {status} task file ({elapsed:.0f}s old)"
                    )
                    progress_file.unlink()
                    return True  # Keep polling disabled
                else:
                    # Recent error/complete - enable polling to show and auto-hide
                    logger.info(
                        f"[Progress] Enabling polling for recent {status} task ({elapsed:.0f}s old)"
                    )
                    return False  # Enable polling
            else:
                # No timestamp - delete stale file
                logger.info(f"[Progress] Deleting {status} task file with no timestamp")
                progress_file.unlink()
                return True

        # Task is in_progress or idle - enable polling to update UI
        if status == "in_progress":
            logger.info(
                "[Progress] Found in_progress task on page load, enabling polling"
            )
            return False  # Enable polling

        # Idle status - delete file
        if status == "idle":
            logger.info("[Progress] Deleting idle task file")
            progress_file.unlink()
            return True

        return True  # Keep polling disabled by default

    except Exception as e:
        logger.error(f"[Progress] Error checking stale tasks: {e}")
        return True
