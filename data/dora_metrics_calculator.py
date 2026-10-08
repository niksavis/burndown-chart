import logging
from datetime import UTC, datetime
from typing import Any

from data.dora_metrics import (
    calculate_change_failure_rate,
    calculate_deployment_frequency,
    calculate_lead_time_for_changes,
    calculate_mean_time_to_recovery,
)
from data.iso_week_bucketing import get_last_n_weeks
from data.metrics_snapshots import get_metric_snapshot, save_metric_snapshot

logger = logging.getLogger(__name__)


def calculate_and_save_dora_weekly_metrics(
    week_label: str,
    monday,
    sunday,
    operational_tasks: list[dict],
    development_issues: list[dict],
    production_bugs: list[dict],
    production_value: str,
) -> tuple[bool, str]:

    try:
        all_issues = operational_tasks + development_issues + production_bugs

        logger.info(
            f"Week {week_label}: Calculating deployment frequency with "
            f"{len(all_issues)} issues"
        )
        deployment_freq = calculate_deployment_frequency(
            all_issues,
            time_period_days=7,
        )
        logger.info(
            f"Week {week_label}: Deployment frequency result: "
            f"{deployment_freq.get('deployment_count', 0)} deployments"
        )

        lead_time = calculate_lead_time_for_changes(
            all_issues,
            time_period_days=7,
        )

        if lead_time.get("value") is None:
            logger.info(
                f"Week {week_label}: No lead time data "
                f"(checked {len(all_issues)} issues)"
            )

        cfr = calculate_change_failure_rate(
            operational_tasks,
            production_bugs,
            time_period_days=7,
        )

        mttr = calculate_mean_time_to_recovery(
            production_bugs,
            time_period_days=7,
        )

        save_metric_snapshot(
            week_label,
            "dora_deployment_frequency",
            {
                "deployment_count": deployment_freq.get("deployment_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        lead_time_value = lead_time.get("value")
        lead_time_hours = lead_time_value * 24 if lead_time_value is not None else None

        save_metric_snapshot(
            week_label,
            "dora_lead_time",
            {
                "median_hours": lead_time_hours,
                "mean_hours": lead_time_hours,
                "p95_hours": lead_time_hours,
                "issues_with_lead_time": lead_time.get("sample_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_change_failure_rate",
            {
                "change_failure_rate_percent": cfr.get("value", 0),
                "total_deployments": cfr.get("deployment_count", 0),
                "failed_deployments": cfr.get("incident_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        save_metric_snapshot(
            week_label,
            "dora_mttr",
            {
                "median_hours": mttr.get("value"),
                "mean_hours": mttr.get("value"),
                "p95_hours": mttr.get("value"),
                "bugs_with_mttr": mttr.get("incident_count", 0),
                "week_label": week_label,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        return True, f"Week {week_label} calculated successfully"

    except Exception as e:
        error_msg = f"Error calculating DORA metrics for {week_label}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg


def load_dora_metrics_from_cache(n_weeks: int = 12) -> dict[str, Any] | None:

    try:
        from data.metrics_snapshots import load_snapshots  # noqa: PLC0415

        snapshots = load_snapshots()

        dora_weeks = sorted(
            wk
            for wk, metrics in snapshots.items()
            if any(k.startswith("dora_") for k in metrics)
        )

        if dora_weeks:
            selected_week_labels = dora_weeks[-n_weeks:]
        else:
            selected_week_labels = [label for label, _, _ in get_last_n_weeks(n_weeks)]

        weekly_labels = []
        weekly_deployment_freq = []
        weekly_release_freq = []
        weekly_lead_time = []
        weekly_cfr = []
        weekly_cfr_releases = []
        weekly_mttr = []

        total_deployments = 0
        total_releases = 0
        all_lead_times = []
        all_lead_times_p95 = []
        all_lead_times_mean = []
        total_cfr_numerator = 0
        total_cfr_denominator = 0
        total_cfr_failed_releases = 0
        total_cfr_total_releases = 0
        all_mttr_values = []
        all_mttr_p95 = []
        all_mttr_mean = []

        total_lead_time_issues = 0
        total_deployment_issues = 0
        total_cfr_issues = 0
        total_mttr_issues = 0

        has_any_data = False

        for week_label in selected_week_labels:
            weekly_labels.append(week_label)

            df_data = get_metric_snapshot(week_label, "dora_deployment_frequency")
            lt_data = get_metric_snapshot(week_label, "dora_lead_time")
            cfr_data = get_metric_snapshot(week_label, "dora_change_failure_rate")
            mttr_data = get_metric_snapshot(week_label, "dora_mttr")

            if df_data or lt_data or cfr_data or mttr_data:
                has_any_data = True

            df_count = df_data.get("deployment_count", 0) if df_data else 0
            release_count = df_data.get("release_count", 0) if df_data else 0
            weekly_deployment_freq.append(df_count)
            weekly_release_freq.append(release_count)
            total_deployments += df_count
            total_releases += release_count
            if df_count > 0:
                total_deployment_issues += df_count

            lt_hours = lt_data.get("median_hours") if lt_data else None
            lt_p95_hours = lt_data.get("p95_hours") if lt_data else None
            lt_mean_hours = lt_data.get("mean_hours") if lt_data else None
            lt_count = lt_data.get("issues_with_lead_time", 0) if lt_data else 0
            logger.info(
                f"[LOAD_CACHE] Week {week_label}: lt_data={lt_data}, "
                f"lt_hours={lt_hours}"
            )
            lt_days = lt_hours / 24 if lt_hours else 0
            weekly_lead_time.append(lt_days)

            if lt_count > 0:
                total_lead_time_issues += lt_count

            if lt_hours is not None and lt_hours > 0:
                all_lead_times.append(lt_hours)
                if lt_p95_hours is not None:
                    all_lead_times_p95.append(lt_p95_hours)
                if lt_mean_hours is not None:
                    all_lead_times_mean.append(lt_mean_hours)
                logger.info(
                    f"[LOAD_CACHE] Week {week_label}: Added {lt_hours}h to "
                    f"all_lead_times (total: {len(all_lead_times)})"
                )

            cfr_percent = (
                cfr_data.get("change_failure_rate_percent", 0) if cfr_data else 0
            )
            weekly_cfr.append(cfr_percent)
            cfr_release_percent = (
                cfr_data.get("release_failure_rate_percent", 0) if cfr_data else 0
            )
            weekly_cfr_releases.append(cfr_release_percent)

            if cfr_data:
                total_cfr_numerator += cfr_data.get("failed_deployments", 0)
                total_cfr_denominator += cfr_data.get("total_deployments", 0)
                total_cfr_issues += cfr_data.get("total_deployments", 0)
                total_cfr_failed_releases += cfr_data.get("failed_releases", 0)
                total_cfr_total_releases += cfr_data.get("total_releases", 0)

            mttr_hours = mttr_data.get("median_hours") if mttr_data else None
            mttr_p95_hours = mttr_data.get("p95_hours") if mttr_data else None
            mttr_mean_hours = mttr_data.get("mean_hours") if mttr_data else None
            mttr_count = mttr_data.get("bugs_with_mttr", 0) if mttr_data else 0
            weekly_mttr.append(mttr_hours if mttr_hours else 0)

            if mttr_count > 0:
                total_mttr_issues += mttr_count

            if mttr_hours:
                all_mttr_values.append(mttr_hours)
                if mttr_p95_hours is not None:
                    all_mttr_p95.append(mttr_p95_hours)
                if mttr_mean_hours is not None:
                    all_mttr_mean.append(mttr_mean_hours)

        deployment_freq_per_week = (
            total_deployments / len(selected_week_labels)
            if len(selected_week_labels) > 0
            else 0
        )
        release_freq_per_week = (
            total_releases / len(selected_week_labels)
            if len(selected_week_labels) > 0
            else 0
        )

        logger.info(f"[LOAD_CACHE] all_lead_times list: {all_lead_times}")
        import statistics  # noqa: PLC0415

        overall_lead_time = (
            statistics.median(all_lead_times) if all_lead_times else None
        )
        overall_lead_time_p95 = (
            statistics.median(all_lead_times_p95) if all_lead_times_p95 else None
        )
        overall_lead_time_mean = (
            statistics.median(all_lead_times_mean) if all_lead_times_mean else None
        )
        logger.info(f"[LOAD_CACHE] overall_lead_time (hours): {overall_lead_time}")
        overall_cfr = (
            (total_cfr_numerator / total_cfr_denominator * 100)
            if total_cfr_denominator > 0
            else 0
        )
        overall_cfr_releases = (
            (total_cfr_failed_releases / total_cfr_total_releases * 100)
            if total_cfr_total_releases > 0
            else 0
        )
        overall_mttr = statistics.median(all_mttr_values) if all_mttr_values else None
        overall_mttr_p95 = statistics.median(all_mttr_p95) if all_mttr_p95 else None
        overall_mttr_mean = statistics.median(all_mttr_mean) if all_mttr_mean else None

        if not has_any_data:
            logger.info("No DORA metrics found in cache")
            return None

        return {
            "deployment_frequency": {
                "value": round(deployment_freq_per_week, 2),
                "release_value": round(release_freq_per_week, 2),
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_deployment_freq,
                "weekly_release_values": weekly_release_freq,
                "total_issue_count": total_deployment_issues,
            },
            "lead_time_for_changes": {
                "value": overall_lead_time / 24
                if overall_lead_time is not None
                else None,
                "value_hours": overall_lead_time
                if overall_lead_time is not None
                else None,
                "value_days": overall_lead_time / 24
                if overall_lead_time is not None
                else None,
                "p95_value": overall_lead_time_p95 / 24
                if overall_lead_time_p95 is not None
                else None,
                "mean_value": overall_lead_time_mean / 24
                if overall_lead_time_mean is not None
                else None,
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_lead_time,
                "total_issue_count": total_lead_time_issues,
            },
            "change_failure_rate": {
                "value": overall_cfr,
                "release_value": overall_cfr_releases,
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_cfr,
                "weekly_release_values": weekly_cfr_releases,
                "total_issue_count": total_cfr_issues,
            },
            "mean_time_to_recovery": {
                "value": overall_mttr if overall_mttr else None,
                "value_hours": overall_mttr if overall_mttr is not None else None,
                "value_days": overall_mttr / 24 if overall_mttr is not None else None,
                "p95_value": overall_mttr_p95 if overall_mttr_p95 is not None else None,
                "mean_value": overall_mttr_mean
                if overall_mttr_mean is not None
                else None,
                "weekly_labels": weekly_labels,
                "weekly_values": weekly_mttr,
                "total_issue_count": total_mttr_issues,
            },
        }

    except Exception as e:
        logger.error(f"Error loading DORA metrics from cache: {e}", exc_info=True)
        return None


def calculate_and_save_dora_metrics_for_all_issues(
    week_label: str,
    monday,
    sunday,
    all_issues: list[dict],
) -> tuple[bool, str]:

    try:
        start_date = datetime.combine(monday, datetime.min.time()).replace(tzinfo=UTC)
        end_date = datetime.combine(sunday, datetime.max.time()).replace(tzinfo=UTC)
        time_period_days = (end_date - start_date).days

        logger.info(
            f"Week {week_label}: Calculating DORA metrics "
            f"({len(all_issues)} issues, {time_period_days} days)"
        )

        deployment_freq = calculate_deployment_frequency(
            all_issues,
            time_period_days=time_period_days,
        )

        lead_time = calculate_lead_time_for_changes(
            all_issues,
            time_period_days=time_period_days,
        )

        cfr = calculate_change_failure_rate(
            all_issues,
            all_issues,
            time_period_days=time_period_days,
        )

        mttr = calculate_mean_time_to_recovery(
            all_issues,
            time_period_days=time_period_days,
        )

        if "error_state" not in deployment_freq:
            save_metric_snapshot(
                week_label,
                "dora_deployment_frequency",
                {
                    "deployment_count": deployment_freq.get("deployment_count", 0),
                    "release_count": deployment_freq.get("release_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Deployment frequency calculation failed - "
                f"{deployment_freq.get('error_message', 'Unknown error')}"
            )

        if "error_state" not in lead_time:
            lead_time_value = lead_time.get("value")
            lead_time_hours = (
                lead_time_value * 24 if lead_time_value is not None else None
            )
            lead_time_p95_value = lead_time.get("p95_value")
            lead_time_p95_hours = (
                lead_time_p95_value * 24 if lead_time_p95_value is not None else None
            )
            lead_time_mean_value = lead_time.get("mean_value")
            lead_time_mean_hours = (
                lead_time_mean_value * 24 if lead_time_mean_value is not None else None
            )

            save_metric_snapshot(
                week_label,
                "dora_lead_time",
                {
                    "median_hours": lead_time_hours,
                    "p95_hours": lead_time_p95_hours,
                    "mean_hours": lead_time_mean_hours,
                    "issues_with_lead_time": lead_time.get("sample_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Lead time calculation failed - "
                f"{lead_time.get('error_message', 'Unknown error')}"
            )

        if "error_state" not in cfr:
            save_metric_snapshot(
                week_label,
                "dora_change_failure_rate",
                {
                    "change_failure_rate_percent": cfr.get("value", 0),
                    "release_failure_rate_percent": cfr.get("release_value", 0),
                    "total_deployments": cfr.get("deployment_count", 0),
                    "failed_deployments": cfr.get("incident_count", 0),
                    "total_releases": cfr.get("release_count", 0),
                    "failed_releases": cfr.get("failed_release_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: Change failure rate calculation failed - "
                f"{cfr.get('error_message', 'Unknown error')}"
            )

        if "error_state" not in mttr:
            mttr_value = mttr.get("value")
            mttr_p95_value = mttr.get("p95_value")
            mttr_mean_value = mttr.get("mean_value")

            save_metric_snapshot(
                week_label,
                "dora_mttr",
                {
                    "median_hours": mttr_value,
                    "p95_hours": mttr_p95_value,
                    "mean_hours": mttr_mean_value,
                    "bugs_with_mttr": mttr.get("incident_count", 0),
                    "week_label": week_label,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
        else:
            logger.warning(
                f"Week {week_label}: MTTR calculation failed - "
                f"{mttr.get('error_message', 'Unknown error')}"
            )

        return True, f"Week {week_label} calculated successfully (variable extraction)"

    except Exception as e:
        error_msg = f"Error calculating DORA metrics for {week_label}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return False, error_msg
