"""Helper functions for report generation.

This module contains utility functions that support report generation
but don't fit into specific semantic groups (domain metrics, chart generation, etc.)
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_weekly_breakdown(statistics: List[Dict]) -> List[Dict]:
    """
    Calculate weekly breakdown of created/completed items and points.

    Args:
        statistics: List of daily statistics

    Returns:
        List of weekly aggregates with ISO week labels
    """
    if not statistics:
        return []

    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")  # type: ignore
    df["week"] = df["date"].dt.strftime("%Y-W%U")  # type: ignore

    # Group by week and aggregate
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

    # Convert to list of dicts with formatted week labels
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
) -> Dict[str, Any]:
    """
    Calculate budget metrics for report using proper budget calculator functions.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        weeks_count: Number of weeks in analysis period
        velocity_items: Items velocity for cost_per_item calculation (from dashboard)
        velocity_points: Story points velocity for cost_per_point calculation (from dashboard)

    Returns:
        Dictionary with budget metrics and weekly tracking data including cost breakdown
    """
    from data.persistence.factory import get_backend
    from data.budget_calculator import (
        calculate_budget_consumed,
        calculate_runway,
        calculate_cost_breakdown_by_type,
        get_budget_baseline_vs_actual,
    )
    from data.iso_week_bucketing import get_week_label

    logger.info(f"Calculating budget metrics for {profile_id}/{query_id}")

    backend = get_backend()
    budget_settings = backend.get_budget_settings(profile_id, query_id)

    if not budget_settings:
        logger.info("No budget configured for query")
        return {"has_data": False}

    # Get budget revisions for history
    revisions = backend.get_budget_revisions(profile_id, query_id) or []

    # Calculate latest budget state
    time_allocated = budget_settings.get("time_allocated_weeks", 0)
    cost_per_week = budget_settings.get("team_cost_per_week_eur", 0.0)
    budget_total = budget_settings.get("budget_total_eur", 0.0)
    currency = budget_settings.get("currency_symbol", "€")

    # Get current week for calculations
    current_week = get_week_label(datetime.now())

    # Use proper budget calculator functions (same as app)
    try:
        # Calculate consumption using actual budget calculator
        consumed_eur, budget_total_calc, consumed_pct = calculate_budget_consumed(
            profile_id, query_id, current_week
        )

        # Calculate runway using actual budget calculator
        runway_weeks, burn_rate = calculate_runway(
            profile_id, query_id, current_week, data_points_count=weeks_count
        )

        # Calculate cost breakdown by work type
        cost_breakdown = calculate_cost_breakdown_by_type(
            profile_id, query_id, current_week
        )

        # Get variance metrics for health calculator (includes burn_rate_variance_pct, etc.)
        baseline_vs_actual = get_budget_baseline_vs_actual(
            profile_id, query_id, current_week, data_points_count=weeks_count
        )
        variance_metrics = baseline_vs_actual.get("variance", {})

        # Use velocity from dashboard (already calculated in report) for accurate cost per item/point
        # This ensures consistency with the velocity shown in the dashboard section
        cost_per_item = cost_per_week / velocity_items if velocity_items > 0 else 0
        cost_per_point = cost_per_week / velocity_points if velocity_points > 0 else 0

        # Use 999999 as sentinel for infinity (Jinja2 compatible)
        if runway_weeks == float("inf"):
            runway_weeks = 999999

        logger.info(
            f"Budget metrics calculated: consumed={consumed_pct:.1f}%, "
            f"runway={runway_weeks:.1f}w, burn_rate={burn_rate:.2f}, "
            f"variance_pct={variance_metrics.get('burn_rate_variance_pct', 0):.1f}%"
        )

    except Exception as e:
        logger.error(f"Failed to calculate budget metrics: {e}", exc_info=True)
        # Fallback to basic calculations
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
        # Add variance metrics for health calculator
        "burn_rate_variance_pct": variance_metrics.get("burn_rate_variance_pct", 0),
        "runway_vs_baseline_pct": variance_metrics.get("runway_vs_baseline_pct", 0),
        "utilization_vs_pace_pct": variance_metrics.get("utilization_vs_pace_pct", 0),
    }


def calculate_historical_burndown(
    statistics: List[Dict], project_scope: Dict
) -> Dict[str, List]:
    """Calculate historical remaining work for burndown chart."""
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

    # Format dates and convert to lists
    dates = [d.strftime("%Y-%m-%d") for d in df["date"]]
    remaining_items = [round(x) for x in df["historical_remaining_items"]]
    remaining_points = [round(x) for x in df["historical_remaining_points"]]

    return {
        "dates": dates,
        "remaining_items": remaining_items,
        "remaining_points": remaining_points,
    }
