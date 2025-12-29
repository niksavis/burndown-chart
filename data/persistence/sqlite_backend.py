"""
SQLite persistence backend implementation.

This module implements PersistenceBackend interface for SQLite storage.
Provides normalized database operations with connection-per-request pattern.

Architecture:
- Uses context managers from data.database module
- Implements full PersistenceBackend interface
- Provides both normalized operations (get_issues, get_statistics)
  and legacy JSON blob methods (get_jira_cache, get_project_data) for migration

Performance:
- Connection pooling via get_db_connection()
- WAL mode for concurrent reads during writes
- Batch operations with ON CONFLICT DO UPDATE
- Indexed queries for <50ms response times

Usage:
    from data.persistence.sqlite_backend import SQLiteBackend

    backend = SQLiteBackend("profiles/burndown.db")
    profile = backend.get_profile("kafka")
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from data.persistence import (
    PersistenceBackend,
    ProfileNotFoundError,
    QueryNotFoundError,
    ValidationError,
)
from data.database import get_db_connection

logger = logging.getLogger(__name__)


class SQLiteBackend(PersistenceBackend):
    """
    SQLite implementation of persistence backend.

    This is a STUB implementation - methods will be implemented incrementally
    during Phase 2 (Foundation) and Phase 3 (User Story 1 - Migration).

    Args:
        db_path: Path to SQLite database file (e.g., "profiles/burndown.db")

    Example:
        >>> backend = SQLiteBackend("profiles/burndown.db")
        >>> profile = backend.get_profile("kafka")
    """

    def __init__(self, db_path: str):
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to database file (created if doesn't exist)
        """
        self.db_path = Path(db_path)
        logger.info(f"SQLiteBackend initialized with database: {self.db_path}")

    # ========================================================================
    # Profile Operations
    # ========================================================================

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Load profile configuration from profiles table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,))
                result = cursor.fetchone()

                if not result:
                    return None

                # Convert Row to dict and parse JSON fields
                profile = dict(result)
                profile["jira_config"] = json.loads(profile["jira_config"])
                profile["field_mappings"] = json.loads(profile["field_mappings"])
                profile["forecast_settings"] = json.loads(profile["forecast_settings"])
                profile["project_classification"] = json.loads(
                    profile["project_classification"]
                )
                profile["flow_type_mappings"] = json.loads(
                    profile["flow_type_mappings"]
                )

                return profile

        except Exception as e:
            logger.error(
                f"Failed to get profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__, "profile_id": profile_id},
            )
            raise

    def save_profile(self, profile: Dict) -> None:
        """Save profile configuration (insert or update) to profiles table."""
        required_fields = ["id", "name", "created_at", "last_used"]
        for field in required_fields:
            if field not in profile:
                raise ValidationError(f"Profile missing required field: {field}")

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Serialize JSON fields
                jira_config = json.dumps(profile.get("jira_config", {}))
                field_mappings = json.dumps(profile.get("field_mappings", {}))
                forecast_settings = json.dumps(
                    profile.get(
                        "forecast_settings",
                        {"pert_factor": 1.2, "deadline": None, "data_points_count": 12},
                    )
                )
                project_classification = json.dumps(
                    profile.get("project_classification", {})
                )
                flow_type_mappings = json.dumps(profile.get("flow_type_mappings", {}))

                cursor.execute(
                    """
                    INSERT INTO profiles (
                        id, name, description, created_at, last_used,
                        jira_config, field_mappings, forecast_settings,
                        project_classification, flow_type_mappings,
                        show_milestone, show_points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        description = excluded.description,
                        last_used = excluded.last_used,
                        jira_config = excluded.jira_config,
                        field_mappings = excluded.field_mappings,
                        forecast_settings = excluded.forecast_settings,
                        project_classification = excluded.project_classification,
                        flow_type_mappings = excluded.flow_type_mappings,
                        show_milestone = excluded.show_milestone,
                        show_points = excluded.show_points
                """,
                    (
                        profile["id"],
                        profile["name"],
                        profile.get("description", ""),
                        profile["created_at"],
                        profile["last_used"],
                        jira_config,
                        field_mappings,
                        forecast_settings,
                        project_classification,
                        flow_type_mappings,
                        profile.get("show_milestone", 0),
                        profile.get("show_points", 0),
                    ),
                )

                conn.commit()
                logger.info(f"Saved profile: {profile['id']}")

        except Exception as e:
            logger.error(
                f"Failed to save profile '{profile.get('id')}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def list_profiles(self) -> List[Dict]:
        """List all profiles, ordered by last_used descending."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, name, description, created_at, last_used FROM profiles ORDER BY last_used DESC"
                )
                results = cursor.fetchall()
                return [dict(row) for row in results]

        except Exception as e:
            logger.error(
                f"Failed to list profiles: {e}", extra={"error_type": type(e).__name__}
            )
            raise

    def delete_profile(self, profile_id: str) -> None:
        """Delete profile and cascade to all queries and data."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if profile exists
                cursor.execute("SELECT id FROM profiles WHERE id = ?", (profile_id,))
                if not cursor.fetchone():
                    raise ProfileNotFoundError(f"Profile '{profile_id}' not found")

                # DELETE CASCADE handles related data automatically
                cursor.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
                conn.commit()

                logger.info(f"Deleted profile: {profile_id}")

        except ProfileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete profile '{profile_id}': {e}",
                extra={"error_type": type(e).__name__, "profile_id": profile_id},
            )
            raise

    # ========================================================================
    # Query Operations
    # ========================================================================

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

    # ========================================================================
    # App State Operations
    # ========================================================================

    def get_app_state(self, key: str) -> Optional[str]:
        """Get application state value from app_state table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM app_state WHERE key = ?", (key,))
                result = cursor.fetchone()
                return result["value"] if result else None
        except Exception as e:
            logger.error(
                f"Failed to get app_state key '{key}': {e}",
                extra={"error_type": type(e).__name__, "key": key},
            )
            raise

    def set_app_state(self, key: str, value: str) -> None:
        """Set application state value in app_state table."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                    (key, value),
                )
                conn.commit()
                logger.debug(f"Set app_state: {key} = {value}")
        except Exception as e:
            logger.error(
                f"Failed to set app_state key '{key}': {e}",
                extra={"error_type": type(e).__name__, "key": key},
            )
            raise

    # ========================================================================
    # JIRA Cache Operations - Normalized (STUB)
    # ========================================================================

    def get_issues(
        self,
        profile_id: str,
        query_id: str,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        issue_type: Optional[str] = None,
        project_key: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Query normalized JIRA issues with optional filters."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Build dynamic query with filters
                query = (
                    "SELECT * FROM jira_issues WHERE profile_id = ? AND query_id = ?"
                )
                params: List[Any] = [profile_id, query_id]

                if status:
                    query += " AND status = ?"
                    params.append(status)
                if assignee:
                    query += " AND assignee = ?"
                    params.append(assignee)
                if issue_type:
                    query += " AND issue_type = ?"
                    params.append(issue_type)
                if project_key:
                    query += " AND project_key = ?"
                    params.append(project_key)

                query += " ORDER BY updated DESC"

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                results = cursor.fetchall()

                # Parse JSON fields
                issues = []
                for row in results:
                    issue = dict(row)
                    issue["fix_versions"] = json.loads(
                        issue.get("fix_versions", "null") or "null"
                    )
                    issue["labels"] = json.loads(issue.get("labels", "null") or "null")
                    issue["components"] = json.loads(
                        issue.get("components", "null") or "null"
                    )
                    issue["custom_fields"] = json.loads(
                        issue.get("custom_fields", "null") or "null"
                    )
                    issues.append(issue)

                return issues

        except Exception as e:
            logger.error(
                f"Failed to get issues for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: List[Dict],
        expires_at: datetime,
    ) -> None:
        """Batch UPSERT normalized issues."""
        if not issues:
            return

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for issue in issues:
                    cursor.execute(
                        """
                        INSERT INTO jira_issues (
                            profile_id, query_id, cache_key, issue_key, summary,
                            status, assignee, issue_type, priority, resolution,
                            created, updated, resolved, points, project_key,
                            project_name, fix_versions, labels, components,
                            custom_fields, expires_at, fetched_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(profile_id, query_id, issue_key) DO UPDATE SET
                            summary = excluded.summary,
                            status = excluded.status,
                            assignee = excluded.assignee,
                            issue_type = excluded.issue_type,
                            priority = excluded.priority,
                            resolution = excluded.resolution,
                            updated = excluded.updated,
                            resolved = excluded.resolved,
                            points = excluded.points,
                            fix_versions = excluded.fix_versions,
                            labels = excluded.labels,
                            components = excluded.components,
                            custom_fields = excluded.custom_fields,
                            expires_at = excluded.expires_at,
                            fetched_at = excluded.fetched_at
                    """,
                        (
                            profile_id,
                            query_id,
                            cache_key,
                            issue.get("key"),
                            issue.get("fields", {}).get("summary", ""),
                            issue.get("fields", {}).get("status", {}).get("name", ""),
                            issue.get("fields", {})
                            .get("assignee", {})
                            .get("displayName")
                            if issue.get("fields", {}).get("assignee")
                            else None,
                            issue.get("fields", {})
                            .get("issuetype", {})
                            .get("name", ""),
                            issue.get("fields", {}).get("priority", {}).get("name"),
                            issue.get("fields", {}).get("resolution", {}).get("name"),
                            issue.get("fields", {}).get("created"),
                            issue.get("fields", {}).get("updated"),
                            issue.get("fields", {}).get("resolutiondate"),
                            issue.get("fields", {}).get(
                                "customfield_10016"
                            ),  # Story points
                            issue.get("fields", {}).get("project", {}).get("key", ""),
                            issue.get("fields", {}).get("project", {}).get("name", ""),
                            json.dumps(issue.get("fields", {}).get("fixVersions")),
                            json.dumps(issue.get("fields", {}).get("labels")),
                            json.dumps(issue.get("fields", {}).get("components")),
                            json.dumps(
                                {
                                    k: v
                                    for k, v in issue.get("fields", {}).items()
                                    if k.startswith("customfield_")
                                }
                            ),
                            expires_at.isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
                logger.info(f"Saved {len(issues)} issues for {profile_id}/{query_id}")

        except Exception as e:
            logger.error(
                f"Failed to save issues batch for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def delete_expired_issues(self, cutoff_time: datetime) -> int:
        """Delete issues where expires_at < cutoff_time."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM jira_issues WHERE expires_at < ?",
                    (cutoff_time.isoformat(),),
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(f"Deleted {deleted_count} expired issues")
                return deleted_count
        except Exception as e:
            logger.error(
                f"Failed to delete expired issues: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> Optional[Dict]:
        """LEGACY: Get JIRA cache - returns aggregated normalized data."""
        # For backward compatibility, reconstruct JSON blob from normalized tables
        issues = self.get_issues(profile_id, query_id)
        if not issues:
            return None
        return {"issues": issues, "total": len(issues)}

    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: Dict,
        expires_at: datetime,
    ) -> None:
        """LEGACY: Save JIRA cache - redirects to save_issues_batch."""
        issues = response.get("issues", [])
        self.save_issues_batch(profile_id, query_id, cache_key, issues, expires_at)

    def cleanup_expired_cache(self) -> int:
        """Remove expired JIRA cache entries (issues + changelog)."""
        try:
            cutoff = datetime.now()
            issues_deleted = self.delete_expired_issues(cutoff)

            # Also delete expired changelog entries
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

    # ========================================================================
    # Changelog Operations - Normalized (STUB)
    # ========================================================================

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
                        INSERT INTO jira_changelog_entries (
                            profile_id, query_id, issue_key, change_date, author,
                            field_name, field_type, old_value, new_value, expires_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(profile_id, query_id, issue_key, change_date, field_name) DO UPDATE SET
                            author = excluded.author,
                            old_value = excluded.old_value,
                            new_value = excluded.new_value,
                            expires_at = excluded.expires_at
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

    # ========================================================================
    # Project Statistics - Normalized (STUB)
    # ========================================================================

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

                query += " ORDER BY stat_date DESC"

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
        """Batch UPSERT weekly statistics."""
        if not stats:
            return

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for stat in stats:
                    cursor.execute(
                        """
                        INSERT INTO project_statistics (
                            profile_id, query_id, stat_date, week_label,
                            completed_items, completed_points, created_items, created_points,
                            velocity_items, velocity_points, recorded_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(profile_id, query_id, stat_date) DO UPDATE SET
                            week_label = excluded.week_label,
                            completed_items = excluded.completed_items,
                            completed_points = excluded.completed_points,
                            created_items = excluded.created_items,
                            created_points = excluded.created_points,
                            velocity_items = excluded.velocity_items,
                            velocity_points = excluded.velocity_points,
                            recorded_at = excluded.recorded_at
                    """,
                        (
                            profile_id,
                            query_id,
                            stat.get("stat_date"),
                            stat.get("week_label"),
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

    # ========================================================================
    # Metrics Operations - Normalized (STUB)
    # ========================================================================

    def get_metric_values(
        self,
        profile_id: str,
        query_id: str,
        metric_name: Optional[str] = None,
        metric_category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """Query normalized metric data points."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM metrics_data_points WHERE profile_id = ? AND query_id = ?"
                params: List[Any] = [profile_id, query_id]

                if metric_name:
                    query += " AND metric_name = ?"
                    params.append(metric_name)
                if metric_category:
                    query += " AND metric_category = ?"
                    params.append(metric_category)
                if start_date:
                    query += " AND snapshot_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND snapshot_date <= ?"
                    params.append(end_date)

                query += " ORDER BY snapshot_date DESC"

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                results = cursor.fetchall()

                # Parse JSON fields
                metrics = []
                for row in results:
                    metric = dict(row)
                    if metric.get("calculation_metadata"):
                        metric["calculation_metadata"] = json.loads(
                            metric["calculation_metadata"]
                        )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            logger.error(
                f"Failed to get metric values for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: List[Dict],
    ) -> None:
        """Batch UPSERT metric data points."""
        if not metrics:
            return

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for metric in metrics:
                    cursor.execute(
                        """
                        INSERT INTO metrics_data_points (
                            profile_id, query_id, snapshot_date, metric_category, metric_name,
                            metric_value, metric_unit, excluded_issue_count, calculation_metadata,
                            forecast_value, forecast_confidence_low, forecast_confidence_high, calculated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(profile_id, query_id, snapshot_date, metric_category, metric_name) DO UPDATE SET
                            metric_value = excluded.metric_value,
                            metric_unit = excluded.metric_unit,
                            excluded_issue_count = excluded.excluded_issue_count,
                            calculation_metadata = excluded.calculation_metadata,
                            forecast_value = excluded.forecast_value,
                            forecast_confidence_low = excluded.forecast_confidence_low,
                            forecast_confidence_high = excluded.forecast_confidence_high,
                            calculated_at = excluded.calculated_at
                    """,
                        (
                            profile_id,
                            query_id,
                            metric.get("snapshot_date"),
                            metric.get("metric_category"),
                            metric.get("metric_name"),
                            metric.get("metric_value"),
                            metric.get("metric_unit"),
                            metric.get("excluded_issue_count", 0),
                            json.dumps(metric.get("calculation_metadata"))
                            if metric.get("calculation_metadata")
                            else None,
                            metric.get("forecast_value"),
                            metric.get("forecast_confidence_low"),
                            metric.get("forecast_confidence_high"),
                            datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
                logger.info(f"Saved {len(metrics)} metrics for {profile_id}/{query_id}")

        except Exception as e:
            logger.error(
                f"Failed to save metrics batch for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> List[Dict]:
        """LEGACY: Get metrics snapshots - returns normalized metrics."""
        return self.get_metric_values(
            profile_id, query_id, metric_category=metric_type, limit=limit
        )

    def save_metrics_snapshot(
        self,
        profile_id: str,
        query_id: str,
        snapshot_date: str,
        metric_type: str,
        metrics: Dict,
        forecast: Optional[Dict] = None,
    ) -> None:
        """LEGACY: Save metrics snapshot - converts to normalized metrics."""
        metric_list = []
        for metric_name, metric_value in metrics.items():
            metric_list.append(
                {
                    "snapshot_date": snapshot_date,
                    "metric_category": metric_type,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metric_unit": "",
                }
            )
        self.save_metrics_batch(profile_id, query_id, metric_list)

    # ========================================================================
    # Task Progress Operations (STUB)
    # ========================================================================

    def get_task_progress(self, task_name: str) -> Optional[Dict]:
        """Get task progress state."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM task_progress WHERE task_name = ?", (task_name,)
                )
                result = cursor.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(
                f"Failed to get task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:
        """Update task progress."""
        if not 0.0 <= progress_percent <= 100.0:
            raise ValidationError(
                f"progress_percent must be 0-100, got {progress_percent}"
            )

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO task_progress (task_name, progress_percent, status, message, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(task_name) DO UPDATE SET
                        progress_percent = excluded.progress_percent,
                        status = excluded.status,
                        message = excluded.message,
                        updated_at = excluded.updated_at
                """,
                    (
                        task_name,
                        progress_percent,
                        status,
                        message,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.debug(
                    f"Task progress: {task_name} - {progress_percent}% {status}"
                )
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to save task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def clear_task_progress(self, task_name: str) -> None:
        """Remove task progress entry."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM task_progress WHERE task_name = ?", (task_name,)
                )
                conn.commit()
                logger.debug(f"Cleared task progress: {task_name}")
        except Exception as e:
            logger.error(
                f"Failed to clear task progress '{task_name}': {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    # ========================================================================
    # Transaction Management
    # ========================================================================

    def begin_transaction(self) -> None:
        """Begin database transaction (not implemented - use context managers)."""
        logger.warning(
            "begin_transaction not implemented - use get_db_connection() context manager"
        )

    def commit_transaction(self) -> None:
        """Commit database transaction (not implemented - use context managers)."""
        logger.warning(
            "commit_transaction not implemented - use get_db_connection() context manager"
        )

    def rollback_transaction(self) -> None:
        """Rollback database transaction (not implemented - use context managers)."""
        logger.warning(
            "rollback_transaction not implemented - use get_db_connection() context manager"
        )
