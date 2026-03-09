"""
Visualization Callbacks Module

This module handles callbacks related to visualization updates and interactions.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import json
import logging
from datetime import datetime

# Third-party library imports
import pandas as pd
from dash import (
    Input,
    Output,
    State,
    callback,
    callback_context,
    html,
)
from dash.exceptions import PreventUpdate

# Application imports
from callbacks.active_work_timeline import _render_active_work_timeline_content
from callbacks.bug_analysis import _render_bug_analysis_content
from callbacks.sprint_tracker import _render_sprint_tracker_content
from callbacks.visualization_helpers import check_has_points_in_period
from callbacks.visualization_helpers.burndown_tab import _render_burndown_tab
from callbacks.visualization_helpers.dashboard_tab import _render_dashboard_tab
from callbacks.visualization_helpers.data_checks import filter_df_by_week_labels
from callbacks.visualization_helpers.tab_content import (
    create_scope_tracking_tab_content,
)
from data import compute_cumulative_values
from data.metrics_snapshots import load_snapshots
from data.persistence import load_unified_project_data
from ui.cards.data_cards import create_statistics_data_card
from ui.dora_metrics_dashboard import create_dora_dashboard
from ui.flow_metrics_dashboard import create_flow_dashboard
from ui.loading_utils import create_content_placeholder
from visualization import create_forecast_plot
from visualization.charts import apply_mobile_optimization

# Setup logging
logger = logging.getLogger("burndown_chart")

#######################################################################
# CALLBACKS
#######################################################################


#######################################################################
# CALLBACKS
#######################################################################


def register(app):
    """
    Register all visualization-related callbacks.

    Args:
        app: Dash application instance
    """

    # Client-side callback for dynamic viewport detection
    app.clientside_callback(
        """
        function(n_intervals, init_complete) {
            const width = window.innerWidth;
            if (width < 768) {
                return "mobile";
            } else if (width < 1024) {
                return "tablet";
            } else {
                return "desktop";
            }
        }
        """,
        Output("viewport-size", "data"),
        [Input("viewport-detector", "n_intervals"), Input("app-init-complete", "data")],
    )

    @app.callback(
        Output("app-init-complete", "data"), [Input("chart-tabs", "active_tab")]
    )
    def mark_initialization_complete(active_tab):
        """
        Mark the application as fully initialized after the tabs are rendered.
        This prevents saving during initial load
        and avoids triggering callbacks prematurely.
        """
        return True

    @app.callback(
        Output("forecast-graph", "figure"),
        [
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
            Input("chart-tabs", "active_tab"),
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
            State("viewport-size", "data"),
        ],
    )
    def update_forecast_graph(
        settings_ts,
        statistics_ts,
        calc_results,
        active_tab,
        settings,
        statistics,
        viewport_size,
    ):
        """Update the forecast graph when settings or statistics change."""
        # Get context to see which input triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Only proceed if we're on the burndown tab
        if active_tab != "tab-burndown":
            raise PreventUpdate  # Don't update when not on burndown tab

        # Validate inputs
        if settings is None or statistics is None:
            raise PreventUpdate

        # Get triggered input ID
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # If triggered by calculation_results but data is None, prevent update
        if trigger_id == "calculation-results" and calc_results is None:
            raise PreventUpdate

        # Detect viewport size for mobile optimization
        viewport_size = viewport_size or "desktop"
        is_mobile = viewport_size == "mobile"
        is_tablet = viewport_size == "tablet"

        # Process the settings and statistics data
        df = pd.DataFrame(statistics)
        if len(df) > 0:  # Check if there's any data
            df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
            df = df.sort_values("date")

        # Get necessary values
        total_items = settings.get("total_items", 100)
        total_points = settings.get("total_points", 500)
        pert_factor = settings.get("pert_factor", 3)
        deadline = settings.get("deadline", None)
        data_points_count = int(
            settings.get("data_points_count", len(df))
        )  # Get selected data points count (ensure int)

        # Get milestone settings
        show_milestone = settings.get("show_milestone", False)
        milestone = settings.get("milestone", None) if show_milestone else None

        # Process data for calculations
        if not df.empty:
            df = compute_cumulative_values(df, total_items, total_points)

        # Create forecast plot and get PERT values
        fig, _ = create_forecast_plot(
            df=df,
            total_items=total_items,
            total_points=total_points,
            pert_factor=pert_factor,
            deadline_str=deadline,
            milestone_str=milestone,  # Pass milestone parameter
            data_points_count=data_points_count,
            show_points=settings.get(
                "show_points", False
            ),  # Pass show_points parameter
        )

        # Apply mobile optimization to chart
        fig, _ = apply_mobile_optimization(
            fig,
            is_mobile=is_mobile,
            is_tablet=is_tablet,
            title="Burndown Forecast" if not is_mobile else None,
        )

        return fig

    # Performance-optimized tab content callback with lazy loading and caching
    @app.callback(
        [
            Output("tab-content", "children"),
            Output("chart-cache", "data"),
            Output("ui-state", "data"),
        ],
        [
            Input("chart-tabs", "active_tab"),
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
            Input("date-range-weeks", "data"),
            Input("points-toggle", "value"),  # Updated to new parameter panel component
            Input(
                "budget-settings-store", "data"
            ),  # Trigger refresh when budget changes
            Input("metrics-refresh-trigger", "data"),  # Trigger refresh after import
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
            State("chart-cache", "data"),
            State("ui-state", "data"),
            State("viewport-size", "data"),
        ],
    )
    def render_tab_content(
        active_tab,
        settings_ts,
        statistics_ts,
        calc_results,
        date_range_weeks,
        show_points,  # Added parameter
        budget_store,  # Added parameter
        import_trigger,  # Added parameter
        settings,
        statistics,
        chart_cache,
        ui_state,
        viewport_size,
    ):
        """
        Render the appropriate content based on the selected tab
        with lazy loading and caching.
        Only generates charts for the active tab to improve performance.
        Target: <500ms chart rendering,
        immediate skeleton loading, <100ms cached responses.
        """
        # TECH LEAD FIX: The previous "CRITICAL FIX" code was causing
        # the bug, not fixing it.
        #
        # The bug: That code tried to work around stale active_tab
        # by using ui_state["last_tab"]
        # when the trigger wasn't from tab change. But this is backwards logic!
        #
        # What actually happens:
        # 1. User clicks scope tab ->
        #    active_tab="tab-scope-tracking", last_tab="tab-scope-tracking"
        # 2. User clicks burndown tab -> Dash correctly passes active_tab="tab-burndown"
        # 3. If any other input changes (settings, statistics, etc),
        #    the old code would
        #    IGNORE the correct active_tab and use the stale last_tab instead!
        # 4. This caused scope content to render on every tab after visiting it once
        #
        # THE FIX: Trust Dash! The active_tab parameter is ALWAYS correct.
        # Dash automatically provides the current tab state,
        # even when other inputs trigger the callback.
        # We should NEVER override it with stored state.

        ctx = callback_context
        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else "initial"
        logger.debug(
            "[CTO DEBUG] render_tab_content triggered by: "
            f"{trigger_info}, active_tab='{active_tab}', "
            f"cache_size={len(chart_cache) if chart_cache else 0}"
        )

        # CRITICAL DEBUG: Log statistics data to diagnose query switching issue
        if statistics:
            logger.info(
                "[VISUALIZATION] render_tab_content received "
                f"{len(statistics)} statistics"
            )
            logger.info(
                "[VISUALIZATION] First stat: "
                f"date={statistics[0].get('date')}, "
                f"items={statistics[0].get('remaining_items')}, "
                f"points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                "[VISUALIZATION] Last stat: "
                f"date={statistics[-1].get('date')}, "
                f"items={statistics[-1].get('remaining_items')}, "
                f"points={statistics[-1].get('remaining_total_points')}"
            )
        else:
            logger.warning(
                "[VISUALIZATION] render_tab_content received EMPTY statistics!"
            )

        # Handle initial load: if active_tab is None or empty, default to burndown
        if not active_tab:
            logger.debug(
                "[CTO DEBUG] active_tab was empty/None, defaulting to tab-burndown"
            )
            active_tab = "tab-burndown"

        if not settings or not statistics:
            ui_state = ui_state or {"loading": False, "last_tab": None}
            chart_cache = chart_cache or {}
            error_content = create_content_placeholder(
                type="chart",
                text="No data available. Please load project data first.",
                height="400px",
            )
            return error_content, chart_cache, ui_state

        # Initialize cache and UI state if None
        if chart_cache is None:
            chart_cache = {}
        if ui_state is None:
            ui_state = {"loading": False, "last_tab": None}

        # Detect viewport size for mobile optimization (Phase 7: User Story 5)
        viewport_size = viewport_size or "desktop"
        is_mobile = viewport_size == "mobile"
        is_tablet = viewport_size == "tablet"
        logger.info(
            f"Rendering charts for viewport: {viewport_size} "
            f"(mobile={is_mobile}, tablet={is_tablet})"
        )

        # Convert checklist value to boolean (points-toggle returns list, not boolean)
        show_points = bool(
            show_points and (show_points is True or "show" in show_points)
        )

        # CTO FIX: Clear old cache entries to prevent memory bloat (keep last 5)
        # BUT: If we're switching tabs (trigger is from chart-tabs), clear ALL cache
        # to prevent any possibility of cross-tab contamination
        # ALSO: Clear ALL cache when budget changes to ensure fresh render
        # ALSO: Clear ALL cache when statistics change (table edits)
        # to ensure immediate reactivity
        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        if "chart-tabs" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Tab switch detected - "
                "CLEARING ALL CACHE to prevent contamination"
            )
            chart_cache = {}
        elif "budget-settings-store" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Budget change detected - "
                "CLEARING ALL CACHE to refresh budget cards"
            )
            chart_cache = {}
        elif "metrics-refresh-trigger" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Import/refresh detected - "
                "CLEARING ALL CACHE to reload data"
            )
            chart_cache = {}
        elif "current-statistics.modified_timestamp" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Statistics modified (table edit) - "
                "CLEARING ALL CACHE to show changes immediately"
            )
            chart_cache = {}
        elif len(chart_cache) > 5:
            oldest_keys = list(chart_cache.keys())[:-5]
            for old_key in oldest_keys:
                if old_key in chart_cache:
                    del chart_cache[old_key]

        # Create simplified cache key - only essential data for chart generation
        data_hash = hash(
            str(statistics)
            + str(settings)
            + str(show_points)
            + str(budget_store)
            + str(import_trigger)
        )
        cache_key = f"{active_tab}_{data_hash}"
        use_cache_for_tab = active_tab != "tab-active-work-timeline"
        logger.debug(f"[CTO DEBUG] Cache key generated: {cache_key}")

        # Check if we have cached content for this exact state
        if use_cache_for_tab and cache_key in chart_cache:
            # Return cached content immediately for <100ms response time
            logger.debug(
                "[CTO DEBUG] Returning CACHED content for "
                f"active_tab='{active_tab}', cache_key={cache_key}"
            )
            ui_state["loading"] = False
            ui_state["last_tab"] = active_tab
            return chart_cache[cache_key], chart_cache, ui_state

        # Set loading state for new tab content generation
        ui_state["loading"] = True
        ui_state["last_tab"] = active_tab

        try:
            data_points_count = int(
                settings.get("data_points_count", 12)
            )  # Ensure int, default 12

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            if active_tab == "tab-dashboard":
                logger.debug(
                    "[CTO DEBUG] Creating NEW modern dashboard "
                    f"content, cache_key={cache_key}"
                )
                dashboard_content = _render_dashboard_tab(df, settings, show_points)
                chart_cache[cache_key] = dashboard_content
                ui_state["loading"] = False
                return dashboard_content, chart_cache, ui_state
            elif active_tab == "tab-burndown":
                logger.debug(
                    f"[CTO DEBUG] Creating NEW burndown content, cache_key={cache_key}"
                )
                burndown_tab_content = _render_burndown_tab(
                    df,
                    statistics,
                    settings,
                    show_points,
                    data_points_count,
                    is_mobile,
                    is_tablet,
                )
                chart_cache[cache_key] = burndown_tab_content
                ui_state["loading"] = False
                return burndown_tab_content, chart_cache, ui_state

            elif active_tab == "tab-scope-tracking":
                logger.debug(
                    "[CTO DEBUG] Creating NEW scope tracking content, "
                    f"cache_key={cache_key}"
                )
                df_for_scope = filter_df_by_week_labels(df.copy(), data_points_count)
                has_points_data = show_points and check_has_points_in_period(
                    statistics, data_points_count
                )
                scope_tab_content = create_scope_tracking_tab_content(
                    df_for_scope, settings, show_points and has_points_data
                )
                chart_cache[cache_key] = scope_tab_content
                ui_state["loading"] = False
                return scope_tab_content, chart_cache, ui_state

            elif active_tab == "tab-bug-analysis":
                # Generate bug analysis tab content directly (no placeholder loading)
                # Import the actual rendering function from bug_analysis callback

                # Get data_points_count from settings
                data_points_count = int(
                    settings.get("data_points_count", 12)
                )  # Ensure int

                # Check if points data exists in the filtered time period
                has_points_data = False
                if show_points:
                    has_points_data = check_has_points_in_period(
                        statistics, data_points_count
                    )

                # Render the actual content immediately
                bug_analysis_content = _render_bug_analysis_content(
                    data_points_count, show_points, has_points_data
                )

                # Cache the result for next time
                chart_cache[cache_key] = bug_analysis_content
                ui_state["loading"] = False
                return bug_analysis_content, chart_cache, ui_state

            elif active_tab == "tab-dora-metrics":
                # Generate DORA metrics dashboard
                # Callback will populate with metrics (prevent_initial_call=False)

                dora_content = create_dora_dashboard()

                # Cache the result for next time
                chart_cache[cache_key] = dora_content
                ui_state["loading"] = False
                return dora_content, chart_cache, ui_state

            elif active_tab == "tab-flow-metrics":
                # Generate Flow metrics dashboard
                # Callback will populate with metrics (prevent_initial_call=False)

                flow_content = create_flow_dashboard()

                # Cache the result for next time
                chart_cache[cache_key] = flow_content
                ui_state["loading"] = False
                return flow_content, chart_cache, ui_state

            elif active_tab == "tab-statistics-data":
                # Load statistics from DB and render table

                statistics_content = create_statistics_data_card(statistics)

                # Cache the result for next time
                chart_cache[cache_key] = statistics_content
                ui_state["loading"] = False
                return statistics_content, chart_cache, ui_state

            elif active_tab == "tab-sprint-tracker":
                # Generate Sprint Tracker content directly (no placeholder loading)

                # Get data_points_count from settings
                data_points_count = int(
                    settings.get("data_points_count", 12)
                )  # Ensure int

                # Render the actual content immediately
                sprint_tracker_content = _render_sprint_tracker_content(
                    data_points_count, show_points
                )

                # Cache the result for next time
                chart_cache[cache_key] = sprint_tracker_content
                ui_state["loading"] = False
                return sprint_tracker_content, chart_cache, ui_state

            elif active_tab == "tab-active-work-timeline":
                # Generate Active Work Timeline content directly
                # (no placeholder loading)

                # Get data_points_count from settings
                data_points_count = int(settings.get("data_points_count", 12))

                # Render the actual content immediately
                timeline_content = _render_active_work_timeline_content(
                    show_points, data_points_count
                )

                if use_cache_for_tab:
                    chart_cache[cache_key] = timeline_content
                ui_state["loading"] = False
                return timeline_content, chart_cache, ui_state

            # Default fallback (should not reach here)
            fallback_content = create_content_placeholder(
                type="chart", text="Select a tab to view data", height="400px"
            )
            ui_state["loading"] = False
            return fallback_content, chart_cache, ui_state

        except Exception as e:
            import traceback  # noqa: PLC0415

            logger.error(f"Error in render_tab_content callback: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            error_content = html.Div(
                [
                    html.H4("Error Loading Chart", className="text-danger"),
                    html.P(f"An error occurred: {str(e)}"),
                    html.P(
                        "Please check the application logs for details.",
                        className="text-muted",
                    ),
                ]
            )
            ui_state["loading"] = False
            return error_content, chart_cache, ui_state

    # Enhance the existing update_date_range callback
    # to immediately trigger chart updates
    @app.callback(
        Output("date-range-weeks", "data"),
        [
            Input({"type": "date-range-slider", "tab": "ALL"}, "value"),
        ],
    )
    def update_date_range(value):
        """
        Update the date range based on whichever slider was most recently changed.
        This uses a pattern-matching callback to handle sliders across different tabs.
        """
        # Get the ID of the component that triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Get the ID and value of the slider that was changed
        trigger = ctx.triggered[0]
        value = trigger["value"]

        # If no valid value, use default
        if value is None:
            return 24

        return value

    # Add callback for export project data button (JSON export)
    @app.callback(
        Output("export-project-data-download", "data"),
        Input("export-project-data-button", "n_clicks"),
        prevent_initial_call=True,
    )
    def export_project_data(n_clicks):
        """
        Export complete project data as JSON when the export button is clicked.

        Includes:
        - project_data: Statistics, issues, burndown calculations
        - metrics_snapshots: DORA/Flow metrics pre-calculated snapshots

        Args:
            n_clicks: Number of button clicks

        Returns:
            Dictionary with JSON download data
        """
        if not n_clicks:
            raise PreventUpdate

        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Load the complete unified project data
            project_data = load_unified_project_data()

            # Load metrics snapshots (DORA/Flow metrics)
            metrics_snapshots = load_snapshots()

            # Combine into single export package
            export_package = {
                "export_timestamp": current_time,
                "project_data": project_data,
                "metrics_snapshots": metrics_snapshots,
                "format_version": "1.0",
            }

            # Create filename with timestamp
            filename = f"project_data_{current_time}.json"

            # Convert to JSON string with pretty formatting
            json_content = json.dumps(export_package, indent=2, ensure_ascii=False)

            logger.info(
                f"Exported project data with {len(metrics_snapshots)} metric snapshots"
            )

            # Return JSON data for download
            return dict(
                content=json_content, filename=filename, type="application/json"
            )

        except Exception as e:
            logger.error(f"Error exporting project data: {e}")
            # Define current_time for the error case
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Return error JSON
            error_data = {"error": f"Failed to export project data: {str(e)}"}
            error_json = json.dumps(error_data, indent=2)
            return dict(
                content=error_json,
                filename=f"export_error_{current_time}.json",
                type="application/json",
            )

    # Chart toggle callbacks removed - burnup functionality deprecated


# Collapsible forecast info card callbacks
def toggle_items_forecast_info_collapse(n_clicks, is_open):
    """Toggle the collapse state of the items forecast information card."""
    if n_clicks is None:
        # Initial state - collapsed
        return False

    # Toggle the state when button is clicked
    return not is_open


@callback(
    Output("points-forecast-info-collapse", "is_open"),
    Input("points-forecast-info-collapse-button", "n_clicks"),
    State("points-forecast-info-collapse", "is_open"),
)
def toggle_points_forecast_info_collapse(n_clicks, is_open):
    """Toggle the collapse state of the points forecast information card."""
    if n_clicks is None:
        # Initial state - collapsed
        return False

    # Toggle the state when button is clicked
    return not is_open


@callback(
    Output("forecast-info-collapse", "is_open"),
    Input("forecast-info-collapse-button", "n_clicks"),
    State("forecast-info-collapse", "is_open"),
)
def toggle_forecast_info_collapse(n_clicks, is_open):
    """Toggle the collapse state of the forecast information card."""
    if n_clicks is None:
        # Initial state - collapsed
        return False

    # Toggle the state when button is clicked
    return not is_open
