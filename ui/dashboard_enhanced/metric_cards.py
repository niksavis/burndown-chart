"""
Dashboard Enhanced - Forecast and Velocity Metric Cards

Provides card builders for items/points forecast and velocity display.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import html

from ui.dashboard_enhanced.components import _create_sparkline_bars


def _create_forecast_card(
    title: str,
    icon: str,
    icon_color: str,
    pert_date: str,
    confidence_intervals: dict,
    status: str,
    probability: float,
    show_data: bool = True,
    card_id: str | None = None,
) -> dbc.Card:
    """Create enhanced forecast card - readable text, minimal whitespace."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"{icon} me-2",
                                style={"color": icon_color, "fontSize": "1.25rem"},
                            ),
                            html.Span(
                                title,
                                className="fw-semibold",
                                style={"fontSize": "1rem"},
                            ),
                        ],
                        className="d-flex align-items-center mb-1",
                    ),
                    html.Div(
                        "Tracking disabled",
                        className="text-center text-muted py-2",
                        style={"fontSize": "0.95rem"},
                    ),
                ],
                className="p-2",
            ),
            className="h-100 shadow-sm",
            id=card_id,
            style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
        )

    ci_50_date = (
        datetime.now() + timedelta(days=confidence_intervals["ci_50"])
    ).strftime("%b %d, %Y")
    ci_95_date = (
        datetime.now() + timedelta(days=confidence_intervals["ci_95"])
    ).strftime("%b %d, %Y")

    status_color = "#28a745" if status == "on_track" else "#dc3545"
    status_icon = (
        "fa-check-circle" if status == "on_track" else "fa-exclamation-triangle"
    )
    status_text = "On Track" if status == "on_track" else "At Risk"

    # Probability color
    if probability >= 70:
        prob_color = "#28a745"
    elif probability >= 40:
        prob_color = "#ffc107"
    else:
        prob_color = "#dc3545"

    card_suffix = card_id or "default"

    return dbc.Card(
        dbc.CardBody(
            [
                # Header - minimal spacing
                html.Div(
                    [
                        html.I(
                            className=f"{icon} me-2",
                            style={"color": icon_color, "fontSize": "1.25rem"},
                        ),
                        html.Span(
                            title,
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Primary forecast
                html.Div(
                    [
                        html.Div(
                            pert_date,
                            className="fw-bold",
                            style={
                                "color": icon_color,
                                "fontSize": "1.75rem",
                                "lineHeight": "1",
                            },
                        ),
                        html.Div(
                            "Expected Completion",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-2",
                ),
                # Confidence intervals
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Confidence Intervals",
                                    className="text-muted",
                                    style={
                                        "fontSize": "0.75rem",
                                        "fontWeight": "600",
                                        "textTransform": "uppercase",
                                        "letterSpacing": "0.5px",
                                    },
                                ),
                                html.I(
                                    className="fas fa-info-circle ms-1 text-info",
                                    id=f"ci-section-info-{card_suffix}",
                                    style={
                                        "fontSize": "0.7rem",
                                        "cursor": "help",
                                    },
                                ),
                                dbc.Tooltip(
                                    "Statistical probability ranges for "
                                    "completion dates. Based on velocity "
                                    "variance using normal distribution "
                                    "(50th and 95th percentiles).",
                                    target=f"ci-section-info-{card_suffix}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        "50%: ",
                                        html.I(
                                            className=(
                                                "fas fa-info-circle ms-1 text-info"
                                            ),
                                            id=f"ci-50-info-{card_suffix}",
                                            style={
                                                "fontSize": "0.75rem",
                                                "cursor": "help",
                                            },
                                        ),
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                dbc.Tooltip(
                                    "50th percentile (median): 50% "
                                    "probability of completion by this date. "
                                    "This is the PERT forecast.",
                                    target=f"ci-50-info-{card_suffix}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                                html.Span(
                                    ci_50_date,
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    [
                                        "95%: ",
                                        html.I(
                                            className=(
                                                "fas fa-info-circle ms-1 text-info"
                                            ),
                                            id=f"ci-95-info-{card_suffix}",
                                            style={
                                                "fontSize": "0.75rem",
                                                "cursor": "help",
                                            },
                                        ),
                                    ],
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                dbc.Tooltip(
                                    "95th percentile (high confidence): 95% "
                                    "probability of completion by this date. "
                                    "Safe estimate with 1.65sigma buffer.",
                                    target=f"ci-95-info-{card_suffix}",
                                    placement="top",
                                    trigger="click",
                                    autohide=True,
                                ),
                                html.Span(
                                    ci_95_date,
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between",
                        ),
                    ],
                    className="mb-2 pb-2 border-bottom",
                ),
                # Status
                html.Div(
                    [
                        html.Div(
                            [
                                html.I(
                                    className=f"fas {status_icon} me-1",
                                    style={"color": status_color, "fontSize": "1rem"},
                                ),
                                html.Span(
                                    status_text,
                                    style={
                                        "color": status_color,
                                        "fontWeight": "600",
                                        "fontSize": "1rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "On-Track: ",
                                    className="text-muted me-1",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{probability:.0f}%",
                                    className="fw-bold",
                                    style={
                                        "color": prob_color,
                                        "fontSize": "1.1rem",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        id=card_id,
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )


def _create_velocity_card(
    title: str,
    icon: str,
    icon_color: str,
    velocity_stats: dict,
    show_data: bool = True,
    card_id: str | None = None,
) -> dbc.Card:
    """Create enhanced velocity card with predictability."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className=f"{icon} me-2",
                                style={"color": icon_color, "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                title,
                                className="fw-semibold",
                                style={"fontSize": "0.9rem"},
                            ),
                        ],
                        className="d-flex align-items-center mb-2",
                    ),
                    html.Div(
                        "Tracking disabled",
                        className="text-center text-muted py-3",
                        style={"fontSize": "0.9rem"},
                    ),
                ]
            ),
            className="h-100 shadow-sm",
            id=card_id,
            style={"border": "none", "borderRadius": "12px"},
        )

    cv = velocity_stats["cv"]

    # Predictability classification
    if cv < 25:
        predict_label = "Predictable"
        predict_color = "#28a745"
        predict_emoji = "[OK]"
    elif cv < 40:
        predict_label = "Moderate"
        predict_color = "#ffc107"
        predict_emoji = "[!]"
    else:
        predict_label = "Unpredictable"
        predict_color = "#dc3545"
        predict_emoji = "[X]"

    # Recent trend
    recent_change = velocity_stats["recent_change"]
    if abs(recent_change) < 5:
        trend_icon = "fa-minus"
        trend_color = "#6c757d"
        trend_text = "Stable"
    elif recent_change > 0:
        trend_icon = "fa-arrow-up"
        trend_color = "#28a745"
        trend_text = f"+{recent_change:.0f}%"
    else:
        trend_icon = "fa-arrow-down"
        trend_color = "#dc3545"
        trend_text = f"{recent_change:.0f}%"

    return dbc.Card(
        dbc.CardBody(
            [
                # Header
                html.Div(
                    [
                        html.I(
                            className=f"{icon} me-2",
                            style={"color": icon_color, "fontSize": "1rem"},
                        ),
                        html.Span(
                            title,
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Primary metric
                html.Div(
                    [
                        html.Div(
                            f"{velocity_stats['mean']:.1f}",
                            className="fw-bold mb-1",
                            style={
                                "color": icon_color,
                                "fontSize": "1.75rem",
                                "lineHeight": "1",
                            },
                        ),
                        html.Div(
                            "per week (avg)",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-1",
                ),
                # Sparkline
                html.Div(
                    [
                        _create_sparkline_bars(
                            velocity_stats["sparkline_data"],
                            color=icon_color,
                            height=30,
                        ),
                        html.Div(
                            "Last 10 weeks",
                            className="text-muted text-center mt-1",
                            style={"fontSize": "0.75rem"},
                        ),
                    ],
                    className="mb-1 pb-2 border-bottom",
                ),
                # Predictability
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    predict_emoji,
                                    style={"fontSize": "1rem"},
                                    className="me-1",
                                ),
                                html.Span(
                                    predict_label,
                                    style={
                                        "color": predict_color,
                                        "fontWeight": "600",
                                        "fontSize": "0.95rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Trend: ",
                                    className="text-muted me-1",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    [
                                        html.I(
                                            className=f"fas {trend_icon} me-1",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                        trend_text,
                                    ],
                                    style={
                                        "color": trend_color,
                                        "fontWeight": "600",
                                        "fontSize": "0.95rem",
                                    },
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        id=card_id,
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )
