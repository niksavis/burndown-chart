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
import time
from datetime import datetime

# Third-party library imports
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import (
    Input,
    Output,
    State,
    callback,
    callback_context,
    dcc,
    html,
)
from dash.exceptions import PreventUpdate

# Application imports
from configuration import CHART_HELP_TEXTS
from data import (
    calculate_performance_trend,
    calculate_weekly_averages,
    compute_cumulative_values,
    generate_weekly_forecast,
)
from data.schema import DEFAULT_SETTINGS
from ui import (
    create_compact_trend_indicator,
    create_pert_info_table,
)
from ui.loading_utils import (
    create_content_placeholder,
    create_skeleton_loader,
    create_spinner,
)
from ui.tooltip_utils import create_info_tooltip
from visualization import (
    create_forecast_plot,
    create_weekly_items_chart,
    create_weekly_points_chart,
)
from visualization.charts import create_chart_with_loading

# Setup logging
logger = logging.getLogger("burndown_chart")

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def create_forecast_pill(forecast_type, value, color):
    """
    Create a forecast pill component with consistent styling.

    Args:
        forecast_type (str): Type of forecast (e.g., 'Most likely', 'Optimistic', 'Pessimistic')
        value (float): Forecast value
        color (str): Color hex code for styling the pill

    Returns:
        html.Div: Forecast pill component
    """
    return html.Div(
        [
            html.I(
                className="fas fa-chart-line me-1",
                style={"color": color},
            ),
            html.Small(
                [
                    f"{forecast_type}: ",
                    html.Strong(
                        f"{value:.2f}",
                        style={"color": color},
                    ),
                ],
            ),
        ],
        className="forecast-pill",
        style={
            "borderLeft": f"3px solid {color}",
            "paddingLeft": "0.5rem",
            "marginRight": "0.75rem",
        },
    )


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
        [State("current-settings", "data"), State("current-statistics", "data")],
    )
    def update_forecast_graph(
        settings_ts, statistics_ts, calc_results, active_tab, settings, statistics
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

        # Process the settings and statistics data
        df = pd.DataFrame(statistics)
        if len(df) > 0:  # Check if there's any data
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

        # Get necessary values
        total_items = settings.get("total_items", 100)
        total_points = settings.get("total_points", 500)
        pert_factor = settings.get("pert_factor", 3)
        deadline = settings.get("deadline", None)
        data_points_count = settings.get(
            "data_points_count", len(df)
        )  # Get selected data points count

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

        return fig

    @app.callback(
        Output("project-dashboard-pert-content", "children"),
        [
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
        ],
        [State("current-settings", "data"), State("current-statistics", "data")],
    )
    def update_pert_info(
        settings_ts, statistics_ts, calc_results, settings, statistics
    ):
        """Update the PERT information when settings or statistics change."""
        # Get context to see which input triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Validate inputs
        if settings is None or statistics is None:
            raise PreventUpdate

        # Get triggered input ID
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # If triggered by calculation_results but data is None, prevent update
        if trigger_id == "calculation-results" and calc_results is None:
            raise PreventUpdate

        # Process the settings and statistics data
        df = pd.DataFrame(statistics)
        if len(df) > 0:  # Check if there's any data
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

        # Get necessary values
        total_items = settings.get("total_items", 100)
        total_points = settings.get("total_points", 500)
        pert_factor = settings.get("pert_factor", 3)
        deadline = settings.get("deadline", None)
        data_points_count = settings.get(
            "data_points_count", len(df)
        )  # Get selected data points count

        # Get milestone settings
        show_milestone = settings.get("show_milestone", False)
        milestone = settings.get("milestone", None) if show_milestone else None

        # Process data for calculations
        if not df.empty:
            df = compute_cumulative_values(df, total_items, total_points)

        # Create forecast plot and get PERT values
        _, pert_data = create_forecast_plot(
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

        # Calculate weekly averages for the info table with filtering
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(statistics, data_points_count=data_points_count)
        )  # Calculate days to deadline
        deadline_date = pd.to_datetime(deadline)
        current_date = datetime.now()
        days_to_deadline = max(0, (deadline_date - current_date).days)

        # Create the PERT info component for the Project Dashboard
        project_dashboard_pert_info = create_pert_info_table(
            pert_data["pert_time_items"],
            pert_data["pert_time_points"],
            days_to_deadline,
            avg_weekly_items,  # Preserve decimal precision
            avg_weekly_points,  # Preserve decimal precision
            med_weekly_items,  # Preserve decimal precision
            med_weekly_points,  # Preserve decimal precision
            pert_factor=pert_factor,
            total_items=total_items,
            total_points=total_points,
            deadline_str=deadline,
            milestone_str=milestone,  # Pass milestone parameter
            statistics_df=df,
            show_points=settings.get(
                "show_points", False
            ),  # Pass show_points parameter
            data_points_count=data_points_count,  # NEW PARAMETER
        )

        return project_dashboard_pert_info

    def _prepare_trend_data(statistics, pert_factor, data_points_count=None):
        """
        Prepare trend and forecast data for visualizations.

        Args:
            statistics: Statistics data
            pert_factor: PERT factor for forecasts
            data_points_count: Number of data points to use for calculations (default: None, uses all data)

        Returns:
            tuple: (items_trend, points_trend) dictionaries with trend and forecast data
        """
        # Calculate trend indicators for items and points with filtering
        items_trend = calculate_performance_trend(
            statistics, "completed_items", 4, data_points_count=data_points_count
        )
        points_trend = calculate_performance_trend(
            statistics, "completed_points", 4, data_points_count=data_points_count
        )

        # Generate weekly forecast data if statistics available
        if statistics:
            forecast_data = generate_weekly_forecast(
                statistics, pert_factor, data_points_count=data_points_count
            )

            # Add forecast info to trend data if available
            if forecast_data:
                # Process items forecast data
                if "items" in forecast_data:
                    if "optimistic_value" in forecast_data["items"]:
                        items_trend["optimistic_forecast"] = forecast_data["items"][
                            "optimistic_value"
                        ]
                    if "most_likely_value" in forecast_data["items"]:
                        items_trend["most_likely_forecast"] = forecast_data["items"][
                            "most_likely_value"
                        ]
                    if "pessimistic_value" in forecast_data["items"]:
                        items_trend["pessimistic_forecast"] = forecast_data["items"][
                            "pessimistic_value"
                        ]

                # Process points forecast data
                if "points" in forecast_data:
                    if "optimistic_value" in forecast_data["points"]:
                        points_trend["optimistic_forecast"] = forecast_data["points"][
                            "optimistic_value"
                        ]
                    if "most_likely_value" in forecast_data["points"]:
                        points_trend["most_likely_forecast"] = forecast_data["points"][
                            "most_likely_value"
                        ]
                    if "pessimistic_value" in forecast_data["points"]:
                        points_trend["pessimistic_forecast"] = forecast_data["points"][
                            "pessimistic_value"
                        ]

        return items_trend, points_trend

    def _create_trend_header_with_forecasts(
        trend_data, title, icon, color, unit="week"
    ):
        """
        Create a header with trend indicator and forecast pills.

        Args:
            trend_data: Dictionary with trend and forecast data
            title: Title text for the header
            icon: Icon class for the header
            color: Color hex code for the header icon
            unit: Unit for trend values (default: "week")

        Returns:
            html.Div: Header component with trend and forecasts
        """
        # Create forecast pills based on available forecast data
        forecast_pills = []

        # Most likely forecast pill
        if "most_likely_forecast" in trend_data:
            forecast_pills.append(
                create_forecast_pill(
                    "Most likely", trend_data["most_likely_forecast"], color
                )
            )

        # Optimistic forecast pill
        if "optimistic_forecast" in trend_data:
            forecast_pills.append(
                create_forecast_pill(
                    "Optimistic",
                    trend_data["optimistic_forecast"],
                    "#28a745",  # Green color
                )
            )

        # Pessimistic forecast pill
        if "pessimistic_forecast" in trend_data:
            # Use different color based on trend type (items/points)
            pessimistic_color = "#6610f2" if "items" in title.lower() else "#a52a2a"
            forecast_pills.append(
                create_forecast_pill(
                    "Pessimistic", trend_data["pessimistic_forecast"], pessimistic_color
                )
            )

        # Add unit indicator
        forecast_pills.append(
            html.Div(
                html.Small(
                    f"{title.split()[1].lower()}/{unit}",
                    className="text-muted fst-italic",
                ),
                style={"paddingTop": "2px"},
            )
        )

        # Create tooltip components list for proper rendering
        tooltip_components = []

        # Create methodology tooltip
        methodology_tooltip = create_info_tooltip(
            f"weekly-chart-methodology-{title.split()[1].lower()}",
            CHART_HELP_TEXTS["weekly_chart_methodology"],
        )
        tooltip_components.append(methodology_tooltip)

        # Create weighted average tooltip
        weighted_avg_tooltip = create_info_tooltip(
            f"weighted-average-{title.split()[1].lower()}",
            CHART_HELP_TEXTS["weighted_moving_average"],
        )
        tooltip_components.append(weighted_avg_tooltip)

        # Create exponential weighting tooltip
        exponential_tooltip = create_info_tooltip(
            f"exponential-weighting-{title.split()[1].lower()}",
            CHART_HELP_TEXTS["exponential_weighting"],
        )
        tooltip_components.append(exponential_tooltip)

        # Create forecast methodology tooltip
        forecast_tooltip = create_info_tooltip(
            f"forecast-methodology-{title.split()[1].lower()}",
            CHART_HELP_TEXTS["forecast_vs_actual_bars"],
        )
        tooltip_components.append(forecast_tooltip)

        # Create the header component with tooltips rendered separately
        return html.Div(
            [
                # Header with icon and title - enhanced with tooltips
                html.Div(
                    [
                        html.I(
                            className=f"{icon} me-2",
                            style={"color": color},
                        ),
                        html.Span(
                            title,
                            className="fw-medium",
                        ),
                        # Add methodology tooltip icon only
                        html.I(
                            className="fas fa-info-circle text-info ms-2",
                            id=f"info-tooltip-weekly-chart-methodology-{title.split()[1].lower()}",
                            style={"cursor": "pointer"},
                        ),
                    ],
                    className="d-flex align-items-center mb-2",
                ),
                # Enhanced trend indicator with weighted average tooltip
                html.Div(
                    [
                        create_compact_trend_indicator(trend_data, title.split()[1]),
                        # Add weighted average explanation tooltip icon
                        html.I(
                            className="fas fa-chart-line text-info ms-2",
                            id=f"info-tooltip-weighted-average-{title.split()[1].lower()}",
                            style={"cursor": "pointer"},
                        ),
                        # Add exponential weighting details tooltip icon
                        html.I(
                            className="fas fa-calculator text-info ms-2",
                            id=f"info-tooltip-exponential-weighting-{title.split()[1].lower()}",
                            style={"cursor": "pointer"},
                        ),
                    ],
                    className="d-flex align-items-center",
                    style={"gap": "0.25rem"},
                ),
                # Enhanced forecast pills with methodology tooltip
                html.Div(
                    [
                        html.Div(
                            forecast_pills,
                            className="d-flex flex-wrap align-items-center",
                            style={"gap": "0.25rem"},
                        ),
                        # Add forecast methodology tooltip icon
                        html.I(
                            className="fas fa-chart-bar text-info ms-2",
                            id=f"info-tooltip-forecast-methodology-{title.split()[1].lower()}",
                            style={"cursor": "pointer"},
                        ),
                    ],
                    className="d-flex align-items-center mt-2",
                    style={"gap": "0.5rem"},
                ),
                # Add all tooltip components at the end for proper rendering
                html.Div(tooltip_components, style={"display": "none"}),
            ],
            className="col-md-6 col-12 mb-3 pe-md-2",
        )

    def _create_burndown_tab_content(
        df,
        items_trend,
        points_trend,
        burndown_fig,
        burnup_fig,
        settings,
        chart_type="burndown",
        show_points=True,
    ):
        """
        Create content for the burndown tab with toggle between burndown and burnup views.

        Args:
            df: DataFrame with statistics data
            items_trend: Dictionary with items trend and forecast data
            points_trend: Dictionary with points trend and forecast data
            burndown_fig: Burndown chart figure
            burnup_fig: Burnup chart figure
            settings: Settings dictionary
            chart_type: Current chart type to display ('burndown' or 'burnup')

        Returns:
            html.Div: Burndown tab content
        """
        # Use the appropriate figure based on chart_type
        current_figure = burnup_fig if chart_type == "burnup" else burndown_fig
        chart_height = settings.get("chart_height", 700)

        # Create a toggle switch between burndown and burnup charts
        chart_toggle = html.Div(
            [
                html.Div(
                    [
                        dbc.RadioItems(
                            id="chart-type-toggle",
                            className="chart-toggle-buttons",
                            options=[
                                {"label": "Burndown", "value": "burndown"},
                                {"label": "Burnup", "value": "burnup"},
                            ],
                            value=chart_type,  # Set the initial value based on the parameter
                            inline=True,
                            labelStyle={
                                "display": "inline-block",
                                "padding": "8px 15px",
                                "border": "1px solid #dee2e6",
                                "borderRadius": "4px",
                                "margin": "0 5px",
                                "background": "rgba(255, 255, 255, 0.8)",
                                "boxShadow": "0 1px 3px rgba(0,0,0,0.1)",
                                "cursor": "pointer",
                                "transition": "all 0.3s ease",
                            },
                            labelCheckedStyle={
                                "background": "#20c997",
                                "borderColor": "#20c997",
                                "color": "white",
                                "fontWeight": "bold",
                                "boxShadow": "0 2px 5px rgba(0,0,0,0.2)",
                            },
                            inputStyle={"display": "none"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "marginBottom": "0",
                    },
                ),
                dbc.Tooltip(
                    CHART_HELP_TEXTS["burndown_vs_burnup"],
                    target="chart-type-toggle",
                ),
            ],
            className="chart-toggle-container",
            style={"marginBottom": "20px"},
        )

        return html.Div(
            [
                # Weekly trend indicators in a row
                html.Div(
                    [
                        # Items trend box
                        _create_trend_header_with_forecasts(
                            items_trend,
                            "Weekly Items Trend",
                            "fas fa-tasks",
                            "#20c997",
                        ),
                    ]
                    + (
                        [
                            # Points trend box - only show if points tracking is enabled
                            _create_trend_header_with_forecasts(
                                points_trend,
                                "Weekly Points Trend",
                                "fas fa-chart-bar",
                                "#fd7e14",
                            ),
                        ]
                        if show_points
                        else []
                    ),
                    className="row mb-3",
                ),
                # Chart type toggle
                chart_toggle,
                # Chart container - will be updated by the toggle callback
                html.Div(
                    dcc.Graph(
                        id="forecast-graph",
                        figure=current_figure,
                        config={
                            "displayModeBar": False,  # Hidden via CSS for cleaner mobile experience
                            "responsive": True,
                            "scrollZoom": True,
                            "doubleClick": "autosize",
                            "showTips": True,
                            "displaylogo": False,
                        },
                        style={"height": f"{chart_height}px"},
                    ),
                    id="chart-container",
                ),
            ]
        )

    def _create_items_tab_content(items_trend, items_fig):
        """
        Create content for the items tab.

        Args:
            items_trend: Dictionary with items trend and forecast data
            items_fig: Weekly items chart figure

        Returns:
            html.Div: Items tab content
        """
        return html.Div(
            [
                # Enhanced header with trend indicator and forecast pills
                html.Div(
                    [
                        # Column for items trend
                        _create_trend_header_with_forecasts(
                            items_trend,
                            "Weekly Items Trend",
                            "fas fa-tasks",
                            "#20c997",
                        ),
                    ],
                    className="mb-4",
                ),
                # Consolidated items weekly chart with forecast
                dcc.Graph(
                    id="items-chart",
                    figure=items_fig,
                    config={
                        "displayModeBar": True,
                        "responsive": True,
                        "toImageButtonOptions": {
                            "filename": f"weekly_items_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        },
                    },
                    style={"height": "700px"},
                ),
            ]
        )

    def _create_points_tab_content(points_trend, points_fig):
        """
        Create content for the points tab.

        Args:
            points_trend: Dictionary with points trend and forecast data
            points_fig: Weekly points chart figure

        Returns:
            html.Div: Points tab content
        """
        return html.Div(
            [
                # Enhanced header with trend indicator and forecast pills
                html.Div(
                    [
                        # Column for points trend
                        _create_trend_header_with_forecasts(
                            points_trend,
                            "Weekly Points Trend",
                            "fas fa-chart-bar",
                            "#fd7e14",
                        ),
                    ],
                    className="mb-4",
                ),
                # Consolidated points weekly chart with forecast
                dcc.Graph(
                    id="points-chart",
                    figure=points_fig,
                    config={
                        "displayModeBar": True,
                        "responsive": True,
                        "toImageButtonOptions": {
                            "filename": f"weekly_points_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        },
                    },
                    style={"height": "700px"},
                ),
            ]
        )

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
        data_points_count = settings.get("data_points_count", len(df))

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
        df["date"] = pd.to_datetime(df["date"])

        # Get baseline values
        baseline_items = settings.get("total_items", 100)
        baseline_points = settings.get("total_points", 500)

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
        return create_scope_metrics_dashboard(
            scope_creep_rate,
            weekly_growth_data,
            stability_index,
            scope_creep_threshold,
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
            Input("points-toggle", "value"),  # Added points toggle input
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
            State("chart-cache", "data"),
            State("ui-state", "data"),
        ],
    )
    def render_tab_content(
        active_tab,
        settings_ts,
        statistics_ts,
        calc_results,
        date_range_weeks,
        show_points,  # Added parameter
        settings,
        statistics,
        chart_cache,
        ui_state,
    ):
        """
        Render the appropriate content based on the selected tab with lazy loading and caching.
        Only generates charts for the active tab to improve performance.
        Target: <500ms chart rendering, immediate skeleton loading, <100ms cached responses.
        """
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

        # Clear old cache entries to prevent memory bloat (keep last 5)
        if len(chart_cache) > 5:
            oldest_keys = list(chart_cache.keys())[:-5]
            for old_key in oldest_keys:
                if old_key in chart_cache:
                    del chart_cache[old_key]

        # Create simplified cache key - only essential data for chart generation
        data_hash = hash(str(statistics) + str(settings) + str(show_points))
        cache_key = f"{active_tab}_{data_hash}"

        # Check if we have cached content for this exact state
        if cache_key in chart_cache:
            # Return cached content immediately for <100ms response time
            ui_state["loading"] = False
            ui_state["last_tab"] = active_tab
            return chart_cache[cache_key], chart_cache, ui_state

        # Set loading state for new tab content generation
        ui_state["loading"] = True
        ui_state["last_tab"] = active_tab

        try:
            # Get values from settings
            pert_factor = settings["pert_factor"]
            total_items = settings["total_items"]
            total_points = calc_results.get("total_points", settings["total_points"])
            deadline = settings["deadline"]
            data_points_count = settings.get("data_points_count")

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            # LAZY LOADING: Only generate charts for the active tab
            show_milestone = settings.get("show_milestone", False)
            milestone = settings.get("milestone", None) if show_milestone else None

            if active_tab == "tab-burndown":
                # Generate all required data for burndown tab
                items_trend, points_trend = _prepare_trend_data(statistics, pert_factor)

                # Generate burndown chart only when needed
                burndown_fig, _ = create_forecast_plot(
                    df=compute_cumulative_values(df, total_items, total_points)
                    if not df.empty
                    else df,
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,
                    data_points_count=data_points_count,
                    show_points=show_points,
                )

                # Generate burnup chart for the toggle (only if on burndown tab)
                from visualization import create_burnup_chart

                burnup_fig, _ = create_burnup_chart(
                    df=df.copy() if not df.empty else df,
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,
                    data_points_count=data_points_count,
                    show_points=show_points,
                )

                # Create burndown tab content with all required data
                burndown_tab_content = _create_burndown_tab_content(
                    df,
                    items_trend,
                    points_trend,
                    burndown_fig,
                    burnup_fig,
                    settings,
                    "burndown",
                    show_points,
                )
                # Cache the result for next time
                chart_cache[cache_key] = burndown_tab_content
                ui_state["loading"] = False
                return burndown_tab_content, chart_cache, ui_state

            elif active_tab == "tab-items":
                # Generate trend data and weekly items chart only when needed
                items_trend, points_trend = _prepare_trend_data(
                    statistics, pert_factor, data_points_count
                )
                items_fig = create_weekly_items_chart(
                    statistics,
                    date_range_weeks,
                    pert_factor,
                    data_points_count=data_points_count,
                )
                items_tab_content = _create_items_tab_content(items_trend, items_fig)
                # Cache the result for next time
                chart_cache[cache_key] = items_tab_content
                ui_state["loading"] = False
                return items_tab_content, chart_cache, ui_state

            elif active_tab == "tab-points":
                if show_points:
                    # Generate trend data and weekly points chart only when needed
                    items_trend, points_trend = _prepare_trend_data(
                        statistics, pert_factor, data_points_count
                    )
                    points_fig = create_weekly_points_chart(
                        statistics,
                        date_range_weeks,
                        pert_factor,
                        data_points_count=data_points_count,
                    )
                    points_tab_content = _create_points_tab_content(
                        points_trend, points_fig
                    )
                    # Cache the result for next time
                    chart_cache[cache_key] = points_tab_content
                    ui_state["loading"] = False
                    return points_tab_content, chart_cache, ui_state
                else:
                    # Points tracking disabled content
                    points_disabled_content = html.Div(
                        [
                            html.Div(
                                [
                                    html.H4(
                                        "Points Tracking Disabled",
                                        className="text-muted",
                                    ),
                                    html.P(
                                        "Enable the Points Tracking toggle in the Project Timeline form to view points forecasts.",
                                        className="text-muted",
                                    ),
                                ],
                                className="alert alert-info text-center",
                            )
                        ]
                    )
                    # Cache the result for next time
                    chart_cache[cache_key] = points_disabled_content
                    ui_state["loading"] = False
                    return points_disabled_content, chart_cache, ui_state

            elif active_tab == "tab-scope-tracking":
                # Generate scope tracking content only when needed
                scope_tab_content = _create_scope_tracking_tab_content(
                    df, settings, show_points
                )
                # Cache the result for next time
                chart_cache[cache_key] = scope_tab_content
                ui_state["loading"] = False
                return scope_tab_content, chart_cache, ui_state

            elif active_tab == "tab-bug-analysis":
                # Generate bug analysis tab content
                from ui.bug_analysis import create_bug_analysis_tab

                bug_analysis_content = create_bug_analysis_tab()
                # Cache the result for next time
                chart_cache[cache_key] = bug_analysis_content
                ui_state["loading"] = False
                return bug_analysis_content, chart_cache, ui_state

            # Default fallback (should not reach here)
            fallback_content = create_content_placeholder(
                type="chart", text="Select a tab to view data", height="400px"
            )
            ui_state["loading"] = False
            return fallback_content, chart_cache, ui_state

        except Exception as e:
            logger.error(f"Error in render_tab_content callback: {e}")
            error_content = html.Div(
                [
                    html.H4("Error Loading Chart", className="text-danger"),
                    html.P(f"An error occurred: {str(e)}"),
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

        Args:
            n_clicks: Number of button clicks

        Returns:
            Dictionary with JSON download data
        """
        if not n_clicks:
            raise PreventUpdate

        try:
            from data.persistence import load_unified_project_data

            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Load the complete unified project data
            project_data = load_unified_project_data()

            # Create filename with timestamp
            filename = f"project_data_{current_time}.json"

            # Convert to JSON string with pretty formatting
            json_content = json.dumps(project_data, indent=2, ensure_ascii=False)

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

    @app.callback(
        Output("chart-container", "children"),
        [Input("chart-type-toggle", "value")],
        [State("current-settings", "data"), State("current-statistics", "data")],
    )
    def update_chart_type(chart_type, settings, statistics):
        """
        Update the chart based on selected chart type (burndown or burnup).

        Args:
            chart_type: Selected chart type ('burndown' or 'burnup')
            settings: Current settings data
            statistics: Current statistics data

        Returns:
            html.Div: Updated chart container with selected chart type
        """
        if not settings or not statistics:
            raise PreventUpdate

        # Convert statistics to DataFrame
        df = pd.DataFrame(statistics)
        if df.empty:
            # Return empty placeholder chart if no data
            return dcc.Graph(
                id="forecast-graph",
                figure=go.Figure().update_layout(
                    title="No Data Available",
                    annotations=[
                        dict(
                            text="No data available to display chart",
                            showarrow=False,
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                        )
                    ],
                ),
                config={"displayModeBar": True, "responsive": True},
                style={"height": "700px"},
            )

        try:
            # Get necessary values - ensure all parameters are normalized for both charts
            total_items = settings.get("total_items", 100)
            total_points = settings.get("total_points", 500)
            pert_factor = settings.get("pert_factor", 3)
            deadline = settings.get("deadline", None)
            show_points = settings.get("show_points", False)  # Default to False

            # Get milestone settings - THIS WAS MISSING
            show_milestone = settings.get("show_milestone", False)
            milestone = settings.get("milestone", None) if show_milestone else None

            # Dynamically recalculate data_points_count based on actual statistics length
            # This ensures when rows are deleted, both charts use the updated row count
            stored_data_points = settings.get("data_points_count", len(df))
            data_points_count = min(stored_data_points, len(df))

            show_forecast = settings.get("show_forecast", True)
            forecast_visibility = settings.get(
                "forecast_visibility", True
            )  # Changed from "legendonly" to True
            hover_mode = settings.get(
                "hover_mode", "x unified"
            )  # Add hover mode setting
            chart_height = settings.get("chart_height", 700)

            # Generate timestamp for the filename
            current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Prepare data consistently for both charts
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])

            # Create processed dataframe - used for burndown chart
            processed_df = (
                compute_cumulative_values(df.copy(), total_items, total_points)
                if not df.empty
                else df.copy()
            )

            # Get appropriate chart based on selection
            if chart_type == "burndown":
                # For burndown chart
                from visualization import create_forecast_plot

                figure, _ = create_forecast_plot(
                    df=processed_df,
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,  # Pass milestone parameter here
                    data_points_count=data_points_count,
                    show_forecast=show_forecast,
                    forecast_visibility=forecast_visibility,
                    hover_mode=hover_mode,  # Pass hover mode for consistent behavior
                    show_points=show_points,  # Pass show_points parameter
                )

            else:
                # For burnup chart
                from visualization import create_burnup_chart

                figure, _ = create_burnup_chart(
                    df=df.copy(),
                    total_items=total_items,
                    total_points=total_points,
                    pert_factor=pert_factor,
                    deadline_str=deadline,
                    milestone_str=milestone,  # Pass milestone parameter here
                    data_points_count=data_points_count,
                    show_forecast=show_forecast,  # Pass this parameter
                    forecast_visibility=forecast_visibility,  # Pass this parameter
                    hover_mode=hover_mode,  # Pass this parameter
                    show_points=show_points,  # Pass show_points parameter
                )

            return dcc.Graph(
                id="forecast-graph",
                figure=figure,
                config={
                    "displayModeBar": True,
                    "responsive": True,
                    "toImageButtonOptions": {
                        "filename": f"{'burndown' if chart_type == 'burndown' else 'burnup'}_chart_{current_timestamp}"
                    },
                },
                style={"height": f"{chart_height}px"},
            )

        except Exception as e:
            # Log the error
            logger.error(f"Error updating chart type: {str(e)}")

            # Return error message
            return html.Div(
                [
                    html.Div(
                        className="alert alert-light border-danger mb-3",
                        children=[
                            html.I(
                                className="fas fa-exclamation-triangle me-2 text-danger"
                            ),
                            html.Span(
                                f"Error displaying chart: {str(e)}",
                                className="text-dark",
                            ),
                        ],
                    ),
                    dcc.Graph(
                        id="forecast-graph",
                        figure=go.Figure().update_layout(
                            title=f"Error: {str(e)}",
                        ),
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "700px"},
                    ),
                ]
            )

    @app.callback(
        Output("selected-chart-type", "data"),
        Input("chart-type-toggle", "value"),
    )
    def store_chart_type(chart_type):
        """
        Store the selected chart type (burndown or burnup) when the toggle is clicked.
        This allows for persistence of the chart type between parameter changes.

        Args:
            chart_type: Selected chart type ('burndown' or 'burnup')

        Returns:
            str: Chart type to be stored
        """
        # Validate the chart type
        if chart_type not in ["burndown", "burnup"]:
            # Default to burndown if an invalid value is provided
            return "burndown"

        # Store the selected chart type
        return chart_type


def register_loading_callbacks(app):
    """
    Register callbacks that demonstrate loading states.

    Args:
        app: Dash application instance
    """
    from dash import Input, Output, State, callback_context, html

    @app.callback(
        Output("forecast-chart-container", "children"),
        Input("generate-forecast-btn", "n_clicks"),
        [State("data-store", "data")],
        prevent_initial_call=True,
    )
    def update_forecast_chart_with_loading(n_clicks, data):
        """
        Update forecast chart with loading indicators while data is processing
        """
        if not n_clicks or not data:
            # Create placeholder when no data is available
            return create_content_placeholder(
                type="chart",
                text="Click 'Generate Forecast' to create chart",
                height="400px",
            )

        # Simulate processing delay to show loading state (in real app, this would be actual processing time)
        time.sleep(1)

        ctx = callback_context
        if not ctx.triggered:
            return create_content_placeholder(
                type="chart",
                text="Click 'Generate Forecast' to create chart",
                height="400px",
            )

        # Process the data to create the forecast chart (simplified for example)

        try:
            # In a real implementation, we would pass this to create_forecast_plot
            import pandas as pd

            from visualization.charts import create_forecast_plot

            # This would normally be properly processed data
            df = pd.DataFrame(data.get("statistics", []))
            total_items = data.get("total_items", 0)
            total_points = data.get("total_points", 0)
            pert_factor = data.get("pert_factor", 3)
            deadline_str = data.get("deadline", None)

            # Create the chart (real implementation would call create_forecast_plot)
            figure, _ = create_forecast_plot(
                df,
                total_items,
                total_points,
                pert_factor,
                deadline_str,
                show_points=data.get("show_points", False),
            )

            # Return the chart with loading state
            return create_chart_with_loading(
                id="forecast-chart",
                figure=figure,
                loading_state=None,  # No longer loading
                type="line",
                height="500px",
            )

        except Exception as e:
            # Show error state with retry button
            return html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-exclamation-triangle text-danger me-2",
                                style={"fontSize": "2rem"},
                            ),
                            html.H5("Error Generating Chart", className="text-danger"),
                        ],
                        className="d-flex align-items-center mb-3",
                    ),
                    html.P(f"An error occurred: {str(e)}", className="text-muted mb-3"),
                    dbc.Button(
                        [html.I(className="fas fa-sync me-2"), "Retry"],
                        id="retry-forecast-btn",
                        color="primary",
                        className="mt-3",
                    ),
                ],
                className="text-center p-5 border rounded bg-light",
            )

    @app.callback(
        Output("statistics-table-container", "children"),
        [Input("upload-data", "contents"), Input("loading-demo-btn", "n_clicks")],
        [State("upload-data", "filename"), State("data-store", "data")],
        prevent_initial_call=True,
    )
    def update_statistics_table_with_loading(contents, n_clicks, filename, data):
        """
        Update statistics table with various loading state visualizations
        """
        ctx = callback_context
        triggered_id = (
            ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
        )

        if triggered_id == "loading-demo-btn":
            # This is a demo to showcase different loading states
            # Create a tabbed interface showing different loading states
            from ui.loading_utils import create_lazy_loading_tabs

            # Define tabs with different loading state examples
            tabs_data = [
                {
                    "label": "Spinner Overlay",
                    "icon": "spinner",
                    "content": html.Div(
                        [
                            html.H5("Spinner Overlay Example"),
                            html.P(
                                "This demonstrates a spinner overlay on top of content."
                            ),
                            create_spinner(
                                style_key="primary",
                                size_key="lg",
                                text="Loading data...",
                            ),
                        ],
                        className="p-4",
                    ),
                },
                {
                    "label": "Skeleton Loading",
                    "icon": "skeleton",
                    "content": html.Div(
                        [
                            html.H5("Skeleton Loading Example"),
                            html.P(
                                "This demonstrates skeleton loaders that mimic content structure."
                            ),
                            html.Div(
                                [
                                    create_skeleton_loader(
                                        type="text", lines=3, width="100%"
                                    ),
                                    create_skeleton_loader(
                                        type="card", width="100%", className="mt-4"
                                    ),
                                ]
                            ),
                        ],
                        className="p-4",
                    ),
                },
                {
                    "label": "Content Placeholders",
                    "icon": "placeholder",
                    "content": html.Div(
                        [
                            html.H5("Content Placeholders Example"),
                            html.P(
                                "These placeholders indicate the type of content being loaded."
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        create_content_placeholder(
                                            type="chart",
                                            height="150px",
                                            className="mb-3 w-100",
                                        ),
                                        style={"width": "100%"},
                                    ),
                                    create_content_placeholder(
                                        type="table", height="150px", className="w-100"
                                    ),
                                ],
                                className="d-flex flex-column",
                            ),
                        ],
                        className="p-4",
                    ),
                },
            ]

            tabs, contents = create_lazy_loading_tabs(
                tabs_data, "loading-demo-tab", "loading-demo-content"
            )

            return html.Div(
                [
                    html.H4("Loading State Examples", className="mb-3"),
                    html.P(
                        "Click on the tabs below to see different loading state implementations.",
                        className="text-muted mb-4",
                    ),
                    tabs,
                    contents,
                ],
                className="p-3 border rounded",
            )

        # Regular file upload process with loading indicators
        elif triggered_id == "upload-data" and contents:
            # Simulate processing delay
            time.sleep(1)

            # In a real implementation, parse_contents would be called here
            import base64
            import io
            import json

            import pandas as pd
            from dash import dash_table

            # This would be the actual content processing logic
            try:
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)

                # Determine file type and parse accordingly
                if "csv" in filename.lower():
                    # Parse CSV
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
                elif "json" in filename.lower():
                    # Parse JSON
                    json_data = json.loads(decoded.decode("utf-8"))
                    df = pd.DataFrame(json_data)
                elif "xls" in filename.lower():
                    # Parse Excel
                    df = pd.read_excel(io.BytesIO(decoded))
                else:
                    return html.Div(
                        [
                            html.H5("Unsupported File Type", className="text-danger"),
                            html.P(
                                f"File format {filename} is not supported. Please upload a CSV, JSON, or Excel file."
                            ),
                        ],
                        className="p-3 border border-danger rounded",
                    )

                # Return the DataTable with the processed data
                return html.Div(
                    [
                        html.H5(
                            f"Successfully loaded: {filename}",
                            className="text-success mb-3",
                        ),
                        dash_table.DataTable(
                            data=[
                                {str(k): v for k, v in record.items()}
                                for record in df.to_dict("records")
                            ],
                            columns=[{"name": i, "id": i} for i in df.columns],
                            style_table={"overflowX": "auto"},
                            style_cell={
                                "height": "auto",
                                "minWidth": "100px",
                                "width": "150px",
                                "maxWidth": "300px",
                                "whiteSpace": "normal",
                                "textAlign": "left",
                            },
                            style_header={
                                "backgroundColor": "rgb(230, 230, 230)",
                                "fontWeight": "bold",
                            },
                        ),
                    ],
                    className="border rounded p-3",
                )

            except Exception as e:
                # Display error message
                return html.Div(
                    [
                        html.H5("Error Processing File", className="text-danger"),
                        html.P(f"An error occurred: {str(e)}"),
                        dbc.Button(
                            [html.I(className="fas fa-upload me-2"), "Try Again"],
                            id="retry-upload-btn",
                            color="primary",
                            className="mt-3",
                        ),
                    ],
                    className="border border-danger rounded p-4 text-center",
                )

        # Default state with no content yet
        return create_content_placeholder(
            type="table", text="Upload a CSV or Excel file to view data", height="200px"
        )


# New callbacks for collapsible forecast info cards
@callback(
    Output("items-forecast-info-collapse", "is_open"),
    Input("items-forecast-info-collapse-button", "n_clicks"),
    State("items-forecast-info-collapse", "is_open"),
)
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


# DISABLED: This callback causes React hooks errors by dynamically changing tab structure
# @callback(
#     Output("chart-tabs", "children"),
#     [Input("points-toggle", "value")],
#     [State("chart-tabs", "children")],
# )
# def update_tab_visibility(show_points, current_tabs):
#     """
#     Update tab visibility based on points toggle state.
#     Hide the points tab when points toggle is disabled.
#     """
#     if current_tabs is None:
#         raise PreventUpdate

#     # Import here to avoid circular import
#     import dash_bootstrap_components as dbc

#     # Create new tabs list based on show_points state
#     tab_config = [
#         {
#             "id": "tab-burndown",
#             "label": "Burndown Chart",
#             "icon": "fas fa-chart-line",
#             "color": "#0d6efd",  # Primary blue
#         },
#         {
#             "id": "tab-items",
#             "label": "Items per Week",
#             "icon": "fas fa-tasks",
#             "color": "#20c997",  # Teal
#         },
#     ]

#     # Only add points tab if toggle is enabled
#     if show_points:
#         tab_config.append(
#             {
#                 "id": "tab-points",
#                 "label": "Points per Week",
#                 "icon": "fas fa-chart-bar",
#                 "color": "#fd7e14",  # Orange
#             }
#         )

#     # Always include scope tracking tab
#     tab_config.append(
#         {
#             "id": "tab-scope-tracking",
#             "label": "Scope Changes",
#             "icon": "fas fa-project-diagram",
#             "color": "#e83e8c",  # Pink
#         }
#     )

#     # Create new tabs
#     tabs = []
#     for config in tab_config:
#         tab_style = {
#             "borderTopLeftRadius": "0.375rem",
#             "borderTopRightRadius": "0.375rem",
#             "borderBottom": "none",
#             "marginRight": "0.5rem",
#             "color": config["color"],
#         }

#         tab = dbc.Tab(
#             label=config["label"],  # Use string label instead of html.Div
#             tab_id=config["id"],
#             tab_style=tab_style,
#             active_tab_style={
#                 **tab_style,
#                 "backgroundColor": config["color"],
#                 "color": "white",
#             },
#         )
#         tabs.append(tab)

#     return tabs
