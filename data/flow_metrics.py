"""Modern Flow metrics calculator using variable extraction.

Calculates the five Flow Framework metrics:
- Flow Velocity: Number of work items completed per time period
- Flow Time: Average cycle time from start to completion
- Flow Efficiency: Ratio of active time to total time
- Flow Load: Number of work items currently in progress (WIP)
- Flow Distribution: Breakdown of work by type (Feature, Bug, Tech Debt, Risk)

This implementation uses VariableExtractor for clean, rule-based data extraction
with no backward compatibility for legacy field_mappings.

Architecture:
- Pure business logic with no UI dependencies
- Clean separation between data extraction (VariableExtractor) and calculation
- Consistent error handling and metric formatting
- Comprehensive logging for debugging and monitoring

Reference: docs/flow_metrics_spec.md
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from data.variable_mapping.extractor import VariableExtractor

logger = logging.getLogger(__name__)


# Flow Distribution recommended ranges (based on Flow Framework)
FLOW_DISTRIBUTION_RECOMMENDATIONS = {
    "Feature": {"min": 40, "max": 70, "unit": "%", "label": "Product value"},
    "Bug": {"min": 0, "max": 10, "unit": "%", "label": "Defect resolution"},
    "Technical Debt": {"min": 10, "max": 20, "unit": "%", "label": "Sustainability"},
    "Risk": {"min": 10, "max": 20, "unit": "%", "label": "Risk reduction"},
}


def _calculate_trend(
    current_value: float, previous_value: Optional[float]
) -> Dict[str, Any]:
    """Calculate trend direction and percentage change.

    Args:
        current_value: Current period metric value
        previous_value: Previous period metric value (None if unavailable)

    Returns:
        Dictionary with trend information:
        {
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float (percentage change)
        }
    """
    if previous_value is None or previous_value == 0:
        return {"trend_direction": "stable", "trend_percentage": 0.0}

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    # Consider changes < 5% as "stable" to avoid noise
    if abs(percentage_change) < 5:
        return {"trend_direction": "stable", "trend_percentage": percentage_change}

    direction = "up" if percentage_change > 0 else "down"
    return {"trend_direction": direction, "trend_percentage": percentage_change}


def _normalize_work_type(work_type: Any) -> str:
    """Normalize work type value to standard categories.

    Args:
        work_type: Work type value from extractor (can be str, dict, or None)

    Returns:
        Normalized category: "Feature", "Bug", "Technical Debt", or "Risk"
    """
    # If extractor returned a dict (shouldn't happen but be defensive)
    if isinstance(work_type, dict):
        return "Feature"  # Default

    # If it's not a string, default to Feature
    if not isinstance(work_type, str):
        return "Feature"

    # Normalize to lowercase for matching
    work_type_lower = work_type.lower()

    # Map to standard categories
    if "feature" in work_type_lower or "story" in work_type_lower:
        return "Feature"
    elif "bug" in work_type_lower or "defect" in work_type_lower:
        return "Bug"
    elif "debt" in work_type_lower or "technical" in work_type_lower:
        return "Technical Debt"
    elif "risk" in work_type_lower:
        return "Risk"
    else:
        return "Feature"  # Default for unknown types


def calculate_flow_velocity(
    issues: List[Dict],
    extractor: VariableExtractor,
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Velocity - completed items per time period.

    Flow Velocity measures team throughput by counting completed work items.
    Higher velocity indicates higher team productivity.

    Args:
        issues: List of JIRA issues (must include changelog)
        extractor: Configured VariableExtractor with Flow mappings
        time_period_days: Time period for velocity calculation (default: 7 days = 1 week)
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
        >>> extractor = VariableExtractor(variable_mappings)
        >>> velocity = calculate_flow_velocity(issues, extractor, time_period_days=7)
        >>> print(f"Velocity: {velocity['value']} {velocity['unit']}")
        Velocity: 12.5 items/week
    """
    logger.info(
        f"Calculating flow velocity for {len(issues)} issues over {time_period_days} days"
    )

    # Extract completion status and work type from issues
    completed_issues = []
    breakdown = {"Feature": 0, "Bug": 0, "Technical Debt": 0, "Risk": 0}

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed
        is_completed_result = extractor.extract_variable(
            "is_completed", issue, changelog
        )

        if not is_completed_result.get("found") or not is_completed_result.get("value"):
            continue

        # Extract work type category
        work_type_result = extractor.extract_variable(
            "work_type_category", issue, changelog
        )

        # Normalize work type to standard categories
        if work_type_result.get("found"):
            work_type = work_type_result.get("value")
            category = _normalize_work_type(work_type)
            breakdown[category] += 1
        else:
            # Default to Feature if work type not found
            breakdown["Feature"] += 1

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
        f"{breakdown['Feature']} features, {breakdown['Bug']} bugs)"
    )

    return {
        "value": round(velocity, 1),
        "unit": "items/week",
        "breakdown": breakdown,
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_time(
    issues: List[Dict],
    extractor: VariableExtractor,
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Time - average cycle time from start to completion.

    Flow Time measures how long work items take to complete from when work started
    to when they're done. Lower flow time indicates faster delivery.

    Args:
        issues: List of JIRA issues (must include changelog)
        extractor: Configured VariableExtractor with Flow mappings
        time_period_days: Time period for analysis (default: 7 days)
        previous_period_value: Previous period flow time for trend calculation

    Returns:
        Dictionary with:
        {
            "value": float (average days),
            "unit": "days",
            "trend_direction": "up" | "down" | "stable",
            "trend_percentage": float,
            "error_state": None | "no_data" | "missing_mapping",
            "error_message": str | None
        }
    """
    logger.info(
        f"Calculating flow time for {len(issues)} issues over {time_period_days} days"
    )

    # Extract cycle times from completed issues
    cycle_times = []

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed
        is_completed_result = extractor.extract_variable(
            "is_completed", issue, changelog
        )

        if not is_completed_result.get("found") or not is_completed_result.get("value"):
            continue

        # Extract start and completion timestamps
        start_result = extractor.extract_variable(
            "work_started_timestamp", issue, changelog
        )
        completion_result = extractor.extract_variable(
            "work_completed_timestamp", issue, changelog
        )

        if not start_result.get("found") or not completion_result.get("found"):
            continue

        start_timestamp = start_result.get("value")
        completion_timestamp = completion_result.get("value")

        if start_timestamp and completion_timestamp:
            try:
                # Parse timestamps if they're strings
                if isinstance(start_timestamp, str):
                    start_dt = datetime.fromisoformat(
                        start_timestamp.replace("Z", "+00:00")
                    )
                else:
                    start_dt = start_timestamp

                if isinstance(completion_timestamp, str):
                    completion_dt = datetime.fromisoformat(
                        completion_timestamp.replace("Z", "+00:00")
                    )
                else:
                    completion_dt = completion_timestamp

                # Calculate cycle time in days
                cycle_time_delta = completion_dt - start_dt
                cycle_time_days = cycle_time_delta.total_seconds() / (24 * 3600)

                # Only include positive cycle times
                if cycle_time_days > 0:
                    cycle_times.append(cycle_time_days)

            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(
                    f"Could not parse timestamps for issue {issue.get('key', 'unknown')}: {e}"
                )
                continue

    # Check if we have data
    if not cycle_times:
        logger.info("Flow Time: No completed issues with valid timestamps found")
        return {
            "value": 0.0,
            "unit": "days",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues with valid cycle times found",
        }

    # Calculate average flow time
    average_flow_time = sum(cycle_times) / len(cycle_times)

    # Calculate trend
    trend = _calculate_trend(average_flow_time, previous_period_value)

    logger.info(
        f"Flow Time: {average_flow_time:.1f} days average ({len(cycle_times)} issues analyzed)"
    )

    return {
        "value": round(average_flow_time, 1),
        "unit": "days",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_efficiency(
    issues: List[Dict],
    extractor: VariableExtractor,
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Efficiency - ratio of active time to total time.

    Flow Efficiency = (Active Time / Total Time) * 100
    Higher efficiency indicates less waste (waiting, blocked time).

    Args:
        issues: List of JIRA issues (must include changelog)
        extractor: Configured VariableExtractor with Flow mappings
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
        f"Calculating flow efficiency for {len(issues)} issues over {time_period_days} days"
    )

    # Extract active and total times from completed issues
    efficiency_values = []

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed
        is_completed_result = extractor.extract_variable(
            "is_completed", issue, changelog
        )

        if not is_completed_result.get("found") or not is_completed_result.get("value"):
            continue

        # Extract active and total time
        active_time_result = extractor.extract_variable("active_time", issue, changelog)
        total_time_result = extractor.extract_variable("total_time", issue, changelog)

        if not active_time_result.get("found") or not total_time_result.get("found"):
            continue

        active_time = active_time_result.get("value")
        total_time = total_time_result.get("value")

        # Type guard: ensure we have numeric values
        if isinstance(active_time, (int, float)) and isinstance(
            total_time, (int, float)
        ):
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
        f"Flow Efficiency: {average_efficiency:.1f}% average ({len(efficiency_values)} issues analyzed)"
    )

    return {
        "value": round(average_efficiency, 1),
        "unit": "%",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }


def calculate_flow_load(
    issues: List[Dict],
    extractor: VariableExtractor,
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Load - number of work items currently in progress (WIP).

    Flow Load measures the current workload on the team. Lower WIP generally
    leads to faster delivery and better quality.

    Args:
        issues: List of JIRA issues (must include changelog)
        extractor: Configured VariableExtractor with Flow mappings
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

    # Count issues currently in progress
    wip_count = 0

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is currently in progress
        is_in_progress_result = extractor.extract_variable(
            "is_in_progress", issue, changelog
        )

        if is_in_progress_result.get("found") and is_in_progress_result.get("value"):
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
    issues: List[Dict],
    extractor: VariableExtractor,
    time_period_days: int = 7,
    previous_period_value: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """Calculate Flow Distribution - breakdown of work by type.

    Flow Distribution shows the percentage of work allocated to Features, Bugs,
    Technical Debt, and Risk items. Recommended distribution:
    - Feature: 40-70%
    - Bug: <10%
    - Technical Debt: 10-20%
    - Risk: 10-20%

    Args:
        issues: List of JIRA issues (must include changelog)
        extractor: Configured VariableExtractor with Flow mappings
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
        f"Calculating flow distribution for {len(issues)} issues over {time_period_days} days"
    )

    # Count completed issues by work type
    distribution_counts = {"Feature": 0, "Bug": 0, "Technical Debt": 0, "Risk": 0}

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed
        is_completed_result = extractor.extract_variable(
            "is_completed", issue, changelog
        )

        if not is_completed_result.get("found") or not is_completed_result.get("value"):
            continue

        # Extract work type category
        work_type_result = extractor.extract_variable(
            "work_type_category", issue, changelog
        )

        # Normalize work type to standard categories
        if work_type_result.get("found"):
            work_type = work_type_result.get("value")
            category = _normalize_work_type(work_type)
            distribution_counts[category] += 1
        else:
            # Default to Feature if work type not found
            distribution_counts["Feature"] += 1

    total_completed = sum(distribution_counts.values())

    # Check if we have data
    if total_completed == 0:
        logger.info("Flow Distribution: No completed issues found")
        return {
            "value": {"Feature": 0.0, "Bug": 0.0, "Technical Debt": 0.0, "Risk": 0.0},
            "unit": "%",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues found in time period",
        }

    # Calculate percentages
    distribution_percentages = {
        work_type: round((count / total_completed) * 100, 1)
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

    logger.info(
        f"Flow Distribution: Feature={distribution_percentages['Feature']}%, "
        f"Bug={distribution_percentages['Bug']}%, "
        f"Tech Debt={distribution_percentages['Technical Debt']}%, "
        f"Risk={distribution_percentages['Risk']}%"
    )

    return {
        "value": distribution_percentages,
        "unit": "%",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }
