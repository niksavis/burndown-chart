import logging
from datetime import datetime
from typing import Any

import pandas as pd

from data.budget_calculator import (
    calculate_budget_consumed,
    calculate_cost_breakdown_by_type,
    calculate_runway,
    get_budget_baseline_vs_actual,
)
from data.iso_week_bucketing import get_week_label
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def calculate_weekly_breakdown(statistics: list[dict]) -> list[dict]:

    if not statistics:
        return []

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.strftime("%Y-W%U")  # type: ignore

    weekly = (
        df.groupby("week")
        .agg(
            {
                "created_items": "sum",
                "completed_items": "sum",
                "created_points": "sum",
                "completed_points": "sum",
            }
        )
        .reset_index()
    )

    weekly_data = []
    for _, row in weekly.iterrows():
        weekly_data.append(
            {
                "date": row["week"],
                "created_items": int(row["created_items"]),
                "completed_items": int(row["completed_items"]),
                "created_points": int(row["created_points"]),
                "completed_points": int(row["completed_points"]),
            }
        )

    return weekly_data


def calculate_budget_metrics(
    profile_id: str,
    query_id: str,
    weeks_count: int,
    velocity_items: float = 0.0,
    velocity_points: float = 0.0,
) -> dict[str, Any]:

    logger.info(f"Calculating budget metrics for {profile_id}/{query_id}")

    backend = get_backend()
    budget_settings = backend.get_budget_settings(profile_id, query_id)

    if not budget_settings:
        logger.info("No budget configured for query")
        return {"has_data": False}

    revisions = backend.get_budget_revisions(profile_id, query_id) or []

    time_allocated = budget_settings.get("time_allocated_weeks", 0)
    cost_per_week = budget_settings.get("team_cost_per_week_eur", 0.0)
    budget_total = budget_settings.get("budget_total_eur", 0.0)
    currency = budget_settings.get("currency_symbol", "€")

    current_week = get_week_label(datetime.now())

    try:
        consumed_eur, budget_total_calc, consumed_pct = calculate_budget_consumed(
            profile_id, query_id, current_week
        )

        runway_weeks, burn_rate = calculate_runway(
            profile_id, query_id, current_week, data_points_count=weeks_count
        )

        cost_breakdown = calculate_cost_breakdown_by_type(
            profile_id, query_id, current_week
        )

        baseline_vs_actual = get_budget_baseline_vs_actual(
            profile_id, query_id, current_week, data_points_count=weeks_count
        )
        variance_metrics = baseline_vs_actual.get("variance", {})

        cost_per_item = cost_per_week / velocity_items if velocity_items > 0 else 0
        cost_per_point = cost_per_week / velocity_points if velocity_points > 0 else 0

        if runway_weeks == float("inf"):
            runway_weeks = 999999

        logger.info(
            f"Budget metrics calculated: consumed={consumed_pct:.1f}%, "
            f"runway={runway_weeks:.1f}w, burn_rate={burn_rate:.2f}, "
            f"variance_pct={variance_metrics.get('burn_rate_variance_pct', 0):.1f}%"
        )

    except Exception as e:
        logger.error(f"Failed to calculate budget metrics: {e}", exc_info=True)
        consumed_eur = 0.0
        consumed_pct = 0.0
        burn_rate = cost_per_week
        runway_weeks = 0
        cost_breakdown = {}
        cost_per_item = 0.0
        cost_per_point = 0.0
        variance_metrics = {}

    return {
        "has_data": True,
        "time_allocated_weeks": time_allocated,
        "cost_per_week": cost_per_week,
        "budget_total": budget_total,
        "currency_symbol": currency,
        "consumed_amount": consumed_eur,
        "consumed_percentage": consumed_pct,
        "remaining_amount": budget_total - consumed_eur,
        "runway_weeks": runway_weeks,
        "revision_count": len(revisions),
        "burn_rate": burn_rate,
        "cost_per_item": cost_per_item,
        "cost_per_point": cost_per_point,
        "cost_breakdown": cost_breakdown,
        "burn_rate_variance_pct": variance_metrics.get("burn_rate_variance_pct", 0),
        "runway_vs_baseline_pct": variance_metrics.get("runway_vs_baseline_pct", 0),
        "utilization_vs_pace_pct": variance_metrics.get("utilization_vs_pace_pct", 0),
    }


def calculate_historical_burndown(
    statistics: list[dict], project_scope: dict
) -> dict[str, list]:
    if not statistics:
        return {"dates": [], "remaining_items": [], "remaining_points": []}

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.sort_values("date")

    current_remaining_items = project_scope.get("remaining_items", 0)
    current_remaining_points = project_scope.get("remaining_total_points", 0)

    df["cumulative_completed_items"] = df["completed_items"][::-1].cumsum()[::-1]
    df["cumulative_completed_points"] = df["completed_points"][::-1].cumsum()[::-1]

    df["historical_remaining_items"] = (
        current_remaining_items + df["cumulative_completed_items"]
    )
    df["historical_remaining_points"] = (
        current_remaining_points + df["cumulative_completed_points"]
    )

    dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
    remaining_items = [round(x) for x in df["historical_remaining_items"]]
    remaining_points = [round(x) for x in df["historical_remaining_points"]]

    return {
        "dates": dates,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
    }
