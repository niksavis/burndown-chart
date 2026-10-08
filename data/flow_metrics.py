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

    logger.info(
        f"Calculating flow velocity for {len(issues)} issues "
        f"over {time_period_days} days"
    )

    flow_mappings, project_classification = _get_field_mappings()

    settings = load_app_settings()
    flow_type_mappings = settings.get("flow_type_mappings", {})
    flow_end_statuses = project_classification.get("flow_end_statuses", [])

    completed_date_field = _get_completed_date_field()

    completed_issues = []
    breakdown = {key: 0 for key in flow_type_mappings.keys()}
    if not breakdown:
        breakdown = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}

    for issue in issues:
        changelog = issue.get("changelog", {}).get("histories", [])

        if not _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        ):
            continue

        work_type = _get_work_type_for_issue(issue, flow_mappings, flow_type_mappings)
        if work_type in breakdown:
            breakdown[work_type] += 1
        else:
            logger.debug(
                f"Issue {issue.get('key')} has uncategorized work type: {work_type}"
            )
            breakdown[work_type] = breakdown.get(work_type, 0) + 1
        completed_issues.append(issue)

    total_completed = len(completed_issues)

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

    weeks = time_period_days / 7.0
    velocity = total_completed / weeks if weeks > 0 else 0.0

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

    logger.info(
        f"Calculating flow efficiency for {len(issues)} issues "
        f"over {time_period_days} days"
    )

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

    efficiency_values = []

    for issue in issues:
        changelog = issue.get("changelog", {}).get("histories", [])

        if not _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        ):
            continue

        issue_key = issue.get("key", "unknown")
        active_time = _calculate_time_in_statuses(changelog, active_statuses, issue_key)
        total_time = _calculate_time_in_statuses(changelog, wip_statuses, issue_key)

        logger.debug(
            f"[FlowEfficiency] {issue_key}: "
            f"active={active_time:.2f}h, total={total_time:.2f}h"
        )

        if total_time > 0:
            efficiency = (active_time / total_time) * 100
            efficiency_values.append(min(efficiency, 100))

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

    average_efficiency = sum(efficiency_values) / len(efficiency_values)

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

    logger.info(f"Calculating flow load (WIP) for {len(issues)} issues")

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

    wip_count = 0

    for issue in issues:
        if _is_issue_in_progress(issue, wip_statuses):
            wip_count += 1

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

    logger.info(
        f"Calculating flow distribution for {len(issues)} issues "
        f"over {time_period_days} days"
    )

    flow_mappings, project_classification = _get_field_mappings()

    flow_type_mappings = load_app_settings().get("flow_type_mappings", {})
    flow_end_statuses = project_classification.get("flow_end_statuses", [])

    completed_date_field = _get_completed_date_field()

    logger.info(
        f"Flow Distribution: flow_end_statuses={flow_end_statuses}, "
        f"completed_date_field={completed_date_field}"
    )
    logger.info(f"Flow Distribution: flow_type_mappings={flow_type_mappings}")

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
        changelog = issue.get("changelog", {}).get("histories", [])

        is_completed = _is_issue_completed(
            issue, completed_date_field, changelog, flow_end_statuses
        )

        if is_completed:
            completed_count += 1
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

    distribution_percentages = {
        work_type: (count / total_completed) * 100
        for work_type, count in distribution_counts.items()
    }

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
