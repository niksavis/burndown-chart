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
    create_combined_weekly_chart,
    create_weekly_items_forecast_chart,
    create_weekly_points_forecast_chart,
    empty_figure,
)
from ui import (
    create_pert_info_table,
    create_tab_content,
    create_trend_indicator,
    create_export_buttons,
    create_team_capacity_card,
    create_capacity_chart_card,
)
from data.capacity import CapacityManager

# Create a global instance of the capacity manager
capacity_manager = CapacityManager()

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

    # Add capacity metrics callback
    @app.callback(
        Output("capacity-metrics-container", "children"),
        [Input("update-capacity-button", "n_clicks")],
        [
            State("team-members-input", "value"),
            State("hours-per-member-input", "value"),
            State("hours-per-point-input", "value"),
            State("hours-per-item-input", "value"),
            State("include-weekends-input", "value"),
            State("current-statistics", "data"),
        ],
    )
    def update_capacity_metrics(
        n_clicks,
        team_members,
        hours_per_member,
        hours_per_point,
        hours_per_item,
        include_weekends,
        statistics,
    ):
        """
        Update capacity metrics when capacity settings change.
        """
        if n_clicks is None:
            raise PreventUpdate

        # Validate inputs
        if not team_members or not hours_per_member:
            return html.Div(
                "Please enter team members and hours per member",
                className="text-danger",
            )

        # Update capacity manager
        capacity_manager.set_capacity_parameters(
            team_members,
            hours_per_member,
            hours_per_point,
            hours_per_item,
            include_weekends,
        )

        # Calculate capacity metrics from historical data
        stats_df = pd.DataFrame(statistics) if statistics else pd.DataFrame()
        capacity_metrics = capacity_manager.calculate_capacity_from_stats(stats_df)

        # Total team capacity per week
        total_weekly_capacity = team_members * hours_per_member

        # Create metrics display
        return html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Total Weekly Capacity",
                                            className="card-title",
                                        ),
                                        html.H3(
                                            f"{total_weekly_capacity} hours",
                                            className="text-primary",
                                        ),
                                        html.P(
                                            f"Team of {team_members} with {hours_per_member} hours each",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                                className="text-center mb-3",
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Weekly Story Points Capacity",
                                            className="card-title",
                                        ),
                                        html.H3(
                                            f"{capacity_metrics['weekly_points_capacity']:.1f} points",
                                            className="text-warning",
                                        ),
                                        html.P(
                                            f"{capacity_metrics['avg_hours_per_point']:.1f} hours per point (est.)",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                                className="text-center mb-3",
                            ),
                            md=6,
                        ),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5(
                                            "Weekly Items Capacity",
                                            className="card-title",
                                        ),
                                        html.H3(
                                            f"{capacity_metrics['weekly_items_capacity']:.1f} items",
                                            className="text-info",
                                        ),
                                        html.P(
                                            f"{capacity_metrics['avg_hours_per_item']:.1f} hours per item (est.)",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                                className="text-center mb-3",
                            ),
                            md=6,
                        ),
                        dbc.Col(
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H5("Working Days", className="card-title"),
                                        html.H3(
                                            "5 days/week"
                                            if not include_weekends
                                            else "7 days/week",
                                            className="text-success",
                                        ),
                                        html.P(
                                            "Including weekends"
                                            if include_weekends
                                            else "Excluding weekends",
                                            className="card-text",
                                        ),
                                    ]
                                ),
                                className="text-center mb-3",
                            ),
                            md=6,
                        ),
                    ]
                ),
            ]
        )

    # Add capacity chart callback
    @app.callback(
        Output("capacity-chart", "figure"),
        [
            Input("capacity-metrics-container", "children"),
            Input("current-settings", "data"),
            Input("current-statistics", "data"),
            Input("update-capacity-button", "n_clicks"),
        ],
        [
            State("team-members-input", "value"),
            State("hours-per-member-input", "value"),
            State("hours-per-point-input", "value"),
            State("hours-per-item-input", "value"),
            State("include-weekends-input", "value"),
        ],
    )
    def update_capacity_chart(
        capacity_metrics,
        settings,
        statistics,
        n_clicks,
        team_members,
        hours_per_member,
        hours_per_point,
        hours_per_item,
        include_weekends,
    ):
        """
        Update the capacity chart visualization.
        """
        if not settings or not statistics or n_clicks is None:
            raise PreventUpdate

        if not team_members or not hours_per_member:
            # Create empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="Please update capacity settings to generate chart",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            return fig

        # Create DataFrame from statistics
        stats_df = pd.DataFrame(statistics)
        if stats_df.empty:
            # Create empty figure with message
            fig = go.Figure()
            fig.add_annotation(
                text="No statistics data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16),
            )
            return fig

        # Convert date strings to datetime objects
        stats_df["date"] = pd.to_datetime(stats_df["date"])

        # Sort by date
        stats_df = stats_df.sort_values("date")

        # Calculate cumulative values
        stats_df["cumulative_items"] = stats_df["no_items"].cumsum()
        stats_df["cumulative_points"] = stats_df["no_points"].cumsum()

        # Get remaining items and points
        total_items = settings["total_items"]
        total_points = settings["total_points"]
        remaining_items = total_items - stats_df["cumulative_items"].max()
        remaining_points = total_points - stats_df["cumulative_points"].max()

        # Generate capacity forecast
        start_date = datetime.now()
        end_date = datetime.strptime(settings["deadline"], "%Y-%m-%d")

        # Generate capacity forecast
        forecast = capacity_manager.generate_capacity_forecast(
            start_date, end_date, remaining_items, remaining_points
        )

        capacity_data = forecast["capacity_data"]

        # Create figure
        fig = go.Figure()

        # Add historical burndown data
        fig.add_scatter(
            x=stats_df["date"],
            y=total_items - stats_df["cumulative_items"],
            mode="lines+markers",
            name="Remaining Items (historical)",
            line=dict(color="rgba(0, 99, 178, 1)", width=3),
            showlegend=True,
        )

        fig.add_scatter(
            x=stats_df["date"],
            y=total_points - stats_df["cumulative_points"],
            mode="lines+markers",
            name="Remaining Points (historical)",
            line=dict(color="rgba(255, 127, 14, 1)", width=3),
            showlegend=True,
        )

        # Add capacity data for items
        if capacity_data["cumulative_items_capacity"].max() > 0:
            # Calculate remaining items based on capacity
            items_capacity_dates = capacity_data["date"]
            items_capacity = capacity_data["cumulative_items_capacity"]

            remaining_items_with_capacity = [
                max(0, remaining_items - val) for val in items_capacity
            ]

            fig.add_scatter(
                x=items_capacity_dates,
                y=remaining_items_with_capacity,
                mode="lines",
                name="Remaining Items (with capacity)",
                line=dict(color="rgba(0, 99, 178, 0.7)", width=2, dash="dot"),
                showlegend=True,
            )

            # Add vertical line at items completion date
            if forecast["items_completion_date"]:
                fig.add_shape(
                    type="line",
                    x0=forecast["items_completion_date"],
                    y0=0,
                    x1=forecast["items_completion_date"],
                    y1=remaining_items,
                    line=dict(color="rgba(0, 99, 178, 0.5)", width=2, dash="dash"),
                )
                fig.add_annotation(
                    x=forecast["items_completion_date"],
                    y=remaining_items / 2,
                    text=f"Items<br>Complete<br>{forecast['items_completion_date'].strftime('%Y-%m-%d')}",
                    showarrow=False,
                    font=dict(color="rgba(0, 99, 178, 1)"),
                    align="center",
                )

        # Add capacity data for points
        if capacity_data["cumulative_points_capacity"].max() > 0:
            # Calculate remaining points based on capacity
            points_capacity_dates = capacity_data["date"]
            points_capacity = capacity_data["cumulative_points_capacity"]

            remaining_points_with_capacity = [
                max(0, remaining_points - val) for val in points_capacity
            ]

            fig.add_scatter(
                x=points_capacity_dates,
                y=remaining_points_with_capacity,
                mode="lines",
                name="Remaining Points (with capacity)",
                line=dict(color="rgba(255, 127, 14, 0.7)", width=2, dash="dot"),
                showlegend=True,
            )

            # Add vertical line at points completion date
            if forecast["points_completion_date"]:
                fig.add_shape(
                    type="line",
                    x0=forecast["points_completion_date"],
                    y0=0,
                    x1=forecast["points_completion_date"],
                    y1=remaining_points,
                    line=dict(color="rgba(255, 127, 14, 0.5)", width=2, dash="dash"),
                )
                fig.add_annotation(
                    x=forecast["points_completion_date"],
                    y=remaining_points / 2,
                    text=f"Points<br>Complete<br>{forecast['points_completion_date'].strftime('%Y-%m-%d')}",
                    showarrow=False,
                    font=dict(color="rgba(255, 127, 14, 1)"),
                    align="center",
                )

        # Add deadline line
        deadline_date = datetime.strptime(settings["deadline"], "%Y-%m-%d")
        fig.add_shape(
            type="line",
            x0=deadline_date,
            y0=0,
            x1=deadline_date,
            y1=max(remaining_items, remaining_points) * 1.1,
            line=dict(color="red", width=2, dash="dash"),
        )
        fig.add_annotation(
            x=deadline_date,
            y=max(remaining_items, remaining_points) * 1.05,
            text=f"Deadline: {settings['deadline']}",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
            font=dict(color="red", size=12),
        )

        # Update layout
        fig.update_layout(
            title="Team Capacity vs. Project Burndown",
            xaxis_title="Date",
            yaxis_title="Remaining Work",
            legend=dict(x=0.01, y=0.99, bgcolor="rgba(255, 255, 255, 0.8)"),
            margin=dict(l=60, r=30, t=60, b=60),
            hovermode="closest",
            plot_bgcolor="rgba(240, 240, 240, 0.1)",
        )

        return fig

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

            # Weekly items chart
            items_fig = create_weekly_items_chart(statistics, date_range_weeks)
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
                    # Items weekly chart (removed export buttons)
                    dcc.Graph(
                        id="items-chart",
                        figure=items_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "500px"},
                    ),
                    # Items weekly forecast chart
                    html.Div(
                        [
                            html.H5("Forecast for Next 4 Weeks", className="mt-4 mb-3"),
                            # Removed export buttons for forecast chart
                            dcc.Graph(
                                id="items-forecast-chart",
                                figure=create_weekly_items_forecast_chart(
                                    statistics, pert_factor, date_range_weeks
                                ),
                                config={"displayModeBar": True, "responsive": True},
                                style={"height": "500px"},
                            ),
                        ]
                    ),
                ]
            )

            # Weekly points chart
            points_fig = create_weekly_points_chart(statistics, date_range_weeks)
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
                    # Points weekly chart (removed export buttons)
                    dcc.Graph(
                        id="points-chart",
                        figure=points_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "500px"},
                    ),
                    # Points weekly forecast chart
                    html.Div(
                        [
                            html.H5("Forecast for Next 4 Weeks", className="mt-4 mb-3"),
                            # Removed export buttons for forecast chart
                            dcc.Graph(
                                id="points-forecast-chart",
                                figure=create_weekly_points_forecast_chart(
                                    statistics, pert_factor, date_range_weeks
                                ),
                                config={"displayModeBar": True, "responsive": True},
                                style={"height": "500px"},
                            ),
                        ]
                    ),
                ]
            )

            # Combined view chart
            combined_fig = create_combined_weekly_chart(statistics, date_range_weeks)
            # Calculate trend indicators for both items and points
            items_trend = calculate_performance_trend(statistics, "no_items", 4)
            points_trend = calculate_performance_trend(statistics, "no_points", 4)

            charts["tab-combined"] = html.Div(
                [
                    # Date range selector for combined chart
                    html.Div(
                        [
                            html.Label(
                                "Show data for last:", className="mr-2 font-weight-bold"
                            ),
                            dcc.Slider(
                                id={"type": "date-range-slider", "tab": "combined"},
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
                    # Performance trend indicators (side by side)
                    dbc.Row(
                        [
                            dbc.Col(
                                [create_trend_indicator(items_trend, "Items")],
                                md=6,
                                className="mb-3",
                            ),
                            dbc.Col(
                                [create_trend_indicator(points_trend, "Points")],
                                md=6,
                                className="mb-3",
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Removed export buttons
                    # Combined weekly chart
                    dcc.Graph(
                        id="combined-chart",
                        figure=combined_fig,
                        config={"displayModeBar": True, "responsive": True},
                        style={"height": "600px"},
                    ),
                ]
            )

            # Create content for the active tab

            # Add capacity tab content
            charts["tab-capacity"] = html.Div(
                [
                    # Create capacity settings card
                    create_team_capacity_card(),
                    # Create capacity chart card
                    create_capacity_chart_card(),
                ]
            )

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
        "combined",
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

                elif chart_id == "combined":
                    # Export both weekly items and points data
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
                            items=("no_items", "sum"),
                            points=("no_points", "sum"),
                        )
                        .reset_index()
                    )

                    # Filter by date range if specified
                    if date_range_weeks:
                        weekly_df = weekly_df.sort_values("week_start", ascending=False)
                        weekly_df = weekly_df.head(date_range_weeks)
                        weekly_df = weekly_df.sort_values("week_start")

                    df = weekly_df
                    filename = f"combined_weekly_data_{current_time}.csv"

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

    # Add continue iteration modal callbacks
    @app.callback(
        Output("continue-iteration-modal", "is_open"),
        [
            Input("show-continue-iteration", "n_clicks"),
            Input("continue-iteration", "n_clicks"),
            Input("cancel-iteration", "n_clicks"),
        ],
        [State("continue-iteration-modal", "is_open")],
    )
    def toggle_continue_iteration_modal(n1, n2, n3, is_open):
        """
        Toggle the visibility of the continue iteration modal.
        """
        ctx = callback_context
        if not ctx.triggered:
            return is_open

        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "show-continue-iteration" and n1:
            return True
        elif button_id in ["continue-iteration", "cancel-iteration"]:
            return False
        return is_open

    @app.callback(
        Output("iteration-trigger", "data"),
        [Input("continue-iteration", "n_clicks")],
        [State("iteration-trigger", "data")],
    )
    def handle_continue_iteration(n_clicks, current_count):
        """
        Handle the user's decision to continue iteration.
        """
        if not n_clicks or n_clicks == 0:
            # Initial state, don't trigger anything
            return current_count or 0

        # Increment iteration counter when continue is clicked
        return (current_count or 0) + 1

    @app.callback(
        Output("show-continue-iteration", "n_clicks"),
        [Input("calculation-results", "modified_timestamp")],
        [State("show-continue-iteration", "n_clicks")],
    )
    def trigger_continue_iteration_prompt(calc_results_ts, current_clicks):
        """
        Trigger the continue iteration modal after calculations are completed.
        This shows the modal asking the user if they want to continue iterating.
        """
        if not calc_results_ts:
            raise PreventUpdate

        # Increment clicks to trigger the modal
        return (current_clicks or 0) + 1

    @app.callback(
        [
            Output("capacity-forecast-graph", "figure", allow_duplicate=True),
        ],
        [
            Input("team-members-input", "value"),
            Input("hours-per-member-input", "value"),
            Input("include-weekends-switch", "value"),
            Input("current-statistics", "data"),
        ],
        [
            State("current-settings", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_capacity_forecast(
        team_members, hours_per_member, include_weekends, stats_data, settings
    ):
        """
        Update the capacity forecast visualization based on team parameters and statistics.

        Args:
            team_members: Number of team members
            hours_per_member: Hours per team member per week
            include_weekends: Whether to include weekends in the calculation
            stats_data: Dictionary with statistics data
            settings: Dictionary with current settings

        Returns:
            Plotly figure for capacity forecast
        """
        # Create default figure if no data
        if not stats_data or not team_members or not hours_per_member:
            return [empty_figure("No capacity data available")]

        try:
            # Initialize capacity manager
            from data.capacity import CapacityManager

            capacity_manager = CapacityManager()

            # Set capacity parameters
            capacity_manager.set_capacity_parameters(
                team_members=team_members,
                hours_per_member=hours_per_member,
                include_weekends=bool(include_weekends),
            )

            # Convert the statistics data to a pandas DataFrame
            stats_df = pd.DataFrame(stats_data)
            if not stats_df.empty:
                # Ensure date column is datetime and numeric columns are numbers
                stats_df["date"] = pd.to_datetime(stats_df["date"])
                stats_df["no_items"] = pd.to_numeric(stats_df["no_items"])
                stats_df["no_points"] = pd.to_numeric(stats_df["no_points"])

            # Calculate capacity metrics from stats
            capacity_metrics = capacity_manager.calculate_capacity_from_stats(stats_df)

            # Generate capacity forecast for next 6 weeks
            forecast_weeks = settings.get("forecast_weeks", 6) if settings else 6

            # We need to handle the forecast differently based on the function's expected parameters
            # Check if the generate_capacity_forecast accepts a weeks_to_forecast parameter
            import inspect

            forecast_params = inspect.signature(
                capacity_manager.generate_capacity_forecast
            ).parameters

            if "weeks_to_forecast" in forecast_params:
                # Call with weeks_to_forecast parameter
                forecast_data = capacity_manager.generate_capacity_forecast(
                    stats_df, weeks_to_forecast=forecast_weeks
                )
            else:
                # Call with start_date, end_date, total_items, total_points parameters
                from datetime import datetime, timedelta

                start_date = datetime.now().date()
                end_date = start_date + timedelta(weeks=forecast_weeks)

                # Calculate total items and points remaining
                total_items = 0
                total_points = 0
                if not stats_df.empty:
                    total_items = stats_df["no_items"].sum()
                    total_points = stats_df["no_points"].sum()

                forecast_data = capacity_manager.generate_capacity_forecast(
                    start_date=start_date,
                    end_date=end_date,
                    total_items=total_items,
                    total_points=total_points,
                )

            # Handle different forecast_data structures based on what's returned
            if isinstance(forecast_data, dict) and "weekly_forecast" in forecast_data:
                # New structure with weekly_forecast DataFrame
                weekly_forecast = forecast_data["weekly_forecast"]

                # Create forecast figure
                fig = go.Figure()

                # Add capacity line
                weekly_capacity = team_members * hours_per_member
                fig.add_trace(
                    go.Scatter(
                        x=weekly_forecast["date"]
                        if "date" in weekly_forecast
                        else weekly_forecast.index,
                        y=[weekly_capacity] * len(weekly_forecast),
                        mode="lines",
                        name="Available Capacity",
                        line=dict(color="#28a745", width=2, dash="dash"),
                    )
                )

                # Add forecast line
                fig.add_trace(
                    go.Scatter(
                        x=weekly_forecast["date"]
                        if "date" in weekly_forecast
                        else weekly_forecast.index,
                        y=weekly_forecast["required_hours"],
                        mode="lines+markers",
                        name="Forecasted Requirement",
                        line=dict(color="#17a2b8", width=3),
                    )
                )

            else:
                # Old structure with list/dict of weeks
                # Create forecast figure
                fig = go.Figure()

                # Add capacity line
                weekly_capacity = team_members * hours_per_member
                fig.add_trace(
                    go.Scatter(
                        x=list(range(forecast_weeks + 1)),
                        y=[weekly_capacity] * (forecast_weeks + 1),
                        mode="lines",
                        name="Available Capacity",
                        line=dict(color="#28a745", width=2, dash="dash"),
                    )
                )

                # Add forecast line - adapt to whatever structure is returned
                if isinstance(forecast_data, list):
                    y_values = [week.get("required_hours", 0) for week in forecast_data]
                elif isinstance(forecast_data, dict):
                    y_values = [
                        forecast_data.get(week, {}).get("required_hours", 0)
                        for week in range(forecast_weeks + 1)
                    ]
                else:
                    y_values = [0] * (forecast_weeks + 1)

                fig.add_trace(
                    go.Scatter(
                        x=list(range(forecast_weeks + 1)),
                        y=y_values,
                        mode="lines+markers",
                        name="Forecasted Requirement",
                        line=dict(color="#17a2b8", width=3),
                    )
                )

            # Configure layout
            fig.update_layout(
                title="Capacity Forecast",
                xaxis_title="Time",
                yaxis_title="Hours",
                hovermode="x unified",
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
                margin=dict(l=40, r=40, t=60, b=40),
            )

            return [fig]

        except Exception as e:
            import traceback

            print(f"Error updating capacity forecast: {e}")
            traceback.print_exc()
            return [empty_figure(f"Error: {str(e)}")]

    @app.callback(
        [
            Output("tab-capacity-content", "children"),
        ],
        [
            Input("current-statistics", "data"),
            Input("team-members-input", "value"),
            Input("hours-per-member-input", "value"),
            Input("include-weekends-switch", "value"),
        ],
        [
            State("current-settings", "data"),
        ],
    )
    def update_capacity_tab(
        stats_data, team_members, hours_per_member, include_weekends, settings
    ):
        """
        Update the team capacity tab content.

        Args:
            stats_data: Dictionary with statistics data
            team_members: Number of team members
            hours_per_member: Hours per team member per week
            include_weekends: Whether to include weekends in the calculation
            settings: Dictionary with current settings

        Returns:
            Updated capacity tab content
        """
        from ui.cards import create_team_capacity_card

        # Update settings with current values
        if not settings:
            settings = {}

        current_settings = {
            "team_members": team_members
            if team_members is not None
            else settings.get("team_members", 1),
            "hours_per_member": hours_per_member
            if hours_per_member is not None
            else settings.get("hours_per_member", 40),
            "include_weekends": bool(include_weekends),
        }

        try:
            # Initialize capacity manager
            from data.capacity import CapacityManager

            capacity_manager = CapacityManager()

            # Set capacity parameters
            capacity_manager.set_capacity_parameters(
                team_members=current_settings["team_members"],
                hours_per_member=current_settings["hours_per_member"],
                include_weekends=current_settings["include_weekends"],
            )

            # Convert stats_data to DataFrame before calculating metrics
            if stats_data:
                stats_df = pd.DataFrame(stats_data)
                # Ensure date column is datetime and numeric columns are numbers
                if not stats_df.empty:
                    stats_df["date"] = pd.to_datetime(stats_df["date"])
                    stats_df["no_items"] = pd.to_numeric(stats_df["no_items"])
                    stats_df["no_points"] = pd.to_numeric(stats_df["no_points"])

                # Calculate capacity metrics from stats DataFrame
                capacity_metrics = capacity_manager.calculate_capacity_from_stats(
                    stats_df
                )
            else:
                capacity_metrics = None

            # Create capacity card
            capacity_card = create_team_capacity_card(
                capacity_metrics, current_settings
            )

            return [capacity_card]

        except Exception as e:
            import traceback

            print(f"Error updating capacity tab: {e}")
            traceback.print_exc()
            return [
                html.Div(
                    [
                        html.H4("Error Loading Capacity Data"),
                        html.P(f"An error occurred: {str(e)}"),
                        html.Hr(),
                        create_team_capacity_card(None, current_settings),
                    ]
                )
            ]
