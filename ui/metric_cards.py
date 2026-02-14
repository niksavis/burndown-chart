"""Reusable metric card components for DORA and Flow metrics.

This module provides functions to create metric display cards with support for:
- Success state with performance tier indicators
- Error states with actionable guidance
- Loading states
- Responsive design (mobile-first)
"""

from typing import Any, Dict, List, Optional
import logging

import dash_bootstrap_components as dbc
from dash import html

from ui.tooltip_utils import create_info_tooltip

logger = logging.getLogger(__name__)


def _get_flow_performance_tier_color_hex(metric_name: str, value: float) -> str:
    """Get hex color code for Flow metric performance tier.

    Maps Flow metric performance tiers to semaphore colors:
    - Excellent/Healthy: Green (#198754)
    - Good: Cyan (#0dcaf0)
    - Fair/Warning: Yellow (#ffc107)
    - Slow/Low/High: Orange (#fd7e14)
    - Critical: Red (#dc3545)

    Args:
        metric_name: Flow metric identifier (e.g., "flow_velocity", "flow_time")
        value: Metric value

    Returns:
        Hex color code for performance tier
    """
    # Import tier determination function
    from ui.flow_metrics_dashboard import _get_flow_performance_tier

    tier = _get_flow_performance_tier(metric_name, value)

    # Map tier labels to semaphore hex colors
    tier_color_map = {
        "Excellent": "#198754",  # Green
        "Good": "#0dcaf0",  # Cyan
        "Healthy": "#198754",  # Green
        "Fair": "#ffc107",  # Yellow
        "Warning": "#ffc107",  # Yellow
        "Slow": "#fd7e14",  # Orange
        "Low": "#fd7e14",  # Orange
        "High": "#fd7e14",  # Orange (for WIP)
        "Critical": "#dc3545",  # Red
    }

    return tier_color_map.get(tier, "#6f42c1")  # Default to purple if unknown


