"""
Persistence layer abstract interface for burndown chart application.

This module defines the contract for persistence backends, enabling
abstraction between business logic and storage implementation.

Architecture Pattern: Repository Pattern
- Encapsulates data access logic
- Provides domain-centric interface
- Enables testing with mock backends
- Supports multiple storage backends (SQLite, JSON, future remote DB)

Usage Example:
    # In production
    backend = SQLiteBackend(Path("profiles/burndown.db"))

    # In tests
    backend = MockBackend()

    # Business logic uses abstract interface
    profile = backend.get_profile("kafka")
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import sys
import importlib.util
from pathlib import Path


class PersistenceBackend(ABC):
    """
    Abstract base class for persistence backends.

    All persistence operations must be implemented by concrete backends.
    Methods raise ValueError for not-found errors, IOError for persistence failures.
    """

    # ========================================================================
    # Profile Operations
    # ========================================================================

    @abstractmethod
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """
        Load profile configuration.

        Args:
            profile_id: Profile identifier

        Returns:
            Profile dict with parsed JSON fields, or None if not found

        Example:
            >>> profile = backend.get_profile("kafka")
            >>> print(profile["name"])
            "Apache Kafka Analysis"
        """
        pass

    @abstractmethod
    def save_profile(self, profile: Dict) -> None:
        """
        Save profile configuration (insert or update).

        Args:
            profile: Profile dict with all required fields

        Raises:
            ValueError: If required fields missing
            IOError: If persistence fails

        Example:
            >>> profile = {
            ...     "id": "kafka",
            ...     "name": "Apache Kafka",
            ...     "jira_config": {...},
            ...     "field_mappings": {...}
            ... }
            >>> backend.save_profile(profile)
        """
        pass

    @abstractmethod
    def list_profiles(self) -> List[Dict]:
        """
        List all profiles, ordered by last_used descending.

        Returns:
            List of profile dicts (summary only, not full config)

        Example:
            >>> profiles = backend.list_profiles()
            >>> for p in profiles:
            ...     print(f"{p['name']} - {p['last_used']}")
        """
        pass

    @abstractmethod
    def delete_profile(self, profile_id: str) -> None:
        """
        Delete profile and cascade to all queries and data.

        Args:
            profile_id: Profile to delete

        Raises:
            ValueError: If profile doesn't exist
            IOError: If deletion fails

        Note:
            Must cascade delete to:
            - queries
            - jira_cache
            - jira_changelog_cache
            - project_data
            - metrics_snapshots
        """
        pass

    # ========================================================================
    # Query Operations
    # ========================================================================

    @abstractmethod
    def get_query(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """
        Load query configuration.

        Args:
            profile_id: Parent profile ID
            query_id: Query identifier

        Returns:
            Query dict or None if not found

        Example:
            >>> query = backend.get_query("kafka", "12w")
            >>> print(query["jql"])
            "project = KAFKA AND updated >= -12w"
        """
        pass

    @abstractmethod
    def save_query(self, profile_id: str, query: Dict) -> None:
        """
        Save query configuration (insert or update).

        Args:
            profile_id: Parent profile ID
            query: Query dict with all required fields

        Raises:
            ValueError: If profile doesn't exist or required fields missing
            IOError: If persistence fails
        """
        pass

    @abstractmethod
    def list_queries(self, profile_id: str) -> List[Dict]:
        """
        List all queries for a profile, ordered by last_used descending.

        Args:
            profile_id: Profile to list queries for

        Returns:
            List of query dicts

        Example:
            >>> queries = backend.list_queries("kafka")
            >>> for q in queries:
            ...     print(f"{q['name']}: {q['jql']}")
        """
        pass

    @abstractmethod
    def delete_query(self, profile_id: str, query_id: str) -> None:
        """
        Delete query and cascade to cache and data.

        Args:
            profile_id: Parent profile ID
            query_id: Query to delete

        Raises:
            ValueError: If query doesn't exist
            IOError: If deletion fails

        Note:
            Must cascade delete to:
            - jira_cache
            - jira_changelog_cache
            - project_data
            - metrics_snapshots
        """
        pass

    # ========================================================================
    # App State Operations
    # ========================================================================

    @abstractmethod
    def get_app_state(self, key: str) -> Optional[str]:
        """
        Get application state value.

        Args:
            key: State key (e.g., "active_profile_id")

        Returns:
            State value or None if not set

        Example:
            >>> active_profile = backend.get_app_state("active_profile_id")
        """
        pass

    @abstractmethod
    def set_app_state(self, key: str, value: str) -> None:
        """
        Set application state value.

        Args:
            key: State key
            value: State value

        Raises:
            IOError: If persistence fails

        Example:
            >>> backend.set_app_state("active_profile_id", "kafka")
        """
        pass

    # ========================================================================
    # JIRA Cache Operations (Normalized)
    # ========================================================================

    # NOTE: Methods below provide normalized access to JIRA data
    # Legacy JSON blob methods (get_jira_cache/save_jira_cache) kept for migration compatibility

    @abstractmethod
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
        """
        Query normalized JIRA issues with optional filters.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            status: Filter by status (e.g., "Done", "In Progress")
            assignee: Filter by assignee display name
            issue_type: Filter by issue type (e.g., "Bug", "Story")
            project_key: Filter by project key (e.g., "KAFKA")
            limit: Maximum number of results

        Returns:
            List of issue dicts with indexed fields + JSON columns

        Example:
            >>> done_issues = backend.get_issues("kafka", "12w", status="Done")
            >>> for issue in done_issues:
            ...     print(f"{issue['issue_key']}: {issue['summary']}")
        """
        pass

    @abstractmethod
    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: List[Dict],
        expires_at: datetime,
    ) -> None:
        """
        Batch insert/update (UPSERT) normalized JIRA issues.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            cache_key: Cache identifier for this fetch
            issues: List of JIRA issue dicts from API
            expires_at: Cache expiration timestamp

        Notes:
            - Uses ON CONFLICT DO UPDATE for efficient delta updates
            - Extracts indexed columns (status, assignee, etc.) from issue dict
            - Stores nested data (fix_versions, labels) as JSON

        Example:
            >>> issues = jira_api.fetch_issues(jql)
            >>> backend.save_issues_batch("kafka", "12w", "cache_abc", issues, expires_at)
        """
        pass

    @abstractmethod
    def delete_expired_issues(self, cutoff_time: datetime) -> int:
        """
        Delete issues where expires_at < cutoff_time.

        Args:
            cutoff_time: Delete issues expiring before this timestamp

        Returns:
            Number of issues deleted

        Example:
            >>> from datetime import datetime, timedelta
            >>> cutoff = datetime.now() - timedelta(hours=24)
            >>> deleted = backend.delete_expired_issues(cutoff)
            >>> print(f"Cleaned up {deleted} expired issues")
        """
        pass

    @abstractmethod
    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> Optional[Dict]:
        """
        LEGACY: Get cached JIRA response as JSON blob (pre-normalization).

        DEPRECATED: Use get_issues() for normalized access with filters.
        Kept for backward compatibility during migration period.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            cache_key: Cache key (hash of query parameters)

        Returns:
            Cached response dict or None if not found/expired

        Example:
            >>> cache = backend.get_jira_cache("kafka", "12w", "abc123")
            >>> if cache:
            ...     issues = cache["issues"]
        """
        pass

    @abstractmethod
    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: Dict,
        expires_at: datetime,
    ) -> None:
        """
        LEGACY: Save JIRA response to cache as JSON blob (pre-normalization).

        DEPRECATED: Use save_issues_batch() for normalized storage.
        Kept for backward compatibility during migration period.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            cache_key: Cache key
            response: JIRA API response dict
            expires_at: Expiration timestamp

        Raises:
            ValueError: If profile/query doesn't exist
            IOError: If persistence fails

        Example:
            >>> expires = datetime.now() + timedelta(hours=24)
            >>> backend.save_jira_cache("kafka", "12w", "abc123",
            ...                          {"issues": [...]}, expires)
        """
        pass

    @abstractmethod
    def cleanup_expired_cache(self) -> int:
        """
        Remove expired JIRA cache entries.

        Returns:
            Number of entries deleted

        Example:
            >>> deleted = backend.cleanup_expired_cache()
            >>> print(f"Cleaned up {deleted} expired cache entries")
        """
        pass

    # ========================================================================
    # JIRA Changelog Operations (Normalized)
    # ========================================================================

    @abstractmethod
    def get_changelog_entries(
        self,
        profile_id: str,
        query_id: str,
        issue_key: Optional[str] = None,
        field_name: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict]:
        """
        Query normalized changelog entries with filters.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            issue_key: Filter by specific issue (e.g., "KAFKA-1234")
            field_name: Filter by field changed (e.g., "status")
            start_date: ISO timestamp - changes after this date
            end_date: ISO timestamp - changes before this date

        Returns:
            List of changelog entry dicts

        Example:
            >>> # Get all status changes in last week
            >>> changes = backend.get_changelog_entries(
            ...     "kafka", "12w", field_name="status",
            ...     start_date="2025-12-22T00:00:00Z"
            ... )
        """
        pass

    @abstractmethod
    def save_changelog_batch(
        self,
        profile_id: str,
        query_id: str,
        entries: List[Dict],
        expires_at: datetime,
    ) -> None:
        """
        Batch insert/update normalized changelog entries.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            entries: List of changelog entry dicts (flattened from JIRA history)
            expires_at: Cache expiration timestamp

        Example:
            >>> changelog_entries = flatten_jira_changelog(api_response)
            >>> backend.save_changelog_batch("kafka", "12w", changelog_entries, expires)
        """
        pass

    @abstractmethod
    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> Optional[Dict]:
        """
        LEGACY: Get cached JIRA changelog for issue as JSON blob.

        DEPRECATED: Use get_changelog_entries() for normalized access.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            issue_key: JIRA issue key (e.g., "KAFKA-1234")

        Returns:
            Changelog dict or None if not found/expired
        """
        pass

    @abstractmethod
    def save_jira_changelog(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str,
        changelog: Dict,
        expires_at: datetime,
    ) -> None:
        """
        LEGACY: Save JIRA changelog to cache as JSON blob.

        DEPRECATED: Use save_changelog_batch() for normalized storage.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            issue_key: JIRA issue key
            changelog: Changelog entries dict
            expires_at: Expiration timestamp

        Raises:
            ValueError: If profile/query doesn't exist
            IOError: If persistence fails
        """
        pass

    # ========================================================================
    # Project Statistics Operations (Normalized)
    # ========================================================================

    @abstractmethod
    def get_statistics(
        self,
        profile_id: str,
        query_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """
        Query normalized weekly project statistics.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            start_date: ISO date - stats after this date (e.g., "2025-12-01")
            end_date: ISO date - stats before this date
            limit: Maximum number of weeks

        Returns:
            List of weekly stat dicts (completed_items, velocity, etc.)

        Example:
            >>> # Get last 12 weeks of stats
            >>> stats = backend.get_statistics("kafka", "12w", limit=12)
            >>> for week in stats:
            ...     print(f"{week['stat_date']}: {week['velocity_points']} pts/week")
        """
        pass

    @abstractmethod
    def save_statistics_batch(
        self,
        profile_id: str,
        query_id: str,
        stats: List[Dict],
    ) -> None:
        """
        Batch UPSERT weekly statistics.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            stats: List of weekly stat dicts

        Example:
            >>> weekly_stats = calculate_weekly_statistics(issues)
            >>> backend.save_statistics_batch("kafka", "12w", weekly_stats)
        """
        pass

    @abstractmethod
    def get_scope(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """
        Get project scope data (small aggregated JSON).

        Args:
            profile_id: Profile ID
            query_id: Query ID

        Returns:
            Scope dict with remaining_items, baseline, forecast

        Example:
            >>> scope = backend.get_scope("kafka", "12w")
            >>> print(f"Remaining: {scope['remaining_items']} items")
        """
        pass

    @abstractmethod
    def save_scope(
        self,
        profile_id: str,
        query_id: str,
        scope_data: Dict,
    ) -> None:
        """
        Save project scope data.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            scope_data: Scope dict (small JSON, ~1KB)

        Example:
            >>> scope = calculate_project_scope(issues)
            >>> backend.save_scope("kafka", "12w", scope)
        """
        pass

    @abstractmethod
    def get_project_data(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """
        LEGACY: Get project data (statistics, scope) as JSON blob.

        DEPRECATED: Use get_statistics() and get_scope() for normalized access.

        Args:
            profile_id: Profile ID
            query_id: Query ID

        Returns:
            Project data dict or None if not found

        Example:
            >>> data = backend.get_project_data("kafka", "12w")
            >>> print(data["statistics"]["completed"])
            45
        """
        pass

    @abstractmethod
    def save_project_data(self, profile_id: str, query_id: str, data: Dict) -> None:
        """
        Save project data for query.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            data: Project data dict

        Raises:
            ValueError: If profile/query doesn't exist
            IOError: If persistence fails
        """
        pass

    # ========================================================================
    # Metrics Operations (Normalized)
    # ========================================================================

    @abstractmethod
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
        """
        Query normalized metric data points.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            metric_name: Filter by metric (e.g., "deployment_frequency", "lead_time_days")
            metric_category: Filter by category ("dora" or "flow")
            start_date: ISO week - metrics after this date (e.g., "2025-W48")
            end_date: ISO week - metrics before this date
            limit: Maximum number of data points

        Returns:
            List of metric value dicts

        Example:
            >>> # Get deployment frequency trend for last 12 weeks
            >>> values = backend.get_metric_values(
            ...     "kafka", "12w",
            ...     metric_name="deployment_frequency",
            ...     limit=12
            ... )
            >>> for v in values:
            ...     print(f"{v['snapshot_date']}: {v['metric_value']} {v['metric_unit']}")
        """
        pass

    @abstractmethod
    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: List[Dict],
    ) -> None:
        """
        Batch UPSERT metric data points.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            metrics: List of metric value dicts

        Example:
            >>> # Save DORA metrics for week 2025-W48
            >>> metrics = [
            ...     {"snapshot_date": "2025-W48", "metric_category": "dora",
            ...      "metric_name": "deployment_frequency", "metric_value": 2.5,
            ...      "metric_unit": "per_day"},
            ...     {"snapshot_date": "2025-W48", "metric_category": "dora",
            ...      "metric_name": "lead_time_days", "metric_value": 4.2,
            ...      "metric_unit": "days"},
            ... ]
            >>> backend.save_metrics_batch("kafka", "12w", metrics)
        """
        pass

    @abstractmethod
    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> List[Dict]:
        """
        LEGACY: Get historical metrics snapshots as JSON blobs.

        DEPRECATED: Use get_metric_values() for normalized access with filtering.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            metric_type: "dora" or "flow"
            limit: Maximum snapshots to return (default 52 weeks)

        Returns:
            List of snapshot dicts, ordered by snapshot_date descending

        Example:
            >>> snapshots = backend.get_metrics_snapshots("kafka", "12w", "dora", limit=12)
            >>> for snap in snapshots:
            ...     print(f"{snap['snapshot_date']}: {snap['metrics']}")
        """
        pass

    @abstractmethod
    def save_metrics_snapshot(
        self,
        profile_id: str,
        query_id: str,
        snapshot_date: str,
        metric_type: str,
        metrics: Dict,
        forecast: Optional[Dict] = None,
    ) -> None:
        """
        Save metrics snapshot for a specific date.

        Args:
            profile_id: Profile ID
            query_id: Query ID
            snapshot_date: ISO week (e.g., "2025-W12")
            metric_type: "dora" or "flow"
            metrics: Metrics values dict
            forecast: Optional forecast data dict

        Raises:
            ValueError: If profile/query doesn't exist
            IOError: If persistence fails

        Example:
            >>> metrics = {"deployment_frequency": 2.5, "lead_time_days": 4.2}
            >>> backend.save_metrics_snapshot("kafka", "12w", "2025-W12", "dora", metrics)
        """
        pass

    # ========================================================================
    # Task Progress Operations
    # ========================================================================

    @abstractmethod
    def get_task_progress(self, task_name: str) -> Optional[Dict]:
        """
        Get task progress state.

        Args:
            task_name: Task identifier

        Returns:
            Task progress dict or None if not found

        Example:
            >>> progress = backend.get_task_progress("fetch_jira_issues")
            >>> print(f"{progress['progress_percent']}% - {progress['status']}")
        """
        pass

    @abstractmethod
    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:
        """
        Update task progress state.

        Args:
            task_name: Task identifier
            progress_percent: Progress percentage (0.0 to 100.0)
            status: "running", "completed", "failed"
            message: Optional status message

        Raises:
            ValueError: If progress_percent out of range
            IOError: If persistence fails

        Example:
            >>> backend.save_task_progress("fetch_jira_issues", 75.0, "running",
            ...                            "Fetched 750 of 1000 issues")
        """
        pass

    @abstractmethod
    def clear_task_progress(self, task_name: str) -> None:
        """
        Remove task progress entry.

        Args:
            task_name: Task identifier to clear

        Example:
            >>> backend.clear_task_progress("fetch_jira_issues")
        """
        pass

    # ========================================================================
    # Task State Operations
    # ========================================================================

    @abstractmethod
    def get_task_state(self) -> Optional[Dict]:
        """Get the current task state.

        Returns:
            Task state dictionary or None if no active task

        Example:
            >>> state = backend.get_task_state()
            >>> if state and state.get("status") == "in_progress":
            ...     print(f"Task {state['task_name']} is running")
        """
        pass

    @abstractmethod
    def save_task_state(self, state: Dict) -> None:
        """Save task state.

        Args:
            state: Task state dictionary to save

        Raises:
            IOError: If persistence fails

        Example:
            >>> state = {"task_id": "metrics", "status": "in_progress"}
            >>> backend.save_task_state(state)
        """
        pass

    @abstractmethod
    def clear_task_state(self) -> None:
        """Clear/delete the task state.

        Example:
            >>> backend.clear_task_state()
        """
        pass

    # ========================================================================
    # Transaction Management
    # ========================================================================

    @abstractmethod
    def begin_transaction(self) -> None:
        """
        Begin database transaction.

        Note:
            Some backends (JSON) may not support transactions.
            Implementation should be no-op if not applicable.
        """
        pass

    @abstractmethod
    def commit_transaction(self) -> None:
        """
        Commit database transaction.

        Raises:
            IOError: If commit fails
        """
        pass

    @abstractmethod
    def rollback_transaction(self) -> None:
        """
        Rollback database transaction.

        Raises:
            IOError: If rollback fails
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close any open connections or resources.

        Example:
            >>> backend.close()
        """
        pass


# =============================================================================
# Error Handling Contracts
# =============================================================================


class PersistenceError(Exception):
    """Base exception for persistence layer errors."""

    pass


class ProfileNotFoundError(PersistenceError):
    """Raised when profile doesn't exist."""

    pass


