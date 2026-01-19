"""
Comprehensive Project Dashboard - Modern Analytics Platform

A beautiful, comprehensive dashboard that provides deep insights into project health,
team performance, and delivery forecasts. Method-agnostic design supports any
project management approach (Scrum, Kanban, Waterfall, etc.).

Key Features:
- Executive summary with project health score
- Throughput analytics with trend analysis
- Multi-method forecasting (PERT, confidence intervals)
- Scope change tracking and quality metrics
- Team velocity and capacity planning
- Actionable insights and recommendations
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
from datetime import datetime, timedelta


from ui.style_constants import COLOR_PALETTE
from ui.tooltip_utils import create_info_tooltip
from ui.budget_section import _create_budget_section
from ui.budget_cards import create_forecast_alignment_card
from ui.metric_cards import create_metric_card as create_professional_metric_card
from configuration.help_content import DASHBOARD_METRICS_TOOLTIPS


#######################################################################
# UTILITY FUNCTIONS
#######################################################################


def _safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers, returning default if denominator is zero."""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


def _format_date_relative(date_str, reference_date=None):
    """Format date with relative time context."""
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


def _calculate_project_health_score(
    metrics,
    dora_metrics=None,
    flow_metrics=None,
    bug_metrics=None,
    budget_metrics=None,
    scope_metrics=None,
):
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
    """
    import logging

    logger = logging.getLogger(__name__)

    # Always use comprehensive v3.0 calculator with dynamic weighting
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


def _get_health_status(score):
    """Get health status configuration based on score."""
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


def _get_brief_health_reason(health_metrics: dict) -> str:
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


def _create_metric_card(
    title,
    value,
    subtitle,
    icon,
    color,
    trend=None,
    sparkline_data=None,
    tooltip_text=None,
    tooltip_id=None,
):
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


def _create_mini_sparkline(data, color, height=20):
    """Create a mini CSS sparkline."""
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


def _create_progress_ring(percentage, color, size=80):
    """Create accurate circular progress indicator using conic-gradient."""
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


#######################################################################
# MAIN DASHBOARD SECTIONS
#######################################################################


def _create_executive_summary(
    statistics_df, settings, forecast_data, avg_weekly_items=0
):
    """Create executive summary section with key project health indicators.

    The Data Points slider affects historical metrics but not current remaining work:
    - Remaining (items/points): Always shows current not-yet-done work (fixed)
    - Completed (items/points): Shows work completed in the selected window (changes with slider)
    - Total: Remaining + Completed (changes with slider as Completed changes)
    """
    # Calculate completed items from the FILTERED statistics DataFrame
    completed_items = (
        statistics_df["completed_items"].sum() if not statistics_df.empty else 0
    )
    completed_points = (
        statistics_df["completed_points"].sum() if not statistics_df.empty else 0
    )

    # Use CURRENT remaining from settings (fixed, doesn't change with slider)
    remaining_items = settings.get("total_items", 0)
    remaining_points = settings.get("total_points", 0)

    # Calculate total scope = remaining + completed in window
    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    deadline = settings.get("deadline")

    completion_percentage = _safe_divide(completed_items, total_items) * 100
    points_percentage = (
        _safe_divide(completed_points, total_points) * 100 if total_points > 0 else 0
    )

    # DEBUG: Log completion calculation
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"[APP COMPLETION] completed_items={completed_items}, remaining_items={remaining_items}, "
        f"total_items={total_items}, completion_pct={completion_percentage:.2f}%"
    )

    # Calculate project health score with DYNAMIC metrics from filtered data
    velocity_cv = forecast_data.get("velocity_cv", 0)
    schedule_variance = forecast_data.get("schedule_variance_days", 0)

    # Calculate trend direction from filtered data
    trend_direction = "stable"
    recent_velocity_change = 0

    if not statistics_df.empty and len(statistics_df) >= 6:
        # Split data into older and recent halves
        mid_point = len(statistics_df) // 2
        older_half = statistics_df.iloc[:mid_point]
        recent_half = statistics_df.iloc[mid_point:]

        # Calculate velocity for each half (items per week)
        if len(older_half) > 0 and len(recent_half) > 0:
            older_weeks = max(1, len(older_half))
            recent_weeks = max(1, len(recent_half))

            older_velocity = older_half["completed_items"].sum() / older_weeks
            recent_velocity = recent_half["completed_items"].sum() / recent_weeks

            if older_velocity > 0:
                recent_velocity_change = (
                    (recent_velocity - older_velocity) / older_velocity
                ) * 100

                # Determine trend direction (>10% change is significant)
                if recent_velocity_change > 10:
                    trend_direction = "improving"
                elif recent_velocity_change < -10:
                    trend_direction = "declining"

    # Calculate scope change rate from filtered data
    scope_change_rate = 0
    if not statistics_df.empty and "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    # Calculate completion confidence from schedule variance (same as report)
    # Positive schedule_variance = ahead of schedule (buffer days)
    # Negative schedule_variance = behind schedule
    buffer_days = (
        schedule_variance  # schedule_variance is forecast_days - days_to_deadline
    )
    if buffer_days >= 28:
        completion_confidence = 95  # Very high confidence
    elif buffer_days >= 14:
        completion_confidence = 80  # High confidence
    elif buffer_days >= 0:
        completion_confidence = 65  # Moderate confidence
    elif buffer_days >= -14:
        completion_confidence = 45  # Low confidence
    else:
        completion_confidence = 25  # Very low confidence

    health_metrics = {
        "completion_percentage": completion_percentage,
        "current_velocity_items": avg_weekly_items,  # Items per week from filtered statistics
        "velocity_cv": velocity_cv,
        "schedule_variance_days": schedule_variance,
        "scope_change_rate": scope_change_rate,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
        "completion_confidence": completion_confidence,  # Calculated from schedule variance
    }

    # DEBUG: Log health metrics to trace 18% vs 13% discrepancy
    import logging

    logger = logging.getLogger(__name__)
    logger.info(
        f"[HEALTH CALC] Input metrics: velocity_cv={velocity_cv:.2f}, "
        f"schedule_variance={schedule_variance:.2f}, scope_change_rate={scope_change_rate:.2f}, "
        f"trend_direction={trend_direction}, recent_velocity_change={recent_velocity_change:.2f}, "
        f"statistics_rows={len(statistics_df)}"
    )

    # Extract extended metrics from additional_context (calculated in callback)
    # These are optional - if not available, uses dashboard-only mode with adaptive weighting
    extended_metrics = settings.get("extended_metrics", {})

    dora_metrics = extended_metrics.get("dora")
    flow_metrics = extended_metrics.get("flow")
    bug_metrics = extended_metrics.get("bug_analysis")
    budget_metrics = settings.get("budget_data")  # Budget data passed separately
    scope_metrics = {"scope_change_rate": scope_change_rate}

    # Log available extended metrics for v3.0 comprehensive formula
    logger.info(
        f"[HEALTH v3.0] Available extended metrics: "
        f"DORA={'✓' if dora_metrics else '✗'}, "
        f"Flow={'✓' if flow_metrics else '✗'}, "
        f"Bug={'✓' if bug_metrics else '✗'}, "
        f"Budget={'✓' if budget_metrics else '✗'}"
    )

    health_score = _calculate_project_health_score(
        health_metrics,
        dora_metrics=dora_metrics,
        flow_metrics=flow_metrics,
        bug_metrics=bug_metrics,
        budget_metrics=budget_metrics,
        scope_metrics=scope_metrics,
    )

    logger.info(f"[HEALTH CALC] Calculated health_score={health_score}%")

    health_status = _get_health_status(health_score)
    health_reason = _get_brief_health_reason(health_metrics)

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4(
                        [
                            html.I(
                                className="fas fa-tachometer-alt me-2",
                                style={"color": "#007bff"},
                            ),
                            "Project Health Overview",
                            html.Span(
                                [
                                    html.I(
                                        className="fas fa-info-circle ms-2",
                                        id="health-calculation-info",
                                        style={
                                            "fontSize": "0.9rem",
                                            "color": "#6c757d",
                                            "cursor": "help",
                                        },
                                    ),
                                    dbc.Tooltip(
                                        DASHBOARD_METRICS_TOOLTIPS["health_score"],
                                        target="health-calculation-info",
                                        placement="right",
                                    ),
                                ],
                                className="d-inline",
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Redesigned metrics row with consistent sizing and alignment
                    dbc.Row(
                        [
                            # Health Score
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-heartbeat me-2",
                                                    style={"color": "#495057"},
                                                ),
                                                "Health",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": "#495057",
                                            },
                                        ),
                                        _create_progress_ring(
                                            health_score, health_status["color"], 80
                                        ),
                                        html.Div(
                                            health_status["label"],
                                            className="mt-3 mb-1",
                                            style={
                                                "fontSize": "1rem",
                                                "fontWeight": "bold",
                                                "color": health_status["color"],
                                            },
                                        ),
                                        html.Small(
                                            health_reason,
                                            className="text-muted d-block mb-3",
                                            style={
                                                "fontSize": "0.75rem",
                                                "fontStyle": "italic",
                                            },
                                        )
                                        if health_reason
                                        else html.Div(className="mb-2"),
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-calendar-alt me-1",
                                                            style={
                                                                "fontSize": "0.8rem"
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Deadline: ",
                                                            style={"fontWeight": "600"},
                                                        ),
                                                        html.Span(
                                                            deadline
                                                            if deadline
                                                            else "Not set"
                                                        ),
                                                    ],
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "color": "#495057",
                                                    },
                                                ),
                                                html.Div(
                                                    [
                                                        html.I(
                                                            className="fas fa-chart-line me-1",
                                                            style={
                                                                "fontSize": "0.8rem"
                                                            },
                                                        ),
                                                        html.Span(
                                                            "Forecast: ",
                                                            style={"fontWeight": "600"},
                                                            title=f"PERT-weighted forecast based on {'story points' if settings.get('show_points', True) else 'items'} velocity (matches Burndown Chart and Report)",
                                                        ),
                                                        html.Span(
                                                            forecast_data.get(
                                                                "completion_date"
                                                            )
                                                            or "Not calculated"
                                                        ),
                                                    ],
                                                    style={
                                                        "fontSize": "0.8rem",
                                                        "color": "#495057",
                                                    },
                                                ),
                                            ],
                                        ),
                                    ],
                                    className="text-center",
                                    style={
                                        "padding": "15px 10px",
                                        "borderRight": "2px solid #dee2e6",
                                    },
                                ),
                                xs=12,
                                md=2,
                                className="mb-4 mb-md-0",
                            ),
                            # Items Group
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-tasks me-2",
                                                    style={
                                                        "color": COLOR_PALETTE["items"]
                                                    },
                                                ),
                                                "Items",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": COLOR_PALETTE["items"],
                                            },
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            _create_progress_ring(
                                                                completion_percentage,
                                                                COLOR_PALETTE["items"],
                                                                80,
                                                            ),
                                                            html.Div(
                                                                f"{completed_items:,}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.1rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            _create_progress_ring(
                                                                100
                                                                - completion_percentage,
                                                                COLOR_PALETTE["items"],
                                                                80,
                                                            ),
                                                            html.Div(
                                                                f"{remaining_items:,}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.1rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "items"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                        ),
                                        html.Hr(
                                            className="my-2",
                                            style={
                                                "width": "80%",
                                                "margin": "10px auto",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-tasks me-1",
                                                    style={
                                                        "color": COLOR_PALETTE["items"]
                                                    },
                                                ),
                                                html.Span(
                                                    f"{total_items:,} items",
                                                    style={"fontWeight": "600"},
                                                ),
                                            ],
                                            className="mt-2 text-center",
                                            style={
                                                "fontSize": "0.8rem",
                                                "color": "#495057",
                                            },
                                        ),
                                    ],
                                    style={
                                        "padding": "15px 10px",
                                        "borderRight": "2px solid #dee2e6",
                                    },
                                ),
                                xs=12,
                                md=5,
                                className="mb-4 mb-md-0",
                            ),
                            # Points Group
                            dbc.Col(
                                html.Div(
                                    [
                                        html.H6(
                                            [
                                                html.I(
                                                    className="fas fa-chart-bar me-2",
                                                    style={
                                                        "color": COLOR_PALETTE["points"]
                                                    },
                                                ),
                                                "Points",
                                            ],
                                            className="mb-3 text-center",
                                            style={
                                                "fontSize": "0.95rem",
                                                "fontWeight": "600",
                                                "color": COLOR_PALETTE["points"],
                                            },
                                        ),
                                        # Case 1: Points tracking enabled with data
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            _create_progress_ring(
                                                                points_percentage,
                                                                COLOR_PALETTE["points"],
                                                                80,
                                                            ),
                                                            html.Div(
                                                                f"{completed_points:,.1f}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.1rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Completed",
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                                dbc.Col(
                                                    html.Div(
                                                        [
                                                            _create_progress_ring(
                                                                100 - points_percentage,
                                                                COLOR_PALETTE["points"],
                                                                80,
                                                            ),
                                                            html.Div(
                                                                f"{remaining_points:,.1f}",
                                                                className="mt-3 mb-1",
                                                                style={
                                                                    "fontSize": "1.1rem",
                                                                    "fontWeight": "bold",
                                                                    "color": COLOR_PALETTE[
                                                                        "points"
                                                                    ],
                                                                },
                                                            ),
                                                            html.Div(
                                                                "Remaining",
                                                                style={
                                                                    "fontSize": "0.85rem",
                                                                    "color": "#6c757d",
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center",
                                                    ),
                                                    width=6,
                                                ),
                                            ],
                                        )
                                        if (
                                            total_points > 0
                                            and settings.get("show_points", True)
                                        )
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
                                                style={
                                                    "padding": "20px 10px",
                                                },
                                            )
                                            if not settings.get("show_points", True)
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
                                                style={
                                                    "padding": "20px 10px",
                                                },
                                            )
                                        ),
                                        html.Hr(
                                            className="my-2",
                                            style={
                                                "width": "80%",
                                                "margin": "10px auto",
                                            },
                                        )
                                        if total_points > 0
                                        and settings.get("show_points", True)
                                        else None,
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-chart-bar me-1",
                                                    style={
                                                        "color": COLOR_PALETTE["points"]
                                                    },
                                                ),
                                                html.Span(
                                                    f"{total_points:,.1f} points",
                                                    style={"fontWeight": "600"},
                                                ),
                                            ],
                                            className="mt-2 text-center",
                                            style={
                                                "fontSize": "0.8rem",
                                                "color": "#495057",
                                            },
                                        )
                                        if total_points > 0
                                        and settings.get("show_points", True)
                                        else None,
                                    ],
                                    style={"padding": "15px 10px"},
                                ),
                                xs=12,
                                md=5,
                                className="mb-4 mb-md-0",
                            ),
                        ],
                        className="mb-3",
                    ),
                ]
            )
        ],
        className="mb-4 shadow-sm",
        style={
            "background": health_status["bg_color"],
            "border": f"2px solid {health_status['color']}",
            "borderRadius": "0.375rem",
            "transition": "all 0.2s ease-in-out",
        },
        id="project-health-overview-card",
    )


def _create_throughput_section(
    statistics_df,
    forecast_data,
    settings,
    data_points_count=None,
    additional_context=None,
):
    """Create throughput analytics section.

    CRITICAL: Project Dashboard calculates velocity ad-hoc from project_statistics
    to work WITHOUT changelog data. This is different from DORA/Flow metrics which
    use metric snapshots (requires changelog).

    Args:
        statistics_df: DataFrame with filtered statistics (fallback only)
        forecast_data: Dictionary with forecast data
        settings: Settings dictionary containing show_points flag
        data_points_count: Number of weeks for velocity calculation
        additional_context: Dict with profile_id, query_id, current_week_label
    """
    import logging

    logger = logging.getLogger(__name__)
    show_points = settings.get("show_points", True)
    if statistics_df.empty:
        return html.Div()

    # Calculate velocity ad-hoc from project_statistics (works without changelog)
    # This ensures Project Dashboard functions independently of DORA/Flow metrics
    avg_items = None
    avg_points = None

    if (
        additional_context
        and additional_context.get("profile_id")
        and additional_context.get("query_id")
        and additional_context.get("current_week_label")
        and data_points_count
    ):
        from data.budget_calculator import _get_velocity, _get_velocity_points

        avg_items = _get_velocity(
            additional_context["profile_id"],
            additional_context["query_id"],
            additional_context["current_week_label"],
            data_points_count,
        )
        avg_points = _get_velocity_points(
            additional_context["profile_id"],
            additional_context["query_id"],
            additional_context["current_week_label"],
            data_points_count,
        )
        logger.info(
            f"[DASHBOARD] Using _get_velocity for Items per Week: {avg_items:.2f}, "
            f"Points per Week: {avg_points:.2f} (data_points_count={data_points_count})"
        )
    else:
        # Fallback to simple statistics mean
        avg_items = statistics_df["completed_items"].mean()
        avg_points = statistics_df["completed_points"].mean()
        logger.info(
            f"[DASHBOARD] Using statistics fallback for Items per Week: {avg_items:.2f}"
        )

    # Calculate trends by comparing older vs recent halves of filtered data
    items_trend = None
    points_trend = None
    weeks_available = len(statistics_df)

    if weeks_available >= 8:
        # Have enough data for full trend comparison (4 weeks vs 4 weeks)
        mid_point = weeks_available // 2
        older_half = statistics_df.iloc[:mid_point]
        recent_half = statistics_df.iloc[mid_point:]

        older_items = older_half["completed_items"].mean()
        recent_items = recent_half["completed_items"].mean()
        items_trend = {
            "direction": "up"
            if recent_items > older_items
            else "down"
            if recent_items < older_items
            else "stable",
            "percent": abs((recent_items - older_items) / older_items * 100)
            if older_items > 0
            else 0,
        }

        older_points = older_half["completed_points"].mean()
        recent_points = recent_half["completed_points"].mean()
        points_trend = {
            "direction": "up"
            if recent_points > older_points
            else "down"
            if recent_points < older_points
            else "stable",
            "percent": abs((recent_points - older_points) / older_points * 100)
            if older_points > 0
            else 0,
        }
    elif weeks_available >= 4:
        # Have baseline data but not enough for trend comparison
        # Show a message indicating we're building baseline
        items_trend = {
            "direction": "baseline",
            "percent": 0,
            "message": f"Building baseline ({weeks_available} of 8 weeks)",
        }
        points_trend = {
            "direction": "baseline",
            "percent": 0,
            "message": f"Building baseline ({weeks_available} of 8 weeks)",
        }
    else:
        # Not enough data yet
        items_trend = None
        points_trend = None

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-shipping-fast me-2",
                        style={"color": "#28a745"},
                    ),
                    "Team Throughput Analytics",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "items_per_week",
                                    "display_name": "Items per Week",
                                    "value": avg_items,
                                    "unit": "items/week",
                                    "subtitle": "Average delivery rate",
                                    "icon": "fa-tasks",
                                    "color": COLOR_PALETTE["items"],
                                    "performance_tier_color": "green"
                                    if avg_items > 10
                                    else "yellow"
                                    if avg_items > 5
                                    else "orange",
                                    "error_state": "success",
                                    "_n_weeks": data_points_count,
                                    "tooltip": "Average number of work items completed per week. Calculated using the corrected velocity method that counts actual weeks with data (not date range spans).",
                                    "weekly_values": list(
                                        statistics_df["completed_items"]
                                    )
                                    if not statistics_df.empty
                                    else [],
                                    "trend_direction": items_trend.get("direction")
                                    if items_trend
                                    else "stable",
                                    "trend_percent": items_trend.get("percent", 0)
                                    if items_trend
                                    else 0,
                                }
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "points_per_week",
                                    "display_name": "Points per Week",
                                    "value": avg_points
                                    if (show_points and avg_points and avg_points > 0)
                                    else None,
                                    "unit": "points/week"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "subtitle": "Average story points"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "icon": "fa-chart-bar",
                                    "color": COLOR_PALETTE["points"]
                                    if (show_points and avg_points and avg_points > 0)
                                    else "#6c757d",
                                    "performance_tier_color": "green"
                                    if show_points and avg_points and avg_points > 20
                                    else "yellow"
                                    if show_points and avg_points and avg_points > 10
                                    else "orange",
                                    "error_state": "success"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "points_tracking_disabled"
                                    if not show_points
                                    else "no_data",
                                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics."
                                    if not show_points
                                    else "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                    "_n_weeks": data_points_count,
                                    "tooltip": "Average story points completed per week. Story points represent work complexity and effort. Higher values indicate faster delivery of larger work items."
                                    if (show_points and avg_points and avg_points > 0)
                                    else "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, forecasts use item counts instead."
                                    if not show_points
                                    else "No story points data available for the selected time period.",
                                    "weekly_values": list(
                                        statistics_df["completed_points"]
                                    )
                                    if show_points
                                    and avg_points
                                    and avg_points > 0
                                    and not statistics_df.empty
                                    else [],
                                    "trend_direction": points_trend.get("direction")
                                    if points_trend
                                    and show_points
                                    and avg_points
                                    and avg_points > 0
                                    else "stable",
                                    "trend_percent": points_trend.get("percent", 0)
                                    if points_trend
                                    and show_points
                                    and avg_points
                                    and avg_points > 0
                                    else 0,
                                }
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            create_professional_metric_card(
                                {
                                    "metric_name": "avg_item_size",
                                    "alternative_name": "Average Item Size",
                                    "value": _safe_divide(avg_points, avg_items)
                                    if (show_points and avg_points and avg_points > 0)
                                    else None,
                                    "unit": "points/item"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "subtitle": "Points per item"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "",
                                    "icon": "fa-weight-hanging",
                                    "color": "#17a2b8"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "#6c757d",
                                    "performance_tier_color": "green",
                                    "error_state": "success"
                                    if (show_points and avg_points and avg_points > 0)
                                    else "points_tracking_disabled"
                                    if not show_points
                                    else "no_data",
                                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics."
                                    if not show_points
                                    else "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                                    "_n_weeks": data_points_count,
                                    "tooltip": "Average story points per completed work item. Shows typical item complexity. Higher values mean larger items taking longer to complete. Use this to understand capacity: fewer large items or more small items per sprint."
                                    if (show_points and avg_points and avg_points > 0)
                                    else "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, forecasts use item counts instead."
                                    if not show_points
                                    else "No story points data available for the selected time period.",
                                    "weekly_values": [],
                                    "trend_direction": "stable",
                                    "trend_percent": 0,
                                }
                            )
                        ],
                        width=12,
                        md=6,
                        lg=4,
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def _get_forecast_history():
    """Get historical forecast data for trend visualization.

    Returns:
        Tuple of (dates, items_forecasts, points_forecasts) lists
    """
    try:
        from data.persistence import load_unified_project_data

        unified_data = load_unified_project_data()
        forecast_history = unified_data.get("forecast_history", [])

        # Extract data for plotting (last 10 data points)
        dates = []
        items_forecasts = []
        points_forecasts = []

        for entry in forecast_history[-10:]:
            dates.append(entry.get("date", ""))
            items_forecasts.append(entry.get("items_forecast_date", ""))
            points_forecasts.append(entry.get("points_forecast_date", ""))

        return dates, items_forecasts, points_forecasts
    except Exception:
        return [], [], []


def _create_forecast_section(
    pert_data, confidence_data, budget_data=None, show_points=True
):
    """Create forecasting section with multiple prediction methods.

    Args:
        pert_data: Dictionary with pert_time_items, pert_time_points, and last_date
        confidence_data: Dictionary with ci_50, ci_95, deadline_probability
        budget_data: Optional budget data for forecast alignment
        show_points: Whether to use points-based (True) or items-based (False) forecast
    """
    # Use last statistics date from pert_data (aligns with weekly data structure)
    # Falls back to datetime.now() only if last_date not available
    current_date = pert_data.get("last_date", datetime.now())

    # Calculate BOTH items-based and points-based forecasts
    items_forecast_days = pert_data.get("pert_time_items", 0)
    points_forecast_days = pert_data.get("pert_time_points", 0)

    # Only format date if there's actual forecast time (not 0)
    # Use YYYY-MM-DD format for region-neutral display
    items_pert_date = (
        (current_date + timedelta(days=items_forecast_days)).strftime("%Y-%m-%d")
        if items_forecast_days > 0
        else "No data"
    )
    points_pert_date = (
        (current_date + timedelta(days=points_forecast_days)).strftime("%Y-%m-%d")
        if points_forecast_days > 0
        else "No data"
    )

    # Use appropriate forecast metric for confidence intervals (matches report/burndown)
    forecast_metric = "story points" if show_points else "items"

    # Format confidence interval dates
    optimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_50", 0))
    ).strftime("%Y-%m-%d")
    pessimistic_date = (
        current_date + timedelta(days=confidence_data.get("ci_95", 0))
    ).strftime("%Y-%m-%d")

    # Get probabilities for both tracks
    deadline_prob_items = confidence_data.get("deadline_probability_items", 75)
    deadline_prob_points = confidence_data.get("deadline_probability_points")

    # Determine on-track probability tier (using primary metric)
    deadline_prob = (
        deadline_prob_points
        if (show_points and deadline_prob_points)
        else deadline_prob_items
    )
    if deadline_prob >= 70:
        prob_tier = "Healthy"
        prob_color = "#28a745"
    elif deadline_prob >= 40:
        prob_tier = "Warning"
        prob_color = "#ffc107"
    else:
        prob_tier = "At Risk"
        prob_color = "#dc3545"

    # Get tier info for items track
    items_prob_tier = (
        "Healthy"
        if deadline_prob_items >= 70
        else "Warning"
        if deadline_prob_items >= 40
        else "At Risk"
    )
    items_prob_color = (
        "#28a745"
        if deadline_prob_items >= 70
        else "#ffc107"
        if deadline_prob_items >= 40
        else "#dc3545"
    )

    # Create Enhanced Expected Completion card with BOTH forecasts
    expected_completion_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "Expected Completion",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text="Calculated using PERT three-point estimation: (Optimistic + 4×Most_Likely + Pessimistic) ÷ 6. "
                        "Shows forecasts based on both items and story points velocity. "
                        "This weighted average emphasizes the most likely scenario (4x weight) while accounting for best/worst cases from your historical velocity data. "
                        "Same method used in Burndown Chart and Report.",
                        id_suffix="metric-expected_completion",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    # Items-based forecast
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-tasks me-2",
                                        style={
                                            "color": COLOR_PALETTE["items"],
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Span(
                                        "Items-based",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="mb-1",
                            ),
                            html.Div(
                                items_pert_date,
                                className="h3 mb-3",
                                style={
                                    "fontWeight": "bold",
                                    "color": COLOR_PALETTE["items"],
                                },
                            ),
                        ],
                        className="text-center pb-2",
                        style={"borderBottom": "1px solid #e9ecef"}
                        if show_points
                        else {},
                    ),
                    # Points-based forecast (always show, with placeholder when disabled or no data)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-2",
                                        style={
                                            "color": COLOR_PALETTE["points"]
                                            if show_points
                                            and points_pert_date != "No data"
                                            else "#6c757d",
                                            "fontSize": "1rem",
                                        },
                                    ),
                                    html.Span(
                                        "Points-based",
                                        className="text-muted",
                                        style={"fontSize": "0.85rem"},
                                    ),
                                ],
                                className="mb-1 mt-3",
                            ),
                            html.Div(
                                # Case 1: Points tracking enabled with data
                                points_pert_date
                                if show_points and points_pert_date != "No data"
                                # Case 2: Points tracking disabled
                                else (
                                    [
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
                                    ]
                                    if not show_points
                                    # Case 3: Points tracking enabled but no data
                                    else [
                                        html.Div(
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
                                    ]
                                ),
                                className="h3 mb-0"
                                if show_points and points_pert_date != "No data"
                                else "",
                                style={
                                    "fontWeight": "bold",
                                    "color": COLOR_PALETTE["points"],
                                }
                                if show_points and points_pert_date != "No data"
                                else {},
                            ),
                        ],
                        className="text-center",
                    ),
                ],
                className="text-center py-3",
            ),
            dbc.CardFooter(
                html.Small(
                    "PERT forecast based on items and story points velocity"
                    if show_points
                    else "PERT forecast based on items velocity",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )

    # Enhanced Confidence Intervals card with bigger dates and better spacing
    confidence_intervals_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "Confidence Intervals",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text=f"Statistical probability ranges based on {forecast_metric} velocity variability. "
                        f"50%: 50th percentile (median) - the PERT forecast itself. "
                        f"95%: 95th percentile - conservative estimate with 1.65σ buffer (adds uncertainty for remaining work). "
                        f"Wider spread indicates higher velocity uncertainty. Calculated from your historical data variance.",
                        id_suffix="metric-confidence_intervals",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
            ),
            dbc.CardBody(
                [
                    # 50% Confidence (Optimistic)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-thumbs-up me-2",
                                        style={"color": "#28a745"},
                                    ),
                                    html.Span(
                                        "50% Confidence",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                                className="mb-2",
                            ),
                            html.Div(
                                optimistic_date,
                                className="h3 mb-3",
                                style={
                                    "color": "#28a745",
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                        className="text-center pb-3",
                        style={"borderBottom": "2px solid #e9ecef"},
                    ),
                    # 95% Confidence (Pessimistic)
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-shield-alt me-2",
                                        style={"color": "#dc3545"},
                                    ),
                                    html.Span(
                                        "95% Confidence",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                ],
                                className="mb-2 mt-3",
                            ),
                            html.Div(
                                pessimistic_date,
                                className="h3 mb-0",
                                style={
                                    "color": "#dc3545",
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                        className="text-center",
                    ),
                ],
                className="text-center py-3",
            ),
            dbc.CardFooter(
                html.Small(
                    "Statistical delivery probability ranges",
                    className="text-muted",
                ),
                className="text-center",
            ),
        ],
        className="metric-card mb-3 h-100",
    )

    # Enhanced On-Track Probability card with visual indicator
    on_track_card = dbc.Card(
        [
            dbc.CardHeader(
                [
                    html.Span(
                        "On-Track Probability",
                        className="metric-card-title",
                    ),
                    " ",
                    create_info_tooltip(
                        help_text="Statistical probability of meeting deadline using normal distribution. "
                        "Calculated via Z-score: (deadline_days - expected_days) / forecast_std_dev. "
                        "Based on how many standard deviations your deadline is from expected completion, adjusted for velocity consistency.",
                        id_suffix="metric-on_track_probability",
                        placement="top",
                        variant="dark",
                    ),
                ],
                className="d-flex align-items-center",
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
                                        className="d-flex justify-content-between align-items-center mb-2",
                                    ),
                                    html.Div(
                                        html.Div(
                                            f"{deadline_prob_items:.1f}%",
                                            className="progress-bar",
                                            style={
                                                "width": f"{min(deadline_prob_items, 100)}%",
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
                    # Points-based probability (always show, with placeholder when disabled)
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
                                                f"{deadline_prob_points:.0f}%",
                                                className="text-muted",
                                                style={
                                                    "fontSize": "0.85rem",
                                                    "fontWeight": "600",
                                                },
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
                                        className="d-flex justify-content-between align-items-center mb-2",
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
                            # Case 1: Points tracking disabled
                            if show_points
                            and deadline_prob_points is not None
                            and deadline_prob_points > 0
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
                                # Case 2: Points tracking enabled but no data
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
                ],
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

    # Create forecast history trend chart (if data available)
    history_dates, history_items, history_points = _get_forecast_history()

    forecast_trend_chart = None
    if history_dates and len(history_dates) >= 2:
        import plotly.graph_objects as go

        fig = go.Figure()

        # Add items-based forecast trend
        if history_items:
            fig.add_trace(
                go.Scatter(
                    x=history_dates,
                    y=history_items,
                    mode="lines+markers",
                    name="Items-based Forecast",
                    line=dict(color=COLOR_PALETTE["items"], width=3),
                    marker=dict(size=8, symbol="circle"),
                )
            )

        # Add points-based forecast trend (if available)
        if history_points and show_points:
            fig.add_trace(
                go.Scatter(
                    x=history_dates,
                    y=history_points,
                    mode="lines+markers",
                    name="Points-based Forecast",
                    line=dict(color=COLOR_PALETTE["points"], width=3, dash="dot"),
                    marker=dict(size=8, symbol="diamond"),
                )
            )

        fig.update_layout(
            title=dict(
                text="Forecast Evolution Over Time",
                font=dict(size=14, color="#495057"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(
                title="Calculation Date",
                showgrid=True,
                gridcolor="#e9ecef",
            ),
            yaxis=dict(
                title="Predicted Completion Date",
                showgrid=True,
                gridcolor="#e9ecef",
            ),
            hovermode="x unified",
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=300,
            margin=dict(l=60, r=40, t=50, b=60),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        from dash import dcc

        forecast_trend_chart = dbc.Card(
            dbc.CardBody(
                [
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False},
                        style={"height": "300px"},
                    ),
                    html.Div(
                        html.Small(
                            "Historical trend showing how forecast dates have changed as the project progresses",
                            className="text-muted",
                        ),
                        className="text-center mt-2",
                    ),
                ]
            ),
            className="metric-card mb-3",
        )

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-line me-2", style={"color": "#6610f2"}
                    ),
                    "Delivery Forecast",
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(expected_completion_card, width=12, md=4, className="mb-3"),
                    dbc.Col(
                        confidence_intervals_card, width=12, md=4, className="mb-3"
                    ),
                    dbc.Col(on_track_card, width=12, md=4, className="mb-3"),
                ]
            ),
            # Forecast vs Budget Alignment card (if budget configured)
            (
                dbc.Row(
                    [
                        dbc.Col(
                            create_forecast_alignment_card(
                                pert_time_items=pert_data.get("pert_time_items", 0),
                                pert_time_points=pert_data.get("pert_time_points"),
                                runway_weeks=budget_data.get("runway_weeks", 0),
                                show_points=show_points,
                                last_date=pert_data.get("last_date"),
                                card_id="forecast-alignment-card",
                            ),
                            width=12,
                            className="mb-3",
                        )
                    ]
                )
                if budget_data and budget_data.get("configured")
                else html.Div()
            ),
            # Forecast history trend chart (if available)
            forecast_trend_chart if forecast_trend_chart else html.Div(),
        ],
        className="mb-4",
    )


def _create_recent_activity_section(statistics_df, show_points=True):
    """Create compact recent performance section showing completed items clearly.

    Note: This section ALWAYS shows the last 4 weeks of data, regardless of
    the data_points_count slider. This provides a consistent "current status" view.
    Other dashboard sections respect the data_points_count filter.

    Args:
        statistics_df: DataFrame with statistics data
        show_points: Whether to show points-related metrics (default: True)
    """
    if statistics_df.empty:
        return html.Div()

    # ALWAYS use last 4 weeks for "Recent Completions" - fixed window
    recent_window = min(4, len(statistics_df))  # 4 weeks or less if data is limited
    recent_data = statistics_df.tail(recent_window)

    if recent_data.empty:
        return html.Div()

    # Calculate metrics for items
    total_items_completed = recent_data["completed_items"].sum()
    avg_items_weekly = recent_data["completed_items"].mean()
    items_sparkline_values = recent_data["completed_items"].tolist()

    # Calculate metrics for points
    has_points_data = "completed_points" in recent_data.columns
    total_points_completed = (
        recent_data["completed_points"].sum() if has_points_data else 0
    )
    avg_points_weekly = recent_data["completed_points"].mean() if has_points_data else 0
    points_sparkline_values = (
        recent_data["completed_points"].tolist() if has_points_data else [0, 0, 0, 0]
    )

    # Create metric cards for Recent Completions
    items_cards = [
        create_professional_metric_card(
            {
                "metric_name": "items_completed",
                "value": total_items_completed,
                "unit": "items",
                "_n_weeks": recent_window,
                "tooltip": f"Total items completed in the last {recent_window} weeks. This metric shows recent delivery throughput regardless of the data points filter.",
                "error_state": "success",
                "total_issue_count": 0,
            }
        ),
        create_professional_metric_card(
            {
                "metric_name": "items_per_week_avg",
                "alternative_name": "Average Items Per Week",
                "value": avg_items_weekly,
                "unit": "items/week",
                "_n_weeks": recent_window,
                "tooltip": f"Average items completed per week over the last {recent_window} weeks. Indicates current team velocity.",
                "error_state": "success",
                "total_issue_count": 0,
                "weekly_values": items_sparkline_values,
                "weekly_labels": [
                    f"W{i + 1}" for i in range(len(items_sparkline_values))
                ],
            },
            show_details_button=False,
        ),
    ]

    # Always show points cards - distinguish between disabled and no data
    if has_points_data and show_points and total_points_completed > 0:
        # Case 1: Points tracking enabled with data
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": total_points_completed,
                    "unit": "points",
                    "_n_weeks": recent_window,
                    "tooltip": f"Total story points completed in the last {recent_window} weeks. This metric shows recent delivery throughput in terms of story points.",
                    "error_state": "success",
                    "total_issue_count": 0,
                }
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": avg_points_weekly,
                    "unit": "points/week",
                    "_n_weeks": recent_window,
                    "tooltip": f"Average story points completed per week over the last {recent_window} weeks. Indicates current team velocity in terms of story points.",
                    "error_state": "success",
                    "total_issue_count": 0,
                    "weekly_values": points_sparkline_values,
                    "weekly_labels": [
                        f"W{i + 1}" for i in range(len(points_sparkline_values))
                    ],
                },
                show_details_button=False,
            ),
        ]
    elif not show_points:
        # Case 2: Points tracking disabled
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": None,
                    "unit": "",
                    "error_state": "points_tracking_disabled",
                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                    "tooltip": "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, use Items Completed for throughput tracking.",
                    "total_issue_count": 0,
                }
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": None,
                    "unit": "",
                    "error_state": "points_tracking_disabled",
                    "error_message": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
                    "tooltip": "Enable Points Tracking in Parameters panel and configure the points field in JIRA Configuration to view this metric. When disabled, use Items/Week Avg for velocity tracking.",
                    "total_issue_count": 0,
                }
            ),
        ]
    else:
        # Case 3: Points tracking enabled but no data (0 points)
        points_cards = [
            create_professional_metric_card(
                {
                    "metric_name": "points_completed",
                    "value": None,
                    "unit": "",
                    "error_state": "no_data",
                    "error_message": "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                    "tooltip": f"No story points completed in the last {recent_window} weeks. This may indicate that story points are not configured or no items with point estimates have been completed.",
                    "total_issue_count": 0,
                }
            ),
            create_professional_metric_card(
                {
                    "metric_name": "points_per_week_avg",
                    "alternative_name": "Average Points Per Week",
                    "value": None,
                    "unit": "",
                    "error_state": "no_data",
                    "error_message": "No story points data available. Configure story points field in Settings or complete items with point estimates.",
                    "tooltip": f"No story points data available for the last {recent_window} weeks. Configure story points field in Settings or complete items with point estimates.",
                    "total_issue_count": 0,
                }
            ),
        ]

    all_cards = items_cards + points_cards

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-check-circle me-2",
                        style={"color": COLOR_PALETTE["items"]},
                    ),
                    "Recent Completions",
                    html.Small(
                        f" (Last {recent_window} Weeks)", className="text-muted ms-2"
                    ),
                ],
                className="mb-3 mt-2",
            ),
            dbc.Row(
                [
                    dbc.Col(card, width=12, md=6, lg=3, className="mb-3")
                    for card in all_cards
                ]
            ),
        ],
        className="mb-4",
    )


def _create_quality_scope_section(statistics_df, settings):
    """Create quality and scope tracking section."""
    if statistics_df.empty:
        return html.Div()

    # Calculate scope metrics with time frame context
    scope_metrics = []

    if "created_items" in statistics_df.columns:
        total_created = statistics_df["created_items"].sum()
        total_completed = statistics_df["completed_items"].sum()
        scope_growth_rate = _safe_divide(total_created, total_completed) * 100

        # Get date range for context
        if "date" in statistics_df.columns and not statistics_df.empty:
            start_date = statistics_df["date"].min()
            end_date = statistics_df["date"].max()
            # Convert to datetime and handle NaT (Not a Time) values
            start_dt = pd.to_datetime(start_date, format="mixed", errors="coerce")
            end_dt = pd.to_datetime(end_date, format="mixed", errors="coerce")
            if pd.notna(start_dt) and pd.notna(end_dt):
                date_range = (
                    f"{start_dt.strftime('%Y-%m-%d')} - {end_dt.strftime('%Y-%m-%d')}"
                )
            else:
                date_range = "tracked period"
            weeks_count = len(statistics_df)
        else:
            date_range = "tracked period"
            weeks_count = len(statistics_df)

        scope_metrics.extend(
            [
                {
                    "label": "New Items Added",
                    "value": f"{total_created:,}",
                    "color": "#fd7e14",
                    "icon": "fa-plus-circle",
                    "tooltip": f"Total new work items added to project backlog during {date_range} ({weeks_count} weeks). This represents scope expansion - new features, bugs, or tasks discovered after project start. Monitor this to identify uncontrolled scope growth.",
                },
                {
                    "label": "Scope Growth Rate",
                    "value": f"{scope_growth_rate:.1f}%",
                    "color": "#6610f2",
                    "icon": "fa-chart-line",
                    "tooltip": f"Ratio of new items added vs items completed during {date_range}. Shows {total_created:,} new items added while {total_completed:,} completed. Healthy projects: <20% (balanced scope). Warning: 20-50% (scope creep). Critical: >50% (uncontrolled growth). Your value: {scope_growth_rate:.1f}%",
                },
            ]
        )

    # Calculate quality metrics
    if len(statistics_df) >= 4:
        # Velocity stability
        velocity_std = statistics_df["completed_items"].std()
        velocity_mean = statistics_df["completed_items"].mean()
        velocity_cv = _safe_divide(velocity_std, velocity_mean) * 100

        # Trend analysis - compare first half vs second half of filtered data
        mid_point = len(statistics_df) // 2
        recent_avg = statistics_df.iloc[mid_point:]["completed_items"].mean()
        older_avg = (
            statistics_df.iloc[:mid_point]["completed_items"].mean()
            if mid_point > 0
            else recent_avg
        )
        trend_stability = (
            abs(recent_avg - older_avg) / older_avg * 100 if older_avg > 0 else 0
        )

        quality_metrics = [
            {
                "label": "Velocity Consistency",
                "value": f"{max(0, 100 - velocity_cv):.0f}%",
                "color": "#28a745",
            },
            {
                "label": "Trend Stability",
                "value": f"{max(0, 100 - trend_stability):.0f}%",
                "color": "#17a2b8",
            },
        ]
    else:
        quality_metrics = [
            {"label": "Velocity Consistency", "value": "N/A", "color": "#6c757d"},
            {"label": "Trend Stability", "value": "N/A", "color": "#6c757d"},
        ]

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-shield-alt me-2", style={"color": "#6f42c1"}
                    ),
                    "Quality & Scope Tracking",
                ],
                className="mb-3 mt-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(
                                                className="fas fa-expand-arrows-alt me-2"
                                            ),
                                            "Scope Management",
                                            html.Span(
                                                " ", style={"marginRight": "8px"}
                                            ),
                                            create_info_tooltip(
                                                "Track scope changes and backlog growth. Shows ratio of new items added vs completed, helping identify scope creep early. Healthy projects maintain balance between scope growth and completion rate.",
                                                "scope-management-card",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    html.I(
                                                                        className=f"fas {metric.get('icon', 'fa-info-circle')} me-2",
                                                                        style={
                                                                            "color": metric[
                                                                                "color"
                                                                            ],
                                                                            "fontSize": "1.2rem",
                                                                        },
                                                                    ),
                                                                    metric["label"],
                                                                    html.Span(
                                                                        " ",
                                                                        style={
                                                                            "marginRight": "4px"
                                                                        },
                                                                    ),
                                                                    create_info_tooltip(
                                                                        metric.get(
                                                                            "tooltip",
                                                                            "",
                                                                        ),
                                                                        f"scope-{metric['label'].lower().replace(' ', '-')}",
                                                                    )
                                                                    if metric.get(
                                                                        "tooltip"
                                                                    )
                                                                    else None,
                                                                ],
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem",
                                                                    "display": "flex",
                                                                    "alignItems": "center",
                                                                    "justifyContent": "center",
                                                                },
                                                            ),
                                                            html.Div(
                                                                metric["value"],
                                                                className="h3 mb-0",
                                                                style={
                                                                    "fontWeight": "bold",
                                                                    "color": metric[
                                                                        "color"
                                                                    ],
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center p-2",
                                                    )
                                                    for metric in scope_metrics
                                                ]
                                            )
                                            if scope_metrics
                                            else html.Div(
                                                "No scope change data available",
                                                className="text-muted text-center p-3",
                                            )
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-chart-line me-1"
                                                ),
                                                "Tracks new items added vs completed • Monitors backlog growth over project lifecycle",
                                            ],
                                            className="text-muted",
                                        ),
                                        className="text-center bg-light border-top py-2",
                                    ),
                                ],
                                className="h-100 shadow-sm border-0 metric-card",
                            )
                        ],
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        [
                                            html.I(
                                                className="fas fa-check-circle me-2"
                                            ),
                                            "Quality Indicators",
                                            html.Span(
                                                " ", style={"marginRight": "8px"}
                                            ),
                                            create_info_tooltip(
                                                "Measures delivery predictability and consistency. High values (80%+) indicate stable, reliable team performance. Use these metrics to assess forecast accuracy and process maturity.",
                                                "quality-indicators-card",
                                            ),
                                        ],
                                        style={
                                            "display": "flex",
                                            "alignItems": "center",
                                        },
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.Div(
                                                        [
                                                            html.Div(
                                                                [
                                                                    metric["label"],
                                                                    html.Span(
                                                                        " ",
                                                                        style={
                                                                            "marginRight": "4px"
                                                                        },
                                                                    ),
                                                                    create_info_tooltip(
                                                                        "Measures how consistent velocity is week-over-week. Calculated as 100% - coefficient of variation. Higher values (80%+) indicate predictable delivery pace, making forecasts more reliable.",
                                                                        "quality-velocity-consistency",
                                                                    )
                                                                    if metric["label"]
                                                                    == "Velocity Consistency"
                                                                    else create_info_tooltip(
                                                                        "Measures velocity change between recent and historical periods. High values (80%+) indicate stable trends. Low values suggest significant velocity shifts requiring investigation.",
                                                                        "quality-trend-stability",
                                                                    )
                                                                    if metric["label"]
                                                                    == "Trend Stability"
                                                                    else None,
                                                                ],
                                                                className="text-muted",
                                                                style={
                                                                    "fontSize": "0.85rem",
                                                                    "display": "flex",
                                                                    "alignItems": "center",
                                                                    "justifyContent": "center",
                                                                },
                                                            ),
                                                            html.Div(
                                                                metric["value"],
                                                                className="h3 mb-0",
                                                                style={
                                                                    "fontWeight": "bold",
                                                                    "color": metric[
                                                                        "color"
                                                                    ],
                                                                },
                                                            ),
                                                        ],
                                                        className="text-center p-2",
                                                    )
                                                    for metric in quality_metrics
                                                ]
                                            )
                                        ]
                                    ),
                                    dbc.CardFooter(
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-gauge-high me-1"
                                                ),
                                                "Consistency + stability metrics • High values (80%+) enable reliable forecasting",
                                            ],
                                            className="text-muted",
                                        ),
                                        className="text-center bg-light border-top py-2",
                                    ),
                                ],
                                className="h-100 shadow-sm border-0 metric-card",
                            )
                        ],
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                ]
            ),
        ],
        className="mb-4",
    )


def _create_insights_section(
    statistics_df, settings, budget_data=None, pert_data=None, deadline=None
):
    """Create actionable insights section with comprehensive intelligence.

    Args:
        statistics_df: Filtered project statistics (by data_points_count in callback)
        settings: Project settings dictionary
        budget_data: Budget baseline vs actual data
        pert_data: PERT forecast data (optimistic, most likely, pessimistic)
        deadline: Project deadline date string

    Note: statistics_df is already filtered by data_points_count in the callback.
    For velocity comparison, we split the filtered data into two halves:
    - First half: "historical" baseline velocity
    - Second half: "recent" velocity trend

    IMPORTANT: Scope growth calculations here use the SAME filtered time window as the
    Scope Analysis tab. Both calculate from the same statistics_df filtered by the
    Data Points slider. The numbers should always match. If they don't match:
    - Check if viewing stale/cached data (refresh the page)
    - Verify both tabs are using the same data_points_count setting
    """
    insights = []

    if not statistics_df.empty:
        # Velocity insights - compare first half vs second half of filtered data
        mid_point = len(statistics_df) // 2
        if mid_point > 0:
            recent_velocity = statistics_df.iloc[mid_point:]["completed_items"].mean()
            historical_velocity = statistics_df.iloc[:mid_point][
                "completed_items"
            ].mean()
        else:
            # Fallback if dataset is too small to split
            recent_velocity = statistics_df["completed_items"].mean()
            historical_velocity = recent_velocity

        if historical_velocity > 0 and recent_velocity > historical_velocity * 1.1:
            insights.append(
                {
                    "severity": "success",
                    "message": f"Accelerating Delivery - Team velocity increased {((recent_velocity / historical_velocity - 1) * 100):.2f}% in recent weeks ({recent_velocity:.1f} vs {historical_velocity:.1f} items/week)",
                    "recommendation": "Consider taking on additional scope or bringing forward deliverables to capitalize on this momentum.",
                }
            )
        elif historical_velocity > 0 and recent_velocity < historical_velocity * 0.9:
            insights.append(
                {
                    "severity": "warning",
                    "message": f"Velocity Decline - Team velocity decreased {((1 - recent_velocity / historical_velocity) * 100):.2f}% recently ({recent_velocity:.1f} vs {historical_velocity:.1f} items/week)",
                    "recommendation": "Review team capacity, identify blockers, and assess scope complexity. Consider retrospectives to understand root causes.",
                }
            )

        # Budget insights (if budget data is available)
        if budget_data:
            import math

            utilization_pct = budget_data.get("utilization_percentage", 0)
            runway_weeks = budget_data.get("runway_weeks", 0)
            burn_rate = budget_data.get("burn_rate", 0)
            currency = budget_data.get("currency_symbol", "€")

            # Handle infinity runway (when burn rate is 0)
            if math.isinf(runway_weeks):
                insights.append(
                    {
                        "severity": "info",
                        "message": "Budget Status - No consumption detected",
                        "recommendation": "Budget tracking will begin once team velocity and costs are established. Ensure project parameters and team costs are configured correctly.",
                    }
                )
            elif utilization_pct > 90:
                insights.append(
                    {
                        "severity": "danger",
                        "message": f"Budget Critical - {utilization_pct:.2f}% consumed with only {runway_weeks:.2f} weeks remaining",
                        "recommendation": f"Immediate action required: Review remaining scope, consider budget increase, or reduce team costs. Current burn rate: {currency}{burn_rate:,.0f}/week.",
                    }
                )
            elif utilization_pct > 75:
                insights.append(
                    {
                        "severity": "warning",
                        "message": f"Budget Alert - {utilization_pct:.2f}% consumed, approaching budget limits",
                        "recommendation": f"Monitor closely: {runway_weeks:.2f} weeks of runway remaining at current burn rate ({currency}{burn_rate:,.2f}/week). Consider optimizing team costs or adjusting scope.",
                    }
                )
            elif runway_weeks < 8 and runway_weeks > 0:
                insights.append(
                    {
                        "severity": "warning",
                        "message": f"Limited Runway - Only {runway_weeks:.2f} weeks of budget remaining",
                        "recommendation": f"Plan for project completion or budget extension. Current burn rate: {currency}{burn_rate:,.0f}/week. Review if remaining scope aligns with available runway.",
                    }
                )
            elif utilization_pct < 50 and runway_weeks > 12:
                insights.append(
                    {
                        "severity": "success",
                        "message": f"Healthy Budget - {utilization_pct:.2f}% consumed with {runway_weeks:.2f} weeks of runway",
                        "recommendation": f"Budget on track. Continue monitoring burn rate ({currency}{burn_rate:,.0f}/week) and adjust forecasts as scope evolves.",
                    }
                )

        # Scope change insights
        if "created_items" in statistics_df.columns:
            scope_growth = statistics_df["created_items"].sum()
            scope_completion = statistics_df["completed_items"].sum()

            # Calculate time window info for clarity
            time_window_desc = ""
            if len(statistics_df) > 0:
                weeks_count = len(statistics_df)
                time_window_desc = f" over {weeks_count} weeks"

            if scope_growth > scope_completion * 0.2:
                # Calculate ratio for clarity
                ratio = scope_growth / scope_completion if scope_completion > 0 else 0
                insights.append(
                    {
                        "severity": "warning",
                        "message": f"High Scope Growth{time_window_desc} - For every completed item, {ratio:.2f} new items are being created ({scope_growth} created vs {scope_completion} completed)",
                        "recommendation": "Consider scope prioritization and implement change management processes. Assess if continuous scope growth impacts delivery predictability.",
                    }
                )
            elif scope_growth > 0:
                ratio = scope_growth / scope_completion if scope_completion > 0 else 0
                insights.append(
                    {
                        "severity": "info",
                        "message": f"Active Scope Management{time_window_desc} - Moderate scope growth with {ratio:.2f} new items created per completed item ({scope_growth} created vs {scope_completion} completed)",
                        "recommendation": "Continue monitoring scope changes and maintaining stakeholder feedback loops to ensure alignment.",
                    }
                )

        # Consistency insights
        velocity_cv = (
            (
                statistics_df["completed_items"].std()
                / statistics_df["completed_items"].mean()
                * 100
            )
            if statistics_df["completed_items"].mean() > 0
            else 0
        )

        if velocity_cv < 20:
            insights.append(
                {
                    "severity": "success",
                    "message": f"Predictable Delivery - Low velocity variation ({velocity_cv:.2f}%) indicates predictable delivery rhythm",
                    "recommendation": "Maintain current practices and leverage this predictability for better sprint planning and stakeholder commitments.",
                }
            )
        elif velocity_cv > 50:
            insights.append(
                {
                    "severity": "warning",
                    "message": f"Inconsistent Velocity - High velocity variation ({velocity_cv:.2f}%) suggests unpredictable delivery",
                    "recommendation": "Investigate root causes: story sizing accuracy, blockers, team availability, or external dependencies. Consider establishing sprint commitments discipline.",
                }
            )

        # Throughput efficiency insights - compare first half vs second half of filtered data
        if len(statistics_df) >= 8:
            mid_point = len(statistics_df) // 2
            recent_items = statistics_df.iloc[mid_point:]["completed_items"].sum()
            prev_items = statistics_df.iloc[:mid_point]["completed_items"].sum()

            if prev_items > 0 and recent_items > prev_items * 1.2:
                insights.append(
                    {
                        "severity": "success",
                        "message": f"Increasing Throughput - Recent period delivered {recent_items} items, exceeding previous period by {((recent_items / prev_items - 1) * 100):.2f}% ({recent_items} vs {prev_items} items)",
                        "recommendation": "Analyze what's working well and consider scaling successful practices across the team or to other projects.",
                    }
                )

    # === NEW INSIGHTS: Forecast vs Reality Alignment ===
    if pert_data and deadline:
        from datetime import datetime
        import pandas as pd

        try:
            # Parse deadline
            deadline_date = pd.to_datetime(deadline)
            if not pd.isna(deadline_date):
                current_date = datetime.now()
                days_to_deadline = max(0, (deadline_date - current_date).days)

                pert_most_likely_days = pert_data.get("pert_time_items", 0)
                pert_optimistic_days = pert_data.get("pert_optimistic_days", 0)
                pert_pessimistic_days = pert_data.get("pert_pessimistic_days", 0)

                # A3: Deadline Risk Alert (CRITICAL)
                if days_to_deadline > 0 and pert_most_likely_days > days_to_deadline:
                    days_over = pert_most_likely_days - days_to_deadline
                    weeks_over = days_over / 7.0
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Deadline At Risk - Current forecast shows completion {days_over:.2f} days ({weeks_over:.2f} weeks) after deadline",
                            "recommendation": f"Escalate immediately. Options: (1) Descope to MVP and reduce scope by {(days_over / pert_most_likely_days * 100):.2f}%, (2) Request deadline extension, (3) Increase team capacity (with ramp-up risk). Review deadline feasibility with stakeholders.",
                        }
                    )

                # G2: Optimistic Scenario Misses Deadline (CRITICAL)
                elif (
                    days_to_deadline > 0
                    and pert_optimistic_days > 0
                    and pert_optimistic_days > days_to_deadline
                ):
                    days_over = pert_optimistic_days - days_to_deadline
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Deadline Unachievable - Even best-case scenario completes {days_over:.2f} days after deadline",
                            "recommendation": "Immediate action required. Deadline is mathematically unattainable without dramatic changes: (1) Aggressively descope to critical MVP features only, (2) Negotiate deadline extension immediately, (3) Consider increasing team size (requires ramp-up time). No realistic path exists with current parameters.",
                        }
                    )

                # G1: Pessimistic Scenario Still Meets Deadline (SUCCESS)
                elif (
                    days_to_deadline > 0
                    and pert_pessimistic_days > 0
                    and pert_pessimistic_days < days_to_deadline
                ):
                    buffer_days = days_to_deadline - pert_pessimistic_days
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"High Deadline Confidence - Even pessimistic forecast completes {buffer_days:.2f} days before deadline ({(buffer_days / days_to_deadline * 100):.2f}% buffer)",
                            "recommendation": "Strong position. Consider: (1) Committing to stretch goals or additional features, (2) Adding low-risk quality enhancements, (3) Building buffer for technical debt or documentation. Use confidence to negotiate valuable scope additions.",
                        }
                    )

                # A1: Forecast Slippage Alert (HIGH)
                if budget_data and pert_most_likely_days > 0:
                    baseline_end = budget_data.get("baseline", {}).get(
                        "allocated_end_date"
                    )
                    if baseline_end:
                        baseline_date = pd.to_datetime(baseline_end)
                        forecast_date = current_date + pd.Timedelta(
                            days=pert_most_likely_days
                        )
                        slippage_days = (forecast_date - baseline_date).days

                        if slippage_days > 14:  # >2 weeks slippage
                            slippage_weeks = slippage_days / 7.0
                            insights.append(
                                {
                                    "severity": "warning",
                                    "message": f"Forecast Slippage - Project expected to complete {slippage_weeks:.2f} weeks after planned end date",
                                    "recommendation": f"Re-evaluate scope priorities and adjust timeline expectations. Current velocity suggests {(pert_most_likely_days / 7.0):.2f} weeks needed vs {budget_data.get('baseline', {}).get('time_allocated_weeks', 0):.2f} weeks allocated. Consider descoping {(slippage_days / pert_most_likely_days * 100):.2f}% of remaining work or extending timeline.",
                                }
                            )

                # A2: Forecast Confidence Warning (MEDIUM)
                if (
                    pert_optimistic_days > 0
                    and pert_pessimistic_days > 0
                    and (pert_pessimistic_days - pert_optimistic_days) / 7.0 > 4
                ):
                    range_weeks = (pert_pessimistic_days - pert_optimistic_days) / 7.0
                    insights.append(
                        {
                            "severity": "warning",
                            "message": f"Low Forecast Confidence - Wide prediction range (±{range_weeks:.2f} weeks) indicates delivery uncertainty",
                            "recommendation": "Improve predictability by: (1) Stabilizing team capacity and reducing interruptions, (2) Breaking down large stories into smaller chunks, (3) Reducing work-in-progress limits, (4) Addressing recurring blockers. Use Monte Carlo projections for stakeholder communication to set realistic expectations.",
                        }
                    )
        except Exception:
            # Silently skip if date parsing fails
            pass

    # === NEW INSIGHTS: Budget vs Forecast Misalignment ===
    if pert_data and budget_data:
        import math

        try:
            pert_forecast_weeks = (
                pert_data.get("pert_time_items", 0) / 7.0
                if pert_data.get("pert_time_items")
                else 0
            )
            pert_pessimistic_weeks = (
                pert_data.get("pert_pessimistic_days", 0) / 7.0
                if pert_data.get("pert_pessimistic_days")
                else 0
            )
            runway_weeks = budget_data.get("runway_weeks", 0)
            currency = budget_data.get("currency_symbol", "€")

            if not math.isinf(runway_weeks) and pert_forecast_weeks > 0:
                # B1: Runway Shorter Than Forecast (CRITICAL)
                if runway_weeks > 0 and runway_weeks < pert_forecast_weeks - 2:
                    shortfall_weeks = pert_forecast_weeks - runway_weeks
                    shortfall_pct = (shortfall_weeks / pert_forecast_weeks) * 100
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Budget Exhaustion Before Completion - Budget runs out {shortfall_weeks:.2f} weeks before forecast completion",
                            "recommendation": f"Critical misalignment detected. Forecast requires {pert_forecast_weeks:.2f} weeks but only {runway_weeks:.2f} weeks of budget remain. Required actions: (1) Reduce burn rate by scaling down team, (2) Secure additional budget ({shortfall_pct:.2f}% increase needed), or (3) Aggressively descope to fit runway.",
                        }
                    )

                # B3: Budget Surplus Opportunity (LOW)
                elif (
                    pert_pessimistic_weeks > 0
                    and runway_weeks > pert_pessimistic_weeks + 4
                ):
                    surplus_weeks = runway_weeks - pert_pessimistic_weeks
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"Budget Surplus Likely - Project forecast suggests {surplus_weeks:.2f} weeks of unspent budget",
                            "recommendation": "Consider value-adding opportunities: (1) Adding high-priority backlog items within scope, (2) Investing in technical debt reduction or quality improvements, (3) Enhancing UX/documentation, or (4) Reallocating surplus to other initiatives. Confirm assumptions and opportunities with stakeholders.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Velocity & Capacity Patterns ===
    if not statistics_df.empty:
        try:
            # C1: Velocity Plateau Alert (MEDIUM)
            mid_point = len(statistics_df) // 2
            if mid_point > 2:
                recent_velocity = statistics_df.iloc[mid_point:][
                    "completed_items"
                ].mean()
                historical_velocity = statistics_df.iloc[:mid_point][
                    "completed_items"
                ].mean()

                # Check if stagnant AND below baseline
                if (
                    budget_data
                    and historical_velocity > 0
                    and abs(recent_velocity - historical_velocity)
                    < historical_velocity * 0.05
                ):
                    baseline_velocity = budget_data.get("baseline", {}).get(
                        "assumed_baseline_velocity", 0
                    )
                    if (
                        baseline_velocity > 0
                        and recent_velocity < baseline_velocity * 0.5
                    ):
                        pct_below = (1 - recent_velocity / baseline_velocity) * 100
                        insights.append(
                            {
                                "severity": "warning",
                                "message": f"Stagnant Velocity - Team throughput unchanged for {len(statistics_df)} weeks at {pct_below:.2f}% below baseline",
                                "recommendation": "Investigate capacity constraints: Are we hitting team size limits, facing consistent blockers, or underutilizing available capacity? Review sprint retrospectives for patterns and consider process improvements or removing impediments.",
                            }
                        )
        except Exception:
            pass

    # === NEW INSIGHTS: Scope & Requirements Management ===
    if not statistics_df.empty and "created_items" in statistics_df.columns:
        try:
            # D1: Scope Creep Acceleration (HIGH)
            if len(statistics_df) >= 4:
                recent_created = statistics_df.tail(4)["created_items"].sum()
                recent_completed = statistics_df.tail(4)["completed_items"].sum()

                # Check if sustained pattern
                weeks_over = sum(
                    1
                    for _, row in statistics_df.tail(4).iterrows()
                    if row["created_items"] > row["completed_items"]
                )

                if recent_created > recent_completed and weeks_over >= 3:
                    excess_pct = (
                        (recent_created - recent_completed) / recent_completed * 100
                        if recent_completed > 0
                        else 0
                    )
                    insights.append(
                        {
                            "severity": "warning",
                            "message": f"Accelerating Scope Creep - New items added faster than completion rate for {weeks_over} consecutive weeks (backlog growing by {excess_pct:.2f}%)",
                            "recommendation": "Implement change control immediately: (1) Temporary freeze on new items to stabilize backlog, (2) Require stakeholder approval for all additions, (3) Establish scope change budget/buffer in forecast, (4) Review and prioritize existing backlog before accepting new work.",
                        }
                    )

            # D2: Backlog Burn-Down Accelerating (SUCCESS)
            if len(statistics_df) >= 4:
                recent_net = (
                    statistics_df.tail(4)["completed_items"].sum()
                    - statistics_df.tail(4)["created_items"].sum()
                )
                if recent_net > 0:
                    weeks_over = sum(
                        1
                        for _, row in statistics_df.tail(4).iterrows()
                        if row["completed_items"] > row["created_items"]
                    )
                    if weeks_over >= 4:
                        insights.append(
                            {
                                "severity": "success",
                                "message": f"Backlog Burn-Down Accelerating - Completing items faster than new additions for {weeks_over} consecutive weeks",
                                "recommendation": "Leverage momentum to maximize value delivery: (1) Consider accepting additional valuable scope from backlog, (2) Advance future roadmap items to capitalize on team productivity, or (3) Use capacity for quality/UX enhancements. Coordinate with product stakeholders.",
                            }
                        )

            # D3: Zero New Items Warning (INFO)
            if len(statistics_df) >= 3:
                recent_created = statistics_df.tail(3)["created_items"].sum()
                remaining = (
                    statistics_df.tail(1)["remaining_items"].iloc[0]
                    if len(statistics_df) > 0
                    and "remaining_items" in statistics_df.columns
                    else 0
                )

                if recent_created == 0 and remaining > 0:
                    insights.append(
                        {
                            "severity": "info",
                            "message": "No New Requirements - Zero items added for last 3 weeks",
                            "recommendation": "Verify backlog health: (1) Is product backlog refinement happening regularly? (2) Are stakeholders engaged and providing feedback? (3) Is this an intentional scope freeze for delivery focus? Ensure pipeline exists for future work and stakeholder feedback loops remain active.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Multi-Metric Correlations ===
    if not statistics_df.empty and budget_data:
        try:
            velocity_cv = (
                (
                    statistics_df["completed_items"].std()
                    / statistics_df["completed_items"].mean()
                    * 100
                )
                if statistics_df["completed_items"].mean() > 0
                else 0
            )

            # H1: High Variance + Scope Growth (CRITICAL)
            if (
                velocity_cv > 40
                and "created_items" in statistics_df.columns
                and statistics_df["created_items"].sum()
                > statistics_df["completed_items"].sum() * 0.2
            ):
                insights.append(
                    {
                        "severity": "danger",
                        "message": f"Unstable Delivery + Scope Creep - High velocity variation ({velocity_cv:.2f}%) combined with increasing scope creates critical delivery risk",
                        "recommendation": "Dual intervention required: (1) Stabilize velocity through consistent team capacity, better story sizing, and reduced context switching, (2) Implement strict change control to prevent scope additions until delivery stabilizes. Consider freezing new features until predictability improves.",
                    }
                )

            # H2: Low Runway + High Forecast Uncertainty (CRITICAL)
            if pert_data:
                import math

                runway_weeks = budget_data.get("runway_weeks", 0)
                pert_optimistic_days = pert_data.get("pert_optimistic_days", 0)
                pert_pessimistic_days = pert_data.get("pert_pessimistic_days", 0)

                if (
                    not math.isinf(runway_weeks)
                    and runway_weeks > 0
                    and runway_weeks < 6
                    and pert_optimistic_days > 0
                    and pert_pessimistic_days > 0
                    and (pert_pessimistic_days - pert_optimistic_days) / 7.0 > 4
                ):
                    insights.append(
                        {
                            "severity": "danger",
                            "message": f"Budget Risk + Forecast Uncertainty - Limited budget ({runway_weeks:.2f} weeks) combined with unpredictable delivery creates critical planning risk",
                            "recommendation": "Urgently stabilize project: (1) Define and commit to minimum viable scope that fits budget, (2) Increase forecast accuracy by breaking stories into smaller pieces and reducing WIP, (3) Secure budget contingency or prepare for partial delivery. Risk of budget overrun or incomplete delivery is high.",
                        }
                    )

            # H3: Accelerating Velocity + Budget Surplus (OPPORTUNITY)
            mid_point = len(statistics_df) // 2
            if mid_point > 0 and pert_data:
                import math

                recent_velocity = statistics_df.iloc[mid_point:][
                    "completed_items"
                ].mean()
                historical_velocity = statistics_df.iloc[:mid_point][
                    "completed_items"
                ].mean()
                runway_weeks = budget_data.get("runway_weeks", 0)
                pert_forecast_weeks = (
                    pert_data.get("pert_time_items", 0) / 7.0
                    if pert_data.get("pert_time_items")
                    else 0
                )

                if (
                    historical_velocity > 0
                    and recent_velocity > historical_velocity * 1.15
                    and not math.isinf(runway_weeks)
                    and runway_weeks > 0
                    and pert_forecast_weeks > 0
                    and runway_weeks > pert_forecast_weeks + 3
                ):
                    velocity_increase = (
                        recent_velocity / historical_velocity - 1
                    ) * 100
                    surplus_weeks = runway_weeks - pert_forecast_weeks
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"Performance Surplus - Team accelerating ({velocity_increase:.2f}% increase) while budget has {surplus_weeks:.2f} weeks headroom",
                            "recommendation": "Opportunity to maximize value delivery: (1) Bring forward high-value roadmap items from future releases, (2) Invest in technical debt reduction or architecture improvements, (3) Enhance product quality, UX, or documentation. Coordinate with stakeholders to capitalize on this favorable position.",
                        }
                    )
        except Exception:
            pass

    # === NEW INSIGHTS: Baseline Deviation Patterns ===
    if not statistics_df.empty and budget_data:
        try:
            actual_velocity = statistics_df["completed_items"].mean()
            baseline_velocity = budget_data.get("baseline", {}).get(
                "assumed_baseline_velocity", 0
            )

            # F1: Baseline Velocity Miss (HIGH)
            if (
                baseline_velocity > 0
                and actual_velocity < baseline_velocity * 0.8
                and len(statistics_df) >= 4
            ):
                pct_below = (1 - actual_velocity / baseline_velocity) * 100
                insights.append(
                    {
                        "severity": "warning",
                        "message": f"Underperforming Baseline - Team velocity {pct_below:.2f}% below planned baseline ({actual_velocity:.2f} vs {baseline_velocity:.2f} items/week) for {len(statistics_df)} weeks",
                        "recommendation": "Baseline assumptions appear incorrect. Actions: (1) Adjust baseline expectations to realistic levels and re-plan timeline, (2) Investigate root causes of underperformance (team capacity, story complexity, blockers), (3) Reset stakeholder expectations with revised forecasts. Document lessons learned for future planning.",
                    }
                )

            # F2: Cost Per Item Deviation (MEDIUM)
            cost_variance_pct = budget_data.get("variance", {}).get(
                "cost_per_item_variance_pct", 0
            )
            if abs(cost_variance_pct) > 25:
                if cost_variance_pct > 0:
                    insights.append(
                        {
                            "severity": "warning",
                            "message": f"Cost Efficiency Degraded - Items costing {cost_variance_pct:.2f}% more than baseline assumption",
                            "recommendation": "Stories more complex than expected or velocity lower than planned. Review: (1) Are stories properly sized and estimated? (2) Is team capacity lower than assumed? (3) Are there hidden complexities or technical debt? Consider adjusting cost assumptions for future planning.",
                        }
                    )
                else:
                    insights.append(
                        {
                            "severity": "success",
                            "message": f"Cost Efficiency Improved - Items costing {abs(cost_variance_pct):.2f}% less than baseline assumption",
                            "recommendation": "Team more efficient than planned, possibly due to higher velocity or simpler stories. Consider: (1) Taking on additional valuable scope within budget, (2) Reducing future budget projections if sustainable, (3) Documenting efficiency drivers for replication. Verify this is sustainable before committing to expanded scope.",
                        }
                    )
        except Exception:
            pass

    # Sort insights by severity priority
    severity_priority = {"danger": 0, "warning": 1, "info": 2, "success": 3}
    insights.sort(key=lambda x: severity_priority.get(x["severity"], 2))

    # Limit to top 10 most important insights to avoid overwhelming users
    insights = insights[:10]

    if not insights:
        insights.append(
            {
                "severity": "success",
                "message": "Stable Performance - Project metrics are within normal ranges, no immediate concerns detected",
                "recommendation": "Continue current practices and monitor for changes in upcoming weeks. Consider documenting what's working well.",
            }
        )

    # Map severity to configuration (matching Quality Insights style)
    def get_severity_config(severity: str):
        severity_configs = {
            "danger": {
                "icon": "fa-exclamation-triangle",
                "color": "danger",
                "badge_text": "Critical",
            },
            "warning": {
                "icon": "fa-exclamation-circle",
                "color": "warning",
                "badge_text": "High",
            },
            "info": {
                "icon": "fa-info-circle",
                "color": "info",
                "badge_text": "Medium",
            },
            "success": {
                "icon": "fa-check-circle",
                "color": "success",
                "badge_text": "Low",
            },
        }
        return severity_configs.get(severity, severity_configs["info"])

    # Create insight items with expandable details (matching Quality Insights structure)
    insight_items = []
    for idx, insight in enumerate(insights):
        severity_config = get_severity_config(insight["severity"])
        collapse_id = f"actionable-insight-collapse-{idx}"

        insight_item = dbc.Card(
            [
                dbc.CardHeader(
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.I(
                                        className=f"fas {severity_config['icon']} me-2"
                                    ),
                                    html.Span(insight["message"]),
                                ],
                                width=10,
                            ),
                            dbc.Col(
                                [
                                    dbc.Badge(
                                        severity_config["badge_text"],
                                        color=severity_config["color"],
                                        className="me-2",
                                    ),
                                    dbc.Button(
                                        html.I(className="fas fa-chevron-down"),
                                        id=f"actionable-insight-toggle-{idx}",
                                        color="link",
                                        size="sm",
                                        className="p-0",
                                    ),
                                ],
                                width=2,
                                className="text-end",
                            ),
                        ],
                        align="center",
                    ),
                    className=f"bg-{severity_config['color']} bg-opacity-10 border-{severity_config['color']}",
                    style={"cursor": "pointer"},
                    id=f"actionable-insight-header-{idx}",
                ),
                dbc.Collapse(
                    dbc.CardBody(
                        [
                            html.H6("Recommendation:", className="fw-bold mb-2"),
                            html.P(
                                insight["recommendation"],
                                className="mb-0",
                            ),
                        ]
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ],
            className="mb-2",
        )
        insight_items.append(insight_item)

    return html.Div(
        [
            html.H5(
                [
                    html.I(
                        className="fas fa-lightbulb me-2", style={"color": "#ffc107"}
                    ),
                    "Actionable Insights",
                ],
                className="mb-3 mt-2",
            ),
            dbc.Card(
                dbc.CardBody(html.Div(insight_items)),
                className="mb-4",
            ),
        ],
    )


#######################################################################
# MAIN DASHBOARD FUNCTION
#######################################################################


def create_comprehensive_dashboard(
    statistics_df,
    statistics_df_unfiltered,
    pert_time_items,
    pert_time_points,
    avg_weekly_items,
    avg_weekly_points,
    med_weekly_items,
    med_weekly_points,
    days_to_deadline,
    total_items,
    total_points,
    deadline_str,
    show_points=True,
    additional_context=None,
    data_points_count=None,
):
    """
    Create a comprehensive project dashboard with all available metrics.

    This dashboard provides:
    - Executive summary with project health scoring
    - Throughput analytics with trend analysis
    - Multi-method forecasting with confidence intervals
    - Actionable insights and recommendations

    Args:
        statistics_df: DataFrame with filtered project statistics (respects data_points_count slider)
        statistics_df_unfiltered: DataFrame with ALL project statistics (for Recent Completions)
        pert_time_items: PERT forecast time for items
        pert_time_points: PERT forecast time for points
        avg_weekly_items: Average weekly items completed
        avg_weekly_points: Average weekly points completed
        med_weekly_items: Median weekly items completed
        med_weekly_points: Median weekly points completed
        days_to_deadline: Days until project deadline
        total_items: Total items in project scope
        total_points: Total points in project scope
        deadline_str: Deadline date string
        show_points: Whether to show points-based metrics
        additional_context: Optional additional metrics and context

    Returns:
        html.Div: Complete dashboard layout
    """
    # CRITICAL FIX: Dashboard shows CURRENT remaining work, not windowed scope
    # The Data Points slider filters statistics for forecasting, but remaining is always current
    from data.persistence import load_unified_project_data

    unified_data = load_unified_project_data()
    project_scope = unified_data.get("project_scope", {})

    # Use CURRENT remaining values directly - slider doesn't affect remaining work
    total_items = project_scope.get("remaining_items", 0)
    total_points = project_scope.get("remaining_total_points", 0)

    # Prepare forecast data
    # Use points-based forecast when available, otherwise use items-based
    forecast_days = (
        pert_time_points if (show_points and pert_time_points) else pert_time_items
    )

    import logging

    logger = logging.getLogger(__name__)

    logger.info("[DASHBOARD] Using current remaining work (independent of slider):")
    logger.info(
        f"  data_points_count={data_points_count or 'all'}, "
        f"total_items={total_items}, total_points={total_points}"
    )

    logger.info(
        f"[DASHBOARD PERT] Input PERT values: pert_time_items={pert_time_items}, "
        f"pert_time_points={pert_time_points}, show_points={show_points}, "
        f"chosen forecast_days={forecast_days}"
    )

    schedule_variance_calc = (
        (
            days_to_deadline - forecast_days
        )  # Positive = ahead of schedule (buffer), negative = behind
        if (forecast_days and days_to_deadline)
        else 0
    )
    logger.info(
        f"[APP SCHEDULE] forecast_days={forecast_days}, days_to_deadline={days_to_deadline}, schedule_variance={schedule_variance_calc}"
    )

    # Extract last statistics date for forecast starting point (aligns with weekly data structure)
    # CRITICAL: Statistics are weekly-based (Mondays), so use last Monday data point not datetime.now()
    # Use iloc[-1] (not max()) to ensure we get the LAST date in the sorted/filtered dataframe
    # This matches report_generator.py logic exactly (df_windowed["date"].iloc[-1])
    last_date = (
        statistics_df["date"].iloc[-1]
        if not statistics_df.empty and "date" in statistics_df.columns
        else datetime.now()
    )

    logger.info(
        f"[DASHBOARD FORECAST] last_date={last_date.strftime('%Y-%m-%d') if hasattr(last_date, 'strftime') else last_date}, "
        f"forecast_days={forecast_days}, statistics_rows={len(statistics_df)}, "
        f"completion_date={(last_date + timedelta(days=forecast_days)).strftime('%Y-%m-%d') if forecast_days else 'None'}"
    )

    forecast_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "velocity_cv": 25,  # Default coefficient of variation
        "schedule_variance_days": schedule_variance_calc,
        "last_date": last_date,  # Starting point for forecast calculations
        "completion_date": (last_date + timedelta(days=forecast_days)).strftime(
            "%Y-%m-%d"
        )
        if forecast_days
        else None,
    }

    # Calculate velocity statistics for confidence intervals
    velocity_std = 0
    velocity_mean = 0

    if not statistics_df.empty and len(statistics_df) >= 4:
        # Use population std (ddof=0) to match report calculation
        velocity_std = statistics_df["completed_items"].std(ddof=0)
        velocity_mean = statistics_df["completed_items"].mean()
        if velocity_mean > 0:
            forecast_data["velocity_cv"] = (velocity_std / velocity_mean) * 100
            logger.info(
                f"[HEALTH DEBUG] Velocity CV calculation: std={velocity_std:.2f}, "
                f"mean={velocity_mean:.2f}, CV={forecast_data['velocity_cv']:.2f}%, "
                f"statistics_rows={len(statistics_df)}"
            )

    # Calculate statistically-based confidence intervals
    # Using Monte Carlo-inspired approach: forecast uncertainty grows with remaining work
    # Standard error of completion time ≈ (remaining / velocity) * (velocity_std / velocity_mean)
    # This accounts for: more remaining work = more uncertainty, higher velocity variance = more uncertainty

    # Use points-based forecast when available (matches report and burndown chart)
    forecast_days = pert_time_points if pert_time_points else pert_time_items

    # Calculate deadline probability for BOTH items and points tracks
    def calculate_deadline_probability(
        forecast, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    ):
        """Calculate deadline probability for a given forecast."""
        if not forecast or velocity_mean <= 0 or velocity_std <= 0:
            return 75 if (forecast or 0) <= (days_to_deadline or 0) else 25

        cv_ratio = velocity_std / velocity_mean
        weeks_remaining = max(1, forecast / 7)
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5
        forecast_std_days = forecast * cv_ratio * uncertainty_factor

        if days_to_deadline > 0 and forecast_std_days > 0:
            z_score = (days_to_deadline - forecast) / forecast_std_days
            return 100 / (1 + 2.718 ** (-1.7 * z_score))
        else:
            return 75 if forecast <= days_to_deadline else 25

    weeks_observed = len(statistics_df) if not statistics_df.empty else 1
    deadline_probability_items = calculate_deadline_probability(
        pert_time_items, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    )
    deadline_probability_points = (
        calculate_deadline_probability(
            pert_time_points,
            days_to_deadline,
            velocity_mean,
            velocity_std,
            weeks_observed,
        )
        if pert_time_points
        else None
    )

    if forecast_days and velocity_mean > 0 and velocity_std > 0:
        # Coefficient of variation as a ratio (not percentage)
        cv_ratio = velocity_std / velocity_mean

        # Forecast standard deviation: uncertainty scales with forecast duration and velocity variability
        # Using: σ_forecast ≈ forecast_days * CV * sqrt(weeks_remaining / weeks_observed)
        weeks_remaining = max(1, forecast_days / 7)  # Convert days to weeks
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5

        forecast_std_days = forecast_days * cv_ratio * uncertainty_factor

        # Confidence intervals using z-scores:
        # 50% CI: ±0.67σ (but we show median which equals PERT estimate)
        # 95% CI: +1.65σ (one-tailed, conservative estimate)
        ci_50_days = forecast_days  # Median = PERT estimate (50th percentile)
        ci_95_days = forecast_days + (1.65 * forecast_std_days)  # 95th percentile

        # Use combined probability (average when both available, or single track)
        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )
    else:
        # Fallback for insufficient data: use conservative fixed offsets
        ci_50_days = forecast_days if forecast_days else 0
        ci_95_days = (forecast_days + 14) if forecast_days else 0
        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )

    # Ensure deadline_probability is not None before using in min()
    final_deadline_prob = (
        deadline_probability if deadline_probability is not None else 75
    )

    confidence_data = {
        "ci_50": max(0, ci_50_days),
        "ci_80": pert_time_items if pert_time_items else 0,  # Keep for compatibility
        "ci_95": max(0, ci_95_days),
        "deadline_probability": max(0, min(100, final_deadline_prob)),
        "deadline_probability_items": max(0, min(100, deadline_probability_items)),
        "deadline_probability_points": max(0, min(100, deadline_probability_points))
        if deadline_probability_points
        else None,
    }

    # Prepare settings for sections
    settings = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "show_points": show_points,
        "extended_metrics": additional_context.get("extended_metrics", {})
        if additional_context
        else {},
    }

    # Extract budget data from additional_context for insights
    budget_data = additional_context.get("budget_data") if additional_context else None

    # Construct PERT data for insights (need optimistic/pessimistic for uncertainty analysis)
    # Calculate PERT bounds based on velocity variability
    pert_optimistic_days = 0
    pert_pessimistic_days = 0
    if pert_time_items and velocity_mean > 0 and velocity_std > 0:
        # Optimistic: -1σ scenario (faster than typical)
        cv_ratio = velocity_std / velocity_mean
        optimistic_factor = 1 - cv_ratio
        pessimistic_factor = 1 + (
            1.5 * cv_ratio
        )  # More conservative on pessimistic side
        pert_optimistic_days = max(1, pert_time_items * max(0.5, optimistic_factor))
        pert_pessimistic_days = pert_time_items * pessimistic_factor
    elif pert_time_items:
        # Fallback: use simple ±25% range
        pert_optimistic_days = pert_time_items * 0.75
        pert_pessimistic_days = pert_time_items * 1.25

    pert_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "pert_optimistic_days": pert_optimistic_days,
        "pert_pessimistic_days": pert_pessimistic_days,
        "last_date": last_date,
    }

    return html.Div(
        [
            # Page header
            # Executive Summary
            _create_executive_summary(
                statistics_df, settings, forecast_data, avg_weekly_items
            ),
            # Throughput Analytics
            _create_throughput_section(
                statistics_df,
                forecast_data,
                settings,
                data_points_count,
                additional_context,
            ),
            # Recent Completions Section - uses unfiltered data for consistent 4-week view
            _create_recent_activity_section(statistics_df_unfiltered, show_points),
            # Delivery Forecast Section
            _create_forecast_section(
                forecast_data,
                confidence_data,
                budget_data=budget_data,
                show_points=show_points,
            ),
            # Budget & Resource Tracking (conditional on budget configuration)
            _create_budget_section(
                profile_id=additional_context.get("profile_id", "")
                if additional_context
                else "",
                query_id=additional_context.get("query_id", "")
                if additional_context
                else "",
                week_label=additional_context.get("current_week_label", "")
                if additional_context
                else "",
                budget_data=budget_data,
                points_available=show_points,
                data_points_count=data_points_count or 12,
            ),
            # Quality & Scope Section
            _create_quality_scope_section(statistics_df, settings),
            # Insights Section
            _create_insights_section(
                statistics_df,
                settings,
                budget_data,
                pert_data=pert_data,
                deadline=settings.get("deadline") if settings else None,
            ),
        ],
        className="dashboard-comprehensive",
    )
