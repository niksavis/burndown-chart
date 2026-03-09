"""DORA metric calculations for weekly snapshots."""

import logging
from datetime import datetime

from data.dora_metrics import (
    calculate_change_failure_rate,
    calculate_lead_time_for_changes,
    calculate_mean_time_to_recovery,
)
from data.fixversion_matcher import filter_issues_deployed_in_week
from data.metrics._weekly_dora_prep import (
    count_deployments_for_week,
    filter_bugs_by_resolution_week,
)

logger = logging.getLogger(__name__)


def save_metric_snapshot(*args, **kwargs):  # noqa: PLC0415
    """Lazy wrapper: breaks circular data.metrics -> metrics_snapshots."""
    from data.metrics_snapshots import save_metric_snapshot as _save  # noqa: PLC0415

    return _save(*args, **kwargs)


def _calculate_lead_time(
    development_issues: list,
    fixversion_release_map: dict,
    week_start: datetime,
    week_end: datetime,
    week_label: str,
) -> dict:
    """Calculate Lead Time for Changes snapshot for the given week."""

    try:
        week_dev_issues = filter_issues_deployed_in_week(
            development_issues, fixversion_release_map, week_start, week_end
        )
        logger.info(
            f"Week {week_label}: {len(week_dev_issues)} development issues deployed "
            f"(from {len(development_issues)} total)"
        )

        lead_time_result = calculate_lead_time_for_changes(
            week_dev_issues,
            time_period_days=7,
            fixversion_release_map=fixversion_release_map,
        )

        if lead_time_result:
            no_status_count = lead_time_result.get("no_deployment_status_count", 0)
            no_op_task_count = lead_time_result.get("no_operational_task_count", 0)
            logger.info(
                f"Week {week_label} Lead Time: "
                f"{lead_time_result.get('issues_with_lead_time', 0)} issues matched, "
                f"{no_status_count} no status, {no_op_task_count} no op task, "
                f"{lead_time_result.get('no_deployment_date_count', 0)} no date, "
                f"{lead_time_result.get('excluded_count', 0)} excluded by time"
            )

        if lead_time_result and lead_time_result.get("median_hours"):
            return {
                "median_hours": lead_time_result.get("median_hours", 0),
                "mean_hours": lead_time_result.get("mean_hours", 0),
                "p95_hours": lead_time_result.get("p95_hours", 0),
                "issues_with_lead_time": lead_time_result.get(
                    "issues_with_lead_time", 0
                ),
            }

        logger.info(f"DORA Lead Time: No data for week {week_label}")
        return {
            "median_hours": 0,
            "mean_hours": 0,
            "p95_hours": 0,
            "issues_with_lead_time": 0,
        }

    except Exception as e:
        logger.error(f"Failed to calculate DORA Lead Time: {e}", exc_info=True)
        return {
            "median_hours": 0,
            "mean_hours": 0,
            "p95_hours": 0,
            "issues_with_lead_time": 0,
        }


def _calculate_deployment_frequency(
    operational_tasks: list,
    flow_end_statuses: list[str],
    week_label: str,
    week_start: datetime,
    week_end: datetime,
    development_fix_versions: set,
) -> dict:
    """Calculate Deployment Frequency snapshot for the given week."""

    try:
        weekly_deployments = count_deployments_for_week(
            operational_tasks,
            flow_end_statuses,
            week_label,
            week_start,
            week_end,
            valid_fix_versions=development_fix_versions,
        )
        week_data = weekly_deployments.get(week_label, {})
        return {
            "deployment_count": week_data.get("deployments", 0),
            "release_count": week_data.get("releases", 0),
            "release_names": week_data.get("release_names", []),
            "week": week_label,
        }
    except Exception as e:
        logger.error(
            f"Failed to calculate DORA Deployment Frequency: {e}", exc_info=True
        )
        return {"deployment_count": 0, "week": week_label}


def _calculate_cfr(
    operational_tasks: list,
    production_bugs: list,
    fixversion_release_map: dict,
    development_fix_versions: set,
    week_label: str,
    week_start: datetime,
    week_end: datetime,
) -> dict:
    """Calculate Change Failure Rate snapshot for the given week."""

    try:
        week_operational_tasks = filter_issues_deployed_in_week(
            operational_tasks, fixversion_release_map, week_start, week_end
        )
        logger.info(
            f"Week {week_label}: {len(week_operational_tasks)} operational tasks "
            f"deployed (from {len(operational_tasks)} total) for CFR calculation"
        )

        cfr_result = calculate_change_failure_rate(
            week_operational_tasks,
            production_bugs,
            time_period_days=7,
            valid_fix_versions=development_fix_versions,
        )

        return {
            "change_failure_rate_percent": cfr_result.get(
                "change_failure_rate_percent", 0
            ),
            "total_deployments": cfr_result.get("total_deployments", 0),
            "failed_deployments": cfr_result.get("failed_deployments", 0),
            "total_releases": cfr_result.get("total_releases", 0),
            "failed_releases": cfr_result.get("failed_releases", 0),
            "release_failure_rate_percent": cfr_result.get(
                "release_failure_rate_percent", 0
            ),
            "release_names": cfr_result.get("release_names", []),
            "failed_release_names": cfr_result.get("failed_release_names", []),
            "week": week_label,
        }
    except Exception as e:
        logger.error(f"Failed to calculate DORA CFR: {e}", exc_info=True)
        return {
            "change_failure_rate_percent": 0,
            "total_deployments": 0,
            "failed_deployments": 0,
            "week": week_label,
        }


