import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data.bug_processing import (
    calculate_bug_metrics_summary,
    calculate_bug_statistics,
    filter_bug_issues,
    forecast_bug_resolution,
)
from data.dora._common import _classify_performance_tier
from data.dora_metrics import (
    CHANGE_FAILURE_RATE_TIERS,
    DEPLOYMENT_FREQUENCY_TIERS,
    LEAD_TIME_TIERS,
    MTTR_TIERS,
)
from data.dora_metrics_calculator import load_dora_metrics_from_cache
from data.metrics_snapshots import (
    get_available_weeks,
    get_metric_snapshot,
    get_metric_weekly_values,
)
from data.processing import calculate_velocity_from_dataframe
from data.report.helpers import (
    calculate_historical_burndown,
    calculate_weekly_breakdown,
)
from data.time_period_calculator import format_year_week, get_iso_week

logger = logging.getLogger(__name__)


def calculate_burndown_metrics(
    statistics: list[dict], project_scope: dict, weeks_count: int
) -> dict[str, Any]:

    if not statistics:
        return {"has_data": False, "weeks_count": weeks_count}

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore

    velocity_items = calculate_velocity_from_dataframe(df, "completed_items")
    velocity_points = calculate_velocity_from_dataframe(df, "completed_points")

    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    weeks_remaining_items = (
        remaining_items / velocity_items if velocity_items > 0 else float("inf")
    )
    weeks_remaining_points = (
        remaining_points / velocity_points if velocity_points > 0 else float("inf")
    )

    weekly_data = calculate_weekly_breakdown(statistics)

    historical_data = calculate_historical_burndown(statistics, project_scope)

    return {
        "has_data": True,
        "velocity_items": velocity_items,
        "velocity_points": velocity_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "weeks_remaining_items": weeks_remaining_items,
        "weeks_remaining_points": weeks_remaining_points,
        "weekly_data": weekly_data,
        "historical_data": historical_data,
        "weeks_count": weeks_count,
    }


