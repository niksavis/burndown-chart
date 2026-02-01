"""Budget operations mixin for SQLiteBackend."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.database import get_db_connection
from data.persistence.sqlite.helpers import retry_on_db_lock

logger = logging.getLogger(__name__)


class BudgetMixin:
    """Mixin for budget settings and revisions operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_budget_settings(
        self, profile_id: str, query_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get budget settings for a query.

        Args:
            profile_id: Profile identifier
            query_id: Query identifier

        Returns:
            Dict with budget settings, or None if not configured
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT time_allocated_weeks, budget_total_eur, currency_symbol,
                           team_cost_per_week_eur, cost_rate_type, created_at, updated_at,
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
                    "time_allocated_weeks": result[0],
                    "budget_total_eur": result[1],
                    "currency_symbol": result[2],
                    "team_cost_per_week_eur": result[3],
                    "cost_rate_type": result[4],
                    "created_at": result[5],
                    "updated_at": result[6],
                    "baseline_velocity_items": result[7],
                    "baseline_velocity_points": result[8],
                }

        except Exception as e:
            logger.error(f"Failed to get budget settings for '{profile_id}': {e}")
            return None

    def get_budget_revisions(
        self, profile_id: str, query_id: str
    ) -> List[Dict[str, Any]]:
        """Get all budget revisions for a query.

        Args:
            profile_id: Profile identifier
            query_id: Query identifier

        Returns:
            List of budget revision dicts
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, revision_date, week_label, time_allocated_weeks_delta,
                           team_cost_delta, budget_total_delta, revision_reason,
                           created_at, metadata
                    FROM budget_revisions
                    WHERE profile_id = ? AND query_id = ?
                    ORDER BY revision_date ASC
                """,
                    (profile_id, query_id),
                )
                results = cursor.fetchall()

                revisions = []
                for row in results:
                    revisions.append(
                        {
                            "id": row[0],
                            "revision_date": row[1],
                            "week_label": row[2],
                            "time_allocated_weeks_delta": row[3],
                            "team_cost_delta": row[4],
                            "budget_total_delta": row[5],
                            "revision_reason": row[6],
                            "created_at": row[7],
                            "metadata": row[8],
                        }
                    )

                return revisions

        except Exception as e:
            logger.error(
                f"Failed to get budget revisions for profile '{profile_id}', query '{query_id}': {e}"
            )
            return []

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_budget_settings(
        self, profile_id: str, query_id: str, budget_settings: Dict[str, Any]
    ) -> None:
        """Save budget settings for a query.

        Args:
            profile_id: Profile identifier
            query_id: Query identifier
            budget_settings: Budget configuration dict
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO budget_settings (
                        profile_id, query_id, time_allocated_weeks, budget_total_eur,
                        currency_symbol, team_cost_per_week_eur, cost_rate_type,
                        baseline_velocity_items, baseline_velocity_points,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        profile_id,
                        query_id,
                        budget_settings["time_allocated_weeks"],
                        budget_settings.get("budget_total_eur"),
                        budget_settings.get("currency_symbol", "€"),
                        budget_settings.get("team_cost_per_week_eur"),
                        budget_settings.get("cost_rate_type", "weekly"),
                        budget_settings.get("baseline_velocity_items"),
                        budget_settings.get("baseline_velocity_points"),
                        budget_settings["created_at"],
                        budget_settings["updated_at"],
                    ),
                )
                conn.commit()
                logger.info(
                    f"Saved budget settings for profile '{profile_id}', query '{query_id}'"
                )

        except Exception as e:
            logger.error(
                f"Failed to save budget settings for profile '{profile_id}', query '{query_id}': {e}"
            )
            raise

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_budget_revisions(
        self, profile_id: str, query_id: str, revisions: List[Dict[str, Any]]
    ) -> None:
        """Save budget revisions for a query.

        Args:
            profile_id: Profile identifier
            query_id: Query identifier
            revisions: List of revision dicts
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for revision in revisions:
                    cursor.execute(
                        """
                        INSERT INTO budget_revisions (
                            profile_id, query_id, revision_date, week_label,
                            time_allocated_weeks_delta, team_cost_delta,
                            budget_total_delta, revision_reason,
                            created_at, metadata
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            profile_id,
                            query_id,
                            revision["revision_date"],
                            revision["week_label"],
                            revision.get("time_allocated_weeks_delta", 0),
                            revision.get("team_cost_delta", 0),
                            revision.get("budget_total_delta", 0),
                            revision.get("revision_reason"),
                            revision["created_at"],
                            revision.get("metadata"),
                        ),
                    )

                conn.commit()
                logger.info(
                    f"Saved {len(revisions)} budget revisions for profile '{profile_id}', query '{query_id}'"
                )

        except Exception as e:
            logger.error(
                f"Failed to save budget revisions for profile '{profile_id}', query '{query_id}': {e}"
            )
            raise
