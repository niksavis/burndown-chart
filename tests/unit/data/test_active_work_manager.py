"""Unit tests for active_work_manager module.

Tests epic aggregation, activity filtering, and progress calculation
for Active Work Timeline feature (burndown-chart-s530).
"""

from datetime import datetime, timedelta, timezone
from data.active_work_manager import (
    _add_health_indicators,
    _build_epic_timeline,
    calculate_epic_progress,
    filter_active_issues,
    get_active_work_data,
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

        # Check timeline has epics
        assert len(result["timeline"]) > 0
        assert result["timeline"][0]["epic_key"] == "EPIC-1"

        # Check issues have health indicators in timeline
        child_issues = result["timeline"][0]["child_issues"]
        assert len(child_issues) == 2
        for issue in child_issues:
            assert "health_indicators" in issue


class TestFilterActiveIssues:
    """Test suite for filter_active_issues function."""

    def test_filter_issues_within_data_points_window(self):
        """Test filtering by data points window."""
        now = datetime.now(timezone.utc)
        recent = now - timedelta(days=7)
        old = now - timedelta(days=60)

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "In Progress",
                "updated": recent.isoformat(),
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "updated": old.isoformat(),
            },
        ]

        filtered = filter_active_issues(
            issues,
            data_points_count=2,
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )

        all_keys = [issue["issue_key"] for issue in filtered]
        assert "PROJ-1" in all_keys
        assert "PROJ-2" not in all_keys

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
            issues,
            data_points_count=2,
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )

        all_keys = [issue["issue_key"] for issue in filtered]
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


class TestHealthIndicators:
    """Test suite for health indicator logic."""

    def test_add_health_indicators_blocked_aging_wip(self):
        """Test blocked, aging, and WIP indicators from changelog data."""
        now = datetime.now(timezone.utc)

        changelog_entries = {
            "PROJ-1": [{"change_date": (now - timedelta(days=6)).isoformat()}],
            "PROJ-2": [{"change_date": (now - timedelta(days=4)).isoformat()}],
            "PROJ-3": [{"change_date": (now - timedelta(days=1)).isoformat()}],
        }

        class FakeBackend:
            def get_changelog_entries(
                self, profile_id, query_id, issue_key, field_name
            ):
                return changelog_entries.get(issue_key, [])

        backend = FakeBackend()

        blocked_issue = _add_health_indicators(
            {"issue_key": "PROJ-1", "status": "In Progress"},
            backend,
            "profile",
            "query",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )
        aging_issue = _add_health_indicators(
            {"issue_key": "PROJ-2", "status": "In Progress"},
            backend,
            "profile",
            "query",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )
        wip_issue = _add_health_indicators(
            {"issue_key": "PROJ-3", "status": "In Progress"},
            backend,
            "profile",
            "query",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )

        assert blocked_issue["health_indicators"]["is_blocked"] is True
        assert aging_issue["health_indicators"]["is_aging"] is True
        assert wip_issue["health_indicators"]["is_wip"] is True

    def test_add_health_indicators_completed_issue(self):
        """Test completed status sets completion indicator."""
        issue = _add_health_indicators(
            {"issue_key": "PROJ-4", "status": "Done"},
            backend=None,
            profile_id=None,
            query_id=None,
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
        )

        assert issue["health_indicators"]["is_completed"] is True
        assert issue["health_indicators"]["is_blocked"] is False
        assert issue["health_indicators"]["is_aging"] is False
        assert issue["health_indicators"]["is_wip"] is False


