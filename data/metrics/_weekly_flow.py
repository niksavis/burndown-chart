"""Flow metrics calculation for weekly snapshots."""

import logging
from datetime import UTC, datetime

from configuration.metrics_config import get_metrics_config
from data.changelog_processor import (
    get_first_status_transition_timestamp,
    get_status_at_point_in_time,
)
from data.flow_metrics import calculate_flow_efficiency, calculate_flow_time
from data.metrics_snapshots import save_metric_snapshot

logger = logging.getLogger(__name__)


def _compute_wip_at_week_end(
    all_issues: list,
    wip_statuses: list[str],
    flow_end_statuses: list[str],
    week_start: datetime,
    week_end: datetime,
    is_current_week: bool,
    completion_cutoff: datetime,
    week_label: str,
) -> dict:
    """Build the Flow Load result dict from historical WIP reconstruction."""

    issues_in_wip_at_week_end = []
    week_end_check_time = completion_cutoff

    for issue in all_issues:
        if is_current_week:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                current_status = issue["fields"].get("status", {}).get("name", "")
            else:
                current_status = issue.get("status", "")

            is_in_wip_now = current_status in wip_statuses
            is_completed = current_status in flow_end_statuses

            if is_in_wip_now and not is_completed:
                issues_in_wip_at_week_end.append(issue)
                issue_ref = issue.get("key", issue.get("issue_key"))
                logger.debug(
                    f"[WIP Current Week] {issue_ref}: "
                    f"status='{current_status}', "
                    f"is_in_wip={is_in_wip_now}, is_completed={is_completed}"
                )
        else:
            status_at_week_end = get_status_at_point_in_time(issue, week_end_check_time)
            logger.debug(
                f"[WIP Historical] {issue.get('key', issue.get('issue_key'))}: "
                f"status_at_week_end='{status_at_week_end}', "
                f"week_end={week_end_check_time.date()}"
            )
            is_completed_at_week_end = status_at_week_end in flow_end_statuses
            if (
                status_at_week_end
                and status_at_week_end in wip_statuses
                and not is_completed_at_week_end
            ):
                issues_in_wip_at_week_end.append(issue)
                issue_ref = issue.get("key", issue.get("issue_key"))
                logger.debug(
                    f"[WIP Historical] {issue_ref}: "
                    f"IN WIP at week end (status='{status_at_week_end}')"
                )

    by_status: dict[str, int] = {}
    by_issue_type: dict[str, int] = {}

    for issue in issues_in_wip_at_week_end:
        if is_current_week:
            if "fields" in issue and isinstance(issue.get("fields"), dict):
                issue_wip_status = issue["fields"].get("status", {}).get("name", "")
            else:
                issue_wip_status = issue.get("status", "")
        else:
            issue_wip_status = None
            latest_wip_time = None
            for wip_status in wip_statuses:
                timestamp = get_first_status_transition_timestamp(issue, wip_status)
                if timestamp:
                    timestamp = timestamp.astimezone(UTC).replace(tzinfo=None)
                    if timestamp < week_end_check_time:
                        if latest_wip_time is None or timestamp > latest_wip_time:
                            latest_wip_time = timestamp
                            issue_wip_status = wip_status

        if issue_wip_status:
            by_status[issue_wip_status] = by_status.get(issue_wip_status, 0) + 1

        if "fields" in issue and isinstance(issue.get("fields"), dict):
            issue_type = issue["fields"].get("issuetype", {}).get("name", "Unknown")
        else:
            issue_type = issue.get("issue_type", issue.get("issuetype", "Unknown"))

        by_issue_type[issue_type] = by_issue_type.get(issue_type, 0) + 1

    wip_time_desc = (
        "now (running)" if is_current_week else f"at {week_end_check_time.date()}"
    )
    wip_period_label = "Current" if is_current_week else "Historical"
    logger.info(
        f"{wip_period_label} WIP for week {week_label}: "
        f"{len(issues_in_wip_at_week_end)} items were in active work {wip_time_desc}"
    )
    logger.info(f"WIP breakdown by status: {by_status}")
    logger.info(f"WIP breakdown by issue type: {by_issue_type}")

    return {
        "metric_name": "flow_load",
        "wip_count": len(issues_in_wip_at_week_end),
        "by_status": by_status,
        "by_issue_type": by_issue_type,
        "unit": "items",
        "error_state": "success",
        "error_message": None,
    }


