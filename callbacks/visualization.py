"""
Visualization Callbacks Module

This module handles callbacks related to visualization updates and interactions.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, Input, Output, State, dcc, callback_context
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import dash_bootstrap_components as dbc

# Import from application modules
from configuration import logger
from data import (
    compute_cumulative_values,
    calculate_weekly_averages,
    calculate_performance_trend,
    generate_weekly_forecast,
)
from visualization import (
    create_forecast_plot,
    create_weekly_items_chart,
    create_weekly_points_chart,
    create_weekly_items_forecast_chart,
    create_weekly_points_forecast_chart,
    empty_figure,
)
from ui import (
    create_pert_info_table,
    create_tab_content,
    create_trend_indicator,
    create_export_buttons,
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
        [Output("forecast-graph", "figure"), Output("pert-info-container", "children")],
        [
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
        ],
        [State("current-settings", "data"), State("current-statistics", "data")],
    )
    def update_graph_and_pert_info(
        settings_ts, statistics_ts, calc_results, settings, statistics
    ):
        """
        Update the forecast graph and PERT analysis when settings or statistics change.
        """
        if not settings or not statistics:
            raise PreventUpdate

        try:
            # Create dataframe from statistics data
            df = pd.DataFrame(statistics)

            # Get values from settings
            pert_factor = settings["pert_factor"]
            total_items = settings["total_items"]
            total_points = calc_results.get("total_points", settings["total_points"])
            deadline = settings["deadline"]
            data_points_count = settings.get(
                "data_points_count", len(df)
            )  # Get selected data points count

            # Process data for calculations
            if not df.empty:
                df = compute_cumulative_values(df, total_items, total_points)

            # Create forecast plot and get PERT values
            fig, pert_time_items, pert_time_points = create_forecast_plot(
                df=df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
                data_points_count=data_points_count,  # Pass data_points_count to forecast function
            )

            # Calculate days to deadline
            deadline_date = pd.to_datetime(deadline)
            current_date = datetime.now()
            days_to_deadline = max(0, (deadline_date - current_date).days)

            # Calculate average and median weekly metrics
            avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
                calculate_weekly_averages(statistics)
            )

            # Create PERT info component
            pert_info = create_pert_info_table(
                pert_time_items,
                pert_time_points,
                days_to_deadline,
                avg_weekly_items,
                avg_weekly_points,
                med_weekly_items,
                med_weekly_points,
                pert_factor,
                total_items,  # Pass total items to the info table
                total_points,  # Pass total points to the info table
                deadline,  # Pass the original deadline string from settings
            )

            return fig, pert_info
        except Exception as e:
            logger.error(f"Error in update_graph_and_pert_info callback: {e}")
            # Return empty figure and error message on failure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error generating forecast: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="red"),
            )
            error_info = html.Div(
                [html.P("Error calculating PERT values", style={"color": "red"})]
            )
            return fig, error_info

    @app.callback(
        Output("help-modal", "is_open"),
        [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
        [State("help-modal", "is_open")],
    )
    def toggle_help_modal(n1, n2, is_open):
        """
        Toggle the help modal visibility.
        """
        if n1 or n2:
            return not is_open
        return is_open

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

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            # Prepare charts for each tab
            charts = {}

            # Burndown chart (existing)
            burndown_fig, _, _ = create_forecast_plot(
                df=compute_cumulative_values(df, total_items, total_points)
                if not df.empty
                else df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
            )
            charts["tab-burndown"] = html.Div(
                [
                    # Burndown chart (removed export buttons)
                    dcc.Graph(
                        id="forecast-graph",
                        figure=burndown_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "600px"},
                    ),
                ]
            )

            # Weekly items chart with forecast
            items_fig = create_weekly_items_chart(
                statistics, date_range_weeks, pert_factor
            )
            # Calculate trend indicators for items
            items_trend = calculate_performance_trend(statistics, "no_items", 4)

            charts["tab-items"] = html.Div(
                [
                    # Date range selector for items chart
                    html.Div(
                        [
                            html.Label(
                                "Show data for last:", className="mr-2 font-weight-bold"
                            ),
                            dcc.Slider(
                                id={"type": "date-range-slider", "tab": "items"},
                                min=4,
                                max=52,
                                step=4,
                                value=date_range_weeks or 24,
                                marks={
                                    4: "4 weeks",
                                    12: "12 weeks",
                                    24: "24 weeks",
                                    52: "All",
                                },
                                className="mb-4",
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Performance trend indicator
                    html.Div(
                        [create_trend_indicator(items_trend, "Items")], className="mb-4"
                    ),
                    # Consolidated items weekly chart with forecast
                    dcc.Graph(
                        id="items-chart",
                        figure=items_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "600px"},
                    ),
                ]
            )

            # Weekly points chart with forecast
            points_fig = create_weekly_points_chart(
                statistics, date_range_weeks, pert_factor
            )
            # Calculate trend indicators for points
            points_trend = calculate_performance_trend(statistics, "no_points", 4)

            charts["tab-points"] = html.Div(
                [
                    # Date range selector for points chart
                    html.Div(
                        [
                            html.Label(
                                "Show data for last:", className="mr-2 font-weight-bold"
                            ),
                            dcc.Slider(
                                id={"type": "date-range-slider", "tab": "points"},
                                min=4,
                                max=52,
                                step=4,
                                value=date_range_weeks or 24,
                                marks={
                                    4: "4 weeks",
                                    12: "12 weeks",
                                    24: "24 weeks",
                                    52: "All",
                                },
                                className="mb-4",
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Performance trend indicator
                    html.Div(
                        [create_trend_indicator(points_trend, "Points")],
                        className="mb-4",
                    ),
                    # Consolidated points weekly chart with forecast
                    dcc.Graph(
                        id="points-chart",
                        figure=points_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "600px"},
                    ),
                ]
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

    # Replace the previous update_date_range callback with this pattern-matching callback
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
        prop_id = trigger["prop_id"]
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
                        .agg(week_start=("date", "min"), items=("no_items", "sum"))
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
                        .agg(week_start=("date", "min"), points=("no_points", "sum"))
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