def _calculate_mttr(
    production_bugs: list,
    fixversion_release_map: dict,
    dora_mappings: dict,
    week_label: str,
    week_start: datetime,
    week_end: datetime,
) -> dict:
    """Calculate Mean Time To Recovery snapshot for the given week."""

    try:
        incident_resolved_field = dora_mappings.get(
            "incident_resolved_at", "resolutiondate"
        )
        use_deployment_date = incident_resolved_field.lower() == "fixversions"

        if use_deployment_date:
            week_bugs = filter_issues_deployed_in_week(
                production_bugs, fixversion_release_map, week_start, week_end
            )
            logger.info(
                f"Week {week_label}: {len(week_bugs)} bugs deployed for MTTR "
                f"(from {len(production_bugs)} total, using fixVersion deployment)"
            )
        else:
            week_bugs = filter_bugs_by_resolution_week(
                production_bugs, week_start, week_end
            )
            logger.info(
                f"Week {week_label}: Filtered {len(week_bugs)} bugs for MTTR "
                f"(from {len(production_bugs)} total, using resolutiondate)"
            )

        mttr_result = calculate_mean_time_to_recovery(
            week_bugs,
            time_period_days=7,
            fixversion_release_map=fixversion_release_map,
        )

        mttr_value = mttr_result.get("value")
        mttr_unit = mttr_result.get("unit", "hours")
        bugs_count = mttr_result.get("incident_count", 0)

        if mttr_value is not None:
            mttr_hours = mttr_value * 24 if mttr_unit == "days" else mttr_value
        else:
            mttr_hours = None

        return {
            "median_hours": mttr_hours,
            "mean_hours": mttr_hours,
            "value": mttr_value,
            "unit": mttr_unit,
            "bugs_with_mttr": bugs_count,
            "performance_tier": mttr_result.get("performance_tier"),
            "week": week_label,
        }
    except Exception as e:
        logger.error(f"Failed to calculate DORA MTTR: {e}", exc_info=True)
        return {"median_hours": None, "bugs_with_mttr": 0, "week": week_label}


def calculate_dora_metrics(
    operational_tasks: list,
    development_issues: list,
    production_bugs: list,
    development_fix_versions: set,
    fixversion_release_map: dict,
    flow_end_statuses: list[str],
    dora_mappings: dict,
    week_label: str,
    week_start: datetime,
    week_end: datetime,
    report_progress,
) -> tuple[int, list[str]]:
    """Calculate and save all DORA metrics for the given week.

    Returns (metrics_saved, metrics_details).
    """

    metrics_saved = 0
    metrics_details: list[str] = []

    # Lead Time for Changes
    lead_time_snapshot = _calculate_lead_time(
        development_issues, fixversion_release_map, week_start, week_end, week_label
    )
    save_metric_snapshot(week_label, "dora_lead_time", lead_time_snapshot)
    metrics_saved += 1
    median_hours = lead_time_snapshot.get("median_hours", 0)
    lead_time_count = lead_time_snapshot.get("issues_with_lead_time", 0)
    if median_hours:
        metrics_details.append(
            f"DORA Lead Time: {median_hours / 24:.1f} days median "
            f"({lead_time_count} issues)"
        )
        logger.info(
            f"Saved DORA Lead Time: {median_hours / 24:.1f} days, "
            f"{lead_time_count} issues"
        )
    else:
        metrics_details.append("DORA Lead Time: No Data")
        logger.info(f"DORA Lead Time: No data for week {week_label}")

    # Deployment Frequency
    deployment_snapshot = _calculate_deployment_frequency(
        operational_tasks,
        flow_end_statuses,
        week_label,
        week_start,
        week_end,
        development_fix_versions,
    )
    save_metric_snapshot(week_label, "dora_deployment_frequency", deployment_snapshot)
    metrics_saved += 1
    deployment_count = deployment_snapshot.get("deployment_count", 0)
    release_count = deployment_snapshot.get("release_count", 0)
    metrics_details.append(
        f"DORA Deployment Frequency: {deployment_count} deployments, "
        f"{release_count} releases"
    )
    logger.info(
        f"Saved DORA Deployment Frequency: "
        f"{deployment_count} deployments, {release_count} releases"
    )

    # Change Failure Rate
    cfr_snapshot = _calculate_cfr(
        operational_tasks,
        production_bugs,
        fixversion_release_map,
        development_fix_versions,
        week_label,
        week_start,
        week_end,
    )
    save_metric_snapshot(week_label, "dora_change_failure_rate", cfr_snapshot)
    metrics_saved += 1
    cfr_percent = cfr_snapshot.get("change_failure_rate_percent", 0)
    failed_deps = cfr_snapshot.get("failed_deployments", 0)
    total_deps = cfr_snapshot.get("total_deployments", 0)
    metrics_details.append(
        f"DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps} deployments)"
    )
    logger.info(f"Saved DORA CFR: {cfr_percent:.1f}% ({failed_deps}/{total_deps})")

    # Mean Time To Recovery
    mttr_snapshot = _calculate_mttr(
        production_bugs,
        fixversion_release_map,
        dora_mappings,
        week_label,
        week_start,
        week_end,
    )
    save_metric_snapshot(week_label, "dora_mttr", mttr_snapshot)
    metrics_saved += 1
    mttr_value = mttr_snapshot.get("value")
    mttr_unit = mttr_snapshot.get("unit", "hours")
    bugs_count = mttr_snapshot.get("bugs_with_mttr", 0)
    if mttr_value is not None:
        metrics_details.append(
            f"DORA MTTR: {mttr_value:.1f} {mttr_unit} ({bugs_count} incidents)"
        )
        logger.info(
            f"Saved DORA MTTR: {mttr_value:.1f} {mttr_unit} ({bugs_count} incidents)"
        )
    else:
        metrics_details.append("DORA MTTR: No data")
        logger.info(f"DORA MTTR: No data for week {week_label}")

    return metrics_saved, metrics_details
