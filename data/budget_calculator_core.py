"""
Budget Calculator - Core Configuration and Velocity Helpers

Private helpers for reading budget configuration and computing velocity.
Used internally by budget_calculator_consumption and budget_calculator_comparison.

Public:
- get_budget_at_week(): Replay budget revisions to get budget at specific week

Private helpers (also exposed via shim for backward compatibility):
- _get_current_budget(): Get current budget from budget_settings
- _get_velocity(): Get velocity (items per week)
- _get_velocity_points(): Get velocity (points per week)
"""

import logging
from pathlib import Path
from typing import Any

from data.database import get_db_connection

logger = logging.getLogger(__name__)


def _get_current_budget(
    profile_id: str, query_id: str, db_path: Path | None = None
) -> dict[str, Any] | None:
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
    profile_id: str, query_id: str, week_label: str, db_path: Path | None = None
) -> dict[str, Any] | None:
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
                f"Calculated budget for {profile_id}/{query_id} at "
                f"{week_label}: {budget['budget_total_eur']:.2f}"
            )
            return budget

    except Exception as e:
        logger.error(f"Failed to get budget at week {week_label}: {e}")
        return None


def _get_velocity(
    profile_id: str,
    query_id: str,
    week_label: str,
    data_points_count: int = 4,
    db_path: Path | None = None,
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
    db_path: Path | None = None,
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
