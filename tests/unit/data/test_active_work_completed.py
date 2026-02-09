"""Unit tests for active_work_completed module.

Tests completed items bucketing and week formatting.
"""

from datetime import date
from collections import OrderedDict


class TestGetCompletedItemsByWeek:
    """Test get_completed_items_by_week function."""

    def test_basic_bucketing_with_completed_issues(self):
        """Test basic bucketing of completed issues into weeks."""
        from data.active_work_completed import get_completed_items_by_week

        # Create test issues with resolutiondate in current week (JIRA format)
        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "fields": {"resolutiondate": "2026-02-09T10:00:00.000+0000"},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "Closed",
                "fields": {"resolutiondate": "2026-02-03T10:00:00.000+0000"},
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "Done",
                "fields": {"resolutiondate": "2026-01-30T10:00:00.000+0000"},
                "points": 2.0,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        # Should return OrderedDict with 2 weeks
        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        # Check structure
        for week_label, week_data in result.items():
            assert "display_label" in week_data
            assert "issues" in week_data
            assert "is_current" in week_data
            assert "total_issues" in week_data
            assert "total_epics_closed" in week_data
            assert "total_epics_linked" in week_data
            assert "total_points" in week_data
            assert "epic_groups" in week_data

    def test_filters_only_completed_status(self):
        """Test that only completed statuses are included."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        # Use dates from within the last 2 weeks
        now = datetime.now()
        recent_date = (now - timedelta(days=3)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "In Progress",  # Not completed
                "fields": {"resolutiondate": recent_date},
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "To Do",  # Not completed
                "fields": {"resolutiondate": recent_date},
                "points": 2.0,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        # Should only include PROJ-1
        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1

    def test_requires_resolutiondate(self):
        """Test that issues without resolutiondate are excluded."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=3)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "fields": {"resolutiondate": None},  # No resolution date
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "Done",
                "fields": {},  # Missing resolutiondate field
                "points": 2.0,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        # Should only include PROJ-1
        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1

    def test_accepts_flat_resolved_field(self):
        """Test that flat resolved field is accepted for bucketing."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=2)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "resolved": recent_date,
                "points": 3.0,
            }
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1

    def test_counts_epics_and_filters_parent_issues(self):
        """Test epic counting and parent filtering when parent_field is provided."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=2)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "EPIC-1",
                "status": "Done",
                "resolved": recent_date,
                "issue_type": "Epic",
            },
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "resolved": recent_date,
                "parent": {"key": "EPIC-1", "summary": "Epic One"},
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "resolved": recent_date,
                "parent": {"key": "EPIC-1", "summary": "Epic One"},
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2, parent_field="parent")

        total_issues = sum(week["total_issues"] for week in result.values())
        total_epics_closed = sum(week["total_epics_closed"] for week in result.values())
        total_epics_linked = sum(week["total_epics_linked"] for week in result.values())

        assert total_epics_closed == 1
        assert total_epics_linked == 1
        assert total_issues == 2

    def test_uses_epic_summary_from_all_issues(self):
        """Test epic summary lookup when parent field is a string key."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=2)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "EPIC-1",
                "status": "In Progress",
                "summary": "Customer Validation for Tariff Change",
            },
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "resolved": recent_date,
                "parent": "EPIC-1",
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2, parent_field="parent")

        epic_groups = next(
            (week["epic_groups"] for week in result.values() if week["epic_groups"]),
            [],
        )
        assert epic_groups[0]["epic_key"] == "EPIC-1"
        assert epic_groups[0]["epic_summary"] == "Customer Validation for Tariff Change"

    def test_empty_issues_list(self):
        """Test handling of empty issues list."""
        from data.active_work_completed import get_completed_items_by_week

        result = get_completed_items_by_week([], n_weeks=2)

        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        # All weeks should be empty
        for week_data in result.values():
            assert week_data["total_issues"] == 0
            assert week_data["total_points"] == 0.0
            assert week_data["issues"] == []

    def test_no_completed_issues(self):
        """Test handling when no issues are completed."""
        from data.active_work_completed import get_completed_items_by_week

        issues = [
            {"issue_key": "PROJ-1", "status": "In Progress", "points": 3.0},
            {"issue_key": "PROJ-2", "status": "To Do", "points": 5.0},
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        # All weeks should be empty
        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 0

    def test_current_week_comes_first(self):
        """Test that current week is first in the result."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=1)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            }
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        # First item should be current week
        first_week = list(result.values())[0]
        assert first_week["is_current"] is True

        # Second item should be last week
        second_week = list(result.values())[1]
        assert second_week["is_current"] is False

    def test_points_calculation(self):
        """Test that points are correctly summed."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=2)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": None,  # No points
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        # Sum points across all weeks (test is date-independent)
        total_points = sum(week["total_points"] for week in result.values())
        assert total_points == 8.0  # 3.0 + 5.0 + 0

    def test_custom_flow_end_statuses(self):
        """Test using custom completion statuses."""
        from data.active_work_completed import get_completed_items_by_week
        from datetime import datetime, timedelta

        now = datetime.now()
        recent_date = (now - timedelta(days=1)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Deployed",  # Custom status
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",  # Won't match custom list
                "fields": {"resolutiondate": recent_date},
                "points": 5.0,
            },
        ]

        result = get_completed_items_by_week(
            issues, n_weeks=2, flow_end_statuses=["Deployed", "Released"]
        )

        # Should only include PROJ-1
        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1


class TestFormatWeekLabel:
    """Test _format_week_label helper function."""

    def test_current_week_label(self):
        """Test formatting of current week label."""
        from data.active_work_completed import _format_week_label

        monday = date(2026, 2, 3)
        sunday = date(2026, 2, 9)

        result = _format_week_label("2026-W06", monday, sunday, is_current=True)

        assert result == "Current Week (Feb 3-9)"
        assert "Current Week" in result
        assert "Feb 3-9" in result

    def test_last_week_label(self):
        """Test formatting of last week label."""
        from data.active_work_completed import _format_week_label

        monday = date(2026, 1, 27)
        sunday = date(2026, 2, 2)

        result = _format_week_label("2026-W05", monday, sunday, is_current=False)

        assert result == "Last Week (Jan 27 - Feb 2)"
        assert "Last Week" in result
        assert "Jan 27 - Feb 2" in result

    def test_same_month_formatting(self):
        """Test date range formatting when week is within same month."""
        from data.active_work_completed import _format_week_label

        monday = date(2026, 2, 16)
        sunday = date(2026, 2, 22)

        result = _format_week_label("2026-W08", monday, sunday, is_current=True)

        # Should use abbreviated format for same month
        assert "Feb 16-22" in result

    def test_month_boundary_formatting(self):
        """Test date range formatting when week crosses month boundary."""
        from data.active_work_completed import _format_week_label

        monday = date(2026, 1, 26)
        sunday = date(2026, 2, 1)

        result = _format_week_label("2026-W05", monday, sunday, is_current=False)

        # Should show both months
        assert "Jan 26 - Feb 1" in result or "Jan 26-Feb 1" in result


class TestCreateEmptyWeekStructure:
    """Test _create_empty_week_structure helper function."""

    def test_creates_correct_number_of_weeks(self):
        """Test that correct number of weeks are created."""
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        assert len(result) == 2

    def test_all_weeks_are_empty(self):
        """Test that all weeks have zero counts."""
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        for week_data in result.values():
            assert week_data["total_issues"] == 0
            assert week_data["total_points"] == 0.0
            assert week_data["issues"] == []

    def test_current_week_flag_set(self):
        """Test that is_current flag is set correctly."""
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        # First week should be current
        first_week = list(result.values())[0]
        assert first_week["is_current"] is True

        # Other weeks should not be current
        other_weeks = list(result.values())[1:]
        for week in other_weeks:
            assert week["is_current"] is False
