from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate

from callbacks.settings.helpers import calculate_remaining_work_for_data_window
from configuration import DEFAULT_PERT_FACTOR
from configuration import logger as config_logger
from data.profile_manager import get_active_profile_and_query_display_names
from data.task_progress import TaskProgress
from ui.parameter_panel import create_parameter_bar_collapsed

logger = logging.getLogger(__name__)


def register(app: Any) -> None:

    @app.callback(
        [
            Output("parameter-collapse", "is_open"),
            Output("parameter-panel-state", "data"),
            Output("settings-collapse", "is_open", allow_duplicate=True),
            Output("import-export-collapse", "is_open", allow_duplicate=True),
        ],
        Input("btn-expand-parameters", "n_clicks"),
        [
            State("parameter-collapse", "is_open"),
            State("parameter-panel-state", "data"),
            State("settings-collapse", "is_open"),
            State("import-export-collapse", "is_open"),
        ],
        prevent_initial_call=True,
    )
    def toggle_parameter_panel(
        n_clicks: int | None,
        is_open: bool,
        panel_state: dict,
        settings_is_open: bool,
        import_export_is_open: bool,
    ) -> tuple:

        if n_clicks:
            new_is_open = not is_open
            updated_state = {
                "is_open": new_is_open,
                "last_updated": datetime.now().isoformat(),
                "user_preference": True,
            }

            new_settings_state = no_update
            new_import_export_state = no_update

            if new_is_open:
                if settings_is_open:
                    new_settings_state = False
                if import_export_is_open:
                    new_import_export_state = False

            return (
                new_is_open,
                updated_state,
                new_settings_state,
                new_import_export_state,
            )

        return is_open, panel_state, no_update, no_update

    @app.callback(
        Output("parameter-bar-collapsed", "children"),
        [
            Input("pert-factor-slider", "value"),
            Input("deadline-picker", "date"),
            Input("total-items-input", "value"),
            Input("total-points-display", "value"),
            Input("data-points-input", "value"),
        ],
        [State("current-settings", "data")],
        prevent_initial_call=False,
    )
    def update_parameter_summary(
        pert_factor: float | None,
        deadline: str | None,
        scope_items: int | None,
        scope_points: float | str | None,
        data_points: int | None,
        settings: dict | None,
    ) -> Any:

        pert_factor = pert_factor or DEFAULT_PERT_FACTOR

        if deadline is None:
            deadline = settings.get("deadline") if settings else None
            if deadline is None:
                deadline = "2025-12-31"
                config_logger.warning(
                    "[Banner] Deadline is None (possibly invalid input). "
                    "Using default for banner display. "
                    "NOTE: Deadline is optional - health score uses "
                    "graceful degradation."
                )
            else:
                config_logger.info(
                    "[Banner] Deadline from picker is None, "
                    f"using stored value: {deadline}"
                )

        scope_items = scope_items or 0

        try:
            scope_points = float(scope_points) if scope_points else 0.0
        except ValueError, TypeError:
            scope_points = 0.0

        show_points = settings.get("show_points", True) if settings else True

        remaining_items = scope_items if scope_items > 0 else None
        remaining_points = scope_points if scope_points > 0 else None

        config_logger.info(
            f"Banner callback - remaining_items: {remaining_items}, "
            f"remaining_points: {remaining_points}"
        )

        display_names = get_active_profile_and_query_display_names()
        profile_name = display_names.get("profile_name")
        query_name = display_names.get("query_name")

        banner_content = create_parameter_bar_collapsed(
            pert_factor=pert_factor,
            deadline=deadline,
            scope_items=scope_items,
            scope_points=round(scope_points, 1),
            remaining_items=scope_items,
            remaining_points=round(scope_points, 1),
            total_items=scope_items,
            total_points=round(scope_points, 1),
            show_points=show_points,
            data_points=data_points,
            profile_name=profile_name,
            query_name=query_name,
        )

        return banner_content.children[0]  # type: ignore[index]

    @app.callback(
        [
            Output("data-points-input", "max"),
            Output("data-points-input", "marks"),
            Output("data-points-input", "value"),
        ],
        [Input("current-statistics", "data")],
        [State("data-points-input", "value")],
        prevent_initial_call=False,
    )
    def update_data_points_slider_marks(
        statistics: list | None, current_value: int | None
    ) -> tuple[int, dict, int]:

        max_data_points = 52
        if statistics and len(statistics) > 0:
            max_data_points = len(statistics)

        min_data_points = 4
        range_size = max_data_points - min_data_points

        if range_size <= 12:
            data_points_marks = {
                i: {"label": str(i)}
                for i in range(min_data_points, max_data_points + 1)
            }
        else:
            quarter_point = round(min_data_points + range_size / 4)
            middle_point = round(min_data_points + range_size / 2)
            three_quarter_point = round(min_data_points + 3 * range_size / 4)

            mark_values = sorted(
                {
                    min_data_points,
                    quarter_point,
                    middle_point,
                    three_quarter_point,
                    max_data_points,
                }
            )
            data_points_marks = {val: {"label": str(val)} for val in mark_values}

        clamped_value = current_value if current_value else max_data_points
        if clamped_value > max_data_points:
            clamped_value = max_data_points
            logger.info(
                f"Data Points slider value clamped from {current_value} to "
                f"{clamped_value} (max={max_data_points})"
            )

        logger.info(
            f"Data Points slider updated: max={max_data_points}, "
            f"marks={list(data_points_marks.keys())}, value={clamped_value}"
        )

        return max_data_points, data_points_marks, clamped_value

    @app.callback(
        [
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("calculation-results", "data", allow_duplicate=True),
        ],
        [Input("metrics-refresh-trigger", "data")],
        [State("current-statistics", "data"), State("data-points-input", "value")],
        prevent_initial_call=True,
    )
    def reload_scope_after_metrics(
        refresh_trigger: int | None,
        statistics: list | None,
        data_points_count: int | None,
    ) -> tuple:

        if not refresh_trigger:
            raise PreventUpdate

        logger.info(
            f"[Settings] Reloading BASE scope from database after metrics, then "
            f"calculating WINDOWED scope for {data_points_count} data points"
        )

        result = calculate_remaining_work_for_data_window(data_points_count, statistics)

        if result:
            logger.info(
                f"[Settings] Scope reloaded and windowed: estimated_items={result[0]}, "
                f"remaining_items={result[1]}, estimated_points={result[2]}, "
                f"remaining_points={result[3]}"
            )
            return result
        else:
            logger.warning(
                "[Settings] Failed to calculate windowed scope after metrics reload"
            )
            raise PreventUpdate

    @app.callback(
        [
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("calculation-results", "data", allow_duplicate=True),
        ],
        [Input("data-points-input", "value")],
        [
            State("current-statistics", "data"),
            State("app-init-complete", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_remaining_work_on_data_points_change(
        data_points_count: int | None, statistics: list | None, init_complete: bool
    ) -> tuple:

        logger.info(
            "[Settings] Data Points slider callback fired: "
            f"data_points={data_points_count}, "
            f"init_complete={init_complete}, "
            f"statistics count={len(statistics) if statistics else 0}"
        )

        if not init_complete or not statistics or not data_points_count:
            raise PreventUpdate

        result = calculate_remaining_work_for_data_window(data_points_count, statistics)

        if result:
            return result
        else:
            raise PreventUpdate

    @app.callback(
        [
            Output("jira-cache-status", "children", allow_duplicate=True),
            Output("progress-poll-interval", "disabled", allow_duplicate=True),
            Output("update-data-progress-container", "style", allow_duplicate=True),
            Output("update-data-unified", "style", allow_duplicate=True),
            Output("cancel-operation-btn", "style", allow_duplicate=True),
            Output("trigger-auto-metrics-calc", "data", allow_duplicate=True),
        ],
        Input("url", "pathname"),
        prevent_initial_call="initial_duplicate",
    )
    def restore_update_data_progress(pathname: str) -> tuple:

        import time  # noqa: PLC0415

        restart_marker = Path("task_progress.json.restart")
        if restart_marker.exists():
            try:
                import json  # noqa: PLC0415

                marker_data = json.loads(restart_marker.read_text())
                restart_time = marker_data.get("restart_time", 0)
                if time.time() - restart_time < 5:
                    logger.info(
                        "[Settings] App restart detected - "
                        "not restoring stale task progress"
                    )
                    restart_marker.unlink()
                    raise PreventUpdate
                else:
                    restart_marker.unlink()
            except Exception as e:
                logger.debug(f"Restart marker check failed: {e}")

        active_task = TaskProgress.get_active_task()

        if (
            active_task
            and active_task.get("task_id") == "update_data"
            and active_task.get("status") == "in_progress"
        ):
            logger.info(
                "[Settings] Restoring Update Data progress state on page load - "
                "enabling progress bar polling"
            )

            status_message = html.Div(
                [
                    html.I(className="fas fa-spinner fa-spin me-2 text-primary"),
                    html.Span(
                        TaskProgress.get_task_status_message("update_data")
                        or "Updating data...",
                        className="fw-medium",
                    ),
                ],
                className="text-primary small text-center mt-2",
            )

            metrics_trigger = None
            phase = active_task.get("phase")
            fetch_progress = active_task.get("fetch_progress", {})
            fetch_percent = fetch_progress.get("percent", 0)

            logger.info(
                "[Settings] Recovery check: "
                f"phase={phase}, fetch_percent={fetch_percent}"
            )

            if phase == "calculate":
                logger.info(
                    "Task in calculate phase on page load - "
                    "triggering metrics calculation"
                )
                metrics_trigger = int(time.time() * 1000)
            elif phase == "fetch" and fetch_percent == 0:
                logger.warning(
                    "[Settings] Recovery: Task stuck at fetch 0%. "
                    "Post-migration assumes changes exist."
                )

                TaskProgress.update_progress(
                    "update_data",
                    "calculate",
                    0,
                    0,
                    "Preparing metrics calculation...",
                )
                metrics_trigger = int(time.time() * 1000)

            ui_state = active_task.get("ui_state", {})
            operation_in_progress = ui_state.get("operation_in_progress", True)

            update_data_style = {"display": "none"} if operation_in_progress else {}
            cancel_button_style = {} if operation_in_progress else {"display": "none"}

            logger.info(
                f"[Settings] Restoring button visibility: "
                f"operation_in_progress={operation_in_progress}"
            )

            return (
                status_message,
                False,
                {"display": "block", "minHeight": "60px"},
                update_data_style,
                cancel_button_style,
                metrics_trigger,
            )

        return (
            "",
            True,
            {"display": "none"},
            {},
            {"display": "none"},
            no_update,
        )
