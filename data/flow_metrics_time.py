"""Flow Time metric calculation.

Calculates Flow Time (cycle time) from when work starts to when it completes,
using median for outlier resistance (consistent with DORA methodology).

Also contains the shared _calculate_time_in_statuses helper used by Flow
Efficiency (imported via flow_metrics_helpers).
"""

import logging
import statistics
from datetime import UTC, datetime
from typing import Any

from data.flow_metrics_helpers import (
    _calculate_trend,
    _find_first_transition_to_statuses,
    _get_completed_date_field,
    _get_field_mappings,
    _is_issue_completed,
)

logger = logging.getLogger(__name__)


def _calculate_time_in_statuses(
    changelog: list[dict], status_list: list[str], issue_key: str = ""
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
                            f"[FlowEfficiency] {issue_key}: "
                            f"{current_status} period: {duration_hours:.2f}h"
                        )
                except (ValueError, TypeError) as e:
                    logger.debug(f"[FlowEfficiency] {issue_key}: Parse error: {e}")

            # Start tracking new status
            current_status = to_status
            current_start = transition_time

    # If we're still in a tracked status, calculate time up to now
    if current_status in status_list and current_start:
        try:
            now = datetime.now(UTC)
            start_time = datetime.fromisoformat(current_start.replace("Z", "+00:00"))
            duration_hours = (now - start_time).total_seconds() / 3600
            if duration_hours > 0:
                total_hours += duration_hours
                logger.debug(
                    f"[FlowEfficiency] {issue_key}: "
                    f"Still in {current_status}: {duration_hours:.2f}h"
                )
        except (ValueError, TypeError) as e:
            logger.debug(f"[FlowEfficiency] {issue_key}: Final period parse error: {e}")

    if transitions_found == 0:
        logger.debug(
            f"[FlowEfficiency] {issue_key}: No status transitions found in changelog"
        )

    return total_hours


def calculate_flow_time(
    issues: list[dict],
    time_period_days: int = 7,
    previous_period_value: float | None = None,
) -> dict[str, Any]:
    """Calculate Flow Time - median cycle time from start to completion.

    Flow Time measures how long work items take to complete from when work started
    to when they're done. Lower flow time indicates faster delivery.
    Uses median for outlier resistance (consistent with DORA methodology).

    Uses flow_start_statuses (e.g., In Progress, In Review) to find when work started,
    and flow_end_statuses (e.g., Done, Resolved, Closed) to find when work completed.

    Args:
        issues: List of JIRA issues (must include changelog)
        time_period_days: Time period for analysis (default: 7 days)
        previous_period_value: Previous period flow time for trend calculation

    Returns:
        Dictionary with:
        {
            "value": float (median days),
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

    # Check for empty input first (before configuration check)
    if not issues:
        logger.info("Flow Time: No issues provided")
        return {
            "value": 0.0,
            "unit": "days",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No issues provided",
        }

    # Load field mappings and status lists
    flow_mappings, project_classification = _get_field_mappings()

    flow_start_statuses = project_classification.get("flow_start_statuses", [])
    flow_end_statuses = project_classification.get("flow_end_statuses", [])
    completed_date_field = _get_completed_date_field()

    logger.info(
        f"[Flow Time] Configuration loaded: flow_start_statuses={flow_start_statuses}, "
        f"flow_end_statuses={flow_end_statuses}, "
        f"completed_date_field={completed_date_field}"
    )

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
    issues_checked = 0
    issues_completed = 0
    issues_with_start = 0
    issues_with_completion = 0

    for issue in issues:
        issues_checked += 1
        issue_key = issue.get("key", "unknown")
        # Extract changelog for status transition detection
        changelog = issue.get("changelog", {}).get("histories", [])

        # Extract current status and completed date field for debugging
        current_status = (
            issue.get("fields", {}).get("status", {}).get("name", "unknown")
        )
        fields = issue.get("fields", {})
        completed_date_value = fields.get(completed_date_field)

        # Check if issue is completed using field mappings
        is_completed = _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        )

        if issues_checked <= 3:  # Log first 3 issues for debugging
            logger.info(
                f"[Flow Time] Issue {issue_key}: status={current_status}, "
                f"{completed_date_field}={completed_date_value}, "
                f"is_completed={is_completed}, "
                f"has_changelog={len(changelog) > 0}"
            )

        if not is_completed:
            continue

        issues_completed += 1

        # Find first transition to any flow_start_status (work started)
        start_timestamp = _find_first_transition_to_statuses(
            changelog, flow_start_statuses
        )
        # Find first transition to any completion_status (work completed)
        completion_timestamp = _find_first_transition_to_statuses(
            changelog, flow_end_statuses
        )

        if start_timestamp:
            issues_with_start += 1
        if completion_timestamp:
            issues_with_completion += 1

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
                f"Could not parse timestamps for issue "
                f"{issue.get('key', 'unknown')}: {e}"
            )
            continue

    # Check if we have data
    if not cycle_times:
        logger.info(
            f"Flow Time: No completed issues with valid timestamps found "
            f"(checked={issues_checked}, completed={issues_completed}, "
            f"with_start={issues_with_start}, with_completion={issues_with_completion})"
        )
        return {
            "value": 0.0,
            "unit": "days",
            "trend_direction": "stable",
            "trend_percentage": 0.0,
            "error_state": "no_data",
            "error_message": "No completed issues with valid cycle times found",
        }

    # Use MEDIAN for outlier resistance (consistent with DORA methodology)
    median_flow_time = statistics.median(cycle_times)
    mean_flow_time = sum(cycle_times) / len(cycle_times)  # Keep for reference

    # Calculate trend
    trend = _calculate_trend(median_flow_time, previous_period_value)

    logger.info(
        f"Flow Time: {median_flow_time:.1f} days median "
        f"({len(cycle_times)} issues analyzed)"
    )

    return {
        "value": median_flow_time,
        "unit": "days",
        "trend_direction": trend["trend_direction"],
        "trend_percentage": trend["trend_percentage"],
        "error_state": None,
        "error_message": None,
        # Additional statistics for analysis
        "mean_days": mean_flow_time,
    }
