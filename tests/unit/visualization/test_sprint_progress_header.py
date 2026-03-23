"""Tests for sprint progress header rendering."""

from datetime import UTC, datetime

from visualization.sprint_charts._progress_bars import _build_sprint_progress_info


def test_future_sprint_progress_hides_today_marker_and_clamps_progress():
    """Future sprint header should not render TODAY marker when not started."""
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