def _create_mini_bar_sparkline(
    data: List[float], color: str, height: int = 40
) -> html.Div:
    """Create a mini CSS-based bar sparkline for inline trend display.

    Args:
        data: List of numeric values to display
        color: CSS color for bars
        height: Maximum height of bars in pixels

    Returns:
        Div containing mini bar chart
    """
    if not data or len(data) < 2:
        return html.Div()

    max_val = max(data) if max(data) > 0 else 1
    normalized = [v / max_val for v in data]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * height, 2)
        opacity = 0.5 + (i / len(normalized)) * 0.5  # Fade from 0.5 to 1.0

        bars.append(
            html.Div(
                style={
                    "width": "4px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "margin": "0 1px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "1px"},
    )


def create_forecast_section(
    forecast_data: Optional[Dict[str, Any]],
    trend_vs_forecast: Optional[Dict[str, Any]],
    metric_name: str,
    unit: str,
) -> html.Div:
    """Create forecast display section for metric card (Feature 009).

    Displays 4-week weighted forecast benchmark with trend indicator showing
    current performance vs forecast.

    Args:
        forecast_data: Forecast calculation results from calculate_forecast():
            {
                "forecast_value": float,
                "confidence": "established" | "building",
                "weeks_available": int,
                "weights_applied": List[float],
                "historical_values": List[float],
                "forecast_range": Optional[Dict] (for Flow Load only)
            }
        trend_vs_forecast: Trend analysis from calculate_trend_vs_forecast():
            {
                "direction": "↗" | "→" | "↘",
                "deviation_percent": float,
                "status_text": str,
                "color_class": str,
                "is_good": bool
            }
        metric_name: Metric identifier (e.g., "flow_velocity", "dora_lead_time")
        unit: Metric unit for display

    Returns:
        Div containing forecast display, or empty div if no forecast data

    Example:
        >>> forecast_section = create_forecast_section(
        ...     forecast_data={"forecast_value": 11.9, "confidence": "established", ...},
        ...     trend_vs_forecast={"direction": "↗", "deviation_percent": 26.1, ...},
        ...     metric_name="flow_velocity",
        ...     unit="items/week"
        ... )
    """
    # No forecast data - return empty div
    if not forecast_data:
        return html.Div()

    forecast_value = forecast_data.get("forecast_value")
    confidence = forecast_data.get("confidence", "building")
    # Support both keys for backwards compatibility (weeks_with_data is preferred, weeks_available is fallback)
    weeks_with_data = forecast_data.get("weeks_with_data") or forecast_data.get(
        "weeks_available"
    )
    used_non_zero_filter = forecast_data.get(
        "used_non_zero_filter", False
    )  # Whether zeros were filtered

    # Format forecast value - standard formatting for all metrics
    if forecast_value is not None:
        forecast_display = f"{forecast_value:.2f}"
    else:
        forecast_display = "N/A"

    # Build forecast section children
    forecast_children = []

    # Build forecast label based on metric type and data availability
    # Duration metrics (filtered zeros): "(3w with data)" - emphasizes found non-zero weeks
    # Count/rate metrics (kept zeros): "(4w)" - standard label
    if weeks_with_data:
        if used_non_zero_filter:
            # Duration metric - filtered out zero weeks, always show "with data"
            weeks_label = f" ({weeks_with_data}w with data)"
        else:
            # Count/rate metric - used all weeks including zeros
            weeks_label = f" ({weeks_with_data}w)"
    else:
        weeks_label = ""

    # Confidence badge (building baseline vs established) - only show if building
    if confidence == "building" and weeks_with_data and weeks_with_data < 4:
        confidence_badge = dbc.Badge(
            "Building baseline",
            color="secondary",
            className="ms-2",
            style={"fontSize": "0.65rem", "fontWeight": "500"},
        )
    else:
        confidence_badge = None

    # Forecast value line
    forecast_children.append(
        html.Div(
            [
                html.Span(
                    "Forecast: ",
                    className="text-muted",
                    style={"fontSize": "0.85rem"},
                ),
                html.Span(
                    forecast_display,
                    className="fw-bold",
                    style={"fontSize": "0.85rem"},
                ),
                html.Span(
                    f" {unit}",
                    className="text-muted",
                    style={"fontSize": "0.75rem"},
                ),
                html.Span(
                    weeks_label,
                    className="text-muted",
                    style={"fontSize": "0.7rem"},
                ),
                confidence_badge if confidence_badge else html.Span(),
            ],
            className="text-center mb-1",
        )
    )

    # Trend vs forecast (if available)
    if trend_vs_forecast:
        direction = trend_vs_forecast.get("direction", "→")
        status_text = trend_vs_forecast.get("status_text", "On track")
        color_class = trend_vs_forecast.get("color_class", "text-secondary")

        forecast_children.append(
            html.Div(
                [
                    html.Span(
                        direction,
                        className="me-1",
                        style={"fontFamily": "inherit", "fontVariantEmoji": "text"},
                    ),
                    html.Span(status_text, className=f"{color_class}"),
                ],
                className="text-center small",
                style={"fontSize": "0.8rem", "fontWeight": "500"},
            )
        )

    # Wrap in container with subtle styling
    return html.Div(
        forecast_children,
        className="mt-2 mb-2",
        style={
            "borderTop": "1px solid #dee2e6",
            "paddingTop": "0.5rem",
        },
    )


def _get_metric_explanation(metric_name: str) -> str:
    """Get explanation text for what a metric measures.

    Args:
        metric_name: Internal metric name

    Returns:
        Explanation text for the metric
    """
    explanations = {
        "deployment_frequency": "How often you deploy to production. Higher is better - measures delivery velocity.",
        "lead_time_for_changes": "Time from code commit to production. Lower is better - measures delivery speed.",
        "change_failure_rate": "Percentage of deployments causing failures. Lower is better - measures quality.",
        "mean_time_to_recovery": "Time to restore service after incident. Lower is better - measures resilience.",
        "flow_velocity": "Work items completed per week. Higher is better - measures throughput.",
        "flow_load": "Work in progress (WIP). Lower WIP enables faster delivery and better focus.",
        "flow_time": "Time to complete work items. Lower is better - measures cycle time.",
        "flow_efficiency": "Active work time vs. total time. 25-40% is healthy - too high indicates overload.",
        "flow_distribution": "Mix of feature vs. defect vs. risk work. Balance indicates healthy product development.",
        "budget_utilization": "Percentage of total budget consumed. Shows how much budget has been spent based on completed work and team costs.",
        "weekly_burn_rate": "Budget spent per week. Calculated from completed items × cost per item. Trend shows if spending is accelerating or decelerating.",
        "budget_runway": "Weeks of budget remaining at current burn rate. Based on actual work completion, not just team cost. Critical when < 4 weeks.",
        "cost_per_item": "Average cost to complete one work item. Calculated from team cost per week ÷ velocity. Lower indicates better efficiency.",
        "cost_per_point": "Average cost to complete one story point. Calculated from team cost per week ÷ velocity. Tracks cost efficiency over time.",
        "budget_forecast": "Projected final budget at completion. Uses PERT three-point estimation with optimistic, likely, and pessimistic scenarios.",
        "cost_breakdown": "Distribution of budget across work types (Feature, Defect, Tech Debt, Risk). Shows where money is being spent.",
    }

    return explanations.get(
        metric_name, "Metric indicator for team performance and delivery capability."
    )


def _get_metric_relationship_hint(
    metric_name: str, value: Optional[float], metric_data: Dict[str, Any]
) -> Optional[str]:
    """Get relationship hint showing how this metric affects others.

    These hints explain universal relationships between metrics and are shown
    regardless of current metric state to provide educational context and
    maintain consistent card layouts.

    Args:
        metric_name: Internal metric name
        value: Current metric value
        metric_data: Full metric data dictionary

    Returns:
        Relationship hint text or None
    """
    if value is None:
        return None

    # Show hints for all metrics - they explain universal relationships

    # Flow Load (WIP) - affects everything
    if metric_name == "flow_load":
        return "High WIP typically increases Lead Time and Flow Time"

    # Change Failure Rate - affects MTTR
    elif metric_name == "change_failure_rate":
        return "High failure rate often increases MTTR and slows delivery"

    # Mean Time To Recovery - affected by CFR and process maturity
    elif metric_name == "mean_time_to_recovery":
        return "Long MTTR may indicate insufficient monitoring or unclear rollback procedures"

    # Deployment Frequency - foundation for other DORA metrics
    elif metric_name == "deployment_frequency":
        return "Low deployment frequency can increase batch size and Lead Time"

    # Lead Time - affected by WIP
    elif metric_name == "lead_time_for_changes":
        return "Long lead time may indicate high WIP or process bottlenecks"

    # Flow Time - affected by WIP
    elif metric_name == "flow_time":
        return "Long cycle time may indicate high WIP or too much waiting"

    # Flow Velocity - core throughput metric
    elif metric_name == "flow_velocity":
        return (
            "Low velocity may indicate bottlenecks, high WIP, or process inefficiency"
        )

    # Flow Efficiency - related to waiting
    elif metric_name == "flow_efficiency":
        if value < 20:
            return "Low efficiency indicates high wait times between work stages"
        elif value > 60:
            return "Very high efficiency may indicate team overload - check WIP"
        else:
            return "Efficiency = active work time / total time. 25-40% is typical for healthy teams"

    return None


def _get_action_prompt(
    metric_name: str, value: Optional[float], metric_data: Dict[str, Any]
) -> Optional[str]:
    """Get actionable guidance when metrics are concerning.

    Args:
        metric_name: Internal metric name
        value: Current metric value
        metric_data: Full metric data dictionary

    Returns:
        Action prompt text or None if metric is healthy
    """
    if value is None:
        return None

    # Flow Load (WIP) - Critical state
    if metric_name == "flow_load":
        wip_thresholds = metric_data.get("wip_thresholds", {})
        critical_threshold = wip_thresholds.get("critical", 40)

        if value >= critical_threshold:
            return "Stop starting new work. Focus on finishing existing items to reduce WIP."

    # Change Failure Rate - High failure rate
    elif metric_name == "change_failure_rate":
        if value > 30:
            return "High failure rate detected. Review deployment process and testing procedures."

    # Lead Time for Changes - Slow delivery (>1 week = 7 days)
    elif metric_name == "lead_time_for_changes":
        unit = metric_data.get("unit", "")
        if "day" in unit.lower() and value > 7:
            return (
                "Slow delivery cycle. Check for bottlenecks and consider reducing WIP."
            )

    # Mean Time to Recovery - Slow recovery (>1 day = 24 hours)
    elif metric_name == "mean_time_to_recovery":
        unit = metric_data.get("unit", "")
        if "hour" in unit.lower() and value > 24:
            return "Slow incident recovery. Review incident response process and automation."
        elif "day" in unit.lower() and value > 1:
            return "Slow incident recovery. Review incident response process and automation."

    # Deployment Frequency - Low deployment rate
    elif metric_name == "deployment_frequency":
        # Check if deploying less than once per week (< ~0.14 deploys/week = < 1/month)
        if value < 1:
            return "Low deployment frequency. Consider smaller batch sizes and more frequent releases."

    # Flow Efficiency - Too low or too high
    elif metric_name == "flow_efficiency":
        if value < 20:
            return "Low efficiency indicates high wait times. Investigate process bottlenecks."
        elif value > 60:
            return "Very high efficiency may indicate overload. Check WIP and team capacity."

    return None


def _create_detailed_chart(
    metric_name: str,
    display_name: str,
    weekly_labels: List[str],
    weekly_values: List[float],
    weekly_values_adjusted: Optional[List[float]],
    metric_data: Dict[str, Any],
    sparkline_color: str,
) -> Any:
    """Create detailed chart for metric card collapse section.

    Special handling for:
    - deployment_frequency: Shows dual lines (deployments vs releases) and details table
    For other metrics (including change_failure_rate), shows standard single-line chart.

    Args:
        metric_name: Internal metric name (e.g., "deployment_frequency", "change_failure_rate")
        display_name: Display name for chart title
        weekly_labels: Week labels
        weekly_values: Primary metric values
        weekly_values_adjusted: Optional adjusted values for current week blending
        metric_data: Full metric data dict with potential weekly_release_values
        sparkline_color: Color for the chart

    Returns:
        Div containing chart and optional details table
    """
    # Import visualization functions needed for chart creation
    from visualization.metric_trends import (
        create_metric_trend_sparkline,
        create_dual_line_trend,
        create_metric_trend_full,
    )
    from visualization.flow_charts import create_flow_efficiency_trend_chart

    # Special case 1: deployment_frequency with release tracking
    if metric_name == "deployment_frequency" and "weekly_release_values" in metric_data:
        weekly_release_values = metric_data.get("weekly_release_values", [])
        adjusted_deployment_values = weekly_values_adjusted

        # Use performance tier color already calculated from overall metric value
        # (Don't recalculate based on latest week - use the metric_data color)
        tier_color = metric_data.get("performance_tier_color", "blue")

        tier_color_map = {
            "green": "#198754",  # Elite
            "blue": "#0dcaf0",  # High (cyan)
            "yellow": "#ffc107",  # Medium
            "orange": "#fd7e14",  # Low
        }
        primary_color = tier_color_map.get(tier_color, "#0d6efd")

        chart = create_dual_line_trend(
            week_labels=weekly_labels,
            deployment_values=weekly_values,
            release_values=weekly_release_values,
            adjusted_deployment_values=adjusted_deployment_values,
            height=250,
            show_axes=True,
            primary_color=primary_color,  # Dynamic color based on performance
            chart_title="Deployment Frequency",  # Explicit title
        )

        # Removed deployment details table for cleaner card layout
        # (enables 2-cards-per-row grid on desktop)
        return chart

    # Standard single-line chart for other metrics
    # Note: change_failure_rate uses standard single-line chart (not dual-line like deployment_frequency)
    # Use full trend chart with performance zones for DORA metrics
    is_dora_metric = metric_name in [
        "deployment_frequency",
        "lead_time_for_changes",
        "change_failure_rate",
        "mean_time_to_recovery",
    ]

    if is_dora_metric:
        # Use performance tier color already calculated from overall metric value
        tier_color = metric_data.get("performance_tier_color", "blue")

        # Map tier colors to hex codes (semaphore style)
        tier_color_map = {
            "green": "#198754",  # Elite
            "blue": "#0dcaf0",  # High (cyan)
            "yellow": "#ffc107",  # Medium
            "orange": "#fd7e14",  # Low
        }
        line_color = tier_color_map.get(tier_color, "#6c757d")

        # Use full chart with performance tier zones
        return create_metric_trend_full(
            week_labels=weekly_labels,
            values=weekly_values,
            adjusted_values=weekly_values_adjusted,
            metric_name=metric_name,  # Use internal name for zone matching
            unit=metric_data.get("unit", ""),
            height=250,
            show_performance_zones=True,
            line_color=line_color,  # Dynamic color based on performance
        )
    elif metric_name == "flow_efficiency":
        # Phase 2.2: Use specialized Flow Efficiency chart with health zones
        from visualization.flow_charts import create_flow_efficiency_trend_chart
        from dash import dcc

        # Convert data format for flow_charts function (expects {date, value})
        trend_data = [
            {"date": week, "value": value}
            for week, value in zip(weekly_labels, weekly_values)
        ]

        # Calculate performance tier color based on most recent value
        latest_value = weekly_values[-1] if weekly_values else 0
        tier_color = _get_flow_performance_tier_color_hex(
            "flow_efficiency", latest_value
        )

        figure = create_flow_efficiency_trend_chart(trend_data, line_color=tier_color)
        chart_height = int(getattr(figure.layout, "height", 300) or 300)

        # CRITICAL: Remove plotly toolbar completely
        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,  # Remove plotly toolbar completely
                "staticPlot": False,  # Allow hover but no tools
                "responsive": True,  # Mobile-responsive scaling
            },
            style={"height": f"{chart_height}px"},
        )
    elif metric_name == "flow_load":
        # Use specialized Flow Load chart with dynamic WIP thresholds and tier-based color
        from visualization.flow_charts import create_flow_load_trend_chart
        from dash import dcc

        # Convert data format for flow_charts function (expects {date, value})
        trend_data = [
            {"date": week, "value": value}
            for week, value in zip(weekly_labels, weekly_values)
        ]

        # Extract WIP thresholds from metric_data (if calculated)
        wip_thresholds = metric_data.get("wip_thresholds", None)

        # Calculate performance tier color based on most recent value
        # Note: Uses dynamic wip_thresholds from metric_data if available
        latest_value = weekly_values[-1] if weekly_values else 0

        # Determine tier color using same logic as badge (lines 776-828)
        if wip_thresholds and "healthy" in wip_thresholds:
            # Use dynamic thresholds
            if latest_value < wip_thresholds["healthy"]:
                tier_color = "#198754"  # Green - Healthy
            elif latest_value < wip_thresholds["warning"]:
                tier_color = "#ffc107"  # Yellow - Warning
            elif latest_value < wip_thresholds["high"]:
                tier_color = "#fd7e14"  # Orange - High
            else:
                tier_color = "#dc3545"  # Red - Critical
        else:
            # Fallback to standard tier color calculation
            tier_color = _get_flow_performance_tier_color_hex("flow_load", latest_value)

        figure = create_flow_load_trend_chart(
            trend_data, wip_thresholds=wip_thresholds, line_color=tier_color
        )
        chart_height = int(getattr(figure.layout, "height", 300) or 300)

        # CRITICAL: Remove plotly toolbar completely
        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,  # Remove plotly toolbar completely
                "staticPlot": False,  # Allow hover but no tools
                "responsive": True,  # Mobile-responsive scaling
            },
            style={"height": f"{chart_height}px"},
        )
    else:
        # Use sparkline for other Flow metrics
        # Calculate performance tier color based on most recent value
        latest_value = weekly_values[-1] if weekly_values else 0
        tier_color = _get_flow_performance_tier_color_hex(metric_name, latest_value)

        return create_metric_trend_sparkline(
            week_labels=weekly_labels,
            values=weekly_values,
            adjusted_values=weekly_values_adjusted,
            metric_name=display_name,
            unit=metric_data.get("unit", ""),
            height=200,
            show_axes=True,
            color=tier_color,  # Dynamic color based on performance
        )


