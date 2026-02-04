"""Integration tests for Active Work Timeline flow."""

import unittest
from datetime import datetime, timedelta, timezone

from dash import html

from data.active_work_manager import get_active_work_data
from ui.active_work_epic_timeline import create_nested_epic_timeline


class TestActiveWorkTimelineFlow(unittest.TestCase):
    """Integration coverage for active work timeline data to UI pipeline."""

    def test_active_work_data_renders_timeline_component(self):
        """Test end-to-end flow from data aggregation to UI component."""
        now = datetime.now(timezone.utc)
        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Task 1",
                "status": "In Progress",
                "points": 5.0,
                "updated": now.isoformat(),
                "created": (now - timedelta(days=2)).isoformat(),
                "parent": {"key": "EPIC-1", "summary": "Epic 1"},
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Task 2",
                "status": "Done",
                "points": 3.0,
                "updated": now.isoformat(),
                "created": (now - timedelta(days=3)).isoformat(),
                "parent": {"key": "EPIC-1", "summary": "Epic 1"},
            },
        ]

        work_data = get_active_work_data(issues, parent_field="parent")
        component = create_nested_epic_timeline(
            work_data["timeline"],
            show_points=True,
            parent_field_configured=True,
            summary_text="Integration summary",
        )

        self.assertIsInstance(component, html.Div)
        self.assertIn("Integration summary", str(component.to_plotly_json()))
