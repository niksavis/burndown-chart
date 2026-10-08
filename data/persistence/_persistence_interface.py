from abc import ABC, abstractmethod
from datetime import datetime


class PersistenceBackend(ABC):
    @abstractmethod
    def get_profile(self, profile_id: str) -> dict | None:

        pass

    @abstractmethod
    def save_profile(self, profile: dict) -> None:

        pass

    @abstractmethod
    def list_profiles(self) -> list[dict]:

        pass

    @abstractmethod
    def delete_profile(self, profile_id: str) -> None:

        pass

    @abstractmethod
    def get_query(self, profile_id: str, query_id: str) -> dict | None:

        pass

    @abstractmethod
    def save_query(self, profile_id: str, query: dict) -> None:

        pass

    @abstractmethod
    def list_queries(self, profile_id: str) -> list[dict]:

        pass

    @abstractmethod
    def delete_query(self, profile_id: str, query_id: str) -> None:

        pass

    @abstractmethod
    def get_app_state(self, key: str) -> str | None:

        pass

    @abstractmethod
    def set_app_state(self, key: str, value: str | None) -> None:

        pass

    @abstractmethod
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

        pass

    @abstractmethod
    def save_issues_batch(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        issues: list[dict],
        expires_at: datetime,
    ) -> None:

        pass

    @abstractmethod
    def delete_expired_issues(self, cutoff_time: datetime) -> int:

        pass

    @abstractmethod
    def get_jira_cache(
        self, profile_id: str, query_id: str, cache_key: str
    ) -> dict | None:

        pass

    @abstractmethod
    def save_jira_cache(
        self,
        profile_id: str,
        query_id: str,
        cache_key: str,
        response: dict,
        expires_at: datetime,
    ) -> None:

        pass

    @abstractmethod
    def cleanup_expired_cache(self) -> int:

        pass

    @abstractmethod
    def get_changelog_entries(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str | None = None,
        field_name: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict]:

        pass

    @abstractmethod
    def save_changelog_batch(
        self,
        profile_id: str,
        query_id: str,
        entries: list[dict],
        expires_at: datetime,
    ) -> None:

        pass

    @abstractmethod
    def get_jira_changelog(
        self, profile_id: str, query_id: str, issue_key: str
    ) -> dict | None:

        pass

    @abstractmethod
    def save_jira_changelog(
        self,
        profile_id: str,
        query_id: str,
        issue_key: str,
        changelog: dict,
        expires_at: datetime,
    ) -> None:

        pass

    @abstractmethod
    def get_statistics(
        self,
        profile_id: str,
        query_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:

        pass

    @abstractmethod
    def save_statistics_batch(
        self,
        profile_id: str,
        query_id: str,
        stats: list[dict],
    ) -> None:

        pass

    @abstractmethod
    def get_scope(self, profile_id: str, query_id: str) -> dict | None:

        pass

    @abstractmethod
    def save_scope(
        self,
        profile_id: str,
        query_id: str,
        scope_data: dict,
    ) -> None:

        pass

    @abstractmethod
    def get_project_data(self, profile_id: str, query_id: str) -> dict | None:

        pass

    @abstractmethod
    def save_project_data(self, profile_id: str, query_id: str, data: dict) -> None:

        pass

    @abstractmethod
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

        pass

    @abstractmethod
    def delete_metrics(
        self,
        profile_id: str,
        query_id: str,
    ) -> int:

        pass

    @abstractmethod
    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: list[dict],
    ) -> None:

        pass

    @abstractmethod
    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> list[dict]:

        pass

    @abstractmethod
    def save_metrics_snapshot(
        self,
        profile_id: str,
        query_id: str,
        snapshot_date: str,
        metric_type: str,
        metrics: dict,
        forecast: dict | None = None,
    ) -> None:

        pass

    @abstractmethod
    def get_task_progress(self, task_name: str) -> dict | None:

        pass

    @abstractmethod
    def save_task_progress(
        self, task_name: str, progress_percent: float, status: str, message: str = ""
    ) -> None:

        pass

    @abstractmethod
    def clear_task_progress(self, task_name: str) -> None:

        pass

    @abstractmethod
    def get_task_state(self) -> dict | None:

        pass

    @abstractmethod
    def save_task_state(self, state: dict) -> None:

        pass

    @abstractmethod
    def clear_task_state(self) -> None:

        pass

    @abstractmethod
    def begin_transaction(self) -> None:

        pass

    @abstractmethod
    def commit_transaction(self) -> None:

        pass

    @abstractmethod
    def rollback_transaction(self) -> None:

        pass

    @abstractmethod
    def close(self) -> None:

        pass

    @abstractmethod
    def get_budget_settings(self, profile_id: str, query_id: str) -> dict | None:

        pass

    @abstractmethod
    def get_budget_revisions(self, profile_id: str, query_id: str) -> list[dict]:

        pass

    @abstractmethod
    def save_budget_settings(
        self, profile_id: str, query_id: str, budget_settings: dict
    ) -> None:

        pass

    @abstractmethod
    def save_budget_revisions(
        self, profile_id: str, query_id: str, revisions: list[dict]
    ) -> None:

        pass
