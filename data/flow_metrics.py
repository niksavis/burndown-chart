"""Modern Flow metrics calculator using field mappings.

Calculates the five Flow Framework metrics:
- Flow Velocity: Number of work items completed per time period
- Flow Time: Median cycle time from start to completion
- Flow Efficiency: Ratio of active time to total time
- Flow Load: Number of work items currently in progress (WIP)
- Flow Distribution: Breakdown of work by type (Feature, Bug, Tech Debt, Risk)

Helper functions and shared utilities are in data/flow_metrics_helpers.py.
Flow Time and _calculate_time_in_statuses are in data/flow_metrics_time.py.

Reference: docs/flow_metrics_spec.md
"""

import logging
from typing import Any

from data.flow_metrics_helpers import (
    FLOW_DISTRIBUTION_RECOMMENDATIONS,  # noqa: F401 (re-exported)
    _calculate_trend,
    _extract_datetime_from_field_mapping,  # noqa: F401 (re-exported)
    _find_first_transition_to_statuses,  # noqa: F401 (re-exported)
    _get_completed_date_field,
    _get_field_mappings,
    _get_work_type_for_issue,
    _is_issue_completed,
    _is_issue_in_progress,
    _normalize_work_type,  # noqa: F401 (re-exported)
)
from data.flow_metrics_time import (
    _calculate_time_in_statuses,
    calculate_flow_time,  # noqa: F401 (re-exported)
)
from data.persistence import load_app_settings

logger = logging.getLogger(__name__)


