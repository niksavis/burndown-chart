import logging
import time
from datetime import datetime

from dash import Input, Output, callback, html, no_update
from dash.exceptions import PreventUpdate

from data.persistence.adapters import load_statistics
from data.persistence.factory import get_backend
from data.query_manager import get_query_dropdown_options
from data.task_progress import TaskProgress
from utils.datetime_utils import parse_iso_datetime

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
        Output("current-statistics", "modified_timestamp", allow_duplicate=True),
    ],
    [Input("progress-poll-interval", "n_intervals")],
    prevent_initial_call=True,
)
def update_progress_bars(n_intervals):

    try:
        backend = get_backend()
        progress_data = backend.get_task_state()

        if progress_data is None:
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},
                False,
                {"display": "none"},
                no_update,
                no_update,
                no_update,
            )

        task_id = progress_data.get("task_id")

        if task_id != "update_data":
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},
                False,
                {"display": "none"},
                no_update,
                no_update,
                no_update,
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

        if status == "in_progress" and cancelled and cancel_time:
            cancel_timestamp = parse_iso_datetime(cancel_time)
            if cancel_timestamp:
                elapsed = (datetime.now() - cancel_timestamp).total_seconds()

                if elapsed > 5:
                    logger.warning(
                        "[Progress] Detected stuck cancelled task "
                        f"({elapsed:.0f}s since cancellation). "
                        "Forcing to error status."
                    )
                    TaskProgress.fail_task("update_data", "Operation cancelled by user")
                    raise PreventUpdate
            else:
                logger.warning(
                    "[Progress] Invalid cancel_time value, "
                    "skipping cancellation grace check"
                )

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
            logger.info(
                "[Progress] Detected calculate phase transition - "
                "triggering metrics calculation"
            )

            stuck_metrics_trigger = int(time.time() * 1000)

        postprocess_trigger = None
        if status == "in_progress" and phase == "postprocess":
            postprocess_time = progress_data.get("postprocess_time")
            postprocess_message = progress_data.get(
                "postprocess_message", "Data updated successfully"
            )

            last_postprocess_time_seen = getattr(
                update_progress_bars, "_last_postprocess_time", None
            )

            if postprocess_time and postprocess_time != last_postprocess_time_seen:
                logger.info(
                    "[Progress] Detected postprocess phase - triggering "
                    "UI refresh to complete task"
                )
                postprocess_trigger = int(time.time() * 1000)
                update_progress_bars._last_postprocess_time = postprocess_time

            postprocess_timestamp = parse_iso_datetime(postprocess_time)
            if postprocess_timestamp:
                elapsed = (datetime.now() - postprocess_timestamp).total_seconds()
                if elapsed >= 60:
                    logger.warning(
                        "[Progress] Postprocess exceeded 60s, completing task"
                    )
                    TaskProgress.complete_task("update_data", postprocess_message)
                    raise PreventUpdate
            else:
                start_timestamp = parse_iso_datetime(progress_data.get("start_time"))
                if start_timestamp:
                    elapsed = (datetime.now() - start_timestamp).total_seconds()
                    if elapsed >= 90:
                        logger.warning(
                            "[Progress] Stale postprocess state detected, "
                            "completing task"
                        )
                        TaskProgress.complete_task("update_data", postprocess_message)
                        raise PreventUpdate

        if status == "complete":
            complete_time = progress_data.get("complete_time")
            if complete_time:
                completed_at = parse_iso_datetime(complete_time)
                if not completed_at:
                    logger.warning(
                        "[Progress] Invalid complete_time value, hiding immediately"
                    )
                    completed_at = datetime.now()

                elapsed = (datetime.now() - completed_at).total_seconds()

                if elapsed > 10:
                    logger.info(
                        f"[Progress] Stale completion detected "
                        f"({elapsed:.0f}s old), hiding immediately"
                    )

                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},
                        False,
                        {"display": "none"},
                        no_update,
                        int(time.time() * 1000),
                        int(time.time() * 1000),
                    )
                elif elapsed >= 3:
                    logger.info("[Progress] Auto-hiding progress bar after 3s")

                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},
                        False,
                        {"display": "none"},
                        no_update,
                        int(time.time() * 1000),
                        int(time.time() * 1000),
                    )
                else:
                    message = progress_data.get("message", "✓ Complete")
                    logger.info(
                        f"[Progress] Task complete: {message}, "
                        f"hiding in {3 - elapsed:.1f}s"
                    )

                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        100,
                        "success",
                        False,
                        False,
                        {},
                        False,
                        {"display": "none"},
                        no_update,
                        int(time.time() * 1000),
                        int(time.time() * 1000),
                    )
            logger.info("[Progress] Task complete (no timestamp), hiding immediately")

            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},
                False,
                {"display": "none"},
                no_update,
                int(time.time() * 1000),
                int(time.time() * 1000),
            )

        if status == "error":
            error_time = progress_data.get("error_time")
            if error_time:
                error_timestamp = parse_iso_datetime(error_time)
                if not error_timestamp:
                    logger.warning(
                        "[Progress] Invalid error_time value, hiding immediately"
                    )
                    error_timestamp = datetime.now()

                elapsed = (datetime.now() - error_timestamp).total_seconds()

                if elapsed >= 3:
                    logger.info("[Progress] Auto-hiding error message after 3s")
                    return (
                        {"display": "none"},
                        "Processing: 0%",
                        0,
                        "primary",
                        True,
                        True,
                        {},
                        False,
                        {"display": "none"},
                        no_update,
                        no_update,
                        no_update,
                    )
                else:
                    message = progress_data.get("message", "Operation failed")
                    logger.info(
                        f"[Progress] Showing error: {message}, "
                        f"hiding in {3 - elapsed:.1f}s"
                    )
                    return (
                        {"display": "block", "minHeight": "60px"},
                        message,
                        0,
                        "danger",
                        False,
                        False,
                        {},
                        False,
                        {"display": "none"},
                        no_update,
                        no_update,
                        no_update,
                    )
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},
                False,
                {"display": "none"},
                no_update,
                no_update,
                no_update,
            )

        if status == "idle":
            return (
                {"display": "none"},
                "Processing: 0%",
                0,
                "primary",
                True,
                True,
                {},
                False,
                {"display": "none"},
                no_update,
                no_update,
                no_update,
            )

        container_style = {"display": "block", "minHeight": "60px"}

        phase = progress_data.get("phase", "fetch")

        fetch_progress = progress_data.get("fetch_progress", {})
        calc_progress = progress_data.get("calculate_progress", {})

        if phase == "fetch":
            phase_label = "Fetching"
            color = "primary"
            phase_percent = fetch_progress.get("percent", 0)
            current = fetch_progress.get("current", 0)
            total = fetch_progress.get("total", 0)
            message = fetch_progress.get("message", "")
        elif phase == "calculate":
            phase_label = "Calculating"
            color = "success"
            phase_percent = calc_progress.get("percent", 0)
            current = calc_progress.get("current", 0)
            total = calc_progress.get("total", 0)
            message = calc_progress.get("message", "")
        else:
            phase_label = "Finalizing"
            color = "primary"
            phase_percent = 100
            current = calc_progress.get("current", 0)
            total = calc_progress.get("total", 0)
            message = calc_progress.get("message", "Finalizing UI...")

        if total > 0:
            label = f"{phase_label}: {current}/{total} ({phase_percent:.0f}%)"
            if message:
                label += f" - {message}"
        else:
            label = f"{phase_label}: {message or 'Preparing...'}"

        ui_state = progress_data.get("ui_state", {})
        operation_in_progress = ui_state.get("operation_in_progress", True)

        update_data_style = {"display": "none"} if operation_in_progress else {}
        update_data_disabled = operation_in_progress
        cancel_button_style = {} if operation_in_progress else {"display": "none"}

        return (
            container_style,
            label,
            phase_percent,
            color,
            True,
            False,
            update_data_style,
            update_data_disabled,
            cancel_button_style,
            stuck_metrics_trigger if stuck_metrics_trigger else no_update,
            postprocess_trigger if postprocess_trigger else no_update,
            no_update,
        )

    except PreventUpdate:
        raise
    except Exception as e:
        logger.error(
            f"[Progress] Error reading progress from database: {e}", exc_info=True
        )
        return (
            {"display": "none"},
            "Processing: 0%",
            0,
            "primary",
            True,
            True,
            {},
            False,
            {"display": "none"},
            no_update,
            no_update,
            no_update,
        )


