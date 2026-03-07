"""Private helper utilities for metric card components.

Provides color/tier lookups, text explanations, sparkline builder, and
the additional-info formatter used across metric card sub-modules.
"""

from typing import Any

from dash import html


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
    data: list[float], color: str, height: int = 40
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
        "deployment_frequency": (
            "How often you deploy to production. "
            "Higher is better - measures delivery velocity."
        ),
        "lead_time_for_changes": (
            "Time from code commit to production. "
            "Lower is better - measures delivery speed."
        ),
        "change_failure_rate": (
            "Percentage of deployments causing failures. "
            "Lower is better - measures quality."
        ),
        "mean_time_to_recovery": (
            "Time to restore service after incident. "
            "Lower is better - measures resilience."
        ),
        "flow_velocity": (
            "Work items completed per week. Higher is better - measures throughput."
        ),
        "flow_load": (
            "Work in progress (WIP). Lower WIP enables "
            "faster delivery and better focus."
        ),
        "flow_time": (
            "Time to complete work items. Lower is better - measures cycle time."
        ),
        "flow_efficiency": (
            "Active work time vs. total time. 25-40% is healthy "
            "- too high indicates overload."
        ),
        "flow_distribution": (
            "Mix of feature vs. defect vs. risk work. "
            "Balance indicates healthy product development."
        ),
        "budget_utilization": (
            "Percentage of total budget consumed. "
            "Shows how much budget has been spent based "
            "on completed work and team costs."
        ),
        "weekly_burn_rate": (
            "Budget spent per week. Calculated from completed items "
            "x cost per item. Trend shows if spending is "
            "accelerating or decelerating."
        ),
        "budget_runway": (
            "Weeks of budget remaining at current burn rate. "
            "Based on actual work completion, not just team cost. "
            "Critical when < 4 weeks."
        ),
        "cost_per_item": (
            "Average cost to complete one work item. Calculated from "
            "team cost per week / velocity. Lower indicates "
            "better efficiency."
        ),
        "cost_per_point": (
            "Average cost to complete one story point. Calculated from "
            "team cost per week / velocity. Tracks cost "
            "efficiency over time."
        ),
        "budget_forecast": (
            "Projected final budget at completion. Uses PERT "
            "three-point estimation with optimistic, likely, "
            "and pessimistic scenarios."
        ),
        "cost_breakdown": (
            "Distribution of budget across work types "
            "(Feature, Defect, Tech Debt, Risk). "
            "Shows where money is being spent."
        ),
    }

    return explanations.get(
        metric_name, "Metric indicator for team performance and delivery capability."
    )


def _get_metric_relationship_hint(
    metric_name: str, value: float | None, metric_data: dict[str, Any]
) -> str | None:
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
        return (
            "Long MTTR may indicate insufficient monitoring "
            "or unclear rollback procedures"
        )

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
            return (
                "Efficiency = active work time / total time. "
                "25-40% is typical for healthy teams"
            )

    return None


def _get_action_prompt(
    metric_name: str, value: float | None, metric_data: dict[str, Any]
) -> str | None:
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
            return (
                "Stop starting new work. Focus on finishing existing "
                "items to reduce WIP."
            )

    # Change Failure Rate - High failure rate
    elif metric_name == "change_failure_rate":
        if value > 30:
            return (
                "High failure rate detected. Review deployment process "
                "and testing procedures."
            )

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
            return (
                "Slow incident recovery. Review incident response "
                "process and automation."
            )
        elif "day" in unit.lower() and value > 1:
            return (
                "Slow incident recovery. Review incident response "
                "process and automation."
            )

    # Deployment Frequency - Low deployment rate
    elif metric_name == "deployment_frequency":
        # Check if deploying less than once per week (< ~0.14 deploys/week = < 1/month)
        if value < 1:
            return (
                "Low deployment frequency. Consider smaller batch sizes "
                "and more frequent releases."
            )

    # Flow Efficiency - Too low or too high
    elif metric_name == "flow_efficiency":
        if value < 20:
            return (
                "Low efficiency indicates high wait times. "
                "Investigate process bottlenecks."
            )
        elif value > 60:
            return (
                "Very high efficiency may indicate overload. "
                "Check WIP and team capacity."
            )

    return None


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

    # Format: "Aggregation method * Based on X issues * Y weeks"
    parts = []
    if aggregation_label:
        parts.append(aggregation_label)
    if base_text:
        parts.append(base_text)
    if metric_name != "flow_load" and n_weeks:  # Don't show weeks for WIP
        parts.append(f"{n_weeks} weeks")

    return " \u2022 ".join(parts)
