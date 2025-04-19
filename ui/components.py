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
            dbc.ModalFooter(dbc.Button("Close", id="close-help", className="ml-auto")),
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
                        "Project Overview",
                        className="mb-3 border-bottom pb-2",
                    ),
                    # Progress bar with percentage inside
                    html.Div(
                        [
                            # Combined progress bar - shown when percentages are similar
                            html.Div(
                                [
                                    html.Div(
                                        className="progress",
                                        style={
                                            "height": "24px",
                                            "position": "relative",
                                        },
                                        children=[
                                            html.Div(
                                                className="progress-bar bg-primary",
                                                style={
                                                    "width": f"{items_percentage}%",
                                                    "height": "100%",
                                                },
                                            ),
                                            html.Span(
                                                f"{items_percentage}%",
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
                                                    if items_percentage > 50
                                                    else "black",
                                                    "fontWeight": "bold",
                                                },
                                            ),
                                        ],
                                    ),
                                    html.Small(
                                        [
                                            f"{completed_items} of {actual_total_items} items ({total_items} remaining)",
                                            html.Span(
                                                " • ",
                                                className="mx-2 text-muted",
                                            ),
                                            f"{completed_points} of {actual_total_points} points ({remaining_points} remaining)",
                                        ],
                                        className="text-muted mt-1 d-block",
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
                                    # Items progress bar
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
                                            html.Div(
                                                className="progress",
                                                style={
                                                    "height": "24px",
                                                    "position": "relative",
                                                },
                                                children=[
                                                    html.Div(
                                                        className="progress-bar bg-info",
                                                        style={
                                                            "width": f"{items_percentage}%",
                                                            "height": "100%",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{items_percentage}%",
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
                                                            if items_percentage > 50
                                                            else "black",
                                                            "fontWeight": "bold",
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
                                    # Points progress bar
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
                                            html.Div(
                                                className="progress",
                                                style={
                                                    "height": "24px",
                                                    "position": "relative",
                                                },
                                                children=[
                                                    html.Div(
                                                        className="progress-bar bg-warning",
                                                        style={
                                                            "width": f"{points_percentage}%",
                                                            "height": "100%",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f"{points_percentage}%",
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
                                                            if points_percentage > 50
                                                            else "black",
                                                            "fontWeight": "bold",
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
                            ),
                            # Added deadline information below progress bars
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-calendar-day mr-2",
                                        style={"color": COLOR_PALETTE["deadline"]},
                                    ),
                                    html.Span(
                                        f"Deadline: {deadline_date_str} ({days_to_deadline} days remaining)",
                                        style={"fontWeight": "bold"},
                                    ),
                                ],
                                className="mt-3 d-flex align-items-center",
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                className="p-3 border rounded mb-4",
            ),
            # Deadline and Forecast Section in one-column layout (removing Deadline Status column)
            dbc.Row(
                [
                    # Right column - Completion Forecast (now full width)
                    dbc.Col(
                        [
                            html.H5(
                                "Completion Forecast",
                                className="mb-3 border-bottom pb-2",
                            ),
                            html.Div(
                                [
                                    # Items completion
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-tasks mr-2 text-primary"
                                            ),
                                            html.Span(
                                                "Items Forecast:",
                                                className="font-weight-bold d-block mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "By Average: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{avg_items_completion_enhanced}",
                                                        style={
                                                            "color": weeks_avg_items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "By Median: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{med_items_completion_enhanced}",
                                                        style={
                                                            "color": weeks_med_items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4 mb-1",
                                            ),
                                            # PERT estimate for Items
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "PERT: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{items_completion_enhanced}",
                                                        style={
                                                            "color": items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4",
                                            ),
                                        ],
                                        className="mb-3 p-2 border-bottom",
                                    ),
                                    # Points completion
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-chart-bar mr-2 text-primary"
                                            ),
                                            html.Span(
                                                "Points Forecast:",
                                                className="font-weight-bold d-block mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "By Average: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{avg_points_completion_enhanced}",
                                                        style={
                                                            "color": weeks_avg_points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "By Median: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{med_points_completion_enhanced}",
                                                        style={
                                                            "color": weeks_med_points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4",
                                            ),
                                            # Add PERT estimate for Points
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "PERT: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{points_completion_enhanced}",
                                                        style={
                                                            "color": points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                ],
                                                className="ml-4",
                                            ),
                                        ],
                                        className="mb-1 p-2",
                                    ),
                                ],
                                className="p-3 border rounded",
                            ),
                        ],
                        width=12,
                        lg=6,
                    ),
                ],
                className="mb-4",
            ),
            # Weekly Velocity Metrics Section - add more top margin
            html.Div(
                [
                    html.H5(
                        "Weekly Velocity (Last 10 Weeks)",
                        className="mb-3 border-bottom pb-2",
                    ),
                    dbc.Row(
                        [
                            # Items Velocity
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-tasks mr-2 text-primary"
                                                    ),
                                                    "Items",
                                                ],
                                                className="text-center mb-3 border-bottom pb-2",
                                            ),
                                            html.Div(
                                                [
                                                    # Average Items with trend indicator
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{avg_weekly_items}",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": "#007bff",
                                                                },
                                                            ),
                                                            # Add trend indicator icon
                                                            html.I(
                                                                className=f"{avg_items_icon} ml-2",
                                                                style={
                                                                    "color": avg_items_icon_color,
                                                                    "fontSize": "1.2rem",
                                                                },
                                                                title=f"{'+' if avg_items_trend > 0 else ''}{avg_items_trend}% compared to previous period",
                                                            ),
                                                            html.Span(
                                                                " items/week",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        "Average",
                                                        className="text-center text-muted small",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(
                                                [
                                                    # Median Items with trend indicator
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{med_weekly_items}",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": "#6c757d",
                                                                },
                                                            ),
                                                            # Add trend indicator icon
                                                            html.I(
                                                                className=f"{med_items_icon} ml-2",
                                                                style={
                                                                    "color": med_items_icon_color,
                                                                    "fontSize": "1.2rem",
                                                                },
                                                                title=f"{'+' if med_items_trend > 0 else ''}{med_items_trend}% compared to previous period",
                                                            ),
                                                            html.Span(
                                                                " items/week",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        "Median",
                                                        className="text-center text-muted small",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="p-3 border rounded h-100",
                                    ),
                                ],
                                width=12,
                                md=6,
                                className="mb-3 mb-md-0",
                            ),
                            # Points Velocity
                            dbc.Col(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-bar mr-2 text-primary"
                                                    ),
                                                    "Points",
                                                ],
                                                className="text-center mb-3 border-bottom pb-2",
                                            ),
                                            html.Div(
                                                [
                                                    # Average Points with trend indicator
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{avg_weekly_points}",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": "#fd7e14",
                                                                },
                                                            ),
                                                            # Add trend indicator icon
                                                            html.I(
                                                                className=f"{avg_points_icon} ml-2",
                                                                style={
                                                                    "color": avg_points_icon_color,
                                                                    "fontSize": "1.2rem",
                                                                },
                                                                title=f"{'+' if avg_points_trend > 0 else ''}{avg_points_trend}% compared to previous period",
                                                            ),
                                                            html.Span(
                                                                " points/week",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        "Average",
                                                        className="text-center text-muted small",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            html.Div(
                                                [
                                                    # Median Points with trend indicator
                                                    html.Div(
                                                        [
                                                            html.Span(
                                                                f"{med_weekly_points}",
                                                                style={
                                                                    "fontSize": "1.5rem",
                                                                    "fontWeight": "bold",
                                                                    "color": "#6c757d",
                                                                },
                                                            ),
                                                            # Add trend indicator icon
                                                            html.I(
                                                                className=f"{med_points_icon} ml-2",
                                                                style={
                                                                    "color": med_points_icon_color,
                                                                    "fontSize": "1.2rem",
                                                                },
                                                                title=f"{'+' if med_points_trend > 0 else ''}{med_points_trend}% compared to previous period",
                                                            ),
                                                            html.Span(
                                                                " points/week",
                                                                className="text-muted ml-1",
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    html.Div(
                                                        "Median",
                                                        className="text-center text-muted small",
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="p-3 border rounded h-100",
                                    ),
                                ],
                                width=12,
                                md=6,
                            ),
                        ],
                    ),
                ],
                # Add more top margin to push the section down
                className="mt-4",  # Added top margin
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
    buttons = []

    if chart_id:
        # Add CSV export button for chart
        buttons.append(
            dbc.Button(
                [html.I(className="fas fa-file-csv mr-2"), "Export CSV"],
                id=f"{chart_id}-csv-button",
                color="secondary",
                size="sm",
                className="mr-2",
            )
        )
        buttons.append(html.Div(dcc.Download(id=f"{chart_id}-csv-download")))

    if statistics_data:
        # Add button for export stats
        buttons.append(
            dbc.Button(
                [html.I(className="fas fa-file-export mr-2"), "Export Statistics"],
                id="export-statistics-button",
                color="secondary",
                size="sm",
                className="mr-2",
            )
        )
        buttons.append(html.Div(dcc.Download(id="export-statistics-download")))

    return html.Div(
        buttons,
        className="d-flex justify-content-end mb-3",
    )