class QueryNotFoundError(PersistenceError):
    """Raised when query doesn't exist."""

    pass


class ValidationError(PersistenceError):
    """Raised when data validation fails."""

    pass


class DatabaseCorruptionError(PersistenceError):
    """Raised when database integrity check fails."""

    pass


# =============================================================================
# Re-export Legacy Functions for Backward Compatibility
# =============================================================================
# The old data/persistence.py file is now shadowed by this package.
# Re-export its functions to maintain backward compatibility with existing code.

# Add parent to path temporarily to import the old persistence module
_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    # Import from the file (not the package) using a workaround
    _persistence_file = Path(__file__).parent.parent / "persistence.py"
    _spec = importlib.util.spec_from_file_location(
        "_legacy_persistence", _persistence_file
    )
    if _spec is None or _spec.loader is None:
        raise ImportError("Failed to load legacy persistence module")
    _legacy_persistence = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_legacy_persistence)

    # Re-export all public functions
    generate_realistic_sample_data = _legacy_persistence.generate_realistic_sample_data
    load_app_settings = _legacy_persistence.load_app_settings
    load_project_data = _legacy_persistence.load_project_data
    load_settings = _legacy_persistence.load_settings
    load_statistics = _legacy_persistence.load_statistics
    read_and_clean_data = _legacy_persistence.read_and_clean_data
    save_app_settings = _legacy_persistence.save_app_settings
    save_project_data = _legacy_persistence.save_project_data
    save_settings = _legacy_persistence.save_settings
    save_statistics = _legacy_persistence.save_statistics
    save_statistics_from_csv_import = (
        _legacy_persistence.save_statistics_from_csv_import
    )
    load_jira_configuration = _legacy_persistence.load_jira_configuration
    save_jira_configuration = _legacy_persistence.save_jira_configuration
    validate_jira_config = _legacy_persistence.validate_jira_config
    save_jira_data_unified = _legacy_persistence.save_jira_data_unified
    load_unified_project_data = _legacy_persistence.load_unified_project_data
    save_unified_project_data = _legacy_persistence.save_unified_project_data
    get_project_statistics = _legacy_persistence.get_project_statistics
    get_project_scope = _legacy_persistence.get_project_scope
    update_project_scope = _legacy_persistence.update_project_scope
    calculate_project_scope_from_jira = (
        _legacy_persistence.calculate_project_scope_from_jira
    )

    # Clean up temporary module
    del _legacy_persistence, _spec, _persistence_file
finally:
    # Remove parent from path
    if _parent_dir in sys.path:
        sys.path.remove(_parent_dir)

del _parent_dir
