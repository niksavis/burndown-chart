"""
Forecast Card Components

This module provides forecast-related card components including:
- Main forecast graph visualization
- Forecast methodology explanation
- Items per week forecast information
- Points per week forecast information

All forecast cards use PERT (Program Evaluation and Review Technique)
methodology for three-point estimation.
"""

from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html

from configuration import COLOR_PALETTE
from configuration.settings import CHART_HELP_TEXTS
from ui.styles import (
    create_card_header_with_tooltip,
    create_rhythm_text,
    create_standardized_card,
)
from ui.tooltip_utils import (
    create_dismissible_tooltip,
    create_enhanced_tooltip,
    create_expandable_tooltip,
    create_info_tooltip,
)


def create_forecast_graph_card() -> dbc.Card:
    """
    Create the forecast graph card component with customized download filename.

    Returns:
        Dash Card component with the forecast graph
    """
    # Generate the current date for the filename
    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    # Create the card header with tooltip and Phase 9.2 Progressive Disclosure help button
    header_content = create_card_header_with_tooltip(
        "Forecast Graph",
        tooltip_id="forecast-graph",
        tooltip_text=CHART_HELP_TEXTS["forecast_explanation"],
        help_key="forecast_graph_overview",
        help_category="forecast",
    )

    # Create the card body content
    body_content = dcc.Graph(
        id="forecast-graph",
        style={
            "height": "700px"
        },  # Updated from 650px to match the height in apply_layout_settings
        config={
            # Only specify the filename, let Plotly handle the rest of the export settings
            "toImageButtonOptions": {
                "filename": default_filename,
            },
        },
    )

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-2",  # Less padding to maximize graph space
        shadow="sm",
    )


