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

# Import from configuration
from configuration.config import COLOR_PALETTE
# HELP_TEXTS is imported but not directly used in this file

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
):
    """
    Create the PERT information table.

    Args:
        pert_time_items: PERT estimate for items (days)
        pert_time_points: PERT estimate for points (days)
        days_to_deadline: Days remaining until deadline
        avg_weekly_items: Average weekly items completed (last 10 weeks)
        avg_weekly_points: Average weekly points completed (last 10 weeks)
        med_weekly_items: Median weekly items completed (last 10 weeks)
        med_weekly_points: Median weekly points completed (last 10 weeks)
        pert_factor: Number of data points used for optimistic/pessimistic scenarios

    Returns:
        Dash component with PERT information table
    """
    # Determine colors based on if we'll meet the deadline
    items_color = "green" if pert_time_items <= days_to_deadline else "red"
    points_color = "green" if pert_time_points <= days_to_deadline else "red"

    return html.Div(
        [
            html.Table(
                [
                    html.Tbody(
                        [
                            # PERT formula as first row in the table
                            html.Tr(
                                [
                                    html.Td(
                                        "PERT Formula:",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            dcc.Markdown(
                                                r"$E = \frac{O + 4M + P}{6}$",
                                                mathjax=True,
                                                style={"display": "inline-block"},
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Items):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_items:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": items_color,
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Estimated Days (Points):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{pert_time_points:.1f}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={
                                            "color": points_color,
                                            "fontWeight": "bold",
                                        },
                                    ),
                                ]
                            ),
                            html.Tr(
                                [
                                    html.Td(
                                        "Deadline in:",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{days_to_deadline}",
                                            html.Span(
                                                " days",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add separator between deadline and metrics
                            html.Tr(
                                [
                                    html.Td(
                                        html.Hr(style={"margin": "10px 0"}),
                                        colSpan=2,
                                    )
                                ]
                            ),
                            # Add Average Weekly Items
                            html.Tr(
                                [
                                    html.Td(
                                        "Avg Weekly Items (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{avg_weekly_items}",
                                            html.Span(
                                                " items/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Median Weekly Items
                            html.Tr(
                                [
                                    html.Td(
                                        "Med Weekly Items (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{med_weekly_items}",
                                            html.Span(
                                                " items/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Average Weekly Points
                            html.Tr(
                                [
                                    html.Td(
                                        "Avg Weekly Points (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{avg_weekly_points}",
                                            html.Span(
                                                " points/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                            # Add Median Weekly Points
                            html.Tr(
                                [
                                    html.Td(
                                        "Med Weekly Points (10w):",
                                        className="text-right pr-2",
                                        style={"fontWeight": "bold"},
                                    ),
                                    html.Td(
                                        [
                                            f"{med_weekly_points}",
                                            html.Span(
                                                " points/week",
                                                style={
                                                    "fontSize": "0.9em",
                                                    "color": "#666",
                                                },
                                            ),
                                        ],
                                        style={"fontWeight": "bold"},
                                    ),
                                ]
                            ),
                        ]
                    )
                ],
                className="table table-borderless",
                style={
                    "margin": "0 auto",
                    "width": "auto",
                    "border": "1px solid #eee",
                    "borderRadius": "5px",
                    "padding": "10px",
                },
            )
        ]
    )
