"""
Dashboard Tab Renderer

Renders the tab-dashboard content including budget, DORA metrics,
flow metrics, and bug analysis data preparation.

All business logic delegated to data/ modules; this module coordinates
the data loading and hands off to ui.dashboard for rendering.
"""

import logging
from datetime import datetime, timedelta

import pandas as pd

from callbacks.visualization_helpers.extended_metrics import load_extended_metrics
from data import calculate_weekly_averages, compute_cumulative_values
from ui.dashboard import create_comprehensive_dashboard
from visualization import create_forecast_plot

logger = logging.getLogger("burndown_chart")


def _render_dashboard_tab(
    df: pd.DataFrame,
    settings: dict,
    show_points: bool,
) -> object:
    """
    Render the dashboard tab content.

    Loads budget, DORA, flow, and bug metrics then delegates
    to create_comprehensive_dashboard for rendering.

    Args:
        df: Raw statistics DataFrame (unfiltered, not yet cumulative).
        settings: Current application settings dictionary.
        show_points: Whether story-points tracking is enabled.

    Returns:
        Rendered dashboard content (html.Div).
    """
    from data.time_period_calculator import format_year_week, get_iso_week

    pert_factor = settings.get("pert_factor", 1.2)
    deadline = settings.get("deadline") or None
    data_points_count = int(settings.get("data_points_count", 12))
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    show_milestone = settings.get("show_milestone", False)
    milestone = settings.get("milestone", None) if show_milestone else None

    df_unfiltered = df.copy()

    if not df.empty:
        if data_points_count is not None and data_points_count > 0:
            logger.info(f"Filtering dashboard data by {data_points_count} weeks")

            weeks = []
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
                current_date = df["date"].max()
            else:
                current_date = datetime.now()

            for _i in range(data_points_count):
                year, week = get_iso_week(current_date)
                week_label = format_year_week(year, week)
                weeks.append(week_label)
                current_date = current_date - timedelta(days=7)

            week_labels = set(reversed(weeks))

            if "week_label" in df.columns:
                df = df[df["week_label"].isin(week_labels)]
                df = df.sort_values("date", ascending=True)
                logger.info(f"Filtered to {len(df)} rows using week_label matching")
            else:
                df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
                df = df.dropna(subset=["date"]).sort_values("date", ascending=True)
                latest_date = df["date"].max()
                cutoff_date = latest_date - timedelta(weeks=data_points_count)
                df = df[df["date"] >= cutoff_date]
                logger.warning(
                    "No week_label column - using date range filtering (less accurate)"
                )

        df = compute_cumulative_values(df, total_items, total_points)
        df_unfiltered = compute_cumulative_values(
            df_unfiltered, total_items, total_points
        )

    _, pert_data = create_forecast_plot(
        df=df,
        total_items=total_items,
        total_points=total_points,
        pert_factor=pert_factor,
        deadline_str=deadline,
        milestone_str=milestone,
        data_points_count=None,
        show_points=show_points,
    )

    (
        avg_weekly_items,
        avg_weekly_points,
        med_weekly_items,
        med_weekly_points,
    ) = calculate_weekly_averages(
        df.to_dict("records") if not df.empty else [],
        data_points_count=data_points_count,
    )

    from data.processing import calculate_velocity_from_dataframe

    velocity_for_health_items = calculate_velocity_from_dataframe(df, "completed_items")
    velocity_for_health_points = calculate_velocity_from_dataframe(
        df, "completed_points"
    )

    try:
        deadline_date = pd.to_datetime(deadline) if deadline else pd.NaT
        if pd.isna(deadline_date):
            days_to_deadline = 0
        else:
            last_date = (
                df["date"].iloc[-1].date()
                if not df.empty and "date" in df.columns
                else datetime.now().date()
            )
            days_to_deadline = max(0, (deadline_date.date() - last_date).days)
    except Exception:
        days_to_deadline = 0

    profile_id, query_id, current_week_label, budget_data = _load_budget_data(
        data_points_count, pert_data
    )

    extended_metrics = load_extended_metrics(
        profile_id, query_id, data_points_count, current_week_label
    )

    return create_comprehensive_dashboard(
        statistics_df=df,
        statistics_df_unfiltered=df_unfiltered,
        pert_time_items=pert_data["pert_time_items"],
        pert_time_points=pert_data["pert_time_points"],
        avg_weekly_items=velocity_for_health_items,
        avg_weekly_points=velocity_for_health_points,
        med_weekly_items=med_weekly_items,
        med_weekly_points=med_weekly_points,
        days_to_deadline=days_to_deadline,
        total_items=total_items,
        total_points=total_points,
        data_points_count=data_points_count,
        deadline_str=deadline,
        show_points=show_points,
        additional_context={
            "profile_id": profile_id,
            "query_id": query_id,
            "current_week_label": current_week_label,
            "budget_data": budget_data,
            "extended_metrics": extended_metrics,
        },
    )


