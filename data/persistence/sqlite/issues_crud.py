"""JIRA issues CRUD operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from data.database import get_db_connection
from data.persistence.sqlite.helpers import extract_nested_field, retry_on_db_lock

logger = logging.getLogger(__name__)


class IssuesCRUDMixin:
    """Mixin for JIRA issues CRUD operations (Create, Read, Update, Delete)."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    # Method stub for cross-mixin call (provided by ProfilesMixin)
    def get_profile(self, profile_id: str) -> Optional[Dict]: ...  # type: ignore[empty-body]

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
                    fields_raw = issue.get("fields", {})
                    fields = fields_raw if isinstance(fields_raw, dict) else {}
                    is_flat_issue = not fields

                    # RAW LAYER: Save ALL custom fields (immutable)
                    if is_flat_issue:
                        if isinstance(issue.get("custom_fields"), dict):
                            custom_fields_raw = issue.get("custom_fields", {})
                        else:
                            custom_fields_raw = {
                                k: v
                                for k, v in issue.items()
                                if isinstance(k, str) and k.startswith("customfield_")
                            }
                    else:
                        custom_fields_raw = {
                            k: v
                            for k, v in fields.items()
                            if k.startswith("customfield_")
                        }
                    custom_fields_json = json.dumps(custom_fields_raw)

                    issue_key = issue.get("key") or issue.get("issue_key")
                    status_value = fields.get("status") if not is_flat_issue else None
                    issue_type_value = (
                        fields.get("issuetype") if not is_flat_issue else None
                    )
                    priority_value = (
                        fields.get("priority") if not is_flat_issue else None
                    )
                    resolution_value = (
                        fields.get("resolution") if not is_flat_issue else None
                    )
                    assignee_value = (
                        fields.get("assignee") if not is_flat_issue else None
                    )
                    project_value = fields.get("project") if not is_flat_issue else None

                    summary = (
                        fields.get("summary", "")
                        if not is_flat_issue
                        else issue.get("summary", "")
                    )
                    status_name = (
                        status_value.get("name", "")
                        if isinstance(status_value, dict)
                        else issue.get("status", "")
                    )
                    assignee_name = (
                        assignee_value.get("displayName")
                        if isinstance(assignee_value, dict)
                        else issue.get("assignee")
                    )
                    issue_type_name = (
                        issue_type_value.get("name", "")
                        if isinstance(issue_type_value, dict)
                        else issue.get("issue_type", "")
                    )
                    priority_name = (
                        priority_value.get("name")
                        if isinstance(priority_value, dict)
                        else issue.get("priority")
                    )
                    resolution_name = (
                        resolution_value.get("name")
                        if isinstance(resolution_value, dict)
                        else issue.get("resolution")
                    )
                    created_value = (
                        extract_nested_field(fields, created_date_field)
                        if not is_flat_issue
                        else issue.get("created")
                    )
                    updated_value = (
                        extract_nested_field(fields, updated_date_field)
                        if not is_flat_issue
                        else issue.get("updated")
                    )
                    resolved_value = (
                        extract_nested_field(fields, completed_date_field)
                        if not is_flat_issue
                        else issue.get("resolved")
                    )
                    project_key = (
                        project_value.get("key", "")
                        if isinstance(project_value, dict)
                        else issue.get("project_key", "")
                    )
                    project_name = (
                        project_value.get("name", "")
                        if isinstance(project_value, dict)
                        else issue.get("project_name", "")
                    )

                    fix_versions_value = (
                        fields.get("fixVersions")
                        if not is_flat_issue
                        else issue.get("fix_versions", issue.get("fixVersions"))
                    )
                    labels_value = (
                        fields.get("labels")
                        if not is_flat_issue
                        else issue.get("labels")
                    )
                    components_value = (
                        fields.get("components")
                        if not is_flat_issue
                        else issue.get("components")
                    )

                    # NORMALIZED LAYER: Extract points via configured mapping
                    points = None
                    if points_field and not is_flat_issue:
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
                    elif is_flat_issue:
                        points_raw = issue.get("points")
                        if points_raw is not None:
                            try:
                                points = float(points_raw)
                            except (ValueError, TypeError):
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
                            issue_key,
                            summary,
                            status_name,
                            assignee_name,
                            issue_type_name,
                            priority_name,
                            resolution_name,
                            created_value,
                            updated_value,
                            resolved_value,
                            points,
                            project_key,
                            project_name,
                            json.dumps(fix_versions_value),
                            json.dumps(labels_value),
                            json.dumps(components_value),
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
