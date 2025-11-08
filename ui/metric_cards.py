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
    }

    return explanations.get(
        metric_name, "Metric indicator for team performance and delivery capability."
    )


def _get_metric_relationship_hint(
    metric_name: str, value: Optional[float], metric_data: Dict[str, Any]
) -> Optional[str]:
    """Get relationship hint showing how this metric affects others.

    Args:
        metric_name: Internal metric name
        value: Current metric value
        metric_data: Full metric data dictionary

    Returns:
        Relationship hint text or None
    """
    if value is None:
        return None

    # Only show hints when metrics are in concerning states

    # Flow Load (WIP) - affects everything
    if metric_name == "flow_load":
        wip_thresholds = metric_data.get("wip_thresholds", {})
        high_threshold = wip_thresholds.get("high", 30)

        if value >= high_threshold:
            return "💡 High WIP typically increases Lead Time and Flow Time"

    # Change Failure Rate - affects MTTR
    elif metric_name == "change_failure_rate":
        if value > 30:
            return "💡 High failure rate often increases MTTR and slows delivery"

    # Lead Time - affected by WIP
    elif metric_name == "lead_time_for_changes":
        unit = metric_data.get("unit", "")
        if "day" in unit.lower() and value > 7:
            return "💡 Long lead time may indicate high WIP or process bottlenecks"

    # Flow Time - affected by WIP
    elif metric_name == "flow_time":
        if value > 14:  # More than 2 weeks
            return "💡 Long cycle time may indicate high WIP or too much waiting"

    # Flow Efficiency - related to waiting
    elif metric_name == "flow_efficiency":
        if value < 20:
            return "💡 Low efficiency indicates high wait times between work stages"
        elif value > 60:
            return "💡 Very high efficiency may indicate team overload - check WIP"

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
    metric_data: Dict[str, Any],
    sparkline_color: str,
) -> Any:
    """Create detailed chart for metric card collapse section.

    Special handling for:
    - deployment_frequency: Shows dual lines (deployments vs releases) and details table
    - change_failure_rate: Shows dual lines (deployment CFR vs release CFR)
    For other metrics, shows standard single-line chart.

    Args:
        metric_name: Internal metric name (e.g., "deployment_frequency", "change_failure_rate")
        display_name: Display name for chart title
        weekly_labels: Week labels
        weekly_values: Primary metric values
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
            height=250,
            show_axes=True,
            primary_color=primary_color,  # Dynamic color based on performance
            chart_title="Deployment Frequency",  # Explicit title
        )

        # Removed deployment details table for cleaner card layout
        # (enables 2-cards-per-row grid on desktop)
        return chart

    # Special case 2: change_failure_rate with release tracking
    if metric_name == "change_failure_rate" and "weekly_release_values" in metric_data:
        weekly_release_values = metric_data.get("weekly_release_values", [])

        # Use performance tier color already calculated from overall metric value
        tier_color = metric_data.get("performance_tier_color", "green")

        tier_color_map = {
            "green": "#198754",  # Elite
            "blue": "#0dcaf0",  # High (cyan)
            "yellow": "#ffc107",  # Medium
            "orange": "#fd7e14",  # Low
        }
        primary_color = tier_color_map.get(tier_color, "#0d6efd")

        # Reuse dual line chart but with different labels and dynamic color
        chart = create_dual_line_trend(
            week_labels=weekly_labels,
            deployment_values=weekly_values,
            release_values=weekly_release_values,
            height=250,
            show_axes=True,
            primary_color=primary_color,  # Dynamic color based on performance
            chart_title="Change Failure Rate",  # Explicit title
        )

        # Customize the chart for CFR context with a note
        cfr_note = html.Div(
            [
                html.Hr(className="my-2"),
                html.Small(
                    [
                        html.I(className="fas fa-info-circle me-1 text-info"),
                        "Blue line shows deployment-based CFR (operational tasks), ",
                        "Green line shows release-based CFR (unique fixVersions). ",
                        "Release-based CFR avoids double-counting failures for the same release.",
                    ],
                    className="text-muted",
                ),
            ],
            className="text-center",
        )

        return html.Div([chart, cfr_note])

    # Standard single-line chart for other metrics
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

        # CRITICAL: Remove plotly toolbar completely
        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,  # Remove plotly toolbar completely
                "staticPlot": False,  # Allow hover but no tools
                "responsive": True,  # Mobile-responsive scaling
            },
        )
    elif metric_name == "flow_load":
        # Use specialized Flow Load chart with dynamic WIP thresholds
        from visualization.flow_charts import create_flow_load_trend_chart
        from dash import dcc

        # Convert data format for flow_charts function (expects {date, value})
        trend_data = [
            {"date": week, "value": value}
            for week, value in zip(weekly_labels, weekly_values)
        ]

        # Extract WIP thresholds from metric_data (if calculated)
        wip_thresholds = metric_data.get("wip_thresholds", None)

        figure = create_flow_load_trend_chart(trend_data, wip_thresholds=wip_thresholds)

        # CRITICAL: Remove plotly toolbar completely
        return dcc.Graph(
            figure=figure,
            config={
                "displayModeBar": False,  # Remove plotly toolbar completely
                "staticPlot": False,  # Allow hover but no tools
                "responsive": True,  # Mobile-responsive scaling
            },
        )
    else:
        # Use sparkline for other Flow metrics
        # Calculate performance tier color based on most recent value
        latest_value = weekly_values[-1] if weekly_values else 0
        tier_color = _get_flow_performance_tier_color_hex(metric_name, latest_value)

        return create_metric_trend_sparkline(
            week_labels=weekly_labels,
            values=weekly_values,
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
                            f"Ratio: {ratio:.1f}:1",
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
                                f"{week_ratio:.1f}:1",
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


def create_metric_card(metric_data: dict, card_id: Optional[str] = None) -> dbc.Card:
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

    return _create_success_card(metric_data, card_id)


def _create_success_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for successful metric calculation.

    Now includes inline trend sparkline (always visible) below the metric value.
    Trend data should be provided in metric_data as:
    - weekly_labels: List of week labels (e.g., ["2025-W40", "2025-W41", ...])
    - weekly_values: List of metric values for each week
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
        tooltip_text = f"Interpreted as: {alternative_name} (Standard field: {metric_name.replace('_', ' ').title()})"
    else:
        display_name = metric_name.replace("_", " ").title()
        tooltip_text = None

    # Format value - special handling for deployment_frequency with release count
    value = metric_data.get("value")
    release_value = metric_data.get("release_value")  # NEW: for deployment_frequency
    p95_value = metric_data.get("p95_value")  # NEW: for lead_time and mttr

    if value is not None:
        formatted_value = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
    else:
        formatted_value = "N/A"

    # Format release value if present (deployment_frequency metric)
    if release_value is not None:
        formatted_release_value = (
            f"{release_value:.1f}" if release_value >= 10 else f"{release_value:.2f}"
        )
    else:
        formatted_release_value = None

    # Format P95 value if present (lead_time and mttr metrics)
    if p95_value is not None:
        formatted_p95_value = (
            f"{p95_value:.1f}" if p95_value >= 10 else f"{p95_value:.2f}"
        )
    else:
        formatted_p95_value = None

    # Build card with h-100 for consistent heights with error cards
    card_props = {"className": "metric-card mb-3 h-100"}
    if card_id:
        card_props["id"] = card_id

    # Build card header with flex layout for title on left, badge on right
    if alternative_name:
        title_element = html.Span(
            [
                html.I(
                    className="fas fa-info-circle me-2 text-info",
                    title=tooltip_text,
                ),
                display_name,
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
        # Regular badge for other metrics (DORA metrics)
        perf_tier = metric_data.get("performance_tier")

        if perf_tier:
            # Set tooltip text based on performance tier
            tier_tooltips = {
                "Elite": "Top 10% of teams - world-class performance",
                "High": "Top 25% of teams - strong performance",
                "Medium": "Top 50% of teams - room for improvement",
                "Low": "Below average - needs immediate attention",
            }
            badge_tooltip_text = tier_tooltips.get(
                perf_tier, "Performance tier indicator"
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
                relationship_hint,
                className="text-muted text-center small mb-2",
                style={"fontSize": "0.8rem", "fontStyle": "italic"},
            )
        )

    # Add trend indicator with percentage change
    weekly_labels = metric_data.get("weekly_labels", [])
    weekly_values = metric_data.get("weekly_values", [])

    trend_added = False  # Track if we added a trend indicator

    if weekly_values and len(weekly_values) >= 2:
        # Calculate trend: compare most recent value to median of previous values
        current_value = weekly_values[-1]
        previous_values = weekly_values[:-1]
        if previous_values:
            previous_avg = sum(previous_values) / len(previous_values)
            # Handle case where average is 0 (but we still want to show trend)
            if previous_avg > 0:
                percent_change = ((current_value - previous_avg) / previous_avg) * 100
            elif current_value > 0:
                # If previous was 0 but current is non-zero, show large increase
                percent_change = 100.0
            elif current_value == 0 and previous_avg == 0:
                # Both zero - show neutral/no change
                percent_change = 0.0
            else:
                # Current is 0 but previous was non-zero (shouldn't happen if previous_avg > 0 check failed)
                percent_change = -100.0

            # Determine if trend is good based on metric type
            # For deployment_frequency, flow_velocity: higher is better (green up, red down)
            # For lead_time, mttr, cfr, flow_time, flow_load: lower is better (green down, red up)
            is_higher_better = metric_name in ["deployment_frequency", "flow_velocity"]

            # Show neutral/stable indicator for no change (exactly 0.0%)
            if percent_change == 0.0:
                trend_color = "secondary"
                trend_icon = "fas fa-arrow-right"
                trend_text = "0.0% vs prev avg"
            elif is_higher_better:
                # Higher is better metrics
                if percent_change > 0:
                    trend_color = "success"
                    trend_icon = "fas fa-arrow-up"
                else:
                    trend_color = "danger"
                    trend_icon = "fas fa-arrow-down"
                trend_text = f"{abs(percent_change):.1f}% vs prev avg"
            else:
                # Lower is better metrics
                if percent_change < 0:
                    trend_color = "success"
                    trend_icon = "fas fa-arrow-down"
                else:
                    trend_color = "danger"
                    trend_icon = "fas fa-arrow-up"
                trend_text = f"{abs(percent_change):.1f}% vs prev avg"

            # Show neutral color for very small changes (< 5% but not exactly 0)
            if abs(percent_change) < 5 and percent_change != 0.0:
                trend_color = "secondary"
                trend_icon = "fas fa-minus"

            # Create context-aware tooltip explaining if trend is good or bad
            if percent_change == 0.0:
                trend_tooltip = "No change from recent average - stable performance"
            elif is_higher_better:
                # Higher is better (Deployment Frequency, Flow Velocity)
                if percent_change > 0:
                    trend_tooltip = (
                        "Trending better ↑ - Higher than recent average. Keep it up!"
                    )
                else:
                    trend_tooltip = "Trending worse ↓ - Lower than recent average. Review bottlenecks."
            else:
                # Lower is better (Lead Time, MTTR, CFR, Flow Time, Flow Load)
                if percent_change < 0:
                    trend_tooltip = (
                        "Trending better ↓ - Lower than recent average. Great progress!"
                    )
                else:
                    trend_tooltip = "Trending worse ↑ - Higher than recent average. Needs attention."

            # Small changes are neutral
            if abs(percent_change) < 5 and percent_change != 0.0:
                trend_tooltip = "Minor change - performance is relatively stable"

            # Create trend indicator with tooltip
            trend_indicator = html.Div(
                [
                    html.I(className=f"{trend_icon} me-1"),
                    html.Span(trend_text),
                ],
                className=f"text-center text-{trend_color} small mb-2",
                style={"fontWeight": "500"},
                id=f"trend-{card_id}" if card_id else f"trend-{metric_name}",
            )

            # Wrap trend indicator with tooltip
            card_body_children.append(
                html.Div(
                    [
                        trend_indicator,
                        dbc.Tooltip(
                            trend_tooltip,
                            target=f"trend-{card_id}"
                            if card_id
                            else f"trend-{metric_name}",
                            placement="top",
                        ),
                    ],
                    className="d-inline-block w-100",
                )
            )
            trend_added = True

    # Add placeholder if no trend was added (maintains consistent card height)
    if not trend_added:
        card_body_children.append(
            html.Div(
                [
                    html.I(className="fas fa-minus me-1"),
                    html.Span("No trend data yet"),
                ],
                className="text-center text-muted small mb-2",
                style={"fontWeight": "500"},
            )
        )

    # Add release count for deployment_frequency and change_failure_rate metrics
    # Add P95 for lead_time_for_changes and mean_time_to_recovery metrics
    if formatted_release_value is not None and metric_name in [
        "deployment_frequency",
        "change_failure_rate",
    ]:
        # Determine text and icon based on metric type
        release_config = {
            "deployment_frequency": {
                "text": f"{formatted_release_value} releases/week",
                "icon": "fas fa-code-branch me-1",
            },
            "change_failure_rate": {
                "text": f"{formatted_release_value}% release CFR",
                "icon": "fas fa-code-branch me-1",
            },
        }

        config = release_config.get(metric_name, {})
        if config:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className=config["icon"]),
                        html.Span(config["text"]),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

    # Add P95 information for lead_time_for_changes and mean_time_to_recovery
    elif formatted_p95_value is not None and metric_name in [
        "lead_time_for_changes",
        "mean_time_to_recovery",
    ]:
        # Determine text and icon based on metric type
        p95_config = {
            "lead_time_for_changes": {
                "text": f"{formatted_p95_value}d P95 (95% faster)",
                "icon": "fas fa-chart-line me-1",
            },
            "mean_time_to_recovery": {
                "text": f"{formatted_p95_value}h P95 (95% faster)",
                "icon": "fas fa-chart-line me-1",
            },
        }

        config = p95_config.get(metric_name, {})
        if config:
            card_body_children.append(
                html.Div(
                    [
                        html.I(className=config["icon"]),
                        html.Span(config["text"]),
                    ],
                    className="text-center text-muted small mb-2",
                )
            )

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
        mini_sparkline = _create_mini_bar_sparkline(
            weekly_values, sparkline_color, height=40
        )

        # Generate unique collapse ID for this card
        collapse_id = f"{metric_name}-details-collapse"

        card_body_children.append(
            html.Div(
                [
                    html.Hr(className="my-2"),
                    html.Div(
                        [
                            html.Small(
                                f"Trend (last {len(weekly_values)} weeks):",
                                className="text-muted d-block mb-1",
                            ),
                            mini_sparkline,
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
                            ),
                        ],
                        className="text-center",
                    ),
                    # Expandable detailed chart section
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                # Removed HTML heading - chart has its own title
                                # Special handling for deployment_frequency to show dual lines
                                _create_detailed_chart(
                                    metric_name=metric_name,
                                    display_name=display_name,
                                    weekly_labels=weekly_labels,
                                    weekly_values=weekly_values,
                                    metric_data=metric_data,
                                    sparkline_color=sparkline_color,
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
                    ),
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
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    display_name = metric_name.replace("_", " ").title()

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
        "no_data": {
            "icon": "fas fa-inbox",
            "title": "No Data Available",
            "color": "secondary",
            "action_text": "Recalculate Metrics",
            "action_id": "open-time-period-selector",
            "message_override": "No data found for the selected time period. Try recalculating metrics or adjusting the time range.",
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

    return dbc.Card([card_header, card_body], **card_props)  # type: ignore[call-arg]


def _format_additional_info(metric_data: dict) -> str:
    """Format additional information text for metric card."""
    total_issues = metric_data.get("total_issue_count", 0)
    excluded_issues = metric_data.get("excluded_issue_count", 0)

    if excluded_issues > 0:
        return (
            f"Based on {total_issues - excluded_issues} of {total_issues} issues. "
            f"{excluded_issues} excluded due to missing data."
        )
    else:
        return f"Based on {total_issues} issues"


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

        card = create_metric_card(metric_info, card_id=f"{metric_name}-card")
        # 2 cards per row on desktop (lg=6), 1 card per row on mobile (xs=12)
        col = dbc.Col(card, xs=12, lg=6, className="mb-3")
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid")
