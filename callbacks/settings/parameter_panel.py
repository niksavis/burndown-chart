"""Parameter Panel UI Callbacks.

This module handles parameter panel user interface interactions:
- Toggle panel expand/collapse
- Update parameter summary bar
- Data points slider dynamic marks
- Reload scope after metrics calculation
- Update remaining work on slider changes
- Task progress restoration on page load

Related modules:
- ui.parameter_panel: Parameter panel components
- data.task_progress: Background task progress tracking
- callbacks.settings.helpers: Calculation utilities
"""

from __future__ import annotations

import logging
from typing import Any

from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate

# Import helper functions
from callbacks.settings.helpers import calculate_remaining_work_for_data_window
from configuration import DEFAULT_PERT_FACTOR
from configuration import logger as config_logger
from ui.parameter_panel import create_parameter_bar_collapsed

# Get logger
logger = logging.getLogger(__name__)


def register(app: Any) -> None:
    """Register parameter panel UI callbacks.

    Args:
        app: Dash application instance
    """

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
        """Toggle parameter panel expand/collapse and persist state.

        This supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
        Ensures only one flyout panel is open at a time.

        Args:
            n_clicks: Number of times expand button was clicked
            is_open: Current state of the collapse component
            panel_state: Current parameter panel state from dcc.Store
            settings_is_open: Current settings panel state
            import_export_is_open: Current import/export panel state

        Returns:
            Tuple of (new_is_open, updated_panel_state, new_settings_state,
                      new_import_export_state)
        """
        from datetime import datetime

        if n_clicks:
            new_is_open = not is_open
            # Update panel state with new preference
            updated_state = {
                "is_open": new_is_open,
                "last_updated": datetime.now().isoformat(),
                "user_preference": True,
            }

            # If opening parameter panel, close other panels
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
        """Update parameter summary in collapsed bar when values change.

        This supports User Story 1: Quick Parameter Adjustments While Viewing Charts.

        Args:
            pert_factor: Current PERT factor value
            deadline: Current deadline date string
            scope_items: Total number of items in scope
            scope_points: Total story points in scope
            data_points: Number of data points to display
            settings: Current app settings

        Returns:
            Updated collapsed bar children
        """
        # Provide defaults for None values
        pert_factor = pert_factor or DEFAULT_PERT_FACTOR

        # If deadline from picker is None, use settings fallback
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

        # Parse scope_points - may be string or float
        try:
            scope_points = float(scope_points) if scope_points else 0.0
        except (ValueError, TypeError):
            scope_points = 0.0

        # Get show_points setting
        show_points = settings.get("show_points", True) if settings else True

        remaining_items = scope_items if scope_items > 0 else None
        remaining_points = scope_points if scope_points > 0 else None

        config_logger.info(
            f"Banner callback - remaining_items: {remaining_items}, "
            f"remaining_points: {remaining_points}"
        )

        # Get active profile and query names for display
        from data.profile_manager import get_active_profile_and_query_display_names

        display_names = get_active_profile_and_query_display_names()
        profile_name = display_names.get("profile_name")
        query_name = display_names.get("query_name")

        # Use the shared function to create the banner
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

        # Extract just the Row children from the returned html.Div
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
        """Update Data Points slider max, marks, and value when statistics change.

        This ensures the slider reflects the current data size after fetching
        new data from JIRA or importing data. The slider value is clamped to the
        new maximum to prevent invalid states when switching between queries.

        Args:
            statistics: List of statistics data points
            current_value: Current slider value (to be clamped if needed)

        Returns:
            Tuple of (max_value, marks_dict, clamped_value)
        """
        # Calculate max data points from statistics
        max_data_points = 52  # Default max
        if statistics and len(statistics) > 0:
            max_data_points = len(statistics)

        # Calculate dynamic marks for Data Points slider
        min_data_points = 4
        range_size = max_data_points - min_data_points

        # If range is small (<=12 weeks), show all intermediate values
        if range_size <= 12:
            data_points_marks = {
                i: {"label": str(i)}
                for i in range(min_data_points, max_data_points + 1)
            }
        else:
            # For larger ranges, calculate 5 evenly-spaced marks
            quarter_point = round(min_data_points + range_size / 4)
            middle_point = round(min_data_points + range_size / 2)
            three_quarter_point = round(min_data_points + 3 * range_size / 4)

            # Ensure no duplicates
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

        # Clamp current value to new maximum
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
        """Reload scope data from database after metrics calculation completes.

        This callback reloads the BASE scope from database and recalculates the
        WINDOWED scope based on the current data points slider value.

        Args:
            refresh_trigger: Timestamp when metrics calculation completed
            statistics: Current statistics data
            data_points_count: Current data points slider value

        Returns:
            Tuple of (estimated_items, remaining_items, estimated_points,
                      remaining_points_display, calc_results)
        """
        if not refresh_trigger:
            raise PreventUpdate

        logger.info(
            f"[Settings] Reloading BASE scope from database after metrics, then "
            f"calculating WINDOWED scope for {data_points_count} data points"
        )

        # Calculate windowed scope based on current slider position
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
        """Recalculate WINDOWED remaining work scope when Data Points slider changes.

        This is the PRIMARY callback that ensures parameter panel values reflect
        the selected time window.

        Args:
            data_points_count: Number of data points selected on the slider
            statistics: List of statistics data points
            init_complete: Whether app initialization is complete

        Returns:
            Tuple of (estimated_items, remaining_items, estimated_points,
                      remaining_points, calc_results)
        """
        logger.info(
            "[Settings] Data Points slider callback fired: "
            f"data_points={data_points_count}, "
            f"init_complete={init_complete}, "
            f"statistics count={len(statistics) if statistics else 0}"
        )

        if not init_complete or not statistics or not data_points_count:
            raise PreventUpdate

        # Use the helper function to calculate remaining work
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
        """Restore progress bar and button visibility on page load.

        This callback runs on page load to check if an Update Data task
        was in progress before the page was refreshed or app restarted.

        Args:
            pathname: Current URL pathname (triggers on page load)

        Returns:
            Tuple of (status_message, polling_enabled, progress_bar_style,
                      update_button_style, cancel_button_style, metrics_trigger)
        """
        import time
        from pathlib import Path

        from data.task_progress import TaskProgress

        # Check if app was just restarted (stale task cleanup ran)
        restart_marker = Path("task_progress.json.restart")
        if restart_marker.exists():
            try:
                import json

                marker_data = json.loads(restart_marker.read_text())
                restart_time = marker_data.get("restart_time", 0)
                # If restart was within last 5 seconds, don't restore progress
                if time.time() - restart_time < 5:
                    logger.info(
                        "[Settings] App restart detected - "
                        "not restoring stale task progress"
                    )
                    restart_marker.unlink()
                    raise PreventUpdate
                else:
                    # Old marker, ignore it
                    restart_marker.unlink()
            except Exception as e:
                logger.debug(f"Restart marker check failed: {e}")

        # Check if Update Data task is active
        active_task = TaskProgress.get_active_task()

        # Only restore in_progress tasks, not complete/error
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

            # Check if we're in calculate phase and need to trigger metrics
            metrics_trigger = None
            phase = active_task.get("phase")
            fetch_progress = active_task.get("fetch_progress", {})
            fetch_percent = fetch_progress.get("percent", 0)

            logger.info(
                "[Settings] Recovery check: "
                f"phase={phase}, fetch_percent={fetch_percent}"
            )

            if phase == "calculate":
                # Page refreshed during/after fetch - trigger metrics calculation
                logger.info(
                    "Task in calculate phase on page load - "
                    "triggering metrics calculation"
                )
                metrics_trigger = int(time.time() * 1000)
            elif phase == "fetch" and fetch_percent == 0:
                # Recovery: Stuck in fetch phase with 0% progress
                logger.warning(
                    "[Settings] Recovery: Task stuck at fetch 0%. "
                    "Post-migration assumes changes exist."
                )

                # Update progress to show fetch complete
                TaskProgress.update_progress(
                    "update_data",
                    "calculate",
                    0,
                    0,
                    "Preparing metrics calculation...",
                )
                metrics_trigger = int(time.time() * 1000)

            # Read button visibility from ui_state
            ui_state = active_task.get("ui_state", {})
            operation_in_progress = ui_state.get("operation_in_progress", True)

            update_data_style = {"display": "none"} if operation_in_progress else {}
            cancel_button_style = {} if operation_in_progress else {"display": "none"}

            logger.info(
                f"[Settings] Restoring button visibility: "
                f"operation_in_progress={operation_in_progress}"
            )

            # Enable progress polling and show progress bar
            return (
                status_message,
                False,  # Enable progress polling
                {"display": "block", "minHeight": "60px"},
                update_data_style,
                cancel_button_style,
                metrics_trigger,
            )

        # No active task - return normal state
        return (
            "",  # No status message
            True,  # Disable progress polling
            {"display": "none"},  # Hide progress bar
            {},  # Show Update Data button
            {"display": "none"},  # Hide Cancel button
            no_update,
        )