class TestBuildEpicTimeline:
    """Test suite for epic timeline aggregation."""

    def test_build_epic_timeline_uses_unfiltered_parent_summary(self):
        """Test parent summary lookup from unfiltered issues list."""
        child_issue = {
            "issue_key": "PROJ-1",
            "status": "In Progress",
            "points": 3.0,
            "parent": "EPIC-1",
            "health_indicators": {},
        }
        parent_issue = {"issue_key": "EPIC-1", "summary": "Parent Epic"}

        timeline = _build_epic_timeline(
            issues=[child_issue],
            backend=None,
            profile_id=None,
            query_id=None,
            parent_field="parent",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
            all_issues_unfiltered=[child_issue, parent_issue],
        )

        assert timeline[0]["epic_key"] == "EPIC-1"
        assert timeline[0]["epic_summary"] == "Parent Epic"

    def test_build_epic_timeline_customfield_parent(self):
        """Test custom field parent handling for epic summary."""
        child_issue = {
            "issue_key": "PROJ-2",
            "status": "In Progress",
            "points": 2.0,
            "custom_fields": {
                "customfield_10006": {
                    "key": "EPIC-9",
                    "summary": "Custom Epic",
                }
            },
            "health_indicators": {},
        }

        timeline = _build_epic_timeline(
            issues=[child_issue],
            backend=None,
            profile_id=None,
            query_id=None,
            parent_field="customfield_10006",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
            all_issues_unfiltered=[child_issue],
        )

        assert timeline[0]["epic_key"] == "EPIC-9"
        assert timeline[0]["epic_summary"] == "Custom Epic"

    def test_build_epic_timeline_sorts_by_health_priority(self):
        """Test child issue sorting order by health priority."""
        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "In Progress",
                "parent": "EPIC-2",
                "health_indicators": {"is_blocked": True},
            },
            {
                "issue_key": "PROJ-2",
                "status": "In Progress",
                "parent": "EPIC-2",
                "health_indicators": {"is_aging": True},
            },
            {
                "issue_key": "PROJ-3",
                "status": "In Progress",
                "parent": "EPIC-2",
                "health_indicators": {"is_wip": True},
            },
            {
                "issue_key": "PROJ-4",
                "status": "To Do",
                "parent": "EPIC-2",
                "health_indicators": {},
            },
            {
                "issue_key": "PROJ-5",
                "status": "Done",
                "parent": "EPIC-2",
                "health_indicators": {"is_completed": True},
            },
        ]

        timeline = _build_epic_timeline(
            issues=issues,
            backend=None,
            profile_id=None,
            query_id=None,
            parent_field="parent",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
            all_issues_unfiltered=issues,
        )

        sorted_keys = [issue["issue_key"] for issue in timeline[0]["child_issues"]]
        assert sorted_keys == [
            "PROJ-1",
            "PROJ-2",
            "PROJ-3",
            "PROJ-4",
            "PROJ-5",
        ]

    def test_build_epic_timeline_sorts_epics_by_completion_desc(self):
        """Test epic ordering by completion percentage with completed last."""
        issues = [
            {
                "issue_key": "PROJ-10",
                "status": "Done",
                "points": 8.0,
                "parent": "EPIC-B",
                "health_indicators": {"is_completed": True},
            },
            {
                "issue_key": "PROJ-11",
                "status": "To Do",
                "points": 2.0,
                "parent": "EPIC-B",
                "health_indicators": {},
            },
            {
                "issue_key": "PROJ-20",
                "status": "Done",
                "points": 5.0,
                "parent": "EPIC-A",
                "health_indicators": {"is_completed": True},
            },
            {
                "issue_key": "PROJ-21",
                "status": "In Progress",
                "points": 5.0,
                "parent": "EPIC-A",
                "health_indicators": {"is_wip": True},
            },
            {
                "issue_key": "PROJ-30",
                "status": "Done",
                "points": 3.0,
                "parent": "EPIC-C",
                "health_indicators": {"is_completed": True},
            },
            {
                "issue_key": "PROJ-31",
                "status": "Done",
                "points": 2.0,
                "parent": "EPIC-C",
                "health_indicators": {"is_completed": True},
            },
        ]

        timeline = _build_epic_timeline(
            issues=issues,
            backend=None,
            profile_id=None,
            query_id=None,
            parent_field="parent",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
            all_issues_unfiltered=issues,
        )

        epic_order = [epic["epic_key"] for epic in timeline]
        assert epic_order == ["EPIC-B", "EPIC-A", "EPIC-C"]

    def test_build_epic_timeline_sorts_epics_by_health_priority_on_tie(self):
        """Test health priority tie-breaker for epics with equal completion."""
        issues = [
            {
                "issue_key": "PROJ-40",
                "status": "Done",
                "points": 5.0,
                "parent": "EPIC-X",
                "health_indicators": {"is_completed": True},
            },
            {
                "issue_key": "PROJ-41",
                "status": "In Progress",
                "points": 5.0,
                "parent": "EPIC-X",
                "health_indicators": {"is_blocked": True},
            },
            {
                "issue_key": "PROJ-50",
                "status": "Done",
                "points": 5.0,
                "parent": "EPIC-Y",
                "health_indicators": {"is_completed": True},
            },
            {
                "issue_key": "PROJ-51",
                "status": "In Progress",
                "points": 5.0,
                "parent": "EPIC-Y",
                "health_indicators": {"is_aging": True},
            },
        ]

        timeline = _build_epic_timeline(
            issues=issues,
            backend=None,
            profile_id=None,
            query_id=None,
            parent_field="parent",
            flow_end_statuses=["Done"],
            flow_wip_statuses=["In Progress"],
            all_issues_unfiltered=issues,
        )

        epic_order = [epic["epic_key"] for epic in timeline]
        assert epic_order == ["EPIC-X", "EPIC-Y"]
