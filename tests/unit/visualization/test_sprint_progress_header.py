from datetime import UTC, datetime

import pytest

from visualization.sprint_charts._health import _calculate_issue_health_priority
from visualization.sprint_charts._progress_bars import (
    _build_sprint_progress_info,
    create_sprint_progress_bars,
)


def test_future_sprint_progress_hides_today_marker_and_clamps_progress():
    sprint_start = datetime(2026, 3, 30, tzinfo=UTC)
    sprint_end = datetime(2026, 4, 13, tzinfo=UTC)
    now = datetime(2026, 3, 23, tzinfo=UTC)

    component = _build_sprint_progress_info(
        sprint_start=sprint_start,
        sprint_end=sprint_end,
        sprint_duration_seconds=(sprint_end - sprint_start).total_seconds(),
        now=now,
        sprint_state="FUTURE",
        scope_changes=None,
        sprint_data={"issue_states": {}},
    )

    rendered = str(component)
    assert "Not started yet" in rendered
    assert "TODAY" not in rendered


def test_demo_sprint_progress_uses_the_business_evaluation_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BURNDOWN_DEMO_MODE", "1")
    monkeypatch.setenv("BURNDOWN_AS_OF", "2026-01-29T12:00:00+00:00")
    component = create_sprint_progress_bars(
        {
            "name": "Demo Sprint 4",
            "issue_states": {"DEMO-1": {"status": "In Progress"}},
        },
        [
            {
                "issue_key": "DEMO-1",
                "field": "status",
                "new_value": "In Progress",
                "change_date": "2026-01-28T12:00:00+00:00",
            }
        ],
        sprint_start_date="2026-01-19T00:00:00+00:00",
        sprint_end_date="2026-02-02T00:00:00+00:00",
        sprint_state="ACTIVE",
    )
    rendered = str(component)
    assert "Sprint Progress: 75%" in rendered
    assert "3.5 days remaining" in rendered


def test_demo_issue_health_uses_the_business_evaluation_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BURNDOWN_DEMO_MODE", "1")
    monkeypatch.setenv("BURNDOWN_AS_OF", "2026-01-29T12:00:00+00:00")
    priority = _calculate_issue_health_priority(
        "DEMO-1",
        {"status": "In Progress", "created": "2026-01-28T12:00:00+00:00"},
        [],
        ["Done"],
        ["In Progress"],
    )
    assert priority == (0, 3, 0.0)