def _compute_work_distribution(issues_completed: list, app_settings: dict) -> dict:
    """Compute work distribution by flow type for completed issues."""

    field_mappings = app_settings.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})
    flow_type_field = flow_mappings.get("flow_item_type", "issuetype")
    effort_category_field = flow_mappings.get("effort_category")

    if not effort_category_field:
        logger.warning(
            "effort_category field not configured, "
            "classification will use issue type only"
        )

    config = get_metrics_config()
    distribution: dict[str, int] = {
        "feature": 0,
        "defect": 0,
        "risk": 0,
        "tech_debt": 0,
    }

    for issue in issues_completed:
        if "fields" in issue and isinstance(issue.get("fields"), dict):
            fields = issue.get("fields", {})
        else:
            fields = issue.copy()
            if "custom_fields" in issue and isinstance(
                issue.get("custom_fields"), dict
            ):
                fields.update(issue.get("custom_fields", {}))

        issue_type_value = fields.get(flow_type_field)
        if not issue_type_value and flow_type_field == "issuetype":
            issue_type_value = fields.get("issue_type")

        if isinstance(issue_type_value, dict):
            issue_type = issue_type_value.get("name") or issue_type_value.get(
                "value", ""
            )
        else:
            issue_type = str(issue_type_value) if issue_type_value else ""

        effort_category = None
        if effort_category_field:
            effort_value = fields.get(effort_category_field)
            if isinstance(effort_value, dict):
                effort_category = effort_value.get("value") or effort_value.get("name")
            else:
                effort_category = str(effort_value) if effort_value else None

        flow_type = config.get_flow_type_for_issue(issue_type, effort_category)

        if flow_type == "Feature":
            distribution["feature"] += 1
        elif flow_type == "Defect":
            distribution["defect"] += 1
        elif flow_type == "Risk":
            distribution["risk"] += 1
        elif flow_type == "Technical Debt":
            distribution["tech_debt"] += 1
        else:
            logger.warning(
                f"[Work Distribution] Unknown flow type '{flow_type}' "
                f"for issue {issue.get('key', issue.get('issue_key'))} "
                f"(issue_type='{issue_type}')"
            )

    return distribution


