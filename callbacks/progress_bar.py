"""Progress bar callback for tracking Update Data operations."""

import logging
from dash import callback, Output, Input, no_update
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)


@callback(
    [
        Output("update-data-progress-container", "style", allow_duplicate=True),
        Output("progress-label", "children", allow_duplicate=True),
        Output("progress-bar", "value", allow_duplicate=True),
        Output("progress-bar", "color", allow_duplicate=True),
        Output("progress-bar", "animated", allow_duplicate=True),
        Output("progress-poll-interval", "disabled", allow_duplicate=True),
        Output("update-data-unified", "style", allow_duplicate=True),
        Output("update-data-unified", "disabled", allow_duplicate=True),
        Output("cancel-operation-btn", "style", allow_duplicate=True),
        Output("trigger-auto-metrics-calc", "data", allow_duplicate=True),
        Output("metrics-refresh-trigger", "data", allow_duplicate=True),
    ],
    [Input("progress-poll-interval", "n_intervals")],
    prevent_initial_call=True,
)
def update_progress_bars(n_intervals):
    """
    Poll task progress database and update progress bar.

    Args:
        n_intervals: Number of intervals elapsed (polling trigger)

    Returns:
        Tuple of (container_style, label, value, color, animated, interval_disabled)
    """
    from data.persistence.factory import get_backend

    try:
        # Read task progress from database
        backend = get_backend()
        progress_data = backend.get_task_state()

        if progress_data is None:
            # No progress data - hide progress bar and disable polling
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                False,  # Enable Update Data button
                {"display": "none"},  # Hide Cancel button
                no_update,  # No metrics trigger
                no_update,  # No metrics refresh
            )

        task_id = progress_data.get("task_id")

        # ISOLATION: Only handle Update Data tasks, ignore Generate Report tasks
        if task_id != "update_data":
            # Different task running (e.g., generate_report) - don't interfere
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                False,  # Enable Update Data button
                {"display": "none"},  # Hide Cancel button
                no_update,  # No metrics trigger
                no_update,  # No metrics refresh
            )

        status = progress_data.get("status", "idle")
        phase = progress_data.get("phase", "fetch")
        fetch_progress = progress_data.get("fetch_progress", {})
        calc_progress = progress_data.get("calculate_progress", {})
        complete_time = progress_data.get("complete_time")
        cancelled = progress_data.get("cancelled", False)
        cancel_time = progress_data.get("cancel_time")

        logger.info(
            f"[Progress] Polling: status={status}, phase={phase}, "
            f"fetch={fetch_progress.get('percent', 0):.0f}%, "
            f"calc={calc_progress.get('percent', 0):.0f}%, "
            f"cancelled={cancelled}, "
            f"complete_time={complete_time}, "
            f"n_intervals={n_intervals}"
        )

        # RECOVERY: Detect stuck cancelled tasks
        # If task is cancelled but still in_progress (backend didn't call fail_task),
        # force it to error status after grace period
        if status == "in_progress" and cancelled and cancel_time:
            from datetime import datetime

            elapsed = (
                datetime.now() - datetime.fromisoformat(cancel_time)
            ).total_seconds()

            if elapsed > 5:  # 5 second grace period for backend to respond
                logger.warning(
                    f"[Progress] Detected stuck cancelled task ({elapsed:.0f}s since cancellation). "
                    "Forcing to error status."
                )
                from data.task_progress import TaskProgress

                TaskProgress.fail_task("update_data", "Operation cancelled by user")
                # Will be handled on next poll as error status
                raise PreventUpdate

        # RECOVERY: Detect calculate phase and trigger metrics calculation
        # When background thread completes fetch, it sets phase="calculate" but can't trigger
        # the metrics callback directly (running in different thread). So we detect the phase
        # change here and trigger the metrics calculation.
        # CRITICAL: Only trigger ONCE - check if calc has started (percent > 0 or message changed)
        stuck_metrics_trigger = None
        calc_message = calc_progress.get("message", "")
        initial_messages = ["", "Fetch complete, starting metrics calculation..."]
        if (
            status == "in_progress"
            and phase == "calculate"
            and calc_progress.get("percent", 0) == 0
            and calc_message in initial_messages
            and not cancelled
        ):
            # Only trigger if the message is still the initial one set by background fetch
            # Once auto_calculate_metrics_after_fetch runs, it changes the message
            logger.info(
                "[Progress] Detected calculate phase transition - triggering metrics calculation"
            )
            import time

            # Trigger metrics calculation by returning a timestamp
            stuck_metrics_trigger = int(time.time() * 1000)

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
                    import time

                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},  # Show Update Data button
                        False,  # Enable Update Data button
                        {"display": "none"},  # Hide Cancel button
                        no_update,  # No metrics trigger
                        int(time.time() * 1000),  # Trigger metrics refresh
                    )
                elif elapsed >= 3:
                    # 3 seconds elapsed - hide progress bar but DON'T delete file
                    # Let the next task's start_task() handle cleanup to avoid race condition
                    logger.info("[Progress] Auto-hiding progress bar after 3s")
                    import time

                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},  # Show Update Data button
                        False,  # Enable Update Data button
                        {"display": "none"},  # Hide Cancel button
                        no_update,  # No metrics trigger
                        int(time.time() * 1000),  # Trigger metrics refresh
                    )
                else:
                    # Show success message
                    message = progress_data.get("message", "✓ Complete")
                    logger.info(
                        f"[Progress] Task complete: {message}, hiding in {3 - elapsed:.1f}s"
                    )
                    import time

                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        100,
                        "success",
                        False,  # Not animated when complete
                        False,  # Keep polling to hide after 3s
                        {},  # Show Update Data button
                        False,  # Enable Update Data button
                        {"display": "none"},  # Hide Cancel button
                        no_update,  # No metrics trigger
                        int(time.time() * 1000),  # Trigger metrics refresh
                    )
            # No complete_time, hide immediately
            logger.info("[Progress] Task complete (no timestamp), hiding immediately")
            import time

            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},  # Show Update Data button
                False,  # Enable Update Data button
                {"display": "none"},  # Hide Cancel button
                no_update,  # No metrics trigger
                int(time.time() * 1000),  # Trigger metrics refresh
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
                        False,  # Enable Update Data button
                        {"display": "none"},  # Hide Cancel button
                        no_update,  # No metrics trigger
                        no_update,  # No metrics refresh
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
                        False,  # Enable Update Data button
                        {"display": "none"},  # Hide Cancel button
                        no_update,  # No metrics trigger
                        no_update,  # No metrics refresh
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
                False,  # Enable Update Data button
                {"display": "none"},  # Hide Cancel button
                no_update,  # No metrics trigger
                no_update,  # No metrics refresh
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
                False,  # Enable Update Data button
                {"display": "none"},  # Hide Cancel button
                no_update,  # No metrics trigger
                no_update,  # No metrics refresh
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
        update_data_disabled = operation_in_progress  # Disable button during operation
        cancel_button_style = {} if operation_in_progress else {"display": "none"}

        return (
            container_style,
            label,
            phase_percent,  # Show phase-specific percentage (0-100 for each phase)
            color,
            True,  # Animated during progress
            False,  # Keep polling enabled
            update_data_style,  # Button visibility from ui_state
            update_data_disabled,  # Button disabled state from ui_state
            cancel_button_style,  # Button visibility from ui_state
            stuck_metrics_trigger
            if stuck_metrics_trigger
            else no_update,  # Auto-trigger metrics if stuck
            no_update,  # No metrics refresh during progress
        )

    except Exception as e:
        logger.error(f"[Progress] Error reading progress from database: {e}")
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
            {},  # Show Update Data button
            False,  # Enable Update Data button
            {"display": "none"},  # Hide Cancel button
            no_update,  # No metrics trigger on exception
            no_update,  # No metrics refresh on exception
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
    [
        Output("statistics-table", "data", allow_duplicate=True),
        Output("jira-cache-status", "children", allow_duplicate=True),
    ],
    Input("metrics-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def reload_data_after_update(refresh_trigger):
    """
    Reload statistics and update JIRA cache status after Update Data completes.

    This callback is triggered when the task completes (metrics-refresh-trigger is set by
    the progress polling callback). It reloads the statistics from disk and updates the
    JIRA cache status, which triggers downstream callbacks to refresh the UI.

    Args:
        refresh_trigger: Timestamp when the refresh was triggered

    Returns:
        tuple: (statistics_data, cache_status)
    """
    if not refresh_trigger:
        raise PreventUpdate

    logger.info("[Progress] Reloading statistics after Update Data completion")

    try:
        # Load statistics from disk
        from data.persistence import load_statistics
        from dash import html

        statistics, is_sample = load_statistics()

        if not statistics:
            logger.warning("[Progress] No statistics found after reload")
            return (
                [],
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "No data loaded",
                    ],
                    className="text-warning small",
                ),
            )

        logger.info(f"[Progress] Reloaded {len(statistics)} statistics records")

        # Update cache status to trigger jira-issues-store refresh
        cache_status = html.Div(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Data loaded: {len(statistics)} records",
            ],
            className="text-success small",
        )

        return statistics, cache_status

    except Exception as e:
        logger.error(f"[Progress] Error reloading statistics: {e}", exc_info=True)
        from dash import html

        return (
            no_update,
            html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error: {str(e)}",
                ],
                className="text-danger small",
            ),
        )


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
    from data.persistence.factory import get_backend

    try:
        backend = get_backend()
        state = backend.get_task_state()

        if state is None:
            # No task state, keep polling disabled
            return True

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
                    # Very stale task - clear state immediately
                    logger.info(
                        f"[Progress] Clearing stale {status} task state ({elapsed:.0f}s old)"
                    )
                    backend.clear_task_state()
                    return True  # Keep polling disabled
                else:
                    # Recent error/complete - enable polling to show and auto-hide
                    logger.info(
                        f"[Progress] Enabling polling for recent {status} task ({elapsed:.0f}s old)"
                    )
                    return False  # Enable polling
            else:
                # No timestamp - clear stale state
                logger.info(
                    f"[Progress] Clearing {status} task state with no timestamp"
                )
                backend.clear_task_state()
                return True

        # Task is in_progress or idle - enable polling to update UI
        if status == "in_progress":
            logger.info(
                "[Progress] Found in_progress task on page load, enabling polling"
            )
            return False  # Enable polling

        # Idle status - clear state
        if status == "idle":
            logger.info("[Progress] Clearing idle task state")
            backend.clear_task_state()
            return True

        return True  # Keep polling disabled by default

    except Exception as e:
        logger.error(f"[Progress] Error checking stale tasks: {e}")
        return True
