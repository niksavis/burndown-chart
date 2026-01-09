"""
Budget Calculator - Time-Based Cost Model

Implements flexible time-based budgeting at the profile level with SQLite persistence.
Uses team cost per time period as single source of truth, deriving cost per item/point
from velocity. Tracks budget revisions with preserved historical accuracy using cached
computed values.

Key Functions:
- get_budget_at_week(): Replay budget revisions to get budget at specific week
- calculate_budget_consumed(): Calculate consumption percentage
- calculate_cost_breakdown_by_type(): Cost breakdown by Flow Distribution types
- calculate_weekly_cost_breakdowns(): Weekly cost breakdowns for trend visualization
- calculate_runway(): Calculate budget runway weeks

Created: January 4, 2026
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List

logger = logging.getLogger(__name__)


def _get_current_budget(
    profile_id: str, query_id: str, db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Get current budget from budget_settings (already includes revisions).

    NOTE: budget_settings is always up-to-date after revisions. Do NOT replay revisions.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        db_path: Optional database path

    Returns:
        Dict with current budget or None if not configured
    """
    from data.database import get_db_connection

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT time_allocated_weeks, team_cost_per_week_eur,
                       budget_total_eur, currency_symbol, cost_rate_type,
                       baseline_velocity_items, baseline_velocity_points
                FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
            """,
                (profile_id, query_id),
            )

            result = cursor.fetchone()
            if not result:
                return None

            return {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
                "cost_rate_type": result[4] or "weekly",
                "baseline_velocity_items": result[5] or 3.5,  # Default to 3.5 if NULL
                "baseline_velocity_points": result[6]
                or 21.0,  # Default to 21.0 if NULL
            }
    except Exception as e:
        logger.error(f"Failed to get current budget: {e}")
        return None


def get_budget_at_week(
    profile_id: str, query_id: str, week_label: str, db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Get budget configuration at specific week by replaying revisions.

    Queries budget_settings and replays budget_revisions using cumulative delta logic.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label (e.g., "2025-W44")
        db_path: Optional database path (defaults to active profile)

    Returns:
        Dict with budget state at specified week, or None if budget not configured:
        {
            "time_allocated_weeks": int,
            "team_cost_per_week_eur": float,
            "budget_total_eur": float,
            "currency_symbol": str,
            "cost_rate_type": str
        }

    Example:
        >>> budget = get_budget_at_week("my_profile", "my_query", "2025-W44")
        >>> print(budget["budget_total_eur"])
        50000.0
    """
    from data.database import get_db_connection

    try:
        # Handle db_path None by using default
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            # Load base budget settings
            cursor.execute(
                """
                SELECT time_allocated_weeks, team_cost_per_week_eur,
                       budget_total_eur, currency_symbol, cost_rate_type,
                       baseline_velocity_items, baseline_velocity_points
                FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
            """,
                (profile_id, query_id),
            )

            result = cursor.fetchone()
            if not result:
                logger.debug(
                    f"No budget configured for profile {profile_id}, query {query_id}"
                )
                return None

            # Start with base settings
            budget = {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
                "cost_rate_type": result[4] or "weekly",
                "baseline_velocity_items": result[5] or 3.5,  # Default to 3.5 if NULL
                "baseline_velocity_points": result[6]
                or 21.0,  # Default to 21.0 if NULL
            }

            # Replay revisions up to specified week
            cursor.execute(
                """
                SELECT time_allocated_weeks_delta, team_cost_delta, budget_total_delta
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                  AND week_label <= ?
                ORDER BY week_label ASC
            """,
                (profile_id, query_id, week_label),
            )

            for row in cursor.fetchall():
                budget["time_allocated_weeks"] += row[0] or 0
                budget["team_cost_per_week_eur"] += row[1] or 0.0
                budget["budget_total_eur"] += row[2] or 0.0

            logger.info(
                f"Calculated budget for {profile_id}/{query_id} at {week_label}: {budget['budget_total_eur']:.2f}"
            )
            return budget

    except Exception as e:
        logger.error(f"Failed to get budget at week {week_label}: {e}")
        return None


