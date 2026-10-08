import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data.processing import (
    calculate_rates,
    calculate_velocity_from_dataframe,
    compute_weekly_throughput,
)
from data.project_health_calculator import (
    calculate_comprehensive_project_health,
    prepare_dashboard_metrics_for_health,
)
from data.time_period_calculator import format_year_week, get_iso_week
from data.types import MetricsResult

logger = logging.getLogger(__name__)


def calculate_dashboard_metrics(
    all_statistics: list[dict],
    windowed_statistics: list[dict],
    project_scope: dict,
    settings: dict,
    weeks_count: int,
    show_points: bool = False,
    extended_metrics: dict[str, Any] | None = None,
) -> MetricsResult:

    if not all_statistics:
        return {
            "has_data": False,
            "completed_items": 0,
            "completed_points": 0,
            "remaining_items": 0,
            "remaining_points": 0,
            "total_items": 0,
            "total_points": 0,
            "items_completion_pct": 0,
            "points_completion_pct": 0,
            "health_score": 0,
            "health_status": "Unknown",
            "deadline": None,
            "milestone": None,
            "velocity_items": 0,
            "velocity_points": 0,
            "velocity_items_recent_4w": 0,
            "velocity_points_recent_4w": 0,
        }

    df_windowed = pd.DataFrame(windowed_statistics)
    if not df_windowed.empty and "date" in df_windowed.columns:
        df_windowed["date"] = pd.to_datetime(
            df_windowed["date"], format="mixed", errors="coerce"
        )

    df_all = pd.DataFrame(all_statistics)
    if not df_all.empty and "date" in df_all.columns:
        df_all["date"] = pd.to_datetime(df_all["date"], format="mixed", errors="coerce")

    completed_items = (
        int(df_windowed["completed_items"].sum()) if not df_windowed.empty else 0
    )
    completed_points = (
        df_windowed["completed_points"].sum() if not df_windowed.empty else 0
    )

    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    total_items = remaining_items + completed_items
    total_points = remaining_points + completed_points

    items_completion_pct = (
        (completed_items / total_items) * 100 if total_items > 0 else 0
    )
    points_completion_pct = (
        (completed_points / total_points) * 100 if total_points > 0 else 0
    )

    logger.info(
        f"[REPORT COMPLETION] completed_items={completed_items}, "
        f"remaining_items={remaining_items}, "
        f"total_items={total_items}, completion_pct={items_completion_pct:.2f}%"
    )

    data_points_count = weeks_count
    df_for_velocity = df_windowed

    logger.info(
        f"[REPORT FILTER DEBUG] weeks_count={weeks_count}, "
        f"df_windowed len={len(df_windowed)}, "
        f"data_points_count={data_points_count}"
    )

    if (
        data_points_count > 0
        and not df_windowed.empty
        and "date" in df_windowed.columns
    ):
        df_windowed_temp = df_windowed.copy()
        df_windowed_temp["date"] = pd.to_datetime(
            df_windowed_temp["date"], format="mixed", errors="coerce"
        )
        df_windowed_temp = df_windowed_temp.dropna(subset=["date"]).sort_values(
            "date", ascending=True
        )

        weeks = []
        current_date = df_windowed_temp["date"].max()
        for _i in range(data_points_count):
            year, week = get_iso_week(current_date)
            week_label = format_year_week(year, week)
            weeks.append(week_label)
            current_date = current_date - timedelta(days=7)

        week_labels = set(reversed(weeks))

        if "week_label" in df_windowed_temp.columns:
            df_for_velocity = df_windowed_temp[
                df_windowed_temp["week_label"].isin(week_labels)
            ]
            logger.info(
                "[REPORT FILTER EARLY] Filtered to "
                f"{len(df_for_velocity)} rows for health calculation "
                f"(requested {data_points_count} weeks)"
            )
        else:
            latest_date = df_windowed_temp["date"].max()
            cutoff_date = latest_date - timedelta(weeks=data_points_count)
            df_for_velocity = df_windowed_temp[df_windowed_temp["date"] > cutoff_date]
            logger.warning(
                "[REPORT FILTER EARLY] No week_label column - "
                "using date range filtering: "
                f"{len(df_for_velocity)} rows"
            )

    velocity_cv = 0
    logger.info(
        "[REPORT FILTER DEBUG] After filtering: "
        f"df_for_velocity len={len(df_for_velocity)}"
    )
    if not df_for_velocity.empty and len(df_for_velocity) >= 2:
        weekly_velocities = df_for_velocity["completed_items"].tolist()
        mean_vel = (
            sum(weekly_velocities) / len(weekly_velocities)
            if len(weekly_velocities) > 0
            else 0
        )
        if mean_vel > 0:
            variance = sum((x - mean_vel) ** 2 for x in weekly_velocities) / len(
                weekly_velocities
            )
            std_dev = variance**0.5
            velocity_cv = (std_dev / mean_vel) * 100

    trend_direction = "stable"
    recent_velocity_change = 0
    if not df_for_velocity.empty and len(df_for_velocity) >= 6:
        mid_point = len(df_for_velocity) // 2
        older_half = df_for_velocity.iloc[:mid_point]
        recent_half = df_for_velocity.iloc[mid_point:]

        if len(older_half) > 0 and len(recent_half) > 0:
            older_velocity = older_half["completed_items"].sum() / len(older_half)
            recent_velocity = recent_half["completed_items"].sum() / len(recent_half)

            if older_velocity > 0:
                recent_velocity_change = (
                    (recent_velocity - older_velocity) / older_velocity
                ) * 100
                if recent_velocity_change > 10:
                    trend_direction = "improving"
                elif recent_velocity_change < -10:
                    trend_direction = "declining"

    schedule_variance_days = 0
    completion_confidence = 50

    velocity_items_early = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_items"
    )

    dashboard_metrics_for_health = prepare_dashboard_metrics_for_health(
        completion_percentage=items_completion_pct
        if not show_points
        else points_completion_pct,
        current_velocity_items=velocity_items_early,
        velocity_cv=velocity_cv,
        trend_direction=trend_direction,
        recent_velocity_change=recent_velocity_change,
        schedule_variance_days=schedule_variance_days,
        completion_confidence=50,
    )

    completion_pct_for_health = (
        items_completion_pct if not show_points else points_completion_pct
    )
    logger.info(
        f"[REPORT HEALTH FIRST] Input: completion_pct={completion_pct_for_health:.2f}, "
        f"velocity_items={velocity_items_early:.2f}, velocity_cv={velocity_cv:.2f}, "
        f"trend={trend_direction}, recent_change={recent_velocity_change:.2f}, "
        f"schedule_var={schedule_variance_days:.2f}, confidence=50"
    )

    if extended_metrics is None:
        extended_metrics = {}

    health_result = calculate_comprehensive_project_health(
        dashboard_metrics=dashboard_metrics_for_health,
        dora_metrics=extended_metrics.get("dora"),
        flow_metrics=extended_metrics.get("flow"),
        bug_metrics=extended_metrics.get("bug_analysis"),
        budget_metrics=extended_metrics.get("budget"),
        scope_metrics={"scope_change_rate": 0},
    )

    health_score = health_result["overall_score"]

    if health_score >= 70:
        health_status = "GOOD"
    elif health_score >= 50:
        health_status = "CAUTION"
    elif health_score >= 30:
        health_status = "AT RISK"
    else:
        health_status = "CRITICAL"

    logger.info(
        f"[REPORT HEALTH] Comprehensive health_score={health_score}% "
        f"status={health_status} "
        f"formula_version={health_result.get('formula_version')} "
        f"dimensions={len(health_result.get('dimensions', {}))}"
    )

    velocity_items = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_items"
    )
    velocity_points = calculate_velocity_from_dataframe(
        df_for_velocity, "completed_points"
    )

    logger.debug(
        f"[REPORT VELOCITY] df_windowed len={len(df_windowed)}, "
        f"data_points_count={data_points_count}, "
        f"df_for_velocity len={len(df_for_velocity)}"
    )
    logger.debug(
        f"[REPORT VELOCITY] velocity_items={velocity_items:.2f} items/week, "
        f"velocity_points={velocity_points:.2f} points/week"
    )

    velocity_items_recent_4w = 0
    velocity_points_recent_4w = 0
    if not df_for_velocity.empty and len(df_for_velocity) >= 4:
        df_recent_4w = df_for_velocity.tail(4)
        velocity_items_recent_4w = calculate_velocity_from_dataframe(
            df_recent_4w, "completed_items"
        )
        velocity_points_recent_4w = calculate_velocity_from_dataframe(
            df_recent_4w, "completed_points"
        )
        logger.debug(
            "[REPORT VELOCITY 4W] Recent 4 weeks: "
            f"velocity_items={velocity_items_recent_4w:.2f}, "
            f"velocity_points={velocity_points_recent_4w:.2f}"
        )
    elif not df_for_velocity.empty:
        velocity_items_recent_4w = velocity_items
        velocity_points_recent_4w = velocity_points

    scope_change_rate = 0
    if not df_for_velocity.empty and "created_items" in df_for_velocity.columns:
        total_created = df_for_velocity["created_items"].sum()
        if total_items > 0:
            scope_change_rate = (total_created / total_items) * 100

    logger.debug(
        f"[REPORT SCOPE] scope_change_rate={scope_change_rate:.2f}% "
        f"(from {len(df_for_velocity)} rows)"
    )

    deadline = settings.get("deadline")
    milestone = settings.get("milestone")
    pert_factor = settings.get("pert_factor", 6)

    forecast_date = None
    forecast_months = None
    forecast_metric = "story points" if show_points else "items"
    pert_days = None
    forecast_date_items = None
    forecast_date_points = None

    grouped = compute_weekly_throughput(df_for_velocity)

    logger.info(
        f"[REPORT DATA] df_for_velocity rows={len(df_for_velocity)}, "
        f"grouped weeks={len(grouped)}, "
        f"data_points_count={data_points_count}"
    )

    pert_time_items, _, _, pert_time_points, _, _ = calculate_rates(
        grouped,
        remaining_items,
        remaining_points,
        pert_factor,
        show_points,
    )

    pert_days = (
        pert_time_points if (show_points and pert_time_points) else pert_time_items
    )

    logger.debug(
        f"[REPORT FORECAST] velocity_items={velocity_items:.2f}, "
        f"velocity_points={velocity_points:.2f}, "
        f"remaining_items={remaining_items}, "
        f"remaining_points={remaining_points:.2f}, "
        f"pert_factor={pert_factor}, pert_days={pert_days}, "
        f"pert_time_items={pert_time_items:.2f}, "
        f"pert_time_points={pert_time_points:.2f}, "
        f"show_points={show_points}"
    )

    last_date = (
        df_for_velocity["date"].iloc[-1]
        if not df_for_velocity.empty
        else datetime.now()
    )

    last_date_display = (
        last_date.strftime("%Y-%m-%d") if hasattr(last_date, "strftime") else last_date
    )
    completion_date_display = (
        (last_date + timedelta(days=pert_days)).strftime("%Y-%m-%d")
        if pert_days and pert_days > 0
        else "None"
    )
    logger.info(
        f"[REPORT FORECAST] last_date={last_date_display}, "
        f"pert_days={pert_days}, df_for_velocity_rows={len(df_for_velocity)}, "
        f"completion_date={completion_date_display}"
    )

    if pert_days and pert_days > 0:
        forecast_date_obj = last_date + timedelta(days=pert_days)
        forecast_date = forecast_date_obj.strftime("%Y-%m-%d")

        forecast_months = round(pert_days / 30.44)

    if pert_time_items and pert_time_items > 0:
        forecast_date_items_obj = last_date + timedelta(days=pert_time_items)
        forecast_date_items = forecast_date_items_obj.strftime("%Y-%m-%d")
        logger.info(
            f"[REPORT] Calculated forecast_date_items: {forecast_date_items} "
            f"(pert_time_items={pert_time_items:.2f} days "
            f"from {last_date.strftime('%Y-%m-%d')})"
        )

    if pert_time_points and pert_time_points > 0:
        forecast_date_points_obj = last_date + timedelta(days=pert_time_points)
        forecast_date_points = forecast_date_points_obj.strftime("%Y-%m-%d")
        logger.info(
            f"[REPORT] Calculated forecast_date_points: {forecast_date_points} "
            f"(pert_time_points={pert_time_points:.2f} days "
            f"from {last_date.strftime('%Y-%m-%d')})"
        )

    logger.info(
        f"[REPORT] Final forecast values: forecast_date={forecast_date}, "
        f"forecast_date_items={forecast_date_items}, "
        f"forecast_date_points={forecast_date_points}"
    )

    deadline_months = None
    days_to_deadline = None
    if deadline:
        try:
            deadline_obj = datetime.strptime(deadline, "%Y-%m-%d")
            days_to_deadline = (deadline_obj - last_date).days
            deadline_months = round(days_to_deadline / 30.44)
        except ValueError:
            pass

    if pert_days and days_to_deadline:
        schedule_variance_days = days_to_deadline - pert_days
        logger.info(
            f"[REPORT HEALTH] RECALC: "
            f"schedule_variance_days={schedule_variance_days:.2f} "
            f"(pert_days={pert_days:.2f}, days_to_deadline={days_to_deadline})"
        )

        buffer_days = days_to_deadline - pert_days
        if buffer_days >= 28:
            completion_confidence = 95
        elif buffer_days >= 14:
            completion_confidence = 80
        elif buffer_days >= 0:
            completion_confidence = 65
        elif buffer_days >= -14:
            completion_confidence = 45
        else:
            completion_confidence = 25

        dashboard_metrics_for_health = prepare_dashboard_metrics_for_health(
            completion_percentage=items_completion_pct,
            current_velocity_items=velocity_items,
            velocity_cv=velocity_cv,
            trend_direction=trend_direction,
            recent_velocity_change=recent_velocity_change,
            schedule_variance_days=schedule_variance_days,
            completion_confidence=completion_confidence,
        )

        logger.info(
            f"[REPORT HEALTH] Input: completion_pct={items_completion_pct:.2f}, "
            f"velocity_items={velocity_items:.2f}, velocity_cv={velocity_cv:.2f}, "
            f"trend={trend_direction}, recent_change={recent_velocity_change:.2f}, "
            f"schedule_var={schedule_variance_days:.2f}, "
            f"confidence={completion_confidence}, "
            f"scope_change_rate={scope_change_rate:.2f}"
        )

        health_result = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_for_health,
            dora_metrics=extended_metrics.get("dora"),
            flow_metrics=extended_metrics.get("flow"),
            bug_metrics=extended_metrics.get("bug_analysis"),
            budget_metrics=extended_metrics.get("budget"),
            scope_metrics={"scope_change_rate": scope_change_rate},
        )

        health_score = health_result["overall_score"]

        if health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 50:
            health_status = "CAUTION"
        elif health_score >= 30:
            health_status = "AT RISK"
        else:
            health_status = "CRITICAL"

        logger.info(
            f"[REPORT HEALTH] FINAL health_score={health_score}% "
            f"status={health_status} "
            f"(recalculated with schedule_variance_days={schedule_variance_days:.2f})"
        )
    else:
        logger.info(
            "[REPORT HEALTH] No deadline - recalculating health "
            "with all extended metrics"
        )
        health_result = calculate_comprehensive_project_health(
            dashboard_metrics=dashboard_metrics_for_health,
            dora_metrics=extended_metrics.get("dora"),
            flow_metrics=extended_metrics.get("flow"),
            bug_metrics=extended_metrics.get("bug_analysis"),
            budget_metrics=extended_metrics.get("budget"),
            scope_metrics={"scope_change_rate": scope_change_rate},
        )
        health_score = health_result["overall_score"]
        if health_score >= 70:
            health_status = "GOOD"
        elif health_score >= 50:
            health_status = "CAUTION"
        elif health_score >= 30:
            health_status = "AT RISK"
        else:
            health_status = "CRITICAL"

    return {
        "has_data": True,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
        "total_items": total_items,
        "total_points": total_points,
        "items_completion_pct": items_completion_pct,
        "points_completion_pct": points_completion_pct,
        "health_score": health_score,
        "health_status": health_status,
        "deadline": deadline,
        "deadline_months": deadline_months,
        "milestone": milestone,
        "forecast_date": forecast_date,
        "forecast_date_items": forecast_date_items,
        "forecast_date_points": forecast_date_points,
        "forecast_months": forecast_months,
        "forecast_metric": forecast_metric,
        "velocity_items": velocity_items,
        "velocity_points": velocity_points,
        "velocity_items_recent_4w": velocity_items_recent_4w,
        "velocity_points_recent_4w": velocity_points_recent_4w,
        "weeks_count": weeks_count,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "pert_time_items_weeks": (pert_time_items / 7.0) if pert_time_items else 0,
        "pert_time_points_weeks": (pert_time_points / 7.0) if pert_time_points else 0,
        "show_points": show_points,
        "health_dimensions": health_result.get("dimensions", {}),
        "velocity_cv": velocity_cv,
        "trend_direction": trend_direction,
        "recent_velocity_change": recent_velocity_change,
        "schedule_variance_days": schedule_variance_days,
        "completion_confidence": completion_confidence,
        "scope_change_rate": scope_change_rate,
        "forecast_weeks_items": (pert_time_items / 7.0) if pert_time_items else 0,
    }
