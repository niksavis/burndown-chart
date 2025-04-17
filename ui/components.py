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

    # Use the provided deadline string instead of recalculating
    if deadline_str:
        deadline_date_str = deadline_str
    else:
        # Fallback to calculation if not provided
        current_date = datetime.now()
        deadline_date = current_date + timedelta(days=days_to_deadline)
        deadline_date_str = deadline_date.strftime("%Y-%m-%d")

    # Format dates for display (only format completion dates, use deadline_str directly)
    items_completion_str = items_completion_date.strftime("%Y-%m-%d")
    points_completion_str = points_completion_date.strftime("%Y-%m-%d")

    return html.Div(
        [
            # PERT Formula Section
            html.Div(
                [
                    html.H5("PERT Formula", className="mb-3 border-bottom pb-2"),
                    html.Div(
                        [
                            html.Div(
                                "E = ",
                                className="font-weight-bold mr-1",
                                style={"fontSize": "1.2rem"},
                            ),
                            dcc.Markdown(
                                r"$\frac{O + 4M + P}{6}$",
                                mathjax=True,
                                style={"display": "inline-block"},
                            ),
                            html.Div(
                                "(O=Optimistic, M=Most Likely, P=Pessimistic)",
                                className="text-muted ml-2",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="d-flex align-items-center justify-content-center mb-2",
                    ),
                ],
                className="mb-4 text-center",
            ),
            # Deadline and Forecast Section
            dbc.Row(
                [
                    # Left column - Deadline Status
                    dbc.Col(
                        [
                            html.H5(
                                "Deadline Status", className="mb-3 border-bottom pb-2"
                            ),
                            html.Div(
                                [
                                    # Deadline - reformatted to match other sections
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-calendar-day mr-2 text-primary"
                                            ),
                                            html.Span(
                                                "Deadline:",
                                                className="font-weight-bold d-block mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Date: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{deadline_date_str}",
                                                    ),
                                                ],
                                                className="ml-4 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Remaining: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{days_to_deadline} days",
                                                    ),
                                                ],
                                                className="ml-4",
                                            ),
                                        ],
                                        className="mb-3 p-2 border-bottom",
                                    ),
                                    # PERT Estimates - keep as is
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-chart-line mr-2 text-primary"
                                            ),
                                            html.Span(
                                                "PERT Estimates:",
                                                className="font-weight-bold d-block mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Items: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{pert_time_items:.1f} days",
                                                        style={
                                                            "color": items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f" (by {items_completion_str})",
                                                        className="ml-1 text-muted small",
                                                    ),
                                                ],
                                                className="ml-4 mb-1",
                                            ),
                                            html.Div(
                                                [
                                                    html.Span(
                                                        "Points: ",
                                                        className="font-weight-bold",
                                                    ),
                                                    html.Span(
                                                        f"{pert_time_points:.1f} days",
                                                        style={
                                                            "color": points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(
                                                        f" (by {points_completion_str})",
                                                        className="ml-1 text-muted small",
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
                        className="mb-3 mb-lg-0",
                    ),
                    # Right column - Completion Estimates
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
                                                        f"{weeks_avg_items:.1f}"
                                                        if weeks_avg_items
                                                        != float("inf")
                                                        else "∞",
                                                        style={
                                                            "color": weeks_avg_items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(" weeks"),
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
                                                        f"{weeks_med_items:.1f}"
                                                        if weeks_med_items
                                                        != float("inf")
                                                        else "∞",
                                                        style={
                                                            "color": weeks_med_items_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(" weeks"),
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
                                                        f"{weeks_avg_points:.1f}"
                                                        if weeks_avg_points
                                                        != float("inf")
                                                        else "∞",
                                                        style={
                                                            "color": weeks_avg_points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(" weeks"),
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
                                                        f"{weeks_med_points:.1f}"
                                                        if weeks_med_points
                                                        != float("inf")
                                                        else "∞",
                                                        style={
                                                            "color": weeks_med_points_color,
                                                            "fontWeight": "bold",
                                                        },
                                                    ),
                                                    html.Span(" weeks"),
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
                                                    # Average Items
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
                                                    # Median Items
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
                                                    # Average Points
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
                                                    # Median Points
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


def create_export_buttons(chart_id, statistics_data=None):
    """
    Create buttons for exporting chart as PNG and data as CSV.

    Args:
        chart_id: ID of the chart to export
        statistics_data: Optional statistics data for CSV export

    Returns:
        A Dash component with export buttons
    """
    return html.Div(
        [
            dbc.Button(
                [html.I(className="fas fa-file-image mr-2"), "Save as PNG"],
                id=f"{chart_id}-png-button",
                color="outline-primary",
                size="sm",
                className="mr-2",
            ),
            dbc.Button(
                [html.I(className="fas fa-file-csv mr-2"), "Export Data (CSV)"],
                id=f"{chart_id}-csv-button",
                color="outline-secondary",
                size="sm",
            ),
            # Hidden download component for CSV export
            dcc.Download(id=f"{chart_id}-csv-download"),
            # Hidden div to store timestamp when export was triggered
            html.Div(id=f"{chart_id}-export-timestamp", style={"display": "none"}),
        ],
        className="d-flex mb-3 mt-2",
    )
