"""
Dashboard Enhanced - Capacity Gap Analysis Card

Provides the capacity gap card comparing required vs actual velocity.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import html


def _create_capacity_card(
    required_velocity: float,
    actual_velocity: float,
    remaining_items: float,
    days_to_deadline: float,
    show_data: bool = True,
) -> dbc.Card:
    """Create capacity gap analysis card."""
    if not show_data:
        return dbc.Card(
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.I(
                                className="fas fa-gauge-high me-2",
                                style={"color": "#6610f2", "fontSize": "1.1rem"},
                            ),
                            html.Span(
                                "Capacity Analysis",
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
            style={"border": "none", "borderRadius": "12px"},
        )

    capacity_gap = actual_velocity - required_velocity
    gap_percent = (
        (capacity_gap / required_velocity * 100) if required_velocity > 0 else 0
    )

    # Status
    if gap_percent >= -5:
        gap_color = "#28a745"
        gap_emoji = "[OK]"
        gap_label = "ADEQUATE"
    elif gap_percent >= -20:
        gap_color = "#ffc107"
        gap_emoji = "[!]"
        gap_label = "STRETCHED"
    else:
        gap_color = "#dc3545"
        gap_emoji = "[X]"
        gap_label = "SHORTFALL"

    # Calculate options
    weeks_to_deadline = days_to_deadline / 7
    scope_reduction = abs(capacity_gap * weeks_to_deadline) if gap_percent < 0 else 0
    velocity_increase = abs(gap_percent) if gap_percent < 0 else 0

    return dbc.Card(
        dbc.CardBody(
            [
                # Header
                html.Div(
                    [
                        html.I(
                            className="fas fa-gauge-high me-2",
                            style={"color": "#6610f2", "fontSize": "1rem"},
                        ),
                        html.Span(
                            "Capacity Analysis",
                            className="fw-semibold",
                            style={"fontSize": "1rem"},
                        ),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                # Status
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    gap_emoji,
                                    style={"fontSize": "1.2rem"},
                                    className="me-1",
                                ),
                                html.Span(
                                    gap_label,
                                    style={
                                        "color": gap_color,
                                        "fontWeight": "bold",
                                        "fontSize": "1rem",
                                    },
                                ),
                            ],
                            className="mb-1",
                        ),
                        html.Div(
                            f"{gap_percent:+.0f}% capacity gap",
                            className="text-muted",
                            style={"fontSize": "0.875rem", "fontWeight": "500"},
                        ),
                    ],
                    className="mb-1",
                ),
                # Metrics
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span(
                                    "Required: ",
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{required_velocity:.1f}/wk",
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Current: ",
                                    className="text-muted",
                                    style={"fontSize": "0.875rem"},
                                ),
                                html.Span(
                                    f"{actual_velocity:.1f}/wk",
                                    className="fw-semibold",
                                    style={"fontSize": "0.95rem"},
                                ),
                            ],
                            className="d-flex justify-content-between",
                        ),
                    ],
                    className="mb-1 pb-2 border-bottom",
                ),
                # Action
                html.Div(
                    (
                        html.Div(
                            (
                                f"Need +{velocity_increase:.0f}% velocity "
                                f"or {scope_reduction:.0f} fewer items"
                            ),
                            className="text-center",
                            style={
                                "fontSize": "0.875rem",
                                "color": gap_color,
                                "fontWeight": "500",
                            },
                        )
                        if gap_percent < -5
                        else html.Div(
                            "[OK] On track to meet deadline",
                            className="text-center",
                            style={
                                "fontSize": "0.95rem",
                                "color": "#28a745",
                                "fontWeight": "500",
                            },
                        )
                    ),
                ),
            ],
            className="p-2",
        ),
        className="h-100 shadow-sm",
        style={"border": "none", "borderRadius": "12px", "minHeight": "240px"},
    )
