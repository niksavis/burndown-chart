from __future__ import annotations

import logging

import dash_bootstrap_components as dbc
from dash import html

from data.velocity_projections import assess_pace_health
from ui.style_constants import COLOR_PALETTE
from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def create_pace_health_card(
    required_items: float,
    current_items: float,
    required_points: float | None,
    current_points: float | None,
    deadline_days: int,
    show_points: bool = True,
) -> dbc.Card:

    items_health = assess_pace_health(current_items, required_items)

    points_health = None
    if show_points and required_points and current_points:
        points_health = assess_pace_health(current_points, required_points)

    if points_health:
        overall_health = (
            items_health
            if items_health["ratio"] < points_health["ratio"]
            else points_health
        )
    else:
        overall_health = items_health

    items_percent = (current_items / required_items * 100) if required_items > 0 else 0
    items_display_text = f"{current_items:.2f} of {required_items:.2f} items/week"

    points_ratio = (current_points or 0) / (required_points or 1) * 100
    points_display_text = (
        f"{current_points or 0:.2f} of {required_points or 0:.2f} points/week"
    )

    logger.info(
        "Pace health card: "
        f"Items {items_health['status']} ({items_health['ratio']:.2%}), "
        f"Overall: {overall_health['status']}"
    )

    return dbc.Card(
        [
            create_metric_card_header(
                title="Required Pace",
                tooltip_text=(
                    "Shows your current velocity vs. required velocity "
                    "to meet the deadline. "
                    "Progress bars indicate velocity achievement "
                    "percentage (current / required). "
                    "Green: on track | Yellow: at risk | Red: behind schedule."
                ),
                tooltip_id="pace-health-card",
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
                                                items_display_text,
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                items_health["status"]
                                                .replace("_", " ")
                                                .title(),
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": items_health[
                                                        "color"
                                                    ],
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=(
                                            "d-flex justify-content-between "
                                            "align-items-center mb-2"
                                        ),
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{items_percent:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(items_percent, 100)}%",
                                                "backgroundColor": items_health[
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
                                            "color": COLOR_PALETTE["points"]
                                            if show_points
                                            else "#6c757d",
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
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                points_display_text,
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                points_health["status"]
                                                .replace("_", " ")
                                                .title(),
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": points_health[
                                                        "color"
                                                    ],
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=(
                                            "d-flex justify-content-between "
                                            "align-items-center mb-2"
                                        ),
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{points_ratio:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(points_ratio, 100)}%",
                                                "backgroundColor": points_health[
                                                    "color"
                                                ],
                                            },
                                            role="progressbar",
                                        ),
                                        className="progress",
                                        style={"height": "20px"},
                                    ),
                                ],
                            )
                            if show_points
                            and points_health
                            and required_points is not None
                            and required_points > 0
                            else (
                                html.Div(
                                    [
                                        html.I(
                                            className=(
                                                "fas fa-toggle-off fa-2x "
                                                "text-secondary mb-2"
                                            )
                                        ),
                                        html.Div(
                                            "Points Tracking Disabled",
                                            className="h5 mb-2",
                                            style={
                                                "fontWeight": "600",
                                                "color": "#6c757d",
                                            },
                                        ),
                                        html.Small(
                                            "Points tracking is disabled. "
                                            "Enable Points Tracking in Parameters "
                                            "panel to view story points metrics.",
                                            className="text-muted",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                    ],
                                    className="text-center",
                                )
                                if not show_points
                                else html.Div(
                                    [
                                        html.I(
                                            className=(
                                                "fas fa-database fa-2x "
                                                "text-secondary mb-2"
                                            )
                                        ),
                                        html.Div(
                                            "No Points Data",
                                            className="h5 mb-2",
                                            style={
                                                "fontWeight": "600",
                                                "color": "#6c757d",
                                            },
                                        ),
                                        html.Small(
                                            "No story points data available. "
                                            "Configure story points field in Settings "
                                            "or complete items with point estimates.",
                                            className="text-muted",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                    ],
                                    className="text-center",
                                )
                            ),
                        ],
                    ),
                ]
            ),
            dbc.CardFooter(
                html.Small(
                    f"{deadline_days} days remaining to deadline",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )
