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
from datetime import datetime

# Import from other modules
from config import HELP_TEXTS, COLOR_PALETTE
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
    Create the input parameters card component.

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
                    # PERT factor and Deadline
                    dbc.Row(
                        [
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
                                        marks={i: str(i) for i in range(3, 16, 2)},
                                        step=1,
                                    ),
                                ],
                                width=12,
                                lg=6,
                            ),
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
                                        className="form-control",
                                    ),
                                ],
                                width=12,
                                lg=6,
                            ),
                        ]
                    ),
                    html.Br(),
                    # Estimated Items and Total Items
                    dbc.Row(
                        [
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
                                        value=current_settings["estimated_items"],
                                        min=0,
                                        step=1,
                                    ),
                                ],
                                width=12,
                                lg=6,
                            ),
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
                                lg=6,
                            ),
                        ]
                    ),
                    html.Br(),
                    # Estimated Points and Total Points
                    dbc.Row(
                        [
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
                                        value=current_settings["estimated_points"],
                                        min=0,
                                        step=1,
                                    ),
                                ],
                                width=12,
                                lg=6,
                            ),
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
                                                style={"backgroundColor": "#f8f9fa"},
                                            ),
                                            dbc.InputGroupText(
                                                html.I(className="fas fa-calculator"),
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
                                lg=6,
                            ),
                        ]
                    ),
                    html.Br(),
                    # CSV Upload section
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
                                            "margin": "10px 0",
                                        },
                                        multiple=False,
                                    ),
                                ],
                                width=12,
                            ),
                        ]
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