def _create_deployment_details_table(
    metric_data: Dict[str, Any],
    weekly_labels: List[str],
    weekly_deployments: List[float],
    weekly_releases: List[float],
) -> html.Div:
    """Create details table showing release names per week.

    Args:
        metric_data: Full metric data with weekly_release_names
        weekly_labels: Week labels
        weekly_deployments: Deployment counts per week
        weekly_releases: Release counts per week

    Returns:
        Div containing summary and table
    """
    # Calculate ratio stats
    total_deployments = sum(weekly_deployments)
    total_releases = sum(weekly_releases)
    ratio = total_deployments / total_releases if total_releases > 0 else 0

    # Create summary
    summary = html.Div(
        [
            html.Hr(className="my-3"),
            html.H6("Deployment Details", className="text-center mb-2"),
            html.Div(
                [
                    html.Small(
                        [
                            f"Total: {int(total_deployments)} deployments • ",
                            f"{int(total_releases)} releases • ",
                            f"Ratio: {ratio:.2f}:1",
                        ],
                        className="text-muted",
                    ),
                ],
                className="text-center mb-3",
            ),
        ]
    )

    # Get release names from snapshots (need to load from cache)
    # For now, show a simple week-by-week breakdown
    table_rows = []

    for i, week in enumerate(weekly_labels):
        if i < len(weekly_deployments) and i < len(weekly_releases):
            deployments = int(weekly_deployments[i])
            releases = int(weekly_releases[i])

            if deployments > 0 or releases > 0:
                week_ratio = deployments / releases if releases > 0 else deployments

                table_rows.append(
                    html.Tr(
                        [
                            html.Td(week, style={"fontSize": "0.85rem"}),
                            html.Td(
                                str(deployments),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                str(releases),
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Td(
                                f"{week_ratio:.2f}:1",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                )

    if not table_rows:
        table_content = html.Div(
            html.Small(
                "No deployment activity in selected period", className="text-muted"
            ),
            className="text-center my-2",
        )
    else:
        table_content = html.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th("Week", style={"fontSize": "0.85rem"}),
                            html.Th(
                                "Deployments",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Releases",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                            html.Th(
                                "Ratio",
                                className="text-center",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    )
                ),
                html.Tbody(table_rows),
            ],
            className="table table-sm table-hover",
            style={"fontSize": "0.85rem"},
        )

    return html.Div([summary, table_content])


def create_metric_card(
    metric_data: dict,
    card_id: Optional[str] = None,
    forecast_data: Optional[Dict[str, Any]] = None,
    trend_vs_forecast: Optional[Dict[str, Any]] = None,
    show_details_button: bool = True,
    text_details: Optional[List[Any]] = None,
) -> dbc.Card:
    """Create a metric display card.

    Args:
        metric_data: Dictionary with metric information:
            {
                "metric_name": str,
                "value": float | None,
                "unit": str,
                "performance_tier": str | None,  # Elite/High/Medium/Low
                "performance_tier_color": str,   # green/yellow/orange/red
                "error_state": str,              # success/missing_mapping/no_data/calculation_error
                "error_message": str | None,
                "excluded_issue_count": int,
                "total_issue_count": int,
                "details": dict
            }
        card_id: Optional HTML ID for the card
        forecast_data: Optional forecast calculation results (Feature 009)
        trend_vs_forecast: Optional trend vs forecast analysis (Feature 009)
        show_details_button: If True, show "Show Details" button for expandable chart (default: True)
        text_details: Optional list of html.Div components with rich text content to display inline

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> metric_data = {
        ...     "metric_name": "deployment_frequency",
        ...     "value": 45.2,
        ...     "unit": "deployments/month",
        ...     "performance_tier": "High",
        ...     "performance_tier_color": "yellow",
        ...     "error_state": "success",
        ...     "total_issue_count": 50
        ... }
        >>> card = create_metric_card(metric_data)
    """
    # Determine if error state
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        return _create_error_card(metric_data, card_id)

    return _create_success_card(
        metric_data,
        card_id,
        forecast_data,
        trend_vs_forecast,
        show_details_button,
        text_details,
    )


def _create_success_card(
    metric_data: dict,
    card_id: Optional[str],
    forecast_data: Optional[Dict[str, Any]] = None,
    trend_vs_forecast: Optional[Dict[str, Any]] = None,
    show_details_button: bool = True,
    text_details: Optional[List[Any]] = None,
) -> dbc.Card:
    """Create card for successful metric calculation.

    Now includes inline trend sparkline (always visible) below the metric value.
    Trend data should be provided in metric_data as:
    - weekly_labels: List of week labels (e.g., ["2025-W40", "2025-W41", ...])
    - weekly_values: List of metric values for each week

    Feature 009: Also includes forecast display section when forecast_data is provided.

    Args:
        text_details: Optional list of html components to display inline (e.g., baseline comparisons)
    """
    # Map performance tier colors to Bootstrap/custom colors
    # Use custom 'tier-orange' class for proper visual distinction
    tier_color_map = {
        "green": "success",  # Elite/Excellent
        "blue": "tier-high",  # High/Good - custom cyan
        "yellow": "tier-medium",  # Medium/Fair - custom yellow
        "orange": "tier-orange",  # Low/Slow - custom orange
        "red": "danger",  # Critical/Worst
    }

    tier_color = metric_data.get("performance_tier_color", "secondary")

    # Special handling for Flow Load (WIP) - apply health-based color coding
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    value = metric_data.get("value")

    if metric_name == "flow_load" and value is not None:
        # Get dynamic thresholds calculated from historical data using Little's Law
        wip_thresholds = metric_data.get("wip_thresholds", {})

        # Use dynamic thresholds if available, otherwise fall back to hardcoded defaults
        if wip_thresholds and "healthy" in wip_thresholds:
            healthy_threshold = wip_thresholds["healthy"]
            warning_threshold = wip_thresholds["warning"]
            high_threshold = wip_thresholds["high"]
            # critical_threshold = wip_thresholds["critical"]  # Not used in tier logic

            # Apply dynamic thresholds
            if value < healthy_threshold:
                tier_color = "green"  # Healthy
            elif value < warning_threshold:
                tier_color = "yellow"  # Warning
            elif value < high_threshold:
                tier_color = "orange"  # High
            else:
                tier_color = "red"  # Critical
        else:
            # Fallback to hardcoded thresholds if calculation failed
            if value < 10:
                tier_color = "green"  # Healthy
            elif value < 20:
                tier_color = "yellow"  # Warning
            elif value < 30:
                tier_color = "orange"  # High
            else:
                tier_color = "red"  # Critical

    # Map tier colors to valid Bootstrap color names OR custom CSS classes
    # Standard Bootstrap colors: success, danger, primary, secondary, warning, info, light, dark
    # Custom colors need className with bg- prefix
    bootstrap_color = tier_color_map.get(tier_color, "secondary")
    use_custom_class = bootstrap_color in ["tier-high", "tier-medium", "tier-orange"]

    alternative_name = metric_data.get("alternative_name")
    metric_tooltip = metric_data.get("tooltip")  # Optional tooltip text

    if alternative_name:
        display_name = alternative_name
    else:
        display_name = metric_name.replace("_", " ").title()

    # Format value - special handling for deployment_frequency with release count
    value = metric_data.get("value")
    # Note: release_value, task_value, p95_value available in metric_data for future use
    task_value = metric_data.get(
        "task_value"
    )  # NEW: deployment count (operational tasks)

    if value is not None:
        # Apply different decimal precision based on metric type
        if metric_name == "items_completed":
            # Items are countable - show as natural number
            formatted_value = f"{int(round(value))}"
        elif "items_per_week" in metric_name or "items/week" in metric_name:
            # Items per week average can have decimals (e.g., 3.5 items/week)
            formatted_value = f"{value:.1f}"
        elif "points" in metric_name:
            # Points are typically Fibonacci-based (0.5, 1, 2, 3, 5, 8, etc.) - 1 decimal
            formatted_value = f"{value:.1f}"
        else:
            # Default: 2 decimal places
            formatted_value = f"{value:.2f}"
    else:
        formatted_value = "N/A"

    # Format release value if present (deployment_frequency metric)
    # Currently not used in display but calculated for potential future use

    # Format task value if present (deployment_frequency - operational task count)
    if task_value is not None:
        formatted_task_value = f"{task_value:.2f}"
    else:
        formatted_task_value = None

    # Format P95 value if present (lead_time and mttr metrics)
    # Currently not used in display but calculated for potential future use

    # Build card with h-100 for consistent heights with error cards
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Build card header with flex layout for title on left, badge on right
    if alternative_name:
        # Use metric tooltip if provided, otherwise fall back to generic explanation
        if metric_tooltip:
            help_text = metric_tooltip
        else:
            help_text = _get_metric_explanation(metric_name)

        title_element = html.Span(
            [
                display_name,
                " ",
                create_info_tooltip(
                    help_text=help_text,
                    id_suffix=f"metric-{metric_name}",
                    placement="top",
                    variant="dark",
                ),
            ],
            className="metric-card-title",
        )
    else:
        # Start with display name
        title_content = [display_name]

        # Add metric explanation tooltip if available (from configuration)
        # If not available, use generic explanation as fallback
        if metric_tooltip:
            help_text = metric_tooltip
        else:
            help_text = _get_metric_explanation(metric_name)

        title_content.extend(
            [
                " ",
                create_info_tooltip(
                    help_text=help_text,
                    id_suffix=f"metric-{metric_name}",
                    placement="top",
                    variant="dark",
                ),
            ]
        )

        title_element = html.Span(title_content, className="metric-card-title")

    # Build header with flex layout
    # Special badge for Flow Load (WIP) showing health status
    badge_element = None
    badge_tooltip_text = None

    if metric_name == "flow_load" and value is not None:
        # Get dynamic thresholds if available
        wip_thresholds = metric_data.get("wip_thresholds", {})

        if wip_thresholds and "healthy" in wip_thresholds:
            healthy_threshold = wip_thresholds["healthy"]
            warning_threshold = wip_thresholds["warning"]
            high_threshold = wip_thresholds["high"]
            critical_threshold = wip_thresholds["critical"]

            # Apply dynamic thresholds and format badge text with threshold value
            if value < healthy_threshold:
                badge_text = f"Healthy (<{healthy_threshold:.1f})"
                badge_tooltip_text = (
                    "Optimal WIP - Team capacity is healthy and sustainable"
                )
            elif value < warning_threshold:
                badge_text = f"Warning (<{warning_threshold:.1f})"
                badge_tooltip_text = "Moderate WIP - Monitor closely, consider finishing items before starting new work"
            elif value < high_threshold:
                badge_text = f"High (<{high_threshold:.1f})"
                badge_tooltip_text = (
                    "High WIP - Too much work in progress, implement WIP limits"
                )
            else:
                badge_text = f"Critical (≥{critical_threshold:.1f})"
                badge_tooltip_text = (
                    "Critical WIP - Severely overloaded, immediate action required"
                )
        else:
            # Fallback to hardcoded thresholds with values
            if value < 10:
                badge_text = "Healthy (<10)"
                badge_tooltip_text = (
                    "Optimal WIP - Team capacity is healthy and sustainable"
                )
            elif value < 20:
                badge_text = "Warning (<20)"
                badge_tooltip_text = "Moderate WIP - Monitor closely, consider finishing items before starting new work"
            elif value < 30:
                badge_text = "High (<30)"
                badge_tooltip_text = (
                    "High WIP - Too much work in progress, implement WIP limits"
                )
            else:
                badge_text = "Critical (≥40)"
                badge_tooltip_text = (
                    "Critical WIP - Severely overloaded, immediate action required"
                )

        # Create badge with custom or standard colors
        if use_custom_class:
            badge_element = dbc.Badge(
                children=badge_text,
                className=f"ms-auto bg-{bootstrap_color}",
                style={"fontSize": "0.75rem", "fontWeight": "600"},
                id=f"badge-{card_id}" if card_id else f"badge-{metric_name}",
            )
        else:
            badge_element = dbc.Badge(
                children=badge_text,
                color=bootstrap_color,
                className="ms-auto",
                style={"fontSize": "0.75rem", "fontWeight": "600"},
                id=f"badge-{card_id}" if card_id else f"badge-{metric_name}",
            )
    else:
        # Regular badge for other metrics (DORA and Flow metrics)
        perf_tier = metric_data.get("performance_tier")

        if perf_tier:
            # Set tooltip text based on performance tier
            # DORA tier tooltips
            dora_tier_tooltips = {
                "Elite": "Top 10% of teams - world-class performance",
                "High": "Top 25% of teams - strong performance",
                "Medium": "Top 50% of teams - room for improvement",
                "Low": "Below average - needs immediate attention",
            }

            # Flow metrics tier tooltips
            flow_tier_tooltips = {
                # Flow Velocity
                "Excellent": "Outstanding throughput - team is highly productive",
                "Good": "Solid throughput - consistent delivery pace",
                "Fair": "Acceptable throughput - room for improvement",
                "Low": "Below target throughput - investigate bottlenecks",
                # Flow Time
                "Slow": "Items taking too long - reduce cycle time",
                # Generic (used by other Flow metrics if tier matches)
            }

            # Try Flow tooltips first, then DORA tooltips, then fallback
            badge_tooltip_text = (
                flow_tier_tooltips.get(perf_tier)
                or dora_tier_tooltips.get(perf_tier)
                or "Performance tier indicator"
            )

            # Use className for custom colors, color parameter for standard Bootstrap colors
            if use_custom_class:
                badge_element = dbc.Badge(
                    children=perf_tier,
                    className=f"ms-auto bg-{bootstrap_color}",
                    style={"fontSize": "0.75rem", "fontWeight": "600"},
                    id=f"badge-{card_id}" if card_id else f"badge-{metric_name}",
                )
            else:
                badge_element = dbc.Badge(
                    children=perf_tier,
                    color=bootstrap_color,
                    className="ms-auto",
                    style={"fontSize": "0.75rem", "fontWeight": "600"},
                    id=f"badge-{card_id}" if card_id else f"badge-{metric_name}",
                )

    # Wrap badge with tooltip if we have tooltip text
    if badge_element and badge_tooltip_text:
        badge_id = f"badge-{card_id}" if card_id else f"badge-{metric_name}"
        badge_with_tooltip = html.Div(
            [
                badge_element,
                dbc.Tooltip(
                    badge_tooltip_text,
                    target=badge_id,
                    placement="top",
                    trigger="click",
                    autohide=True,
                ),
            ],
            className="d-inline-block",
        )
    else:
        badge_with_tooltip = badge_element

    header_children: List[Any] = [
        html.Div(
            [
                title_element,
                badge_with_tooltip,
            ],
            className="d-flex align-items-center justify-content-between w-100",
        )
    ]

    card_header = dbc.CardHeader(header_children)

    # Build card body with inline trend sparkline
    card_body_children = [
        # Metric value (large, centered)
        html.H2(formatted_value, className="text-center metric-value mb-2"),
        # Unit (smaller, centered)
        html.P(
            metric_data.get("unit", ""),
            className="text-muted text-center metric-unit mb-1",
        ),
    ]

    # Add relationship hint if metric is in concerning state
    relationship_hint = _get_metric_relationship_hint(metric_name, value, metric_data)
    if relationship_hint:
        card_body_children.append(
            html.P(
                [
                    html.I(className="fas fa-lightbulb me-1"),
                    relationship_hint,
                ],
                className="text-muted text-center small mb-2",
                style={"fontSize": "0.8rem", "fontStyle": "italic"},
            )
        )

    # DRY/KISS FIX: Removed duplicate trend calculation (lines 1059-1145)
    # Trend data is now ONLY calculated in _calculate_dynamic_forecast() callback
    # and displayed via create_forecast_section() below (lines 1209-1217)
    # This eliminates the "100% vs prev avg" bug caused by duplicate logic.

    # Get weekly data for sparkline display (not for trend calculation)
    weekly_labels = metric_data.get("weekly_labels", [])
    weekly_values = metric_data.get("weekly_values", [])

    # For deployment_frequency, use release values for sparkline (primary metric)
    # Deployments are secondary, releases are what we measure for DORA
    if metric_name == "deployment_frequency":
        weekly_release_values = metric_data.get("weekly_release_values", [])
        if weekly_release_values:
            sparkline_values = weekly_release_values
        else:
            sparkline_values = weekly_values
    else:
        sparkline_values = weekly_values

    # Add deployment count for deployment_frequency metric
    # Add release CFR for change_failure_rate metric
    if metric_name == "deployment_frequency" and formatted_task_value is not None:
        # Show deployment count (operational tasks) as secondary metric
        card_body_children.append(
            html.Div(
                [
                    html.I(className="fas fa-rocket me-1"),
                    html.Span(f"{formatted_task_value} deployments/week"),
                ],
                className="text-center text-muted small mb-2",
            )
        )

    # Add release-based CFR as secondary for change_failure_rate
    if metric_name == "change_failure_rate":
        release_cfr = metric_data.get("release_value")
        if release_cfr is not None:
            formatted_release_cfr = (
                f"{release_cfr:.1f}" if release_cfr >= 10 else f"{release_cfr:.1f}"
            )
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-tag me-1"),
                        html.Span(f"{formatted_release_cfr}% by release"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    # Add secondary value display for Lead Time and MTTR (comparison in alternate unit)
    # Lead Time shows in days primarily, so show hours as secondary
    # MTTR shows in hours primarily, so show days as secondary
    if metric_name == "lead_time_for_changes":
        value_hours = metric_data.get("value_hours")
        if value_hours is not None:
            formatted_hours = f"{value_hours:.2f}"
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-clock me-1"),
                        html.Span(f"{formatted_hours} hours"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )
    elif metric_name == "mean_time_to_recovery":
        value_days = metric_data.get("value_days")
        if value_days is not None:
            formatted_days = f"{value_days:.2f}"
            card_body_children.append(
                html.Div(
                    [
                        html.I(className="fas fa-calendar-day me-1"),
                        html.Span(f"{formatted_days} days"),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    # Add forecast section (Feature 009)
    if forecast_data or trend_vs_forecast:
        forecast_section = create_forecast_section(
            forecast_data=forecast_data,
            trend_vs_forecast=trend_vs_forecast,
            metric_name=metric_name,
            unit=metric_data.get("unit", ""),
        )
        if forecast_section.children:  # Only add if forecast section has content
            card_body_children.append(forecast_section)

    # PROGRESSIVE BLENDING: Display blend breakdown (Feature bd-a1vn)
    blend_metadata = metric_data.get("blend_metadata")
    if blend_metadata and blend_metadata.get("is_blended"):
        from data.metrics.blending import format_blend_description

        # Create blend indicator section with f(x,y) breakdown
        blend_section = html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(
                            className="fas fa-chart-line me-1",
                            style={"fontSize": "0.8rem"},
                        ),
                        html.Span(
                            "Current Week (Blended)",
                            className="fw-bold",
                            style={"fontSize": "0.85rem"},
                        ),
                        html.Span(
                            " 📊",
                            style={"fontSize": "1rem", "marginLeft": "4px"},
                        ),
                    ],
                    className="text-muted mb-2",
                ),
                # Breakdown details in compact format
                html.Div(
                    [
                        html.Div(
                            [
                                html.Small("Adjusted Total: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['blended']:.1f}",
                                    className="fw-bold",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Small("Actual So Far: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['actual']:.0f}",
                                    className="text-secondary",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                        html.Div(
                            [
                                html.Small("Expected: ", className="text-muted"),
                                html.Small(
                                    f"{blend_metadata['forecast']:.1f}",
                                    className="text-secondary",
                                ),
                            ],
                            className="d-flex justify-content-between mb-1",
                        ),
                    ],
                    className="small",
                    style={
                        "backgroundColor": "#f8f9fa",
                        "padding": "8px",
                        "borderRadius": "4px",
                        "fontSize": "0.8rem",
                    },
                ),
                # Blend description
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        html.Small(
                            format_blend_description(blend_metadata),
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="mt-2",
                    style={"fontSize": "0.75rem"},
                ),
            ],
            className="mb-3",
        )
        card_body_children.append(blend_section)
    elif blend_metadata and not blend_metadata.get("is_blended"):
        # Weekend (Sat-Sun): Using 100% actual data, no blending needed
        day_name = blend_metadata.get("day_name", "Today")
        blend_placeholder = html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Small(
                            f"Using actual data ({day_name})",
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="text-center",
                    style={"fontSize": "0.8rem"},
                ),
            ],
            className="mb-3",
        )
        card_body_children.append(blend_placeholder)
    elif forecast_data and not blend_metadata:
        # Forecast exists but blending not available (insufficient historical data for blending)
        weeks_count = len(weekly_values) if weekly_values else 0
        blend_placeholder = html.Div(
            [
                html.Hr(className="my-2"),
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        html.Small(
                            f"Blending requires 2+ weeks of data (have {weeks_count})",
                            className="text-muted fst-italic",
                        ),
                    ],
                    className="text-center",
                    style={"fontSize": "0.8rem"},
                ),
            ],
            className="mb-3",
        )
        card_body_children.append(blend_placeholder)

    # Add optional text details (e.g., baseline comparisons for budget cards)
    if text_details:
        card_body_children.append(html.Hr(className="my-2"))
        card_body_children.extend(text_details)

    # Add inline trend sparkline if weekly data is provided
    # Note: weekly_labels and weekly_values already fetched above for trend indicator
    if weekly_labels and weekly_values and len(weekly_labels) > 1:
        # Determine color based on performance tier (semaphore system)
        sparkline_color = {
            "green": "#198754",  # Elite/Excellent (Bootstrap success)
            "blue": "#0dcaf0",  # High/Good (cyan)
            "yellow": "#ffc107",  # Medium/Fair (yellow)
            "orange": "#fd7e14",  # Low/Slow (orange)
            "red": "#dc3545",  # Critical (Bootstrap danger)
        }.get(tier_color, "#6c757d")

        # Create inline mini sparkline (CSS-based, compact)
        # For deployment_frequency, use sparkline_values (releases) not weekly_values (deployments)
        mini_sparkline = _create_mini_bar_sparkline(
            sparkline_values, sparkline_color, height=40
        )

        # Generate unique collapse ID for this card
        collapse_id = f"{metric_name}-details-collapse"

        # Build sparkline section children
        sparkline_section_children = [
            html.Small(
                f"Trend (last {len(sparkline_values)} weeks):",
                className="text-muted d-block mb-1",
            ),
            mini_sparkline,
        ]

        # Only add "Show Details" button if enabled
        if show_details_button:
            sparkline_section_children.append(
                dbc.Button(
                    [
                        html.I(className="fas fa-chart-line me-2"),
                        "Show Details",
                    ],
                    id=f"{metric_name}-details-btn",
                    color="link",
                    size="sm",
                    className="mt-2 p-0",
                    style={"fontSize": "0.85rem"},
                )
            )

        card_body_children.append(
            html.Div(
                [
                    html.Hr(className="my-2"),
                    html.Div(
                        sparkline_section_children,
                        className="text-center",
                    ),
                    # Expandable detailed chart section (only shown if button exists)
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                # Render chart lazily on first expand to avoid zero-width sizing.
                                html.Div(
                                    id=f"{metric_name}-details-chart",
                                    className="metric-details-chart",
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Hover for values • Double-click to reset zoom",
                                            className="text-muted",
                                        )
                                    ],
                                    className="text-center mt-2",
                                ),
                            ],
                            className="bg-white border-top",  # Clean white background instead of gray
                        ),
                        id=collapse_id,
                        is_open=False,
                    )
                    if show_details_button
                    else html.Div(),  # Only render Collapse if button enabled
                ],
                className="metric-trend-section",
            )
        )

    # Additional info at bottom
    card_body_children.extend(
        [
            html.Hr(className="my-2"),
            html.Small(
                _format_additional_info(metric_data),
                className="text-muted d-block text-center",
            ),
        ]
    )

    card_body = dbc.CardBody(card_body_children)

    # Create footer for action prompts (keeps cards uniform height and appearance)
    action_prompt = _get_action_prompt(metric_name, value, metric_data)
    if action_prompt:
        # Footer with action prompt alert
        card_footer = dbc.CardFooter(
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Span(action_prompt),
                ],
                color="warning",
                className="mb-0 py-2 px-3",
                style={"fontSize": "0.85rem", "lineHeight": "1.4"},
            ),
            className="bg-light border-top",
        )
    else:
        # Empty footer (same gray background for visual symmetry)
        card_footer = dbc.CardFooter(
            html.Div(
                "\u00a0",  # Non-breaking space to maintain minimal height
                className="text-center text-muted",
                style={"fontSize": "0.75rem", "opacity": "0"},
            ),
            className="bg-light border-top py-2",  # Same padding and styling
        )

    return dbc.Card([card_header, card_body, card_footer], **card_props)  # type: ignore[call-arg]


