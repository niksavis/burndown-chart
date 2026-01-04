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
- calculate_runway(): Calculate budget runway weeks

Created: January 4, 2026
"""

import logging
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


def get_budget_at_week(
    profile_id: str, week_label: str, db_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Get budget configuration at specific week by replaying revisions.

    Queries budget_settings and replays budget_revisions using cumulative delta logic.
    Caches result in metrics_data_points table to avoid repeated replay.

    Args:
        profile_id: Profile identifier
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
        >>> budget = get_budget_at_week("my_profile", "2025-W44")
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
                       budget_total_eur, currency_symbol, cost_rate_type
                FROM budget_settings
                WHERE profile_id = ?
            """,
                (profile_id,),
            )

            result = cursor.fetchone()
            if not result:
                logger.debug(f"No budget configured for profile {profile_id}")
                return None

            # Start with base settings
            budget = {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
                "cost_rate_type": result[4] or "weekly",
            }

            # Replay revisions up to specified week
            cursor.execute(
                """
                SELECT time_allocated_weeks_delta, team_cost_delta, budget_total_delta
                FROM budget_revisions
                WHERE profile_id = ?
                  AND week_label <= ?
                ORDER BY week_label ASC
            """,
                (profile_id, week_label),
            )

            for row in cursor.fetchall():
                budget["time_allocated_weeks"] += row[0] or 0
                budget["team_cost_per_week_eur"] += row[1] or 0.0
                budget["budget_total_eur"] += row[2] or 0.0

            # Note: Budget snapshots are profile-level, not cached in metrics_data_points
            # because metrics_data_points requires a query_id foreign key.
            # Budget calculation is fast enough without caching.

            logger.info(
                f"Calculated budget for {profile_id} at {week_label}: {budget['budget_total_eur']:.2f}"
            )
            return budget

    except Exception as e:
        logger.error(f"Failed to get budget at week {week_label}: {e}")
        return None


def calculate_budget_consumed(
    profile_id: str, query_id: str, week_label: str, db_path: Optional[Path] = None
) -> Tuple[float, float, float]:
    """
    Calculate budget consumption percentage using cached active budget.

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
        budget = get_budget_at_week(profile_id, week_label, db_path)
        if not budget:
            return 0.0, 0.0, 0.0

        # Get completed work from project_statistics
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()
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

        # Calculate cost from velocity
        velocity = _get_velocity(profile_id, query_id, week_label, db_path)
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

    Integrates with flow_type_classifier.get_flow_type() using exact same
    classification logic as calculate_flow_distribution(). Unknown types
    default to "Feature". 4-category aggregation only.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
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
    from data.database import get_db_connection
    from data.flow_type_classifier import get_flow_type

    try:
        budget = get_budget_at_week(profile_id, week_label, db_path)
        if not budget:
            return _empty_breakdown()

        # Get velocity and cost per item
        velocity = _get_velocity(profile_id, query_id, week_label, db_path)
        if velocity <= 0:
            return _empty_breakdown()

        cost_per_item = budget["team_cost_per_week_eur"] / velocity

        # Get completed issues with their types
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            # Get effort category field from profile
            cursor.execute(
                """
                SELECT field_mappings FROM profiles WHERE id = ?
            """,
                (profile_id,),
            )
            result = cursor.fetchone()
            if not result:
                return _empty_breakdown()

            field_mappings = json.loads(result[0])
            effort_category_field = field_mappings.get("effort_category_field", "")

            # Get completed issues
            cursor.execute(
                """
                SELECT issue_type, fields
                FROM jira_issues
                WHERE profile_id = ?
                  AND query_id = ?
                  AND status IN (
                      SELECT json_each.value
                      FROM profiles,
                           json_each(json_extract(field_mappings, '$.done_statuses'))
                      WHERE profiles.id = ?
                  )
            """,
                (profile_id, query_id, profile_id),
            )

            # Count by flow type
            flow_counts = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}

            for row in cursor.fetchall():
                issue_type = row[0]
                fields = json.loads(row[1]) if row[1] else {}

                # Create mock issue object for classifier
                class MockIssue:
                    def __init__(self, issue_type, fields):
                        self.fields = type(
                            "obj",
                            (object,),
                            {
                                "issuetype": type(
                                    "obj", (object,), {"name": issue_type}
                                )(),
                                effort_category_field: fields.get(
                                    effort_category_field
                                ),
                            },
                        )()

                mock_issue = MockIssue(issue_type, fields)
                flow_type = get_flow_type(mock_issue, effort_category_field)

                # Default unknown types to Feature
                if flow_type not in flow_counts:
                    flow_type = "Feature"

                flow_counts[flow_type] += 1

        # Calculate costs and percentages
        total_items = sum(flow_counts.values())
        breakdown = {}

        for flow_type, count in flow_counts.items():
            cost = count * cost_per_item
            percentage = (count / total_items * 100) if total_items > 0 else 0.0
            breakdown[flow_type] = {
                "cost": cost,
                "count": count,
                "percentage": percentage,
            }

        return breakdown

    except Exception as e:
        logger.error(f"Failed to calculate cost breakdown: {e}")
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
        budget = get_budget_at_week(profile_id, week_label, db_path)
        if not budget or budget["budget_total_eur"] <= 0:
            return 0.0, 0.0

        consumed, total, _ = calculate_budget_consumed(
            profile_id, query_id, week_label, db_path
        )
        remaining = total - consumed

        # Get last N weeks for burn rate calculation
        weights = [0.1, 0.2, 0.3, 0.4][:data_points_count]
        weeks = get_last_n_weeks(data_points_count)

        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

            weekly_costs = []
            for week_info in weeks:
                wk_label = week_info[0]
                velocity = _get_velocity(profile_id, query_id, wk_label, db_path)

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

        # Calculate weighted burn rate
        if not weekly_costs or all(c == 0 for c in weekly_costs):
            return 0.0, 0.0

        weighted_burn_rate = sum(w * c for w, c in zip(weights, weekly_costs)) / sum(
            weights
        )

        if weighted_burn_rate > 0:
            runway_weeks = remaining / weighted_burn_rate
        else:
            runway_weeks = float("inf")

        return runway_weeks, weighted_burn_rate

    except Exception as e:
        logger.error(f"Failed to calculate runway: {e}")
        return 0.0, 0.0


def _get_velocity(
    profile_id: str, query_id: str, week_label: str, db_path: Optional[Path] = None
) -> float:
    """
    Get velocity from metrics_data_points or calculate from statistics.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier
        week_label: ISO week label
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
                    LIMIT 4
                )
            """,
                (profile_id, query_id, week_label),
            )

            result = cursor.fetchone()
            return float(result[0]) if result and result[0] else 0.0

    except Exception as e:
        logger.error(f"Failed to get velocity: {e}")
        return 0.0


def _empty_breakdown() -> Dict[str, Dict[str, float]]:
    """Return empty cost breakdown structure."""
    return {
        "Feature": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Defect": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Technical Debt": {"cost": 0.0, "count": 0, "percentage": 0.0},
        "Risk": {"cost": 0.0, "count": 0, "percentage": 0.0},
    }
