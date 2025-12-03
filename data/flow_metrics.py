"""Modern Flow metrics calculator using field mappings.

Calculates the five Flow Framework metrics:
- Flow Velocity: Number of work items completed per time period
- Flow Time: Average cycle time from start to completion
- Flow Efficiency: Ratio of active time to total time
- Flow Load: Number of work items currently in progress (WIP)
- Flow Distribution: Breakdown of work by type (Feature, Bug, Tech Debt, Risk)

This implementation uses field_mappings from user profile configuration.

Architecture:
- Pure business logic with no UI dependencies
- Uses user-configured field mappings (no hardcoded field names)
- Consistent error handling and metric formatting
- Comprehensive logging for debugging and monitoring

Reference: docs/flow_metrics_spec.md
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def _get_field_mappings():
    """Load field mappings and project classification from app settings.

    Returns:
        Tuple of (flow_mappings, project_classification)
    """
    from data.persistence import load_app_settings

    app_settings = load_app_settings()
    field_mappings = app_settings.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})

    # Project classification is flattened to root level by load_app_settings
    # Reconstruct the nested structure for backward compatibility
    project_classification = {
        "flow_end_statuses": app_settings.get("flow_end_statuses", []),
        "active_statuses": app_settings.get("active_statuses", []),
        "wip_statuses": app_settings.get("wip_statuses", []),
        "flow_start_statuses": app_settings.get("flow_start_statuses", []),
        "bug_types": app_settings.get("bug_types", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "production_environment_values": app_settings.get(
            "production_environment_values", []
        ),
    }

    return flow_mappings, project_classification


def _extract_datetime_from_field_mapping(
    issue: Dict[str, Any], field_mapping: str, changelog: Optional[List] = None
) -> Optional[str]:
    """Extract datetime value from issue based on field mapping configuration.

    Supports multiple field mapping formats:
    - Simple field: "created", "resolutiondate"
    - Changelog transition: "status:Done.DateTime"

    Args:
        issue: JIRA issue dictionary
        field_mapping: Field mapping string from profile.json
        changelog: Optional changelog history

    Returns:
        ISO datetime string if found, None otherwise
    """
    if not field_mapping:
        return None

    # Handle changelog transition format
    if ":" in field_mapping and ".DateTime" in field_mapping:
        parts = field_mapping.split(":")
        if len(parts) != 2:
            return None

        field_name = parts[0]
        target_status = parts[1].replace(".DateTime", "")

        if changelog is None:
            changelog = issue.get("changelog", {}).get("histories", [])

        if not isinstance(changelog, list):
            return None

        for history in changelog:
            for item in history.get("items", []):
                if (
                    item.get("field") == field_name
                    and item.get("toString") == target_status
                ):
                    return history.get("created")
        return None

    # Handle simple field paths
    fields = issue.get("fields", {})
    return fields.get(field_mapping)


def _find_first_transition_to_statuses(
    changelog: List[Dict], status_list: List[str]
) -> Optional[str]:
    """Find the first transition to any status in the given list.

    Searches through changelog history to find the earliest timestamp when
    the issue transitioned to any of the specified statuses.

    Args:
        changelog: Issue changelog history (list of history entries)
        status_list: List of status names to look for (e.g., flow_start_statuses)

    Returns:
        ISO datetime string of first transition to any status in list, None if not found
    """
    if not changelog or not status_list:
        return None

    # Sort changelog chronologically to find FIRST transition
    sorted_changelog = sorted(changelog, key=lambda h: h.get("created", ""))

    for history in sorted_changelog:
        for item in history.get("items", []):
            if item.get("field") == "status" and item.get("toString") in status_list:
                return history.get("created")

    return None


def _is_issue_completed(
    issue: Dict[str, Any], completed_date_field: str, changelog: Optional[List] = None
) -> bool:
    """Check if issue is completed by checking if completed_date field has a value.

    Args:
        issue: JIRA issue dictionary
        completed_date_field: Field mapping for completion date
        changelog: Optional changelog history

    Returns:
        True if issue has a completion date
    """
    completed_date = _extract_datetime_from_field_mapping(
        issue, completed_date_field, changelog
    )
    return completed_date is not None


def _is_issue_in_progress(issue: Dict[str, Any], wip_statuses: List[str]) -> bool:
    """Check if issue is currently in progress based on WIP statuses.

    Args:
        issue: JIRA issue dictionary
        wip_statuses: List of status names that indicate WIP

    Returns:
        True if issue status is in wip_statuses
    """
    status = issue.get("fields", {}).get("status", {}).get("name", "")
    return status in wip_statuses


def _get_work_type_for_issue(
    issue: Dict[str, Any], flow_mappings: Dict, flow_type_mappings: Dict
) -> str:
    """Classify issue into work type category using field mappings.

    Uses the same logic as metrics_calculator.py lines 651-716.

    Args:
        issue: JIRA issue dictionary
        flow_mappings: Flow field mappings
        flow_type_mappings: Work type classification mappings

    Returns:
        Work type: "Feature", "Defect", "Technical Debt", or "Risk"
    """
    from configuration.metrics_config import get_metrics_config

    fields = issue.get("fields", {})

    # Extract issue type
    flow_type_field = flow_mappings.get("flow_item_type", "issuetype")
    issue_type_value = fields.get(flow_type_field)
    if isinstance(issue_type_value, dict):
        issue_type = issue_type_value.get("name") or issue_type_value.get("value", "")
    else:
        issue_type = str(issue_type_value) if issue_type_value else ""

    # Extract effort category (optional)
    effort_category = None
    effort_category_field = flow_mappings.get("effort_category")
    if effort_category_field:
        effort_value = fields.get(effort_category_field)
        if isinstance(effort_value, dict):
            effort_category = effort_value.get("value") or effort_value.get("name")
        else:
            effort_category = str(effort_value) if effort_value else None

    # Use configured classification
    config = get_metrics_config()
    flow_type = config.get_flow_type_for_issue(issue_type, effort_category)
    return flow_type if flow_type else "Feature"


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
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Velocity - completed items per time period.

    Flow Velocity measures team throughput by counting completed work items.
    Higher velocity indicates higher team productivity.

    Args:
        issues: List of JIRA issues (must include changelog)
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
        >>> velocity = calculate_flow_velocity(issues, time_period_days=7)
        >>> print(f"Velocity: {velocity['value']} {velocity['unit']}")
        Velocity: 12.5 items/week
    """
    logger.info(
        f"Calculating flow velocity for {len(issues)} issues over {time_period_days} days"
    )

    # Load field mappings
    flow_mappings, project_classification = _get_field_mappings()
    from data.persistence import load_app_settings

    flow_type_mappings = load_app_settings().get("flow_type_mappings", {})

    completed_date_field = flow_mappings.get("completed_date", "resolutiondate")

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
        if not _is_issue_completed(issue, completed_date_field, changelog):
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
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate Flow Time - average cycle time from start to completion.

    Flow Time measures how long work items take to complete from when work started
    to when they're done. Lower flow time indicates faster delivery.

    Uses flow_start_statuses (e.g., In Progress, In Review) to find when work started,
    and flow_end_statuses (e.g., Done, Resolved, Closed) to find when work completed.

    Args:
        issues: List of JIRA issues (must include changelog)
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

    # Load field mappings and status lists
    flow_mappings, project_classification = _get_field_mappings()

    flow_start_statuses = project_classification.get("flow_start_statuses", [])
    flow_end_statuses = project_classification.get("flow_end_statuses", [])
    completed_date_field = flow_mappings.get("completed_date", "resolutiondate")

    # Validate required configuration
    if not flow_start_statuses:
        logger.warning("Flow Time: Missing flow_start_statuses configuration")
        return {
            "value": 0.0,
            "unit": "days",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "missing_mapping",
            "error_message": "Missing flow_start_statuses configuration",
        }

    if not flow_end_statuses:
        logger.warning("Flow Time: Missing flow_end_statuses configuration")
        return {
            "value": 0.0,
            "unit": "days",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "missing_mapping",
            "error_message": "Missing flow_end_statuses configuration",
        }

    # Extract cycle times from completed issues
    cycle_times = []

    for issue in issues:
        # Extract changelog for status transition detection
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed using field mappings
        if not _is_issue_completed(issue, completed_date_field, changelog):
            continue

        # Find first transition to any flow_start_status (work started)
        start_timestamp = _find_first_transition_to_statuses(
            changelog, flow_start_statuses
        )
        # Find first transition to any completion_status (work completed)
        completion_timestamp = _find_first_transition_to_statuses(
            changelog, flow_end_statuses
        )

        if not start_timestamp or not completion_timestamp:
            continue

        try:
            # Parse timestamps
            start_dt = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
            completion_dt = datetime.fromisoformat(
                completion_timestamp.replace("Z", "+00:00")
            )

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