def _create_error_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for error state with actionable guidance.

    Updated to match h-100 layout of success cards for consistent card heights.
    """
    error_state = metric_data.get("error_state", "unknown_error")
    error_message = metric_data.get("error_message", "An error occurred")

    # Format metric name for display
    # Use alternative_name if provided, otherwise convert metric_name
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    alternative_name = metric_data.get("alternative_name")
    display_name = (
        alternative_name if alternative_name else metric_name.replace("_", " ").title()
    )

    # Map error states to icons and titles
    error_config = {
        "missing_mapping": {
            "icon": "fas fa-cog",
            "title": "Field Mapping Required",
            "color": "warning",
            "action_text": "Configure Mappings",
            "action_id": {
                "type": "open-field-mapping",
                "index": metric_name,
            },  # Pattern-matching ID
            "message_override": "Configure JIRA field mappings in Settings to enable this metric.",
        },
        "field_not_configured": {
            "icon": "fas fa-toggle-off",
            "title": "Metric Disabled",
            "color": "secondary",
            "action_text": "Configure Field Mapping",
            "action_id": {
                "type": "open-field-mapping",
                "index": metric_name,
            },
            "message_override": "This metric is disabled because the required JIRA field mapping is not configured for your JIRA setup.",
        },
        "points_tracking_disabled": {
            "icon": "fas fa-toggle-off",
            "title": "Points Tracking Disabled",
            "color": "secondary",
            "action_text": "Enable in Parameters",
            "action_id": "open-parameters-panel",
            "message_override": "Points tracking is disabled. Enable Points Tracking in Parameters panel to view story points metrics.",
        },
        "no_data": {
            "icon": "fas fa-database",
            "title": "No Data Available",
            "color": "secondary",
            "action_text": "Recalculate Metrics",
            "action_id": "open-time-period-selector",
            "message_override": "No data available for the selected time period. Adjust the Data Points slider or refresh metrics.",
        },
        "calculation_error": {
            "icon": "fas fa-exclamation-triangle",
            "title": "Calculation Error",
            "color": "danger",
            "action_text": "Retry Calculation",
            "action_id": "retry-metric-calculation",
        },
    }

    config = error_config.get(
        error_state,
        {
            "icon": "fas fa-exclamation-circle",
            "title": "Error",
            "color": "warning",
            "action_text": "View Details",
            "action_id": "view-error-details",
        },
    )

    # Build card with consistent h-100 class for equal heights
    card_props = {"className": "metric-card metric-card-error mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Determine badge text based on error state
    badge_text_map = {
        "no_data": "No Data",
        "missing_mapping": "Setup Required",
        "field_not_configured": "Disabled",
        "points_tracking_disabled": "Disabled",
        "calculation_error": "Error",
    }
    badge_text = badge_text_map.get(error_state, "Error")

    card_header = dbc.CardHeader(
        [
            html.Span(display_name, className="metric-card-title"),
            dbc.Badge(
                children=badge_text, color=config["color"], className="float-end"
            ),
        ]
    )

    card_body = dbc.CardBody(
        [
            # Icon and title (compact layout)
            html.Div(
                [
                    html.I(
                        className=f"{config['icon']} fa-2x text-{config['color']} mb-2"
                    ),
                    html.H2("—", className="text-center metric-value mb-1 text-muted"),
                    html.P(
                        config["title"],
                        className="text-muted text-center metric-unit mb-2",
                    ),
                ],
                className="text-center",
            ),
            # Divider matching success cards
            html.Hr(className="my-2"),
            # Error message (compact)
            html.Small(
                config.get("message_override", error_message),
                className="text-muted d-block text-center",
            ),
        ],
        className="d-flex flex-column",
    )

    # Add footer matching success cards (gray background for visual consistency)
    card_footer = dbc.CardFooter(
        html.Div(
            "\u00a0",  # Non-breaking space to maintain minimal height
            className="text-center text-muted",
            style={"fontSize": "0.75rem", "opacity": "0"},
        ),
        className="bg-light border-top py-2",  # Same padding and styling as success cards
    )

    return dbc.Card([card_header, card_body, card_footer], **card_props)  # type: ignore[call-arg]


def _format_additional_info(metric_data: dict) -> str:
    """Format additional information text for metric card."""
    total_issues = metric_data.get("total_issue_count", 0)
    excluded_issues = metric_data.get("excluded_issue_count", 0)
    metric_name = metric_data.get("metric_name", "")
    n_weeks = metric_data.get("_n_weeks", 12)  # Get selected time period

    # Determine aggregation method label
    aggregation_labels = {
        "lead_time_for_changes": "Median of weekly medians",
        "mean_time_to_recovery": "Median of weekly medians",
        "flow_time": "Median of weekly medians",
        "flow_velocity": "Average per week",
        "flow_efficiency": "Average of weekly values",
        "flow_load": "Current week snapshot",
        "deployment_frequency": "Average per week",
        "change_failure_rate": "Overall rate",
    }

    aggregation_label = aggregation_labels.get(metric_name, "")

    if excluded_issues > 0:
        base_text = f"{total_issues - excluded_issues} of {total_issues} issues"
    else:
        base_text = f"{total_issues} issues" if total_issues > 0 else ""

    # Format: "Aggregation method • Based on X issues • Y weeks"
    parts = []
    if aggregation_label:
        parts.append(aggregation_label)
    if base_text:
        parts.append(base_text)
    if metric_name != "flow_load" and n_weeks:  # Don't show weeks for WIP
        parts.append(f"{n_weeks} weeks")

    return " • ".join(parts)


def create_loading_card(metric_name: str) -> dbc.Card:
    """Create a loading placeholder card.

    Args:
        metric_name: Name of the metric being calculated

    Returns:
        Card with loading spinner
    """
    display_name = metric_name.replace("_", " ").title()

    return dbc.Card(
        [
            dbc.CardHeader(display_name),
            dbc.CardBody(
                [
                    dbc.Spinner(size="lg", color="primary"),
                    html.P("Calculating...", className="text-muted text-center mt-3"),
                ],
                className="text-center",
            ),
        ],
        className="metric-card metric-card-loading mb-3",
    )


def create_metric_cards_grid(
    metrics_data: Dict[str, dict], tooltips: Optional[Dict[str, str]] = None
) -> dbc.Row:
    """Create a responsive grid of metric cards.

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "deployment_frequency": {...},
                "lead_time_for_changes": {...}
            }
        tooltips: Optional dictionary mapping metric names to tooltip text
            Example:
            {
                "flow_velocity": "Number of work items completed per week...",
                "flow_time": "Median time from work start to completion..."
            }

    Returns:
        Dash Bootstrap Row with responsive columns
    """
    cards = []
    for metric_name, metric_info in metrics_data.items():
        # Add tooltip to metric_info if provided
        if tooltips and metric_name in tooltips:
            metric_info = {**metric_info, "tooltip": tooltips[metric_name]}

        # Extract forecast data (Feature 009)
        forecast_data = metric_info.get("forecast_data")
        trend_vs_forecast = metric_info.get("trend_vs_forecast")

        card = create_metric_card(
            metric_info,
            card_id=f"{metric_name}-card",
            forecast_data=forecast_data,
            trend_vs_forecast=trend_vs_forecast,
        )
        # 2 cards per row on desktop (lg=6), 1 card per row on mobile (xs=12)
        col = dbc.Col(card, xs=12, lg=6, className="mb-3")
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid")
