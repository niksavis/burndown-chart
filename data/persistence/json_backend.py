"""
JSON file-based persistence backend (LEGACY).

This module provides backward compatibility with the existing JSON file structure:
profiles/{profile_id}/
├── profile.json
└── queries/{query_id}/
    ├── project_data.json
    └── jira_cache.json

WARNING: This backend is DEPRECATED and will be replaced by SQLiteBackend.
Kept only for:
1. Fallback during migration failures
2. Migration source data reading
3. Temporary dual-write during transition period

Performance Limitations:
- No indexed queries (full file scans)
- Large JSON files (>100k lines) for big projects
- No concurrent read/write safety
- No ACID guarantees

Do not use for new features - use SQLiteBackend instead.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from data.persistence import PersistenceBackend

logger = logging.getLogger(__name__)


class JSONBackend(PersistenceBackend):
    """
    LEGACY: JSON file-based persistence backend.

    This is a STUB for legacy compatibility only.
    Methods will NOT be implemented fully - minimal implementation
    for migration source reading only.

    Args:
        base_path: Base path for profiles directory (e.g., "profiles/")

    Example:
        >>> # LEGACY USAGE - DO NOT USE FOR NEW CODE
        >>> backend = JSONBackend("profiles/")
        >>> profile = backend.get_profile("kafka")  # Reads profiles/kafka/profile.json
    """

    def __init__(self, base_path: str = "profiles"):
        """
        Initialize JSON backend.

        Args:
            base_path: Base directory for profile storage
        """
        self.base_path = Path(base_path)
        logger.warning(
            f"JSONBackend initialized - LEGACY MODE. Use SQLiteBackend for new features. Path: {self.base_path}"
        )

    # ========================================================================
    # Profile Operations (STUB)
    # ========================================================================

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """STUB: Load profile from profile.json."""
        raise NotImplementedError(
            "JSONBackend.get_profile - Legacy only, use SQLiteBackend"
        )

    def save_profile(self, profile: Dict) -> None:
        """STUB: Save profile to profile.json."""
        raise NotImplementedError(
            "JSONBackend.save_profile - Legacy only, use SQLiteBackend"
        )

    def list_profiles(self) -> List[Dict]:
        """STUB: List profiles from filesystem."""
        raise NotImplementedError(
            "JSONBackend.list_profiles - Legacy only, use SQLiteBackend"
        )

    def delete_profile(self, profile_id: str) -> None:
        """STUB: Delete profile directory."""
        raise NotImplementedError(
            "JSONBackend.delete_profile - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # Query Operations (STUB)
    # ========================================================================

    def get_query(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """STUB: Load query from profile.json queries array."""
        raise NotImplementedError(
            "JSONBackend.get_query - Legacy only, use SQLiteBackend"
        )

    def save_query(self, profile_id: str, query: Dict) -> None:
        """STUB: Save query to profile.json queries array."""
        raise NotImplementedError(
            "JSONBackend.save_query - Legacy only, use SQLiteBackend"
        )

    def list_queries(self, profile_id: str) -> List[Dict]:
        """STUB: List queries from profile.json."""
        raise NotImplementedError(
            "JSONBackend.list_queries - Legacy only, use SQLiteBackend"
        )

    def delete_query(self, profile_id: str, query_id: str) -> None:
        """STUB: Delete query from profile.json and remove query directory."""
        raise NotImplementedError(
            "JSONBackend.delete_query - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # App State Operations (STUB)
    # ========================================================================

    def get_app_state(self, key: str) -> Optional[str]:
        """STUB: Get state from app_state.json."""
        raise NotImplementedError(
            "JSONBackend.get_app_state - Legacy only, use SQLiteBackend"
        )

    def set_app_state(self, key: str, value: str) -> None:
        """STUB: Save state to app_state.json."""
        raise NotImplementedError(
            "JSONBackend.set_app_state - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # JIRA Cache Operations (STUB)
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
        """NOT SUPPORTED: JSON backend cannot filter issues efficiently."""
        raise NotImplementedError(
            "JSONBackend.get_issues - Not supported, use SQLiteBackend for filtered queries"
        )

    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: List[Dict],
        expires_at: datetime,
    ) -> None:
        """NOT SUPPORTED: JSON backend uses jira_cache.json blob."""
        raise NotImplementedError(
            "JSONBackend.save_issues_batch - Not supported, use SQLiteBackend"
        )

    def delete_expired_issues(self, cutoff_time: datetime) -> int:
        """NOT SUPPORTED: JSON backend doesn't track expiration."""
        raise NotImplementedError(
            "JSONBackend.delete_expired_issues - Not supported, use SQLiteBackend"
        )

    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> Optional[Dict]:
        """STUB: Read jira_cache.json (migration source)."""
        raise NotImplementedError("JSONBackend.get_jira_cache - Phase 3 migration only")

    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: Dict,
        expires_at: datetime,
    ) -> None:
        """STUB: Write jira_cache.json."""
        raise NotImplementedError(
            "JSONBackend.save_jira_cache - Legacy only, use SQLiteBackend"
        )

    def cleanup_expired_cache(self) -> int:
        """NOT SUPPORTED: JSON backend doesn't track expiration."""
        return 0

    # ========================================================================
    # Changelog Operations (STUB)
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
        """NOT SUPPORTED: JSON backend cannot filter changelog efficiently."""
        raise NotImplementedError(
            "JSONBackend.get_changelog_entries - Not supported, use SQLiteBackend"
        )

    def save_changelog_batch(
        self,
        profile_id: str,
        query_id: str,
        entries: List[Dict],
        expires_at: datetime,
    ) -> None:
        """NOT SUPPORTED: JSON backend uses jira_cache.json blob."""
        raise NotImplementedError(
            "JSONBackend.save_changelog_batch - Not supported, use SQLiteBackend"
        )

    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> Optional[Dict]:
        """STUB: Read jira_cache.json changelog (migration source)."""
        raise NotImplementedError(
            "JSONBackend.get_jira_changelog - Phase 3 migration only"
        )

    def save_jira_changelog(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str,
        changelog: Dict,
        expires_at: datetime,
    ) -> None:
        """STUB: Write jira_cache.json changelog."""
        raise NotImplementedError(
            "JSONBackend.save_jira_changelog - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # Project Statistics (STUB)
    # ========================================================================

    def get_statistics(
        self,
        profile_id: str,
        query_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict]:
        """NOT SUPPORTED: JSON backend stores statistics as array in project_data.json."""
        raise NotImplementedError(
            "JSONBackend.get_statistics - Not supported, use SQLiteBackend"
        )

    def save_statistics_batch(
        self,
        profile_id: str,
        query_id: str,
        stats: List[Dict],
    ) -> None:
        """NOT SUPPORTED: JSON backend uses project_data.json blob."""
        raise NotImplementedError(
            "JSONBackend.save_statistics_batch - Not supported, use SQLiteBackend"
        )

    def get_scope(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """STUB: Read scope from project_data.json (migration source)."""
        raise NotImplementedError("JSONBackend.get_scope - Phase 3 migration only")

    def save_scope(
        self,
        profile_id: str,
        query_id: str,
        scope_data: Dict,
    ) -> None:
        """STUB: Write scope to project_data.json."""
        raise NotImplementedError(
            "JSONBackend.save_scope - Legacy only, use SQLiteBackend"
        )

    def get_project_data(self, profile_id: str, query_id: str) -> Optional[Dict]:
        """STUB: Read project_data.json (migration source)."""
        raise NotImplementedError(
            "JSONBackend.get_project_data - Phase 3 migration only"
        )

    def save_project_data(self, profile_id: str, query_id: str, data: Dict) -> None:
        """STUB: Write project_data.json."""
        raise NotImplementedError(
            "JSONBackend.save_project_data - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # Metrics Operations (STUB)
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
        """NOT SUPPORTED: JSON backend stores metrics as snapshots array."""
        raise NotImplementedError(
            "JSONBackend.get_metric_values - Not supported, use SQLiteBackend"
        )

    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: List[Dict],
    ) -> None:
        """NOT SUPPORTED: JSON backend uses metrics_snapshots file."""
        raise NotImplementedError(
            "JSONBackend.save_metrics_batch - Not supported, use SQLiteBackend"
        )

    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> List[Dict]:
        """STUB: Read metrics_snapshots.json (migration source)."""
        raise NotImplementedError(
            "JSONBackend.get_metrics_snapshots - Phase 3 migration only"
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
        """STUB: Write metrics_snapshots.json."""
        raise NotImplementedError(
            "JSONBackend.save_metrics_snapshot - Legacy only, use SQLiteBackend"
        )

    # ========================================================================
    # Task Progress (STUB)
    # ========================================================================

    def get_task_progress(self, task_name: str) -> Optional[Dict]:
        """NOT SUPPORTED: Task progress is runtime-only in SQLite."""
        raise NotImplementedError(
            "JSONBackend.get_task_progress - Not supported, use SQLiteBackend"
        )

    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:
        """NOT SUPPORTED: Task progress is runtime-only in SQLite."""
        raise NotImplementedError(
            "JSONBackend.save_task_progress - Not supported, use SQLiteBackend"
        )

    def clear_task_progress(self, task_name: str) -> None:
        """NOT SUPPORTED: Task progress is runtime-only in SQLite."""
        raise NotImplementedError(
            "JSONBackend.clear_task_progress - Not supported, use SQLiteBackend"
        )

    # ========================================================================
    # Transaction Management (NO-OP)
    # ========================================================================

    def begin_transaction(self) -> None:
        """NO-OP: JSON backend doesn't support transactions."""
        pass

    def commit_transaction(self) -> None:
        """NO-OP: JSON backend doesn't support transactions."""
        pass

    def rollback_transaction(self) -> None:
        """NO-OP: JSON backend doesn't support transactions."""
        pass

    def close(self) -> None:
        """Close any open resources.

        Note: JSON backend has no persistent connections, so this is a no-op.
        """
        pass