def calculate_budget_consumed(
    profile_id: str, query_id: str, week_label: str, db_path: Optional[Path] = None
) -> Tuple[float, float, float]:
    """
    Calculate budget consumption percentage using current budget from budget_settings.

    NOTE: budget_settings always contains the CURRENT budget after revisions are applied.
    We do NOT replay revisions here - that would double-count deltas.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
        db_path: Optional database path

    Returns:
        Tuple of (consumed_eur, budget_total_eur, percentage)

    Example:
        >>> consumed, total, pct = calculate_budget_consumed("profile", "query", "2025-W44")
        >>> print(f"{pct:.1f}% consumed")
        75.5% consumed
    """
    from data.database import get_db_connection

    try:
        # Load budget directly from budget_settings (already contains current budget after revisions)
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            # Get current budget from budget_settings
            cursor.execute(
                """
                SELECT time_allocated_weeks, team_cost_per_week_eur,
                       budget_total_eur, currency_symbol
                FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
            """,
                (profile_id, query_id),
            )

            result = cursor.fetchone()
            if not result:
                return 0.0, 0.0, 0.0

            budget = {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
            }

            # Get completed work from project_statistics
            cursor.execute(
                """
                SELECT SUM(completed_items)
                FROM project_statistics
                WHERE profile_id = ?
                  AND query_id = ?
                  AND week_label <= ?
            """,
                (profile_id, query_id, week_label),
            )

            result = cursor.fetchone()
            completed_items = result[0] if result and result[0] else 0

        # Calculate cost from velocity (use default 4-week for historical calculation)
        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity > 0:
            cost_per_item = budget["team_cost_per_week_eur"] / velocity
            consumed_eur = completed_items * cost_per_item
        else:
            consumed_eur = 0.0

        budget_total = budget["budget_total_eur"]
        percentage = (consumed_eur / budget_total * 100) if budget_total > 0 else 0.0

        return consumed_eur, budget_total, percentage

    except Exception as e:
        logger.error(f"Failed to calculate budget consumed: {e}")
        return 0.0, 0.0, 0.0


def calculate_cost_breakdown_by_type(
    profile_id: str, query_id: str, week_label: str, db_path: Optional[Path] = None
) -> Dict[str, Dict[str, float]]:
    """
    Calculate cost breakdown by Flow Distribution work types.

    Uses flow_velocity metric snapshots which already contain work distribution data.
    Aggregates counts across all weeks and multiplies by cost per item.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label (used to get budget at specific week)
        db_path: Optional database path

    Returns:
        Dict mapping flow types to cost details:
        {
            "Feature": {"cost": 12500.0, "count": 25, "percentage": 62.5},
            "Defect": {"cost": 5000.0, "count": 10, "percentage": 25.0},
            "Technical Debt": {"cost": 2500.0, "count": 5, "percentage": 12.5},
            "Risk": {"cost": 0.0, "count": 0, "percentage": 0.0}
        }

    Example:
        >>> breakdown = calculate_cost_breakdown_by_type("profile", "query", "2025-W44")
        >>> print(f"Feature cost: €{breakdown['Feature']['cost']:.2f}")
        Feature cost: €12500.00
    """
    from data.metrics_snapshots import load_snapshots

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget:
            logger.info("[COST BREAKDOWN] No budget configured")
            return _empty_breakdown()

        # Get velocity and cost per item (use default 4-week for historical)
        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity <= 0:
            logger.info("[COST BREAKDOWN] Velocity is zero")
            return _empty_breakdown()

        cost_per_item = budget["team_cost_per_week_eur"] / velocity
        logger.info(f"[COST BREAKDOWN] Cost per item: €{cost_per_item:.2f}")

        # Load flow_velocity snapshots which contain work distribution data
        snapshots = load_snapshots()
        if not snapshots:
            logger.info("[COST BREAKDOWN] No metric snapshots found")
            return _empty_breakdown()

        # Aggregate distribution counts across all weeks
        flow_counts = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}

        for week, metrics in snapshots.items():
            velocity_data = metrics.get("flow_velocity", {})
            distribution = velocity_data.get("distribution", {})

            if distribution:
                # Map lowercase keys to proper flow type names
                flow_counts["Feature"] += distribution.get("feature", 0)
                flow_counts["Defect"] += distribution.get("defect", 0)
                flow_counts["Technical Debt"] += distribution.get("tech_debt", 0)
                flow_counts["Risk"] += distribution.get("risk", 0)

        total_items = sum(flow_counts.values())
        logger.info(
            f"[COST BREAKDOWN] Total items across all weeks: {total_items} "
            f"(Feature={flow_counts['Feature']}, Defect={flow_counts['Defect']}, "
            f"Tech Debt={flow_counts['Technical Debt']}, Risk={flow_counts['Risk']})"
        )

        if total_items == 0:
            logger.info("[COST BREAKDOWN] No completed items found in snapshots")
            return _empty_breakdown()

        # Calculate costs and percentages
        breakdown = {}
        for flow_type, count in flow_counts.items():
            cost = count * cost_per_item
            percentage = (count / total_items * 100) if total_items > 0 else 0.0
            breakdown[flow_type] = {
                "cost": cost,
                "count": count,
                "percentage": percentage,
            }
            logger.info(
                f"[COST BREAKDOWN] {flow_type}: {count} items, €{cost:.2f} ({percentage:.1f}%)"
            )

        return breakdown

    except Exception as e:
        logger.error(f"Failed to calculate cost breakdown: {e}", exc_info=True)
        return _empty_breakdown()


