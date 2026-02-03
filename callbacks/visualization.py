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
from datetime import datetime, timedelta

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
from data import (
    calculate_weekly_averages,
    compute_cumulative_values,
)
from data.schema import DEFAULT_SETTINGS
from data.iso_week_bucketing import get_week_label
from ui.loading_utils import (
    create_content_placeholder,
)
from visualization import (
    create_forecast_plot,
)
from visualization.weekly_charts import (
    create_weekly_items_chart,
    create_weekly_points_chart,
)
from visualization.charts import (
    apply_mobile_optimization,
)
from callbacks.visualization_helpers import (
    check_has_points_in_period,
    prepare_trend_data,
    create_burndown_tab_content,
)

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
        This prevents saving during initial load and avoids triggering callbacks prematurely.
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

    def _create_scope_tracking_tab_content(df, settings, show_points=True):
        """
        Create content for the scope tracking tab.

        Args:
            df: DataFrame with statistics data
            settings: Settings dictionary
            show_points: Whether points tracking is enabled

        Returns:
            html.Div: Scope tracking tab content
        """
        from data.scope_metrics import (
            calculate_scope_creep_rate,
            calculate_scope_stability_index,
            calculate_weekly_scope_growth,
        )
        from ui.scope_metrics import create_scope_metrics_dashboard

        # Get threshold and data_points_count from settings
        scope_creep_threshold = settings.get(
            "scope_creep_threshold", DEFAULT_SETTINGS["scope_creep_threshold"]
        )
        data_points_count = int(
            settings.get("data_points_count", len(df))
        )  # Ensure int

        if df.empty:
            return html.Div(
                [
                    html.Div(
                        className="alert alert-info",
                        children=[
                            html.I(className="fas fa-info-circle me-2"),
                            "No data available to display scope metrics.",
                        ],
                    )
                ]
            )

        # Ensure datetime format for date
        df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")

        # Calculate baseline values using the correct method (same as report)
        # Baseline = current remaining + total completed in filtered period
        # This gives us the initial backlog at the start of the data window

        # CRITICAL FIX: Do NOT re-filter here! Data is already filtered in the callback
        # to ensure consistency with Dashboard's Actionable Insights (T073 fix)
        # The df parameter is already filtered by data_points_count using week_label matching
        df_filtered = df

        # Get current remaining from project_data.json (not from settings)
        from typing import cast
        from data.persistence import load_project_data

        try:
            project_data = cast(dict, load_project_data())
            current_remaining_items = project_data.get("total_items", 0)
            current_remaining_points = project_data.get("total_points", 0)
        except Exception as e:
            logger.error(f"[SCOPE BASELINE APP] Failed to load project_data: {e}")
            current_remaining_items = 0
            current_remaining_points = 0

        # Calculate baseline as: current remaining + sum of completed in period
        total_completed_items = df_filtered["completed_items"].sum()
        total_completed_points = df_filtered["completed_points"].sum()

        baseline_items = int(current_remaining_items + total_completed_items)
        baseline_points = current_remaining_points + total_completed_points

        # Debug logging to verify baseline calculation
        logger.debug(
            f"[SCOPE BASELINE] data_points_count={data_points_count}, "
            f"filtered_rows={len(df_filtered)}, "
            f"current_remaining={current_remaining_items}/{current_remaining_points}, "
            f"completed_sum={total_completed_items}/{total_completed_points}, "
            f"calculated_baseline={baseline_items}/{baseline_points}"
        )

        # Ensure required columns exist with default values of 0 if they don't
        if "created_items" not in df.columns:
            df["created_items"] = 0
        if "created_points" not in df.columns:
            df["created_points"] = 0

        # Make sure data types are appropriate
        df["completed_items"] = pd.to_numeric(
            df["completed_items"], errors="coerce"
        ).fillna(0)
        df["completed_points"] = pd.to_numeric(
            df["completed_points"], errors="coerce"
        ).fillna(0)
        df["created_items"] = pd.to_numeric(
            df["created_items"], errors="coerce"
        ).fillna(0)
        df["created_points"] = pd.to_numeric(
            df["created_points"], errors="coerce"
        ).fillna(0)

        # Calculate scope creep rate with data filtering
        scope_creep_rate = calculate_scope_creep_rate(
            df, baseline_items, baseline_points, data_points_count=data_points_count
        )

        # Calculate weekly scope growth - ensure the function returns a DataFrame
        try:
            weekly_growth_data = calculate_weekly_scope_growth(
                df, data_points_count=data_points_count
            )
            # Verify the result is a DataFrame
            if not isinstance(weekly_growth_data, pd.DataFrame):
                logger.warning(
                    f"weekly_growth_data is not a DataFrame: {type(weekly_growth_data)}"
                )
                weekly_growth_data = pd.DataFrame(
                    columns=[
                        "week_label",
                        "items_growth",
                        "points_growth",
                        "start_date",
                    ]
                )
        except Exception as e:
            logger.error(f"Error calculating weekly scope growth: {str(e)}")
            weekly_growth_data = pd.DataFrame(
                columns=["week_label", "items_growth", "points_growth", "start_date"]
            )

        # Calculate scope stability index with data filtering
        stability_index = calculate_scope_stability_index(
            df, baseline_items, baseline_points, data_points_count=data_points_count
        )

        # Create the scope metrics dashboard
        # Pass the correctly calculated baseline values
        return create_scope_metrics_dashboard(
            scope_creep_rate,
            weekly_growth_data,
            stability_index,
            scope_creep_threshold,
            total_items_scope=baseline_items,
            total_points_scope=baseline_points,
            show_points=show_points,
        )

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
        Render the appropriate content based on the selected tab with lazy loading and caching.
        Only generates charts for the active tab to improve performance.
        Target: <500ms chart rendering, immediate skeleton loading, <100ms cached responses.
        """
        # TECH LEAD FIX: The previous "CRITICAL FIX" code was CAUSING the bug, not fixing it!
        #
        # The bug: That code tried to work around stale active_tab by using ui_state["last_tab"]
        # when the trigger wasn't from tab change. But this is backwards logic!
        #
        # What actually happens:
        # 1. User clicks scope tab -> active_tab="tab-scope-tracking", last_tab="tab-scope-tracking"
        # 2. User clicks burndown tab -> Dash correctly passes active_tab="tab-burndown"
        # 3. BUT if any other input changes (settings, statistics, etc), the old code would
        #    IGNORE the correct active_tab and use the stale last_tab instead!
        # 4. This caused scope content to render on every tab after visiting it once
        #
        # THE FIX: Trust Dash! The active_tab parameter is ALWAYS correct.
        # Dash automatically provides the current tab state, even when other inputs trigger the callback.
        # We should NEVER override it with stored state.

        ctx = callback_context
        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else "initial"
        logger.debug(
            f"[CTO DEBUG] render_tab_content triggered by: {trigger_info}, active_tab='{active_tab}', cache_size={len(chart_cache) if chart_cache else 0}"
        )

        # CRITICAL DEBUG: Log statistics data to diagnose query switching issue
        if statistics:
            logger.info(
                f"[VISUALIZATION] render_tab_content received {len(statistics)} statistics"
            )
            logger.info(
                f"[VISUALIZATION] First stat: date={statistics[0].get('date')}, items={statistics[0].get('remaining_items')}, points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                f"[VISUALIZATION] Last stat: date={statistics[-1].get('date')}, items={statistics[-1].get('remaining_items')}, points={statistics[-1].get('remaining_total_points')}"
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
            f"Rendering charts for viewport: {viewport_size} (mobile={is_mobile}, tablet={is_tablet})"
        )

        # Convert checklist value to boolean (points-toggle returns list, not boolean)
        show_points = bool(
            show_points and (show_points is True or "show" in show_points)
        )

        # CTO FIX: Clear old cache entries to prevent memory bloat (keep last 5)
        # BUT: If we're switching tabs (trigger is from chart-tabs), clear ALL cache
        # to prevent any possibility of cross-tab contamination
        # ALSO: Clear ALL cache when budget changes to ensure fresh render
        # ALSO: Clear ALL cache when statistics change (table edits) to ensure immediate reactivity
        trigger_info = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        if "chart-tabs" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Tab switch detected - CLEARING ALL CACHE to prevent contamination"
            )
            chart_cache = {}
        elif "budget-settings-store" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Budget change detected - CLEARING ALL CACHE to refresh budget cards"
            )
            chart_cache = {}
        elif "metrics-refresh-trigger" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Import/refresh detected - CLEARING ALL CACHE to reload data"
            )
            chart_cache = {}
        elif "current-statistics.modified_timestamp" in trigger_info:
            logger.debug(
                "[CTO DEBUG] Statistics modified (table edit) - CLEARING ALL CACHE to show changes immediately"
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
        logger.debug(f"[CTO DEBUG] Cache key generated: {cache_key}")

        # Check if we have cached content for this exact state
        if cache_key in chart_cache:
            # Return cached content immediately for <100ms response time
            logger.debug(
                f"[CTO DEBUG] Returning CACHED content for active_tab='{active_tab}', cache_key={cache_key}"
            )
            ui_state["loading"] = False
            ui_state["last_tab"] = active_tab
            return chart_cache[cache_key], chart_cache, ui_state

        # Set loading state for new tab content generation
        ui_state["loading"] = True
        ui_state["last_tab"] = active_tab

        try:
            # Get values from settings with safe defaults
            pert_factor = settings.get("pert_factor", 1.2)
            deadline = (
                settings.get("deadline") or None
            )  # CRITICAL: Use None for empty dates (not "")
            data_points_count = int(
                settings.get("data_points_count", 12)
            )  # Ensure int, default 12

            # Get remaining items/points from settings (loaded from project_data.json)
            total_items = settings.get("total_items", 0)
            total_points = settings.get("total_points", 0)

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            # LAZY LOADING: Only generate charts for the active tab
            show_milestone = settings.get("show_milestone", False)
            milestone = settings.get("milestone", None) if show_milestone else None

            if active_tab == "tab-dashboard":
                # Generate modern compact dashboard content
                logger.debug(
                    f"[CTO DEBUG] Creating NEW modern dashboard content, cache_key={cache_key}"
                )

                # CRITICAL: Filter data ONCE before all calculations to ensure consistency
                # This ensures all dashboard sections respect the data_points_count slider
                # EXCEPT "Recent Completions" which always shows last 4 weeks
                df_unfiltered = (
                    df.copy()
                )  # Keep unfiltered copy for Recent Completions section

                if not df.empty:
                    # CRITICAL FIX: Apply data_points_count filter by WEEK LABELS, not date ranges
                    # This ensures Dashboard and DORA/Flow metrics use the same time periods
                    if data_points_count is not None and data_points_count > 0:
                        logger.info(
                            f"Filtering dashboard data by {data_points_count} weeks"
                        )

                        # Generate the same week labels that DORA/Flow metrics use
                        from data.time_period_calculator import (
                            get_iso_week,
                            format_year_week,
                        )

                        weeks = []
                        # CRITICAL: Start from last statistics date, not today
                        # Statistics are weekly (Mondays), so starting from "now" may include
                        # incomplete current week with no data
                        if not df.empty and "date" in df.columns:
                            df["date"] = pd.to_datetime(
                                df["date"], format="mixed", errors="coerce"
                            )
                            current_date = df["date"].max()
                        else:
                            current_date = datetime.now()

                        for i in range(data_points_count):
                            year, week = get_iso_week(current_date)
                            week_label = format_year_week(year, week)
                            weeks.append(week_label)
                            current_date = current_date - timedelta(days=7)

                        week_labels = set(
                            reversed(weeks)
                        )  # Convert to set for fast lookup

                        # Filter by week_label if available, otherwise fall back to date range
                        if "week_label" in df.columns:
                            df = df[df["week_label"].isin(week_labels)]
                            # CRITICAL: Sort after filtering to ensure .iloc[-1] gets the chronologically last date
                            # This matches report_generator.py logic and ensures forecast dates align
                            df = df.sort_values("date", ascending=True)
                            logger.info(
                                f"Filtered to {len(df)} rows using week_label matching"
                            )
                        else:
                            # Fallback: date range filtering (old behavior for backward compatibility)
                            df["date"] = pd.to_datetime(
                                df["date"], format="mixed", errors="coerce"
                            )
                            df = df.dropna(subset=["date"]).sort_values(
                                "date", ascending=True
                            )
                            latest_date = df["date"].max()
                            cutoff_date = latest_date - timedelta(
                                weeks=data_points_count
                            )
                            df = df[df["date"] >= cutoff_date]
                            logger.warning(
                                "No week_label column - using date range filtering (less accurate)"
                            )

                    df = compute_cumulative_values(df, total_items, total_points)
                    df_unfiltered = compute_cumulative_values(
                        df_unfiltered, total_items, total_points
                    )

                # Create forecast plot with already-filtered data
                # Pass data_points_count=None since data is already filtered
                _, pert_data = create_forecast_plot(
                    df=df,
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,
                    data_points_count=None,  # Already filtered above
                    show_points=show_points,
                )

                # Calculate weekly averages for the dashboard
                (
                    avg_weekly_items,
                    avg_weekly_points,
                    med_weekly_items,
                    med_weekly_points,
                ) = calculate_weekly_averages(
                    statistics, data_points_count=data_points_count
                )

                # CRITICAL: Calculate velocity for health using same method as report
                # calculate_velocity_from_dataframe() counts actual weeks with data (5.06)
                # calculate_weekly_averages() uses Flow metrics snapshots (4.94)
                # Report uses calculate_velocity_from_dataframe(), so app must match
                from data.processing import calculate_velocity_from_dataframe

                velocity_for_health_items = calculate_velocity_from_dataframe(
                    df, "completed_items"
                )
                velocity_for_health_points = calculate_velocity_from_dataframe(
                    df, "completed_points"
                )

                # Calculate days to deadline
                try:
                    deadline_date = pd.to_datetime(deadline) if deadline else pd.NaT
                    if pd.isna(deadline_date):
                        days_to_deadline = 0
                    else:
                        # CRITICAL: Use last statistics date (not datetime.now()) for consistency with report
                        # This ensures health score remains stable between data updates
                        # and matches report calculation exactly
                        last_date = (
                            df["date"].iloc[-1].date()
                            if not df.empty and "date" in df.columns
                            else datetime.now().date()
                        )
                        days_to_deadline = max(
                            0, (deadline_date.date() - last_date).days
                        )
                except Exception:
                    days_to_deadline = 0

                # Calculate budget data for dashboard
                budget_data = None
                profile_id = ""
                query_id = ""
                current_week_label = ""
                try:
                    from data.persistence.factory import get_backend

                    backend = get_backend()
                    profile_id = backend.get_app_state("active_profile_id") or ""
                    query_id = backend.get_app_state("active_query_id") or ""
                    current_week_label = get_week_label(datetime.now())

                    logger.info(
                        f"[BUDGET DEBUG] profile_id={profile_id}, query_id={query_id}, "
                        f"week={current_week_label}"
                    )

                    if profile_id and query_id:
                        # Check if budget is configured
                        from data.budget_calculator import (
                            _get_current_budget,
                            get_budget_baseline_vs_actual,
                            calculate_cost_breakdown_by_type,
                            calculate_weekly_cost_breakdowns,
                        )

                        budget_config = _get_current_budget(profile_id, query_id)
                        logger.info(f"[BUDGET DEBUG] budget_config={budget_config}")

                        if budget_config:
                            # Calculate PERT forecast weeks for comparison
                            pert_forecast_weeks = None
                            last_date = None
                            if pert_data and pert_data.get("pert_time_items"):
                                pert_time_items = pert_data["pert_time_items"]
                                last_date = pert_data.get(
                                    "last_date"
                                )  # Get last statistics date
                                if pert_time_items and pert_time_items > 0:
                                    pert_forecast_weeks = (
                                        pert_time_items / 7.0
                                    )  # Convert days to weeks

                            # Get comprehensive baseline vs actual comparison (single call - DRY)
                            baseline_comparison = get_budget_baseline_vs_actual(
                                profile_id,
                                query_id,
                                current_week_label,
                                data_points_count,
                                pert_forecast_weeks,
                            )
                            logger.info(
                                f"[BUDGET DEBUG] Baseline comparison calculated: "
                                f"variance={baseline_comparison['variance']}"
                            )

                            # Extract metrics from comprehensive data (no redundant calculations)
                            consumed_eur = baseline_comparison["actual"]["consumed_eur"]
                            budget_total = baseline_comparison["baseline"][
                                "budget_total_eur"
                            ]
                            consumed_pct = baseline_comparison["actual"]["consumed_pct"]
                            burn_rate = baseline_comparison["actual"]["burn_rate"]
                            runway_weeks = baseline_comparison["actual"]["runway_weeks"]
                            cost_per_item = baseline_comparison["actual"][
                                "cost_per_item"
                            ]
                            cost_per_point = baseline_comparison["actual"][
                                "cost_per_point"
                            ]

                            # Get cost breakdown (separate function)
                            cost_breakdown = calculate_cost_breakdown_by_type(
                                profile_id, query_id, current_week_label
                            )
                            logger.info(f"[BUDGET DEBUG] breakdown={cost_breakdown}")

                            # Calculate weekly cost breakdowns for sparkline trends
                            weekly_breakdowns, weekly_breakdown_labels = (
                                calculate_weekly_cost_breakdowns(
                                    profile_id,
                                    query_id,
                                    current_week_label,
                                    data_points_count,
                                )
                            )
                            logger.info(
                                f"[BUDGET DEBUG] weekly_breakdowns count={len(weekly_breakdowns)}, "
                                f"labels={weekly_breakdown_labels}"
                            )

                            # Get weekly burn rates for sparkline
                            # weekly_breakdowns is a list of dicts with breakdowns by type per week
                            # Sum up total costs for each week
                            weekly_burn_rates = []
                            for breakdown in weekly_breakdowns:
                                week_total = sum(
                                    flow_type_data.get("cost", 0)
                                    for flow_type_data in breakdown.values()
                                )
                                weekly_burn_rates.append(week_total)
                            weekly_labels = weekly_breakdown_labels

                            budget_data = {
                                "configured": True,
                                "currency_symbol": budget_config.get(
                                    "currency_symbol", "€"
                                ),
                                "consumed_pct": consumed_pct,
                                "consumed_eur": consumed_eur,
                                "budget_total": budget_total,
                                "burn_rate": burn_rate,
                                "runway_weeks": runway_weeks,
                                "breakdown": cost_breakdown,
                                "baseline_comparison": baseline_comparison,  # NEW: comprehensive data
                                "pert_forecast_weeks": pert_forecast_weeks,  # For timeline card
                                "last_date": last_date,  # Last statistics date for forecast alignment
                                # Weekly breakdowns for sparkline trend charts
                                "weekly_breakdowns": weekly_breakdowns,
                                "weekly_breakdown_labels": weekly_breakdown_labels,
                                # Additional fields for budget cards
                                "cost_per_item": cost_per_item,
                                "cost_per_point": cost_per_point,
                                "weekly_burn_rates": weekly_burn_rates,
                                "weekly_labels": weekly_labels,
                                "burn_trend_pct": 0,  # TODO: Calculate trend
                                "pert_cost_avg_item": None,  # TODO: Add PERT cost calculation
                                "pert_cost_avg_point": None,
                                "forecast_total": budget_total,  # TODO: Add forecast calculation
                                "forecast_low": budget_total * 0.9,
                                "forecast_high": budget_total * 1.1,
                            }
                            # Format runway for logging (handle inf and negative)
                            import math

                            if math.isinf(runway_weeks):
                                runway_str = "inf"
                            else:
                                runway_str = f"{runway_weeks:.1f}"

                            logger.info(
                                f"Budget data calculated: {consumed_pct:.1f}% consumed, "
                                f"runway={runway_str} weeks, cost_per_item={cost_per_item:.2f}"
                            )
                        else:
                            logger.debug(
                                f"No budget configured for profile {profile_id}"
                            )
                except Exception as e:
                    logger.error(f"Failed to calculate budget data: {e}", exc_info=True)
                    budget_data = None

                # Calculate extended metrics for comprehensive health formula (v3.0)
                # These enhance health score accuracy when available
                extended_metrics = {}

                if profile_id and query_id:
                    # DORA Metrics - Load from cache (same as report)
                    try:
                        from data.dora_metrics_calculator import (
                            load_dora_metrics_from_cache,
                        )

                        cached_metrics = load_dora_metrics_from_cache(
                            n_weeks=data_points_count or 12
                        )

                        if cached_metrics:
                            # Extract values matching app structure (same as report logic)
                            deploy_data = cached_metrics.get("deployment_frequency", {})
                            deployment_freq = deploy_data.get(
                                "release_value", 0
                            )  # Primary: unique releases

                            lead_time_data = cached_metrics.get(
                                "lead_time_for_changes", {}
                            )
                            lead_time_days = lead_time_data.get(
                                "value"
                            )  # Already in days

                            cfr_data = cached_metrics.get("change_failure_rate", {})
                            change_failure_rate = cfr_data.get("value", 0)  # Percentage

                            mttr_data = cached_metrics.get("mean_time_to_recovery", {})
                            mttr_hours = mttr_data.get("value")  # Already in hours

                            # Check if there's any meaningful data (same logic as report)
                            has_meaningful_data = (
                                (deployment_freq > 0)
                                or (lead_time_days is not None and lead_time_days > 0)
                                or (mttr_hours is not None and mttr_hours > 0)
                            )

                            if has_meaningful_data:
                                extended_metrics["dora"] = {
                                    "has_data": True,
                                    "deployment_frequency": deployment_freq,
                                    "lead_time": lead_time_days or 0,
                                    "change_failure_rate": change_failure_rate,
                                    "mttr_hours": mttr_hours or 0,
                                }
                                logger.info(
                                    f"[HEALTH v3.0] DORA metrics loaded: "
                                    f"DF={deployment_freq:.2f}, LT={lead_time_days:.1f}d, "
                                    f"CFR={change_failure_rate:.1f}%, MTTR={mttr_hours:.1f}h"
                                )
                    except Exception as e:
                        logger.warning(f"[HEALTH v3.0] DORA metrics unavailable: {e}")

                    # Flow Metrics - Load from snapshots (same as report)
                    try:
                        from data.metrics_snapshots import (
                            get_metric_weekly_values,
                            get_metric_snapshot,
                            get_available_weeks,
                        )
                        from data.time_period_calculator import (
                            get_iso_week,
                            format_year_week,
                        )

                        # Generate week labels (same as report)
                        weeks = []
                        current_date = datetime.now()
                        for i in range(data_points_count or 12):
                            year, week = get_iso_week(current_date)
                            week_label = format_year_week(year, week)
                            weeks.append(week_label)
                            current_date = current_date - timedelta(days=7)

                        week_labels = list(reversed(weeks))  # Oldest to newest
                        current_week_label = week_labels[-1] if week_labels else ""

                        # Check if any data exists
                        available_weeks = get_available_weeks()
                        has_any_data = any(
                            week in available_weeks for week in week_labels
                        )

                        if has_any_data:
                            # Load weekly values from snapshots
                            flow_time_values = get_metric_weekly_values(
                                week_labels, "flow_time", "median_days"
                            )
                            flow_efficiency_values = get_metric_weekly_values(
                                week_labels, "flow_efficiency", "overall_pct"
                            )
                            velocity_values = get_metric_weekly_values(
                                week_labels, "flow_velocity", "completed_count"
                            )

                            # AGGREGATE metrics (same as report)
                            avg_velocity = (
                                sum(velocity_values) / len(velocity_values)
                                if velocity_values
                                else 0
                            )

                            # Flow Time: Median of weekly medians (exclude zeros)
                            non_zero_flow_times = [v for v in flow_time_values if v > 0]
                            if non_zero_flow_times:
                                sorted_times = sorted(non_zero_flow_times)
                                mid = len(sorted_times) // 2
                                median_flow_time = (
                                    sorted_times[mid]
                                    if len(sorted_times) % 2 == 1
                                    else (sorted_times[mid - 1] + sorted_times[mid]) / 2
                                )
                            else:
                                median_flow_time = 0

                            # Flow Efficiency: Average efficiency (exclude zeros)
                            non_zero_efficiency = [
                                v for v in flow_efficiency_values if v > 0
                            ]
                            avg_efficiency = (
                                sum(non_zero_efficiency) / len(non_zero_efficiency)
                                if non_zero_efficiency
                                else 0
                            )

                            # Flow Load (WIP): Current week snapshot
                            flow_load_snapshot = get_metric_snapshot(
                                current_week_label, "flow_load"
                            )
                            wip = (
                                flow_load_snapshot.get("wip_count", 0)
                                if flow_load_snapshot
                                else 0
                            )

                            # Work Distribution: Sum across all weeks (for Sustainability dimension)
                            total_feature = 0
                            total_defect = 0
                            total_tech_debt = 0
                            total_risk = 0
                            total_completed = 0

                            for week in week_labels:
                                week_snapshot = get_metric_snapshot(
                                    week, "flow_velocity"
                                )
                                if week_snapshot:
                                    week_dist = week_snapshot.get("distribution", {})
                                    total_feature += week_dist.get("feature", 0)
                                    total_defect += week_dist.get("defect", 0)
                                    total_tech_debt += week_dist.get("tech_debt", 0)
                                    total_risk += week_dist.get("risk", 0)
                                    total_completed += week_snapshot.get(
                                        "completed_count", 0
                                    )

                            if avg_velocity > 0:  # Has meaningful data
                                extended_metrics["flow"] = {
                                    "has_data": True,
                                    "velocity": avg_velocity,
                                    "flow_time": median_flow_time,
                                    "efficiency": avg_efficiency,
                                    "wip": wip,
                                    "work_distribution": {
                                        "feature": total_feature,
                                        "defect": total_defect,
                                        "tech_debt": total_tech_debt,
                                        "risk": total_risk,
                                        "total": total_completed,
                                    },
                                }
                                logger.info(
                                    f"[HEALTH v3.0] Flow metrics loaded: "
                                    f"Velocity={avg_velocity:.1f}, Efficiency={avg_efficiency:.1f}%, "
                                    f"Flow Time={median_flow_time:.1f}d"
                                )
                    except Exception as e:
                        logger.warning(f"[HEALTH v3.0] Flow metrics unavailable: {e}")

                    # Bug Metrics (~10-20ms from cache)
                    try:
                        from data.bug_processing import (
                            calculate_bug_metrics_summary,
                            filter_bug_issues,
                        )
                        from data.persistence.factory import get_backend
                        from data.query_manager import get_active_query_id

                        # Load issues from backend for bug metrics
                        backend = get_backend()
                        query_id_active = get_active_query_id()
                        bug_data = None

                        if query_id_active and profile_id:
                            issues = backend.get_issues(profile_id, query_id_active)

                            # Filter to get ONLY bugs (same as report)
                            from data.persistence import load_app_settings

                            settings = load_app_settings()
                            bug_types = settings.get("bug_types", {})

                            # Calculate date range for timeline filtering
                            date_to = datetime.now()
                            date_from = date_to - timedelta(
                                weeks=data_points_count or 12
                            )

                            # Filter bugs WITHOUT date filter for current state metrics
                            all_bug_issues = filter_bug_issues(
                                issues,
                                bug_type_mappings=bug_types,
                                date_from=None,
                                date_to=None,
                            )

                            # Filter bugs WITH date filter for historical metrics
                            timeline_filtered_bugs = filter_bug_issues(
                                issues,
                                bug_type_mappings=bug_types,
                                date_from=date_from,
                                date_to=date_to,
                            )

                            # Get weekly stats - calculate from project data
                            from data.persistence import load_unified_project_data

                            project_data = load_unified_project_data()
                            weekly_stats = project_data.get("statistics", [])

                            bug_data = calculate_bug_metrics_summary(
                                all_bug_issues=all_bug_issues,
                                timeline_filtered_bugs=timeline_filtered_bugs,
                                weekly_stats=weekly_stats,
                            )

                            if bug_data and bug_data.get("total_bugs", 0) > 0:
                                # Convert resolution rate from decimal (0-1) to percentage (0-100) like report does
                                resolution_rate_pct = (
                                    bug_data.get("resolution_rate", 0) * 100
                                )

                                logger.info(
                                    f"[BUG METRICS] Passing to health: resolution_rate={resolution_rate_pct:.2f}%, "
                                    f"total_bugs={bug_data.get('total_bugs', 0)}, "
                                    f"avg_age_days={bug_data.get('avg_age_days', 0):.1f}d, "
                                    f"all_bug_issues_count={len(all_bug_issues)}, "
                                    f"timeline_bugs_count={len(timeline_filtered_bugs)}"
                                )
                                extended_metrics["bug_analysis"] = {
                                    "has_data": True,
                                    "resolution_rate": resolution_rate_pct,  # Already converted to percentage
                                    "avg_resolution_time_days": bug_data.get(
                                        "avg_resolution_time_days", 0
                                    ),
                                    "avg_age_days": bug_data.get(
                                        "avg_age_days", 0
                                    ),  # Add avg_age_days for Bug Health calculation
                                    "capacity_consumed_by_bugs": bug_data.get(
                                        "capacity_consumed_by_bugs", 0
                                    )
                                    / 100
                                    if bug_data.get("capacity_consumed_by_bugs")
                                    else 0,  # Convert % to decimal
                                    "open_bugs": bug_data.get("open_bugs", 0),
                                }
                                logger.info(
                                    f"[HEALTH v3.0] Bug metrics available: "
                                    f"Resolution={extended_metrics['bug_analysis']['resolution_rate']:.1f}%, "
                                    f"Capacity={extended_metrics['bug_analysis']['capacity_consumed_by_bugs'] * 100:.1f}%"
                                )
                    except Exception as e:
                        logger.warning(f"[HEALTH v3.0] Bug metrics unavailable: {e}")

                    # Log extended metrics summary with ACTUAL VALUES for health debugging
                    logger.info(
                        f"[HEALTH v3.0] Extended metrics summary: "
                        f"DORA={'✓' if 'dora' in extended_metrics else '✗'}, "
                        f"Flow={'✓' if 'flow' in extended_metrics else '✗'}, "
                        f"Bug={'✓' if 'bug_analysis' in extended_metrics else '✗'}, "
                        f"Budget={'✓' if budget_data else '✗'}"
                    )

                # Import and use comprehensive dashboard
                from ui.dashboard import create_comprehensive_dashboard

                # Create the comprehensive dashboard layout
                dashboard_content = create_comprehensive_dashboard(
                    statistics_df=df,
                    statistics_df_unfiltered=df_unfiltered,  # For Recent Completions (always last 4 weeks)
                    pert_time_items=pert_data["pert_time_items"],
                    pert_time_points=pert_data["pert_time_points"],
                    avg_weekly_items=velocity_for_health_items,  # CRITICAL: Use report's velocity calculation for health (not Flow metrics)
                    avg_weekly_points=velocity_for_health_points,  # CRITICAL: Use report's velocity calculation for health (not Flow metrics)
                    med_weekly_items=med_weekly_items,
                    med_weekly_points=med_weekly_points,
                    days_to_deadline=days_to_deadline,
                    total_items=total_items,
                    total_points=total_points,
                    data_points_count=data_points_count,  # Pass for metric snapshot lookup
                    deadline_str=deadline,
                    show_points=show_points,
                    additional_context={
                        "profile_id": profile_id,
                        "query_id": query_id,
                        "current_week_label": current_week_label,
                        "budget_data": budget_data,
                        "extended_metrics": extended_metrics,  # v3.0 comprehensive health data
                    },
                )

                # Cache the result for next time
                chart_cache[cache_key] = dashboard_content
                ui_state["loading"] = False
                return dashboard_content, chart_cache, ui_state

            elif active_tab == "tab-burndown":
                # Generate all required data for burndown tab
                # CRITICAL: Pass data_points_count to ensure trend indicators use filtered data
                items_trend, points_trend = prepare_trend_data(
                    statistics, pert_factor, data_points_count
                )

                # Check if points data exists in the filtered time period
                # This respects the Data Points slider to only check the selected weeks
                has_points_data = False
                if show_points:
                    has_points_data = check_has_points_in_period(
                        statistics, data_points_count
                    )

                # For burndown chart, hide points traces if no data (like when disabled)
                effective_show_points = show_points and has_points_data

                # Generate burndown chart only when needed
                # NOTE: Don't pre-compute cumulative values - let create_forecast_plot handle it
                # to avoid redundant DataFrame operations that slow down rendering
                burndown_fig, _ = create_forecast_plot(
                    df=df,
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,
                    data_points_count=data_points_count,
                    show_points=effective_show_points,  # Use effective flag
                )

                # Calculate required velocity for chart reference lines
                required_velocity_items = None
                required_velocity_points = None
                if deadline:
                    from data.velocity_projections import calculate_required_velocity
                    from data.persistence import load_unified_project_data

                    try:
                        # Parse deadline
                        deadline_date = datetime.strptime(deadline, "%Y-%m-%d")

                        # Get current remaining work
                        project_data = load_unified_project_data()
                        project_scope = project_data.get("project_scope", {})
                        remaining_items = project_scope.get("remaining_items", 0)
                        remaining_points = project_scope.get(
                            "remaining_total_points", 0
                        )

                        # Calculate required velocities
                        if remaining_items > 0:
                            required_velocity_items = calculate_required_velocity(
                                remaining_items, deadline_date, time_unit="week"
                            )
                        if remaining_points and remaining_points > 0:
                            required_velocity_points = calculate_required_velocity(
                                remaining_points, deadline_date, time_unit="week"
                            )
                    except Exception as e:
                        logger.warning(f"Could not calculate required velocity: {e}")

                # Generate items chart for consolidated view
                items_fig = create_weekly_items_chart(
                    statistics,
                    pert_factor,
                    data_points_count=data_points_count,
                    required_velocity=required_velocity_items,
                )
                # Apply mobile optimization to items chart
                items_fig, _ = apply_mobile_optimization(
                    items_fig,
                    is_mobile=is_mobile,
                    is_tablet=is_tablet,
                    title="Weekly Items" if not is_mobile else None,
                )

                # Generate points chart for consolidated view (only if enabled AND has data)
                points_fig = None
                if show_points and has_points_data:
                    points_fig = create_weekly_points_chart(
                        statistics,
                        pert_factor,
                        data_points_count=data_points_count,
                        required_velocity=required_velocity_points,
                    )
                    # Apply mobile optimization to points chart
                    points_fig, _ = apply_mobile_optimization(
                        points_fig,
                        is_mobile=is_mobile,
                        is_tablet=is_tablet,
                        title="Weekly Points" if not is_mobile else None,
                    )

                # Create burndown tab content with all required data
                burndown_tab_content = create_burndown_tab_content(
                    df,
                    items_trend,
                    points_trend,
                    burndown_fig,
                    items_fig,
                    points_fig,
                    settings,
                    show_points,  # Original flag
                    has_points_data,  # Whether data exists
                )
                # Cache the result for next time
                logger.debug(
                    f"[CTO DEBUG] Created NEW burndown content, caching with key={cache_key}"
                )
                chart_cache[cache_key] = burndown_tab_content
                ui_state["loading"] = False
                return burndown_tab_content, chart_cache, ui_state

            elif active_tab == "tab-scope-tracking":
                # Generate scope tracking content only when needed
                logger.debug(
                    f"[CTO DEBUG] Creating NEW scope tracking content, cache_key={cache_key}"
                )

                # CRITICAL FIX: Apply SAME filtering as Dashboard to ensure consistency
                # The Scope Analysis tab must use the same filtered time window as Dashboard's Actionable Insights
                # Otherwise they show different numbers for the same metrics (T073 bug)
                df_for_scope = df.copy()
                if (
                    data_points_count is not None
                    and data_points_count > 0
                    and not df_for_scope.empty
                ):
                    logger.info(
                        f"[SCOPE FILTER] Filtering scope data by {data_points_count} weeks using week_label matching"
                    )

                    # Generate the same week labels that Dashboard uses
                    from data.time_period_calculator import (
                        get_iso_week,
                        format_year_week,
                    )

                    weeks = []
                    # Start from last statistics date, not today
                    if "date" in df_for_scope.columns:
                        df_for_scope["date"] = pd.to_datetime(
                            df_for_scope["date"], format="mixed", errors="coerce"
                        )
                        current_date = df_for_scope["date"].max()
                    else:
                        current_date = datetime.now()

                    for i in range(data_points_count):
                        year, week = get_iso_week(current_date)
                        week_label = format_year_week(year, week)
                        weeks.append(week_label)
                        current_date = current_date - timedelta(days=7)

                    week_labels = set(reversed(weeks))  # Convert to set for fast lookup

                    # Filter by week_label if available, otherwise fall back to date range
                    if "week_label" in df_for_scope.columns:
                        df_for_scope = df_for_scope[
                            df_for_scope["week_label"].isin(week_labels)
                        ]
                        df_for_scope = df_for_scope.sort_values("date", ascending=True)
                        logger.info(
                            f"[SCOPE FILTER] Filtered to {len(df_for_scope)} rows using week_label matching"
                        )
                    else:
                        # Fallback: date range filtering
                        df_for_scope = df_for_scope.dropna(subset=["date"]).sort_values(
                            "date", ascending=True
                        )
                        latest_date = df_for_scope["date"].max()
                        cutoff_date = latest_date - timedelta(weeks=data_points_count)
                        df_for_scope = df_for_scope[df_for_scope["date"] >= cutoff_date]
                        logger.warning(
                            "[SCOPE FILTER] No week_label column - using date range filtering"
                        )

                # Check if points data exists in the filtered time period (respects Data Points slider)
                has_points_data = False
                if show_points:
                    has_points_data = check_has_points_in_period(
                        statistics, data_points_count
                    )

                # Only show points in charts if tracking is enabled AND data exists in filtered period
                effective_show_points = show_points and has_points_data

                scope_tab_content = _create_scope_tracking_tab_content(
                    df_for_scope, settings, effective_show_points
                )
                # Cache the result for next time
                chart_cache[cache_key] = scope_tab_content
                ui_state["loading"] = False
                return scope_tab_content, chart_cache, ui_state

            elif active_tab == "tab-bug-analysis":
                # Generate bug analysis tab content directly (no placeholder loading)
                # Import the actual rendering function from bug_analysis callback
                from callbacks.bug_analysis import _render_bug_analysis_content

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
                from ui.dora_metrics_dashboard import create_dora_dashboard

                dora_content = create_dora_dashboard()

                # Cache the result for next time
                chart_cache[cache_key] = dora_content
                ui_state["loading"] = False
                return dora_content, chart_cache, ui_state

            elif active_tab == "tab-flow-metrics":
                # Generate Flow metrics dashboard
                # Callback will populate with metrics (prevent_initial_call=False)
                from ui.flow_metrics_dashboard import create_flow_dashboard

                flow_content = create_flow_dashboard()

                # Cache the result for next time
                chart_cache[cache_key] = flow_content
                ui_state["loading"] = False
                return flow_content, chart_cache, ui_state

            elif active_tab == "tab-statistics-data":
                # Load statistics from DB and render table
                from ui.cards import create_statistics_data_card

                statistics_content = create_statistics_data_card(statistics)

                # Cache the result for next time
                chart_cache[cache_key] = statistics_content
                ui_state["loading"] = False
                return statistics_content, chart_cache, ui_state

            elif active_tab == "tab-sprint-tracker":
                # Generate Sprint Tracker content directly (no placeholder loading)
                from callbacks.sprint_tracker import _render_sprint_tracker_content

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

            # Default fallback (should not reach here)
            fallback_content = create_content_placeholder(
                type="chart", text="Select a tab to view data", height="400px"
            )
            ui_state["loading"] = False
            return fallback_content, chart_cache, ui_state

        except Exception as e:
            import traceback

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

    # Enhance the existing update_date_range callback to immediately trigger chart updates
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
            from data.persistence import load_unified_project_data
            from data.metrics_snapshots import load_snapshots

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
