"""
Visualization Callbacks Module

This module handles callbacks related to visualization updates and interactions.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import logging
import time
from datetime import datetime

# Third-party library imports
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, callback, callback_context, dcc, html
from dash.exceptions import PreventUpdate

# Application imports
from data import (
    calculate_performance_trend,
    calculate_weekly_averages,
    compute_cumulative_values,
    generate_weekly_forecast,
)
from ui import (
    create_compact_trend_indicator,
    create_pert_info_table,
    create_tab_content,
)
from ui.loading_utils import (
    create_spinner,
    create_skeleton_loader,
    create_content_placeholder,
)
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
                        f"{value:.1f}",
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
            data_points_count=data_points_count,
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
            data_points_count=data_points_count,
        )

        # Calculate weekly averages for the info table
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(statistics)
        )

        # Calculate days to deadline
        deadline_date = pd.to_datetime(deadline)
        current_date = datetime.now()
        days_to_deadline = max(0, (deadline_date - current_date).days)

        # Create the PERT info component for the Project Dashboard
        project_dashboard_pert_info = create_pert_info_table(
            pert_data["pert_time_items"],
            pert_data["pert_time_points"],
            days_to_deadline,
            avg_weekly_items,
            avg_weekly_points,
            med_weekly_items,
            med_weekly_points,
            pert_factor=pert_factor,
            total_items=total_items,
            total_points=total_points,
            deadline_str=deadline,
            statistics_df=df,
        )

        return project_dashboard_pert_info

    def _prepare_trend_data(statistics, pert_factor):
        """
        Prepare trend and forecast data for visualizations.

        Args:
            statistics: Statistics data
            pert_factor: PERT factor for forecasts

        Returns:
            tuple: (items_trend, points_trend) dictionaries with trend and forecast data
        """
        # Calculate trend indicators for items and points
        items_trend = calculate_performance_trend(statistics, "completed_items", 4)
        points_trend = calculate_performance_trend(statistics, "completed_points", 4)

        # Generate weekly forecast data if statistics available
        if statistics:
            forecast_data = generate_weekly_forecast(statistics, pert_factor)

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

        # Create the header component
        return html.Div(
            [
                # Header with icon and title
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
                    ],
                    className="d-flex align-items-center mb-2",
                ),
                # Add compact trend indicator
                create_compact_trend_indicator(trend_data, title.split()[1]),
                # Add forecast pills in a flex container
                html.Div(
                    forecast_pills,
                    className="d-flex flex-wrap mt-2 align-items-center",
                    style={"gap": "0.25rem"},
                ),
            ],
            className="col-md-6 col-12 mb-3 pe-md-2",
        )

    def _create_burndown_tab_content(
        df, items_trend, points_trend, burndown_fig, burnup_fig, settings
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

        Returns:
            html.Div: Burndown tab content
        """
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
                            value="burndown",
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
                        "marginBottom": "15px",
                    },
                ),
                dbc.Tooltip(
                    "Toggle between burndown view (showing work remaining) and burnup view (showing work completed and total scope)",
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
                        # Points trend box
                        _create_trend_header_with_forecasts(
                            points_trend,
                            "Weekly Points Trend",
                            "fas fa-chart-bar",
                            "#fd7e14",
                        ),
                    ],
                    className="row mb-3",
                ),
                # Chart type toggle
                chart_toggle,
                # Chart container - will be updated by the toggle callback
                html.Div(
                    dcc.Graph(
                        id="forecast-graph",
                        figure=burndown_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "700px"},
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
                    config={"displayModeBar": True, "responsive": True},
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
                    config={"displayModeBar": True, "responsive": True},
                    style={"height": "700px"},
                ),
            ]
        )

    def _create_scope_tracking_tab_content(df, settings):
        """
        Create content for the scope tracking tab.

        Args:
            df: DataFrame with statistics data
            settings: Settings dictionary

        Returns:
            html.Div: Scope tracking tab content
        """
        from data.scope_metrics import (
            calculate_scope_creep_rate,
            calculate_weekly_scope_growth,
            calculate_scope_stability_index,
        )
        from ui.scope_metrics import create_scope_metrics_dashboard

        # Get threshold from settings or use default
        scope_creep_threshold = settings.get("scope_creep_threshold", 15)

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

        # Calculate scope creep rate
        scope_creep_rate = calculate_scope_creep_rate(
            df, baseline_items, baseline_points
        )

        # Calculate weekly scope growth - ensure the function returns a DataFrame
        try:
            weekly_growth_data = calculate_weekly_scope_growth(df)
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

        # Calculate scope stability index
        stability_index = calculate_scope_stability_index(
            df, baseline_items, baseline_points
        )

        # Create the scope metrics dashboard
        return create_scope_metrics_dashboard(
            scope_creep_rate, weekly_growth_data, stability_index, scope_creep_threshold
        )

    @app.callback(
        Output("tab-content", "children"),
        [
            Input("chart-tabs", "active_tab"),
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
            Input("date-range-weeks", "data"),
        ],
        [
            State("current-settings", "data"),
            State("current-statistics", "data"),
        ],
    )
    def render_tab_content(
        active_tab,
        settings_ts,
        statistics_ts,
        calc_results,
        date_range_weeks,
        settings,
        statistics,
    ):
        """
        Render the appropriate content based on the selected tab.
        This callback updates whenever tab selection changes or the underlying data changes.
        """
        if not settings or not statistics:
            raise PreventUpdate

        try:
            # Get values from settings
            pert_factor = settings["pert_factor"]
            total_items = settings["total_items"]
            total_points = calc_results.get("total_points", settings["total_points"])
            deadline = settings["deadline"]
            # Get the data_points_count setting
            data_points_count = settings.get("data_points_count")

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            # Prepare charts for each tab
            charts = {}

            # Prepare trend data (items and points trends with forecasts)
            items_trend, points_trend = _prepare_trend_data(statistics, pert_factor)

            # Burndown chart
            burndown_fig, _ = create_forecast_plot(
                df=compute_cumulative_values(df, total_items, total_points)
                if not df.empty
                else df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
                data_points_count=data_points_count,
            )

            # Burnup chart
            from visualization import create_burnup_chart

            burnup_fig, _ = create_burnup_chart(
                df=df.copy() if not df.empty else df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
                data_points_count=data_points_count,
            )

            # Create burndown tab content with both chart types
            charts["tab-burndown"] = _create_burndown_tab_content(
                df, items_trend, points_trend, burndown_fig, burnup_fig, settings
            )

            # Weekly items chart with forecast
            items_fig = create_weekly_items_chart(
                statistics, date_range_weeks, pert_factor
            )

            # Create items tab content
            charts["tab-items"] = _create_items_tab_content(items_trend, items_fig)

            # Weekly points chart with forecast
            points_fig = create_weekly_points_chart(
                statistics, date_range_weeks, pert_factor
            )

            # Create points tab content
            charts["tab-points"] = _create_points_tab_content(points_trend, points_fig)

            # Create scope tracking tab content
            charts["tab-scope-tracking"] = _create_scope_tracking_tab_content(
                df, settings
            )

            # Create content for the active tab
            return create_tab_content(active_tab, charts)

        except Exception as e:
            logger.error(f"Error in render_tab_content callback: {e}")
            return html.Div(
                [
                    html.H4("Error Loading Chart", className="text-danger"),
                    html.P(f"An error occurred: {str(e)}"),
                ]
            )

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

    # Add callbacks for CSV exports
    # Create one callback for each chart
    chart_ids = [
        "burndown",
        "items",
        "points",
        "items-forecast",
        "points-forecast",
    ]

    for chart_id in chart_ids:

        @app.callback(
            Output(f"{chart_id}-csv-download", "data"),
            Input(f"{chart_id}-csv-button", "n_clicks"),
            [State("current-statistics", "data"), State("date-range-weeks", "data")],
            prevent_initial_call=True,
        )
        def export_csv_data(n_clicks, statistics, date_range_weeks, chart_id=chart_id):
            """
            Export chart data as CSV when the export button is clicked.

            Args:
                n_clicks: Number of button clicks
                statistics: Current statistics data
                date_range_weeks: Selected date range in weeks
                chart_id: ID of the chart to export (passed in via closure)

            Returns:
                Dictionary with CSV download data
            """
            if not n_clicks or not statistics:
                raise PreventUpdate

            try:
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

                # Create pandas DataFrame for CSV export
                if chart_id == "burndown":
                    # Export burndown chart data
                    df = pd.DataFrame(statistics)
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date")
                    filename = f"burndown_chart_data_{current_time}.csv"

                elif chart_id in ["items", "items-forecast"]:
                    # Export weekly items data
                    df = pd.DataFrame(statistics)
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date")

                    # Group by week
                    df["week"] = df["date"].dt.isocalendar().week
                    df["year"] = df["date"].dt.year
                    df["year_week"] = df.apply(
                        lambda r: f"{r['year']}-W{r['week']:02d}", axis=1
                    )
                    weekly_df = (
                        df.groupby("year_week")
                        .agg(
                            week_start=("date", "min"), items=("completed_items", "sum")
                        )
                        .reset_index()
                    )

                    # Filter by date range if specified
                    if date_range_weeks and chart_id == "items":
                        weekly_df = weekly_df.sort_values("week_start", ascending=False)
                        weekly_df = weekly_df.head(date_range_weeks)
                        weekly_df = weekly_df.sort_values("week_start")

                    df = weekly_df
                    prefix = "forecast_" if chart_id == "items-forecast" else ""
                    filename = f"{prefix}weekly_items_data_{current_time}.csv"

                elif chart_id in ["points", "points-forecast"]:
                    # Export weekly points data
                    df = pd.DataFrame(statistics)
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.sort_values("date")

                    # Group by week
                    df["week"] = df["date"].dt.isocalendar().week
                    df["year"] = df["date"].dt.year
                    df["year_week"] = df.apply(
                        lambda r: f"{r['year']}-W{r['week']:02d}", axis=1
                    )
                    weekly_df = (
                        df.groupby("year_week")
                        .agg(
                            week_start=("date", "min"),
                            points=("completed_points", "sum"),
                        )
                        .reset_index()
                    )

                    # Filter by date range if specified
                    if date_range_weeks and chart_id == "points":
                        weekly_df = weekly_df.sort_values("week_start", ascending=False)
                        weekly_df = weekly_df.head(date_range_weeks)
                        weekly_df = weekly_df.sort_values("week_start")

                    df = weekly_df
                    prefix = "forecast_" if chart_id == "points-forecast" else ""
                    filename = f"{prefix}weekly_points_data_{current_time}.csv"

                # Format dates for better readability
                if "date" in df.columns:
                    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
                if "week_start" in df.columns:
                    df["week_start"] = df["week_start"].dt.strftime("%Y-%m-%d")

                # Return CSV data
                return dcc.send_data_frame(df.to_csv, filename, index=False)

            except Exception as e:
                logger.error(f"Error exporting CSV data for {chart_id}: {e}")
                # Return empty CSV with error message
                error_df = pd.DataFrame({"Error": [f"Failed to export data: {str(e)}"]})
                return dcc.send_data_frame(
                    error_df.to_csv, f"export_error_{current_time}.csv", index=False
                )

    # Add callback for export statistics button
    @app.callback(
        Output("export-statistics-download", "data"),
        Input("export-statistics-button", "n_clicks"),
        [State("current-statistics", "data")],
        prevent_initial_call=True,
    )
    def export_statistics_data(n_clicks, statistics):
        """
        Export statistics data as CSV when the export button is clicked.

        Args:
            n_clicks: Number of button clicks
            statistics: Current statistics data

        Returns:
            Dictionary with CSV download data
        """
        if not n_clicks or not statistics:
            raise PreventUpdate

        try:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Create pandas DataFrame for CSV export
            df = pd.DataFrame(statistics)

            # Ensure required columns exist
            required_columns = [
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
            for col in required_columns:
                if col not in df.columns:
                    if col == "date":
                        # Date is special - can't be missing
                        raise ValueError(
                            "Statistics data is missing required 'date' column"
                        )
                    else:
                        # For other columns, add with default value 0
                        df[col] = 0

            # Ensure numeric columns are properly formatted
            numeric_columns = [
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

            # Ensure date column is in proper datetime format for sorting
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # Sort by date in ascending order (oldest first)
            df = df.sort_values("date", ascending=True)

            # Convert back to string format for display
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")

            # Reorder columns to ensure consistent format
            column_order = [
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
            # Add any additional columns that might be present
            for col in df.columns:
                if col not in column_order:
                    column_order.append(col)

            # Apply the column ordering
            df = df[column_order]

            # Create filename with timestamp
            filename = f"statistics_{current_time}.csv"

            # Return CSV data
            return dcc.send_data_frame(df.to_csv, filename, index=False)

        except Exception as e:
            logger.error(f"Error exporting statistics data: {e}")
            # Return empty CSV with error message
            error_df = pd.DataFrame(
                {"Error": [f"Failed to export statistics data: {str(e)}"]}
            )
            return dcc.send_data_frame(
                error_df.to_csv, f"export_error_{current_time}.csv", index=False
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
            data_points_count = settings.get("data_points_count", len(df))
            show_forecast = settings.get("show_forecast", True)
            forecast_visibility = settings.get("forecast_visibility", "legendonly")
            hover_mode = settings.get(
                "hover_mode", "x unified"
            )  # Add hover mode setting
            chart_height = settings.get("chart_height", 700)

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
                    data_points_count=data_points_count,
                    show_forecast=show_forecast,
                    forecast_visibility=forecast_visibility,
                    hover_mode=hover_mode,  # Pass hover mode for consistent behavior
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
                    data_points_count=data_points_count,
                    show_forecast=show_forecast,  # Pass this parameter
                    forecast_visibility=forecast_visibility,  # Pass this parameter
                    hover_mode=hover_mode,  # Pass this parameter
                )

            return dcc.Graph(
                id="forecast-graph",
                figure=figure,
                config={"displayModeBar": True, "responsive": True},
                style={"height": f"{chart_height}px"},
            )

        except Exception as e:
            # Log the error
            logger.error(f"Error updating chart type: {str(e)}")

            # Return error message
            return html.Div(
                [
                    html.Div(
                        className="alert alert-danger",
                        children=[
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Error displaying chart: {str(e)}",
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


def register_loading_callbacks(app):
    """
    Register callbacks that demonstrate loading states.

    Args:
        app: Dash application instance
    """
    from dash import Input, Output, State, callback_context
    from dash import html

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
            from visualization.charts import create_forecast_plot
            import pandas as pd

            # This would normally be properly processed data
            df = pd.DataFrame(data.get("statistics", []))
            total_items = data.get("total_items", 0)
            total_points = data.get("total_points", 0)
            pert_factor = data.get("pert_factor", 3)
            deadline_str = data.get("deadline", None)

            # Create the chart (real implementation would call create_forecast_plot)
            figure, _ = create_forecast_plot(
                df, total_items, total_points, pert_factor, deadline_str
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
                                    create_content_placeholder(
                                        type="chart",
                                        width="100%",
                                        height="150px",
                                        className="mb-3",
                                    ),
                                    create_content_placeholder(
                                        type="table", width="100%", height="150px"
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
            from dash import dash_table
            import pandas as pd
            import base64
            import io

            # This would be the actual content processing logic
            try:
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)

                # Determine file type and parse accordingly
                if "csv" in filename:
                    # Parse CSV
                    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
                elif "xls" in filename:
                    # Parse Excel
                    df = pd.read_excel(io.BytesIO(decoded))
                else:
                    return html.Div(
                        [
                            html.H5("Unsupported File Type", className="text-danger"),
                            html.P(
                                f"File format {filename} is not supported. Please upload a CSV or Excel file."
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
                            data=df.to_dict("records"),
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
