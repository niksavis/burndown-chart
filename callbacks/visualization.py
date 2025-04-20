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
    create_project_summary_card,
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
        [
            Output("forecast-graph", "figure"),
            Output("project-dashboard-pert-content", "children"),
        ],
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
        """Update the forecast graph and PERT information when settings or statistics change."""
        # Get context to see which input triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Get triggered input ID
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Validate inputs
        if settings is None or statistics is None:
            raise PreventUpdate

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
        fig, pert_data = create_forecast_plot(
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

        return fig, project_dashboard_pert_info

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
            # Get the data_points_count setting
            data_points_count = settings.get("data_points_count")

            # Convert statistics to DataFrame
            df = pd.DataFrame(statistics)

            # Prepare charts for each tab
            charts = {}

            # Burndown chart (existing)
            burndown_fig, _ = create_forecast_plot(
                df=compute_cumulative_values(df, total_items, total_points)
                if not df.empty
                else df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
                data_points_count=data_points_count,  # Pass the data_points_count parameter
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


def register_loading_callbacks(app):
    """
    Register callbacks that demonstrate loading states.

    Args:
        app: Dash application instance
    """
    from dash import Input, Output, State, callback_context
    from ui.styles import (
        create_spinner,
        create_skeleton_loader,
        create_content_placeholder,
    )
    import time
    from dash import html
    import dash_bootstrap_components as dbc

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
        from visualization.charts import create_chart_with_loading

        try:
            # In a real implementation, we would pass this to create_forecast_plot
            from visualization.charts import create_forecast_plot
            from dash import dcc
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
            from ui.components import create_lazy_loading_tabs

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
