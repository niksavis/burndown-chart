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

Concurrency:
- Automatic retry logic for database lock scenarios (up to 3 retries with exponential backoff)
- Graceful handling of OperationalError: database is locked
- WAL mode enables concurrent reads

Usage:
    from data.persistence.sqlite_backend import SQLiteBackend

    backend = SQLiteBackend("profiles/burndown.db")
    profile = backend.get_profile("kafka")
"""

import logging
import json
import time
import sqlite3
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone

from data.persistence import (
    PersistenceBackend,
    ProfileNotFoundError,
    QueryNotFoundError,
    ValidationError,
)
from data.database import get_db_connection

logger = logging.getLogger(__name__)


def _extract_nested_field(fields_dict: Dict, field_path: str) -> Any:
    """Extract value from nested field path (e.g., 'resolved.resolutiondate').

    Args:
        fields_dict: JIRA fields dictionary
        field_path: Field path, may contain dots for nested access

    Returns:
        Field value or None if not found
    """
    if not field_path:
        return None

    # Handle nested field paths (e.g., "resolved.resolutiondate")
    if "." in field_path:
        parts = field_path.split(".")
        value = fields_dict
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    else:
        # Simple field (e.g., "created", "resolutiondate")
        return fields_dict.get(field_path)


# ========================================================================
# Retry Logic for Database Locks (T062, T064)
# ========================================================================


def retry_on_db_lock(max_retries: int = 3, base_delay: float = 0.1):
    """
    Decorator to retry database operations when database is locked.

    Implements exponential backoff: 0.1s, 0.2s, 0.4s for default settings.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 0.1)

    Example:
        @retry_on_db_lock(max_retries=3, base_delay=0.1)
        def save_profile(self, profile: Dict) -> None:
            # Database operation that might encounter locks
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Only retry on database lock errors
                    if "database is locked" in error_msg or "locked" in error_msg:
                        if attempt < max_retries:
                            delay = base_delay * (2**attempt)
                            logger.warning(
                                f"Database locked in {func.__name__}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(
                                f"Database locked in {func.__name__} after {max_retries} retries"
                            )
                            raise RuntimeError(
                                f"Database is locked after {max_retries} retry attempts. "
                                "This may indicate concurrent access or a hung transaction. "
                                "Try closing other instances of the app or wait a moment."
                            ) from e
                    else:
                        # Non-lock error - don't retry
                        raise
                except Exception:
                    # Non-OperationalError exceptions should not be retried
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


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

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
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

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
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

    @retry_on_db_lock(max_retries=3, base_delay=0.1)
    def set_app_state(self, key: str, value: str | None) -> None:
        """Set application state value in app_state table.

        Args:
            key: State key to set
            value: State value (if None, deletes the key)
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                if value is None:
                    # Delete key if value is None
                    cursor.execute("DELETE FROM app_state WHERE key = ?", (key,))
                    logger.debug(f"Deleted app_state key: {key}")
                else:
                    # Insert or update key-value pair
                    cursor.execute(
                        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                        (key, value),
                    )
                    logger.debug(f"Set app_state: {key} = {value}")
                conn.commit()
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
        """
        Batch UPSERT normalized issues with two-layer storage:
        1. RAW LAYER: All custom fields preserved in custom_fields JSON
        2. NORMALIZED LAYER: Points extracted via profile's configured mapping

        This enables:
        - User-configurable field mappings (no hardcoded field IDs)
        - Graceful degradation (points=NULL if mapping not configured)
        - Re-normalization without re-fetching from JIRA
        - Repository pattern (app reads normalized data, backend handles transformation)
        """
        if not issues:
            return

        # Load profile configuration to get points field mapping and general field mappings
        profile_data = self.get_profile(profile_id)
        jira_config = {}
        points_field = ""
        field_mappings = {}

        if profile_data:
            # get_profile already parses jira_config from JSON to dict
            jira_config = profile_data.get("jira_config", {})
            if isinstance(jira_config, dict):
                points_field = jira_config.get("points_field", "").strip()
                if not points_field:
                    logger.debug(
                        f"No points_field configured for profile {profile_id} - points will be NULL"
                    )
            else:
                logger.warning(f"Unexpected jira_config type: {type(jira_config)}")

            # Get general field mappings for standard JIRA fields
            field_mappings = profile_data.get("field_mappings", {})
            if not isinstance(field_mappings, dict):
                field_mappings = {}
                logger.warning(
                    f"Unexpected field_mappings type: {type(field_mappings)}"
                )

        # Get general field mappings with fallbacks to standard JIRA field names
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

                    # DEBUG: Log field structure for resolved issues
                    if fields.get("resolution"):
                        logger.info(
                            f"[DEBUG] Issue {issue.get('key')} has resolution: {fields.get('resolution')}"
                        )
                        logger.info(f"[DEBUG] Field keys: {list(fields.keys())[:20]}")
                        if "resolved" in fields:
                            logger.info(
                                f"[DEBUG] 'resolved' field type: {type(fields['resolved'])}, value: {fields['resolved']}"
                            )
                        else:
                            logger.info(
                                "[DEBUG] 'resolved' field NOT FOUND in fields dict"
                            )
                        if "resolutiondate" in fields:
                            logger.info(
                                f"[DEBUG] 'resolutiondate' field found: {fields['resolutiondate']}"
                            )

                    # === RAW LAYER: Save ALL custom fields (immutable) ===
                    custom_fields_raw = {
                        k: v for k, v in fields.items() if k.startswith("customfield_")
                    }
                    custom_fields_json = json.dumps(custom_fields_raw)

                    # === NORMALIZED LAYER: Extract points via configured mapping ===
                    points = None
                    if points_field:  # Only if mapping is configured
                        points_raw = fields.get(points_field)

                        if points_raw is not None:
                            # Handle JIRA's complex field types
                            if isinstance(points_raw, dict):
                                # Some fields return objects: {"value": 8.0}
                                points_raw = points_raw.get("value")

                            # Convert to float (check for None first)
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
                            _extract_nested_field(
                                fields, created_date_field
                            ),  # Supports nested: "created"
                            _extract_nested_field(
                                fields, updated_date_field
                            ),  # Supports nested: "updated"
                            _extract_nested_field(
                                fields, completed_date_field
                            ),  # Supports nested: "resolved.resolutiondate"
                            points,  # ← Normalized from configured points_field (can be NULL)
                            fields.get("project", {}).get("key", ""),
                            fields.get("project", {}).get("name", ""),
                            json.dumps(fields.get("fixVersions")),
                            json.dumps(fields.get("labels")),
                            json.dumps(fields.get("components")),
                            custom_fields_json,  # ← Raw data (all customfield_* preserved)
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
        """
        Get JIRA cache - returns aggregated normalized data with metadata.

        Note: Metadata (timestamp, config_hash) is derived from jira_issues table.
        The jira_cache table is no longer used as issues table has all needed info.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # Get cache metadata derived from jira_issues table
                # Use fetched_at as timestamp (when data was fetched)
                # Note: config_hash is not stored in jira_issues, but cache_key already
                # encodes configuration, so we use empty string (validated by cache_key match)
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

                if not row or row[1] == 0:  # No issues found
                    return None

                timestamp, issue_count = row

                # Get issues from normalized table
                issues = self.get_issues(profile_id, query_id)

                # Return in cache_manager expected format
                # Note: config_hash is empty since cache_key already encodes config
                return {
                    "issues": issues,
                    "metadata": {
                        "timestamp": timestamp,
                        "cache_key": cache_key,
                        "config_hash": "",  # Not needed - cache_key encodes config
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
        """
        Save JIRA cache - saves issues and changelog.

        This is the main entry point for saving JIRA data to the database.
        It handles both issues and changelog extraction from the JIRA API response.

        Note: Cache metadata (timestamp, config_hash) is no longer stored separately
        in jira_cache table. It can be derived from jira_issues table when needed.
        """
        issues = response.get("issues", [])

        # Save normalized issues (with two-layer storage: raw + normalized)
        self.save_issues_batch(profile_id, query_id, cache_key, issues, expires_at)

        # Extract and save changelog entries from issues
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
        """
        Extract changelog entries from issues with expanded changelog.

        JIRA API returns changelog in this structure:
        issue.changelog.histories[] -> each history has:
          - created: timestamp
          - author: {displayName: "..."}
          - items[]: list of field changes

        Args:
            issues: List of JIRA issues (may or may not have changelog expanded)

        Returns:
            List of normalized changelog entry dicts
        """
        changelog_entries = []

        for issue in issues:
            issue_key = issue.get("key")
            if not issue_key:
                continue

            changelog = issue.get("changelog", {})
            if not changelog:
                continue

            # Handle both dict and object formats (from jira_adapter)
            if isinstance(changelog, dict):
                histories = changelog.get("histories", [])
            else:
                histories = getattr(changelog, "histories", [])

            for history in histories:
                # Extract history metadata
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

                # Extract field changes
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

                    if field_name:  # Only save if we have a field name
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

    def renormalize_points(
        self, profile_id: str, query_id: Optional[str] = None
    ) -> int:
        """
        Re-normalize points column from raw custom_fields data.

        Use cases:
        - User changes points_field mapping in profile configuration
        - Migration completed but mapping was empty/incorrect
        - Fix data corruption in normalized columns

        This function reads the current points_field mapping from the profile
        and re-extracts points from the immutable custom_fields JSON for all
        issues in the profile (or specific query if specified).

        Args:
            profile_id: Profile to re-normalize
            query_id: Optional - re-normalize specific query, or all queries if None

        Returns:
            Number of issues updated

        Example:
            >>> backend = get_backend()
            >>> # User changed points_field from customfield_10016 to customfield_10002
            >>> updated = backend.renormalize_points("my_profile")
            >>> print(f"Re-normalized {updated} issues")
        """
        # Get current mapping from profile
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

                # Build query to get issues
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

                    # Extract points from configured field
                    points = None
                    points_raw = custom_fields.get(points_field)

                    if points_raw is not None:
                        # Handle JIRA's complex field types
                        if isinstance(points_raw, dict):
                            points_raw = points_raw.get("value")

                        # Convert to float (check for None first)
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

                    # Update normalized column
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
                    # Check if entry already exists to avoid duplicates
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
                        # Update existing entry
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
                        # Insert new entry
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

                query += " ORDER BY stat_date ASC"  # BUGFIX: Charts expect chronological order (oldest first)

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
        """
        Batch save weekly statistics (replaces all existing data for query).

        CRITICAL: This performs a full replacement - deletes all existing statistics
        for the query, then inserts the new data. This ensures row deletions persist.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                # CRITICAL FIX: Delete all existing statistics for this query first
                # This ensures row deletions persist (UPSERT only updates, never deletes)
                cursor.execute(
                    "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                    (profile_id, query_id),
                )
                deleted_count = cursor.rowcount
                logger.info(
                    f"Deleted {deleted_count} existing statistics for {profile_id}/{query_id}"
                )

                # DEBUG: Log sample of data being saved to detect manual edits
                if stats and len(stats) > 0:
                    first_stat = stats[0]
                    last_stat = stats[-1] if len(stats) > 1 else first_stat
                    logger.info(
                        f"[SAVE DEBUG] Saving {len(stats)} stats. "
                        f"First: {first_stat.get('date') or first_stat.get('stat_date')} "
                        f"remaining_items={first_stat.get('remaining_items')}, "
                        f"completed_items={first_stat.get('completed_items')}. "
                        f"Last: {last_stat.get('date') or last_stat.get('stat_date')} "
                        f"remaining_items={last_stat.get('remaining_items')}, "
                        f"completed_items={last_stat.get('completed_items')}"
                    )

                # Now insert the new statistics
                if not stats:
                    logger.info(
                        f"No new statistics to insert for {profile_id}/{query_id}"
                    )
                    conn.commit()
                    return

                for stat in stats:
                    # Handle both "stat_date" (database format) and "date" (legacy format)
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
                    # Parse metric_value if it's a JSON string
                    metric_value = metric.get("metric_value")
                    if isinstance(metric_value, str) and (
                        metric_value.startswith("{") or metric_value.startswith("[")
                    ):
                        try:
                            metric["metric_value"] = json.loads(metric_value)
                        except (json.JSONDecodeError, TypeError):
                            # Keep as string if not valid JSON
                            pass
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

    def delete_metrics(
        self,
        profile_id: str,
        query_id: str,
    ) -> int:
        """Delete all metrics for a specific profile/query combination.

        Args:
            profile_id: Profile identifier
            query_id: Query identifier

        Returns:
            Number of metrics deleted
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM metrics_data_points WHERE profile_id = ? AND query_id = ?",
                    (profile_id, query_id),
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(
                    f"Deleted {deleted_count} metrics for {profile_id}/{query_id}"
                )
                return deleted_count

        except Exception as e:
            logger.error(
                f"Failed to delete metrics for {profile_id}/{query_id}: {e}",
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
                    # Convert dict/list values to JSON for SQLite compatibility
                    metric_value = metric.get("metric_value")
                    if isinstance(metric_value, (dict, list)):
                        metric_value = json.dumps(metric_value)

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
                            metric_value,
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
            # Convert dict/list values to JSON since SQLite doesn't support them
            if isinstance(metric_value, (dict, list)):
                metric_value = json.dumps(metric_value)

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

    def get_task_state(self) -> Optional[Dict]:
        """
        Get full task state (supports complex nested structures).
        Retrieves the first (and only) task progress row and returns full state.
        """
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT message FROM task_progress LIMIT 1")
                result = cursor.fetchone()
                if not result or not result["message"]:
                    return None
                # Parse JSON from message field
                return json.loads(result["message"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse task state JSON: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Failed to get task state: {e}",
                extra={"error_type": type(e).__name__},
            )
            return None

    def save_task_state(self, state: Dict) -> None:
        """
        Save full task state (supports complex nested structures).
        Stores state as JSON in message field.
        """
        try:
            # Serialize state to JSON
            state_json = json.dumps(state)

            # Extract key fields for indexing
            task_name = state.get("task_id", "unknown")
            status = state.get("status", "in_progress")

            # Calculate progress percent (try multiple fields for compatibility)
            progress_percent = 0.0
            if "percent" in state:
                progress_percent = state["percent"]
            elif "fetch_progress" in state:
                progress_percent = state["fetch_progress"].get("percent", 0.0)
            elif "report_progress" in state:
                progress_percent = state["report_progress"].get("percent", 0.0)

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
                        state_json,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                logger.debug(
                    f"Task state saved: {task_name} - {progress_percent}% {status}"
                )
        except Exception as e:
            logger.error(
                f"Failed to save task state: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def clear_task_state(self) -> None:
        """Clear all task progress state."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM task_progress")
                conn.commit()
                logger.debug("Cleared all task progress state")
        except Exception as e:
            logger.error(
                f"Failed to clear task state: {e}",
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

    def close(self) -> None:
        """Close database connections.

        Note: SQLiteBackend uses connection-per-request pattern via context managers,
        so there are no persistent connections to close. This is a no-op.
        """
        logger.debug("close() called on SQLiteBackend (no-op with context managers)")

    # ========================================================================
    # Budget Operations
    # ========================================================================

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
