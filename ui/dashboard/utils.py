"""
Utility Functions for Comprehensive Dashboard

Provides shared helper functions for dashboard sections:
- Safe mathematical operations
- Date formatting utilities
- Project health score calculation
- Metric card creation
- Visualization helpers (sparklines, progress rings)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from dash import html

from ui.metric_cards import create_metric_card as create_professional_metric_card

logger = logging.getLogger(__name__)


def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: Number to divide
        denominator: Number to divide by
        default: Value to return if division fails

    Returns:
        Result of division or default value
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def format_date_relative(date_str, reference_date=None):
    """Format date with relative time context.

    Args:
        date_str: Date string to format
        reference_date: Reference date for comparison (defaults to now)

    Returns:
        Human-readable relative date string
    """
    if not date_str:
        return "Not set"

    try:
        target_date = pd.to_datetime(date_str, format="mixed", errors="coerce")
        ref_date = reference_date or datetime.now()
        days_diff = (target_date - ref_date).days

        if days_diff < 0:
            return f"{abs(days_diff)} days overdue"
        elif days_diff == 0:
            return "Today"
        elif days_diff <= 7:
            return f"{days_diff} days"
        elif days_diff <= 30:
            return f"{days_diff // 7} weeks"
        else:
            return f"{days_diff // 30} months"
    except Exception:
        return str(date_str)


def calculate_project_health_score(
    metrics: dict[str, Any],
    dora_metrics: dict[str, Any] | None = None,
    flow_metrics: dict[str, Any] | None = None,
    bug_metrics: dict[str, Any] | None = None,
    budget_metrics: dict[str, Any] | None = None,
    scope_metrics: dict[str, Any] | None = None,
) -> float:
    """Calculate overall project health score (0-100) using comprehensive multi-dimensional analysis.

    Formula - Comprehensive with dynamic weighting:
    Calculates health across 6 dimensions with dynamic weight redistribution when metrics are unavailable:
    - Delivery Performance (25% max): velocity, throughput, completion rate
    - Predictability (20% max): velocity CV, forecast confidence, schedule adherence
    - Quality (20% max): bug density, DORA CFR, bug resolution, MTTR
    - Efficiency (15% max): flow efficiency, flow time, resource utilization
    - Sustainability (10% max): scope stability, WIP management, flow distribution
    - Financial Health (10% max): budget adherence, burn rate, runway

    When extended metrics (DORA, Flow, Bug, Budget) are unavailable, the v3.0 calculator
    redistributes weights dynamically to available dimensions, ensuring consistent scoring.

    Args:
        metrics: Dashboard metrics with velocity, completion, schedule data
        dora_metrics: Optional DORA metrics for quality dimension
        flow_metrics: Optional flow metrics for efficiency dimension
        bug_metrics: Optional bug metrics for quality dimension
        budget_metrics: Optional budget metrics for financial health
        scope_metrics: Optional scope change metrics for sustainability

    Returns:
        Health score from 0-100
    """
    logger.info("[HEALTH v3.0] Using comprehensive multi-dimensional health formula")

    from data.project_health_calculator import (
        calculate_comprehensive_project_health,
        prepare_dashboard_metrics_for_health,
    )

    # Prepare metrics for comprehensive calculator using shared function (DRY)
    dashboard_metrics = prepare_dashboard_metrics_for_health(
        completion_percentage=metrics.get("completion_percentage", 0),
        current_velocity_items=metrics.get("current_velocity_items", 0),
        velocity_cv=metrics.get("velocity_cv", 0),
        trend_direction=metrics.get("trend_direction", "stable"),
        recent_velocity_change=metrics.get("recent_velocity_change", 0),
        schedule_variance_days=metrics.get("schedule_variance_days", 0),
        completion_confidence=metrics.get("completion_confidence", 50),
    )

    logger.info(
        f"[APP HEALTH] Input: completion_pct={metrics.get('completion_percentage', 0):.2f}, "
        f"velocity_items={metrics.get('current_velocity_items', 0):.2f}, "
        f"velocity_cv={metrics.get('velocity_cv', 0):.2f}, "
        f"trend={metrics.get('trend_direction', 'stable')}, "
        f"recent_change={metrics.get('recent_velocity_change', 0):.2f}, "
        f"schedule_var={metrics.get('schedule_variance_days', 0):.2f}, "
        f"confidence={metrics.get('completion_confidence', 50)}"
    )

    # Call comprehensive calculator
    health_result = calculate_comprehensive_project_health(
        dashboard_metrics=dashboard_metrics,
        dora_metrics=dora_metrics,
        flow_metrics=flow_metrics,
        bug_metrics=bug_metrics,
        budget_metrics=budget_metrics,
        scope_metrics=scope_metrics,
    )

    logger.info(
        f"[HEALTH v3.0] Overall Score: {health_result['overall_score']}/100 "
        f"(formula_version={health_result['formula_version']})"
    )

    return health_result["overall_score"]


def get_health_status(score: float) -> dict[str, str]:
    """Get health status configuration based on score.

    Args:
        score: Health score from 0-100

    Returns:
        Dictionary with label, color, icon, and background color
    """
    if score >= 70:
        return {
            "label": "GOOD",
            "color": "#28a745",
            "icon": "fa-check-circle",
            "bg_color": "rgba(40, 167, 69, 0.1)",
        }
    elif score >= 50:
        return {
            "label": "CAUTION",
            "color": "#ffc107",
            "icon": "fa-exclamation-triangle",
            "bg_color": "rgba(255, 193, 7, 0.1)",
        }
    elif score >= 30:
        return {
            "label": "AT RISK",
            "color": "#fd7e14",
            "icon": "fa-exclamation-triangle",
            "bg_color": "rgba(253, 126, 20, 0.1)",
        }
    else:
        return {
            "label": "CRITICAL",
            "color": "#dc3545",
            "icon": "fa-times-circle",
            "bg_color": "rgba(220, 53, 69, 0.1)",
        }


def get_brief_health_reason(health_metrics: dict[str, Any]) -> str:
    """Get brief one-line reason for health score.

    Args:
        health_metrics: Dictionary with velocity_cv, schedule_variance_days,
                       scope_change_rate, trend_direction, recent_velocity_change

    Returns:
        Brief reason string explaining the most concerning metric
    """
    # Identify most concerning metric (lowest performer)
    concerns = []

    # Check velocity consistency (CV)
    velocity_cv = health_metrics.get("velocity_cv", 0)
    if velocity_cv >= 40:
        concerns.append(("Velocity unpredictable (CV ≥ 40%)", 3))  # High priority
    elif velocity_cv >= 25:
        concerns.append(("Velocity inconsistent (CV ≥ 25%)", 2))

    # Check schedule
    schedule_variance = health_metrics.get("schedule_variance_days", 0)
    if schedule_variance > 30:
        concerns.append((f"Behind schedule ({int(schedule_variance)} days)", 3))
    elif schedule_variance > 14:
        concerns.append((f"Slightly behind ({int(schedule_variance)} days)", 2))

    # Check scope
    scope_change_rate = health_metrics.get("scope_change_rate", 0)
    if scope_change_rate > 30:
        concerns.append((f"High scope growth ({scope_change_rate:.0f}%)", 3))
    elif scope_change_rate > 15:
        concerns.append((f"Scope growing ({scope_change_rate:.0f}%)", 2))

    # Check trend
    trend_direction = health_metrics.get("trend_direction", "stable")
    if trend_direction == "declining":
        concerns.append(("Velocity declining", 2))

    # Check recent performance
    recent_change = health_metrics.get("recent_velocity_change", 0)
    if recent_change < -15:
        concerns.append((f"Recent drop ({recent_change:.0f}%)", 2))

    # Return highest priority concern
    if concerns:
        concerns.sort(key=lambda x: x[1], reverse=True)
        return concerns[0][0]

    return ""


def create_metric_card(
    title: str,
    value: Any,
    subtitle: str,
    icon: str,
    color: str,
    trend: dict[str, Any] | None = None,
    sparkline_data: list[float] | None = None,
    tooltip_text: str | None = None,
    tooltip_id: str | None = None,
) -> Any:
    """Create a standardized metric card using professional system.

    Adapter function that converts old card format to new professional
    metric_cards.create_metric_card format for visual consistency.

    Args:
        title: Card title text
        value: Primary metric value to display
        subtitle: Descriptive text below the value
        icon: Font Awesome icon class
        color: Color for icon and value
        trend: Optional trend data dict with 'direction' and 'percent'
        sparkline_data: Optional data for sparkline visualization
        tooltip_text: Optional help text for info tooltip
        tooltip_id: Optional unique ID suffix for tooltip

    Returns:
        Dash HTML Div component with metric card
    """
    # Convert old format to professional metric_data format
    # Extract numeric value from formatted string
    try:
        numeric_value = (
            float(value.replace(",", "").split()[0])
            if isinstance(value, str)
            else float(value)
        )
    except (ValueError, IndexError, AttributeError):
        numeric_value = None

    # Determine performance tier color based on value
    if numeric_value is not None:
        if numeric_value > 15:
            tier_color = "green"
        elif numeric_value > 8:
            tier_color = "yellow"
        elif numeric_value > 3:
            tier_color = "orange"
        else:
            tier_color = "red"
    else:
        tier_color = "green"

    metric_data = {
        "metric_name": title.lower().replace(" ", "_"),
        "display_name": title,
        "value": numeric_value,
        "unit": "",
        "subtitle": subtitle,
        "icon": icon,
        "color": color,
        "performance_tier_color": tier_color,
        "error_state": "success" if numeric_value is not None else "no_data",
        "tooltip": tooltip_text,
        "weekly_values": sparkline_data if sparkline_data else [],
        "trend_direction": trend.get("direction", "stable")
        if trend and trend.get("direction") != "baseline"
        else "stable",
        "trend_percent": abs(trend.get("percent", 0))
        if trend and trend.get("direction") != "baseline"
        else 0,
    }

    # Handle baseline case
    if trend and trend.get("direction") == "baseline":
        metric_data["error_state"] = "building_baseline"
        metric_data["error_message"] = trend.get("message", "Building baseline")

    return create_professional_metric_card(metric_data, show_details_button=False)


def create_mini_sparkline(data: list[float], color: str, height: int = 20) -> html.Div:
    """Create a mini CSS sparkline.

    Args:
        data: List of numeric values to visualize
        color: Color for sparkline bars
        height: Height of sparkline in pixels

    Returns:
        Dash HTML Div with sparkline visualization
    """
    if not data or len(data) < 2:
        return html.Div()

    max_val = max(data) if max(data) > 0 else 1
    normalized = [v / max_val for v in data]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * height, 2)
        opacity = 0.4 + (i / len(normalized)) * 0.6

        bars.append(
            html.Div(
                style={
                    "width": "5px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center mt-2",
        style={"height": f"{height}px", "gap": "3px", "minWidth": "80px"},
    )


def create_progress_ring(percentage: float, color: str, size: int = 80) -> html.Div:
    """Create accurate circular progress indicator using conic-gradient.

    Args:
        percentage: Progress percentage (0-100)
        color: Color for progress arc
        size: Size of ring in pixels

    Returns:
        Dash HTML Div with progress ring
    """
    # Inner white circle to create ring effect
    inner_size = size - 16

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        f"{percentage:.0f}%",
                        style={
                            "position": "absolute",
                            "top": "50%",
                            "left": "50%",
                            "transform": "translate(-50%, -50%)",
                            "fontSize": "1.1rem",
                            "fontWeight": "bold",
                            "color": "#333",
                            "textAlign": "center",
                            "zIndex": "2",
                        },
                    )
                ],
                style={
                    "width": f"{inner_size}px",
                    "height": f"{inner_size}px",
                    "borderRadius": "50%",
                    "background": "white",
                    "position": "absolute",
                    "top": "8px",
                    "left": "8px",
                    "zIndex": "1",
                },
            )
        ],
        style={
            "width": f"{size}px",
            "height": f"{size}px",
            "borderRadius": "50%",
            "background": f"conic-gradient(from -90deg, {color} 0deg {percentage * 3.6}deg, #e9ecef {percentage * 3.6}deg 360deg)",
            "position": "relative",
            "transition": "all 0.3s ease",
            "display": "inline-block",
        },
    )
