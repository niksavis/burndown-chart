"""Tests for Active Work epic timeline card rendering."""

from ui.active_work_epic_timeline import _render_filtered_timeline


def test_render_filtered_timeline_shows_empty_epic_message() -> None:
    """Standalone epic cards should show a clear empty-state message."""
    timeline = [
        {
            "epic_key": "EPIC-123",
            "epic_summary": "Standalone Epic",
            "child_issues": [],
            "total_points": 0.0,
        }
    ]

    cards = _render_filtered_timeline(timeline, show_points=False)

    assert len(cards) == 1
    card_json = str(cards[0].to_plotly_json())
    assert "No tickets assigned to this epic." in card_json


def test_render_filtered_timeline_keeps_no_parent_empty_message() -> None:
    """No Parent bucket should keep the generic empty-state message."""
    timeline = [
        {
            "epic_key": "No Parent",
            "epic_summary": "Other",
            "child_issues": [],
            "total_points": 0.0,
        }
    ]

    cards = _render_filtered_timeline(timeline, show_points=False)

    assert len(cards) == 1
    card_json = str(cards[0].to_plotly_json())
    assert "No issues" in card_json
