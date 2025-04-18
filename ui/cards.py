"""
UI Cards Module

This module provides card components that make up the main UI sections
of the application, such as the forecast graph card, info card, etc.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pandas as pd

# Import from other modules
from configuration import HELP_TEXTS, COLOR_PALETTE
from visualization import empty_figure

# Fix circular import issue - import directly from components instead of ui
from ui.components import create_info_tooltip, create_pert_info_table

#######################################################################
# CARD COMPONENTS
#######################################################################


def create_forecast_graph_card():
    """
    Create the forecast graph card component with customized download filename.

    Returns:
        Dash Card component with the forecast graph
    """
    # Generate the current date for the filename
    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Forecast Graph", className="d-inline"),
                    create_info_tooltip(
                        "forecast-graph", HELP_TEXTS["forecast_explanation"]
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="forecast-graph",
                        style={"height": "650px"},
                        config={
                            # Only specify the filename, let Plotly handle the rest of the export settings
                            "toImageButtonOptions": {
                                "filename": default_filename,
                            },
                        },
                    ),
                ]
            ),
        ],
        className="mb-3 shadow-sm",
    )


def create_forecast_info_card():
    """
    Create the forecast methodology information card component with enhanced explanations.

    Returns:
        Dash Card component with detailed forecast methodology explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "forecast-info",
                        "Detailed explanation of how to interpret the forecast graph.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Forecast Methodology: "),
                                    "PERT (Program Evaluation and Review Technique) estimation based on your historical performance data. ",
                                    "The forecast uses three scenarios:",
                                ],
                                className="mb-2",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Teal",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Gold",
                                                style={
                                                    "color": "rgb(184, 134, 11)",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your best performance periods (20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Blue",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Orange",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your average performance (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Purple",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for items, ",
                                            html.Span(
                                                "Brown",
                                                style={
                                                    "color": "rgb(165, 42, 42)",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " for points. Based on your slowest performance periods (80% confidence level).",
                                        ]
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Reading the Graph: "),
                                    "Solid lines show historical data. Dashed and dotted lines show forecasts. ",
                                    "Where these lines cross zero indicates estimated completion dates.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Color Coding for Estimates: "),
                                    "Estimated days appear in ",
                                    html.Span(
                                        "green",
                                        style={"color": "green", "fontWeight": "bold"},
                                    ),
                                    " when on track to meet the deadline, and in ",
                                    html.Span(
                                        "red",
                                        style={"color": "red", "fontWeight": "bold"},
                                    ),
                                    " when at risk of missing the deadline. The red vertical line represents your deadline date.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-3",  # Slightly more padding for better readability
            ),
        ],
        className="mb-3 shadow-sm",
    )


def create_pert_analysis_card():
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("PERT Analysis", className="d-inline"),
                    create_info_tooltip(
                        "pert-info",
                        "PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(id="pert-info-container", className="text-center"),
                ]
            ),
        ],
        className="mb-3 h-100 shadow-sm",
    )


