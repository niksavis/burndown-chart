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
from ui.tooltip_utils import create_info_tooltip

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
    from data.velocity_projections import (
        calculate_velocity_gap,
        assess_pace_health,
    )

    # Calculate items-based metrics
    items_gap_data = calculate_velocity_gap(current_items, required_items)
    items_health = assess_pace_health(current_items, required_items)

    # Calculate points-based metrics (if enabled and data available)
    points_gap_data = None
    points_health = None
    if show_points and required_points and current_points:
        points_gap_data = calculate_velocity_gap(current_points, required_points)
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
            dbc.CardHeader(
                [
                    html.Span(
                        "Required Pace",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text=(
                            "Shows the velocity you need to maintain to complete remaining work by the deadline. "
                            "Automatically adjusts for scope changes. "
                            "Health: ✓ On track | ○ At risk | ❄ Behind schedule."
                        ),
                        id_suffix="pace-health-card",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center justify-content-between",
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
                                className="mb-2",
                            ),
                            html.Div(
                                [
                                    _create_pace_metric(
                                        "Required", f"{required_items:.1f} items/week"
                                    ),
                                    _create_pace_metric(
                                        "Current", f"{current_items:.1f} items/week"
                                    ),
                                    _create_pace_metric(
                                        "Gap",
                                        (
                                            f"{'+' if items_gap_data['gap'] > 0 else ''}"
                                            f"{items_gap_data['gap']:.1f} items/week"
                                        ),
                                        color=items_health["color"],
                                        indicator=items_health["indicator"],
                                    ),
                                ],
                                className="pace-metrics",
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Points-based section (conditional)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-1",
                                        style={
                                            "color": COLOR_PALETTE["points"],
                                            "fontSize": "0.9rem",
                                        },
                                    ),
                                    html.Span(
                                        "Points-based",
                                        className="text-muted",
                                        style={"fontSize": "0.75rem"},
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(
                                [
                                    _create_pace_metric(
                                        "Required", f"{required_points:.1f} pts/week"
                                    ),
                                    _create_pace_metric(
                                        "Current", f"{current_points:.1f} pts/week"
                                    ),
                                    _create_pace_metric(
                                        "Gap",
                                        _format_gap_value(points_gap_data),
                                        color=points_health["color"]
                                        if points_health
                                        else None,
                                        indicator=points_health["indicator"]
                                        if points_health
                                        else None,
                                    ),
                                ],
                                className="pace-metrics",
                            ),
                        ],
                        className="mb-3",
                    )
                    if show_points and points_health
                    else html.Div(),
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


def _create_pace_metric(
    label: str, value: str, color: Optional[str] = None, indicator: Optional[str] = None
) -> html.Div:
    """Helper to create a pace metric row.

    Args:
        label: Metric label (e.g., "Required", "Current", "Gap")
        value: Metric value with units
        color: Optional hex color for value text
        indicator: Optional Unicode indicator (✓/○/❄)

    Returns:
        Div containing formatted metric row
    """
    return html.Div(
        [
            html.Span(
                f"{label}:",
                className="text-muted",
                style={"width": "80px", "display": "inline-block"},
            ),
            html.Span(indicator, className="me-1") if indicator else html.Span(),
            html.Span(
                value,
                style={"fontWeight": "500", "color": color}
                if color
                else {"fontWeight": "500"},
            ),
        ],
        className="mb-1",
    )


def _format_gap_value(gap_data: Optional[dict]) -> str:
    """Format gap value for display.

    Args:
        gap_data: Dictionary with 'gap' key or None

    Returns:
        Formatted gap string
    """
    if gap_data is None:
        return "0.0 pts/week"
    gap = gap_data.get("gap", 0)
    sign = "+" if gap > 0 else ""
    return f"{sign}{gap:.1f} pts/week"


def _create_action_recommendation(
    gap: float, deadline_days: int, status: str
) -> html.Div:
    """Generate actionable recommendation based on pace health.

    Args:
        gap: Velocity gap (positive = need more velocity)
        deadline_days: Days remaining to deadline
        status: Health status ('healthy', 'at_risk', 'behind')

    Returns:
        Div with icon and recommendation message
    """
    if status == "healthy":
        message = "Maintain current pace to meet deadline on time."
        icon = "fa-check-circle"
        color = "#28a745"
    elif status == "at_risk":
        # Calculate approximate improvement needed
        if gap > 0:
            improvement_pct = int((gap / (gap + abs(gap))) * 100)
            message = (
                f"Consider increasing velocity by ~{improvement_pct}% "
                "or negotiating deadline extension."
            )
        else:
            message = "Close to required pace - small improvements will ensure success."
        icon = "fa-exclamation-triangle"
        color = "#ffc107"
    elif status == "deadline_passed":
        message = "Deadline has passed. Update deadline or close completed work."
        icon = "fa-exclamation-circle"
        color = "#dc3545"
    else:  # behind
        # Calculate approximate weeks short
        if gap > 0 and deadline_days > 0:
            weeks_remaining = deadline_days / 7
            weeks_short = (gap * weeks_remaining) / (gap + abs(gap))
            weeks_short = max(1, int(weeks_short))
            message = (
                f"Significant action needed: increase velocity substantially "
                f"or extend deadline by ~{weeks_short} week{'s' if weeks_short > 1 else ''}."
            )
        else:
            message = (
                "Significant action needed: reassess scope, resources, or timeline."
            )
        icon = "fa-exclamation-circle"
        color = "#dc3545"

    return html.Div(
        [
            html.I(className=f"fas {icon} me-2", style={"color": color}),
            html.Small(message, className="text-muted"),
        ],
        className="mt-2",
        style={"fontSize": "0.85rem"},
    )