def calculate_bug_metrics(
    jira_issues: list[dict],
    statistics: list[dict],
    settings: dict,
    weeks_count: int,
) -> dict[str, Any]:

    if not jira_issues:
        logger.warning("[REPORT BUG] No JIRA issues available for bug analysis")
        return {"has_data": False}

    try:
        bug_types = settings.get("bug_types", {})
        logger.info(
            f"[REPORT BUG] Processing {len(jira_issues)} JIRA issues "
            f"with bug_types={bug_types}"
        )

        date_to = datetime.now()
        date_from = (
            date_to - timedelta(weeks=weeks_count)
            if weeks_count > 0
            else date_to - timedelta(weeks=12)
        )

        all_bug_issues = filter_bug_issues(
            jira_issues,
            bug_type_mappings=bug_types,
            date_from=None,
            date_to=None,
        )

        timeline_filtered_bugs = filter_bug_issues(
            jira_issues,
            bug_type_mappings=bug_types,
            date_from=date_from,
            date_to=date_to,
        )

        if not all_bug_issues and not timeline_filtered_bugs:
            logger.warning(
                f"[REPORT BUG] No bugs found matching configured types. "
                f"Total JIRA issues: {len(jira_issues)}, bug_types={bug_types}"
            )
            return {"has_data": False}

        points_field = settings.get("points_field", "customfield_10016")
        weekly_stats = []
        try:
            weekly_stats = calculate_bug_statistics(
                timeline_filtered_bugs,
                date_from,
                date_to,
                story_points_field=points_field,
            )
        except Exception as e:
            logger.warning(f"Failed to calculate bug statistics: {e}")

        bug_summary = calculate_bug_metrics_summary(
            all_bug_issues=all_bug_issues,
            timeline_filtered_bugs=timeline_filtered_bugs,
            weekly_stats=weekly_stats,
            date_from=date_from,
            date_to=date_to,
            all_project_issues=jira_issues,
        )

        forecast = None
        open_bugs = bug_summary.get("open_bugs", 0)
        if open_bugs > 0 and weekly_stats:
            try:
                forecast_weeks = min(8, weeks_count)
                forecast = forecast_bug_resolution(
                    open_bugs=open_bugs,
                    weekly_stats=weekly_stats,
                    use_last_n_weeks=forecast_weeks,
                )
            except Exception as e:
                logger.warning(f"Failed to calculate bug forecast: {e}")

        total_completed = sum(s.get("completed_items", 0) for s in statistics)
        total_bugs_resolved = sum(s.get("bugs_resolved", 0) for s in weekly_stats)
        bug_investment_pct = (
            (total_bugs_resolved / total_completed) * 100 if total_completed > 0 else 0
        )

        resolution_rate = bug_summary.get("resolution_rate", 0)
        resolution_rate_pct = resolution_rate * 100

        avg_age_days = bug_summary.get("avg_age_days", 0)

        closed_bugs = bug_summary.get("closed_bugs", 0)

        if resolution_rate_pct >= 75:
            health_status = "Healthy"
            health_color = "#198754"
            health_icon = "fas fa-shield-alt"
            health_desc = (
                "Resolution rate is high — bugs are being resolved effectively"
            )
        elif resolution_rate_pct >= 50:
            health_status = "Moderate"
            health_color = "#fd7e14"
            health_icon = "fas fa-exclamation-circle"
            health_desc = "Resolution rate is moderate — monitor for backlog growth"
        else:
            health_status = "Critical"
            health_color = "#dc3545"
            health_icon = "fas fa-exclamation-triangle"
            health_desc = (
                "Low resolution rate — bug backlog may be growing"
                " faster than it is resolved"
            )

        return {
            "has_data": True,
            "open_bugs": bug_summary.get("open_bugs", 0),
            "total_bugs": bug_summary.get("total_bugs", 0),
            "closed_bugs": closed_bugs,
            "resolution_rate": resolution_rate_pct,
            "avg_age_days": avg_age_days,
            "capacity_consumed_by_bugs": bug_summary.get(
                "capacity_consumed_by_bugs", 0
            ),
            "forecast_weeks": forecast.get("most_likely_weeks") if forecast else None,
            "forecast_date": forecast.get("most_likely_date") if forecast else None,
            "avg_closure_rate": forecast.get("avg_closure_rate") if forecast else None,
            "weeks_analyzed": forecast.get("weeks_analyzed") if forecast else None,
            "bug_investment_pct": bug_investment_pct,
            "bug_capacity_consumption_pct": bug_summary.get(
                "capacity_consumed_by_bugs", 0
            ),
            "weekly_stats": weekly_stats,
            "date_from": date_from.strftime("%b %d, %Y"),
            "date_to": date_to.strftime("%b %d, %Y"),
            "health_status": health_status,
            "health_color": health_color,
            "health_icon": health_icon,
            "health_desc": health_desc,
        }
    except Exception as e:
        logger.error(f"Error calculating bug metrics: {e}", exc_info=True)
        return {"has_data": False, "error": str(e)}


