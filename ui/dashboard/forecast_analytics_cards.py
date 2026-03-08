"""Forecast Analytics - Summary Card Builders.

Contains builders for expected completion and confidence interval cards.
"""

from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import COLOR_PALETTE
from ui.styles import create_metric_card_header


def _build_expected_completion_card(
    items_pert_date: str,
    points_pert_date: str,
    items_schedule_status: dict,
    points_schedule_status: dict,
    show_points: bool,
    points_disabled_text: str,
    no_points_data_text: str,
    expected_completion_tooltip: str,
    row_between_class: str,
) -> dbc.Card:
    """Build the Expected Completion metric card."""
    points_track_body: Any
    if show_points and points_pert_date != "No data":
        points_track_body = html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            points_pert_date,
                            className="text-muted",
                            style={"fontSize": "0.85rem", "fontWeight": "600"},
                        ),
                        html.Span(
                            points_schedule_status["badge_text"],
                            className="badge ms-2",
                            style={
                                "backgroundColor": points_schedule_status["color"],
                                "fontSize": "0.75rem",
                            },
                        ),
                    ],
                    className=row_between_class,
                ),
                html.Div(
                    html.Div(
                        f"{points_schedule_status['percentage']:.1f}%",
                        className="progress-bar",
                        style={
                            "width": f"{points_schedule_status['bar_width']}%",
                            "backgroundColor": points_schedule_status["color"],
                        },
                        role="progressbar",
                    ),
                    className="progress",
                    style={"height": "20px"},
                ),
            ]
        )
    elif not show_points:
        points_track_body = html.Div(
            [
                html.I(className="fas fa-toggle-off fa-2x text-secondary mb-2"),
                html.Div(
                    "Points Tracking Disabled",
                    className="h5 mb-2",
                    style={"fontWeight": "600", "color": "#6c757d"},
                ),
                html.Small(
                    points_disabled_text,
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
            ],
            className="text-center",
        )
    else:
        points_track_body = html.Div(
            [
                html.I(className="fas fa-database fa-2x text-secondary mb-2"),
                html.Div(
                    "No Points Data",
                    className="h5 mb-2",
                    style={"fontWeight": "600", "color": "#6c757d"},
                ),
                html.Small(
                    no_points_data_text,
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
            ],
            className="text-center",
        )

    return dbc.Card(
        [
            create_metric_card_header(
                title="Expected Completion",
                tooltip_text=expected_completion_tooltip,
                tooltip_id="metric-expected_completion",
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-tasks me-1",
                                        style={
                                            "color": COLOR_PALETTE["items"],
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "Items-based",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                items_pert_date,
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                items_schedule_status["badge_text"],
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": (
                                                        items_schedule_status["color"]
                                                    ),
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=row_between_class,
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{items_schedule_status['percentage']:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": (
                                                    f"{items_schedule_status['bar_width']}%"
                                                ),
                                                "backgroundColor": (
                                                    items_schedule_status["color"]
                                                ),
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            ),
                        ],
                        className="pb-3 mb-3",
                        style={"borderBottom": "1px solid #e9ecef"}
                        if show_points
                        else {"marginBottom": "0"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-1",
                                        style={
                                            "color": (
                                                COLOR_PALETTE["points"]
                                                if show_points
                                                and points_pert_date != "No data"
                                                else "#6c757d"
                                            ),
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "Points-based",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            points_track_body,
                        ],
                    ),
                ]
            ),
            dbc.CardFooter(
                html.Small(
                    "PERT forecast based on items and story points velocity"
                    if show_points
                    else "PERT forecast based on items velocity",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )


def _build_confidence_intervals_card(
    optimistic_date: str,
    pessimistic_date: str,
    ci_50_status: dict,
    ci_95_status: dict,
    confidence_intervals_tooltip: str,
    row_between_class: str,
) -> dbc.Card:
    """Build the Confidence Intervals metric card."""
    return dbc.Card(
        [
            create_metric_card_header(
                title="Confidence Intervals",
                tooltip_text=confidence_intervals_tooltip,
                tooltip_id="metric-confidence_intervals",
            ),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-thumbs-up me-1",
                                        style={
                                            "color": "#28a745",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "50% Confidence",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                optimistic_date,
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                ci_50_status["badge_text"],
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": ci_50_status[
                                                        "color"
                                                    ],
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=row_between_class,
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{ci_50_status['percentage']:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": (
                                                    f"{ci_50_status['bar_width']}%"
                                                ),
                                                "backgroundColor": ci_50_status[
                                                    "color"
                                                ],
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            ),
                        ],
                        className="pb-3 mb-3",
                        style={"borderBottom": "1px solid #e9ecef"},
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-shield-alt me-1",
                                        style={
                                            "color": "#dc3545",
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "95% Confidence",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                pessimistic_date,
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                ci_95_status["badge_text"],
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": ci_95_status[
                                                        "color"
                                                    ],
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=row_between_class,
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{ci_95_status['percentage']:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": (
                                                    f"{ci_95_status['bar_width']}%"
                                                ),
                                                "backgroundColor": ci_95_status[
                                                    "color"
                                                ],
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            dbc.CardFooter(
                html.Small(
                    "Statistical delivery probability ranges",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )
