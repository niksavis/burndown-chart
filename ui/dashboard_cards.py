"""Dashboard Metric Cards using modern metric_cards.py patterns.

This module provides dashboard-specific metric card creation using the
standardized metric_cards.py component for visual consistency with DORA/Flow metrics.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html

from ui.metric_cards import create_metric_card
from ui.tooltip_utils import create_info_tooltip


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
        Div containing overview content with enhanced visuals
    """
    completion_percentage = metrics.get("completion_percentage", 0.0)
    days_to_completion = metrics.get("days_to_completion", 0)
    completion_confidence = metrics.get("completion_confidence", 0)
    velocity_items = metrics.get("current_velocity_items", 0.0)
    velocity_trend = metrics.get("velocity_trend", "stable")
    days_to_deadline = metrics.get("days_to_deadline", 0)

    # Calculate project health score (0-100)
    health_score = _calculate_health_score(metrics)
    health_color, health_label = _get_health_color_and_label(health_score)

    # Determine trend icon and color
    trend_icons = {
        "increasing": ("fas fa-arrow-up", "#198754"),  # Green
        "stable": ("fas fa-minus", "#0dcaf0"),  # Cyan
        "decreasing": ("fas fa-arrow-down", "#ffc107"),  # Warning
        "unknown": ("fas fa-question", "#6c757d"),  # Gray
    }
    trend_icon, trend_color = trend_icons.get(velocity_trend, trend_icons["unknown"])

    # Create summary row with enhanced visuals
    return html.Div(
        [
            # Project Health Score - Prominent at top
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Div(
                                                [
                                                    html.Small(
                                                        "Project Health Score",
                                                        className="text-muted text-uppercase fw-medium me-2",
                                                        style={
                                                            "display": "inline-block"
                                                        },
                                                    ),
                                                    create_info_tooltip(
                                                        help_text=(
                                                            "Weighted health score based on: "
                                                            "Progress (25%) - completion percentage, "
                                                            "Schedule Adherence (30%) - forecast vs deadline, "
                                                            "Velocity Stability (25%) - team consistency, "
                                                            "Confidence (20%) - estimate reliability"
                                                        ),
                                                        id_suffix="project-health-score",
                                                    ),
                                                ],
                                                className="d-block mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.H1(
                                                        f"{health_score}",
                                                        className="mb-0 d-inline-block",
                                                        style={
                                                            "color": health_color,
                                                            "fontSize": "3.5rem",
                                                            "fontWeight": "700",
                                                        },
                                                    ),
                                                    html.Span(
                                                        "/100",
                                                        className="text-muted ms-2",
                                                        style={"fontSize": "1.5rem"},
                                                    ),
                                                ],
                                            ),
                                            html.Div(
                                                [
                                                    dbc.Badge(
                                                        health_label,
                                                        color=health_color.replace(
                                                            "#", ""
                                                        ),
                                                        className="mt-2",
                                                        style={
                                                            "fontSize": "0.875rem",
                                                            "padding": "0.5rem 1rem",
                                                        },
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="text-center",
                                    ),
                                    # Progress bar
                                    html.Div(
                                        [
                                            html.Small(
                                                f"{completion_percentage:.1f}% Complete",
                                                className="text-muted d-block mb-1 text-center",
                                                style={"fontSize": "0.75rem"},
                                            ),
                                            dbc.Progress(
                                                value=completion_percentage,
                                                className="mb-0",
                                                style={"height": "8px"},
                                                color="success"
                                                if completion_percentage >= 75
                                                else "primary",
                                            ),
                                        ],
                                        className="mt-3",
                                    ),
                                ],
                                className="p-3",
                            ),
                        ],
                        xs=12,
                        md=4,
                        className="mb-3 mb-md-0",
                    ),
                    # Key Metrics Grid
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    # Estimated Completion with icon
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-calendar-check text-success mb-2",
                                                        style={"fontSize": "1.5rem"},
                                                    ),
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
                                        className="mb-3",
                                    ),
                                    # Velocity with trend indicator
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className=trend_icon,
                                                        style={
                                                            "fontSize": "1.5rem",
                                                            "color": trend_color,
                                                        },
                                                    ),
                                                    html.Small(
                                                        "Velocity",
                                                        className="text-muted text-uppercase d-block mb-1 mt-2",
                                                    ),
                                                    html.H4(
                                                        f"{velocity_items:.1f}/wk"
                                                        if velocity_items
                                                        else "N/A",
                                                        className="mb-0",
                                                        style={"color": trend_color},
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ],
                                        xs=6,
                                        className="mb-3",
                                    ),
                                    # Confidence
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-chart-line text-warning mb-2",
                                                        style={"fontSize": "1.5rem"},
                                                    ),
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
                                        className="mb-3 mb-md-0",
                                    ),
                                    # Days to Deadline
                                    dbc.Col(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-flag-checkered text-primary mb-2",
                                                        style={"fontSize": "1.5rem"},
                                                    ),
                                                    html.Small(
                                                        "To Deadline",
                                                        className="text-muted text-uppercase d-block mb-1",
                                                    ),
                                                    html.H4(
                                                        f"{days_to_deadline} days"
                                                        if days_to_deadline
                                                        else "N/A",
                                                        className="mb-0",
                                                        style={"color": "#0d6efd"},
                                                    ),
                                                ],
                                                className="text-center",
                                            ),
                                        ],
                                        xs=6,
                                        className="mb-3 mb-md-0",
                                    ),
                                ],
                                className="g-3",
                            ),
                        ],
                        xs=12,
                        md=8,
                    ),
                ],
                className="mb-3",
            ),
            # Key Insights Section
            _create_key_insights(metrics),
        ]
    )


def _calculate_health_score(metrics: Dict[str, Any]) -> int:
    """Calculate overall project health score (0-100) using continuous/proportional scoring.

    This function uses the SAME formula as dashboard_comprehensive._calculate_project_health_score()
    to ensure consistency across all dashboard components.

    Weights:
    - Velocity consistency: 30% (lower CV = better)
    - Schedule performance: 25% (on-time or early = better)
    - Scope stability: 20% (low growth rate = better)
    - Quality trends: 15% (improving = better)
    - Recent performance: 10% (positive change = better)

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Health score from 0-100
    """
    # Extract or calculate velocity CV
    velocity_cv = metrics.get("velocity_cv", 0)
    if not velocity_cv:
        # Map velocity trend to CV approximation for backward compatibility
        velocity_trend = metrics.get("velocity_trend", "stable")
        velocity_cv_map = {
            "increasing": 20,  # Good consistency with improvement
            "stable": 25,  # Normal consistency
            "decreasing": 40,  # Higher variation when declining
            "unknown": 30,  # Assume moderate variation
        }
        velocity_cv = velocity_cv_map.get(velocity_trend, 30)

    # Velocity consistency (30 points max)
    # CV of 0% = full points, CV of 50%+ = 0 points, linear in between
    velocity_score = max(0, 30 * (1 - min(velocity_cv / 50, 1)))

    # Schedule performance (25 points max)
    # On-time or early = full points, 60+ days late = 0 points, linear penalty
    days_to_completion = metrics.get("days_to_completion", 0)
    days_to_deadline = metrics.get("days_to_deadline", 0)
    schedule_variance_days = metrics.get(
        "schedule_variance_days",
        abs(days_to_completion - days_to_deadline)
        if days_to_completion and days_to_deadline
        else 0,
    )
    schedule_score = max(0, 25 * (1 - min(schedule_variance_days / 60, 1)))

    # Scope stability (20 points max)
    # 0% growth = full points, 40%+ growth = 0 points, linear penalty
    scope_change_rate = metrics.get("scope_change_rate", 0)
    scope_score = max(0, 20 * (1 - min(scope_change_rate / 40, 1)))

    # Quality trends (15 points max)
    # Improving = 15, stable = 10, declining = 0
    trend_direction = metrics.get("trend_direction", "stable")
    if not trend_direction or trend_direction == "unknown":
        velocity_trend = metrics.get("velocity_trend", "stable")
        if velocity_trend == "increasing":
            trend_direction = "improving"
        elif velocity_trend == "decreasing":
            trend_direction = "declining"
        else:
            trend_direction = "stable"

    if trend_direction == "improving":
        trend_score = 15
    elif trend_direction == "stable":
        trend_score = 10
    else:  # declining
        trend_score = 0

    # Recent performance (10 points max)
    # +20% change = 10 points, 0% = 5 points, -20% = 0 points, linear
    recent_velocity_change = metrics.get("recent_velocity_change", 0)
    if not recent_velocity_change:
        # Use confidence as proxy if recent_velocity_change not available
        completion_confidence = metrics.get("completion_confidence") or 50
        if completion_confidence > 80:
            recent_velocity_change = 15
        elif completion_confidence < 40:
            recent_velocity_change = -25
        else:
            recent_velocity_change = 0

    if recent_velocity_change >= 0:
        # Positive change: 5 base + up to 5 bonus for improvement
        recent_score = 5 + min(5, 5 * (recent_velocity_change / 20))
    else:
        # Negative change: linear penalty from 5 down to 0
        recent_score = max(0, 5 * (1 + recent_velocity_change / 20))

    # Calculate total score (sum of all components)
    total_score = (
        velocity_score + schedule_score + scope_score + trend_score + recent_score
    )

    return max(0, min(100, int(total_score)))


