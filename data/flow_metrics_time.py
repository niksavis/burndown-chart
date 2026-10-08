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

    if not changelog or not status_list:
        logger.debug(f"[FlowEfficiency] {issue_key}: No changelog or empty status_list")
        return 0.0

    sorted_changelog = sorted(changelog, key=lambda h: h.get("created", ""))

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

            current_status = to_status
            current_start = transition_time

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

    logger.info(
        f"Calculating flow time for {len(issues)} issues over {time_period_days} days"
    )

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

    flow_mappings, project_classification = _get_field_mappings()

    flow_start_statuses = project_classification.get("flow_start_statuses", [])
    flow_end_statuses = project_classification.get("flow_end_statuses", [])
    completed_date_field = _get_completed_date_field()

    logger.info(
        f"[Flow Time] Configuration loaded: flow_start_statuses={flow_start_statuses}, "
        f"flow_end_statuses={flow_end_statuses}, "
        f"completed_date_field={completed_date_field}"
    )

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

    cycle_times = []
    issues_checked = 0
    issues_completed = 0
    issues_with_start = 0
    issues_with_completion = 0

    for issue in issues:
        issues_checked += 1
        issue_key = issue.get("key", "unknown")
        changelog = issue.get("changelog", {}).get("histories", [])

        current_status = (
            issue.get("fields", {}).get("status", {}).get("name", "unknown")
        )
        fields = issue.get("fields", {})
        completed_date_value = fields.get(completed_date_field)

        is_completed = _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        )

        if issues_checked <= 3:
            logger.info(
                f"[Flow Time] Issue {issue_key}: status={current_status}, "
                f"{completed_date_field}={completed_date_value}, "
                f"is_completed={is_completed}, "
                f"has_changelog={len(changelog) > 0}"
            )

        if not is_completed:
            continue

        issues_completed += 1

        start_timestamp = _find_first_transition_to_statuses(
            changelog, flow_start_statuses
        )
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
            start_dt = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
            completion_dt = datetime.fromisoformat(
                completion_timestamp.replace("Z", "+00:00")
            )

            cycle_time_delta = completion_dt - start_dt
            cycle_time_days = cycle_time_delta.total_seconds() / (24 * 3600)

            if cycle_time_days > 0:
                cycle_times.append(cycle_time_days)

        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(
                f"Could not parse timestamps for issue "
                f"{issue.get('key', 'unknown')}: {e}"
            )
            continue

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

    median_flow_time = statistics.median(cycle_times)
    mean_flow_time = sum(cycle_times) / len(cycle_times)

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
        "mean_days": mean_flow_time,
    }