def _load_budget_data(
    data_points_count: int,
    pert_data: dict,
) -> tuple[str, str, str, dict | None]:
    """
    Load budget metrics for the dashboard.

    Args:
        data_points_count: Number of weeks to include.
        pert_data: PERT forecast data dict from create_forecast_plot.

    Returns:
        Tuple of (profile_id, query_id, current_week_label, budget_data).
        budget_data is None when not configured or on error.
    """
    import math

    from data.iso_week_bucketing import get_week_label

    budget_data = None
    profile_id = ""
    query_id = ""
    current_week_label = ""
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()
        profile_id = backend.get_app_state("active_profile_id") or ""
        query_id = backend.get_app_state("active_query_id") or ""
        current_week_label = get_week_label(datetime.now())

        logger.info(
            f"[BUDGET DEBUG] profile_id={profile_id}, query_id={query_id}, "
            f"week={current_week_label}"
        )

        if profile_id and query_id:
            from data.budget_calculator import (
                _get_current_budget,
                calculate_cost_breakdown_by_type,
                calculate_weekly_cost_breakdowns,
                get_budget_baseline_vs_actual,
            )

            budget_config = _get_current_budget(profile_id, query_id)
            logger.info(f"[BUDGET DEBUG] budget_config={budget_config}")

            if budget_config:
                pert_forecast_weeks = None
                last_date = None
                if pert_data and pert_data.get("pert_time_items"):
                    pert_time_items = pert_data["pert_time_items"]
                    last_date = pert_data.get("last_date")
                    if pert_time_items and pert_time_items > 0:
                        pert_forecast_weeks = pert_time_items / 7.0

                baseline_comparison = get_budget_baseline_vs_actual(
                    profile_id,
                    query_id,
                    current_week_label,
                    data_points_count,
                    pert_forecast_weeks,
                )
                logger.info(
                    f"[BUDGET DEBUG] Baseline comparison calculated: "
                    f"variance={baseline_comparison['variance']}"
                )

                consumed_eur = baseline_comparison["actual"]["consumed_eur"]
                budget_total = baseline_comparison["baseline"]["budget_total_eur"]
                consumed_pct = baseline_comparison["actual"]["consumed_pct"]
                burn_rate = baseline_comparison["actual"]["burn_rate"]
                runway_weeks = baseline_comparison["actual"]["runway_weeks"]
                cost_per_item = baseline_comparison["actual"]["cost_per_item"]
                cost_per_point = baseline_comparison["actual"]["cost_per_point"]

                cost_breakdown = calculate_cost_breakdown_by_type(
                    profile_id, query_id, current_week_label
                )
                logger.info(f"[BUDGET DEBUG] breakdown={cost_breakdown}")

                weekly_breakdowns, weekly_breakdown_labels = (
                    calculate_weekly_cost_breakdowns(
                        profile_id,
                        query_id,
                        current_week_label,
                        data_points_count,
                    )
                )
                logger.info(
                    "[BUDGET DEBUG] weekly_breakdowns "
                    f"count={len(weekly_breakdowns)}, "
                    f"labels={weekly_breakdown_labels}"
                )

                weekly_burn_rates = [
                    sum(
                        flow_type_data.get("cost", 0)
                        for flow_type_data in breakdown.values()
                    )
                    for breakdown in weekly_breakdowns
                ]
                weekly_labels = weekly_breakdown_labels

                runway_str = (
                    "inf" if math.isinf(runway_weeks) else f"{runway_weeks:.1f}"
                )
                logger.info(
                    "Budget data calculated: "
                    f"{consumed_pct:.1f}% consumed, "
                    f"runway={runway_str} weeks, "
                    f"cost_per_item={cost_per_item:.2f}"
                )

                budget_data = {
                    "configured": True,
                    "currency_symbol": budget_config.get("currency_symbol", "\u20ac"),
                    "consumed_pct": consumed_pct,
                    "consumed_eur": consumed_eur,
                    "budget_total": budget_total,
                    "burn_rate": burn_rate,
                    "runway_weeks": runway_weeks,
                    "breakdown": cost_breakdown,
                    "baseline_comparison": baseline_comparison,
                    "pert_forecast_weeks": pert_forecast_weeks,
                    "last_date": last_date,
                    "weekly_breakdowns": weekly_breakdowns,
                    "weekly_breakdown_labels": weekly_breakdown_labels,
                    "cost_per_item": cost_per_item,
                    "cost_per_point": cost_per_point,
                    "weekly_burn_rates": weekly_burn_rates,
                    "weekly_labels": weekly_labels,
                    "burn_trend_pct": 0,
                    "pert_cost_avg_item": None,
                    "pert_cost_avg_point": None,
                    "forecast_total": budget_total,
                    "forecast_low": budget_total * 0.9,
                    "forecast_high": budget_total * 1.1,
                }
            else:
                logger.debug(f"No budget configured for profile {profile_id}")
    except Exception as e:
        logger.error(f"Failed to calculate budget data: {e}", exc_info=True)
        budget_data = None

    return profile_id, query_id, current_week_label, budget_data
