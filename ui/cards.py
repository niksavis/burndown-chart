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

# Fix circular import issue - import directly from components instead of ui
from ui.components import create_info_tooltip

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
                                                    "Estimated Items:",
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
                                                    "Total Items:",
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
                                                    "Estimated Points:",
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
                                                    "Total Points (calculated):",
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
                                                    f"Using {avg_points_per_item:.1f} points per item for calculation"
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
    Create the project status summary card with key project metrics.

    Args:
        statistics_df: DataFrame with historical statistics
        settings: Dictionary with current application settings

    Returns:
        Dash Card component with project status summary
    """
    # Calculate progress metrics
    total_items = settings["total_items"]
    total_points = settings["total_points"]

    # Calculate completed items and points from statistics
    completed_items = statistics_df["no_items"].sum() if not statistics_df.empty else 0
    completed_points = (
        statistics_df["no_points"].sum() if not statistics_df.empty else 0
    )

    # Calculate percentages
    items_percentage = min(
        round((completed_items / total_items) * 100 if total_items > 0 else 0, 1), 100
    )
    points_percentage = min(
        round((completed_points / total_points) * 100 if total_points > 0 else 0, 1),
        100,
    )

    # Calculate velocity metrics
    if not statistics_df.empty and len(statistics_df) >= 2:
        # Group by week for calculation
        statistics_df["date"] = pd.to_datetime(statistics_df["date"])
        weekly_stats = statistics_df.resample("W", on="date").sum()

        # Get weekly averages
        avg_weekly_items = round(weekly_stats["no_items"].mean(), 1)
        avg_weekly_points = round(weekly_stats["no_points"].mean(), 1)

        # Get standard deviations for stability indicators
        std_weekly_items = round(weekly_stats["no_items"].std(), 1)
        std_weekly_points = round(weekly_stats["no_points"].std(), 1)

        # Calculate stability as coefficient of variation (CV)
        cv_items = (
            round((std_weekly_items / avg_weekly_items) * 100, 1)
            if avg_weekly_items > 0
            else 0
        )
        cv_points = (
            round((std_weekly_points / avg_weekly_points) * 100, 1)
            if avg_weekly_points > 0
            else 0
        )
    else:
        avg_weekly_items = 0
        avg_weekly_points = 0
        std_weekly_items = 0
        std_weekly_points = 0
        cv_items = 0
        cv_points = 0

    # Calculate estimated completion dates
    remaining_items = max(0, total_items - completed_items)
    remaining_points = max(0, total_points - completed_points)

    if avg_weekly_items > 0:
        weeks_to_complete_items = round(remaining_items / avg_weekly_items, 1)
        completion_date_items = (
            datetime.now() + timedelta(weeks=weeks_to_complete_items)
        ).strftime("%Y-%m-%d")
    else:
        weeks_to_complete_items = float("inf")
        completion_date_items = "Unknown"

    if avg_weekly_points > 0:
        weeks_to_complete_points = round(remaining_points / avg_weekly_points, 1)
        completion_date_points = (
            datetime.now() + timedelta(weeks=weeks_to_complete_points)
        ).strftime("%Y-%m-%d")
    else:
        weeks_to_complete_points = float("inf")
        completion_date_points = "Unknown"

    # Calculate days until deadline
    deadline_date = datetime.strptime(settings["deadline"], "%Y-%m-%d")
    days_to_deadline = (deadline_date - datetime.now()).days

    # Determine if completion estimates are within deadline
    items_on_track = (
        completion_date_items != "Unknown"
        and datetime.strptime(completion_date_items, "%Y-%m-%d") <= deadline_date
    )
    points_on_track = (
        completion_date_points != "Unknown"
        and datetime.strptime(completion_date_points, "%Y-%m-%d") <= deadline_date
    )

    # Generate status indicators and colors
    items_color = "success" if items_on_track else "danger"
    points_color = "success" if points_on_track else "danger"

    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Project Status Summary", className="d-inline"),
                    create_info_tooltip(
                        "project-status",
                        "Key metrics showing current progress, velocity, and estimated completion based on historical data.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    # Progress Section
                    html.Div(
                        [
                            html.H5(
                                "Current Progress", className="mb-3 border-bottom pb-2"
                            ),
                            dbc.Row(
                                [
                                    # Items Progress
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    f"Items Completed: {completed_items} of {total_items}",
                                                ]
                                            ),
                                            dbc.Progress(
                                                value=items_percentage,
                                                id="items-progress-bar",
                                                color="info",
                                                className="mb-1",
                                                style={"height": "20px"},
                                            ),
                                            html.Small(
                                                f"{items_percentage}% complete",
                                                className="text-muted",
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                    # Points Progress
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    f"Points Completed: {completed_points} of {total_points}",
                                                ]
                                            ),
                                            dbc.Progress(
                                                value=points_percentage,
                                                id="points-progress-bar",
                                                color="warning",
                                                className="mb-1",
                                                style={"height": "20px"},
                                            ),
                                            html.Small(
                                                f"{points_percentage}% complete",
                                                className="text-muted",
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                ],
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Velocity Section
                    html.Div(
                        [
                            html.H5(
                                "Velocity Metrics", className="mb-3 border-bottom pb-2"
                            ),
                            dbc.Row(
                                [
                                    # Items Velocity
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Label("Weekly Items"),
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{avg_weekly_items}",
                                                                style={
                                                                    "fontSize": "24px",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                                className="mr-2",
                                                            ),
                                                            html.Small(
                                                                f"± {std_weekly_items}",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="d-flex align-items-baseline",
                                                    ),
                                                    html.Small(
                                                        [
                                                            f"Stability: {cv_items}% ",
                                                            html.I(
                                                                className=f"fas {'fa-check-circle text-success' if cv_items < 25 else 'fa-exclamation-circle text-warning'}",
                                                                title=f"{'Stable' if cv_items < 25 else 'Variable'} velocity",
                                                            ),
                                                        ],
                                                        className="d-block",
                                                    ),
                                                ],
                                                className="text-center p-3 border rounded",
                                                style={
                                                    "backgroundColor": "rgba(0, 99, 178, 0.1)"
                                                },
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                    # Points Velocity
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.Label("Weekly Points"),
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{avg_weekly_points}",
                                                                style={
                                                                    "fontSize": "24px",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                                className="mr-2",
                                                            ),
                                                            html.Small(
                                                                f"± {std_weekly_points}",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="d-flex align-items-baseline",
                                                    ),
                                                    html.Small(
                                                        [
                                                            f"Stability: {cv_points}% ",
                                                            html.I(
                                                                className=f"fas {'fa-check-circle text-success' if cv_points < 25 else 'fa-exclamation-circle text-warning'}",
                                                                title=f"{'Stable' if cv_points < 25 else 'Variable'} velocity",
                                                            ),
                                                        ],
                                                        className="d-block",
                                                    ),
                                                ],
                                                className="text-center p-3 border rounded",
                                                style={
                                                    "backgroundColor": "rgba(255, 127, 14, 0.1)"
                                                },
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                ],
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Completion Forecast Section
                    html.Div(
                        [
                            html.H5(
                                "Completion Forecast",
                                className="mb-3 border-bottom pb-2",
                            ),
                            dbc.Row(
                                [
                                    # Items Forecast
                                    dbc.Col(
                                        [
                                            html.Label("Items Forecast"),
                                            html.Div(
                                                html.Span(
                                                    completion_date_items,
                                                    style={
                                                        "fontSize": "20px",
                                                        "color": f"{'green' if items_on_track else 'red'}",
                                                    },
                                                    className="font-weight-bold",
                                                ),
                                                className="mb-1",
                                            ),
                                            html.Small(
                                                f"{weeks_to_complete_items:.1f} weeks remaining"
                                                if weeks_to_complete_items
                                                != float("inf")
                                                else "Cannot estimate",
                                                className="text-muted d-block",
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                    # Points Forecast
                                    dbc.Col(
                                        [
                                            html.Label("Points Forecast"),
                                            html.Div(
                                                html.Span(
                                                    completion_date_points,
                                                    style={
                                                        "fontSize": "20px",
                                                        "color": f"{'green' if points_on_track else 'red'}",
                                                    },
                                                    className="font-weight-bold",
                                                ),
                                                className="mb-1",
                                            ),
                                            html.Small(
                                                f"{weeks_to_complete_points:.1f} weeks remaining"
                                                if weeks_to_complete_points
                                                != float("inf")
                                                else "Cannot estimate",
                                                className="text-muted d-block",
                                            ),
                                        ],
                                        width=12,
                                        md=6,
                                        className="mb-3",
                                    ),
                                ],
                            ),
                            # Deadline Display
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Project Deadline"),
                                            html.Div(
                                                html.Span(
                                                    settings["deadline"],
                                                    style={
                                                        "fontSize": "20px",
                                                        "color": COLOR_PALETTE[
                                                            "deadline"
                                                        ],
                                                    },
                                                    className="font-weight-bold",
                                                ),
                                                className="mb-1",
                                            ),
                                            html.Small(
                                                f"{days_to_deadline} days remaining",
                                                className="text-muted d-block",
                                            ),
                                        ],
                                        width=12,
                                        className="text-center p-3 border rounded",
                                        style={
                                            "backgroundColor": "rgba(220, 20, 60, 0.1)"
                                        },
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
                className="py-3",
            ),
        ],
        className="mb-3 shadow-sm",
    )


def create_team_capacity_card():
    """
    Create the team capacity card component.

    Returns:
        Dash Card component with team capacity inputs and metrics
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Team Capacity Settings", className="d-inline"),
                    create_info_tooltip(
                        "capacity-settings",
                        "Configure your team's capacity to see how it affects project completion forecasts.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    dbc.Form(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Team Members:"),
                                            dbc.Input(
                                                id="team-members-input",
                                                type="number",
                                                min=1,
                                                max=100,
                                                value=5,
                                                step=1,
                                            ),
                                            dbc.FormText(
                                                "Number of people working on the project"
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Hours per Member (weekly):"),
                                            dbc.Input(
                                                id="hours-per-member-input",
                                                type="number",
                                                min=1,
                                                max=80,
                                                value=40,
                                                step=1,
                                            ),
                                            dbc.FormText(
                                                "Available working hours per team member per week"
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label("Hours per Point (optional):"),
                                            dbc.Input(
                                                id="hours-per-point-input",
                                                type="number",
                                                min=0.1,
                                                max=40,
                                                value=None,
                                                placeholder="Auto-calculate",
                                                step=0.1,
                                            ),
                                            dbc.FormText(
                                                "Estimated hours required per story point"
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                    dbc.Col(
                                        [
                                            dbc.Label("Hours per Item (optional):"),
                                            dbc.Input(
                                                id="hours-per-item-input",
                                                type="number",
                                                min=0.1,
                                                max=40,
                                                value=None,
                                                placeholder="Auto-calculate",
                                                step=0.1,
                                            ),
                                            dbc.FormText(
                                                "Estimated hours required per work item"
                                            ),
                                        ],
                                        md=6,
                                        className="mb-3",
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Checkbox(
                                                id="include-weekends-input",
                                                label="Include weekends in capacity",
                                                value=False,
                                                className="mb-3",
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                            dbc.Button(
                                "Update Capacity",
                                id="update-capacity-button",
                                color="primary",
                                className="mt-3",
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.H5("Calculated Capacity Metrics", className="mt-4"),
                    html.Div(id="capacity-metrics-container", className="mt-3"),
                ]
            ),
        ],
        className="mb-4 shadow-sm",
    )


def create_capacity_chart_card():
    """
    Create the capacity chart card component.

    Returns:
        Dash Card component with the team capacity chart
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.H4("Team Capacity Chart", className="d-inline"),
                    create_info_tooltip(
                        "capacity-chart",
                        "This chart shows your team's capacity against project burndown.",
                    ),
                ]
            ),
            dbc.CardBody(
                [
                    dcc.Graph(
                        id="capacity-chart",
                        style={"height": "600px"},
                        config={"displayModeBar": True, "responsive": True},
                    ),
                ]
            ),
        ],
        className="mb-4 shadow-sm",
    )
