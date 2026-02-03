"""Unit tests for active_work_manager module.

Tests epic aggregation, activity filtering, and progress calculation
for Active Work Timeline feature (burndown-chart-s530).

Updated for 2-week window design (WIP + recent completions).
"""

from datetime import datetime, timedelta, timezone
from data.active_work_manager import (
    filter_active_issues,
    get_active_work_data,
    calculate_epic_progress,
)


class TestGetActiveWorkData:
    """Test suite for get_active_work_data function."""

    def test_returns_timeline_and_issue_lists(self):
        """Test that function returns correct structure."""
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
                "created": (now - timedelta(days=1)).isoformat(),
                "parent": {"key": "EPIC-1", "summary": "Epic 1"},
            },
        ]

        result = get_active_work_data(issues, parent_field="parent")

        # Check structure
        assert "timeline" in result
        assert "last_week_issues" in result
        assert "this_week_issues" in result

        # Check timeline has epics
        assert len(result["timeline"]) > 0
        assert result["timeline"][0]["epic_key"] == "EPIC-1"

        # Check issues have health indicators
        all_issues = result["last_week_issues"] + result["this_week_issues"]
        assert len(all_issues) == 2
        for issue in all_issues:
            assert "health_indicators" in issue


class TestFilterActiveIssues:
    """Test suite for filter_active_issues function."""

    def test_filter_wip_issues_any_age(self):
        """Test that WIP issues are included regardless of age."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=60)  # Very old

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "In Progress",
                "updated": old.isoformat(),
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "updated": old.isoformat(),
            },  # Old completion
        ]

        filtered = filter_active_issues(
            issues, flow_end_statuses=["Done"], flow_wip_statuses=["In Progress"]
        )

        # WIP issue should be included even if old
        all_issues = filtered["last_week"] + filtered["this_week"]
        all_keys = [issue["issue_key"] for issue in all_issues]
        assert "PROJ-1" in all_keys  # Old WIP still included
        assert "PROJ-2" not in all_keys  # Old completion excluded

    def test_filter_completed_within_2_weeks(self):
        """Test that completed issues from last 2 weeks are included."""
        now = datetime.now(timezone.utc)
        recent_complete = now - timedelta(days=7)
        old_complete = now - timedelta(days=30)

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "updated": recent_complete.isoformat(),
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "updated": old_complete.isoformat(),
            },
        ]

        filtered = filter_active_issues(
            issues, flow_end_statuses=["Done"], flow_wip_statuses=["In Progress"]
        )

        all_issues = filtered["last_week"] + filtered["this_week"]
        all_keys = [issue["issue_key"] for issue in all_issues]
        assert "PROJ-1" in all_keys  # Recent completion included
        assert "PROJ-2" not in all_keys  # Old completion excluded


class TestCalculateEpicProgress:
    """Test suite for calculate_epic_progress function."""

    def test_basic_progress_calculation(self):
        """Test progress calculation with simple statuses."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Done", "points": 5.0},
            {"issue_key": "PROJ-2", "status": "In Progress", "points": 3.0},
            {"issue_key": "PROJ-3", "status": "To Do", "points": 2.0},
        ]

        progress = calculate_epic_progress(child_issues)

        assert progress["total_issues"] == 3
        assert progress["completed_issues"] == 1
        assert progress["in_progress_issues"] == 1
        assert progress["todo_issues"] == 1
        assert progress["total_points"] == 10.0
        assert progress["completed_points"] == 5.0
        assert progress["completion_pct"] == 50.0

    def test_handles_missing_points(self):
        """Test handling issues without story points."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Done"},  # No points
            {"issue_key": "PROJ-2", "status": "Done", "points": None},  # Null points
            {"issue_key": "PROJ-3", "status": "In Progress", "points": 5.0},
        ]

        progress = calculate_epic_progress(child_issues)

        assert progress["total_issues"] == 3
        assert progress["completed_issues"] == 2
        assert progress["total_points"] == 5.0
        assert progress["completed_points"] == 0.0

    def test_completion_pct_fallback_to_count(self):
        """Test completion percentage falls back to issue count when no points."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Done"},
            {"issue_key": "PROJ-2", "status": "Done"},
            {"issue_key": "PROJ-3", "status": "In Progress"},
            {"issue_key": "PROJ-4", "status": "To Do"},
        ]

        progress = calculate_epic_progress(child_issues)

        assert progress["total_points"] == 0.0
        assert progress["completion_pct"] == 50.0  # 2 of 4 issues done

    def test_custom_status_mappings(self):
        """Test using custom flow status mappings."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Released", "points": 5.0},
            {"issue_key": "PROJ-2", "status": "Code Review", "points": 3.0},
        ]

        progress = calculate_epic_progress(
            child_issues,
            flow_end_statuses=["Released"],
            flow_wip_statuses=["Code Review"],
        )

        assert progress["completed_issues"] == 1
        assert progress["in_progress_issues"] == 1
        assert progress["completed_points"] == 5.0

    def test_by_status_breakdown(self):
        """Test status breakdown aggregation."""
        child_issues = [
            {"issue_key": "PROJ-1", "status": "Done", "points": 5.0},
            {"issue_key": "PROJ-2", "status": "Done", "points": 3.0},
            {"issue_key": "PROJ-3", "status": "In Progress", "points": 2.0},
        ]

        progress = calculate_epic_progress(child_issues)

        assert "Done" in progress["by_status"]
        assert progress["by_status"]["Done"]["count"] == 2
        assert progress["by_status"]["Done"]["points"] == 8.0

        assert "In Progress" in progress["by_status"]
        assert progress["by_status"]["In Progress"]["count"] == 1
        assert progress["by_status"]["In Progress"]["points"] == 2.0