@callback(
    Output("progress-poll-interval", "disabled", allow_duplicate=True),
    Input("update-data-unified", "n_clicks"),
    prevent_initial_call=True,
)
def start_progress_polling(n_clicks):

    if not n_clicks:
        raise PreventUpdate

    logger.info("[Progress] Update Data clicked - enabling progress polling")
    return False


@callback(
    Output("progress-label", "children", allow_duplicate=True),
    Input("cancel-operation-btn", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_operation(n_clicks):

    if not n_clicks:
        raise PreventUpdate

    logger.info("[Progress] Cancel button clicked")

    if TaskProgress.cancel_task():
        logger.info("[Progress] Cancellation request sent successfully")
        return "Cancelling operation..."
    else:
        logger.warning("[Progress] Failed to cancel task")
        raise PreventUpdate


@callback(
    [
        Output("jira-cache-status", "children", allow_duplicate=True),
        Output("current-statistics", "data", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
    ],
    Input("metrics-refresh-trigger", "data"),
    prevent_initial_call=True,
)
def reload_data_after_update(refresh_trigger):

    if not refresh_trigger:
        raise PreventUpdate

    logger.info(
        "[Progress] Reloading statistics after Update Data completion or import"
    )

    try:
        backend = get_backend()
        progress_data = backend.get_task_state()
        task_status = progress_data.get("status") if progress_data else None
        already_complete = task_status == "complete"

        statistics, is_sample = load_statistics()

        logger.info("[DROPDOWN] Refreshing dropdown after Update Data completion")
        dropdown_options = get_query_dropdown_options()
        logger.info(f"[DROPDOWN] Built {len(dropdown_options)} dropdown options")

        if not statistics:
            logger.warning(
                "[Progress] No statistics found after reload - clearing stores"
            )
            if not already_complete:
                logger.info("[Progress] Completing task: No changes detected")
                TaskProgress.complete_task(
                    "update_data", "No changes detected - data is already up to date"
                )
            else:
                logger.info(
                    "[Progress] Task already complete, "
                    "skipping redundant complete_task call"
                )
            return (
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "No data loaded",
                    ],
                    className="text-warning small",
                ),
                [],
                dropdown_options,
            )

        logger.info(f"[Progress] Reloaded {len(statistics)} statistics records")
        if not already_complete:
            logger.info(
                "[Progress] Completing task: Data and metrics updated successfully"
            )
            TaskProgress.complete_task(
                "update_data", "Data and metrics updated successfully"
            )
        else:
            logger.info(
                "[Progress] Task already complete, "
                "skipping redundant complete_task call"
            )

        cache_status = html.Div(
            [
                html.I(className="fas fa-check-circle me-2"),
                f"Data loaded: {len(statistics)} records",
            ],
            className="text-success small",
        )

        return (
            cache_status,
            statistics,
            dropdown_options,
        )

    except Exception as e:
        logger.error(f"[Progress] Error reloading statistics: {e}", exc_info=True)
        TaskProgress.fail_task("update_data", "Error refreshing UI after data update")

        try:
            dropdown_options = get_query_dropdown_options()
        except Exception:
            dropdown_options = []

        return (
            html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error: {str(e)}",
                ],
                className="text-danger small",
            ),
            [],
            dropdown_options,
        )