def calculate_runway(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 4,
    db_path: Optional[Path] = None,
) -> Tuple[float, float]:
    """
    Calculate budget runway weeks using weighted burn rate.

    Uses 4-week weighted average [0.1, 0.2, 0.3, 0.4] matching PERT pattern.
    Respects data_points_count filter.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
        data_points_count: Number of weeks for trend calculation (default: 4)
        db_path: Optional database path

    Returns:
        Tuple of (runway_weeks, weighted_burn_rate_eur_per_week)

    Example:
        >>> runway, burn_rate = calculate_runway("profile", "query", "2025-W44")
        >>> print(f"Runway: {runway:.1f} weeks at €{burn_rate:.2f}/week")
        Runway: 12.5 weeks at €4000.00/week
    """
    from data.database import get_db_connection
    from data.iso_week_bucketing import get_last_n_weeks

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget or budget["budget_total_eur"] <= 0:
            return 0.0, 0.0

        consumed, total, _ = calculate_budget_consumed(
            profile_id, query_id, week_label, db_path
        )
        remaining = total - consumed

        # Get last N weeks for burn rate calculation
        # Use last 4 weeks for weighted average (not data_points_count which could be larger)
        weeks_for_burn = min(data_points_count, 4)
        weights = [0.1, 0.2, 0.3, 0.4][:weeks_for_burn]
        weeks = get_last_n_weeks(weeks_for_burn)

        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            weekly_costs = []
            for week_info in weeks:
                wk_label = week_info[0]
                velocity = _get_velocity(profile_id, query_id, wk_label, 4, db_path)

                cursor.execute(
                    """
                    SELECT completed_items
                    FROM project_statistics
                    WHERE profile_id = ?
                      AND query_id = ?
                      AND week_label = ?
                """,
                    (profile_id, query_id, wk_label),
                )

                result = cursor.fetchone()
                completed = result[0] if result and result[0] else 0

                if velocity > 0:
                    cost_per_item = budget["team_cost_per_week_eur"] / velocity
                    weekly_cost = completed * cost_per_item
                else:
                    weekly_cost = 0.0

                weekly_costs.append(weekly_cost)
                logger.debug(
                    f"Week {wk_label}: completed={completed}, velocity={velocity:.2f}, "
                    f"cost={weekly_cost:.2f}"
                )

        # Calculate weighted burn rate
        if not weekly_costs or all(c == 0 for c in weekly_costs):
            return 0.0, 0.0

        weighted_burn_rate = sum(w * c for w, c in zip(weights, weekly_costs)) / sum(
            weights
        )

        if weighted_burn_rate > 0:
            runway_weeks = max(0, remaining / weighted_burn_rate)  # Clamp to 0 minimum
        else:
            runway_weeks = float("inf")

        return runway_weeks, weighted_burn_rate

    except Exception as e:
        logger.error(f"Failed to calculate runway: {e}")
        return 0.0, 0.0


