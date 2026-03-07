"""
Extended Metrics Loader

Loads DORA, flow, and bug-analysis metrics for the health formula
used in the dashboard tab.  All business logic delegated to data/ modules.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger("burndown_chart")


def load_extended_metrics(
    profile_id: str,
    query_id: str,
    data_points_count: int,
    current_week_label: str,
) -> dict:
    """
    Load DORA, flow, and bug extended metrics for the health formula.

    Args:
        profile_id: Active profile identifier.
        query_id: Active query identifier.
        data_points_count: Number of weeks to include.
        current_week_label: ISO week label for the current week.

    Returns:
        Dict with optional keys: "dora", "flow", "bug_analysis".
    """
    extended_metrics: dict = {}

    if not profile_id or not query_id:
        return extended_metrics

    _try_load_dora(extended_metrics, data_points_count)
    _try_load_flow(extended_metrics, data_points_count, current_week_label)
    _try_load_bugs(extended_metrics, data_points_count, profile_id)

    logger.info(
        f"[HEALTH v3.0] Extended metrics summary: "
        f"DORA={'yes' if 'dora' in extended_metrics else 'no'}, "
        f"Flow={'yes' if 'flow' in extended_metrics else 'no'}, "
        f"Bug={'yes' if 'bug_analysis' in extended_metrics else 'no'}"
    )
    return extended_metrics


def _try_load_dora(extended_metrics: dict, data_points_count: int) -> None:
    """Load DORA metrics into extended_metrics if available."""
    try:
        from data.dora_metrics_calculator import load_dora_metrics_from_cache

        cached_metrics = load_dora_metrics_from_cache(n_weeks=data_points_count or 12)
        if not cached_metrics:
            return

        deploy_data = cached_metrics.get("deployment_frequency", {})
        deployment_freq = deploy_data.get("release_value", 0)

        lead_time_data = cached_metrics.get("lead_time_for_changes", {})
        lead_time_days = lead_time_data.get("value")

        cfr_data = cached_metrics.get("change_failure_rate", {})
        change_failure_rate = cfr_data.get("value", 0)

        mttr_data = cached_metrics.get("mean_time_to_recovery", {})
        mttr_hours = mttr_data.get("value")

        has_meaningful_data = (
            (deployment_freq > 0)
            or (lead_time_days is not None and lead_time_days > 0)
            or (mttr_hours is not None and mttr_hours > 0)
        )

        if has_meaningful_data:
            extended_metrics["dora"] = {
                "has_data": True,
                "deployment_frequency": deployment_freq,
                "lead_time": lead_time_days or 0,
                "change_failure_rate": change_failure_rate,
                "mttr_hours": mttr_hours or 0,
            }
            logger.info(
                f"[HEALTH v3.0] DORA metrics loaded: "
                f"DF={deployment_freq:.2f}, "
                f"LT={lead_time_days:.1f}d, "
                f"CFR={change_failure_rate:.1f}%, "
                f"MTTR={mttr_hours:.1f}h"
            )
    except Exception as e:
        logger.warning(f"[HEALTH v3.0] DORA metrics unavailable: {e}")


def _try_load_flow(
    extended_metrics: dict, data_points_count: int, current_week_label: str
) -> None:
    """Load flow metrics into extended_metrics if available."""
    try:
        from data.metrics_snapshots import (
            get_available_weeks,
            get_metric_snapshot,
            get_metric_weekly_values,
        )
        from data.time_period_calculator import format_year_week, get_iso_week

        weeks = []
        current_date = datetime.now()
        for _i in range(data_points_count or 12):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)

        week_labels = list(reversed(weeks))
        current_week_label = week_labels[-1] if week_labels else current_week_label

        available_weeks = get_available_weeks()
        has_any_data = any(week in available_weeks for week in week_labels)
        if not has_any_data:
            return

        flow_time_values = get_metric_weekly_values(
            week_labels, "flow_time", "median_days"
        )
        flow_efficiency_values = get_metric_weekly_values(
            week_labels, "flow_efficiency", "overall_pct"
        )
        velocity_values = get_metric_weekly_values(
            week_labels, "flow_velocity", "completed_count"
        )

        avg_velocity = (
            sum(velocity_values) / len(velocity_values) if velocity_values else 0
        )

        non_zero_flow_times = [v for v in flow_time_values if v > 0]
        if non_zero_flow_times:
            sorted_times = sorted(non_zero_flow_times)
            mid = len(sorted_times) // 2
            median_flow_time = (
                sorted_times[mid]
                if len(sorted_times) % 2 == 1
                else (sorted_times[mid - 1] + sorted_times[mid]) / 2
            )
        else:
            median_flow_time = 0

        non_zero_efficiency = [v for v in flow_efficiency_values if v > 0]
        avg_efficiency = (
            sum(non_zero_efficiency) / len(non_zero_efficiency)
            if non_zero_efficiency
            else 0
        )

        flow_load_snapshot = get_metric_snapshot(current_week_label, "flow_load")
        wip = flow_load_snapshot.get("wip_count", 0) if flow_load_snapshot else 0

        total_feature = total_defect = total_tech_debt = total_risk = 0
        total_completed = 0
        for week in week_labels:
            week_snapshot = get_metric_snapshot(week, "flow_velocity")
            if week_snapshot:
                week_dist = week_snapshot.get("distribution", {})
                total_feature += week_dist.get("feature", 0)
                total_defect += week_dist.get("defect", 0)
                total_tech_debt += week_dist.get("tech_debt", 0)
                total_risk += week_dist.get("risk", 0)
                total_completed += week_snapshot.get("completed_count", 0)

        if avg_velocity > 0:
            extended_metrics["flow"] = {
                "has_data": True,
                "velocity": avg_velocity,
                "flow_time": median_flow_time,
                "efficiency": avg_efficiency,
                "wip": wip,
                "work_distribution": {
                    "feature": total_feature,
                    "defect": total_defect,
                    "tech_debt": total_tech_debt,
                    "risk": total_risk,
                    "total": total_completed,
                },
            }
            logger.info(
                f"[HEALTH v3.0] Flow metrics loaded: "
                f"Velocity={avg_velocity:.1f}, "
                f"Efficiency={avg_efficiency:.1f}%, "
                f"Flow Time={median_flow_time:.1f}d"
            )
    except Exception as e:
        logger.warning(f"[HEALTH v3.0] Flow metrics unavailable: {e}")


def _try_load_bugs(
    extended_metrics: dict, data_points_count: int, profile_id: str
) -> None:
    """Load bug analysis metrics into extended_metrics if available."""
    try:
        from data.bug_processing import (
            calculate_bug_metrics_summary,
            filter_bug_issues,
        )
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id

        backend = get_backend()
        query_id_active = get_active_query_id()
        bug_data = None

        if not query_id_active or not profile_id:
            return

        issues = backend.get_issues(profile_id, query_id_active)
        if issues:
            from data.issue_filtering import filter_issues_for_metrics
            from data.persistence import load_app_settings

            settings = load_app_settings()
            issues = filter_issues_for_metrics(
                issues, settings=settings, log_prefix="BUG METRICS"
            )

        from data.persistence import load_app_settings

        settings = load_app_settings()
        bug_types = settings.get("bug_types", {})

        date_to = datetime.now()
        date_from = date_to - timedelta(weeks=data_points_count or 12)

        all_bug_issues = filter_bug_issues(
            issues,
            bug_type_mappings=bug_types,
            date_from=None,
            date_to=None,
        )
        timeline_filtered_bugs = filter_bug_issues(
            issues,
            bug_type_mappings=bug_types,
            date_from=date_from,
            date_to=date_to,
        )

        from data.persistence import load_unified_project_data

        project_data = load_unified_project_data()
        weekly_stats = project_data.get("statistics", [])

        bug_data = calculate_bug_metrics_summary(
            all_bug_issues=all_bug_issues,
            timeline_filtered_bugs=timeline_filtered_bugs,
            weekly_stats=weekly_stats,
        )

        if bug_data and bug_data.get("total_bugs", 0) > 0:
            resolution_rate_pct = bug_data.get("resolution_rate", 0) * 100
            logger.info(
                "[BUG METRICS] Passing to health: "
                f"resolution_rate={resolution_rate_pct:.2f}%, "
                f"total_bugs={bug_data.get('total_bugs', 0)}, "
                f"avg_age_days={bug_data.get('avg_age_days', 0)}d, "
                f"all_bug_issues_count={len(all_bug_issues)}, "
                f"timeline_bugs_count={len(timeline_filtered_bugs)}"
            )
            extended_metrics["bug_analysis"] = {
                "has_data": True,
                "resolution_rate": resolution_rate_pct,
                "avg_resolution_time_days": bug_data.get("avg_resolution_time_days", 0),
                "avg_age_days": bug_data.get("avg_age_days", 0),
                "capacity_consumed_by_bugs": (
                    bug_data.get("capacity_consumed_by_bugs", 0) / 100
                    if bug_data.get("capacity_consumed_by_bugs")
                    else 0
                ),
                "open_bugs": bug_data.get("open_bugs", 0),
            }
            bug_resolution_rate = extended_metrics["bug_analysis"]["resolution_rate"]
            bug_capacity_pct = extended_metrics["bug_analysis"][
                "capacity_consumed_by_bugs"
            ]
            logger.info(
                f"[HEALTH v3.0] Bug metrics available: "
                f"Resolution={bug_resolution_rate:.1f}%, "
                f"Capacity={bug_capacity_pct:.1%}"
            )
    except Exception as e:
        logger.warning(f"[HEALTH v3.0] Bug metrics unavailable: {e}")
