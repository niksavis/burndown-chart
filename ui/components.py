"""
UI Components Module

This module provides reusable UI components like tooltips, modals, and information tables
that are used across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, dcc
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta

# Import from configuration
from configuration import COLOR_PALETTE

#######################################################################
# INFO TOOLTIP COMPONENT
#######################################################################


def create_info_tooltip(id_suffix, help_text):
    """
    Create an information tooltip component.

    Args:
        id_suffix: Suffix for the component ID
        help_text: Text to display in the tooltip

    Returns:
        Dash component with tooltip
    """
    return html.Div(
        [
            html.I(
                className="fas fa-info-circle text-info ml-2",
                id=f"info-tooltip-{id_suffix}",
                style={"cursor": "pointer", "marginLeft": "5px"},
            ),
            dbc.Tooltip(
                help_text,
                target=f"info-tooltip-{id_suffix}",
                placement="right",
                style={"maxWidth": "300px"},
            ),
        ],
        style={"display": "inline-block"},
    )


#######################################################################
# HELP MODAL COMPONENT
#######################################################################


def create_help_modal():
    """
    Create the help modal with all content sections.

    Returns:
        Dash Modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader("How to Use the Project Burndown Forecast App"),
            dbc.ModalBody(
                [
                    # Overview section
                    html.Div(
                        [
                            html.H5("Overview", className="border-bottom pb-2 mb-3"),
                            html.P(
                                [
                                    "This application helps you forecast project completion based on historical progress.",
                                    html.Br(),
                                    "It uses the ",
                                    html.Strong("PERT methodology"),
                                    " to estimate when your project will be completed based on optimistic, pessimistic, and most likely scenarios.",
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Input Parameters section
                    html.Div(
                        [
                            html.H5(
                                "Input Parameters", className="border-bottom pb-2 mb-3"
                            ),
                            html.Div(
                                [
                                    html.H6(
                                        html.Strong("PERT Factor:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "Determines how many data points to use for optimistic and pessimistic estimates"
                                            ),
                                            html.Li(
                                                "Higher value considers more historical data points"
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Range:"),
                                                    " 3-15 (default: 3)",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(html.Strong("Deadline:"), className="mt-3"),
                                    html.Ul(
                                        [
                                            html.Li("Set your project deadline here"),
                                            html.Li(
                                                "The app will show if you're on track to meet it"
                                            ),
                                            html.Li(
                                                [html.Strong("Format:"), " YYYY-MM-DD"]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Total Items:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The total number of items (tasks, stories, etc.) to be completed"
                                            ),
                                            html.Li(
                                                [
                                                    html.Em(
                                                        "This represents work quantity"
                                                    )
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Total Points:"), className="mt-3"
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The total number of points (effort, complexity) to be completed"
                                            ),
                                            html.Li(
                                                [
                                                    html.Em(
                                                        "This represents work effort/complexity"
                                                    )
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Estimated Items:"),
                                        className="mt-3",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The number of items that have been estimated with points"
                                            ),
                                            html.Li(
                                                "Used to calculate average points per item and the total points"
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.H6(
                                        html.Strong("Estimated Points:"),
                                        className="mt-3",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                "The sum of points for the items that have been estimated"
                                            ),
                                            html.Li(
                                                "Used along with Estimated Items to calculate the average"
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # CSV Upload section with improved formatting
                    html.Div(
                        [
                            html.H5(
                                "CSV Upload Format", className="border-bottom pb-2 mb-3"
                            ),
                            html.Div(
                                [
                                    html.P(
                                        [
                                            html.Strong(
                                                "Your CSV file should contain the following columns:"
                                            ),
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Strong("date:"),
                                                    " Date of work completed (YYYY-MM-DD format)",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("no_items:"),
                                                    " Number of items completed on that date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("no_points:"),
                                                    " Number of points completed on that date",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.P(
                                        [
                                            "The file can use ",
                                            html.Em("semicolon (;)"),
                                            " or ",
                                            html.Em("comma (,)"),
                                            " as separators.",
                                        ],
                                        className="mb-2",
                                    ),
                                    html.P(html.Strong("Example:"), className="mb-1"),
                                    html.Pre(
                                        """date;no_items;no_points
2025-03-01;5;50
2025-03-02;7;70""",
                                        className="bg-light p-3 border rounded",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Statistics Table section
                    html.Div(
                        [
                            html.H5(
                                "Working with the Statistics Table",
                                className="border-bottom pb-2 mb-3",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        html.Strong(
                                            "This table shows your historical data. You can:"
                                        ),
                                        className="mb-2",
                                    ),
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Strong("Edit any cell"),
                                                    " by clicking on it",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Delete rows"),
                                                    " with the 'x' button",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Add new rows"),
                                                    " with the 'Add Row' button",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Strong("Sort"),
                                                    " by clicking column headers",
                                                ]
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Note:"),
                                            " Changes to this data will update the forecast ",
                                            html.Em("immediately"),
                                            ".",
                                        ],
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.P(
                                                html.Strong("Column definitions:"),
                                                className="mb-1",
                                            ),
                                            html.Ul(
                                                [
                                                    html.Li("Date: YYYY-MM-DD format"),
                                                    html.Li(
                                                        "Items: Number of work items completed"
                                                    ),
                                                    html.Li(
                                                        "Points: Effort points completed"
                                                    ),
                                                ]
                                            ),
                                        ],
                                        className="bg-light p-3 border rounded",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Understanding the Forecast Graph
                    html.Div(
                        [
                            html.H5(
                                "Understanding the Forecast Graph",
                                className="border-bottom pb-2 mb-3",
                            ),
                            html.Div(
                                [
                                    html.P(
                                        html.Strong(
                                            "The graph shows your burndown forecast based on historical data:"
                                        ),
                                        className="mb-2",
                                    ),
                                    html.Div(
                                        [
                                            html.Div(
                                                className="row",
                                                children=[
                                                    html.Div(
                                                        className="col-6",
                                                        children=[
                                                            html.H6(
                                                                "Lines:",
                                                                className="mt-2 mb-2",
                                                            ),
                                                            html.Ul(
                                                                [
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Solid lines:"
                                                                            ),
                                                                            " Historical progress",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Dashed lines:"
                                                                            ),
                                                                            " Most likely forecast",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Dotted lines:"
                                                                            ),
                                                                            " Optimistic and pessimistic forecasts",
                                                                        ]
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className="col-6",
                                                        children=[
                                                            html.H6(
                                                                "Colors:",
                                                                className="mt-2 mb-2",
                                                            ),
                                                            html.Ul(
                                                                [
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Items: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "items"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Blue (history/likely), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "optimistic"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Teal (optimistic), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "pessimistic"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Purple (pessimistic)",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Points: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "points"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Orange (history/likely), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": "rgb(184, 134, 11)"
                                                                                },
                                                                            ),
                                                                            " Gold (optimistic), ",
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": "rgb(165, 42, 42)"
                                                                                },
                                                                            ),
                                                                            " Brown (pessimistic)",
                                                                        ]
                                                                    ),
                                                                    html.Li(
                                                                        [
                                                                            html.Strong(
                                                                                "Deadline: "
                                                                            ),
                                                                            html.Span(
                                                                                "■",
                                                                                style={
                                                                                    "color": COLOR_PALETTE[
                                                                                        "deadline"
                                                                                    ]
                                                                                },
                                                                            ),
                                                                            " Red vertical line",
                                                                        ]
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="bg-light p-3 border rounded mb-3",
                                    ),
                                    html.P(
                                        [
                                            html.Strong("Project Metrics:"),
                                            html.Br(),
                                            "The graph displays key metrics below the chart, including:",
                                            html.Ul(
                                                [
                                                    html.Li(
                                                        "Total Items and Points (whole numbers)"
                                                    ),
                                                    html.Li(
                                                        "Deadline and days remaining"
                                                    ),
                                                    html.Li(
                                                        "Estimated completion days for Items and Points"
                                                    ),
                                                    html.Li(
                                                        "Average and Median weekly Items/Points (last 10 weeks)"
                                                    ),
                                                ]
                                            ),
                                            html.Strong("Status Indicators:"),
                                            " Estimated days appear in ",
                                            html.Span(
                                                "green",
                                                style={
                                                    "color": "green",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " when on track to meet the deadline, and in ",
                                            html.Span(
                                                "red",
                                                style={
                                                    "color": "red",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                            " when at risk of missing the deadline.",
                                        ],
                                        className="mt-3 mb-0",
                                    ),
                                ],
                                className="ml-3",
                            ),
                        ]
                    ),
                ]
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close", id="close-help", className="ms-auto", color="secondary"
                ),
            ),
        ],
        id="help-modal",
        size="lg",
    )


#######################################################################
# PERT INFO TABLE COMPONENT
#######################################################################


def create_pert_info_table(
    pert_time_items,
    pert_time_points,
    days_to_deadline,
    avg_weekly_items=0,
    avg_weekly_points=0,
    med_weekly_items=0,
    med_weekly_points=0,
    pert_factor=3,  # Add default value
    total_items=0,  # New parameter for total items
    total_points=0,  # New parameter for total points
    deadline_str=None,  # Add parameter for direct deadline string
    statistics_df=None,  # New parameter for statistics data
):
    """
    Create the PERT information table with improved organization and visual grouping.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios
        total_items: Total remaining items to complete
        total_points: Total remaining points to complete
        deadline_str: The deadline date string from settings
        statistics_df: DataFrame containing the statistics data

    Returns:
        Dash component with improved PERT information display
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    # Calculate weeks to complete based on average and median rates
    weeks_avg_items = (
        total_items / avg_weekly_items if avg_weekly_items > 0 else float("inf")
    )
    weeks_med_items = (
        total_items / med_weekly_items if med_weekly_items > 0 else float("inf")
    )
    weeks_avg_points = (
        total_points / avg_weekly_points if avg_weekly_points > 0 else float("inf")
    )
    weeks_med_points = (
        total_points / med_weekly_points if med_weekly_points > 0 else float("inf")
    )

    # Determine colors for weeks estimates
    weeks_avg_items_color = (
        "green" if weeks_avg_items * 7 <= days_to_deadline else "red"
    )
    weeks_med_items_color = (
        "green" if weeks_med_items * 7 <= days_to_deadline else "red"
    )
    weeks_avg_points_color = (
        "green" if weeks_avg_points * 7 <= days_to_deadline else "red"
    )
    weeks_med_points_color = (
        "green" if weeks_med_points * 7 <= days_to_deadline else "red"
    )

    # Calculate projected completion dates
    current_date = datetime.now()
    items_completion_date = current_date + timedelta(days=pert_time_items)
    points_completion_date = current_date + timedelta(days=pert_time_points)

    # Calculate dates for average and median completion
    avg_items_completion_date = current_date + timedelta(days=weeks_avg_items * 7)
    med_items_completion_date = current_date + timedelta(days=weeks_med_items * 7)
    avg_points_completion_date = current_date + timedelta(days=weeks_avg_points * 7)
    med_points_completion_date = current_date + timedelta(days=weeks_med_points * 7)

    # Format dates and values for display with enhanced format
    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")

    # Format dates for average and median completion
    avg_items_completion_str = avg_items_completion_date.strftime("%Y-%m-%d")
    med_items_completion_str = med_items_completion_date.strftime("%Y-%m-%d")
    avg_points_completion_str = avg_points_completion_date.strftime("%Y-%m-%d")
    med_points_completion_str = med_points_completion_date.strftime("%Y-%m-%d")

    # Enhanced formatted strings with days and weeks
    items_completion_enhanced = f"{items_completion_str} ({pert_time_items:.1f} days, {pert_time_items / 7:.1f} weeks)"
    points_completion_enhanced = f"{points_completion_str} ({pert_time_points:.1f} days, {pert_time_points / 7:.1f} weeks)"

    # Enhanced formatted strings for average and median
    avg_items_days = weeks_avg_items * 7
    med_items_days = weeks_med_items * 7
    avg_points_days = weeks_avg_points * 7
    med_points_days = weeks_med_points * 7

    avg_items_completion_enhanced = (
        f"{avg_items_completion_str} ({avg_items_days:.1f} days, {weeks_avg_items:.1f} weeks)"
        if weeks_avg_items != float("inf")
        else "∞"
    )
    med_items_completion_enhanced = (
        f"{med_items_completion_str} ({med_items_days:.1f} days, {weeks_med_items:.1f} weeks)"
        if weeks_med_items != float("inf")
        else "∞"
    )
    avg_points_completion_enhanced = (
        f"{avg_points_completion_str} ({avg_points_days:.1f} days, {weeks_avg_points:.1f} weeks)"
        if weeks_avg_points != float("inf")
        else "∞"
    )
    med_points_completion_enhanced = (
        f"{med_points_completion_str} ({med_points_days:.1f} days, {weeks_med_points:.1f} weeks)"
        if weeks_med_points != float("inf")
        else "∞"
    )

    # Define trend indicators (simplified version from performance trend)
    # These would normally come from calculate_performance_trend but we'll simulate it here
    # In a real implementation, you would pass trend data from the parent component

    # Simulate trend data for demonstration - these would normally be calculated and passed in
    # Positive values indicate an upward trend compared to previous period
    # Negative values indicate a downward trend compared to previous period
    avg_items_trend = 10  # sample value: 10% increase from previous period
    med_items_trend = -5  # sample value: 5% decrease from previous period
    avg_points_trend = 0  # sample value: no change
    med_points_trend = 15  # sample value: 15% increase from previous period

    # Define trend arrow icons and colors based on the trend values
    def get_trend_icon_and_color(trend_value):
        if abs(trend_value) < 5:  # Less than 5% change is considered stable
            return "fas fa-equals", "#6c757d"  # Equals sign, gray color
        elif trend_value > 0:
            return "fas fa-arrow-up", "#28a745"  # Up arrow, green color
        else:
            return "fas fa-arrow-down", "#dc3545"  # Down arrow, red color

    # Get icons and colors for each metric
    avg_items_icon, avg_items_icon_color = get_trend_icon_and_color(avg_items_trend)
    med_items_icon, med_items_icon_color = get_trend_icon_and_color(med_items_trend)
    avg_points_icon, avg_points_icon_color = get_trend_icon_and_color(avg_points_trend)
    med_points_icon, med_points_icon_color = get_trend_icon_and_color(med_points_trend)

    # Use the provided deadline string instead of recalculating
    if deadline_str:
        deadline_date_str = deadline_str
    else:
        # Fallback to calculation if not provided
        deadline_date = current_date + timedelta(days=days_to_deadline)
        deadline_date_str = deadline_date.strftime("%Y-%m-%d")

    # Calculate completed items and points from statistics data
    completed_items = 0
    completed_points = 0
    if statistics_df is not None and not statistics_df.empty:
        completed_items = int(statistics_df["no_items"].sum())
        completed_points = int(statistics_df["no_points"].sum())

    # Calculate actual total project items and points
    actual_total_items = completed_items + total_items
    actual_total_points = round(completed_points + total_points)

    # Round the remaining points to natural number for display
    remaining_points = round(total_points)

    # Calculate percentages based on actual project totals
    items_percentage = (
        int((completed_items / actual_total_items) * 100)
        if actual_total_items > 0
        else 0
    )
    points_percentage = (
        int((completed_points / actual_total_points) * 100)
        if actual_total_points > 0
        else 0
    )

    # Check if percentages are similar (within 2% of each other)
    similar_percentages = abs(items_percentage - points_percentage) <= 2

    return html.Div(
        [
            # Project Overview section at the top - full width (100%)
            html.Div(
                [
                    html.H5(
                        [
                            html.I(
                                className="fas fa-project-diagram me-2",
                                style={"color": "#20c997"},
                            ),
                            "Project Overview",
                        ],
                        className="mb-3 border-bottom pb-2 d-flex align-items-center",
                    ),
                    html.Div(
                        [
                            # Project progress section
                            html.Div(
                                [
                                    # Combined progress for similar percentages
                                    html.Div(
                                        [
                                            html.Div(
                                                className="progress",
                                                style={
                                                    "height": "24px",
                                                    "position": "relative",
                                                    "borderRadius": "6px",
                                                    "overflow": "hidden",
                                                    "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                                },
                                                children=[
                                                    html.Div(
                                                        className="progress-bar bg-primary",
                                                        style={
                                                            "width": f"{items_percentage}%",
                                                            "height": "100%",
                                                            "transition": "width 1s ease",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{items_percentage}% Complete",
                                                        style={
                                                            "position": "absolute",
                                                            "top": "0",
                                                            "left": "0",
                                                            "width": "100%",
                                                            "height": "100%",
                                                            "display": "flex",
                                                            "alignItems": "center",
                                                            "justifyContent": "center",
                                                            "color": "white"
                                                            if items_percentage > 40
                                                            else "black",
                                                            "fontWeight": "bold",
                                                            "textShadow": "0 0 2px rgba(0,0,0,0.2)"
                                                            if items_percentage > 40
                                                            else "none",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                [
                                                    html.Small(
                                                        [
                                                            html.Span(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-tasks me-1",
                                                                        style={
                                                                            "color": COLOR_PALETTE[
                                                                                "items"
                                                                            ]
                                                                        },
                                                                    ),
                                                                    html.Strong(
                                                                        f"{completed_items}"
                                                                    ),
                                                                    f" of {actual_total_items} items",
                                                                ],
                                                                className="me-3",
                                                            ),
                                                            html.Span(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-chart-line me-1",
                                                                        style={
                                                                            "color": COLOR_PALETTE[
                                                                                "points"
                                                                            ]
                                                                        },
                                                                    ),
                                                                    html.Strong(
                                                                        f"{completed_points}"
                                                                    ),
                                                                    f" of {actual_total_points} points",
                                                                ]
                                                            ),
                                                        ],
                                                        className="text-muted mt-2 d-block",
                                                    ),
                                                ],
                                                className="d-flex justify-content-center",
                                            ),
                                        ],
                                        style={
                                            "display": "block"
                                            if similar_percentages
                                            else "none"
                                        },
                                        className="mb-3",
                                    ),
                                    # Separate progress bars for different percentages
                                    html.Div(
                                        [
                                            # Items progress
                                            html.Div(
                                                [
                                                    html.Div(
                                                        className="d-flex justify-content-between align-items-center mb-1",
                                                        children=[
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
                                                                    "Items Progress",
                                                                ],
                                                                className="fw-medium",
                                                            ),
                                                            html.Small(
                                                                f"{items_percentage}% Complete",
                                                                className="text-muted",
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className="progress",
                                                        style={
                                                            "height": "16px",
                                                            "borderRadius": "4px",
                                                            "overflow": "hidden",
                                                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                                        },
                                                        children=[
                                                            html.Div(
                                                                className="progress-bar bg-info",
                                                                style={
                                                                    "width": f"{items_percentage}%",
                                                                    "height": "100%",
                                                                    "transition": "width 1s ease",
                                                                },
                                                            ),
                                                        ],
                                                    ),
                                                    html.Small(
                                                        f"{completed_items} of {actual_total_items} items ({total_items} remaining)",
                                                        className="text-muted mt-1 d-block",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Points progress
                                            html.Div(
                                                [
                                                    html.Div(
                                                        className="d-flex justify-content-between align-items-center mb-1",
                                                        children=[
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
                                                                    "Points Progress",
                                                                ],
                                                                className="fw-medium",
                                                            ),
                                                            html.Small(
                                                                f"{points_percentage}% Complete",
                                                                className="text-muted",
                                                            ),
                                                        ],
                                                    ),
                                                    html.Div(
                                                        className="progress",
                                                        style={
                                                            "height": "16px",
                                                            "borderRadius": "4px",
                                                            "overflow": "hidden",
                                                            "boxShadow": "inset 0 1px 2px rgba(0,0,0,.1)",
                                                        },
                                                        children=[
                                                            html.Div(
                                                                className="progress-bar bg-warning",
                                                                style={
                                                                    "width": f"{points_percentage}%",
                                                                    "height": "100%",
                                                                    "transition": "width 1s ease",
                                                                },
                                                            ),
                                                        ],
                                                    ),
                                                    html.Small(
                                                        f"{completed_points} of {actual_total_points} points ({remaining_points} remaining)",
                                                        className="text-muted mt-1 d-block",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        style={
                                            "display": "block"
                                            if not similar_percentages
                                            else "none"
                                        },
                                        className="mb-3",
                                    ),
                                ],
                                className="mb-4",
                            ),
                            # Deadline card
                            html.Div(
                                [
                                    html.Div(
                                        className="d-flex align-items-center mb-2",
                                        children=[
                                            html.I(
                                                className="fas fa-calendar-day fs-3 me-3",
                                                style={
                                                    "color": COLOR_PALETTE["deadline"]
                                                },
                                            ),
                                            html.Div(
                                                [
                                                    html.Div(
                                                        "Project Deadline",
                                                        className="text-muted small",
                                                    ),
                                                    html.Div(
                                                        deadline_date_str,
                                                        className="fs-5 fw-bold",
                                                    ),
                                                ]
                                            ),
                                        ],
                                    ),
                                    # Days remaining visualization
                                    html.Div(
                                        [
                                            html.Div(
                                                className="d-flex justify-content-between align-items-center",
                                                children=[
                                                    html.Small(
                                                        "Today", className="text-muted"
                                                    ),
                                                    html.Small(
                                                        "Deadline",
                                                        className="text-muted",
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                className="progress mt-1 mb-1",
                                                style={
                                                    "height": "8px",
                                                    "borderRadius": "4px",
                                                },
                                                children=[
                                                    html.Div(
                                                        className="progress-bar bg-danger",
                                                        style={
                                                            "width": f"{max(5, min(100, (100 - (days_to_deadline / (days_to_deadline + 30) * 100))))}%",
                                                        },
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                html.Strong(
                                                    f"{days_to_deadline} days remaining",
                                                    style={
                                                        "color": "green"
                                                        if days_to_deadline > 30
                                                        else "orange"
                                                        if days_to_deadline > 14
                                                        else "red"
                                                    },
                                                ),
                                                className="text-center mt-1",
                                            ),
                                        ],
                                        className="mt-2",
                                    ),
                                ],
                                className="p-3 border rounded",
                                style={
                                    "background": "linear-gradient(to bottom, rgba(220, 53, 69, 0.05), rgba(255, 255, 255, 1))",
                                    "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                },
                            ),
                        ],
                        className="p-3 border rounded h-100",
                    ),
                ],
                className="mb-4",
            ),
            # Reorganized layout: Completion Forecast and Weekly Velocity side by side
            dbc.Row(
                [
                    # Left column - Completion Forecast
                    dbc.Col(
                        [
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-calendar-check me-2",
                                        style={"color": "#20c997"},
                                    ),
                                    "Completion Forecast",
                                ],
                                className="mb-3 border-bottom pb-2 d-flex align-items-center",
                            ),
                            html.Div(
                                [
                                    # Subtitle with methodology information
                                    html.Div(
                                        html.Small(
                                            "Based on PERT methodology (optimistic, most likely, and pessimistic estimates)",
                                            className="text-muted mb-3 d-block text-center",
                                        ),
                                        className="mb-3",
                                    ),
                                    # Items Forecast Card
                                    html.Div(
                                        [
                                            # Header with icon
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
                                                        "Items Forecast",
                                                        className="fw-medium",
                                                    ),
                                                ],
                                                className="d-flex align-items-center mb-3",
                                            ),
                                            # Table header
                                            html.Div(
                                                className="d-flex mb-2 px-3 py-2 bg-light rounded-top border-bottom",
                                                style={"fontSize": "0.8rem"},
                                                children=[
                                                    html.Div(
                                                        "Method",
                                                        className="text-muted",
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        "Completion Date",
                                                        className="text-muted text-center",
                                                        style={"width": "45%"},
                                                    ),
                                                    html.Div(
                                                        "Timeframe",
                                                        className="text-muted text-end",
                                                        style={"width": "30%"},
                                                    ),
                                                ],
                                            ),
                                            # PERT row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({items_color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                                                    "borderRadius": "4px",
                                                    "border": f"1px solid {items_color}",
                                                },
                                                children=[
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "PERT",
                                                                className="fw-bold",
                                                            ),
                                                            html.I(
                                                                className="fas fa-star-of-life ms-2",
                                                                style={
                                                                    "fontSize": "0.7rem",
                                                                    "color": items_color,
                                                                },
                                                            ),
                                                        ],
                                                        style={"width": "25%"},
                                                        className="d-flex align-items-center",
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            items_completion_str,
                                                            style={
                                                                "color": items_color
                                                            },
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{pert_time_items:.1f}d ({pert_time_items / 7:.1f}w)",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Average row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_avg_items_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_avg_items != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Average",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            avg_items_completion_str,
                                                            style={
                                                                "color": weeks_avg_items_color
                                                            }
                                                            if weeks_avg_items
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{avg_items_days:.1f}d ({weeks_avg_items:.1f}w)"
                                                            if weeks_avg_items
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Median row
                                            html.Div(
                                                className="d-flex align-items-center p-2",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_med_items_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_med_items != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Median",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            med_items_completion_str,
                                                            style={
                                                                "color": weeks_med_items_color
                                                            }
                                                            if weeks_med_items
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{med_items_days:.1f}d ({weeks_med_items:.1f}w)"
                                                            if weeks_med_items
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="mb-4 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Points Forecast Card
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Points Forecast",
                                                        className="fw-medium",
                                                    ),
                                                ],
                                                className="d-flex align-items-center mb-3",
                                            ),
                                            # Table header
                                            html.Div(
                                                className="d-flex mb-2 px-3 py-2 bg-light rounded-top border-bottom",
                                                style={"fontSize": "0.8rem"},
                                                children=[
                                                    html.Div(
                                                        "Method",
                                                        className="text-muted",
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        "Completion Date",
                                                        className="text-muted text-center",
                                                        style={"width": "45%"},
                                                    ),
                                                    html.Div(
                                                        "Timeframe",
                                                        className="text-muted text-end",
                                                        style={"width": "30%"},
                                                    ),
                                                ],
                                            ),
                                            # PERT row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({points_color == 'green' and '40,167,69' or '220,53,69'},0.08)",
                                                    "borderRadius": "4px",
                                                    "border": f"1px solid {points_color}",
                                                },
                                                children=[
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                "PERT",
                                                                className="fw-bold",
                                                            ),
                                                            html.I(
                                                                className="fas fa-star-of-life ms-2",
                                                                style={
                                                                    "fontSize": "0.7rem",
                                                                    "color": points_color,
                                                                },
                                                            ),
                                                        ],
                                                        style={"width": "25%"},
                                                        className="d-flex align-items-center",
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            points_completion_str,
                                                            style={
                                                                "color": points_color
                                                            },
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{pert_time_points:.1f}d ({pert_time_points / 7:.1f}w)",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Average row
                                            html.Div(
                                                className="d-flex align-items-center p-2 mb-1",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_avg_points_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_avg_points != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Average",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            avg_points_completion_str,
                                                            style={
                                                                "color": weeks_avg_points_color
                                                            }
                                                            if weeks_avg_points
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{avg_points_days:.1f}d ({weeks_avg_points:.1f}w)"
                                                            if weeks_avg_points
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                            # Median row
                                            html.Div(
                                                className="d-flex align-items-center p-2",
                                                style={
                                                    "backgroundColor": f"rgba({weeks_med_points_color == 'green' and '40,167,69' or '220,53,69'},0.05)",
                                                    "borderRadius": "4px",
                                                }
                                                if weeks_med_points != float("inf")
                                                else {},
                                                children=[
                                                    html.Div(
                                                        html.Span(
                                                            "Median",
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "25%"},
                                                    ),
                                                    html.Div(
                                                        html.Span(
                                                            med_points_completion_str,
                                                            style={
                                                                "color": weeks_med_points_color
                                                            }
                                                            if weeks_med_points
                                                            != float("inf")
                                                            else {},
                                                            className="fw-medium",
                                                        ),
                                                        style={"width": "45%"},
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        html.Small(
                                                            f"{med_points_days:.1f}d ({weeks_med_points:.1f}w)"
                                                            if weeks_med_points
                                                            != float("inf")
                                                            else "∞",
                                                            className="text-muted",
                                                        ),
                                                        style={"width": "30%"},
                                                        className="text-end",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="mb-3 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Legend
                                    html.Div(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-star-of-life me-1",
                                                    style={"fontSize": "0.6rem"},
                                                ),
                                                "PERT forecast combines optimistic, most likely, and pessimistic estimates",
                                            ],
                                            className="text-muted fst-italic text-center",
                                        ),
                                        className="mt-2",
                                    ),
                                ],
                                className="p-3 border rounded h-100",
                            ),
                        ],
                        width=12,
                        lg=6,
                        className="mb-3 mb-lg-0",
                    ),
                    # Right column - Weekly Velocity with improved mobile responsiveness
                    dbc.Col(
                        [
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-tachometer-alt me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "Weekly Velocity",
                                ],
                                className="mb-3 border-bottom pb-2 d-flex align-items-center",
                            ),
                            html.Div(
                                [
                                    # Subtitle with period information
                                    html.Div(
                                        html.Small(
                                            "Based on last 10 weeks of data",
                                            className="text-muted mb-3 d-block text-center",
                                        ),
                                        className="mb-3",
                                    ),
                                    # Items Velocity Card
                                    html.Div(
                                        [
                                            # Header with icon
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
                                                        "Items", className="fw-medium"
                                                    ),
                                                ],
                                                className="d-flex align-items-center justify-content-center mb-3",
                                            ),
                                            # Velocity metrics - using flex layout for better responsiveness
                                            html.Div(
                                                [
                                                    # Average Items
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Average",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{avg_items_icon} me-1",
                                                                                style={
                                                                                    "color": avg_items_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if avg_items_trend > 0 else ''}{avg_items_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": avg_items_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{avg_weekly_items}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#0d6efd"
                                                                    },
                                                                ),
                                                                className="text-center mb-2",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{10 + (i * 3) + (5 if i % 3 == 0 else -5)}px",
                                                                                        "backgroundColor": "#0d6efd",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of completed items over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginRight": "0.5rem",
                                                        },
                                                    ),
                                                    # Median Items
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Median",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{med_items_icon} me-1",
                                                                                style={
                                                                                    "color": med_items_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if med_items_trend > 0 else ''}{med_items_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": med_items_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{med_weekly_items}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#6c757d"
                                                                    },
                                                                ),
                                                                className="text-center mb-2",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{8 + (i * 2) + (4 if i % 2 == 0 else -3)}px",
                                                                                        "backgroundColor": "#6c757d",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of median completed items over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginLeft": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                className="d-flex flex-wrap",
                                                style={
                                                    "marginLeft": "-0.5rem",
                                                    "marginRight": "-0.5rem",
                                                },
                                            ),
                                        ],
                                        className="mb-4 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(13, 110, 253, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Points Velocity Card
                                    html.Div(
                                        [
                                            # Header with icon
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar me-2",
                                                        style={
                                                            "color": COLOR_PALETTE[
                                                                "points"
                                                            ]
                                                        },
                                                    ),
                                                    html.Span(
                                                        "Points", className="fw-medium"
                                                    ),
                                                ],
                                                className="d-flex align-items-center justify-content-center mb-3",
                                            ),
                                            # Velocity metrics - using flex layout for better responsiveness
                                            html.Div(
                                                [
                                                    # Average Points
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Average",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{avg_points_icon} me-1",
                                                                                style={
                                                                                    "color": avg_points_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if avg_points_trend > 0 else ''}{avg_points_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": avg_points_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{avg_weekly_points}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#fd7e14"
                                                                    },
                                                                ),
                                                                className="text-center mb-1",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{12 + (i * 3) + (7 if i % 2 == 0 else -4)}px",
                                                                                        "backgroundColor": "#fd7e14",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of average points completed over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginRight": "0.5rem",
                                                        },
                                                    ),
                                                    # Median Points
                                                    html.Div(
                                                        [
                                                            # Header row with label and trend
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        "Median",
                                                                        className="fw-medium",
                                                                    ),
                                                                    html.Span(
                                                                        [
                                                                            html.I(
                                                                                className=f"{med_points_icon} me-1",
                                                                                style={
                                                                                    "color": med_points_icon_color,
                                                                                    "fontSize": "0.75rem",
                                                                                },
                                                                            ),
                                                                            f"{'+' if med_points_trend > 0 else ''}{med_points_trend}%",
                                                                        ],
                                                                        style={
                                                                            "color": med_points_icon_color
                                                                        },
                                                                        title="Change compared to previous period",
                                                                    ),
                                                                ],
                                                                className="d-flex justify-content-between align-items-center mb-2",
                                                            ),
                                                            # Value
                                                            html.Div(
                                                                html.Span(
                                                                    f"{med_weekly_points}",
                                                                    className="fs-3 fw-bold",
                                                                    style={
                                                                        "color": "#6c757d"
                                                                    },
                                                                ),
                                                                className="text-center mb-1",
                                                            ),
                                                            # Mini sparkline trend instead of progress bar
                                                            html.Div(
                                                                [
                                                                    html.Div(
                                                                        className="d-flex align-items-end justify-content-center",
                                                                        style={
                                                                            "height": "30px"
                                                                        },
                                                                        children=[
                                                                            # Simulate a 10-week sparkline with bars
                                                                            # In a real implementation, these would be dynamically generated from actual data
                                                                            *[
                                                                                html.Div(
                                                                                    className="mx-1",
                                                                                    style={
                                                                                        "width": "5px",
                                                                                        "height": f"{10 + (i * 2) + (6 if i % 3 == 0 else -2)}px",
                                                                                        "backgroundColor": "#6c757d",
                                                                                        "opacity": f"{0.4 + (i * 0.06)}",
                                                                                        "borderRadius": "1px",
                                                                                    },
                                                                                )
                                                                                for i in range(
                                                                                    10
                                                                                )
                                                                            ]
                                                                        ],
                                                                    ),
                                                                    html.Div(
                                                                        html.Small(
                                                                            "10-week trend",
                                                                            className="text-muted",
                                                                        ),
                                                                        className="text-center mt-1",
                                                                    ),
                                                                ],
                                                                title="Visual representation of median points completed over the last 10 weeks",
                                                            ),
                                                        ],
                                                        className="p-3 border rounded mb-3",
                                                        style={
                                                            "flex": "1",
                                                            "minWidth": "150px",
                                                            "marginLeft": "0.5rem",
                                                        },
                                                    ),
                                                ],
                                                className="d-flex flex-wrap",
                                                style={
                                                    "marginLeft": "-0.5rem",
                                                    "marginRight": "-0.5rem",
                                                },
                                            ),
                                        ],
                                        className="mb-3 p-3 border rounded",
                                        style={
                                            "boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px",
                                            "background": "linear-gradient(to bottom, rgba(253, 126, 20, 0.05), rgba(255, 255, 255, 1))",
                                        },
                                    ),
                                    # Info text at the bottom
                                    html.Div(
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-info-circle me-1",
                                                    style={"color": "#6c757d"},
                                                ),
                                                "10-week velocity data used for project forecasting.",
                                            ],
                                            className="text-muted fst-italic small text-center",
                                        ),
                                        className="mt-2",
                                    ),
                                ],
                                className="p-3 border rounded h-100",
                            ),
                        ],
                        width=12,
                        lg=6,
                    ),
                ],
                className="mb-4",
            ),
        ],
    )


#######################################################################
# TREND INDICATOR COMPONENT
#######################################################################


def create_trend_indicator(trend_data, metric_name="Items"):
    """
    Create a trend indicator component with arrow and percentage change.

    Args:
        trend_data: Dictionary with trend information from calculate_performance_trend
        metric_name: Name of the metric being displayed ("Items" or "Points")

    Returns:
        A Dash component with the trend indicator
    """
    # Define colors and icons based on trend direction
    trend_colors = {
        "up": "#28a745",  # Green for positive trend
        "down": "#dc3545",  # Red for negative trend
        "stable": "#6c757d",  # Gray for stable trend
    }

    trend_icons = {
        "up": "fas fa-arrow-up",
        "down": "fas fa-arrow-down",
        "stable": "fas fa-arrows-alt-h",
    }

    # Get direction, value and significance
    direction = trend_data.get("trend_direction", "stable")
    percent_change = trend_data.get("percent_change", 0)
    is_significant = trend_data.get("is_significant", False)
    weeks = trend_data.get("weeks_compared", 4)
    current_avg = trend_data.get("current_avg", 0)
    previous_avg = trend_data.get("previous_avg", 0)

    # Determine text color and font weight based on significance
    text_color = trend_colors.get(direction, "#6c757d")
    font_weight = "bold" if is_significant else "normal"

    # Build the component
    return html.Div(
        [
            html.H6(f"{metric_name} Trend (Last {weeks * 2} Weeks)", className="mb-2"),
            html.Div(
                [
                    html.I(
                        className=trend_icons.get(direction, "fas fa-arrows-alt-h"),
                        style={
                            "color": text_color,
                            "fontSize": "1.5rem",
                            "marginRight": "10px",
                        },
                    ),
                    html.Span(
                        f"{abs(percent_change)}% {'Increase' if direction == 'up' else 'Decrease' if direction == 'down' else 'Change'}",
                        style={
                            "color": text_color,
                            "fontWeight": font_weight,
                            "fontSize": "1.2rem",
                        },
                    ),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Recent Average: ", className="font-weight-bold"),
                            html.Span(f"{current_avg} {metric_name.lower()}/week"),
                        ],
                        className="mr-3",
                    ),
                    html.Div(
                        [
                            html.Span(
                                "Previous Average: ", className="font-weight-bold"
                            ),
                            html.Span(f"{previous_avg} {metric_name.lower()}/week"),
                        ],
                    ),
                ],
                className="d-flex flex-wrap small text-muted",
            ),
            # Add warning/celebration message for significant changes
            html.Div(
                html.Span(
                    "Significant change detected!" if is_significant else "",
                    className="font-italic small",
                    style={"color": text_color},
                ),
                className="mt-1",
            ),
        ],
        className="trend-indicator p-3 border rounded",
        style={
            "backgroundColor": f"rgba({','.join(map(str, [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)]))}, 0.1)"
            if (c := trend_colors.get(direction, "#6c757d"))
            else "rgba(108, 117, 125, 0.1)"
        },
    )


#######################################################################
# EXPORT BUTTONS COMPONENT
#######################################################################


def create_export_buttons(chart_id=None, statistics_data=None):
    """
    Create a row of export buttons for charts or statistics data.

    Args:
        chart_id: ID of the chart for export filename
        statistics_data: Statistics data to export (if provided, shows statistics export button)

    Returns:
        Dash Div component with export buttons
    """
    from ui.styles import create_button

    buttons = []

    if chart_id:
        # Add CSV export button for chart using the new button styling system
        csv_button = create_button(
            text="Export CSV",
            id=f"{chart_id}-csv-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-csv",
            className="me-2",
            tooltip="Export chart data as CSV",
        )
        buttons.append(csv_button)
        buttons.append(html.Div(dcc.Download(id=f"{chart_id}-csv-download")))

        # Add PNG export button as well
        png_button = create_button(
            text="Export Image",
            id=f"{chart_id}-png-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-image",
            className="me-2",
            tooltip="Export chart as image",
        )
        buttons.append(png_button)

    if statistics_data:
        # Add button for export stats using the new button styling system
        stats_button = create_button(
            text="Export Statistics",
            id="export-statistics-button",
            variant="secondary",
            size="sm",
            outline=True,
            icon_class="fas fa-file-export",
            tooltip="Export statistics data",
        )
        buttons.append(stats_button)
        buttons.append(html.Div(dcc.Download(id="export-statistics-download")))

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )


#######################################################################
# FORM VALIDATION COMPONENT
#######################################################################


def create_validation_message(message, show=False, type="invalid"):
    """
    Create a validation message for form inputs with consistent styling.

    Args:
        message (str): The validation message to display
        show (bool): Whether to show the message (default: False)
        type (str): The type of validation (valid, invalid, warning)

    Returns:
        html.Div: A validation message component
    """
    from dash import html
    from ui.styles import create_form_feedback_style

    # Determine the appropriate style class based on validation type
    class_name = "d-none"
    if show:
        if type == "valid":
            class_name = "valid-feedback d-block"
        elif type == "warning":
            class_name = "text-warning d-block"
        else:
            class_name = "invalid-feedback d-block"

    # Get the base style from the styling function
    base_style = create_form_feedback_style(type)

    # Add icon based on the type
    icon_class = ""
    if type == "valid":
        icon_class = "fas fa-check-circle me-1"
    elif type == "warning":
        icon_class = "fas fa-exclamation-triangle me-1"
    elif type == "invalid":
        icon_class = "fas fa-times-circle me-1"

    # Return the validation message component
    return html.Div(
        [html.I(className=icon_class) if icon_class else "", message],
        className=class_name,
        style=base_style,
    )


def create_button(
    text=None,
    id=None,
    variant="primary",
    size="md",
    outline=False,
    icon_class=None,
    className="",
    tooltip=None,
    disabled=False,
):
    """
    Create a standardized button with consistent styling and optional icon.

    Args:
        text: Button text (optional if icon_class provided)
        id: Component ID
        variant: Bootstrap color variant (primary, secondary, success, etc.)
        size: Button size (sm, md, lg)
        outline: Whether to use outline style
        icon_class: FontAwesome icon class (e.g., "fas fa-plus")
        className: Additional CSS classes
        tooltip: Optional tooltip text
        disabled: Whether the button is disabled

    Returns:
        A dbc.Button component with standardized styling
    """
    import dash_bootstrap_components as dbc
    from dash import html

    # Determine button style based on parameters
    color = variant
    if outline:
        color = f"outline-{variant}"

    # Determine size class
    size_class = ""
    if size == "sm":
        size_class = "btn-sm"
    elif size == "lg":
        size_class = "btn-lg"

    # Create button content with optional icon
    content = []

    # Add icon if specified
    if icon_class:
        content.append(html.I(className=f"{icon_class} me-1"))

    # Add text if specified
    if text:
        content.append(text)

    # Combine classes
    full_class_name = f"{size_class} {className}".strip()

    # Create the button
    button = dbc.Button(
        children=content,
        id=id,
        color=color,
        disabled=disabled,
        className=full_class_name,
    )

    # Wrap with tooltip if specified
    if tooltip:
        from ui.components import create_info_tooltip

        return html.Div(
            [
                button,
                create_info_tooltip(
                    id=f"{id}-tooltip" if id else None,
                    tooltip_text=tooltip,
                    target=id if id else None,
                ),
            ],
            className="d-inline-block",
        )

    return button