def create_forecast_info_card() -> dbc.Card:
    """
    Create the forecast methodology information card component with concise explanation.

    Returns:
        Dash Card component with concise forecast methodology explanation
    """
    # Generate a unique ID for this collapse component
    collapse_id = "forecast-info-collapse"

    # Create the card body content with optimized layout
    body_content = html.Div(
        [
            # Concise introduction paragraph with enhanced PERT methodology tooltip
            create_rhythm_text(
                [
                    html.Strong("PERT Forecast: "),
                    "Estimates based on optimistic, most likely, and pessimistic scenarios from your historical data.",
                    create_expandable_tooltip(
                        id_suffix="pert-methodology-main",
                        summary_text="PERT uses 3-point estimation for realistic forecasts",
                        detailed_text=CHART_HELP_TEXTS["pert_forecast_methodology"],
                        variant="primary",
                        placement="right",
                    ),
                ],
                element_type="paragraph",
            ),
            # Compact list with less styling and more concise descriptions
            html.Div(
                className="row g-2 mb-2",
                children=[
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Div(
                                    [
                                        html.Strong("Line Colors:"),
                                        create_dismissible_tooltip(
                                            id_suffix="chart-legend-colors",
                                            help_text=CHART_HELP_TEXTS[
                                                "chart_legend_explained"
                                            ],
                                            variant="info",
                                            placement="top",
                                        ),
                                    ]
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Blue",
                                                    style={
                                                        "color": COLOR_PALETTE["items"],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Orange",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "points"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Most likely",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Teal",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "optimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Gold",
                                                    style={  # Fixed double curly braces to single
                                                        "color": "rgb(184, 134, 11)",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Optimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Indigo",
                                                    style={
                                                        "color": COLOR_PALETTE[
                                                            "pessimistic"
                                                        ],
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                "/",
                                                html.Span(
                                                    "Brown",
                                                    style={
                                                        "color": "rgb(165, 42, 42)",
                                                    },
                                                ),
                                                ": Pessimistic",
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                html.Span(
                                                    "Red",
                                                    style={
                                                        "color": "red",
                                                        "fontWeight": "bold",
                                                    },
                                                ),
                                                ": Deadline",
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                    html.Div(
                        className="col-12 col-md-6",
                        children=html.Div(
                            className="border rounded p-2",
                            children=[
                                html.Div(
                                    [
                                        html.Strong("Reading Guide:"),
                                        create_enhanced_tooltip(
                                            id_suffix="reading-guide-enhanced",
                                            help_text=CHART_HELP_TEXTS[
                                                "historical_data_influence"
                                            ],
                                            variant="success",
                                            placement="left",
                                            smart_positioning=True,
                                            icon_class="fas fa-chart-line",
                                        ),
                                    ]
                                ),
                                html.Ul(
                                    [
                                        html.Li(
                                            [
                                                "Solid lines: Historical data ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "chart_legend_explained"
                                                    ],
                                                    "Visual legend and line type meanings",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Dashed/dotted: Forecasts ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "forecast_confidence_bands"
                                                    ],
                                                    "Understanding forecast uncertainty ranges",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Scope changes: Chart annotations ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "scope_change_indicators"
                                                    ],
                                                    "How scope changes are shown on the main chart",
                                                ),
                                            ]
                                        ),
                                        html.Li(
                                            [
                                                "Data points: Accuracy factor ",
                                                create_info_tooltip(
                                                    CHART_HELP_TEXTS[
                                                        "data_points_precision"
                                                    ],
                                                    "How number of data points affects forecast precision",
                                                ),
                                            ]
                                        ),
                                    ],
                                    className="mb-0 ps-3",
                                    style={"fontSize": "0.9rem"},
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
        style={"textAlign": "left"},
    )

    # Return a card with collapsible body content
    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "forecast-info",
                                        "How to interpret the forecast graph.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(body_content, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mb-3 shadow-sm mt-3" to "my-2" for consistent 8px margins
    )


def create_items_forecast_info_card(
    statistics_df: pd.DataFrame | None = None, pert_data: dict | None = None
) -> dbc.Card:
    """
    Create a concise forecast information card for the Items per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with items forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
        recent_df["year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "items-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Blue Bars",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed items",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Dark Blue Line",
                                            style={
                                                "color": "#0047AB",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["items"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Items Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "items-forecast-info",
                                        "Understanding the weekly items forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",  # Changed from "mt-3 mb-2 shadow-sm" to "my-2" for consistent 8px margins
    )


def create_points_forecast_info_card(
    statistics_df: pd.DataFrame | None = None, pert_data: dict | None = None
) -> dbc.Card:
    """
    Create a concise forecast information card for the Points per Week tab.

    Args:
        statistics_df: DataFrame containing the project statistics (optional)
        pert_data: Dictionary containing PERT analysis data (optional)

    Returns:
        Dash Card component with points forecast explanation
    """

    # Extract metrics from statistics if available
    if statistics_df is not None and not statistics_df.empty:
        # Convert to datetime to ensure proper week grouping
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(
            recent_df["date"], format="mixed", errors="coerce"
        )
        recent_df["week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
        recent_df["year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

        # Use tail(10) to focus on recent data
        recent_df = recent_df.tail(10)

    # Generate a unique ID for this collapse component
    collapse_id = "points-forecast-info-collapse"

    # The card content with chart elements and forecast method
    chart_info = html.Div(
        className="row g-3",
        children=[
            # Column 1: Chart Elements
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "Chart Elements",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Span(
                                            "Orange Bars",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Historical weekly completed points",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Tomato Line",
                                            style={
                                                "color": "#FF6347",
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Weighted 4-week moving average",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Span(
                                            "Patterned Bar",
                                            style={
                                                "color": COLOR_PALETTE["points"],
                                                "fontWeight": "bold",
                                            },
                                        ),
                                        ": Next week's forecast with confidence interval",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
            # Column 2: Forecast Method
            html.Div(
                className="col-12 col-md-6",
                children=html.Div(
                    className="border rounded p-2 h-100",
                    children=[
                        html.H6(
                            "PERT Forecast Method",
                            className="mb-2",
                            style={"fontSize": "0.875rem", "fontWeight": "600"},
                        ),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Strong("Most Likely: "),
                                        "Average of recent weekly data",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Optimistic: "),
                                        "Average of highest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Pessimistic: "),
                                        "Average of lowest performing weeks",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Strong("Weighted Average: "),
                                        "Recent weeks weighted [10%, 20%, 30%, 40%]",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
        ],
    )

    return dbc.Card(
        [
            dbc.CardHeader(
                dbc.Row(
                    [
                        dbc.Col(
                            html.H5(
                                "Points Forecast Information",
                                className="d-inline mb-0",
                                style={"fontSize": "0.875rem", "fontWeight": "600"},
                            ),
                            className="col-10 col-lg-11",  # Explicit Bootstrap column classes
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"{collapse_id}-button",
                                        color="link",
                                        size="sm",
                                        className="mobile-touch-target-sm border-0",
                                    ),
                                    create_info_tooltip(
                                        "points-forecast-info",
                                        "Understanding the weekly points forecast chart and trends.",
                                    ),
                                ],
                                className="d-flex justify-content-end align-items-center",
                            ),
                            className="col-2 col-lg-1",  # Explicit Bootstrap column classes
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                className="py-2 px-3 d-flex justify-content-between align-items-center",
            ),
            dbc.Collapse(
                dbc.CardBody(chart_info, className="p-3"),
                id=collapse_id,
                is_open=False,
            ),
        ],
        className="my-2 shadow-sm",
    )
