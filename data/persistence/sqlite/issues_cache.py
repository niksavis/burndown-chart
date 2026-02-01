"""JIRA cache operations mixin for SQLiteBackend."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from data.database import get_db_connection
from data.persistence.sqlite.helpers import retry_on_db_lock

logger = logging.getLogger(__name__)


class IssuesCacheMixin:
    """Mixin for JIRA cache operations (save, retrieve, cleanup)."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    # Method stubs for cross-mixin calls
    def get_issues(
        self,
        profile_id: str,
        query_id: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        issue_type: Optional[str] = None,
        project_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]: ...  # type: ignore[empty-body]
    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: List[Dict],
        expires_at: datetime,
    ) -> None: ...  # type: ignore[empty-body]
    def save_changelog_batch(
        self, profile_id: str, query_id: str, entries: List[Dict], expires_at: datetime
    ) -> None: ...  # type: ignore[empty-body]
    def delete_expired_issues(self, cutoff_time: datetime) -> int: ...  # type: ignore[empty-body]

    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> Optional[Dict]:
        """Get JIRA cache - returns aggregated normalized data with metadata."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT 
                        MIN(fetched_at) as timestamp,
                        COUNT(*) as issue_count
                    FROM jira_issues
                    WHERE profile_id = ? AND query_id = ? AND cache_key = ?
                    """,
                    (profile_id, query_id, cache_key),
                )
                row = cursor.fetchone()

                if not row or row[1] == 0:
                    return None

                timestamp, issue_count = row

                issues = self.get_issues(profile_id, query_id)

                return {
                    "issues": issues,
                    "metadata": {
                        "timestamp": timestamp,
                        "cache_key": cache_key,
                        "config_hash": "",
                    },
                }

        except Exception as e:
            logger.error(f"Failed to get JIRA cache: {e}")
            return None

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: Dict,
        expires_at: datetime,
    ) -> None:
        """Save JIRA cache - saves issues and changelog."""
        issues = response.get("issues", [])

        self.save_issues_batch(profile_id, query_id, cache_key, issues, expires_at)

        changelog_entries = self._extract_changelog_from_issues(issues)
        if changelog_entries:
            self.save_changelog_batch(
                profile_id, query_id, changelog_entries, expires_at
            )
            logger.info(
                f"Extracted and saved {len(changelog_entries)} changelog entries"
            )
        else:
            logger.debug(f"No changelog data found in {len(issues)} issues")

    def _extract_changelog_from_issues(self, issues: List[Dict]) -> List[Dict]:
        """Extract changelog entries from issues with expanded changelog."""
        changelog_entries = []

        for issue in issues:
            issue_key = issue.get("key")
            if not issue_key:
                continue

            changelog = issue.get("changelog", {})
            if not changelog:
                continue

            if isinstance(changelog, dict):
                histories = changelog.get("histories", [])
            else:
                histories = getattr(changelog, "histories", [])

            for history in histories:
                if isinstance(history, dict):
                    created = history.get("created")
                    author_obj = history.get("author", {})
                    author = (
                        author_obj.get("displayName", "")
                        if isinstance(author_obj, dict)
                        else ""
                    )
                    items = history.get("items", [])
                else:
                    created = getattr(history, "created", None)
                    author_obj = getattr(history, "author", None)
                    author = (
                        getattr(author_obj, "displayName", "") if author_obj else ""
                    )
                    items = getattr(history, "items", [])

                for item in items:
                    if isinstance(item, dict):
                        field_name = item.get("field")
                        field_type = item.get("fieldtype", "jira")
                        old_value = item.get("fromString")
                        new_value = item.get("toString")
                    else:
                        field_name = getattr(item, "field", None)
                        field_type = getattr(item, "fieldtype", "jira")
                        old_value = getattr(item, "fromString", None)
                        new_value = getattr(item, "toString", None)

                    if field_name:
                        changelog_entries.append(
                            {
                                "issue_key": issue_key,
                                "change_date": created,
                                "author": author or "",
                                "field_name": field_name,
                                "field_type": field_type,
                                "old_value": old_value,
                                "new_value": new_value,
                            }
                        )

        return changelog_entries

    def cleanup_expired_cache(self) -> int:
        """Remove expired JIRA cache entries (issues + changelog)."""
        try:
            cutoff = datetime.now()
            issues_deleted = self.delete_expired_issues(cutoff)

            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM jira_changelog_entries WHERE expires_at < ?",
                    (cutoff.isoformat(),),
                )
                changelog_deleted = cursor.rowcount
                conn.commit()

            total = issues_deleted + changelog_deleted
            logger.info(
                f"Cleaned up {total} expired cache entries ({issues_deleted} issues, {changelog_deleted} changelog)"
            )
            return total
        except Exception as e:
            logger.error(
                f"Failed to cleanup expired cache: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise
