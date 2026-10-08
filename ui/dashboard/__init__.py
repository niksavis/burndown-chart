from __future__ import annotations

import logging
from datetime import datetime, timedelta

from dash import html

from data.persistence import load_unified_project_data
from ui.budget_section import _create_budget_section
from ui.dashboard.activity_quality import (
    create_quality_scope_section,
    create_recent_activity_section,
)
from ui.dashboard.executive_summary import (
    create_executive_summary_section,
)
from ui.dashboard.forecast_analytics import (
    create_forecast_analytics_section,
    get_forecast_history,
)
from ui.dashboard.insights_engine import (
    create_insights_section,
)
from ui.dashboard.throughput_analytics import (
    create_throughput_analytics_section,
)
from ui.dashboard.utils import (
    calculate_project_health_score,
    create_metric_card,
    create_mini_sparkline,
    create_progress_ring,
    format_date_relative,
    get_brief_health_reason,
    get_health_status,
    safe_divide,
)

__all__ = [
    "safe_divide",
    "format_date_relative",
    "calculate_project_health_score",
    "get_health_status",
    "get_brief_health_reason",
    "create_metric_card",
    "create_mini_sparkline",
    "create_progress_ring",
    "create_executive_summary_section",
    "create_throughput_analytics_section",
    "get_forecast_history",
    "create_forecast_analytics_section",
    "create_recent_activity_section",
    "create_quality_scope_section",
    "create_insights_section",
    "create_comprehensive_dashboard",
]


def create_comprehensive_dashboard(
    statistics_df,
    statistics_df_unfiltered,
    pert_time_items,
    pert_time_points,
    avg_weekly_items,
    avg_weekly_points,
    med_weekly_items,
    med_weekly_points,
    days_to_deadline,
    total_items,
    total_points,
    deadline_str,
    show_points=True,
    additional_context=None,
    data_points_count=None,
):

    unified_data = load_unified_project_data()
    project_scope = unified_data.get("project_scope", {})

    total_items = project_scope.get("remaining_items", 0)
    total_points = project_scope.get("remaining_total_points", 0)

    forecast_days = (
        pert_time_points if (show_points and pert_time_points) else pert_time_items
    )

    logger = logging.getLogger(__name__)

    logger.info("[DASHBOARD] Using current remaining work (independent of slider):")
    logger.info(
        f"  data_points_count={data_points_count or 'all'}, "
        f"total_items={total_items}, total_points={total_points}"
    )

    logger.info(
        f"[DASHBOARD PERT] Input PERT values: pert_time_items={pert_time_items}, "
        f"pert_time_points={pert_time_points}, show_points={show_points}, "
        f"chosen forecast_days={forecast_days}"
    )

    schedule_variance_calc = (
        (days_to_deadline - forecast_days)
        if (forecast_days and days_to_deadline)
        else 0
    )
    logger.info(
        f"[APP SCHEDULE] forecast_days={forecast_days}, "
        f"days_to_deadline={days_to_deadline}, "
        f"schedule_variance={schedule_variance_calc}"
    )

    last_date = (
        statistics_df["date"].iloc[-1]
        if not statistics_df.empty and "date" in statistics_df.columns
        else datetime.now()
    )

    formatted_last_date = (
        last_date.strftime("%Y-%m-%d") if hasattr(last_date, "strftime") else last_date
    )
    completion_date = (
        (last_date + timedelta(days=forecast_days)).strftime("%Y-%m-%d")
        if forecast_days
        else "None"
    )
    logger.info(
        f"[DASHBOARD FORECAST] last_date={formatted_last_date}, "
        f"forecast_days={forecast_days}, statistics_rows={len(statistics_df)}, "
        f"completion_date={completion_date}"
    )

    forecast_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "velocity_cv": 25,
        "schedule_variance_days": schedule_variance_calc,
        "last_date": last_date,
        "completion_date": (last_date + timedelta(days=forecast_days)).strftime(
            "%Y-%m-%d"
        )
        if forecast_days
        else None,
    }

    velocity_std = 0
    velocity_mean = 0

    if not statistics_df.empty and len(statistics_df) >= 4:
        velocity_std = statistics_df["completed_items"].std(ddof=0)
        velocity_mean = statistics_df["completed_items"].mean()
        if velocity_mean > 0:
            forecast_data["velocity_cv"] = (velocity_std / velocity_mean) * 100
            logger.info(
                f"[HEALTH DEBUG] Velocity CV calculation: std={velocity_std:.2f}, "
                f"mean={velocity_mean:.2f}, CV={forecast_data['velocity_cv']:.2f}%, "
                f"statistics_rows={len(statistics_df)}"
            )

    forecast_days = pert_time_points if pert_time_points else pert_time_items

    def calculate_deadline_probability(
        forecast, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    ):
        if not forecast or velocity_mean <= 0 or velocity_std <= 0:
            return 75 if (forecast or 0) <= (days_to_deadline or 0) else 25

        cv_ratio = velocity_std / velocity_mean
        weeks_remaining = max(1, forecast / 7)
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5
        forecast_std_days = forecast * cv_ratio * uncertainty_factor

        if days_to_deadline > 0 and forecast_std_days > 0:
            z_score = (days_to_deadline - forecast) / forecast_std_days
            return 100 / (1 + 2.718 ** (-1.7 * z_score))
        else:
            return 75 if forecast <= days_to_deadline else 25

    weeks_observed = len(statistics_df) if not statistics_df.empty else 1
    deadline_probability_items = calculate_deadline_probability(
        pert_time_items, days_to_deadline, velocity_mean, velocity_std, weeks_observed
    )
    deadline_probability_points = (
        calculate_deadline_probability(
            pert_time_points,
            days_to_deadline,
            velocity_mean,
            velocity_std,
            weeks_observed,
        )
        if pert_time_points
        else None
    )

    if forecast_days and velocity_mean > 0 and velocity_std > 0:
        cv_ratio = velocity_std / velocity_mean

        weeks_remaining = max(1, forecast_days / 7)
        uncertainty_factor = (weeks_remaining / weeks_observed) ** 0.5

        forecast_std_days = forecast_days * cv_ratio * uncertainty_factor

        ci_50_days = forecast_days
        ci_95_days = forecast_days + (1.65 * forecast_std_days)

        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )
    else:
        ci_50_days = forecast_days if forecast_days else 0
        ci_95_days = (forecast_days + 14) if forecast_days else 0
        deadline_probability = (
            deadline_probability_points
            if pert_time_points
            else deadline_probability_items
        )

    final_deadline_prob = (
        deadline_probability if deadline_probability is not None else 75
    )

    confidence_data = {
        "ci_50": max(0, ci_50_days),
        "ci_80": pert_time_items if pert_time_items else 0,
        "ci_95": max(0, ci_95_days),
        "deadline_probability": max(0, min(100, final_deadline_prob)),
        "deadline_probability_items": max(0, min(100, deadline_probability_items)),
        "deadline_probability_points": max(0, min(100, deadline_probability_points))
        if deadline_probability_points
        else None,
    }

    settings = {
        "total_items": total_items,
        "total_points": total_points,
        "deadline": deadline_str,
        "show_points": show_points,
        "extended_metrics": additional_context.get("extended_metrics", {})
        if additional_context
        else {},
    }

    budget_data = additional_context.get("budget_data") if additional_context else None

    pert_optimistic_days = 0
    pert_pessimistic_days = 0
    if pert_time_items and velocity_mean > 0 and velocity_std > 0:
        cv_ratio = velocity_std / velocity_mean
        optimistic_factor = 1 - cv_ratio
        pessimistic_factor = 1 + (1.5 * cv_ratio)
        pert_optimistic_days = max(1, pert_time_items * max(0.5, optimistic_factor))
        pert_pessimistic_days = pert_time_items * pessimistic_factor
    elif pert_time_items:
        pert_optimistic_days = pert_time_items * 0.75
        pert_pessimistic_days = pert_time_items * 1.25

    pert_data = {
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "pert_optimistic_days": pert_optimistic_days,
        "pert_pessimistic_days": pert_pessimistic_days,
        "last_date": last_date,
    }

    return html.Div(
        [
            create_executive_summary_section(
                statistics_df, forecast_data, settings, avg_weekly_items
            ),
            create_throughput_analytics_section(
                statistics_df,
                forecast_data,
                settings,
                data_points_count,
                additional_context,
            ),
            create_recent_activity_section(
                statistics_df_unfiltered, show_points, additional_context
            ),
            create_forecast_analytics_section(
                forecast_data,
                confidence_data,
                budget_data=budget_data,
                show_points=show_points,
                remaining_items=total_items,
                remaining_points=total_points,
                avg_weekly_items=avg_weekly_items,
                avg_weekly_points=avg_weekly_points,
                days_to_deadline=days_to_deadline,
                deadline_str=deadline_str,
            ),
            _create_budget_section(
                profile_id=additional_context.get("profile_id", "")
                if additional_context
                else "",
                query_id=additional_context.get("query_id", "")
                if additional_context
                else "",
                week_label=additional_context.get("current_week_label", "")
                if additional_context
                else "",
                budget_data=budget_data,
                points_available=show_points,
                data_points_count=data_points_count or 12,
            ),
            create_quality_scope_section(statistics_df, settings),
            create_insights_section(
                statistics_df,
                settings,
                budget_data,
                pert_data=pert_data,
                deadline=settings.get("deadline") if settings else None,
            ),
        ],
        className="dashboard-comprehensive",
    )