def _calculate_time_in_statuses(
    changelog: List[Dict], status_list: List[str], issue_key: str = ""
) -> float:
    """Calculate total time spent in specific statuses from changelog.

    Args:
        changelog: Issue changelog history
        status_list: List of status names to track (e.g., active_statuses)
        issue_key: Optional issue key for debug logging

    Returns:
        Total time in hours spent in these statuses
    """
    if not changelog or not status_list:
        logger.debug(f"[FlowEfficiency] {issue_key}: No changelog or empty status_list")
        return 0.0

    # Sort changelog chronologically
    sorted_changelog = sorted(changelog, key=lambda h: h.get("created", ""))

    # Track status transitions
    total_hours = 0.0
    current_status = None
    current_start = None
    transitions_found = 0

    for history in sorted_changelog:
        for item in history.get("items", []):
            if item.get("field") != "status":
                continue

            transitions_found += 1
            to_status = item.get("toString")
            transition_time = history.get("created")

            # Close previous period if we were in a tracked status
            if current_status in status_list and current_start and transition_time:
                try:
                    end_time = datetime.fromisoformat(
                        transition_time.replace("Z", "+00:00")
                    )
                    start_time = datetime.fromisoformat(
                        current_start.replace("Z", "+00:00")
                    )
                    duration_hours = (end_time - start_time).total_seconds() / 3600
                    if duration_hours > 0:
                        total_hours += duration_hours
                        logger.debug(
                            f"[FlowEfficiency] {issue_key}: {current_status} period: {duration_hours:.2f}h"
                        )
                except (ValueError, TypeError) as e:
                    logger.debug(f"[FlowEfficiency] {issue_key}: Parse error: {e}")

            # Start tracking new status
            current_status = to_status
            current_start = transition_time

    # If we're still in a tracked status, calculate time up to now
    if current_status in status_list and current_start:
        try:
            from datetime import timezone

            now = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(current_start.replace("Z", "+00:00"))
            duration_hours = (now - start_time).total_seconds() / 3600
            if duration_hours > 0:
                total_hours += duration_hours
                logger.debug(
                    f"[FlowEfficiency] {issue_key}: Still in {current_status}: {duration_hours:.2f}h"
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"[FlowEfficiency] {issue_key}: Final period parse error: {e}")

    if transitions_found == 0:
        logger.debug(
            f"[FlowEfficiency] {issue_key}: No status transitions found in changelog"
        )

    return total_hours