def create_input_parameters_card(
    current_settings, avg_points_per_item, estimated_total_points
):
    """
    Create the input parameters card component with improved organization and visual hierarchy.

    Args:
        current_settings: Dictionary with current application settings
        avg_points_per_item: Current average points per item
        estimated_total_points: Estimated total points

    Returns:
        Dash Card component for input parameters
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Input Parameters", className="d-inline"),
                    create_info_tooltip(
                        "parameters",
                        "Change these values to adjust your project forecast.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    # Project Timeline Section
                    html.Div(
                        [
                            html.H5(
                                "Project Timeline", className="mb-3 border-bottom pb-2"
                            ),
                            # First row: Deadline and PERT Factor (swapped and no padding)
                            dbc.Row(
                                [
                                    # Deadline - now first
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Deadline:",
                                                    create_info_tooltip(
                                                        "deadline",
                                                        HELP_TEXTS["deadline"],
                                                    ),
                                                ]
                                            ),
                                            dcc.DatePickerSingle(
                                                id="deadline-picker",
                                                date=current_settings["deadline"],
                                                display_format="YYYY-MM-DD",
                                                first_day_of_week=1,
                                                show_outside_days=True,
                                                with_portal=False,
                                                with_full_screen_portal=False,
                                                placeholder="Select deadline date",
                                                persistence=True,
                                                min_date_allowed=datetime.now().strftime(
                                                    "%Y-%m-%d"
                                                ),
                                                style={
                                                    "width": "100%",
                                                    "border-radius": "0.25rem",
                                                },
                                            ),
                                        ],
                                        width=12,
                                        md=4,  # Keep same width
                                    ),
                                    # PERT Factor - directly adjacent to Deadline (removed spacer)
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "PERT Factor:",
                                                    create_info_tooltip(
                                                        "pert-factor",
                                                        HELP_TEXTS["pert_factor"],
                                                    ),
                                                ]
                                            ),
                                            dcc.Slider(
                                                id="pert-factor-slider",
                                                min=3,
                                                max=15,
                                                value=current_settings["pert_factor"],
                                                marks={
                                                    i: str(i) for i in range(3, 16, 2)
                                                },
                                                step=1,
                                                tooltip={
                                                    "placement": "bottom",
                                                    "always_visible": True,
                                                },
                                            ),
                                        ],
                                        width=12,
                                        md=8,  # Expanded from 6 to 8 to fill the space
                                    ),
                                ],
                                className="mb-3",  # Keep margin below this row
                            ),
                            # Second row: Data Points to Include (full width)
                            dbc.Row(
                                [
                                    # Data Points - now full width
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Data Points to Include:",
                                                    create_info_tooltip(
                                                        "data-points-count",
                                                        HELP_TEXTS["data_points_count"],
                                                    ),
                                                ]
                                            ),
                                            dcc.Slider(
                                                id="data-points-input",
                                                min=current_settings["pert_factor"] * 2,
                                                max=10,
                                                value=current_settings.get(
                                                    "data_points_count",
                                                    current_settings["pert_factor"] * 2,
                                                ),
                                                marks=None,
                                                step=1,
                                                tooltip={
                                                    "placement": "bottom",
                                                    "always_visible": True,
                                                },
                                            ),
                                            html.Small(
                                                id="data-points-info",
                                                children="Using all available data points",
                                                className="text-muted mt-1 d-block",
                                            ),
                                        ],
                                        width=12,  # Full width in all screen sizes
                                    ),
                                ],
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Project Scope Section - unchanged
                    html.Div(
                        [
                            html.H5(
                                "Project Scope", className="mb-3 border-bottom pb-2"
                            ),
                            # Items (Estimated and Total) in one row
                            dbc.Row(
                                [
                                    # Estimated Items
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Remaining Estimated Items:",
                                                    create_info_tooltip(
                                                        "estimated-items",
                                                        HELP_TEXTS["estimated_items"],
                                                    ),
                                                ]
                                            ),
                                            dbc.Input(
                                                id="estimated-items-input",
                                                type="number",
                                                value=current_settings[
                                                    "estimated_items"
                                                ],
                                                min=0,
                                                step=1,
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                    ),
                                    # Total Items
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Remaining Total Items:",
                                                    create_info_tooltip(
                                                        "total-items",
                                                        HELP_TEXTS["total_items"],
                                                    ),
                                                ]
                                            ),
                                            dbc.Input(
                                                id="total-items-input",
                                                type="number",
                                                value=current_settings["total_items"],
                                                min=0,
                                                step=1,
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Points (Estimated and Total) in one row
                            dbc.Row(
                                [
                                    # Estimated Points
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Remaining Estimated Points:",
                                                    create_info_tooltip(
                                                        "estimated-points",
                                                        HELP_TEXTS["estimated_points"],
                                                    ),
                                                ]
                                            ),
                                            dbc.Input(
                                                id="estimated-points-input",
                                                type="number",
                                                value=current_settings[
                                                    "estimated_points"
                                                ],
                                                min=0,
                                                step=1,
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                    ),
                                    # Total Points (Calculated)
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Remaining Total Points (calculated):",
                                                    create_info_tooltip(
                                                        "total-points",
                                                        HELP_TEXTS["total_points"],
                                                    ),
                                                ]
                                            ),
                                            dbc.InputGroup(
                                                [
                                                    dbc.Input(
                                                        id="total-points-display",
                                                        value=f"{estimated_total_points:.0f}",
                                                        disabled=True,
                                                        style={
                                                            "backgroundColor": "#f8f9fa"
                                                        },
                                                    ),
                                                    dbc.InputGroupText(
                                                        html.I(
                                                            className="fas fa-calculator"
                                                        ),
                                                    ),
                                                ]
                                            ),
                                            html.Small(
                                                id="points-calculation-info",
                                                children=[
                                                    f"Using {avg_points_per_item:.1f} points per remaining item for calculation"
                                                ],
                                                className="text-muted mt-1 d-block",
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                    ),
                                ],
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Data Import Section
                    html.Div(
                        [
                            html.H5("Data Import", className="mb-3 border-bottom pb-2"),
                            # CSV Upload
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    "Upload Statistics CSV:",
                                                    create_info_tooltip(
                                                        "csv-upload",
                                                        HELP_TEXTS["csv_format"],
                                                    ),
                                                ]
                                            ),
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-file-upload mr-2"
                                                        ),
                                                        "Drag and Drop or ",
                                                        html.A("Select CSV File"),
                                                    ]
                                                ),
                                                style={
                                                    "width": "100%",
                                                    "height": "60px",
                                                    "lineHeight": "60px",
                                                    "borderWidth": "1px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "5px",
                                                    "textAlign": "center",
                                                },
                                                multiple=False,
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ]
            ),
        ],
        className="mb-3 h-100 shadow-sm",
    )


def create_statistics_data_card(current_statistics):
    """
    Create the statistics data card component.

    Args:
        current_statistics: List of dictionaries containing current statistics data

    Returns:
        Dash Card component for statistics data
    """
    from dash import dash_table
    from ui.components import (
        create_export_buttons,
    )  # Import the export buttons component

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Statistics Data", className="d-inline"),
                    create_info_tooltip(
                        "statistics-data",
                        HELP_TEXTS["statistics_table"],
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    # Add the export buttons at the top of the card
                    create_export_buttons(statistics_data=current_statistics),
                    dash_table.DataTable(
                        id="statistics-table",
                        columns=[
                            {
                                "name": "Date (YYYY-MM-DD)",
                                "id": "date",
                                "type": "text",
                            },
                            {
                                "name": "Items Completed",
                                "id": "no_items",
                                "type": "numeric",
                            },
                            {
                                "name": "Points Completed",
                                "id": "no_points",
                                "type": "numeric",
                            },
                        ],
                        data=current_statistics,
                        editable=True,
                        row_deletable=True,
                        sort_action="native",
                        # Add default sorting by date, descending order (newest first)
                        sort_by=[
                            {
                                "column_id": "date",
                                "direction": "desc",
                            }
                        ],
                        # Add pagination
                        page_size=10,
                        page_action="native",
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "center",
                            "minWidth": "100px",
                            "padding": "10px",
                        },
                        style_header={
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "border": "1px solid #ddd",
                        },
                        style_data={
                            "border": "1px solid #ddd",
                        },
                        style_data_conditional=[
                            {
                                "if": {"row_index": "odd"},
                                "backgroundColor": "#f9f9f9",
                            }
                        ],
                        tooltip_data=[
                            {
                                column: {
                                    "value": "Click to edit",
                                    "type": "text",
                                }
                                for column in [
                                    "date",
                                    "no_items",
                                    "no_points",
                                ]
                            }
                            for _ in range(len(current_statistics))
                        ],
                        tooltip_duration=None,
                    ),
                    html.Div(
                        [
                            # Button for adding rows
                            dbc.Button(
                                [
                                    html.I(className="fas fa-plus mr-2"),
                                    "Add Row",
                                ],
                                id="add-row-button",
                                color="primary",
                                className="mt-3",
                            ),
                        ],
                        style={"textAlign": "center"},
                    ),
                ]
            ),
        ],
        className="shadow-sm",
    )


def create_project_status_card(statistics_df, settings):
    """
    Create a comprehensive project status card with metrics and indicators.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings

    Returns:
        A Dash card component for project status summary
    """
    try:
        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["no_items"].sum()) if not statistics_df.empty else 0
        )
        completed_points = (
            int(statistics_df["no_points"].sum()) if not statistics_df.empty else 0
        )

        # Calculate true project totals (completed + remaining)
        total_items = remaining_items + completed_items
        total_points = round(
            remaining_points + completed_points
        )  # Round to nearest integer
        remaining_points = round(
            remaining_points
        )  # Round remaining points to nearest integer

        # Calculate percentages based on true project totals
        items_percentage = (
            int((completed_items / total_items) * 100) if total_items > 0 else 0
        )
        points_percentage = (
            int((completed_points / total_points) * 100) if total_points > 0 else 0
        )

        # Check if percentages are similar (within 2% of each other)
        similar_percentages = abs(items_percentage - points_percentage) <= 2

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        # Create a copy of the DataFrame to avoid SettingWithCopyWarning
        recent_df = statistics_df.copy() if not statistics_df.empty else pd.DataFrame()

        # Convert to datetime to ensure proper week grouping
        if not recent_df.empty:
            # Use proper pandas assignment with .loc to avoid SettingWithCopyWarning
            recent_df.loc[:, "date"] = pd.to_datetime(recent_df["date"])
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            # Use tail(10) after assigning week and year columns
            recent_df = recent_df.tail(10)

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"no_items": "sum", "no_points": "sum"})
                .reset_index()
            )

            # Calculate metrics
            avg_weekly_items = weekly_data["no_items"].mean()
            avg_weekly_points = weekly_data["no_points"].mean()

            # Calculate coefficient of variation (CV = stdev / mean)
            std_weekly_items = weekly_data["no_items"].std()
            std_weekly_points = weekly_data["no_points"].std()

            cv_items = (
                (std_weekly_items / avg_weekly_items * 100)
                if avg_weekly_items > 0
                else 0
            )
            cv_points = (
                (std_weekly_points / avg_weekly_points * 100)
                if avg_weekly_points > 0
                else 0
            )

            # Calculate stability metrics (weeks with 0 or > 2x average)
            zero_item_weeks = len(weekly_data[weekly_data["no_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["no_points"] == 0])

            high_item_weeks = len(
                weekly_data[weekly_data["no_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["no_points"] > avg_weekly_points * 2]
            )

            # Calculate overall stability score (0-100)
            stability_score = max(
                0,
                100
                - cv_items * 0.5
                - cv_points * 0.5
                - zero_item_weeks * 10
                - zero_point_weeks * 10
                - high_item_weeks * 5
                - high_point_weeks * 5,
            )
            stability_score = min(100, max(0, stability_score))

            # Determine velocity consistency status
            if stability_score >= 80:
                stability_status = "Consistent"
                stability_color = "success"
                stability_icon = "fa-check-circle"
            elif stability_score >= 50:
                stability_status = "Moderate"
                stability_color = "warning"
                stability_icon = "fa-exclamation-circle"
            else:
                stability_status = "Variable"
                stability_color = "danger"
                stability_icon = "fa-times-circle"
        else:
            # Default values if no data is available
            avg_weekly_items = 0
            avg_weekly_points = 0
            stability_status = "Unknown"
            stability_color = "secondary"
            stability_icon = "fa-question-circle"

        # Calculate days of data available
        if not statistics_df.empty:
            if "date" in statistics_df.columns:
                earliest_date = pd.to_datetime(statistics_df["date"].min())
                latest_date = pd.to_datetime(statistics_df["date"].max())
                days_of_data = (
                    (latest_date - earliest_date).days + 1
                    if earliest_date and latest_date
                    else 0
                )
            else:
                days_of_data = 0
        else:
            days_of_data = 0

        import dash_bootstrap_components as dbc

        # Create the card component
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4("Project Status Summary", className="d-inline"),
                        create_info_tooltip(
                            "project-status",
                            "Summary of your project's current progress and metrics.",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        # Project Completion Stats Row
                        dbc.Row(
                            [
                                # Items Completion
                                dbc.Col(
                                    [
                                        html.H6("Items Completion"),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{items_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE["items"],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_items} of {total_items} items",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for items
                                        dbc.Progress(
                                            value=items_percentage,
                                            color="info",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                                # Points Completion
                                dbc.Col(
                                    [
                                        html.H6("Points Completion"),
                                        html.Div(
                                            [
                                                html.Span(
                                                    f"{points_percentage}%",
                                                    style={
                                                        "fontSize": "24px",
                                                        "fontWeight": "bold",
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        f"Completed: {completed_points} of {total_points} points",
                                                    ],
                                                    className="text-muted small",
                                                ),
                                            ],
                                            className="text-center mb-2",
                                        ),
                                        # Progress bar for points
                                        dbc.Progress(
                                            value=points_percentage,
                                            color="warning",
                                            className="mb-3",
                                            style={"height": "10px"},
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="mb-4",
                        ),
                        # Metrics Row
                        dbc.Row(
                            [
                                # Weekly Averages
                                dbc.Col(
                                    [
                                        html.H6("Weekly Averages", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-tasks me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "items"
                                                                ]
                                                            },
                                                        ),
                                                        f"{avg_weekly_items:.1f} items/week",
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-2",
                                                            style={
                                                                "color": COLOR_PALETTE[
                                                                    "points"
                                                                ]
                                                            },
                                                        ),
                                                        f"{avg_weekly_points:.1f} points/week",
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Velocity Stability
                                dbc.Col(
                                    [
                                        html.H6("Velocity Stability", className="mb-3"),
                                        html.Div(
                                            [
                                                html.I(
                                                    className=f"fas {stability_icon} me-2",
                                                    style={
                                                        "color": f"var(--bs-{stability_color})"
                                                    },
                                                ),
                                                html.Span(
                                                    stability_status,
                                                    style={
                                                        "color": f"var(--bs-{stability_color})",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                            ],
                                            className="d-flex align-items-center ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                                # Dataset Info
                                dbc.Col(
                                    [
                                        html.H6("Dataset Info", className="mb-3"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-2 text-secondary"
                                                        ),
                                                        f"{days_of_data} days of data",
                                                    ],
                                                    className="d-flex align-items-center mb-2",
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-table me-2 text-secondary"
                                                        ),
                                                        f"{len(statistics_df) if not statistics_df.empty else 0} data points",
                                                    ],
                                                    className="d-flex align-items-center",
                                                ),
                                            ],
                                            className="ps-3",
                                        ),
                                    ],
                                    md=4,
                                ),
                            ],
                        ),
                    ],
                    className="py-4",
                ),
            ],
            className="mb-4 shadow-sm",
        )

    except Exception as e:
        # Return an error card if something goes wrong
        import dash_bootstrap_components as dbc
        from dash import html

        return dbc.Card(
            [
                dbc.CardHeader(
                    html.H4("Project Status Summary", className="text-danger")
                ),
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(
                                    className="fas fa-exclamation-triangle text-danger me-2"
                                ),
                                html.Span(
                                    "Unable to display project information. Please ensure you have valid project data.",
                                    className="text-danger",
                                ),
                            ],
                            className="d-flex align-items-center mb-2",
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                    ]
                ),
            ],
            className="mb-4 shadow-sm",
        )


def create_project_summary_card(statistics_df, settings, pert_data=None):
    """
    Create a comprehensive project summary card that combines the Project Status Summary
    and PERT Analysis information.

    Args:
        statistics_df: DataFrame containing the project statistics
        settings: Dictionary with current settings
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        A Dash card component with comprehensive project information
    """
    try:
        import pandas as pd
        import dash_bootstrap_components as dbc
        from dash import html

        # Make a copy of statistics_df to avoid modifying the original
        statistics_df = (
            statistics_df.copy() if not statistics_df.empty else pd.DataFrame()
        )

        # Convert 'date' column to datetime right at the beginning
        if not statistics_df.empty and "date" in statistics_df.columns:
            statistics_df["date"] = pd.to_datetime(statistics_df["date"])

        # Extract key metrics from settings (these represent remaining work)
        remaining_items = settings.get("total_items", 0)
        remaining_points = settings.get("total_points", 0)

        # Calculate completed items and points from statistics
        completed_items = (
            int(statistics_df["no_items"].sum()) if not statistics_df.empty else 0
        )
        completed_points = (
            int(statistics_df["no_points"].sum()) if not statistics_df.empty else 0
        )

        # Calculate true project totals (completed + remaining)
        total_items = remaining_items + completed_items
        total_points = round(
            remaining_points + completed_points
        )  # Round to nearest integer
        remaining_points = round(
            remaining_points
        )  # Round remaining points to nearest integer

        # Calculate percentages based on true project totals
        items_percentage = (
            int((completed_items / total_items) * 100) if total_items > 0 else 0
        )
        points_percentage = (
            int((completed_points / total_points) * 100) if total_points > 0 else 0
        )

        # Check if percentages are similar (within 2% of each other)
        similar_percentages = abs(items_percentage - points_percentage) <= 2

        # Calculate average weekly velocity and coefficient of variation (last 10 weeks)
        recent_df = (
            statistics_df.tail(10).copy() if not statistics_df.empty else pd.DataFrame()
        )

        # Calculate weekly metrics - Now we know date is already datetime
        if not recent_df.empty:
            # Add week and year columns
            recent_df.loc[:, "week"] = recent_df["date"].dt.isocalendar().week
            recent_df.loc[:, "year"] = recent_df["date"].dt.isocalendar().year

            weekly_data = (
                recent_df.groupby(["year", "week"])
                .agg({"no_items": "sum", "no_points": "sum"})
                .reset_index()
            )

            # Calculate metrics
            avg_weekly_items = weekly_data["no_items"].mean()
            avg_weekly_points = weekly_data["no_points"].mean()

            # Calculate coefficient of variation (CV = stdev / mean)
            std_weekly_items = weekly_data["no_items"].std()
            std_weekly_points = weekly_data["no_points"].std()

            cv_items = (
                (std_weekly_items / avg_weekly_items * 100)
                if avg_weekly_items > 0
                else 0
            )
            cv_points = (
                (std_weekly_points / avg_weekly_points * 100)
                if avg_weekly_points > 0
                else 0
            )

            # Calculate stability metrics (weeks with 0 or > 2x average)
            zero_item_weeks = len(weekly_data[weekly_data["no_items"] == 0])
            zero_point_weeks = len(weekly_data[weekly_data["no_points"] == 0])

            high_item_weeks = len(
                weekly_data[weekly_data["no_items"] > avg_weekly_items * 2]
            )
            high_point_weeks = len(
                weekly_data[weekly_data["no_points"] > avg_weekly_points * 2]
            )

            # Calculate overall stability score (0-100)
            stability_score = max(
                0,
                100
                - cv_items * 0.5
                - cv_points * 0.5
                - zero_item_weeks * 10
                - zero_point_weeks * 10
                - high_item_weeks * 5
                - high_point_weeks * 5,
            )
            stability_score = min(100, max(0, stability_score))

            # Determine velocity consistency status
            if stability_score >= 80:
                stability_status = "Consistent"
                stability_color = "success"
                stability_icon = "fa-check-circle"
            elif stability_score >= 50:
                stability_status = "Moderate"
                stability_color = "warning"
                stability_icon = "fa-exclamation-circle"
            else:
                stability_status = "Variable"
                stability_color = "danger"
                stability_icon = "fa-times-circle"

            # Calculate recent trend (last 4 weeks vs previous 4 weeks)
            recent_4w = weekly_data.tail(4)
            previous_4w = weekly_data.iloc[
                max(0, len(weekly_data) - 8) : max(0, len(weekly_data) - 4)
            ]

            recent_avg_items = (
                recent_4w["no_items"].mean() if not recent_4w.empty else 0
            )
            previous_avg_items = (
                previous_4w["no_items"].mean() if not previous_4w.empty else 0
            )

            recent_avg_points = (
                recent_4w["no_points"].mean() if not recent_4w.empty else 0
            )
            previous_avg_points = (
                previous_4w["no_points"].mean() if not previous_4w.empty else 0
            )

            # Calculate percentage changes in velocity
            if previous_avg_items > 0:
                items_change_pct = (
                    (recent_avg_items - previous_avg_items) / previous_avg_items
                ) * 100
            else:
                items_change_pct = float("inf") if recent_avg_items > 0 else 0

            if previous_avg_points > 0:
                points_change_pct = (
                    (recent_avg_points - previous_avg_points) / previous_avg_points
                ) * 100
            else:
                points_change_pct = float("inf") if recent_avg_points > 0 else 0

            # Determine trend direction and color
            if items_change_pct > 10:
                items_trend = "Increasing"
                items_trend_color = "success"
                items_trend_icon = "fa-arrow-up"
            elif items_change_pct < -10:
                items_trend = "Decreasing"
                items_trend_color = "danger"
                items_trend_icon = "fa-arrow-down"
            else:
                items_trend = "Stable"
                items_trend_color = "secondary"
                items_trend_icon = "fa-equals"

            if points_change_pct > 10:
                points_trend = "Increasing"
                points_trend_color = "success"
                points_trend_icon = "fa-arrow-up"
            elif points_change_pct < -10:
                points_trend = "Decreasing"
                points_trend_color = "danger"
                points_trend_icon = "fa-arrow-down"
            else:
                points_trend = "Stable"
                points_trend_color = "secondary"
                points_trend_icon = "fa-equals"

            # Calculate estimated completion date based on remaining work
            if avg_weekly_items > 0:
                weeks_to_complete_items = remaining_items / avg_weekly_items
                completion_date_items = datetime.now() + timedelta(
                    weeks=weeks_to_complete_items
                )
                days_to_complete_items = int(weeks_to_complete_items * 7)
                completion_date_items_str = completion_date_items.strftime("%Y-%m-%d")
            else:
                completion_date_items_str = "Unknown"
                days_to_complete_items = None

            if avg_weekly_points > 0:
                weeks_to_complete_points = remaining_points / avg_weekly_points
                completion_date_points = datetime.now() + timedelta(
                    weeks=weeks_to_complete_points
                )
                days_to_complete_points = int(weeks_to_complete_points * 7)
                completion_date_points_str = completion_date_points.strftime("%Y-%m-%d")
            else:
                completion_date_points_str = "Unknown"
                days_to_complete_points = None
        else:
            avg_weekly_items = 0
            avg_weekly_points = 0
            cv_items = 0
            cv_points = 0
            items_trend = "No Data"
            points_trend = "No Data"
            items_trend_color = "secondary"
            points_trend_color = "secondary"
            items_trend_icon = "fa-minus"
            points_trend_icon = "fa-minus"
            stability_status = "No Data"
            stability_color = "secondary"
            stability_icon = "fa-question-circle"
            completion_date_items_str = "Unknown"
            completion_date_points_str = "Unknown"
            days_to_complete_items = None
            days_to_complete_points = None
            stability_score = 0
            zero_item_weeks = 0
            zero_point_weeks = 0
            high_item_weeks = 0
            high_point_weeks = 0

        # Calculate days of data available
        if not statistics_df.empty:
            min_date = statistics_df["date"].min()
            max_date = statistics_df["date"].max()
            data_span_days = (
                (max_date - min_date).days + 1 if not statistics_df.empty else 0
            )
            unique_dates = (
                statistics_df["date"].nunique() if not statistics_df.empty else 0
            )
        else:
            data_span_days = 0
            unique_dates = 0

        # Format deadline string for display
        deadline_date = settings.get("deadline")
        deadline_obj = None
        if deadline_date:
            deadline_str = deadline_date
            try:
                deadline_obj = datetime.strptime(deadline_date, "%Y-%m-%d")
                days_to_deadline = (deadline_obj - datetime.now()).days
            except (ValueError, TypeError):
                days_to_deadline = None
        else:
            deadline_str = "Not set"
            days_to_deadline = None

        # Create the pert_info content directly instead of using a container
        pert_info_content = html.Div("PERT analysis data not available")
        if pert_data:
            try:
                pert_time_items = pert_data.get("pert_time_items", 0)
                pert_time_points = pert_data.get("pert_time_points", 0)

                # If both PERT values are None, provide a placeholder message
                if pert_time_items is None and pert_time_points is None:
                    pert_info_content = html.Div(
                        "PERT analysis will display here once forecast data is available",
                        className="text-muted p-3",
                    )
                else:
                    # Create PERT info table directly without using a container
                    pert_info_content = create_pert_info_table(
                        pert_time_items if pert_time_items is not None else 0,
                        pert_time_points if pert_time_points is not None else 0,
                        days_to_deadline if days_to_deadline is not None else 0,
                        avg_weekly_items=avg_weekly_items,
                        avg_weekly_points=avg_weekly_points,
                        pert_factor=settings.get("pert_factor", 3),
                        total_items=remaining_items,
                        total_points=remaining_points,
                        deadline_str=deadline_str,
                    )
            except Exception as pert_error:
                pert_info_content = html.P(
                    f"Error generating PERT analysis: {str(pert_error)}"
                )

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H4("Project Dashboard", className="d-inline"),
                        create_info_tooltip(
                            "project-dashboard",
                            "Comprehensive project overview showing status, forecasts, and PERT analysis based on your historical data.",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        # 1. OVERVIEW SECTION - Key progress indicators in compact form
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5(
                                            [
                                                html.I(
                                                    className="fas fa-tachometer-alt me-2 text-primary"
                                                ),
                                                "Project Overview",
                                            ],
                                            className="border-bottom pb-2 mb-3",
                                        ),
                                        # Project completion stats - Combined or separate
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        # Combined progress bar - shown when percentages are similar
                                                        html.Div(
                                                            [
                                                                dbc.Progress(
                                                                    [
                                                                        html.Span(
                                                                            f"{items_percentage}%",
                                                                            className="progress-bar-label",
                                                                        ),
                                                                    ],
                                                                    value=items_percentage,
                                                                    color="primary",
                                                                    className="mb-1",
                                                                    style={
                                                                        "height": "22px"
                                                                    },
                                                                    id="combined-progress-bar",
                                                                ),
                                                                html.Small(
                                                                    [
                                                                        f"{completed_items} of {total_items} items",
                                                                        html.Span(
                                                                            f" ({remaining_items} remaining)",
                                                                            className="ms-1",
                                                                        ),
                                                                        html.Span(
                                                                            " • ",
                                                                            className="mx-2 text-muted",
                                                                        ),
                                                                        f"{completed_points} of {total_points} points",
                                                                        html.Span(
                                                                            f" ({remaining_points} remaining)",
                                                                            className="ms-1",
                                                                        ),
                                                                    ],
                                                                    className="text-muted d-block",
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "block"
                                                                if similar_percentages
                                                                else "none"
                                                            },
                                                        ),
                                                        # Separate progress bars - shown when percentages differ
                                                        html.Div(
                                                            [
                                                                dbc.Row(
                                                                    [
                                                                        dbc.Col(
                                                                            [
                                                                                # Items progress
                                                                                html.Div(
                                                                                    [
                                                                                        html.Small(
                                                                                            [
                                                                                                html.I(
                                                                                                    className="fas fa-tasks me-1",
                                                                                                    style={
                                                                                                        "color": COLOR_PALETTE[
                                                                                                            "items"
                                                                                                        ]
                                                                                                    },
                                                                                                ),
                                                                                                "Items",
                                                                                            ],
                                                                                            className="mb-1 d-block",
                                                                                        ),
                                                                                        dbc.Progress(
                                                                                            [
                                                                                                html.Span(
                                                                                                    f"{items_percentage}%",
                                                                                                    className="progress-bar-label",
                                                                                                ),
                                                                                            ],
                                                                                            value=items_percentage,
                                                                                            color="info",
                                                                                            className="mb-1",
                                                                                            style={
                                                                                                "height": "20px"
                                                                                            },
                                                                                            id="items-progress-bar",
                                                                                        ),
                                                                                        html.Small(
                                                                                            f"{completed_items} of {total_items} ({remaining_items} left)",
                                                                                            className="text-muted d-block",
                                                                                        ),
                                                                                    ],
                                                                                ),
                                                                            ],
                                                                            md=6,
                                                                        ),
                                                                        dbc.Col(
                                                                            [
                                                                                # Points progress
                                                                                html.Div(
                                                                                    [
                                                                                        html.Small(
                                                                                            [
                                                                                                html.I(
                                                                                                    className="fas fa-chart-line me-1",
                                                                                                    style={
                                                                                                        "color": COLOR_PALETTE[
                                                                                                            "points"
                                                                                                        ]
                                                                                                    },
                                                                                                ),
                                                                                                "Points",
                                                                                            ],
                                                                                            className="mb-1 d-block",
                                                                                        ),
                                                                                        dbc.Progress(
                                                                                            [
                                                                                                html.Span(
                                                                                                    f"{points_percentage}%",
                                                                                                    className="progress-bar-label",
                                                                                                ),
                                                                                            ],
                                                                                            value=points_percentage,
                                                                                            color="warning",
                                                                                            className="mb-1",
                                                                                            style={
                                                                                                "height": "20px"
                                                                                            },
                                                                                            id="points-progress-bar",
                                                                                        ),
                                                                                        html.Small(
                                                                                            f"{completed_points} of {total_points} ({remaining_points} left)",
                                                                                            className="text-muted d-block",
                                                                                        ),
                                                                                    ],
                                                                                ),
                                                                            ],
                                                                            md=6,
                                                                        ),
                                                                    ],
                                                                ),
                                                            ],
                                                            style={
                                                                "display": "block"
                                                                if not similar_percentages
                                                                else "none"
                                                            },
                                                        ),
                                                    ],
                                                    className="mb-3",
                                                ),
                                            ],
                                        ),
                                        # Deadline and forecast completion dates
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="fas fa-calendar-day me-2 text-info"
                                                                        ),
                                                                        html.Span(
                                                                            "Deadline: ",
                                                                            className="fw-bold",
                                                                        ),
                                                                        html.Span(
                                                                            f"{deadline_str}",
                                                                            className="ms-1",
                                                                        ),
                                                                        html.Small(
                                                                            f" ({days_to_deadline} days left)"
                                                                            if days_to_deadline
                                                                            is not None
                                                                            else "",
                                                                            className="ms-1 text-muted",
                                                                        ),
                                                                    ],
                                                                    className="mb-1 d-flex align-items-center",
                                                                ),
                                                                html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="fas fa-tasks me-2",
                                                                            style={
                                                                                "color": COLOR_PALETTE[
                                                                                    "items"
                                                                                ]
                                                                            },
                                                                        ),
                                                                        html.Span(
                                                                            "Items completion: ",
                                                                            className="fw-bold",
                                                                        ),
                                                                        html.Span(
                                                                            f"{completion_date_items_str}",
                                                                            className=f"{('text-success' if deadline_obj is not None and completion_date_items_str != 'Unknown' and datetime.strptime(completion_date_items_str, '%Y-%m-%d') <= deadline_obj else 'text-danger') if deadline_obj is not None and completion_date_items_str != 'Unknown' else ''}",
                                                                        ),
                                                                        html.Small(
                                                                            f" ({days_to_complete_items} days)"
                                                                            if days_to_complete_items
                                                                            is not None
                                                                            else "",
                                                                            className="ms-1 text-muted",
                                                                        ),
                                                                    ],
                                                                    className="mb-1 d-flex align-items-center",
                                                                ),
                                                                html.Div(
                                                                    [
                                                                        html.I(
                                                                            className="fas fa-chart-line me-2",
                                                                            style={
                                                                                "color": COLOR_PALETTE[
                                                                                    "points"
                                                                                ]
                                                                            },
                                                                        ),
                                                                        html.Span(
                                                                            "Points completion: ",
                                                                            className="fw-bold",
                                                                        ),
                                                                        html.Span(
                                                                            f"{completion_date_points_str}",
                                                                            className=f"{('text-success' if deadline_obj is not None and completion_date_points_str != 'Unknown' and datetime.strptime(completion_date_points_str, '%Y-%m-%d') <= deadline_obj else 'text-danger') if deadline_obj is not None and completion_date_points_str != 'Unknown' else ''}",
                                                                        ),
                                                                        html.Small(
                                                                            f" ({days_to_complete_points} days)"
                                                                            if days_to_complete_points
                                                                            is not None
                                                                            else "",
                                                                            className="ms-1 text-muted",
                                                                        ),
                                                                    ],
                                                                    className="d-flex align-items-center",
                                                                ),
                                                            ],
                                                            className="border p-2 rounded",
                                                        ),
                                                    ],
                                                    width=12,
                                                ),
                                            ],
                                            className="mb-4",
                                        ),
                                    ],
                                    lg=6,
                                ),
                                # 2. PERFORMANCE METRICS - Velocity, trends & patterns
                                dbc.Col(
                                    [
                                        html.H5(
                                            [
                                                html.I(
                                                    className="fas fa-chart-bar me-2 text-primary"
                                                ),
                                                "Performance Metrics",
                                            ],
                                            className="border-bottom pb-2 mb-3",
                                        ),
                                        # Velocity metrics
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div(
                                                            [
                                                                # Items velocity & trend
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas {items_trend_icon} me-2 text-{items_trend_color}"
                                                                                ),
                                                                                html.Span(
                                                                                    "Items: ",
                                                                                    className="fw-bold",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{items_trend}",
                                                                                    className=f"text-{items_trend_color}",
                                                                                ),
                                                                            ],
                                                                            className="mb-1 d-flex align-items-center",
                                                                        ),
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    f"{avg_weekly_items:.1f}",
                                                                                    style={
                                                                                        "fontSize": "1.1rem",
                                                                                        "fontWeight": "bold",
                                                                                        "color": COLOR_PALETTE[
                                                                                            "items"
                                                                                        ],
                                                                                    },
                                                                                ),
                                                                                html.Small(
                                                                                    " items/week"
                                                                                ),
                                                                                html.Span(
                                                                                    f" ({items_change_pct:+.1f}%)"
                                                                                    if items_change_pct
                                                                                    != float(
                                                                                        "inf"
                                                                                    )
                                                                                    else " (∞%)",
                                                                                    className=f"ms-2 {'text-success' if items_change_pct > 0 else 'text-danger' if items_change_pct < 0 else 'text-secondary'}",
                                                                                ),
                                                                            ],
                                                                            className="mb-1 d-flex align-items-center",
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                "CV: ",
                                                                                html.Span(
                                                                                    f"{cv_items:.1f}%",
                                                                                    className=f"{'text-success' if cv_items < 30 else 'text-warning' if cv_items < 50 else 'text-danger'}",
                                                                                ),
                                                                                " • Zero weeks: ",
                                                                                html.Span(
                                                                                    f"{zero_item_weeks}",
                                                                                    className=f"{'text-success' if zero_item_weeks == 0 else 'text-danger'}",
                                                                                ),
                                                                            ],
                                                                            className="text-muted",
                                                                        ),
                                                                    ],
                                                                    className="border p-2 rounded mb-2",
                                                                ),
                                                            ],
                                                            className="mb-3",
                                                        ),
                                                    ],
                                                    md=6,
                                                ),
                                                # Points metrics
                                                dbc.Col(
                                                    [
                                                        html.Div(
                                                            [
                                                                # Points velocity & trend
                                                                html.Div(
                                                                    [
                                                                        html.Div(
                                                                            [
                                                                                html.I(
                                                                                    className=f"fas {points_trend_icon} me-2 text-{points_trend_color}"
                                                                                ),
                                                                                html.Span(
                                                                                    "Points: ",
                                                                                    className="fw-bold",
                                                                                ),
                                                                                html.Span(
                                                                                    f"{points_trend}",
                                                                                    className=f"text-{points_trend_color}",
                                                                                ),
                                                                            ],
                                                                            className="mb-1 d-flex align-items-center",
                                                                        ),
                                                                        html.Div(
                                                                            [
                                                                                html.Span(
                                                                                    f"{avg_weekly_points:.1f}",
                                                                                    style={
                                                                                        "fontSize": "1.1rem",
                                                                                        "fontWeight": "bold",
                                                                                        "color": COLOR_PALETTE[
                                                                                            "points"
                                                                                        ],
                                                                                    },
                                                                                ),
                                                                                html.Small(
                                                                                    " points/week"
                                                                                ),
                                                                                html.Span(
                                                                                    f" ({points_change_pct:+.1f}%)"
                                                                                    if points_change_pct
                                                                                    != float(
                                                                                        "inf"
                                                                                    )
                                                                                    else " (∞%)",
                                                                                    className=f"ms-2 {'text-success' if points_change_pct > 0 else 'text-danger' if points_change_pct < 0 else 'text-secondary'}",
                                                                                ),
                                                                            ],
                                                                            className="mb-1 d-flex align-items-center",
                                                                        ),
                                                                        html.Small(
                                                                            [
                                                                                "CV: ",
                                                                                html.Span(
                                                                                    f"{cv_points:.1f}%",
                                                                                    className=f"{'text-success' if cv_points < 30 else 'text-warning' if cv_points < 50 else 'text-danger'}",
                                                                                ),
                                                                                " • Zero weeks: ",
                                                                                html.Span(
                                                                                    f"{zero_point_weeks}",
                                                                                    className=f"{'text-success' if zero_point_weeks == 0 else 'text-danger'}",
                                                                                ),
                                                                            ],
                                                                            className="text-muted",
                                                                        ),
                                                                    ],
                                                                    className="border p-2 rounded",
                                                                ),
                                                            ],
                                                        ),
                                                    ],
                                                    md=6,
                                                ),
                                            ],
                                        ),
                                    ],
                                    lg=6,
                                ),
                            ],
                            className="mb-3",
                        ),
                        # 3. PERT ANALYSIS SECTION
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H5(
                                            [
                                                html.I(
                                                    className="fas fa-project-diagram me-2 text-primary"
                                                ),
                                                "PERT Analysis",
                                            ],
                                            className="border-bottom pb-2 mb-3",
                                        ),
                                        html.Div(
                                            pert_info_content,
                                            id="project-dashboard-pert-content",
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                    className="p-3",  # Add padding to entire card body
                ),
            ],
            className="mb-3 shadow-sm",
        )
    except Exception as e:
        # Fallback card in case of errors
        return dbc.Card(
            [
                dbc.CardHeader("Project Dashboard"),
                dbc.CardBody(
                    [
                        html.P(
                            "Unable to display project information. Please ensure you have valid project data.",
                            className="text-danger",
                        ),
                        html.Small(f"Error: {str(e)}", className="text-muted"),
                        # Debug information
                        html.Div(
                            [
                                html.Hr(),
                                html.H6("Debug Information:", className="text-muted"),
                                html.P(f"Error details: {type(e).__name__}: {str(e)}"),
                                html.Pre(
                                    f"Error context: pert_data: {pert_data if pert_data else 'None'}\n"
                                    f"Settings: {settings if settings else 'None'}",
                                    style={"fontSize": "0.8rem"},
                                ),
                            ],
                            className="mt-3",
                            style={"display": "block"},  # For debugging
                        ),
                    ]
                ),
            ],
            className="mb-3 shadow-sm",
        )


def create_items_forecast_info_card():
    """
    Create a forecast information card specifically for the Items per Week tab.

    Returns:
        Dash Card component with items forecast explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Items Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "items-forecast-info",
                        "Explanation of how to interpret the weekly items forecast.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Weekly Items Chart: "),
                                    "This chart shows your historical weekly completed items as blue bars and forecasts the next week's expected completion.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Chart Components: "),
                                    "The chart includes several visual elements:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Blue Bars: "),
                                            html.Span(
                                                "Historical weekly completed items",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ". These represent your actual completed work each week.",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Dark Blue Line: "),
                                            html.Span(
                                                "Weighted 4-week moving average",
                                                style={
                                                    "color": "#0047AB",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " that prioritizes recent performance (40% latest week, 30%, 20%, 10% for earlier weeks).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Patterned Bar: "),
                                            html.Span(
                                                "Next week forecast",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " based on PERT estimation using your historical data.",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Forecast Methodology: "),
                                    "The next week forecast is calculated using PERT (Program Evaluation and Review Technique) methodology:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Average of all historical weekly items data",
                                                style={
                                                    "color": COLOR_PALETTE["items"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Average of your best performing weeks",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (highest item counts, 20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Average of your lowest performing weeks",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (excluding zero values, 80% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("PERT Formula: "),
                                            html.Code(
                                                "(Optimistic + 4 × Most Likely + Pessimistic) ÷ 6"
                                            ),
                                            " - This weighted average gives more importance to the most likely scenario.",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Interpreting the Forecast: "),
                                    "This forecast helps you predict how many items you're likely to complete next week based on your historical performance patterns. "
                                    "Use this to plan sprint capacities and adjust resource allocation.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-4",  # Increased padding for better readability and more space from chart
            ),
        ],
        className="mt-5 mb-3 shadow-sm",  # Added top margin to create more space from the chart
    )


def create_points_forecast_info_card():
    """
    Create a forecast information card specifically for the Points per Week tab.

    Returns:
        Dash Card component with points forecast explanation
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Points Forecast Information", className="d-inline"),
                    create_info_tooltip(
                        "points-forecast-info",
                        "Explanation of how to interpret the weekly points forecast.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.P(
                                [
                                    html.Strong("Weekly Points Chart: "),
                                    "This chart visualizes your historical weekly completed points as orange bars and provides a statistical forecast for next week.",
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    html.Strong("Chart Components: "),
                                    "The chart includes several visual elements:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Orange Bars: "),
                                            html.Span(
                                                "Historical weekly completed points",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ". These represent your actual completed story points each week.",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Red Trend Line: "),
                                            html.Span(
                                                "Weighted 4-week moving average",
                                                style={
                                                    "color": "#FF6347",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " with exponential weighting (40% for most recent week, 30%, 20%, 10% for earlier weeks).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong(
                                                "Patterned Bar with Error Bars: "
                                            ),
                                            html.Span(
                                                "Next week forecast",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " with confidence interval showing the range of likely outcomes.",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong(
                                        "Understanding the Confidence Interval: "
                                    ),
                                    "The forecast bar includes error bars representing a statistical confidence interval:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Upper Bound: "),
                                            html.Span(
                                                "25% of the difference between Most Likely and Optimistic estimates",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "optimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ".",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Lower Bound: "),
                                            html.Span(
                                                "25% of the difference between Most Likely and Pessimistic estimates",
                                                style={
                                                    "color": COLOR_PALETTE[
                                                        "pessimistic"
                                                    ],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            ".",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            "This gives you a reasonable range of expected performance for planning purposes."
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("PERT Estimation Method: "),
                                    "The forecast uses PERT (Program Evaluation and Review Technique) to provide a weighted average that accounts for uncertainty:",
                                ],
                                className="mb-1",
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        [
                                            html.Strong("Most Likely: "),
                                            html.Span(
                                                "Average of all historical weekly points data",
                                                style={
                                                    "color": COLOR_PALETTE["points"],
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (50% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Optimistic: "),
                                            html.Span(
                                                "Average of weeks with highest point completions",
                                                style={
                                                    "color": "rgb(184, 134, 11)",
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (20% confidence level).",
                                        ]
                                    ),
                                    html.Li(
                                        [
                                            html.Strong("Pessimistic: "),
                                            html.Span(
                                                "Average of weeks with lowest non-zero point completions",
                                                style={
                                                    "color": "rgb(165, 42, 42)",
                                                    "fontWeight": "normal",
                                                },
                                            ),
                                            " (80% confidence level).",
                                        ]
                                    ),
                                ],
                                className="mb-3",  # Increased spacing
                            ),
                            html.P(
                                [
                                    html.Strong("Practical Use: "),
                                    "Use the points forecast to estimate sprint capacity and project velocity. "
                                    "Consider the confidence interval for risk assessment and establishing delivery commitments.",
                                ],
                                className="mb-0",
                            ),
                        ],
                        style={"textAlign": "left"},
                    )
                ],
                className="py-4",  # Increased padding for better readability and more space from chart
            ),
        ],
        className="mt-5 mb-3 shadow-sm",  # Added top margin to create more space from the chart
    )
