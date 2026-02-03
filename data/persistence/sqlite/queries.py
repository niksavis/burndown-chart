"""Query operations mixin for SQLiteBackend."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from data.persistence import ProfileNotFoundError, QueryNotFoundError, ValidationError
from data.database import get_db_connection
from data.persistence.sqlite.helpers import retry_on_db_lock

logger = logging.getLogger(__name__)


class QueriesMixin:
    """Mixin for query CRUD operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_query(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """Load query configuration from queries table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM queries WHERE profile_id = ? AND id = ?",
                    (profile_id, query_id),
                )
                result = cursor.fetchone()
                return dict(result) if result else None

        except Exception as e:
            logger.error(
                f"Failed to get query '{query_id}' for profile '{profile_id}': {e}",
                extra={
                    "error_type": type(e).__name__,
                    "profile_id": profile_id,
                    "query_id": query_id,
                },
            )
            raise

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_query(self, profile_id: str, query: Dict) -> None:
        """Save query configuration (insert or update) to queries table."""
        required_fields = ["id", "name", "jql", "created_at", "last_used"]
        for field in required_fields:
            if field not in query:
                raise ValidationError(f"Query missing required field: {field}")

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check parent profile exists
                cursor.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,))
                if not cursor.fetchone():
                    raise ProfileNotFoundError(f"Profile '{profile_id}' not found")

                cursor.execute(
                    """
                    INSERT INTO queries (id, profile_id, name, jql, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(profile_id, id) DO UPDATE SET
                        name = excluded.name,
                        jql = excluded.jql,
                        last_used = excluded.last_used
                """,
                    (
                        query["id"],
                        profile_id,
                        query["name"],
                        query["jql"],
                        query["created_at"],
                        query["last_used"],
                    ),
                )

                conn.commit()
                logger.info(f"Saved query: {profile_id}/{query['id']}")

        except (ProfileNotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(
                f"Failed to save query '{query.get('id')}' for profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def list_queries(self, profile_id: str) -> List[Dict]:
        """List all queries for a profile, ordered by last_used descending."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM queries WHERE profile_id = ? ORDER BY last_used DESC",
                    (profile_id,),
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(
                f"Failed to list queries for profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__, "profile_id": profile_id},
            )
            raise

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def delete_query(self, profile_id: str, query_id: str) -> None:
        """Delete query and cascade to cache and data."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if query exists
                cursor.execute(
                    "SELECT id FROM queries WHERE profile_id = ? AND id = ?",
                    (profile_id, query_id),
                )
                if not cursor.fetchone():
                    raise QueryNotFoundError(
                        f"Query '{query_id}' not found in profile '{profile_id}'"
                    )

                # DELETE CASCADE handles related data automatically
                cursor.execute(
                    "DELETE FROM queries WHERE profile_id = ? AND id = ?",
                    (profile_id, query_id),
                )
                conn.commit()

                logger.info(f"Deleted query: {profile_id}/{query_id}")

        except QueryNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete query '{query_id}' from profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise
