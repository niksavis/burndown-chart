"""Changelog operations mixin for SQLiteBackend."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.database import get_db_connection

logger = logging.getLogger(__name__)


class ChangelogMixin:
    """Mixin for JIRA changelog operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_changelog_entries(
        self,
        profile_id: str,
        query_id: str,
        issue_key: Optional[str] = None,
        field_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """Query normalized changelog entries with filters."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM jira_changelog_entries WHERE profile_id = ? AND query_id = ?"
                params: List[Any] = [profile_id, query_id]

                if issue_key:
                    query += " AND issue_key = ?"
                    params.append(issue_key)
                if field_name:
                    query += " AND field_name = ?"
                    params.append(field_name)
                if start_date:
                    query += " AND change_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND change_date <= ?"
                    params.append(end_date)

                query += " ORDER BY change_date DESC"

                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(
                f"Failed to get changelog entries for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_changelog_batch(
        self,
        profile_id: str,
        query_id: str,
        entries: List[Dict],
        expires_at: datetime,
    ) -> None:
        """Batch insert normalized changelog entries."""
        if not entries:
            return

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for entry in entries:
                    cursor.execute(
                        """
                        SELECT id FROM jira_changelog_entries
                        WHERE profile_id = ? AND query_id = ? AND issue_key = ?
                          AND change_date = ? AND field_name = ?
                        """,
                        (
                            profile_id,
                            query_id,
                            entry.get("issue_key"),
                            entry.get("change_date"),
                            entry.get("field_name"),
                        ),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        cursor.execute(
                            """
                            UPDATE jira_changelog_entries
                            SET author = ?, old_value = ?, new_value = ?, expires_at = ?
                            WHERE id = ?
                            """,
                            (
                                entry.get("author"),
                                entry.get("old_value"),
                                entry.get("new_value"),
                                expires_at.isoformat(),
                                existing["id"],
                            ),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO jira_changelog_entries (
                                profile_id, query_id, issue_key, change_date, author,
                                field_name, field_type, old_value, new_value, expires_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                profile_id,
                                query_id,
                                entry.get("issue_key"),
                                entry.get("change_date"),
                                entry.get("author"),
                                entry.get("field_name"),
                                entry.get("field_type", "jira"),
                                entry.get("old_value"),
                                entry.get("new_value"),
                                expires_at.isoformat(),
                            ),
                        )

                conn.commit()
                logger.info(
                    f"Saved {len(entries)} changelog entries for {profile_id}/{query_id}"
                )

        except Exception as e:
            logger.error(
                f"Failed to save changelog batch for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> Optional[Dict]:
        """LEGACY: Get changelog - returns aggregated normalized data."""
        entries = self.get_changelog_entries(profile_id, query_id, issue_key=issue_key)
        if not entries:
            return None
        return {"entries": entries, "total": len(entries)}

    def save_jira_changelog(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str,
        changelog: Dict,
        expires_at: datetime,
    ) -> None:
        """LEGACY: Save changelog - redirects to save_changelog_batch."""
        entries = changelog.get("entries", [])
        for entry in entries:
            entry["issue_key"] = issue_key
        self.save_changelog_batch(profile_id, query_id, entries, expires_at)
