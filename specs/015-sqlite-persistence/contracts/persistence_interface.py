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
    # JIRA Cache Operations
    # ========================================================================

    @abstractmethod
    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> Optional[Dict]:
        """
        Get cached JIRA response if not expired.

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
        Save JIRA response to cache.

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
    # JIRA Changelog Cache Operations
    # ========================================================================

    @abstractmethod
    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> Optional[Dict]:
        """
        Get cached JIRA changelog for issue if not expired.

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
        Save JIRA changelog to cache.

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
    # Project Data Operations
    # ========================================================================

    @abstractmethod
    def get_project_data(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """
        Get project data (statistics, scope) for query.

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
    # Metrics Snapshots Operations
    # ========================================================================

    @abstractmethod
    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> List[Dict]:
        """
        Get historical metrics snapshots.

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
