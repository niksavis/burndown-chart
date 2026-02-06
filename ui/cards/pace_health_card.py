"""Pace Health Card - Required Velocity to Meet Deadline.

This module provides the "Required Pace to Deadline" card that shows:
- Required velocity to meet project deadline
- Current velocity from recent data (filtered by Data Points slider)
- Velocity gap (how much team needs to improve)
- Health status with visual indicators (✓/○/❄)
- Actionable recommendations

Automatically handles scope changes by using current remaining work.
"""

from __future__ import annotations

import logging
from typing import Optional

import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import COLOR_PALETTE
from ui.styles import create_metric_card_header

logger = logging.getLogger(__name__)


def create_pace_health_card(
    required_items: float,
    current_items: float,
    required_points: Optional[float],
    current_points: Optional[float],
    deadline_days: int,
    show_points: bool = True,
) -> dbc.Card:
    """Create Required Pace to Deadline card.

    Args:
        required_items: Required items per week to meet deadline
        current_items: Current items per week from filtered data
        required_points: Required points per week (None if points disabled)
        current_points: Current points per week (None if points disabled)
        deadline_days: Days remaining to deadline
        show_points: Whether to show points section

    Returns:
        Dash Card component with pace health metrics

    Example:
        >>> card = create_pace_health_card(
        ...     required_items=12.5,
        ...     current_items=10.0,
        ...     required_points=48.0,
        ...     current_points=45.5,
        ...     deadline_days=28,
        ...     show_points=True
        ... )
    """
    from data.velocity_projections import assess_pace_health

    # Calculate items-based metrics
    items_health = assess_pace_health(current_items, required_items)

    # Calculate points-based metrics (if enabled and data available)
    points_health = None
    if show_points and required_points and current_points:
        points_health = assess_pace_health(current_points, required_points)

    # Determine overall health (worst of items/points)
    if points_health:
        overall_health = (
            items_health
            if items_health["ratio"] < points_health["ratio"]
            else points_health
        )
    else:
        overall_health = items_health

    logger.info(
        f"Pace health card: Items {items_health['status']} ({items_health['ratio']:.2%}), "
        f"Overall: {overall_health['status']}"
    )

    return dbc.Card(
        [
            # Card Header
            create_metric_card_header(
                title="Required Pace",
                tooltip_text=(
                    "Shows your current velocity vs. required velocity to meet the deadline. "
                    "Progress bars indicate velocity achievement percentage (current / required). "
                    "Green: on track | Yellow: at risk | Red: behind schedule."
                ),
                tooltip_id="pace-health-card",
            ),
            # Card Body
            dbc.CardBody(
                [
                    # Items-based section
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
                                    # Numeric display with badge
                                    html.Div(
                                        [
                                            html.Span(
                                                f"{current_items:.2f} of {required_items:.2f} items/week",
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
                                        className="d-flex justify-content-between align-items-center mb-2",
                                    ),
                                    # Progress bar
                                    html.Div(
                                        html.Div(
                                            f"{(current_items / required_items * 100) if required_items > 0 else 0:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min((current_items / required_items * 100) if required_items > 0 else 0, 100)}%",
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
                    # Points-based section (always show, with placeholder when disabled)
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
                                    # Numeric display with badge
                                    html.Div(
                                        [
                                            html.Span(
                                                f"{current_points or 0:.2f} of {required_points or 0:.2f} points/week",
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
                                        className="d-flex justify-content-between align-items-center mb-2",
                                    ),
                                    # Progress bar
                                    html.Div(
                                        html.Div(
                                            f"{((current_points or 0) / (required_points or 1) * 100):.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(((current_points or 0) / (required_points or 1) * 100), 100)}%",
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
                            # Case 1: Points tracking enabled and data available
                            if show_points
                            and points_health
                            and required_points is not None
                            and required_points > 0
                            # Case 2: Points tracking disabled
                            else (
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-toggle-off fa-2x text-secondary mb-2"
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
                                            "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                                            className="text-muted",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                    ],
                                    className="text-center",
                                )
                                if not show_points
                                # Case 3: Points tracking enabled but no data
                                else html.Div(
                                    [
                                        html.I(
                                            className="fas fa-database fa-2x text-secondary mb-2"
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
                                            "No story points data available. Configure story points field in Settings or complete items with point estimates.",
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
            # Card Footer
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
