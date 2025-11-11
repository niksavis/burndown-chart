"""Dashboard Metric Cards using modern metric_cards.py patterns.

This module provides dashboard-specific metric card creation using the
standardized metric_cards.py component for visual consistency with DORA/Flow metrics.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards import create_metric_card


def create_dashboard_forecast_card(metrics: Dict[str, Any]) -> dbc.Card:
    """Create completion forecast metric card.

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Metric card for completion forecast
    """
    days_to_completion = metrics.get("days_to_completion", 0)
    completion_percentage = metrics.get("completion_percentage", 0.0)
    completion_confidence = metrics.get("completion_confidence", 0)

    # Determine performance tier based on progress vs timeline
    if completion_percentage >= 80:
        tier = "On Track"
        tier_color = "green"
    elif completion_percentage >= 50:
        tier = "In Progress"
        tier_color = "blue"
    elif completion_percentage >= 20:
        tier = "Early Stage"
        tier_color = "yellow"
    else:
        tier = "Starting"
        tier_color = "orange"

    # Format metric data for create_metric_card
    metric_data = {
        "metric_name": "completion_forecast",
        "alternative_name": "Completion Forecast",
        "value": days_to_completion if days_to_completion else 0,
        "unit": "days remaining",
        "performance_tier": tier,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "excluded_issue_count": 0,
        "details": {
            "completion_percentage": completion_percentage,
            "confidence": completion_confidence,
        },
        "tooltip": "PERT-based estimate of project completion date with confidence level",
    }

    return create_metric_card(metric_data, card_id="dashboard-forecast-card")


def create_dashboard_velocity_card(metrics: Dict[str, Any]) -> dbc.Card:
    """Create velocity metric card.

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Metric card for velocity
    """
    velocity_items = metrics.get("current_velocity_items", 0.0)
    velocity_points = metrics.get("current_velocity_points", 0.0)
    velocity_trend = metrics.get("velocity_trend", "stable")

    # Determine performance tier based on velocity trend
    if velocity_trend == "increasing":
        tier = "Accelerating"
        tier_color = "green"
    elif velocity_trend == "stable":
        tier = "Steady"
        tier_color = "blue"
    elif velocity_trend == "decreasing":
        tier = "Slowing"
        tier_color = "yellow"
    else:
        tier = "Unknown"
        tier_color = "orange"

    # Format metric data
    metric_data = {
        "metric_name": "current_velocity",
        "alternative_name": "Current Velocity",
        "value": velocity_items if velocity_items else 0,
        "unit": "items/week",
        "performance_tier": tier,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "excluded_issue_count": 0,
        "details": {
            "velocity_points": velocity_points,
            "trend": velocity_trend,
        },
        "tooltip": "Team throughput and delivery pace based on recent completion history",
    }

    return create_metric_card(metric_data, card_id="dashboard-velocity-card")


def create_dashboard_remaining_card(metrics: Dict[str, Any]) -> dbc.Card:
    """Create remaining work metric card.

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Metric card for remaining work
    """
    remaining_items = metrics.get("remaining_items", 0)
    remaining_points = metrics.get("remaining_points", 0.0)
    completion_percentage = metrics.get("completion_percentage", 0.0)

    # Determine performance tier based on remaining work
    if completion_percentage >= 75:
        tier = "Nearly Complete"
        tier_color = "green"
    elif completion_percentage >= 50:
        tier = "Halfway"
        tier_color = "blue"
    elif completion_percentage >= 25:
        tier = "In Progress"
        tier_color = "yellow"
    else:
        tier = "Starting Out"
        tier_color = "orange"

    # Format metric data
    metric_data = {
        "metric_name": "remaining_work",
        "alternative_name": "Remaining Work",
        "value": remaining_items if remaining_items else 0,
        "unit": "items",
        "performance_tier": tier,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "excluded_issue_count": 0,
        "details": {
            "remaining_points": remaining_points,
            "completion_percentage": completion_percentage,
        },
        "tooltip": "Outstanding work items and story points remaining in the project",
    }

    return create_metric_card(metric_data, card_id="dashboard-remaining-card")


def create_dashboard_pert_card(metrics: Dict[str, Any]) -> dbc.Card:
    """Create PERT timeline metric card.

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Metric card for PERT timeline
    """
    days_to_deadline = metrics.get("days_to_deadline", 0)
    days_to_completion = metrics.get("days_to_completion", 0)

    # Determine performance tier based on timeline vs deadline
    if days_to_completion and days_to_deadline:
        timeline_ratio = (
            days_to_completion / days_to_deadline if days_to_deadline > 0 else 0
        )

        if timeline_ratio <= 0.8:
            tier = "Ahead of Schedule"
            tier_color = "green"
        elif timeline_ratio <= 1.0:
            tier = "On Schedule"
            tier_color = "blue"
        elif timeline_ratio <= 1.2:
            tier = "At Risk"
            tier_color = "yellow"
        else:
            tier = "Behind Schedule"
            tier_color = "orange"
    else:
        tier = "Unknown"
        tier_color = "orange"

    # Format metric data
    metric_data = {
        "metric_name": "pert_timeline",
        "alternative_name": "Timeline Range",
        "value": days_to_deadline if days_to_deadline else 0,
        "unit": "days to deadline",
        "performance_tier": tier,
        "performance_tier_color": tier_color,
        "error_state": "success",
        "total_issue_count": 0,
        "excluded_issue_count": 0,
        "details": {
            "days_to_completion": days_to_completion,
        },
        "tooltip": "PERT-based timeline range showing optimistic, likely, and pessimistic completion scenarios",
    }

    return create_metric_card(metric_data, card_id="dashboard-pert-card")


def create_dashboard_overview_content(metrics: Dict[str, Any]) -> html.Div:
    """Create overview section content for dashboard (similar to DORA/Flow metrics).

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Div containing overview content
    """
    completion_percentage = metrics.get("completion_percentage", 0.0)
    days_to_completion = metrics.get("days_to_completion", 0)
    completion_confidence = metrics.get("completion_confidence", 0)
    velocity_items = metrics.get("current_velocity_items", 0.0)

    # Create summary row
    return html.Div(
        [
            dbc.Row(
                [
                    # Progress summary
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Progress",
                                        className="text-muted text-uppercase d-block mb-1",
                                    ),
                                    html.H4(
                                        f"{completion_percentage:.1f}%",
                                        className="mb-0",
                                        style={"color": "#0d6efd"},
                                    ),
                                ],
                                className="text-center",
                            ),
                        ],
                        xs=6,
                        md=3,
                        className="mb-3",
                    ),
                    # Estimated completion
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Est. Completion",
                                        className="text-muted text-uppercase d-block mb-1",
                                    ),
                                    html.H4(
                                        f"{days_to_completion} days"
                                        if days_to_completion
                                        else "N/A",
                                        className="mb-0",
                                        style={"color": "#198754"},
                                    ),
                                ],
                                className="text-center",
                            ),
                        ],
                        xs=6,
                        md=3,
                        className="mb-3",
                    ),
                    # Confidence level
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Confidence",
                                        className="text-muted text-uppercase d-block mb-1",
                                    ),
                                    html.H4(
                                        f"{completion_confidence}%"
                                        if completion_confidence
                                        else "N/A",
                                        className="mb-0",
                                        style={"color": "#ffc107"},
                                    ),
                                ],
                                className="text-center",
                            ),
                        ],
                        xs=6,
                        md=3,
                        className="mb-3",
                    ),
                    # Current velocity
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Small(
                                        "Velocity",
                                        className="text-muted text-uppercase d-block mb-1",
                                    ),
                                    html.H4(
                                        f"{velocity_items:.1f}/wk"
                                        if velocity_items
                                        else "N/A",
                                        className="mb-0",
                                        style={"color": "#0dcaf0"},
                                    ),
                                ],
                                className="text-center",
                            ),
                        ],
                        xs=6,
                        md=3,
                        className="mb-3",
                    ),
                ],
                className="g-3",
            ),
        ]
    )