def calculate_flow_metrics(
    issues_completed: list,
    all_issues: list,
    changelog_available: bool,
    wip_statuses: list[str],
    flow_end_statuses: list[str],
    week_start: datetime,
    week_end: datetime,
    is_current_week: bool,
    completion_cutoff: datetime,
    app_settings: dict,
    week_label: str,
    report_progress,
) -> tuple[int, list[str]]:
    """Calculate and save all Flow metrics for the given week.

    Returns (metrics_saved, metrics_details).
    """

    metrics_saved = 0
    metrics_details: list[str] = []

    if changelog_available:
        report_progress("[Stats] Calculating Flow Time metric...")

        flow_time_result = calculate_flow_time(issues_completed, time_period_days=7)
    else:
        logger.info("Skipping Flow Time (requires changelog data)")
        flow_time_result = None

    if changelog_available:
        report_progress("[Stats] Calculating Flow Efficiency metric...")

        efficiency_result = calculate_flow_efficiency(
            issues_completed, time_period_days=7
        )
    else:
        logger.info("Skipping Flow Efficiency (requires changelog data)")
        efficiency_result = None

    report_progress("[Stats] Calculating Flow Load metric...")
    logger.info(
        f"[Flow Load] Starting calculation for week {week_label}: "
        f"wip_statuses={wip_statuses}, is_current_week={is_current_week}"
    )
    load_result = _compute_wip_at_week_end(
        all_issues,
        wip_statuses,
        flow_end_statuses,
        week_start,
        week_end,
        is_current_week,
        completion_cutoff,
        week_label,
    )

    report_progress("[Stats] Calculating Flow Velocity...")
    velocity_count = len(issues_completed)
    logger.info(
        f"Flow Velocity: {velocity_count} items completed in week {week_label} "
        f"({week_start.date()} to {week_end.date()})"
    )

    # Save Flow Time
    if flow_time_result is not None:
        flow_time_error = flow_time_result.get("error_state")
        if flow_time_error is None:
            avg_days = flow_time_result.get("value", 0)
            completed = len(issues_completed)
            flow_time_snapshot = {
                "median_days": avg_days,
                "avg_days": avg_days,
                "p85_days": 0,
                "completed_count": completed,
            }
            save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
            metrics_saved += 1
            metrics_details.append(
                f"Flow Time: {avg_days:.1f} days avg ({completed} issues)"
            )
            logger.info(f"Saved Flow Time: avg {avg_days:.1f} days, {completed} issues")
        else:
            flow_time_snapshot = {
                "median_days": 0,
                "avg_days": 0,
                "p85_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
            metrics_saved += 1
            error_msg = flow_time_result.get("error_message", "Unknown error")
            metrics_details.append("Flow Time: N/A (0 completed issues)")
            logger.warning(
                f"Flow Time calculation failed: {flow_time_error} - {error_msg}"
            )
    else:
        flow_time_snapshot = {
            "median_days": 0,
            "avg_days": 0,
            "p85_days": 0,
            "completed_count": 0,
        }
        save_metric_snapshot(week_label, "flow_time", flow_time_snapshot)
        metrics_saved += 1
        metrics_details.append("Flow Time: Skipped (no changelog data)")
        logger.info("Flow Time: Skipped (changelog not available)")

    # Save Flow Efficiency
    if efficiency_result is not None:
        efficiency_error = efficiency_result.get("error_state")
        if efficiency_error is None:
            efficiency_pct = efficiency_result.get("value", 0)
            completed = len(issues_completed)
            efficiency_snapshot = {
                "overall_pct": efficiency_pct,
                "median_pct": efficiency_pct,
                "avg_active_days": 0,
                "avg_waiting_days": 0,
                "completed_count": completed,
            }
            save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
            metrics_saved += 1
            metrics_details.append(
                f"Flow Efficiency: {efficiency_pct:.1f}% ({completed} issues)"
            )
            logger.info(
                f"Saved Flow Efficiency: {efficiency_pct:.1f}%, {completed} issues"
            )
        else:
            efficiency_snapshot = {
                "overall_pct": 0,
                "median_pct": 0,
                "avg_active_days": 0,
                "avg_waiting_days": 0,
                "completed_count": 0,
            }
            save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
            metrics_saved += 1
            error_msg = efficiency_result.get("error_message", "Unknown error")
            metrics_details.append("Flow Efficiency: N/A (0 completed issues)")
            logger.warning(
                f"Flow Efficiency calculation failed: {efficiency_error} - {error_msg}"
            )
    else:
        efficiency_snapshot = {
            "overall_pct": 0,
            "median_pct": 0,
            "avg_active_days": 0,
            "avg_waiting_days": 0,
            "completed_count": 0,
        }
        save_metric_snapshot(week_label, "flow_efficiency", efficiency_snapshot)
        metrics_saved += 1
        metrics_details.append("Flow Efficiency: Skipped (no changelog data)")
        logger.info("Flow Efficiency: Skipped (changelog not available)")

    # Save Flow Load
    load_error = load_result.get("error_state")
    if load_error == "success":
        wip = load_result.get("wip_count", 0)
        load_snapshot = {
            "wip_count": wip,
            "by_status": load_result.get("by_status", {}),
            "by_issue_type": load_result.get("by_issue_type", {}),
        }
        save_metric_snapshot(week_label, "flow_load", load_snapshot)
        metrics_saved += 1
        metrics_details.append(f"Flow Load: {wip} items in progress")
        logger.info(f"Saved Flow Load: {wip} items")
    else:
        error_msg = load_result.get("error_message", "Unknown error")
        metrics_details.append(f"Flow Load: [!] {error_msg}")
        logger.warning(f"Flow Load calculation failed: {load_error} - {error_msg}")

    # Work Distribution and Velocity
    report_progress("[Stats] Categorizing work distribution...")
    logger.info(
        f"[Work Distribution] Starting calculation for week {week_label}: "
        f"{len(issues_completed)} completed issues"
    )

    field_mappings = app_settings.get("field_mappings", {})
    flow_mappings = field_mappings.get("flow", {})
    flow_type_field = flow_mappings.get("flow_item_type", "issuetype")
    effort_category_field = flow_mappings.get("effort_category")
    logger.info(
        f"[Work Distribution] Configuration: flow_type_field='{flow_type_field}', "
        f"effort_category_field='{effort_category_field}'"
    )

    distribution = _compute_work_distribution(issues_completed, app_settings)
    logger.info(
        f"Work distribution for week {week_label}: "
        f"Features={distribution['feature']}, Defects={distribution['defect']}, "
        f"Tech Debt={distribution['tech_debt']}, Risk={distribution['risk']}"
    )

    velocity_snapshot = {
        "completed_count": velocity_count,
        "week": week_label,
        "distribution": distribution,
    }
    save_metric_snapshot(week_label, "flow_velocity", velocity_snapshot)
    metrics_saved += 1
    metrics_details.append(f"Flow Velocity: {velocity_count} items completed")
    logger.info(
        f"Saved Flow Velocity: {velocity_count} items completed in week {week_label}"
    )

    return metrics_saved, metrics_details
