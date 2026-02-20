"""
Core Settings Callbacks

This module handles core settings management callbacks including:
- Total points calculation
- Settings reload after import/profile switch
- UI sync with settings store
- Settings persistence
"""

import time
from datetime import datetime

import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate

from configuration import (
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_TOTAL_POINTS,
    logger,
)
from data import calculate_total_points

from .helpers import normalize_show_points


def register(app):
    """
    Register core settings callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [
            Output("total-points-display", "value"),
            Output("calculation-results", "data"),
        ],
        [
            Input("total-items-input", "value"),
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("current-statistics", "modified_timestamp"),
        ],
        [
            State("current-statistics", "data"),
            State("calculation-results", "data"),
            State("total-points-display", "value"),
        ],
    )
    def update_total_points_calculation(
        total_items,
        estimated_items,
        estimated_points,
        stats_ts,
        statistics,
        calc_results,
        current_total_points_display,
    ):
        """
        Update the total points calculation based on estimated items and points or historical data.

        Uses the same extrapolation formula as JIRA scope calculator:
        remaining_total_points = estimated_points + (avg_points_per_item × unestimated_items)

        This ensures consistency between JIRA and manual data entry workflows.
        Manual changes to inputs will always trigger recalculation, allowing users to
        adjust forecasts even when working with JIRA data.
        """
        # Input validation
        if None in [total_items, estimated_items, estimated_points]:
            return (
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.1f}",
                calc_results
                or {"total_points": DEFAULT_TOTAL_POINTS, "avg_points_per_item": 0},
            )

        # Handle invalid inputs by converting to numbers
        try:
            total_items = int(total_items)
            estimated_items = int(estimated_items)
            estimated_points = float(estimated_points)
        except (ValueError, TypeError):
            return (
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.1f}",
                calc_results
                or {"total_points": DEFAULT_TOTAL_POINTS, "avg_points_per_item": 0},
            )

        # Calculate total points and average
        estimated_total_points, avg_points_per_item = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            statistics,
            use_fallback=False,
        )

        # Update the calculation results store
        updated_calc_results = {
            "total_points": estimated_total_points,
            "avg_points_per_item": avg_points_per_item,
        }

        return (
            f"{estimated_total_points:.1f}",
            updated_calc_results,
        )

    @app.callback(
        Output("remaining-points-formula", "children"),
        Input("calculation-results", "data"),
    )
    def update_remaining_points_formula(calc_results):
        """Update the formula display to show the actual avg coefficient being used."""
        if not calc_results:
            return "= Est. Points + (avg × unestimated)."

        avg = calc_results.get("avg_points_per_item", 0)
        if avg > 0:
            return f"= Est. Points + ({avg:.2f} × unestimated)."
        else:
            return "= Est. Points + (avg × unestimated)."

    @app.callback(
        [
            Output("current-settings", "data", allow_duplicate=True),
            Output("current-settings", "modified_timestamp", allow_duplicate=True),
        ],
        [
            Input("metrics-refresh-trigger", "data"),
            Input("profile-switch-trigger", "data"),
        ],
        prevent_initial_call=True,
    )
    def reload_settings_after_import_or_switch(metrics_trigger, profile_trigger):
        """
        Reload settings from database after import or profile switch.

        This ensures that imported profile settings (show_points, pert_factor, etc.)
        are loaded into the UI, fixing the bug where imported settings weren't displayed.
        """
        from data.persistence import load_app_settings
        from data.profile_manager import get_active_profile

        logger.info(
            f"[Settings] reload_settings_after_import_or_switch triggered: "
            f"metrics_trigger={metrics_trigger}, profile_trigger={profile_trigger}"
        )

        try:
            # Check if we have an active profile
            active_profile = get_active_profile()
            if not active_profile:
                logger.info("[Settings] No active profile, skipping settings reload")
                raise PreventUpdate

            # Load settings from database
            settings = load_app_settings()

            if not settings:
                logger.warning(
                    "[Settings] No settings found in database after import/switch"
                )
                raise PreventUpdate

            # Normalize show_points to boolean for consistency
            settings["show_points"] = normalize_show_points(
                settings.get("show_points", True)
            )

            logger.info(
                f"[Settings] Reloaded settings from database: "
                f"show_points={settings.get('show_points')}, "
                f"pert_factor={settings.get('pert_factor')}, "
                f"deadline={settings.get('deadline')}, "
                f"milestone={settings.get('milestone')}, "
                f"data_points={settings.get('data_points_count')}"
            )

            return settings, time.time()

        except Exception as e:
            logger.error(
                f"[Settings] Error reloading settings after import: {e}", exc_info=True
            )
            raise PreventUpdate from e

    @app.callback(
        [
            Output("pert-factor-slider", "value", allow_duplicate=True),
            Output("deadline-picker", "date", allow_duplicate=True),
            Output("points-toggle", "value", allow_duplicate=True),
            Output("data-points-input", "value", allow_duplicate=True),
            Output("milestone-picker", "date", allow_duplicate=True),
        ],
        Input("current-settings", "modified_timestamp"),
        State("current-settings", "data"),
        prevent_initial_call=True,
    )
    def sync_ui_inputs_with_settings(settings_timestamp, settings):
        """
        Update UI input components when current-settings store changes.

        This ensures that when settings are reloaded from database (after import/profile switch),
        the visible UI inputs reflect the loaded values.
        """
        if not settings:
            raise PreventUpdate

        # Convert show_points boolean back to checklist format
        show_points = settings.get("show_points", True)
        points_toggle_value = ["show"] if show_points else []

        # Date pickers use clearable=True
        deadline = settings.get("deadline")
        milestone = settings.get("milestone")

        return (
            settings.get("pert_factor", 1.2),
            deadline,
            points_toggle_value,
            settings.get("data_points_count", 20),
            milestone,
        )

    @app.callback(
        [
            Output("current-settings", "data"),
            Output("current-settings", "modified_timestamp"),
        ],
        [
            Input("pert-factor-slider", "value"),
            Input("deadline-picker", "date"),
            Input("milestone-picker", "date"),
            Input("total-items-input", "value"),
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("data-points-input", "value"),
            Input("points-toggle", "value"),
        ],
        [
            State("app-init-complete", "data"),
            State("current-statistics", "data"),
            State("calculation-results", "data"),
            State("jira-jql-query", "value"),
        ],
    )
    def update_and_save_settings(
        pert_factor,
        deadline,
        milestone,
        total_items,
        estimated_items,
        estimated_points,
        data_points_count,
        show_points,
        init_complete,
        statistics,
        calc_results,
        jql_query,
    ):
        """
        Update current settings and save to disk when changed.
        Handles both legacy inputs and new parameter panel inputs.
        """
        ctx = dash.callback_context

        show_milestone = milestone is not None

        # Skip if not initialized or critical values are None
        if (
            not init_complete
            or not ctx.triggered
            or None in [pert_factor, total_items, data_points_count]
        ):
            raise PreventUpdate

        data_points_count = (
            int(data_points_count) if data_points_count is not None else 12
        )

        # Initialize with fallback values
        total_points = (
            calc_results.get("total_points", DEFAULT_TOTAL_POINTS)
            if calc_results
            else DEFAULT_TOTAL_POINTS
        )

        # Load current remaining work from project_scope
        try:
            from data.persistence import load_unified_project_data
            from data.profile_manager import get_active_profile

            active_profile = get_active_profile()
            if not active_profile:
                logger.info("[Settings] No active profile, using default values")
                raise PreventUpdate

            unified_data = load_unified_project_data()
            project_scope = unified_data.get("project_scope", {})

            total_items = project_scope.get("remaining_items", total_items)
            total_points = project_scope.get("remaining_total_points", total_points)

            logger.info(
                f"[Settings] Using CURRENT remaining work from project_scope: "
                f"{total_items} items, {total_points:.1f} points "
                f"(data_points slider: {data_points_count} weeks)"
            )
        except Exception as e:
            logger.error(
                f"[Settings] Error loading current remaining work: {e}", exc_info=True
            )

        # Use fallback values
        input_values = {
            "estimated_items": estimated_items,
            "estimated_points": estimated_points,
        }
        estimated_items = input_values.get("estimated_items", DEFAULT_ESTIMATED_ITEMS)
        estimated_points = input_values.get(
            "estimated_points", DEFAULT_ESTIMATED_POINTS
        )

        settings = {
            "pert_factor": pert_factor,
            "deadline": deadline,
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items,
            "estimated_points": estimated_points,
            "data_points_count": data_points_count,
            "show_milestone": show_milestone,
            "milestone": milestone,
            "show_points": normalize_show_points(show_points),
        }

        # Save app-level settings
        from data.persistence import load_app_settings, save_app_settings

        existing_settings = load_app_settings()

        # Preserve values that might not have been updated yet
        from dash import ctx

        if ctx.triggered:
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if triggered_id not in [
                "milestone-picker",
                "points-toggle",
                "deadline-picker",
            ]:
                show_milestone = existing_settings.get("show_milestone", show_milestone)
                settings["show_points"] = existing_settings.get(
                    "show_points", settings["show_points"]
                )
                deadline = existing_settings.get("deadline", deadline)
                milestone = existing_settings.get("milestone", milestone)
                settings["deadline"] = deadline
                settings["milestone"] = milestone

        save_app_settings(
            pert_factor,
            deadline,
            data_points_count,
            show_milestone,
            milestone,
            settings["show_points"],
            jql_query.strip()
            if jql_query and jql_query.strip()
            else "project = JRASERVER",
            existing_settings.get("last_used_data_source"),
            existing_settings.get("active_jql_profile_id"),
        )

        trigger_id = (
            ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "unknown"
        )
        logger.info(
            f"[Settings] Updated settings (triggered by {trigger_id}): "
            f"data_points={data_points_count}, total_items={total_items}, "
            f"total_points={total_points:.1f}"
        )
        return settings, int(datetime.now().timestamp() * 1000)
