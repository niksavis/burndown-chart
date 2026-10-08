import logging
from datetime import datetime
from pathlib import Path

from data.persistence import PersistenceBackend

logger = logging.getLogger(__name__)


class JSONBackend(PersistenceBackend):
    def __init__(self, base_path: str = "profiles"):

        self.base_path = Path(base_path)
        logger.warning(
            "JSONBackend initialized - LEGACY MODE. "
            "Use SQLiteBackend for new features. "
            f"Path: {self.base_path}"
        )

    def get_profile(self, profile_id: str) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_profile - Legacy only, use SQLiteBackend"
        )

    def save_profile(self, profile: dict) -> None:
        raise NotImplementedError(
            "JSONBackend.save_profile - Legacy only, use SQLiteBackend"
        )

    def list_profiles(self) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.list_profiles - Legacy only, use SQLiteBackend"
        )

    def delete_profile(self, profile_id: str) -> None:
        raise NotImplementedError(
            "JSONBackend.delete_profile - Legacy only, use SQLiteBackend"
        )

    def get_query(self, profile_id: str, query_id: str) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_query - Legacy only, use SQLiteBackend"
        )

    def save_query(self, profile_id: str, query: dict) -> None:
        raise NotImplementedError(
            "JSONBackend.save_query - Legacy only, use SQLiteBackend"
        )

    def list_queries(self, profile_id: str) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.list_queries - Legacy only, use SQLiteBackend"
        )

    def delete_query(self, profile_id: str, query_id: str) -> None:
        raise NotImplementedError(
            "JSONBackend.delete_query - Legacy only, use SQLiteBackend"
        )

    def get_app_state(self, key: str) -> str | None:
        raise NotImplementedError(
            "JSONBackend.get_app_state - Legacy only, use SQLiteBackend"
        )

    def set_app_state(self, key: str, value: str | None) -> None:
        raise NotImplementedError(
            "JSONBackend.set_app_state - Legacy only, use SQLiteBackend"
        )

    def get_issues(
        self,
        profile_id: str,
        query_id: str,
        status: str | None = None,
        assignee: str | None = None,
        issue_type: str | None = None,
        project_key: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_issues - Not supported, "
            "use SQLiteBackend for filtered queries"
        )

    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: list[dict],
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_issues_batch - Not supported, use SQLiteBackend"
        )

    def delete_expired_issues(self, cutoff_time: datetime) -> int:
        raise NotImplementedError(
            "JSONBackend.delete_expired_issues - Not supported, use SQLiteBackend"
        )

    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> dict | None:
        raise NotImplementedError("JSONBackend.get_jira_cache - Phase 3 migration only")

    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: dict,
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_jira_cache - Legacy only, use SQLiteBackend"
        )

    def cleanup_expired_cache(self) -> int:
        return 0

    def get_changelog_entries(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str | None = None,
        field_name: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_changelog_entries - Not supported, use SQLiteBackend"
        )

    def save_changelog_batch(
        self,
        profile_id: str,
        query_id: str,
        entries: list[dict],
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_changelog_batch - Not supported, use SQLiteBackend"
        )

    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_jira_changelog - Phase 3 migration only"
        )

    def save_jira_changelog(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str,
        changelog: dict,
        expires_at: datetime,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_jira_changelog - Legacy only, use SQLiteBackend"
        )

    def get_statistics(
        self,
        profile_id: str,
        query_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_statistics - Not supported, use SQLiteBackend"
        )

    def save_statistics_batch(
        self,
        profile_id: str,
        query_id: str,
        stats: list[dict],
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_statistics_batch - Not supported, use SQLiteBackend"
        )

    def get_scope(self, profile_id: str, query_id: str) -> dict | None:
        raise NotImplementedError("JSONBackend.get_scope - Phase 3 migration only")

    def save_scope(
        self,
        profile_id: str,
        query_id: str,
        scope_data: dict,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_scope - Legacy only, use SQLiteBackend"
        )

    def get_project_data(self, profile_id: str, query_id: str) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_project_data - Phase 3 migration only"
        )

    def save_project_data(self, profile_id: str, query_id: str, data: dict) -> None:
        raise NotImplementedError(
            "JSONBackend.save_project_data - Legacy only, use SQLiteBackend"
        )

    def get_metric_values(
        self,
        profile_id: str,
        query_id: str,
        metric_name: str | None = None,
        metric_category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_metric_values - Not supported, use SQLiteBackend"
        )

    def delete_metrics(
        self,
        profile_id: str,
        query_id: str,
    ) -> int:
        raise NotImplementedError(
            "JSONBackend.delete_metrics - Not supported, use SQLiteBackend"
        )

    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: list[dict],
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_metrics_batch - Not supported, use SQLiteBackend"
        )

    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_metrics_snapshots - Phase 3 migration only"
        )

    def save_metrics_snapshot(
        self,
        profile_id: str,
        query_id: str,
        snapshot_date: str,
        metric_type: str,
        metrics: dict,
        forecast: dict | None = None,
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_metrics_snapshot - Legacy only, use SQLiteBackend"
        )

    def get_task_progress(self, task_name: str) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_task_progress - Not supported, use SQLiteBackend"
        )

    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_task_progress - Not supported, use SQLiteBackend"
        )

    def clear_task_progress(self, task_name: str) -> None:
        raise NotImplementedError(
            "JSONBackend.clear_task_progress - Not supported, use SQLiteBackend"
        )

    def get_task_state(self) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_task_state - Not supported, use SQLiteBackend"
        )

    def save_task_state(self, state: dict) -> None:
        raise NotImplementedError(
            "JSONBackend.save_task_state - Not supported, use SQLiteBackend"
        )

    def clear_task_state(self) -> None:
        raise NotImplementedError(
            "JSONBackend.clear_task_state - Not supported, use SQLiteBackend"
        )

    def get_budget_settings(self, profile_id: str, query_id: str) -> dict | None:
        raise NotImplementedError(
            "JSONBackend.get_budget_settings - Not supported, use SQLiteBackend"
        )

    def get_budget_revisions(self, profile_id: str, query_id: str) -> list[dict]:
        raise NotImplementedError(
            "JSONBackend.get_budget_revisions - Not supported, use SQLiteBackend"
        )

    def save_budget_settings(
        self, profile_id: str, query_id: str, budget_settings: dict
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_budget_settings - Not supported, use SQLiteBackend"
        )

    def save_budget_revision(
        self, profile_id: str, query_id: str, revision: dict
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_budget_revision - Not supported, use SQLiteBackend"
        )

    def save_budget_revisions(
        self, profile_id: str, query_id: str, revisions: list[dict]
    ) -> None:
        raise NotImplementedError(
            "JSONBackend.save_budget_revisions - Not supported, use SQLiteBackend"
        )

    def begin_transaction(self) -> None:
        pass

    def commit_transaction(self) -> None:
        pass

    def rollback_transaction(self) -> None:
        pass

    def close(self) -> None:

        pass
