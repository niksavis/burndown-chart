import math
from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from configuration import COLOR_PALETTE
from ui.styles import create_metric_card_header


def _create_card_footer(text: str, icon: str = "fa-info-circle") -> dbc.CardFooter:

    return dbc.CardFooter(
        html.Div(
            [
                html.I(className=f"fas {icon} me-1"),
                text,
            ],
            className="text-center text-muted py-2 px-3",
            style={"fontSize": "0.85rem", "lineHeight": "1.4"},
        ),
        className="bg-light border-top",
    )


def create_forecast_alignment_card(
    pert_time_items: float,
    pert_time_points: float | None,
    runway_weeks: float,
    show_points: bool = True,
    last_date: datetime | None = None,
    card_id: str | None = None,
) -> dbc.Card:

    reference_date = last_date if last_date else datetime.now()

    pert_weeks_items = pert_time_items / 7.0
    pert_weeks_points = pert_time_points / 7.0 if pert_time_points else pert_weeks_items

    items_completion_date = reference_date + timedelta(days=pert_time_items)
    points_completion_date = (
        reference_date + timedelta(days=pert_time_points)
        if pert_time_points
        else items_completion_date
    )

    runway_end_date = reference_date + timedelta(weeks=runway_weeks)

    if math.isinf(runway_weeks):
        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.Span(
                            "Forecast vs Budget Alignment",
                            className="metric-card-title",
                        ),
                        " ",
                        html.I(
                            className="fas fa-info-circle text-info",
                            title="Waiting for budget consumption data",
                        ),
                    ],
                ),
                dbc.CardBody(
                    [
                        dbc.Alert(
                            [
                                html.I(className="fas fa-hourglass-start me-2"),
                                html.Strong("No Budget Consumption Data"),
                                html.P(
                                    "Budget tracking will begin once work "
                                    "completion is recorded. "
                                    "The burn rate is calculated from ACTUAL completed "
                                    "work, not just team cost. "
                                    "Complete some items to start tracking budget "
                                    "consumption.",
                                    className="mb-0 mt-2 small",
                                ),
                            ],
                            color="info",
                            className="mb-0",
                        )
                    ]
                ),
            ],
            id=card_id,
            className="metric-card metric-card-large mb-3",
        )

    gap_items = runway_weeks - pert_weeks_items
    gap_points = runway_weeks - pert_weeks_points

    min_gap = min(gap_items, gap_points) if show_points else gap_items
    if min_gap >= 0:
        overall_health = "Healthy"
        health_color = "#198754"
        health_icon = "fa-check-circle"
    elif min_gap >= -2:
        overall_health = "Warning"
        health_color = "#ffc107"
        health_icon = "fa-exclamation-triangle"
    else:
        overall_health = "At Risk"
        health_color = "#dc3545"
        health_icon = "fa-times-circle"

    def format_gap(gap: float) -> tuple[str, str, str]:
        if gap >= 0:
            return f"+{gap:.1f} weeks", "#198754", "fa-arrow-up"
        elif gap >= -2:
            return f"{gap:.1f} weeks", "#ffc107", "fa-minus-circle"
        else:
            return f"{gap:.1f} weeks", "#dc3545", "fa-arrow-down"

    gap_items_text, gap_items_color, gap_items_icon = format_gap(gap_items)
    gap_points_text, gap_points_color, gap_points_icon = format_gap(gap_points)

    content_items = []

    content_items.append(
        html.Div(
            [
                html.Div(
                    [
                        html.I(
                            className="fas fa-tasks me-2",
                            style={
                                "color": COLOR_PALETTE["items"],
                                "fontSize": "1.1rem",
                            },
                        ),
                        html.Span(
                            "Items-based",
                            className="fw-bold",
                            style={"fontSize": "1.1rem"},
                        ),
                    ],
                    className="mb-3",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    "Expected Completion",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    f"{pert_weeks_items:.1f} weeks",
                                    className="fw-bold",
                                    style={"fontSize": "1.3rem"},
                                ),
                                html.Div(
                                    items_completion_date.strftime("%Y-%m-%d"),
                                    className="text-muted",
                                    style={"fontSize": "0.85rem"},
                                ),
                            ],
                            className="text-center",
                            style={"flex": "1"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    "Budget Runway",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    f"{runway_weeks:.1f} weeks",
                                    className="fw-bold",
                                    style={"fontSize": "1.3rem"},
                                ),
                                html.Div(
                                    runway_end_date.strftime("%Y-%m-%d"),
                                    className="text-muted",
                                    style={"fontSize": "0.85rem"},
                                ),
                            ],
                            className="text-center",
                            style={
                                "flex": "1",
                                "borderLeft": "1px solid #dee2e6",
                                "borderRight": "1px solid #dee2e6",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    "Gap",
                                    className="text-muted mb-2",
                                    style={"fontSize": "0.85rem", "fontWeight": "600"},
                                ),
                                html.Div(
                                    [
                                        html.I(className=f"fas {gap_items_icon} me-2"),
                                        html.Span(
                                            gap_items_text,
                                            style={"fontWeight": "bold"},
                                        ),
                                    ],
                                    style={
                                        "fontSize": "1.1rem",
                                        "color": gap_items_color,
                                    },
                                ),
                            ],
                            className="text-center",
                            style={"flex": "1"},
                        ),
                    ],
                    className="d-flex align-items-center",
                    style={"gap": "1rem"},
                ),
            ],
            className="p-3",
            style={
                "borderRadius": "0.375rem",
                "border": "1px solid #dee2e6",
                "backgroundColor": "#f8f9fa",
            },
        )
    )

    if not show_points:
        content_items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-toggle-off me-2",
                                style={"color": "#6c757d", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold text-muted",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.I(className="fas fa-toggle-off fa-lg text-secondary"),
                            html.Div(
                                "Points Tracking Disabled",
                                className="fw-bold",
                                style={"fontSize": "1rem", "color": "#6c757d"},
                            ),
                            html.Small(
                                (
                                    "Enable Points Tracking in Parameters panel to "
                                    "view story points metrics."
                                ),
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className=(
                            "d-flex align-items-center "
                            "justify-content-center flex-column"
                        ),
                        style={"gap": "0.25rem"},
                    ),
                ],
                className="metric-large-panel mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )
    elif pert_time_points is None or pert_time_points == 0:
        content_items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-chart-bar me-2",
                                style={"color": "#6c757d", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold text-muted",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.I(className="fas fa-database fa-lg text-secondary"),
                            html.Div(
                                "No Points Data",
                                className="fw-bold",
                                style={"fontSize": "1rem", "color": "#6c757d"},
                            ),
                            html.Small(
                                (
                                    "No story points data available. Configure story "
                                    "points field in Settings or complete items with "
                                    "point estimates."
                                ),
                                className="text-muted",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className=(
                            "d-flex align-items-center "
                            "justify-content-center flex-column"
                        ),
                        style={"gap": "0.25rem"},
                    ),
                ],
                className="p-3 mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )
    else:
        content_items.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-chart-bar me-2",
                                style={
                                    "color": COLOR_PALETTE["points"],
                                    "fontSize": "1.1rem",
                                },
                            ),
                            html.Span(
                                "Points-based",
                                className="fw-bold",
                                style={"fontSize": "1.1rem"},
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        "Expected Completion",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        f"{pert_weeks_points:.1f} weeks",
                                        className="fw-bold",
                                        style={"fontSize": "1.3rem"},
                                    ),
                                    html.Div(
                                        points_completion_date.strftime("%Y-%m-%d"),
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="text-center",
                                style={"flex": "1"},
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        "Budget Runway",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        f"{runway_weeks:.1f} weeks",
                                        className="fw-bold",
                                        style={"fontSize": "1.3rem"},
                                    ),
                                    html.Div(
                                        runway_end_date.strftime("%Y-%m-%d"),
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="text-center",
                                style={
                                    "flex": "1",
                                    "borderLeft": "1px solid #dee2e6",
                                    "borderRight": "1px solid #dee2e6",
                                },
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        "Gap",
                                        className="text-muted mb-2",
                                        style={
                                            "fontSize": "0.85rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.I(
                                                className=f"fas {gap_points_icon} me-2"
                                            ),
                                            html.Span(
                                                gap_points_text,
                                                style={"fontWeight": "bold"},
                                            ),
                                        ],
                                        style={
                                            "fontSize": "1.1rem",
                                            "color": gap_points_color,
                                        },
                                    ),
                                ],
                                className="text-center",
                                style={"flex": "1"},
                            ),
                        ],
                        className="d-flex align-items-center",
                        style={"gap": "1rem"},
                    ),
                ],
                className="p-3 mt-3",
                style={
                    "borderRadius": "0.375rem",
                    "border": "1px solid #dee2e6",
                    "backgroundColor": "#f8f9fa",
                },
            )
        )

    card = dbc.Card(
        [
            create_metric_card_header(
                title="Forecast vs Budget Alignment",
                tooltip_text=(
                    "Compares PERT forecast completion time with budget runway. "
                    "Positive gap = budget outlasts forecast (healthy). "
                    "Negative gap = budget exhausts before completion (risk). "
                    "Budget runway is calculated from ACTUAL work completed, "
                    "not just team cost."
                ),
                tooltip_id="metric-forecast_alignment",
                badge=dbc.Badge(
                    overall_health,
                    className="badge",
                    style={
                        "backgroundColor": health_color,
                        "color": "white",
                        "fontSize": "0.85rem",
                        "padding": "0.35rem 0.65rem",
                    },
                ),
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=f"fas {health_icon} me-2",
                                        style={"color": health_color},
                                    ),
                                    html.Span(
                                        overall_health,
                                        style={
                                            "color": health_color,
                                            "fontWeight": "bold",
                                            "fontSize": "1.5rem",
                                        },
                                    ),
                                ],
                                className=(
                                    "d-flex align-items-center "
                                    "justify-content-center mb-1"
                                ),
                            ),
                            html.P(
                                f"Worst gap: {min_gap:+.1f} weeks",
                                className="text-muted mb-3",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="text-center",
                    ),
                    html.Div(content_items),
                ],
                className="pt-3 pb-0 mb-0",
            ),
            _create_card_footer(
                "Positive gap = sufficient budget • Negative gap = budget risk • "
                "Runway from actual burn rate",
                "fa-balance-scale",
            ),
        ],
        id=card_id,
        className="metric-card metric-card-large mb-3 h-100",
    )

    return card
