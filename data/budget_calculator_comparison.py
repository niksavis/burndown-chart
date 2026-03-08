"""
Budget Calculator - Baseline vs Actual Comparison

Comprehensive baseline vs actual budget comparison with health indicators and insights.
Single source of truth for all budget variance calculations (DRY principle).

Public:
- get_budget_baseline_vs_actual(): Full baseline/actual/variance/health report
"""

import logging
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from data.budget_calculator_consumption import (
    calculate_budget_consumed,
    calculate_runway,
)
from data.budget_calculator_core import (
    _get_current_budget,
    _get_velocity,
    _get_velocity_points,
)

logger = logging.getLogger(__name__)


def get_budget_baseline_vs_actual(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 12,
    pert_forecast_weeks: float | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    """
    Calculate comprehensive baseline vs actual budget comparison.

    Single source of truth for all budget variance calculations.
    Eliminates code duplication across budget cards (DRY principle).

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: Current ISO week label
        data_points_count: Number of weeks for trend calculations
        pert_forecast_weeks: Optional PERT forecast weeks for comparison
        db_path: Optional database path

    Returns:
        Dict with baseline, actual, variance, health status, and insights:
        {
            "baseline": {
                "time_allocated_weeks": int,
                "team_cost_per_week_eur": float,
                "budget_total_eur": float,
                "start_date": str (ISO),
                "allocated_end_date": str (ISO),
                "currency_symbol": str
            },
            "actual": {
                "elapsed_weeks": float,
                "elapsed_pct": float,
                "consumed_eur": float,
                "consumed_pct": float,
                "burn_rate": float,
                "runway_weeks": float,
                "runway_end_date": str (ISO),
                "velocity_items": float,
                "velocity_points": float,
                "cost_per_item": float,
                "cost_per_point": float
            },
            "variance": {
                "utilization_vs_pace_pct": float,
                "burn_rate_variance_eur": float,
                "burn_rate_variance_pct": float,
                "runway_vs_baseline_weeks": float,
                "runway_vs_baseline_pct": float,
                "runway_vs_forecast_weeks": float (optional),
                "cost_per_item_variance_eur": float,
                "cost_per_item_variance_pct": float,
                "projected_total_spend": float,
                "projected_surplus_eur": float
            },
            "health": {
                "burn_rate_health": str (green/yellow/orange/red),
                "runway_health": str,
                "pace_health": str,
                "overall_status": str
            },
            "insights": List[str]
        }

    Example:
        >>> data = get_budget_baseline_vs_actual("p1", "q1", "2026-W02")
        >>> print(data["variance"]["burn_rate_variance_pct"])
        -43.4
        >>> print(data["insights"][0])
        "Spending 43.4% below budgeted rate"
    """
    from data.database import get_db_connection

    try:
        # Get baseline budget configuration
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget:
            return _empty_baseline_comparison()

        # Get budget start date from database
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()
            cursor.execute(
                (
                    "SELECT created_at FROM budget_settings "
                    "WHERE profile_id = ? AND query_id = ?"
                ),
                (profile_id, query_id),
            )
            result = cursor.fetchone()
            if not result:
                return _empty_baseline_comparison()

            start_date_str = result[0]
            try:
                start_date = datetime.fromisoformat(
                    start_date_str.replace("Z", "+00:00")
                )
                # Ensure timezone-aware for consistent comparison
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=UTC)
            except Exception:
                start_date = datetime.now(UTC)

        # Calculate baseline dates
        allocated_end_date = start_date + timedelta(
            weeks=budget["time_allocated_weeks"]
        )
        current_date = datetime.now(UTC)
        elapsed_days = (current_date - start_date).days
        elapsed_weeks = elapsed_days / 7.0
        elapsed_pct = (
            (elapsed_weeks / budget["time_allocated_weeks"] * 100.0)
            if budget["time_allocated_weeks"] > 0
            else 0.0
        )

        # Calculate actual metrics
        consumed_eur, budget_total, consumed_pct = calculate_budget_consumed(
            profile_id, query_id, week_label, db_path
        )
        runway_weeks, burn_rate = calculate_runway(
            profile_id, query_id, week_label, data_points_count, db_path
        )

        # Calculate runway end date
        if math.isinf(runway_weeks):
            runway_end_date_str = "N/A (no consumption)"
        elif runway_weeks < 0:
            runway_end_date_str = "Over budget"
        else:
            runway_end_date = current_date + timedelta(weeks=runway_weeks)
            runway_end_date_str = runway_end_date.date().isoformat()

        # Get velocities (using data_points_count for dynamic calculation)
        velocity_items = _get_velocity(
            profile_id, query_id, week_label, data_points_count, db_path
        )
        velocity_points = _get_velocity_points(
            profile_id, query_id, week_label, data_points_count, db_path
        )

        # Calculate costs per item/point
        cost_per_item = (
            (budget["team_cost_per_week_eur"] / velocity_items)
            if velocity_items > 0
            else 0.0
        )
        cost_per_point = (
            (budget["team_cost_per_week_eur"] / velocity_points)
            if velocity_points > 0
            else 0.0
        )

        # Calculate variances
        expected_utilization = elapsed_pct
        utilization_vs_pace_pct = consumed_pct - expected_utilization

        burn_rate_variance_eur = burn_rate - budget["team_cost_per_week_eur"]
        burn_rate_variance_pct = (
            (burn_rate_variance_eur / budget["team_cost_per_week_eur"] * 100.0)
            if budget["team_cost_per_week_eur"] > 0
            else 0.0
        )

        runway_vs_baseline_weeks = runway_weeks - budget["time_allocated_weeks"]
        runway_vs_baseline_pct = (
            (runway_vs_baseline_weeks / budget["time_allocated_weeks"] * 100.0)
            if budget["time_allocated_weeks"] > 0
            else 0.0
        )

        # Get baseline velocity from budget settings (not current velocity)
        assumed_baseline_velocity = budget.get("baseline_velocity_items", 3.5)
        assumed_baseline_velocity_points = budget.get("baseline_velocity_points", 21.0)

        budgeted_cost_per_item = (
            budget["team_cost_per_week_eur"] / assumed_baseline_velocity
        )
        cost_per_item_variance_eur = cost_per_item - budgeted_cost_per_item
        cost_per_item_variance_pct = (
            (cost_per_item_variance_eur / budgeted_cost_per_item * 100.0)
            if budgeted_cost_per_item > 0
            else 0.0
        )

        budgeted_cost_per_point = (
            budget["team_cost_per_week_eur"] / assumed_baseline_velocity_points
        )
        cost_per_point_variance_eur = cost_per_point - budgeted_cost_per_point
        cost_per_point_variance_pct = (
            (cost_per_point_variance_eur / budgeted_cost_per_point * 100.0)
            if budgeted_cost_per_point > 0
            else 0.0
        )

        # Project final spend if current pace continues
        if elapsed_weeks > 0:
            projected_total_spend = (consumed_eur / elapsed_weeks) * budget[
                "time_allocated_weeks"
            ]
        else:
            projected_total_spend = consumed_eur

        projected_surplus_eur = budget["budget_total_eur"] - projected_total_spend

        # Calculate health indicators
        burn_rate_health = _calculate_health_tier(burn_rate_variance_pct, inverse=True)
        runway_health = _calculate_health_tier(runway_vs_baseline_pct)
        pace_health = _calculate_health_tier(utilization_vs_pace_pct, inverse=True)

        # Determine overall status
        health_scores = {
            "green": 3,
            "yellow": 2,
            "orange": 1,
            "red": 0,
        }
        min_health = min(
            health_scores.get(burn_rate_health, 0),
            health_scores.get(runway_health, 0),
            health_scores.get(pace_health, 0),
        )
        overall_status = ["critical", "warning", "caution", "healthy"][min_health]

        # Generate insights
        insights = []

        if abs(burn_rate_variance_pct) > 5:
            if burn_rate_variance_pct < 0:
                insights.append(
                    f"Spending {abs(burn_rate_variance_pct):.1f}% below budgeted rate"
                )
            else:
                insights.append(
                    f"Spending {burn_rate_variance_pct:.1f}% above budgeted rate"
                )

        if abs(runway_vs_baseline_weeks) > 2:
            if runway_vs_baseline_weeks > 0:
                insights.append(
                    f"Budget will last {runway_vs_baseline_weeks:.1f} weeks "
                    "longer than allocated"
                )
            else:
                insights.append(
                    f"Budget will run out "
                    f"{abs(runway_vs_baseline_weeks):.1f} weeks before "
                    "allocated end"
                )

        if abs(projected_surplus_eur) > budget["budget_total_eur"] * 0.1:
            surplus_pct = projected_surplus_eur / budget["budget_total_eur"] * 100.0
            if projected_surplus_eur > 0:
                insights.append(
                    f"Projected surplus of {budget['currency_symbol']}"
                    f"{abs(projected_surplus_eur):,.0f} "
                    f"({abs(surplus_pct):.1f}%)"
                )
            else:
                insights.append(
                    f"Projected deficit of {budget['currency_symbol']}"
                    f"{abs(projected_surplus_eur):,.0f} "
                    f"({abs(surplus_pct):.1f}%)"
                )

        if velocity_items > assumed_baseline_velocity:
            velocity_improvement = (
                (velocity_items - assumed_baseline_velocity)
                / assumed_baseline_velocity
                * 100.0
            )
            insights.append(
                f"Higher velocity ({velocity_items:.1f} vs "
                f"{assumed_baseline_velocity:.1f}, "
                f"+{velocity_improvement:.0f}%) driving cost efficiency"
            )

        # Prepare return dict
        result = {
            "baseline": {
                "time_allocated_weeks": budget["time_allocated_weeks"],
                "team_cost_per_week_eur": budget["team_cost_per_week_eur"],
                "budget_total_eur": budget["budget_total_eur"],
                "start_date": start_date.date().isoformat(),
                "allocated_end_date": allocated_end_date.date().isoformat(),
                "currency_symbol": budget.get("currency_symbol", "EUR"),
                "assumed_baseline_velocity": assumed_baseline_velocity,
                "assumed_baseline_velocity_points": assumed_baseline_velocity_points,
            },
            "actual": {
                "elapsed_weeks": elapsed_weeks,
                "elapsed_pct": elapsed_pct,
                "consumed_eur": consumed_eur,
                "consumed_pct": consumed_pct,
                "burn_rate": burn_rate,
                "runway_weeks": runway_weeks,
                "runway_end_date": runway_end_date_str,
                "velocity_items": velocity_items,
                "velocity_points": velocity_points,
                "cost_per_item": cost_per_item,
                "cost_per_point": cost_per_point,
            },
            "variance": {
                "utilization_vs_pace_pct": utilization_vs_pace_pct,
                "burn_rate_variance_eur": burn_rate_variance_eur,
                "burn_rate_variance_pct": burn_rate_variance_pct,
                "runway_vs_baseline_weeks": runway_vs_baseline_weeks,
                "runway_vs_baseline_pct": runway_vs_baseline_pct,
                "cost_per_item_variance_eur": cost_per_item_variance_eur,
                "cost_per_item_variance_pct": cost_per_item_variance_pct,
                "cost_per_point_variance_eur": cost_per_point_variance_eur,
                "cost_per_point_variance_pct": cost_per_point_variance_pct,
                "projected_total_spend": projected_total_spend,
                "projected_surplus_eur": projected_surplus_eur,
            },
            "health": {
                "burn_rate_health": burn_rate_health,
                "runway_health": runway_health,
                "pace_health": pace_health,
                "overall_status": overall_status,
            },
            "insights": insights,
        }

        # Add forecast comparison if provided
        if pert_forecast_weeks is not None:
            result["variance"]["runway_vs_forecast_weeks"] = (
                runway_weeks - pert_forecast_weeks
            )
            if abs(runway_weeks - pert_forecast_weeks) > 4:
                if runway_weeks > pert_forecast_weeks:
                    insights.append(
                        "Budget runway exceeds forecast by "
                        f"{(runway_weeks - pert_forecast_weeks):.1f} weeks"
                    )
                else:
                    insights.append(
                        "Budget will run out "
                        f"{abs(runway_weeks - pert_forecast_weeks):.1f} weeks "
                        "before forecast completion"
                    )

        return result

    except Exception as e:
        logger.error(
            f"Failed to calculate budget baseline comparison: {e}", exc_info=True
        )
        return _empty_baseline_comparison()