def calculate_scope_metrics(
    statistics: list[dict], project_scope: dict, weeks_count: int
) -> dict[str, Any]:

    if not statistics or len(statistics) < 2:
        return {"has_data": False}

    df = pd.DataFrame(statistics)

    total_created_items = int(df["created_items"].sum())
    total_created_points = df["created_points"].sum()
    total_completed_items = int(df["completed_items"].sum())
    total_completed_points = df["completed_points"].sum()

    current_items = project_scope.get("remaining_items", 0)
    current_points = project_scope.get("remaining_total_points", 0)

    initial_items = current_items + total_completed_items - total_created_items
    initial_points = current_points + total_completed_points - total_created_points

    logger.debug(
        f"[SCOPE BASELINE] Current: {current_items} items, {current_points:.2f} points"
    )
    logger.debug(
        "[SCOPE BASELINE] Total completed in period: "
        f"{total_completed_items} items, {total_completed_points:.2f} points"
    )
    logger.debug(
        "[SCOPE BASELINE] Total created in period: "
        f"{total_created_items} items, {total_created_points:.2f} points"
    )
    logger.debug(
        "[SCOPE BASELINE] Calculated initial: "
        f"{initial_items} items, {initial_points:.2f} points"
    )

    items_change = current_items - initial_items
    points_change = current_points - initial_points

    items_ratio = (
        round(total_created_items / total_completed_items, 2)
        if total_completed_items > 0
        else 0
    )
    points_ratio = (
        round(total_created_points / total_completed_points, 2)
        if total_completed_points > 0
        else 0
    )

    _no_completions = total_completed_items == 0 and total_created_items > 0
    if _no_completions or items_ratio >= 1.1:
        scope_health = "Scope Growing"
        scope_health_color = "#dc3545"
        scope_health_icon = "fas fa-exclamation-triangle"
        scope_health_desc = "Creating faster than completing — backlog is expanding"
    elif items_ratio < 0.8:
        scope_health = "On Track"
        scope_health_color = "#198754"
        scope_health_icon = "fas fa-shield-alt"
        scope_health_desc = (
            "Completing significantly more than creating — backlog is burning down"
        )
    else:
        scope_health = "At Risk"
        scope_health_color = "#fd7e14"
        scope_health_icon = "fas fa-exclamation-circle"
        scope_health_desc = (
            "Scope and delivery are roughly balanced — monitor for backlog growth"
        )

    return {
        "has_data": True,
        "initial_items": initial_items,
        "initial_points": round(initial_points, 1),
        "final_items": current_items,
        "final_points": round(current_points, 1),
        "items_change": items_change,
        "points_change": round(points_change, 1),
        "created_items": total_created_items,
        "created_points": total_created_points,
        "completed_items": total_completed_items,
        "completed_points": total_completed_points,
        "items_ratio": items_ratio,
        "points_ratio": points_ratio,
        "weeks_count": weeks_count,
        "scope_health": scope_health,
        "scope_health_color": scope_health_color,
        "scope_health_icon": scope_health_icon,
        "scope_health_desc": scope_health_desc,
    }


def calculate_flow_metrics(
    snapshots: dict[str, dict],
    weeks_count: int,
    week_labels: list[str] | None = None,
) -> dict[str, Any]:

    logger.info(f"Loading Flow metrics from snapshots for {weeks_count} weeks")

    if week_labels:
        week_labels = list(week_labels)
        logger.info(f"[FLOW METRICS] Using provided week labels: {week_labels}")
    else:
        weeks = []
        current_date = datetime.now()
        for _i in range(weeks_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)
        week_labels = list(reversed(weeks))
        logger.warning(
            f"[FLOW METRICS] Generated week labels (should use provided): {week_labels}"
        )

    current_week_label = week_labels[-1] if week_labels else ""

    available_weeks = get_available_weeks()
    has_any_data = any(week in available_weeks for week in week_labels)

    if not has_any_data:
        logger.warning("No Flow metrics snapshots found")
        return {"has_data": False, "weeks_count": weeks_count}

    flow_time_values = get_metric_weekly_values(week_labels, "flow_time", "median_days")
    flow_efficiency_values = get_metric_weekly_values(
        week_labels, "flow_efficiency", "overall_pct"
    )
    velocity_values = get_metric_weekly_values(
        week_labels, "flow_velocity", "completed_count"
    )

    avg_velocity = sum(velocity_values) / len(velocity_values) if velocity_values else 0

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
    if not flow_load_snapshot and available_weeks:
        for week in week_labels[::-1]:
            flow_load_snapshot = get_metric_snapshot(week, "flow_load")
            if flow_load_snapshot:
                logger.info(
                    "Using WIP from "
                    f"{week} (current {current_week_label} not available)"
                )
                break
    wip_count = flow_load_snapshot.get("wip_count", 0) if flow_load_snapshot else 0

    total_feature = 0
    total_defect = 0
    total_tech_debt = 0
    total_risk = 0
    total_completed = 0
    distribution_history = []

    for week in week_labels:
        week_snapshot = get_metric_snapshot(week, "flow_velocity")
        if week_snapshot:
            week_dist = week_snapshot.get("distribution", {})
            week_feature = week_dist.get("feature", 0)
            week_defect = week_dist.get("defect", 0)
            week_tech_debt = week_dist.get("tech_debt", 0)
            week_risk = week_dist.get("risk", 0)
            week_total = week_snapshot.get("completed_count", 0)

            total_feature += week_feature
            total_defect += week_defect
            total_tech_debt += week_tech_debt
            total_risk += week_risk
            total_completed += week_total

            distribution_history.append(
                {
                    "week": week,
                    "feature": week_feature,
                    "defect": week_defect,
                    "tech_debt": week_tech_debt,
                    "risk": week_risk,
                    "total": week_total,
                }
            )
        else:
            distribution_history.append(
                {
                    "week": week,
                    "feature": 0,
                    "defect": 0,
                    "tech_debt": 0,
                    "risk": 0,
                    "total": 0,
                }
            )

    logger.info(
        f"Flow metrics loaded: Velocity={avg_velocity:.2f} items/week, "
        "Flow Time="
        f"{median_flow_time:.2f}d, Efficiency={avg_efficiency:.2f}%, WIP={wip_count}"
    )

    has_meaningful_data = (
        (avg_velocity > 0)
        or (median_flow_time > 0)
        or (avg_efficiency > 0)
        or (wip_count > 0)
        or (total_completed > 0)
    )

    if not has_meaningful_data:
        logger.info("No meaningful Flow data - all metrics are zero")
        return {"has_data": False, "weeks_count": weeks_count}

    _fv_score = (
        3
        if avg_velocity >= 20
        else (2 if avg_velocity >= 10 else (1 if avg_velocity >= 5 else 0))
    )
    _ft_score = (
        3
        if median_flow_time <= 3
        else (2 if median_flow_time <= 7 else (1 if median_flow_time <= 14 else 0))
    )
    _fe_score = (
        3
        if avg_efficiency >= 60
        else (2 if avg_efficiency >= 40 else (1 if avg_efficiency >= 25 else 0))
    )
    _fw_score = (
        3 if wip_count < 10 else (2 if wip_count < 20 else (1 if wip_count < 30 else 0))
    )
    _flow_score = _fv_score + _ft_score + _fe_score + _fw_score
    if _flow_score >= 10:
        _flow_meta: dict[str, str] = {
            "label": "High Performance",
            "color": "#198754",
            "icon": "fas fa-trophy",
            "desc": "Fast, efficient flow with low WIP and short cycle times",
        }
    elif _flow_score >= 7:
        _flow_meta = {
            "label": "Moderate",
            "color": "#0d6efd",
            "icon": "fas fa-chart-line",
            "desc": "Solid flow with some metrics that could be optimised",
        }
    elif _flow_score >= 4:
        _flow_meta = {
            "label": "Developing",
            "color": "#fd7e14",
            "icon": "fas fa-exclamation-circle",
            "desc": "Flow is inconsistent — reduce WIP and improve cycle time",
        }
    else:
        _flow_meta = {
            "label": "Needs Improvement",
            "color": "#dc3545",
            "icon": "fas fa-exclamation-triangle",
            "desc": "Significant flow bottlenecks detected across multiple dimensions",
        }

    return {
        "has_data": True,
        "velocity": avg_velocity,
        "flow_time": round(median_flow_time, 1),
        "efficiency": avg_efficiency,
        "wip": wip_count,
        "performance_level": _flow_meta["label"],
        "performance_level_color": _flow_meta["color"],
        "performance_level_icon": _flow_meta["icon"],
        "performance_level_desc": _flow_meta["desc"],
        "work_distribution": {
            "feature": total_feature,
            "defect": total_defect,
            "tech_debt": total_tech_debt,
            "risk": total_risk,
            "total": total_completed,
        },
        "distribution_history": distribution_history,
        "weeks_count": weeks_count,
    }