@callback(
    Output("progress-poll-interval", "disabled"),
    Input("url", "pathname"),
    prevent_initial_call="initial_duplicate",
)
def cleanup_stale_tasks_on_load(pathname):

    try:
        backend = get_backend()
        state = backend.get_task_state()

        if state is None:
            return True

        status = state.get("status", "idle")

        if status in ["error", "complete"]:
            time_key = "error_time" if status == "error" else "complete_time"
            timestamp = state.get(time_key)

            if timestamp:
                parsed_timestamp = parse_iso_datetime(timestamp)
                if not parsed_timestamp:
                    logger.warning(
                        f"[Progress] Invalid {time_key} value, clearing stale state"
                    )
                    backend.clear_task_state()
                    return True

                elapsed = (datetime.now() - parsed_timestamp).total_seconds()

                if elapsed > 10:
                    logger.info(
                        f"[Progress] Clearing stale {status} task state "
                        f"({elapsed:.0f}s old)"
                    )
                    backend.clear_task_state()
                    return True
                else:
                    logger.info(
                        f"[Progress] Enabling polling for recent {status} task "
                        f"({elapsed:.0f}s old)"
                    )
                    return False
            else:
                logger.info(
                    f"[Progress] Clearing {status} task state with no timestamp"
                )
                backend.clear_task_state()
                return True

        if status == "in_progress":
            logger.info(
                "[Progress] Found in_progress task on page load, enabling polling"
            )
            return False

        if status == "idle":
            logger.info("[Progress] Clearing idle task state")
            backend.clear_task_state()
            return True

        return True

    except Exception as e:
        logger.error(f"[Progress] Error checking stale tasks: {e}")
        return True
