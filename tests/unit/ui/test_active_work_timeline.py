"""Unit tests for Active Work Timeline UI components."""

from dash import html
import dash_bootstrap_components as dbc

from ui.active_work_timeline import (
    create_active_work_timeline_tab,
    create_issue_card,
    create_no_issues_state,
    create_timeline_visualization,
)


def _find_first_component(component, component_type):
    if isinstance(component, component_type):
        return component

    children = getattr(component, "children", None)
    if children is None:
        return None

    if isinstance(children, (list, tuple)):
        for child in children:
            found = _find_first_component(child, component_type)
            if found is not None:
                return found
    else:
        return _find_first_component(children, component_type)

    return None


def test_create_active_work_timeline_tab_placeholder():
    """Test placeholder container for active work timeline tab."""
    component = create_active_work_timeline_tab()

    assert isinstance(component, html.Div)
    assert component.id == "active-work-timeline-tab-content"  # type: ignore[attr-defined]


def test_create_no_issues_state_unconfigured_parent_field():
    """Test empty state messaging when parent field is missing."""
    component = create_no_issues_state(parent_field_configured=False)

    content = str(component.to_plotly_json())
    assert "Configure Parent/Epic Field" in content


def test_create_no_issues_state_configured_parent_field():
    """Test empty state messaging when no issues found."""
    component = create_no_issues_state(parent_field_configured=True)

    content = str(component.to_plotly_json())
    assert "No Active Work Found" in content


def test_create_timeline_visualization_progress_and_points():
    """Test progress color and points text in timeline visualization."""
    timeline = [
        {
            "epic_key": "EPIC-1",
            "epic_summary": "Epic 1",
            "completion_pct": 80.0,
            "total_issues": 4,
            "completed_issues": 3,
            "total_points": 13.0,
            "completed_points": 8.0,
        }
    ]

    component = create_timeline_visualization(timeline, show_points=True)

    progress = _find_first_component(component, dbc.Progress)
    assert progress is not None
    assert getattr(progress, "color", None) == "success"

    content = str(component.to_plotly_json())
    assert "pts" in content


def test_create_issue_card_parent_and_orphan_behavior():
    """Test parent indicator and orphan styling in issue cards."""
    parent_issue = {
        "issue_key": "PROJ-1",
        "summary": "Task",
        "status": "In Progress",
        "issue_type": "Task",
        "parent": {"key": "EPIC-1", "summary": "Epic 1"},
        "health_indicators": {},
    }

    parent_card = create_issue_card(parent_issue)
    parent_json = parent_card.to_plotly_json()
    assert parent_json["props"]["data-parent-key"] == "EPIC-1"

    orphan_issue = {
        "issue_key": "PROJ-2",
        "summary": "Orphan",
        "status": "To Do",
        "issue_type": "Task",
        "health_indicators": {},
    }

    orphan_card = create_issue_card(orphan_issue)
    assert isinstance(orphan_card, dbc.Card)
    assert "orphaned-issue" in getattr(orphan_card, "className", "")