def calculate_dora_metrics(profile_id: str, weeks_count: int) -> dict[str, Any]:

    logger.info(f"Loading DORA metrics from cache for {weeks_count} weeks")

    cached_metrics = load_dora_metrics_from_cache(n_weeks=weeks_count)

    if not cached_metrics:
        logger.warning("No DORA metrics found in cache")
        return {"has_data": False, "weeks_count": weeks_count}

    deploy_data = cached_metrics.get("deployment_frequency", {})
    deployment_freq = deploy_data.get("release_value", 0)
    deployment_freq_tasks = deploy_data.get("value", 0)

    lead_time_data = cached_metrics.get("lead_time_for_changes", {})
    lead_time_days = lead_time_data.get("value")
    lead_time_hours = lead_time_data.get("value_hours")

    cfr_data = cached_metrics.get("change_failure_rate", {})
    change_failure_rate = cfr_data.get("value", 0)

    mttr_data = cached_metrics.get("mean_time_to_recovery", {})
    mttr_hours = mttr_data.get("value")
    mttr_days = mttr_hours / 24 if mttr_hours else None

    weekly_labels = deploy_data.get("weekly_labels", [])

    logger.info(
        f"DORA metrics loaded: DF={deployment_freq} releases/week, "
        f"LT={lead_time_days}d, CFR={change_failure_rate}%, MTTR={mttr_days}d"
    )

    has_meaningful_data = (
        (deployment_freq > 0)
        or (lead_time_days is not None and lead_time_days > 0)
        or (mttr_days is not None and mttr_days > 0)
        or (deployment_freq_tasks > 0)
    )

    if not has_meaningful_data:
        logger.info("No meaningful DORA data - all metrics are zero or None")
        return {"has_data": False, "weeks_count": weeks_count}

    _tier_order = ["elite", "high", "medium", "low"]
    _df_tier = _classify_performance_tier(
        deployment_freq / 7, DEPLOYMENT_FREQUENCY_TIERS, higher_is_better=True
    )
    _lt_tier = (
        _classify_performance_tier(
            lead_time_days, LEAD_TIME_TIERS, higher_is_better=False
        )
        if lead_time_days
        else "elite"
    )
    _cfr_tier = _classify_performance_tier(
        change_failure_rate, CHANGE_FAILURE_RATE_TIERS, higher_is_better=False
    )
    _mttr_tier = (
        _classify_performance_tier(mttr_hours, MTTR_TIERS, higher_is_better=False)
        if mttr_hours
        else "elite"
    )
    _worst = max(
        [_df_tier, _lt_tier, _cfr_tier, _mttr_tier],
        key=lambda t: _tier_order.index(t),
    )
    _dora_tier_meta: dict[str, str] = {
        "elite": {
            "label": "Elite",
            "color": "#198754",
            "icon": "fas fa-trophy",
            "desc": "Top-performing team — on-demand delivery with high stability",
        },
        "high": {
            "label": "High",
            "color": "#0d6efd",
            "icon": "fas fa-star",
            "desc": "Strong delivery cadence and recovery capability",
        },
        "medium": {
            "label": "Medium",
            "color": "#fd7e14",
            "icon": "fas fa-chart-line",
            "desc": "Delivery is established but has room for improvement",
        },
        "low": {
            "label": "Low",
            "color": "#dc3545",
            "icon": "fas fa-exclamation-triangle",
            "desc": "Significant improvements needed in delivery and recovery",
        },
    }[_worst]

    return {
        "has_data": True,
        "deployment_frequency": deployment_freq,
        "deployment_frequency_tasks": deployment_freq_tasks,
        "lead_time": lead_time_days or 0,
        "lead_time_days": lead_time_days,
        "lead_time_hours": lead_time_hours,
        "change_failure_rate": change_failure_rate,
        "mttr_hours": mttr_hours or 0,
        "mttr_days": mttr_days,
        "weekly_labels": weekly_labels,
        "weeks_count": weeks_count,
        "overall_tier": _dora_tier_meta["label"],
        "overall_tier_color": _dora_tier_meta["color"],
        "overall_tier_icon": _dora_tier_meta["icon"],
        "overall_tier_desc": _dora_tier_meta["desc"],
        "_raw": cached_metrics,
    }