def _get_health_color_and_label(score: int) -> tuple[str, str]:
    """Get color and label for health score.

    Args:
        score: Health score (0-100)

    Returns:
        Tuple of (color_hex, label_text)
    """
    if score >= 80:
        return "#198754", "Excellent"  # Green
    elif score >= 60:
        return "#0dcaf0", "Good"  # Cyan
    elif score >= 40:
        return "#ffc107", "Fair"  # Yellow
    else:
        return "#fd7e14", "Needs Attention"  # Orange


def _create_key_insights(metrics: Dict[str, Any]) -> html.Div:
    """Create key insights section with actionable intelligence.

    Args:
        metrics: Dashboard metrics dictionary

    Returns:
        Div containing key insights
    """
    insights = []

    # Schedule insight
    days_to_completion = metrics.get("days_to_completion", 0)
    days_to_deadline = metrics.get("days_to_deadline", 0)

    if days_to_completion and days_to_deadline:
        days_diff = days_to_deadline - days_to_completion
        if days_diff > 0:
            insights.append(
                {
                    "icon": "fas fa-check-circle",
                    "color": "success",
                    "text": f"Trending {abs(days_diff)} days ahead of deadline",
                }
            )
        elif days_diff < 0:
            insights.append(
                {
                    "icon": "fas fa-exclamation-triangle",
                    "color": "warning",
                    "text": f"Trending {abs(days_diff)} days behind deadline",
                }
            )
        else:
            insights.append(
                {
                    "icon": "fas fa-bullseye",
                    "color": "primary",
                    "text": "On track to meet deadline",
                }
            )

    # Velocity insight
    velocity_trend = metrics.get("velocity_trend", "unknown")
    if velocity_trend == "increasing":
        insights.append(
            {
                "icon": "fas fa-arrow-up",
                "color": "success",
                "text": "Team velocity is accelerating",
            }
        )
    elif velocity_trend == "decreasing":
        insights.append(
            {
                "icon": "fas fa-arrow-down",
                "color": "warning",
                "text": "Team velocity is declining - consider addressing blockers",
            }
        )

    # Progress insight
    completion_percentage = metrics.get("completion_percentage", 0.0)
    if completion_percentage >= 75:
        insights.append(
            {
                "icon": "fas fa-star",
                "color": "success",
                "text": "Project is in final stretch - great progress!",
            }
        )

    # Return insights section if we have any
    if not insights:
        return html.Div()

    return html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            [
                                html.I(className="fas fa-lightbulb me-2"),
                                html.Strong("Key Insights"),
                            ],
                            className="mb-2",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.I(
                                            className=f"{insight['icon']} text-{insight['color']} me-2",
                                        ),
                                        html.Span(insight["text"]),
                                    ],
                                    className="mb-2"
                                    if i < len(insights) - 1
                                    else "mb-0",
                                )
                                for i, insight in enumerate(insights)
                            ],
                        ),
                    ],
                    className="py-2 px-3",
                ),
                className="border-0",
                style={
                    "backgroundColor": "#e7f3ff",  # Light blue background
                    "borderLeft": "4px solid #0d6efd",
                },
            ),
        ],
        className="mt-3",
    )