def _get_velocity(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 4,
    db_path: Optional[Path] = None,
) -> float:
    """
    Get velocity from metrics_data_points or calculate from statistics.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
        data_points_count: Number of weeks to average (default 4)
        db_path: Optional database path

    Returns:
        float: Velocity (items per week)
    """
    from data.database import get_db_connection

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            # Try cached velocity first
            cursor.execute(
                """
                SELECT metric_value
                FROM metrics_data_points
                WHERE profile_id = ?
                  AND query_id = ?
                  AND snapshot_date = ?
                  AND metric_name = 'velocity'
            """,
                (profile_id, query_id, week_label),
            )

            result = cursor.fetchone()
            if result and result[0]:
                return float(result[0])

            # Fallback: calculate from project_statistics
            cursor.execute(
                """
                SELECT AVG(completed_items)
                FROM (
                    SELECT completed_items
                    FROM project_statistics
                    WHERE profile_id = ?
                      AND query_id = ?
                      AND week_label <= ?
                    ORDER BY week_label DESC
                    LIMIT ?
                )
            """,
                (profile_id, query_id, week_label, data_points_count),
            )

            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0

    except Exception as e:
        logger.error(f"Failed to get velocity: {e}")
        return 0.0


def _get_velocity_points(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 4,
    db_path: Optional[Path] = None,
) -> float:
    """
    Get velocity for story points from metrics_data_points or calculate from statistics.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
        data_points_count: Number of weeks to average (default 4)
        db_path: Optional database path

    Returns:
        float: Velocity (points per week)
    """
    from data.database import get_db_connection

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            # Try cached velocity_points first
            cursor.execute(
                """
                SELECT metric_value
                FROM metrics_data_points
                WHERE profile_id = ?
                  AND query_id = ?
                  AND snapshot_date = ?
                  AND metric_name = 'velocity_points'
            """,
                (profile_id, query_id, week_label),
            )

            result = cursor.fetchone()
            if result and result[0]:
                return float(result[0])

            # Fallback: calculate from project_statistics
            cursor.execute(
                """
                SELECT AVG(completed_points)
                FROM (
                    SELECT completed_points
                    FROM project_statistics
                    WHERE profile_id = ?
                      AND query_id = ?
                      AND week_label <= ?
                    ORDER BY week_label DESC
                    LIMIT ?
                )
            """,
                (profile_id, query_id, week_label, data_points_count),
            )

            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0

    except Exception as e:
        logger.error(f"Failed to get velocity_points: {e}")
        return 0.0


