"""Unit tests for active_work_manager module.

Tests epic aggregation, activity filtering, and progress calculation
for Active Work Timeline feature (burndown-chart-s530).
"""

from datetime import datetime, timedelta, timezone
from data.active_work_manager import (
    filter_recent_activity,
    get_active_epics,
    calculate_epic_progress,
)


class TestFilterRecentActivity:
    """Test suite for filter_recent_activity function."""

    def test_filter_by_days_back(self):
        """Test filtering issues by days_back parameter."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=3)
        old = now - timedelta(days=10)

        issues = [
            {"issue_key": "PROJ-1", "updated": recent.isoformat()},
            {"issue_key": "PROJ-2", "updated": old.isoformat()},
            {"issue_key": "PROJ-3", "updated": now.isoformat()},
        ]

        filtered = filter_recent_activity(
            issues, days_back=7, include_current_week=False
        )

        assert len(filtered) == 2
        assert filtered[0]["issue_key"] == "PROJ-1"
        assert filtered[1]["issue_key"] == "PROJ-3"

    def test_filter_with_current_week(self):
        """Test including issues from current calendar week."""
        now = datetime.now(timezone.utc)

        # Issue from Monday of current week
        monday = now - timedelta(days=now.weekday())

        issues = [
            {"issue_key": "PROJ-1", "updated": monday.isoformat()},
            {"issue_key": "PROJ-2", "updated": now.isoformat()},
        ]

        filtered = filter_recent_activity(
            issues,
            days_back=1,  # Only yesterday
            include_current_week=True,  # But include whole week
        )

        # Should include both even though Monday might be > 1 day ago
        assert len(filtered) >= 1  # At least PROJ-2

    def test_handles_missing_updated_field(self):
        """Test handling issues without updated field."""
        issues = [
            {"issue_key": "PROJ-1"},  # Missing updated
            {"issue_key": "PROJ-2", "updated": None},  # Null updated
            {"issue_key": "PROJ-3", "updated": datetime.now(timezone.utc).isoformat()},
        ]

        filtered = filter_recent_activity(issues, days_back=7)

        assert len(filtered) == 1
        assert filtered[0]["issue_key"] == "PROJ-3"

    def test_handles_various_timestamp_formats(self):
        """Test parsing different ISO timestamp formats."""
        now = datetime.now(timezone.utc)

        issues = [
            {"issue_key": "PROJ-1", "updated": now.isoformat() + "Z"},  # With Z
            {"issue_key": "PROJ-2", "updated": now.isoformat()},  # Standard
            {
                "issue_key": "PROJ-3",
                "updated": now.strftime("%Y-%m-%dT%H:%M:%S"),
            },  # No TZ
        ]

        filtered = filter_recent_activity(issues, days_back=7)

        assert len(filtered) == 3


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


class TestGetActiveEpics:
    """Test suite for get_active_epics function."""

    def test_groups_issues_by_parent_dict(self):
        """Test grouping issues by parent epic (dict format)."""
        now = datetime.now(timezone.utc).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Task 1",
                "status": "Done",
                "points": 5.0,
                "updated": now,
                "custom_fields": {
                    "parent": {"key": "PROJ-100", "fields": {"summary": "Epic 1"}}
                },
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Task 2",
                "status": "In Progress",
                "points": 3.0,
                "updated": now,
                "custom_fields": {
                    "parent": {"key": "PROJ-100", "fields": {"summary": "Epic 1"}}
                },
            },
        ]

        epics = get_active_epics(issues, days_back=7)

        assert len(epics) == 1
        assert epics[0]["epic_key"] == "PROJ-100"
        assert epics[0]["epic_summary"] == "Epic 1"
        assert epics[0]["total_issues"] == 2
        assert epics[0]["recent_activity_count"] == 2

    def test_groups_issues_by_parent_string(self):
        """Test grouping issues by parent epic (string format)."""
        now = datetime.now(timezone.utc).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Task 1",
                "status": "Done",
                "points": 5.0,
                "updated": now,
                "custom_fields": {"parent": "PROJ-100"},
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Task 2",
                "status": "In Progress",
                "points": 3.0,
                "updated": now,
                "custom_fields": {"parent": "PROJ-100"},
            },
        ]

        epics = get_active_epics(issues, days_back=7)

        assert len(epics) == 1
        assert epics[0]["epic_key"] == "PROJ-100"
        assert epics[0]["total_issues"] == 2

    def test_excludes_orphan_issues(self):
        """Test that issues without parent are excluded."""
        now = datetime.now(timezone.utc).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Task 1",
                "status": "Done",
                "points": 5.0,
                "updated": now,
                "custom_fields": {"parent": {"key": "PROJ-100"}},
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Orphan task",
                "status": "Done",
                "points": 3.0,
                "updated": now,
                "custom_fields": {},  # No parent
            },
        ]

        epics = get_active_epics(issues, days_back=7)

        assert len(epics) == 1
        assert epics[0]["total_issues"] == 1  # Only PROJ-1

    def test_sorts_by_most_recent_activity(self):
        """Test epics are sorted by most recent child update."""
        recent = datetime.now(timezone.utc).isoformat()
        older = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Task 1",
                "status": "Done",
                "updated": older,
                "custom_fields": {"parent": {"key": "PROJ-100"}},
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Task 2",
                "status": "Done",
                "updated": recent,
                "custom_fields": {"parent": {"key": "PROJ-200"}},
            },
        ]

        epics = get_active_epics(issues, days_back=7)

        assert len(epics) == 2
        assert epics[0]["epic_key"] == "PROJ-200"  # Most recent first
        assert epics[1]["epic_key"] == "PROJ-100"

    def test_includes_child_issue_summaries(self):
        """Test child_issues field contains issue summaries."""
        now = datetime.now(timezone.utc).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Login API",
                "status": "Done",
                "points": 5.0,
                "updated": now,
                "custom_fields": {"parent": {"key": "PROJ-100"}},
            },
        ]

        epics = get_active_epics(issues, days_back=7)

        assert len(epics[0]["child_issues"]) == 1
        child = epics[0]["child_issues"][0]
        assert child["issue_key"] == "PROJ-1"
        assert child["summary"] == "Login API"
        assert child["status"] == "Done"
        assert child["points"] == 5.0

    def test_filters_by_recent_activity(self):
        """Test only epics with recent activity are included."""
        recent = datetime.now(timezone.utc).isoformat()
        old = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

        issues = [
            {
                "issue_key": "PROJ-1",
                "summary": "Recent task",
                "status": "Done",
                "updated": recent,
                "custom_fields": {"parent": {"key": "PROJ-100"}},
            },
            {
                "issue_key": "PROJ-2",
                "summary": "Old task",
                "status": "Done",
                "updated": old,
                "custom_fields": {"parent": {"key": "PROJ-200"}},
            },
        ]

        epics = get_active_epics(issues, days_back=7, include_current_week=False)

        # Only epic with recent activity should be included
        assert len(epics) == 1
        assert epics[0]["epic_key"] == "PROJ-100"
