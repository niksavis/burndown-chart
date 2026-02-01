"""JIRA issues and cache operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.database import get_db_connection
from data.persistence.sqlite.helpers import extract_nested_field, retry_on_db_lock

logger = logging.getLogger(__name__)


class IssuesMixin:
    """Mixin for JIRA issues, cache, and data operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    # Method stubs for cross-mixin calls (provided by ProfilesMixin and ChangelogMixin)
    def get_profile(self, profile_id: str) -> Optional[Dict]: ...  # type: ignore[empty-body]
    def save_changelog_batch(
        self, profile_id: str, query_id: str, entries: List[Dict], expires_at: datetime
    ) -> None: ...  # type: ignore[empty-body]

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

                # Parse JSON fields - return database format (flat structure)
                issues = []
                for row in results:
                    issue = dict(row)

                    # Parse JSON fields
                    fix_versions_data = json.loads(
                        issue.get("fix_versions", "null") or "null"
                    )

                    # Store as both fix_versions AND fixVersions for compatibility
                    # (code expects camelCase, database uses snake_case)
                    issue["fix_versions"] = fix_versions_data
                    issue["fixVersions"] = fix_versions_data

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

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: List[Dict],
        expires_at: datetime,
    ) -> None:
        """Batch UPSERT normalized issues with two-layer storage."""
        if not issues:
            return

        # Load profile configuration to get points field mapping
        profile_data = self.get_profile(profile_id)
        jira_config = {}
        points_field = ""
        field_mappings = {}

        if profile_data:
            jira_config = profile_data.get("jira_config", {})
            if isinstance(jira_config, dict):
                points_field = jira_config.get("points_field", "").strip()
                if not points_field:
                    logger.debug(
                        f"No points_field configured for profile {profile_id} - points will be NULL"
                    )
            else:
                logger.warning(f"Unexpected jira_config type: {type(jira_config)}")

            field_mappings = profile_data.get("field_mappings", {})
            if not isinstance(field_mappings, dict):
                field_mappings = {}
                logger.warning(
                    f"Unexpected field_mappings type: {type(field_mappings)}"
                )

        # Get general field mappings with fallbacks
        general_mappings = field_mappings.get("general", {})
        if not isinstance(general_mappings, dict):
            general_mappings = {}

        estimate_field = general_mappings.get("estimate", "")
        if isinstance(estimate_field, str) and estimate_field.strip():
            points_field = estimate_field.strip()

        completed_date_field = general_mappings.get("completed_date", "resolutiondate")
        created_date_field = general_mappings.get("created_date", "created")
        updated_date_field = general_mappings.get("updated_date", "updated")

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for issue in issues:
                    fields = issue.get("fields", {})

                    # RAW LAYER: Save ALL custom fields (immutable)
                    custom_fields_raw = {
                        k: v for k, v in fields.items() if k.startswith("customfield_")
                    }
                    custom_fields_json = json.dumps(custom_fields_raw)

                    # NORMALIZED LAYER: Extract points via configured mapping
                    points = None
                    if points_field:
                        points_raw = fields.get(points_field)

                        if points_raw is not None:
                            if isinstance(points_raw, dict):
                                points_raw = points_raw.get("value")

                            if points_raw is not None:
                                try:
                                    points = float(points_raw)
                                except (ValueError, TypeError):
                                    logger.warning(
                                        f"Cannot convert points to float for {issue.get('key')}: {points_raw}"
                                    )
                                    points = None
                            else:
                                points = None

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
                            fields.get("summary", ""),
                            fields.get("status", {}).get("name", ""),
                            fields.get("assignee", {}).get("displayName")
                            if fields.get("assignee")
                            else None,
                            fields.get("issuetype", {}).get("name", ""),
                            fields.get("priority", {}).get("name")
                            if fields.get("priority")
                            else None,
                            fields.get("resolution", {}).get("name")
                            if fields.get("resolution")
                            else None,
                            extract_nested_field(fields, created_date_field),
                            extract_nested_field(fields, updated_date_field),
                            extract_nested_field(fields, completed_date_field),
                            points,
                            fields.get("project", {}).get("key", ""),
                            fields.get("project", {}).get("name", ""),
                            json.dumps(fields.get("fixVersions")),
                            json.dumps(fields.get("labels")),
                            json.dumps(fields.get("components")),
                            custom_fields_json,
                            expires_at.isoformat(),
                            datetime.now(timezone.utc).isoformat(),
                        ),
                    )

                conn.commit()

                points_configured = (
                    f" (points_field: {points_field})"
                    if points_field
                    else " (no points mapping)"
                )
                logger.info(
                    f"Saved {len(issues)} issues for {profile_id}/{query_id}{points_configured}"
                )

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

    def renormalize_points(
        self, profile_id: str, query_id: Optional[str] = None
    ) -> int:
        """Re-normalize points column from raw custom_fields data."""
        profile = self.get_profile(profile_id)
        if not profile:
            raise ValueError(f"Profile not found: {profile_id}")

        jira_config = profile.get("jira_config") or {}
        if isinstance(jira_config, str):
            try:
                jira_config = json.loads(jira_config) if jira_config else {}
            except json.JSONDecodeError:
                logger.error(f"Invalid jira_config JSON for profile {profile_id}")
                return 0

        field_mappings = profile.get("field_mappings") or {}
        if isinstance(field_mappings, str):
            try:
                field_mappings = json.loads(field_mappings) if field_mappings else {}
            except json.JSONDecodeError:
                logger.error(f"Invalid field_mappings JSON for profile {profile_id}")
                return 0

        estimate_field = ""
        if isinstance(field_mappings, dict):
            estimate_field = field_mappings.get("general", {}).get("estimate", "")

        points_field = (
            estimate_field.strip() if isinstance(estimate_field, str) else ""
        ) or jira_config.get("points_field", "").strip()

        if not points_field:
            logger.warning(
                f"No points_field configured for profile {profile_id} - cannot re-normalize"
            )
            return 0

        logger.info(f"Re-normalizing points using field: {points_field}")

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                if query_id:
                    query = """
                        SELECT id, custom_fields FROM jira_issues 
                        WHERE profile_id = ? AND query_id = ?
                    """
                    params = [profile_id, query_id]
                else:
                    query = """
                        SELECT id, custom_fields FROM jira_issues 
                        WHERE profile_id = ?
                    """
                    params = [profile_id]

                cursor.execute(query, params)
                rows = cursor.fetchall()

                updated_count = 0
                for row in rows:
                    issue_id = row[0]
                    custom_fields_json = row[1]

                    if not custom_fields_json:
                        continue

                    try:
                        custom_fields = json.loads(custom_fields_json)
                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid custom_fields JSON for issue ID {issue_id}"
                        )
                        continue

                    points = None
                    points_raw = custom_fields.get(points_field)

                    if points_raw is not None:
                        if isinstance(points_raw, dict):
                            points_raw = points_raw.get("value")

                        if points_raw is not None:
                            try:
                                points = float(points_raw)
                            except (ValueError, TypeError):
                                logger.debug(
                                    f"Cannot convert points to float for issue ID {issue_id}: {points_raw}"
                                )
                                points = None
                        else:
                            points = None

                    cursor.execute(
                        "UPDATE jira_issues SET points = ? WHERE id = ?",
                        (points, issue_id),
                    )
                    updated_count += 1

                conn.commit()

                query_info = f" for query {query_id}" if query_id else ""
                logger.info(
                    f"Re-normalized {updated_count} issues for profile {profile_id}{query_info} using {points_field}"
                )
                return updated_count

        except Exception as e:
            logger.error(
                f"Failed to re-normalize points for {profile_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise
