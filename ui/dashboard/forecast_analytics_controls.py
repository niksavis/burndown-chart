"""Forecast Analytics - Status and Probability Calculation Helpers.

Provides reusable helper functions for schedule status calculation,
probability tier mapping, on-track probability card, and pace health
element builders used by the forecast analytics summary module.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from data.velocity_projections import calculate_required_velocity
from ui.cards.pace_health_card import create_pace_health_card
from ui.style_constants import COLOR_PALETTE
from ui.styles import create_metric_card_header


def calculate_schedule_status(
    forecast_date_str: str, deadline_date_str: str | None, current_date: datetime
) -> dict:
    """Calculate schedule status for progress bar visualization.

    Args:
        forecast_date_str: Forecast date in YYYY-MM-DD format
        deadline_date_str: Deadline in YYYY-MM-DD format
            (None if no deadline is set)
        current_date: Current date/time

    Returns:
        dict with percentage, bar_width, badge_text, color, and status
    """
    if forecast_date_str == "No data" or not deadline_date_str:
        return {
            "percentage": 0,
            "bar_width": 0,
            "badge_text": "Unknown",
            "color": "#6c757d",
            "status": "unknown",
        }

    try:
        forecast_date = datetime.strptime(forecast_date_str, "%Y-%m-%d")
        deadline_date = datetime.strptime(deadline_date_str, "%Y-%m-%d")

        # Calculate days
        days_to_forecast = (forecast_date - current_date).days
        days_to_deadline = (deadline_date - current_date).days

        # Avoid division by zero
        if days_to_deadline <= 0:
            return {
                "percentage": 100,
                "bar_width": 100,
                "badge_text": "Overdue",
                "color": "#dc3545",
                "status": "overdue",
            }

        # Calculate percentage of deadline timeline used by forecast.
        percentage = (days_to_forecast / days_to_deadline) * 100

        # Determine status
        if days_to_forecast < days_to_deadline:
            # Ahead of schedule
            badge_text = "On Schedule"
            if percentage <= 70:
                color = "#28a745"  # Green - significantly ahead
            elif percentage <= 90:
                color = "#20c997"  # Teal - slightly ahead
            else:
                color = "#ffc107"  # Yellow - barely ahead
        else:
            # Behind schedule or on deadline
            badge_text = "Behind Schedule"
            if percentage <= 110:
                color = "#ffc107"  # Yellow - slightly behind
            else:
                color = "#dc3545"  # Red - significantly behind

        return {
            "percentage": percentage,  # Actual percentage (can exceed 100%)
            "bar_width": min(percentage, 100),  # Bar width capped at 100% for CSS
            "badge_text": badge_text,
            "color": color,
            "status": "ahead" if days_to_forecast < days_to_deadline else "behind",
        }
    except Exception:
        return {
            "percentage": 0,
            "bar_width": 0,
            "badge_text": "Unknown",
            "color": "#6c757d",
            "status": "unknown",
        }


def _get_probability_tier(prob: float) -> tuple[str, str]:
    """Return (tier_name, hex_color) for a probability value.

    Args:
        prob: Probability value (0-100)

    Returns:
        Tuple of (tier_name, hex_color)
    """
    if prob >= 70:
        return "Healthy", "#28a745"
    if prob >= 40:
        return "Warning", "#ffc107"
    return "At Risk", "#dc3545"


def _build_on_track_card(
    deadline_prob_items: float,
    deadline_prob_points: float | None,
    items_prob_tier: str,
    items_prob_color: str,
    prob_tier: str,
    prob_color: str,
    show_points: bool,
    points_disabled_text: str,
    no_points_data_text: str,
    on_track_tooltip: str,
    row_between_class: str,
) -> dbc.Card:
    """Build the On-Track Probability metric card.

    Args:
        deadline_prob_items: Items-based deadline probability (0-100)
        deadline_prob_points: Points-based deadline probability or None
        items_prob_tier: Tier label for items probability
        items_prob_color: Hex color for items probability
        prob_tier: Tier label for primary (points or items) probability
        prob_color: Hex color for primary probability
        show_points: Whether points tracking is enabled
        points_disabled_text: Placeholder text when points disabled
        no_points_data_text: Placeholder text when no points data
        on_track_tooltip: Tooltip text for the card header
        row_between_class: Shared CSS class for row layout

    Returns:
        dbc.Card component
    """
    points_track_content: Any
    if show_points and deadline_prob_points is not None and deadline_prob_points > 0:
        points_track_content = html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            f"{deadline_prob_points:.0f}%",
                            className="text-muted",
                            style={"fontSize": "0.85rem", "fontWeight": "600"},
                        ),
                        html.Span(
                            prob_tier,
                            className="badge ms-2",
                            style={
                                "backgroundColor": prob_color,
                                "fontSize": "0.75rem",
                            },
                        ),
                    ],
                    className=row_between_class,
                ),
                html.Div(
                    html.Div(
                        f"{deadline_prob_points:.1f}%",
                        className="progress-bar",
                        style={
                            "width": f"{min(deadline_prob_points, 100)}%",
                            "backgroundColor": prob_color,
                        },
                        role="progressbar",
                    ),
                    className="progress",
                    style={"height": "20px"},
                ),
            ],
        )
    elif not show_points:
        points_track_content = html.Div(
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
        points_track_content = html.Div(
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
                title="On-Track Probability",
                tooltip_text=on_track_tooltip,
                tooltip_id="metric-on_track_probability",
            ),
            dbc.CardBody(
                [
                    # Items-based probability
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
                                                f"{deadline_prob_items:.0f}%",
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
                                            ),
                                            html.Span(
                                                items_prob_tier,
                                                className="badge ms-2",
                                                style={
                                                    "backgroundColor": items_prob_color,
                                                    "fontSize": "0.75rem",
                                                },
                                            ),
                                        ],
                                        className=row_between_class,
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{deadline_prob_items:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": (
                                                    f"{min(deadline_prob_items, 100)}%"
                                                ),
                                                "backgroundColor": items_prob_color,
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
                    # Points-based probability with placeholder when disabled.
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
                            points_track_content,
                        ],
                    ),
                ]
            ),
            dbc.CardFooter(
                html.Small(
                    "Deadline achievement likelihood based on items and story points"
                    if show_points
                    else "Deadline achievement likelihood based on items",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )


def _build_pace_health_element(
    remaining_items: float | None,
    remaining_points: float | None,
    avg_weekly_items: float | None,
    avg_weekly_points: float | None,
    days_to_deadline: int | None,
    deadline_str: str | None,
    show_points: bool,
    current_date: datetime,
) -> dbc.Card | None:
    """Build the Required Pace to Deadline card element if data is available.

    Args:
        remaining_items: Current remaining items
        remaining_points: Current remaining points
        avg_weekly_items: Current velocity in items/week
        avg_weekly_points: Current velocity in points/week
        days_to_deadline: Days remaining to deadline
        deadline_str: Deadline in YYYY-MM-DD format
        show_points: Whether points tracking is enabled
        current_date: Current date for velocity calculation

    Returns:
        pace_health card html element, or None if insufficient data
    """
    if not (
        remaining_items is not None
        and avg_weekly_items is not None
        and days_to_deadline is not None
        and days_to_deadline > 0
        and deadline_str is not None
    ):
        return None

    # Calculate required velocities using the actual deadline date.
    # This ensures exact match with burndown charts calculation.
    # Use date() to ensure value does not change during the same day (consistency).
    deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
    required_items = calculate_required_velocity(
        remaining_items, deadline_date, current_date=current_date, time_unit="week"
    )

    required_points = None
    if show_points and remaining_points is not None and avg_weekly_points is not None:
        required_points = calculate_required_velocity(
            remaining_points,
            deadline_date,
            current_date=current_date,
            time_unit="week",
        )

    return create_pace_health_card(
        required_items=required_items,
        current_items=avg_weekly_items,
        required_points=required_points,
        current_points=avg_weekly_points if show_points else None,
        deadline_days=days_to_deadline,
        show_points=show_points,
    )
