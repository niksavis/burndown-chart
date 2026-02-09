"""Unit tests for Active Work Timeline callbacks."""

from datetime import datetime, timezone

import dash_bootstrap_components as dbc
from dash import html

from callbacks.active_work_timeline import _render_active_work_timeline_content


class FakeBackend:
    """Minimal backend stub for callback tests."""

    def __init__(self, issues=None, app_state=None):
        self._issues = issues or []
        self._app_state = app_state or {}

    def get_app_state(self, key):
        return self._app_state.get(key)

    def get_issues(self, profile_id, query_id):
        return self._issues


def test_render_returns_no_issues_when_no_active_profile(monkeypatch):
    """Test empty state when active profile/query is missing."""
    backend = FakeBackend(
        app_state={"active_profile_id": None, "active_query_id": None}
    )

    monkeypatch.setattr("data.persistence.factory.get_backend", lambda: backend)
    sentinel = html.Div("empty")
    monkeypatch.setattr(
        "ui.active_work_timeline.create_no_issues_state",
        lambda **kwargs: sentinel,
    )

    result = _render_active_work_timeline_content()

    assert result is sentinel


def test_render_returns_no_issues_when_issue_list_empty(monkeypatch):
    """Test empty state when backend returns no issues."""
    backend = FakeBackend(
        issues=[],
        app_state={"active_profile_id": "profile", "active_query_id": "query"},
    )

    monkeypatch.setattr("data.persistence.factory.get_backend", lambda: backend)
    sentinel = html.Div("empty")
    monkeypatch.setattr(
        "ui.active_work_timeline.create_no_issues_state",
        lambda **kwargs: sentinel,
    )

    result = _render_active_work_timeline_content()

    assert result is sentinel


def test_render_builds_timeline_when_data_available(monkeypatch):
    """Test rendering timeline when issues and settings are valid."""
    now = datetime.now(timezone.utc)
    issues = [
        {
            "issue_key": "PROJ-1",
            "summary": "Task 1",
            "status": "In Progress",
            "created": now.isoformat(),
            "updated": now.isoformat(),
            "parent": {"key": "EPIC-1", "summary": "Epic 1"},
        }
    ]
    backend = FakeBackend(
        issues=issues,
        app_state={"active_profile_id": "profile", "active_query_id": "query"},
    )

    monkeypatch.setattr("data.persistence.factory.get_backend", lambda: backend)
    monkeypatch.setattr(
        "data.persistence.load_app_settings",
        lambda: {
            "field_mappings": {
                "general": {"parent_field": "parent"},
                "workflow": {
                    "flow_end_statuses": ["Done"],
                    "flow_wip_statuses": ["In Progress"],
                },
            },
            "development_projects": [],
            "devops_projects": [],
        },
    )
    monkeypatch.setattr(
        "data.project_filter.filter_development_issues", lambda items, *_: items
    )
    monkeypatch.setattr(
        "data.active_work_manager.get_active_work_data",
        lambda *args, **kwargs: {
            "timeline": [
                {
                    "epic_key": "EPIC-1",
                    "epic_summary": "Epic 1",
                    "total_issues": 1,
                    "child_issues": [],
                    "completion_pct": 0.0,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "data.active_work_completed.get_completed_items_by_week",
        lambda *args, **kwargs: {},  # Return empty dict for completed items
    )

    captured = {}

    def fake_create_nested_epic_timeline(
        timeline,
        show_points,
        parent_field_configured,
        summary_text,
        completed_section=None,
    ):
        captured["summary_text"] = summary_text
        captured["parent_field_configured"] = parent_field_configured
        captured["completed_section"] = completed_section
        return html.Div("timeline")

    monkeypatch.setattr(
        "ui.active_work_epic_timeline.create_nested_epic_timeline",
        fake_create_nested_epic_timeline,
    )

    result = _render_active_work_timeline_content(
        show_points=True, data_points_count=12
    )

    assert isinstance(result, html.Div)
    assert result.children
    container = result.children[0]  # type: ignore[index]
    assert isinstance(container, dbc.Container)
    assert captured["parent_field_configured"] is True
    assert "last 12 weeks" in captured["summary_text"]
