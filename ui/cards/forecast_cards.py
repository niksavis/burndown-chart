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

    current_date = datetime.now().strftime("%Y%m%d")
    default_filename = f"burndown_forecast_{current_date}"

    header_content = create_card_header_with_tooltip(
        "Forecast Graph",
        tooltip_id="forecast-graph",
        tooltip_text=CHART_HELP_TEXTS["forecast_explanation"],
        help_key="forecast_graph_overview",
        help_category="forecast",
    )

    body_content = dcc.Graph(
        id="forecast-graph",
        style={"height": "700px"},
        config={
            "toImageButtonOptions": {
                "filename": default_filename,
            },
        },
    )

    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        body_className="p-2",
        shadow="sm",
    )


def create_forecast_info_card() -> dbc.Card:

    collapse_id = "forecast-info-collapse"

    body_content = html.Div(
        [
            create_rhythm_text(
                [
                    html.Strong("PERT Forecast: "),
                    "Estimates based on optimistic, most likely, and "
                    "pessimistic scenarios from your historical data.",
                    create_expandable_tooltip(
                        id_suffix="pert-methodology-main",
                        summary_text=(
                            "PERT uses 3-point estimation for realistic forecasts"
                        ),
                        detailed_text=CHART_HELP_TEXTS["pert_forecast_methodology"],
                        variant="primary",
                        placement="right",
                    ),
                ],
                element_type="paragraph",
            ),
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
                                                    style={
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
                                                    "Visual legend and "
                                                    "line type meanings",
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
                                                    "Understanding forecast "
                                                    "uncertainty ranges",
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
                                                    "How scope changes are "
                                                    "shown on the main chart",
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
                                                    "How number of data points "
                                                    "affects forecast precision",
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
                            className="col-10 col-lg-11",
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
                                className=(
                                    "d-flex justify-content-end align-items-center"
                                ),
                            ),
                            className="col-2 col-lg-1",
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
        className="my-2 shadow-sm",
    )


def create_items_forecast_info_card(
    statistics_df: pd.DataFrame | None = None, pert_data: dict | None = None
) -> dbc.Card:

    if statistics_df is not None and not statistics_df.empty:
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(recent_df["date"])
        recent_df["week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
        recent_df["year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

        recent_df = recent_df.tail(10)

    collapse_id = "items-forecast-info-collapse"

    chart_info = html.Div(
        className="row g-3",
        children=[
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
                            className="col-10 col-lg-11",
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
                                        "Understanding the weekly items "
                                        "forecast chart and trends.",
                                    ),
                                ],
                                className=(
                                    "d-flex justify-content-end align-items-center"
                                ),
                            ),
                            className="col-2 col-lg-1",
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


def create_points_forecast_info_card(
    statistics_df: pd.DataFrame | None = None, pert_data: dict | None = None
) -> dbc.Card:

    if statistics_df is not None and not statistics_df.empty:
        recent_df = statistics_df.copy()
        recent_df["date"] = pd.to_datetime(
            recent_df["date"], format="mixed", errors="coerce"
        )
        recent_df["week"] = recent_df["date"].dt.isocalendar().week  # type: ignore[attr-defined]
        recent_df["year"] = recent_df["date"].dt.isocalendar().year  # type: ignore[attr-defined]

        recent_df = recent_df.tail(10)

    collapse_id = "points-forecast-info-collapse"

    chart_info = html.Div(
        className="row g-3",
        children=[
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
                                        ": Next week's forecast "
                                        "with confidence interval",
                                    ]
                                ),
                            ],
                            className="mb-0 ps-3",
                            style={"fontSize": "0.85rem"},
                        ),
                    ],
                ),
            ),
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
                            className="col-10 col-lg-11",
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
                                        "Understanding the weekly points "
                                        "forecast chart and trends.",
                                    ),
                                ],
                                className=(
                                    "d-flex justify-content-end align-items-center"
                                ),
                            ),
                            className="col-2 col-lg-1",
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
