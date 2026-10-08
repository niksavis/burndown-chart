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

        days_to_forecast = (forecast_date - current_date).days
        days_to_deadline = (deadline_date - current_date).days

        if days_to_deadline <= 0:
            return {
                "percentage": 100,
                "bar_width": 100,
                "badge_text": "Overdue",
                "color": "#dc3545",
                "status": "overdue",
            }

        percentage = max(0.0, (days_to_forecast / days_to_deadline) * 100)

        if days_to_forecast <= days_to_deadline:
            badge_text = "On Schedule"
            if percentage <= 70:
                color = "#28a745"
            elif percentage <= 90:
                color = "#20c997"
            else:
                color = "#ffc107"
        else:
            badge_text = "Behind Schedule"
            if percentage <= 110:
                color = "#ffc107"
            else:
                color = "#dc3545"

        return {
            "percentage": percentage,
            "bar_width": min(percentage, 100),
            "badge_text": badge_text,
            "color": color,
            "status": "ahead" if days_to_forecast <= days_to_deadline else "behind",
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

    if not (
        remaining_items is not None
        and avg_weekly_items is not None
        and days_to_deadline is not None
        and days_to_deadline > 0
        and deadline_str is not None
    ):
        return None

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
