import logging
from pathlib import Path
from typing import Any

from data.database import get_db_connection

logger = logging.getLogger(__name__)


def _get_current_budget(
    profile_id: str, query_id: str, db_path: Path | None = None
) -> dict[str, Any] | None:

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
                "baseline_velocity_items": result[5] or 3.5,
                "baseline_velocity_points": result[6] or 21.0,
            }
    except Exception as e:
        logger.error(f"Failed to get current budget: {e}")
        return None


def get_budget_at_week(
    profile_id: str, query_id: str, week_label: str, db_path: Path | None = None
) -> dict[str, Any] | None:

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
                logger.debug(
                    f"No budget configured for profile {profile_id}, query {query_id}"
                )
                return None

            budget = {
                "time_allocated_weeks": result[0] or 0,
                "team_cost_per_week_eur": result[1] or 0.0,
                "budget_total_eur": result[2] or 0.0,
                "currency_symbol": result[3] or "€",
                "cost_rate_type": result[4] or "weekly",
                "baseline_velocity_items": result[5] or 3.5,
                "baseline_velocity_points": result[6] or 21.0,
            }

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

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

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

    try:
        conn_context = (
            get_db_connection() if db_path is None else get_db_connection(db_path)
        )
        with conn_context as conn:
            cursor = conn.cursor()

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
