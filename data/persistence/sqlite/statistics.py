"""Statistics and scope operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.database import get_db_connection

logger = logging.getLogger(__name__)


class StatisticsMixin:
    """Mixin for project statistics and scope operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_statistics(
        self,
        profile_id: str,
        query_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Query normalized weekly statistics."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM project_statistics WHERE profile_id = ? AND query_id = ?"
                params: List[Any] = [profile_id, query_id]

                if start_date:
                    query += " AND stat_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND stat_date <= ?"
                    params.append(end_date)

                query += " ORDER BY stat_date ASC"

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(
                f"Failed to get statistics for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_statistics_batch(
        self,
        profile_id: str,
        query_id: str,
        stats: List[Dict],
    ) -> None:
        """Batch save weekly statistics (replaces all existing data for query)."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Delete all existing statistics for this query first
                cursor.execute(
                    "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                    (profile_id, query_id),
                )
                deleted_count = cursor.rowcount
                logger.info(
                    f"Deleted {deleted_count} existing statistics for {profile_id}/{query_id}"
                )

                if not stats:
                    logger.info(
                        f"No new statistics to insert for {profile_id}/{query_id}"
                    )
                    conn.commit()
                    return

                for stat in stats:
                    stat_date = stat.get("stat_date") or stat.get("date")
                    if not stat_date:
                        logger.warning(f"Skipping statistic with no date: {stat}")
                        continue

                    cursor.execute(
                        """
                        INSERT INTO project_statistics (
                            profile_id, query_id, stat_date, week_label,
                            remaining_items, remaining_total_points, items_added, items_completed,
                            completed_items, completed_points, created_items, created_points,
                            velocity_items, velocity_points, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            profile_id,
                            query_id,
                            stat_date,
                            stat.get("week_label"),
                            stat.get("remaining_items"),
                            stat.get("remaining_total_points"),
                            stat.get("items_added", 0),
                            stat.get("items_completed", 0),
                            stat.get("completed_items", 0),
                            stat.get("completed_points", 0.0),
                            stat.get("created_items", 0),
                            stat.get("created_points", 0.0),
                            stat.get("velocity_items", 0.0),
                            stat.get("velocity_points", 0.0),
                            datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
                logger.info(
                    f"Saved {len(stats)} statistics for {profile_id}/{query_id}"
                )

        except Exception as e:
            logger.error(
                f"Failed to save statistics batch for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_scope(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """Get project scope data."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT scope_data, updated_at FROM project_scope WHERE profile_id = ? AND query_id = ?",
                    (profile_id, query_id),
                )
                result = cursor.fetchone()
                if result:
                    scope = json.loads(result["scope_data"])
                    scope["updated_at"] = result["updated_at"]
                    return scope
                return None
        except Exception as e:
            logger.error(
                f"Failed to get scope for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_scope(
        self,
        profile_id: str,
        query_id: str,
        scope_data: Dict,
    ) -> None:
        """Save project scope data."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO project_scope (profile_id, query_id, scope_data, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(profile_id, query_id) DO UPDATE SET
                        scope_data = excluded.scope_data,
                        updated_at = excluded.updated_at
                """,
                    (
                        profile_id,
                        query_id,
                        json.dumps(scope_data),
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.info(f"Saved scope for {profile_id}/{query_id}")
        except Exception as e:
            logger.error(
                f"Failed to save scope for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_project_data(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """LEGACY: Get project data - aggregates normalized statistics and scope."""
        stats = self.get_statistics(profile_id, query_id)
        scope = self.get_scope(profile_id, query_id)
        if not stats and not scope:
            return None
        return {"statistics": stats, "scope": scope}

    def save_project_data(self, profile_id: str, query_id: str, data: Dict) -> None:
        """LEGACY: Save project data - splits to statistics and scope."""
        if "statistics" in data:
            self.save_statistics_batch(profile_id, query_id, data["statistics"])
        if "scope" in data:
            self.save_scope(profile_id, query_id, data["scope"])
