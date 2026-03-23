"""Unit tests for Sprint Tracker UI builders."""

from typing import Any, cast

from ui.sprint_tracker import create_sprint_scope_changes_view


def test_scope_changes_view_renders_for_future_sprint():
    """Future sprints should render an upcoming scope changes card."""
    component = create_sprint_scope_changes_view(
        {"added": ["PROJ-1"], "removed": []},
        sprint_state="FUTURE",
        issue_states={
            "PROJ-1": {
                "issue_type": "Story",
                "summary": "Future scoped issue",
            }
        },
    )

    assert component.__class__.__name__ == "Card"

    children = cast(list[Any], component.children)
    header_children = children[0].children
    assert "Upcoming Sprint Scope Changes" in str(header_children)