def calculate_weekly_cost_breakdowns(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 12,
    db_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, Dict[str, float]]], List[str]]:
    """
    Calculate cost breakdown by work type for each week in data_points_count window.

    Uses metric snapshots to get weekly distribution data, respecting data_points_count
    filter. Returns weekly breakdowns and corresponding week labels for sparkline charts.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: Current ISO week label
        data_points_count: Number of weeks to include (default 12)
        db_path: Optional database path

    Returns:
        Tuple of (weekly_breakdowns, weekly_labels):
        - weekly_breakdowns: List of dicts mapping flow types to cost details per week
        - weekly_labels: List of ISO week labels corresponding to breakdowns

    Example:
        >>> breakdowns, labels = calculate_weekly_cost_breakdowns("profile", "query", "2025-W44", 4)
        >>> print(labels)
        ['2025-W41', '2025-W42', '2025-W43', '2025-W44']
        >>> print(breakdowns[0]['Feature'])
        {'cost': 3125.50, 'count': 8}
    """
    from data.metrics_snapshots import get_metric_snapshot
    from data.iso_week_bucketing import get_last_n_weeks

    try:
        budget = _get_current_budget(profile_id, query_id, db_path)
        if not budget:
            logger.info("[WEEKLY COST BREAKDOWN] No budget configured")
            return [], []

        # Get velocity and cost per item (use default 4-week for historical)
        velocity = _get_velocity(profile_id, query_id, week_label, 4, db_path)
        if velocity <= 0:
            logger.info("[WEEKLY COST BREAKDOWN] Velocity is zero")
            return [], []

        cost_per_item = budget["team_cost_per_week_eur"] / velocity

        # Get week labels using same logic as Flow Metrics
        weeks = get_last_n_weeks(data_points_count)
        week_labels = [w[0] for w in weeks]

        weekly_breakdowns = []

        for week in week_labels:
            # Get flow velocity snapshot for this week
            week_snapshot = get_metric_snapshot(week, "flow_velocity")

            if week_snapshot:
                week_dist = week_snapshot.get("distribution", {})
                week_feature = week_dist.get("feature", 0)
                week_defect = week_dist.get("defect", 0)
                week_tech_debt = week_dist.get("tech_debt", 0)
                week_risk = week_dist.get("risk", 0)

                # Calculate costs for this week
                breakdown = {
                    "Feature": {
                        "cost": week_feature * cost_per_item,
                        "count": week_feature,
                    },
                    "Defect": {
                        "cost": week_defect * cost_per_item,
                        "count": week_defect,
                    },
                    "Technical Debt": {
                        "cost": week_tech_debt * cost_per_item,
                        "count": week_tech_debt,
                    },
                    "Risk": {
                        "cost": week_risk * cost_per_item,
                        "count": week_risk,
                    },
                }
            else:
                # No snapshot for this week - empty breakdown
                breakdown = {
                    "Feature": {"cost": 0.0, "count": 0},
                    "Defect": {"cost": 0.0, "count": 0},
                    "Technical Debt": {"cost": 0.0, "count": 0},
                    "Risk": {"cost": 0.0, "count": 0},
                }

            weekly_breakdowns.append(breakdown)

        logger.info(
            f"[WEEKLY COST BREAKDOWN] Calculated {len(weekly_breakdowns)} weekly breakdowns "
            f"for {data_points_count} weeks (cost_per_item={cost_per_item:.2f})"
        )

        return weekly_breakdowns, week_labels

    except Exception as e:
        logger.error(f"Failed to calculate weekly cost breakdowns: {e}", exc_info=True)
        return [], []


def _empty_breakdown() -> Dict[str, Dict[str, float]]:
    """Return empty cost breakdown structure."""
    return {
        "Feature": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Defect": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Technical Debt": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Risk": {"cost": 0.0, "count": 0, "percentage": 0.0},
    }


def get_budget_baseline_vs_actual(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 12,
    pert_forecast_weeks: Optional[float] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
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
    from datetime import datetime, timedelta, timezone
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
                "SELECT created_at FROM budget_settings WHERE profile_id = ? AND query_id = ?",
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
            except Exception:
                start_date = datetime.now(timezone.utc)

        # Calculate baseline dates
        allocated_end_date = start_date + timedelta(
            weeks=budget["time_allocated_weeks"]
        )
        current_date = datetime.now(timezone.utc)
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
        import math

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
                    f"Budget will last {runway_vs_baseline_weeks:.1f} weeks longer than allocated"
                )
            else:
                insights.append(
                    f"Budget will run out {abs(runway_vs_baseline_weeks):.1f} weeks before allocated end"
                )

        if abs(projected_surplus_eur) > budget["budget_total_eur"] * 0.1:
            surplus_pct = projected_surplus_eur / budget["budget_total_eur"] * 100.0
            if projected_surplus_eur > 0:
                insights.append(
                    f"Projected surplus of {budget['currency_symbol']}{abs(projected_surplus_eur):,.0f} ({abs(surplus_pct):.1f}%)"
                )
            else:
                insights.append(
                    f"Projected deficit of {budget['currency_symbol']}{abs(projected_surplus_eur):,.0f} ({abs(surplus_pct):.1f}%)"
                )

        if velocity_items > assumed_baseline_velocity:
            velocity_improvement = (
                (velocity_items - assumed_baseline_velocity)
                / assumed_baseline_velocity
                * 100.0
            )
            insights.append(
                f"Higher velocity ({velocity_items:.1f} vs {assumed_baseline_velocity:.1f}, +{velocity_improvement:.0f}%) driving cost efficiency"
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
                        f"Budget runway exceeds forecast by {(runway_weeks - pert_forecast_weeks):.1f} weeks"
                    )
                else:
                    insights.append(
                        f"Budget will run out {abs(runway_weeks - pert_forecast_weeks):.1f} weeks before forecast completion"
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


def _empty_baseline_comparison() -> Dict[str, Any]:
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