def calculate_flow_velocity(
    issues: list[dict],
    time_period_days: int = 7,
    previous_period_value: float | None = None,
) -> dict[str, Any]:
    """Calculate Flow Velocity - completed items per time period.

    Flow Velocity measures team throughput by counting completed work items.
    Higher velocity indicates higher team productivity.

    Args:
        issues: List of JIRA issues (must include changelog)
        time_period_days: Time period for velocity calculation
            (default: 7 days = 1 week)
        previous_period_value: Previous period velocity for trend calculation

    Returns:
        Dictionary with:
        {
            "value": float (items per week),
            "unit": "items/week",
            "breakdown": {
                "Feature": int,
                "Bug": int,
                "Technical Debt": int,
                "Risk": int
            },
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float,
            "error_state": None | "no_data" | "missing_mapping",
            "error_message": str | None
        }

    Example:
        >>> velocity = calculate_flow_velocity(issues, time_period_days=7)
        >>> print(f"Velocity: {velocity['value']} {velocity['unit']}")
        Velocity: 12.5 items/week
    """
    logger.info(
        f"Calculating flow velocity for {len(issues)} issues "
        f"over {time_period_days} days"
    )

    # Load field mappings
    flow_mappings, project_classification = _get_field_mappings()

    settings = load_app_settings()
    flow_type_mappings = settings.get("flow_type_mappings", {})
    flow_end_statuses = project_classification.get("flow_end_statuses", [])

    # Get completed_date field (checks general mappings, falls back to flow
    # for compatibility)
    completed_date_field = _get_completed_date_field()

    # Extract completion status and work type from issues
    completed_issues = []
    # Initialize breakdown from configured flow types, with fallback defaults
    breakdown = {key: 0 for key in flow_type_mappings.keys()}
    if not breakdown:
        breakdown = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed using field mappings
        if not _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        ):
            continue

        # Extract work type category using field mappings
        work_type = _get_work_type_for_issue(issue, flow_mappings, flow_type_mappings)
        if work_type in breakdown:
            breakdown[work_type] += 1
        else:
            # Uncategorized work type - count but log
            logger.debug(
                f"Issue {issue.get('key')} has uncategorized work type: {work_type}"
            )
            breakdown[work_type] = breakdown.get(work_type, 0) + 1
        completed_issues.append(issue)

    total_completed = len(completed_issues)

    # Check if we have data
    if total_completed == 0:
        logger.info("Flow Velocity: No completed issues found")
        return {
            "value": 0.0,
            "unit": "items/week",
            "breakdown": breakdown,
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues found in time period",
        }

    # Calculate velocity (items per week)
    weeks = time_period_days / 7.0
    velocity = total_completed / weeks if weeks > 0 else 0.0

    # Calculate trend
    trend = _calculate_trend(velocity, previous_period_value)

    logger.info(
        f"Flow Velocity: {velocity:.1f} items/week ({total_completed} completed, "
        f"breakdown={breakdown})"
    )

    return {
        "value": velocity,
        "unit": "items/week",
        "breakdown": breakdown,
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_efficiency(
    issues: list[dict],
    time_period_days: int = 7,
    previous_period_value: float | None = None,
) -> dict[str, Any]:
    """Calculate Flow Efficiency - ratio of active time to total time.

    Flow Efficiency = (Active Time / Total Time) * 100
    Higher efficiency indicates less waste (waiting, blocked time).

    Args:
        issues: List of JIRA issues (must include changelog)
        time_period_days: Time period for analysis (default: 7 days)
        previous_period_value: Previous period efficiency for trend calculation

    Returns:
        Dictionary with:
        {
            "value": float (percentage 0-100),
            "unit": "%",
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float,
            "error_state": None | "no_data" | "missing_mapping",
            "error_message": str | None
        }
    """
    logger.info(
        f"Calculating flow efficiency for {len(issues)} issues "
        f"over {time_period_days} days"
    )

    # Load field mappings
    flow_mappings, project_classification = _get_field_mappings()

    active_statuses = project_classification.get("active_statuses", [])
    wip_statuses = project_classification.get("wip_statuses", [])
    flow_end_statuses = project_classification.get("flow_end_statuses", [])
    completed_date_field = _get_completed_date_field()

    if not active_statuses or not wip_statuses:
        logger.warning(
            "Flow Efficiency: Missing active_statuses or wip_statuses configuration"
        )
        return {
            "value": 0.0,
            "unit": "%",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "missing_mapping",
            "error_message": "Missing active_statuses or wip_statuses configuration",
        }

    # Extract active and total times from completed issues
    efficiency_values = []

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed using field mappings
        if not _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        ):
            continue

        # Calculate active time and total WIP time from changelog
        issue_key = issue.get("key", "unknown")
        active_time = _calculate_time_in_statuses(changelog, active_statuses, issue_key)
        total_time = _calculate_time_in_statuses(changelog, wip_statuses, issue_key)

        logger.debug(
            f"[FlowEfficiency] {issue_key}: "
            f"active={active_time:.2f}h, total={total_time:.2f}h"
        )

        if total_time > 0:
            # Calculate efficiency for this issue
            efficiency = (active_time / total_time) * 100
            efficiency_values.append(min(efficiency, 100))  # Cap at 100%

    # Check if we have data
    if not efficiency_values:
        logger.info("Flow Efficiency: No completed issues with valid time data found")
        return {
            "value": 0.0,
            "unit": "%",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues with valid active/total time data",
        }

    # Calculate average efficiency
    average_efficiency = sum(efficiency_values) / len(efficiency_values)

    # Calculate trend
    trend = _calculate_trend(average_efficiency, previous_period_value)

    logger.info(
        f"Flow Efficiency: {average_efficiency:.1f}% average "
        f"({len(efficiency_values)} issues analyzed)"
    )

    return {
        "value": average_efficiency,
        "unit": "%",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_load(
    issues: list[dict],
    time_period_days: int = 7,
    previous_period_value: float | None = None,
) -> dict[str, Any]:
    """Calculate Flow Load - number of work items currently in progress (WIP).

    Flow Load measures the current workload on the team. Lower WIP generally
    leads to faster delivery and better quality.

    Args:
        issues: List of JIRA issues (must include changelog)
        time_period_days: Time period for analysis (not used for WIP snapshot)
        previous_period_value: Previous period WIP for trend calculation

    Returns:
        Dictionary with:
        {
            "value": int (number of items in progress),
            "unit": "items",
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float,
            "error_state": None | "no_data" | "missing_mapping",
            "error_message": str | None
        }
    """
    logger.info(f"Calculating flow load (WIP) for {len(issues)} issues")

    # Load field mappings
    _, project_classification = _get_field_mappings()

    wip_statuses = project_classification.get("wip_statuses", [])

    logger.info(f"Flow Load: wip_statuses configuration: {wip_statuses}")

    if not wip_statuses:
        logger.warning("Flow Load: Missing wip_statuses configuration")
        return {
            "value": 0,
            "unit": "items",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "missing_mapping",
            "error_message": "Missing wip_statuses configuration",
        }

    # Count issues currently in progress
    wip_count = 0

    for issue in issues:
        # Check if issue is currently in progress using field mappings
        if _is_issue_in_progress(issue, wip_statuses):
            wip_count += 1

    # Calculate trend
    trend = _calculate_trend(float(wip_count), previous_period_value)

    logger.info(f"Flow Load: {wip_count} items in progress")

    return {
        "value": wip_count,
        "unit": "items",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_distribution(
    issues: list[dict],
    time_period_days: int = 7,
    previous_period_value: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Calculate Flow Distribution - breakdown of work by type.

    Flow Distribution shows the percentage of work allocated to Features, Bugs,
    Technical Debt, and Risk items. Recommended distribution:
    - Feature: 40-70%
    - Bug: <10%
    - Technical Debt: 10-20%
    - Risk: 10-20%

    Args:
        issues: List of JIRA issues (must include changelog)
        time_period_days: Time period for analysis (default: 7 days)
        previous_period_value: Previous period distribution for trend calculation

    Returns:
        Dictionary with:
        {
            "value": {
                "Feature": float (percentage),
                "Bug": float,
                "Technical Debt": float,
                "Risk": float
            },
            "unit": "%",
            "trend_direction": "up" | "down" | "stable",  # Based on Feature %
            "trend_percentage": float,
            "error_state": None | "no_data" | "missing_mapping",
            "error_message": str | None
        }
    """
    logger.info(
        f"Calculating flow distribution for {len(issues)} issues "
        f"over {time_period_days} days"
    )

    # Load field mappings
    flow_mappings, project_classification = _get_field_mappings()

    flow_type_mappings = load_app_settings().get("flow_type_mappings", {})
    flow_end_statuses = project_classification.get("flow_end_statuses", [])

    completed_date_field = _get_completed_date_field()

    logger.info(
        f"Flow Distribution: flow_end_statuses={flow_end_statuses}, "
        f"completed_date_field={completed_date_field}"
    )
    logger.info(f"Flow Distribution: flow_type_mappings={flow_type_mappings}")

    # Initialize distribution counts from configured flow types
    distribution_counts = {key: 0 for key in flow_type_mappings.keys()}
    if not distribution_counts:
        distribution_counts = {
            "Feature": 0,
            "Defect": 0,
            "Technical Debt": 0,
            "Risk": 0,
        }

    completed_count = 0
    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed using field mappings
        is_completed = _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        )

        if is_completed:
            completed_count += 1
            # Extract work type category using field mappings
            work_type = _get_work_type_for_issue(
                issue, flow_mappings, flow_type_mappings
            )
            issue_key = issue.get("key") or issue.get("issue_key", "unknown")
            logger.debug(f"[Work Type] {issue_key}: type='{work_type}'")
            if work_type in distribution_counts:
                distribution_counts[work_type] += 1
            else:
                distribution_counts[work_type] = (
                    distribution_counts.get(work_type, 0) + 1
                )

    logger.info(
        f"Flow Distribution: Found {completed_count} completed issues "
        f"out of {len(issues)} total"
    )
    logger.info(f"Flow Distribution: distribution_counts={distribution_counts}")

    total_completed = sum(distribution_counts.values())

    # Check if we have data
    if total_completed == 0:
        logger.info("Flow Distribution: No completed issues found")
        empty_distribution = {key: 0.0 for key in distribution_counts.keys()}
        return {
            "value": empty_distribution,
            "unit": "%",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues found in time period",
        }

    # Calculate percentages
    distribution_percentages = {
        work_type: (count / total_completed) * 100
        for work_type, count in distribution_counts.items()
    }

    # Calculate trend based on Feature percentage change
    current_feature_pct = distribution_percentages.get("Feature", 0.0)
    previous_feature_pct = (
        previous_period_value.get("Feature", current_feature_pct)
        if previous_period_value
        else None
    )
    trend = _calculate_trend(current_feature_pct, previous_feature_pct)

    logger.info(f"Flow Distribution: {distribution_percentages}")

    return {
        "value": distribution_percentages,
        "unit": "%",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }
