"""Unit tests for Active Work Timeline legend components."""

from ui.active_work_components import create_active_work_legend


def test_create_active_work_legend_includes_epic_todo_signal():
    """Test legend includes epic todo signal badge and tooltip target."""
    component = create_active_work_legend()
    content = str(component.to_plotly_json())

    assert "legend-epic-todo" in content
    assert (
        "Epic is to do when all issues are not in progress, aging, idle, or done"
        in content
    )
