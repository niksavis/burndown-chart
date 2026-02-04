"""Unit tests for redesigned Active Work Timeline.

Tests Active Work timeline with health indicators.
"""

from datetime import datetime, timedelta, timezone
from data.active_work_manager import (
    get_active_work_data,
    calculate_epic_progress,
)


class TestGetActiveWorkData:
    """Test suite for get_active_work_data function."""

    def test_returns_correct_structure(self):
        """Test that function returns timeline and issue lists."""
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
        ]

        result = get_active_work_data(issues, parent_field="parent")

        # Check structure
        assert "timeline" in result

        # Check issues have health indicators
        child_issues = result["timeline"][0]["child_issues"]
        for issue in child_issues:
            assert "health_indicators" in issue
            assert "is_blocked" in issue["health_indicators"]
            assert "is_aging" in issue["health_indicators"]
            assert "is_completed" in issue["health_indicators"]


class TestCalculateEpicProgress:
    """Test suite for calculate_epic_progress function."""

    def test_basic_progress(self):
        """Test basic progress calculation."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Done", "points": 5.0},
            {"issue_key": "PROJ-2", "status": "In Progress", "points": 3.0},
        ]

        progress = calculate_epic_progress(child_issues)

        assert progress["total_issues"] == 2
        assert progress["completed_issues"] == 1
        assert progress["total_points"] == 8.0
        assert progress["completed_points"] == 5.0