def _calculate_health_tier(variance_pct: float, inverse: bool = False) -> str:
    """
    Calculate health tier from variance percentage.

    Args:
        variance_pct: Variance percentage (positive = over budget)
        inverse: If True, negative variance is good (under budget)

    Returns:
        Health tier: green, yellow, orange, or red
    """
    # Normalize so positive = bad
    if inverse:
        variance_pct = -variance_pct

    if variance_pct < -10:
        return "green"
    elif variance_pct < 10:
        return "yellow"
    elif variance_pct < 25:
        return "orange"
    else:
        return "red"


def _empty_baseline_comparison() -> dict[str, Any]:
    """Return empty baseline comparison structure."""
    return {
        "baseline": {
            "time_allocated_weeks": 0,
            "team_cost_per_week_eur": 0.0,
            "budget_total_eur": 0.0,
            "start_date": "",
            "allocated_end_date": "",
            "currency_symbol": "EUR",
            "assumed_baseline_velocity": 3.5,
            "assumed_baseline_velocity_points": 21.0,
        },
        "actual": {
            "elapsed_weeks": 0.0,
            "elapsed_pct": 0.0,
            "consumed_eur": 0.0,
            "consumed_pct": 0.0,
            "burn_rate": 0.0,
            "runway_weeks": 0.0,
            "runway_end_date": "",
            "velocity_items": 0.0,
            "velocity_points": 0.0,
            "cost_per_item": 0.0,
            "cost_per_point": 0.0,
        },
        "variance": {
            "utilization_vs_pace_pct": 0.0,
            "burn_rate_variance_eur": 0.0,
            "burn_rate_variance_pct": 0.0,
            "runway_vs_baseline_weeks": 0.0,
            "runway_vs_baseline_pct": 0.0,
            "cost_per_item_variance_eur": 0.0,
            "cost_per_item_variance_pct": 0.0,
            "cost_per_point_variance_eur": 0.0,
            "cost_per_point_variance_pct": 0.0,
            "projected_total_spend": 0.0,
            "projected_surplus_eur": 0.0,
        },
        "health": {
            "burn_rate_health": "green",
            "runway_health": "green",
            "pace_health": "green",
            "overall_status": "healthy",
        },
        "insights": [],
    }
