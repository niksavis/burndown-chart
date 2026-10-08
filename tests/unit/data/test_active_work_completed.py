from collections import OrderedDict
from datetime import date


class TestGetCompletedItemsByWeek:
    def test_basic_bucketing_with_completed_issues(self):
        from data.active_work_completed import get_completed_items_by_week

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

        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        for _week_label, week_data in result.items():
            assert "display_label" in week_data
            assert "issues" in week_data
            assert "is_current" in week_data
            assert "total_issues" in week_data
            assert "total_epics_closed" in week_data
            assert "total_epics_linked" in week_data
            assert "total_points" in week_data
            assert "epic_groups" in week_data

    def test_filters_only_completed_status(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
                "status": "In Progress",
                "fields": {"resolutiondate": recent_date},
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "To Do",
                "fields": {"resolutiondate": recent_date},
                "points": 2.0,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1

    def test_requires_resolutiondate(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
                "fields": {"resolutiondate": None},
                "points": 5.0,
            },
            {
                "issue_key": "PROJ-3",
                "status": "Done",
                "fields": {},
                "points": 2.0,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1

    def test_accepts_flat_resolved_field(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
        from data.active_work_completed import get_completed_items_by_week

        result = get_completed_items_by_week([], n_weeks=2)

        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        for week_data in result.values():
            assert week_data["total_issues"] == 0
            assert week_data["total_points"] == 0.0
            assert week_data["issues"] == []

    def test_no_completed_issues(self):
        from data.active_work_completed import get_completed_items_by_week

        issues = [
            {"issue_key": "PROJ-1", "status": "In Progress", "points": 3.0},
            {"issue_key": "PROJ-2", "status": "To Do", "points": 5.0},
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        assert isinstance(result, OrderedDict)
        assert len(result) == 2

        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 0

    def test_current_week_comes_first(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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

        first_week = list(result.values())[0]
        assert first_week["is_current"] is True

        second_week = list(result.values())[1]
        assert second_week["is_current"] is False

    def test_points_calculation(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

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
                "points": None,
            },
        ]

        result = get_completed_items_by_week(issues, n_weeks=2)

        total_points = sum(week["total_points"] for week in result.values())
        assert total_points == 8.0

    def test_custom_flow_end_statuses(self):
        from datetime import datetime, timedelta

        from data.active_work_completed import get_completed_items_by_week

        now = datetime.now()
        recent_date = (now - timedelta(days=1)).strftime("%Y-%m-%dT10:00:00.000+0000")

        issues = [
            {
                "issue_key": "PROJ-1",
                "status": "Deployed",
                "fields": {"resolutiondate": recent_date},
                "points": 3.0,
            },
            {
                "issue_key": "PROJ-2",
                "status": "Done",
                "fields": {"resolutiondate": recent_date},
                "points": 5.0,
            },
        ]

        result = get_completed_items_by_week(
            issues, n_weeks=2, flow_end_statuses=["Deployed", "Released"]
        )

        total_issues = sum(week["total_issues"] for week in result.values())
        assert total_issues == 1


class TestFormatWeekLabel:
    def test_current_week_label(self):
        from data.active_work_completed import _format_week_label

        monday = date(2026, 2, 3)
        sunday = date(2026, 2, 9)

        result = _format_week_label("2026-W06", monday, sunday, is_current=True)

        assert result == "Current Week (Feb 3-9)"
        assert "Current Week" in result
        assert "Feb 3-9" in result

    def test_last_week_label(self):
        from data.active_work_completed import _format_week_label

        monday = date(2026, 1, 27)
        sunday = date(2026, 2, 2)

        result = _format_week_label("2026-W05", monday, sunday, is_current=False)

        assert result == "Last Week (Jan 27 - Feb 2)"
        assert "Last Week" in result
        assert "Jan 27 - Feb 2" in result

    def test_same_month_formatting(self):
        from data.active_work_completed import _format_week_label

        monday = date(2026, 2, 16)
        sunday = date(2026, 2, 22)

        result = _format_week_label("2026-W08", monday, sunday, is_current=True)

        assert "Feb 16-22" in result

    def test_month_boundary_formatting(self):
        from data.active_work_completed import _format_week_label

        monday = date(2026, 1, 26)
        sunday = date(2026, 2, 1)

        result = _format_week_label("2026-W05", monday, sunday, is_current=False)

        assert "Jan 26 - Feb 1" in result or "Jan 26-Feb 1" in result


class TestCreateEmptyWeekStructure:
    def test_creates_correct_number_of_weeks(self):
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        assert len(result) == 2

    def test_all_weeks_are_empty(self):
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        for week_data in result.values():
            assert week_data["total_issues"] == 0
            assert week_data["total_points"] == 0.0
            assert week_data["issues"] == []

    def test_current_week_flag_set(self):
        from data.active_work_completed import _create_empty_week_structure

        result = _create_empty_week_structure(n_weeks=2)

        first_week = list(result.values())[0]
        assert first_week["is_current"] is True

        other_weeks = list(result.values())[1:]
        for week in other_weeks:
            assert week["is_current"] is False