def calculate_flow_efficiency(
    issues: List[Dict],
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
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
        f"Calculating flow efficiency for {len(issues)} issues over {time_period_days} days"
    )

    # Load field mappings
    flow_mappings, project_classification = _get_field_mappings()

    active_statuses = project_classification.get("active_statuses", [])
    wip_statuses = project_classification.get("wip_statuses", [])
    completed_date_field = flow_mappings.get("completed_date", "resolutiondate")

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
        if not _is_issue_completed(issue, completed_date_field, changelog):
            continue

        # Calculate active time and total WIP time from changelog
        issue_key = issue.get("key", "unknown")
        active_time = _calculate_time_in_statuses(changelog, active_statuses, issue_key)
        total_time = _calculate_time_in_statuses(changelog, wip_statuses, issue_key)

        logger.debug(
            f"[FlowEfficiency] {issue_key}: active={active_time:.2f}h, total={total_time:.2f}h"
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
    time_period_days: int = 7,
    previous_period_value: Optional[float] = None,
) -> Dict[str, Any]:
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
    issues: List[Dict],
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

    # Load field mappings
    flow_mappings, _ = _get_field_mappings()
    from data.persistence import load_app_settings

    flow_type_mappings = load_app_settings().get("flow_type_mappings", {})

    completed_date_field = flow_mappings.get("completed_date", "resolutiondate")

    # Initialize distribution counts from configured flow types
    distribution_counts = {key: 0 for key in flow_type_mappings.keys()}
    if not distribution_counts:
        distribution_counts = {
            "Feature": 0,
            "Defect": 0,
            "Technical Debt": 0,
            "Risk": 0,
        }

    for issue in issues:
        # Extract changelog for variable extraction
        changelog = issue.get("changelog", {}).get("histories", [])

        # Check if issue is completed using field mappings
        if not _is_issue_completed(issue, completed_date_field, changelog):
            continue

        # Extract work type category using field mappings
        work_type = _get_work_type_for_issue(issue, flow_mappings, flow_type_mappings)
        if work_type in distribution_counts:
            distribution_counts[work_type] += 1
        else:
            distribution_counts[work_type] = distribution_counts.get(work_type, 0) + 1

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

    logger.info(f"Flow Distribution: {distribution_percentages}")

    return {
        "value": distribution_percentages,
        "unit": "%",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
    }
