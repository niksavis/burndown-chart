"""Unit tests for changelog fetcher targeted refresh."""

from typing import Any


def test_fetch_changelog_on_demand_targets_issue_keys(monkeypatch):
    from data.jira import changelog_fetcher

    captured_issue_keys: list[str] = []

    class BackendStub:
        def get_app_state(self, key: str) -> str | None:
            if key == "active_profile_id":
                return "profile-1"
            if key == "active_query_id":
                return "query-1"
            return None

        def get_changelog_entries(self, profile_id: str, query_id: str):
            return [
                {"issue_key": "A-1"},
                {"issue_key": "B-2"},
            ]

        def get_issues(self, profile_id: str, query_id: str):
            return []

        def save_changelog_batch(
            self,
            profile_id: str,
            query_id: str,
            entries: list[dict[str, Any]],
            expires_at,
        ) -> None:
            return None

    def fake_get_backend():
        return BackendStub()

    def fake_fetch(config, issue_keys=None, progress_callback=None):
        nonlocal captured_issue_keys
        captured_issue_keys = issue_keys or []
        return True, []

    monkeypatch.setattr(
        changelog_fetcher,
        "fetch_jira_issues_with_changelog",
        fake_fetch,
    )
    monkeypatch.setattr(
        "data.persistence.factory.get_backend",
        fake_get_backend,
    )

    success, _message = changelog_fetcher.fetch_changelog_on_demand(
        config={},
        profile_id="profile-1",
        query_id="query-1",
        issue_keys=["B-2", "A-1", "A-1"],
    )

    assert success is True
    assert captured_issue_keys == ["A-1", "B-2"]
