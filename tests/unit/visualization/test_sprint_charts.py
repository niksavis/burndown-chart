from datetime import UTC, datetime

import pytest

from data.sprint_snapshot_calculator import (
    calculate_daily_sprint_snapshots,
    get_status_at_timestamp,
)
from visualization.sprint_burnup_chart import create_sprint_burnup_chart
from visualization.sprint_cfd_chart import create_sprint_cfd_chart


@pytest.fixture
def mock_sprint_data() -> dict:
    return {
        "name": "Sprint 23",
        "current_issues": ["PROJ-1", "PROJ-2", "PROJ-3"],
        "added_issues": [
            {
                "issue_key": "PROJ-1",
                "timestamp": "2026-02-01T09:00:00Z",
                "points": 5,
            }
        ],
        "removed_issues": [],
        "issue_states": {
            "PROJ-1": {
                "status": "Done",
                "issue_type": "Story",
                "story_points": 5,
            },
            "PROJ-2": {
                "status": "In Progress",
                "issue_type": "Task",
                "story_points": 3,
            },
            "PROJ-3": {
                "status": "To Do",
                "issue_type": "Bug",
                "story_points": 2,
            },
        },
    }


@pytest.fixture
def mock_issues() -> list[dict]:
    return [
        {
            "key": "PROJ-1",
            "status": "Done",
            "fields": {
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "summary": "Implement feature",
            },
            "points": 5,
        },
        {
            "key": "PROJ-2",
            "status": "In Progress",
            "fields": {
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Task"},
                "summary": "Review code",
            },
            "points": 3,
        },
        {
            "key": "PROJ-3",
            "status": "To Do",
            "fields": {
                "status": {"name": "To Do"},
                "issuetype": {"name": "Bug"},
                "summary": "Fix issue",
            },
            "points": 2,
        },
    ]


@pytest.fixture
def mock_status_changelog() -> list[dict]:
    return [
        {
            "issue_key": "PROJ-1",
            "change_date": "2026-02-01T10:00:00Z",
            "field_name": "status",
            "old_value": "To Do",
            "new_value": "In Progress",
        },
        {
            "issue_key": "PROJ-1",
            "change_date": "2026-02-02T14:00:00Z",
            "field_name": "status",
            "old_value": "In Progress",
            "new_value": "Done",
        },
        {
            "issue_key": "PROJ-2",
            "change_date": "2026-02-02T11:00:00Z",
            "field_name": "status",
            "old_value": "To Do",
            "new_value": "In Progress",
        },
    ]


class TestCalculateDailySprintSnapshots:
    def test_basic_daily_snapshots(
        self, mock_sprint_data, mock_issues, mock_status_changelog
    ):
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            mock_status_changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        assert len(snapshots) == 3

        day1 = snapshots[0]
        assert day1["date"] == "2026-02-01"
        assert day1["completed_points"] == 0
        assert day1["total_scope"] == 10
        assert day1["completed_count"] == 0

        day2 = snapshots[1]
        assert day2["date"] == "2026-02-02"
        assert day2["completed_points"] == 0
        assert day2["total_scope"] == 10

        day3 = snapshots[2]
        assert day3["date"] == "2026-02-03"
        assert day3["completed_points"] == 5
        assert day3["completed_count"] == 1

    def test_scope_changes_mid_sprint(self, mock_issues, mock_status_changelog):
        sprint_data = {
            "name": "Sprint 23",
            "current_issues": ["PROJ-1", "PROJ-2"],
            "added_issues": [
                {
                    "issue_key": "PROJ-3",
                    "timestamp": "2026-02-02T15:00:00Z",
                    "points": 2,
                }
            ],
            "removed_issues": [
                {
                    "issue_key": "PROJ-1",
                    "timestamp": "2026-02-02T16:00:00Z",
                    "points": 5,
                }
            ],
            "issue_states": {
                "PROJ-2": {"status": "In Progress", "story_points": 3},
                "PROJ-3": {"status": "To Do", "story_points": 2},
            },
        }

        snapshots = calculate_daily_sprint_snapshots(
            sprint_data,
            mock_issues,
            mock_status_changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert snapshots[0]["total_scope"] == 8

        assert snapshots[1]["total_scope"] == 3

        assert snapshots[2]["total_scope"] == 3

    def test_linear_progress_pattern(self, mock_issues):
        sprint_data = {
            "name": "Sprint Linear",
            "current_issues": ["PROJ-1", "PROJ-2", "PROJ-3"],
            "added_issues": [],
            "removed_issues": [],
            "issue_states": {
                "PROJ-1": {"status": "Done", "story_points": 5},
                "PROJ-2": {"status": "Done", "story_points": 3},
                "PROJ-3": {"status": "Done", "story_points": 2},
            },
        }

        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2026-02-01T14:00:00Z",
                "field_name": "status",
                "old_value": "In Progress",
                "new_value": "Done",
            },
            {
                "issue_key": "PROJ-2",
                "change_date": "2026-02-02T14:00:00Z",
                "field_name": "status",
                "old_value": "In Progress",
                "new_value": "Done",
            },
            {
                "issue_key": "PROJ-3",
                "change_date": "2026-02-03T14:00:00Z",
                "field_name": "status",
                "old_value": "In Progress",
                "new_value": "Done",
            },
        ]

        snapshots = calculate_daily_sprint_snapshots(
            sprint_data,
            mock_issues,
            changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        assert snapshots[0]["completed_points"] == 0
        assert snapshots[1]["completed_points"] == 5
        assert snapshots[2]["completed_points"] == 8

    def test_stalled_sprint_pattern(self, mock_sprint_data, mock_issues):
        changelog = []

        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        for snapshot in snapshots:
            assert snapshot["completed_points"] == 5
            assert snapshot["total_scope"] == 10

    def test_empty_sprint(self):
        sprint_data = {
            "name": "Empty Sprint",
            "current_issues": [],
            "added_issues": [],
            "removed_issues": [],
            "issue_states": {},
        }

        snapshots = calculate_daily_sprint_snapshots(
            sprint_data,
            [],
            [],
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert len(snapshots) == 0

    def test_invalid_date_formats(self, mock_sprint_data, mock_issues):
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            [],
            sprint_start_date="invalid-date",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert len(snapshots) == 0


class TestGetStatusAtTimestamp:
    def test_status_before_any_changes(self, mock_status_changelog, mock_issues):
        issue = {"key": "PROJ-1", "status": "To Do"}
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 1, 9, 0, tzinfo=UTC),
            proj1_changelog,
        )
        assert status == "To Do"

    def test_status_after_transition(self, mock_status_changelog):
        issue = {"key": "PROJ-1", "status": "Done"}
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 2, 15, 0, tzinfo=UTC),
            proj1_changelog,
        )
        assert status == "Done"

    def test_status_between_transitions(self, mock_status_changelog):
        issue = {"key": "PROJ-1", "status": "Done"}
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 2, 12, 0, tzinfo=UTC),
            proj1_changelog,
        )
        assert status == "In Progress"


class TestCreateSprintBurnupChart:
    def test_basic_burnup_chart_creation(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "completed_points": 0,
                "total_scope": 10,
                "completed_count": 0,
                "total_count": 3,
            },
            {
                "date": "2026-02-02",
                "completed_points": 5,
                "total_scope": 10,
                "completed_count": 1,
                "total_count": 3,
            },
            {
                "date": "2026-02-03",
                "completed_points": 10,
                "total_scope": 10,
                "completed_count": 3,
                "total_count": 3,
            },
        ]

        fig = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert fig is not None
        assert "data" in fig
        assert "layout" in fig

        assert len(fig["data"]) == 8  # type: ignore

        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Sprint Scope (Items)" in trace_names
        assert "Completed Issues" in trace_names
        assert "Sprint Scope (Points)" in trace_names
        assert "Completed Points" in trace_names
        assert "Ideal Progress (Items)" in trace_names
        assert "Ideal Progress (Points)" in trace_names

    def test_burnup_with_scope_changes(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "completed_points": 0,
                "total_scope": 10,
                "completed_count": 0,
                "total_count": 3,
            },
            {
                "date": "2026-02-02",
                "completed_points": 5,
                "total_scope": 15,
                "completed_count": 1,
                "total_count": 4,
            },
            {
                "date": "2026-02-03",
                "completed_points": 10,
                "total_scope": 12,
                "completed_count": 2,
                "total_count": 3,
            },
        ]

        fig = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        scope_points_trace = next(
            t
            for t in fig["data"]
            if t["name"] == "Sprint Scope (Points)"  # type: ignore
        )

        scope_items_trace = next(
            t
            for t in fig["data"]
            if t["name"] == "Sprint Scope (Items)"  # type: ignore
        )

        assert scope_points_trace["y"][0] == 10  # type: ignore
        assert scope_points_trace["y"][1] == 15  # type: ignore
        assert scope_points_trace["y"][2] == 12  # type: ignore

        assert scope_items_trace["y"][0] == 3  # type: ignore
        assert scope_items_trace["y"][1] == 4  # type: ignore
        assert scope_items_trace["y"][2] == 3  # type: ignore

    def test_burnup_with_empty_data(self):
        fig = create_sprint_burnup_chart(
            [],
            sprint_name="Empty Sprint",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert fig is not None
        assert "data" in fig

    def test_burnup_with_issue_counts(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "completed_points": 0,
                "total_scope": 10,
                "completed_count": 0,
                "total_count": 5,
            },
            {
                "date": "2026-02-02",
                "completed_points": 0,
                "total_scope": 10,
                "completed_count": 2,
                "total_count": 5,
            },
            {
                "date": "2026-02-03",
                "completed_points": 0,
                "total_scope": 10,
                "completed_count": 5,
                "total_count": 5,
            },
        ]

        fig = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            show_points=False,
        )

        assert fig is not None
        assert "data" in fig
        assert "layout" in fig

        assert len(fig["data"]) == 5  # type: ignore

        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Sprint Scope (Items)" in trace_names
        assert "Completed Issues" in trace_names
        assert "Ideal Progress (Items)" in trace_names

        assert "Sprint Scope (Points)" not in trace_names
        assert "Completed Points" not in trace_names

        assert fig["layout"]["yaxis"]["title"]["text"] == "Issue Count"  # type: ignore

        assert "yaxis2" not in fig["layout"]  # type: ignore

        completed_trace = next(
            t
            for t in fig["data"]
            if t["name"] == "Completed Issues"  # type: ignore
        )

        assert completed_trace["y"][0] == 0  # type: ignore
        assert completed_trace["y"][1] == 2  # type: ignore
        assert completed_trace["y"][2] == 5  # type: ignore

    def test_burnup_points_vs_counts_toggle(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "completed_points": 10,
                "total_scope": 30,
                "completed_count": 3,
                "total_count": 10,
            },
            {
                "date": "2026-02-02",
                "completed_points": 20,
                "total_scope": 30,
                "completed_count": 6,
                "total_count": 10,
            },
        ]

        fig_with_points = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint Test",
            show_points=True,
        )

        fig_without_points = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint Test",
            show_points=False,
        )

        assert "yaxis2" in fig_with_points["layout"]  # type: ignore
        assert fig_with_points["layout"]["yaxis2"]["title"]["text"] == "Story Points"  # type: ignore

        trace_names_with_points = [t["name"] for t in fig_with_points["data"]]  # type: ignore
        assert "Sprint Scope (Items)" in trace_names_with_points
        assert "Sprint Scope (Points)" in trace_names_with_points
        assert "Completed Issues" in trace_names_with_points
        assert "Completed Points" in trace_names_with_points

        assert "yaxis2" not in fig_without_points["layout"]  # type: ignore

        trace_names_without_points = [t["name"] for t in fig_without_points["data"]]  # type: ignore
        assert "Sprint Scope (Items)" in trace_names_without_points
        assert "Completed Issues" in trace_names_without_points
        assert "Sprint Scope (Points)" not in trace_names_without_points
        assert "Completed Points" not in trace_names_without_points

        items_trace_with = next(
            t
            for t in fig_with_points["data"]
            if t["name"] == "Completed Issues"  # type: ignore
        )
        items_trace_without = next(
            t
            for t in fig_without_points["data"]
            if t["name"] == "Completed Issues"  # type: ignore
        )
        assert items_trace_with["y"][0] == 3  # type: ignore
        assert items_trace_with["y"][1] == 6  # type: ignore
        assert items_trace_without["y"][0] == 3  # type: ignore
        assert items_trace_without["y"][1] == 6  # type: ignore

        points_trace = next(
            (t for t in fig_with_points["data"] if t["name"] == "Completed Points"),  # type: ignore
            None,
        )
        assert points_trace is not None
        assert points_trace["y"][0] == 10  # type: ignore
        assert points_trace["y"][1] == 20  # type: ignore


class TestCreateSprintCFDChart:
    def test_basic_cfd_creation(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "status_breakdown": {
                    "To Do": {"count": 2, "points": 7},
                    "In Progress": {"count": 1, "points": 3},
                    "Done": {"count": 0, "points": 0},
                },
            },
            {
                "date": "2026-02-02",
                "status_breakdown": {
                    "To Do": {"count": 1, "points": 2},
                    "In Progress": {"count": 1, "points": 3},
                    "Done": {"count": 1, "points": 5},
                },
            },
            {
                "date": "2026-02-03",
                "status_breakdown": {
                    "To Do": {"count": 0, "points": 0},
                    "In Progress": {"count": 0, "points": 0},
                    "Done": {"count": 3, "points": 10},
                },
            },
        ]

        fig = create_sprint_cfd_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
            use_points=True,
        )

        assert fig is not None
        assert "data" in fig
        assert "layout" in fig

        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Done" in trace_names
        assert "In Progress" in trace_names
        assert "To Do" in trace_names

    def test_cfd_with_custom_statuses(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "status_breakdown": {
                    "Backlog": {"count": 2, "points": 7},
                    "Development": {"count": 1, "points": 3},
                    "Review": {"count": 0, "points": 0},
                    "Closed": {"count": 0, "points": 0},
                },
            }
        ]

        fig = create_sprint_cfd_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
        )

        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Backlog" in trace_names
        assert "Development" in trace_names
        assert "Review" in trace_names
        assert "Closed" in trace_names

    def test_cfd_identifies_bottlenecks(self):
        daily_snapshots = [
            {
                "date": "2026-02-01",
                "status_breakdown": {
                    "To Do": {"count": 2, "points": 7},
                    "In Progress": {"count": 1, "points": 3},
                    "Done": {"count": 0, "points": 0},
                },
            },
            {
                "date": "2026-02-02",
                "status_breakdown": {
                    "To Do": {"count": 0, "points": 0},
                    "In Progress": {"count": 3, "points": 10},
                    "Done": {"count": 0, "points": 0},
                },
            },
        ]

        fig = create_sprint_cfd_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
        )

        in_progress_trace = next(t for t in fig["data"] if t["name"] == "In Progress")  # type: ignore

        assert in_progress_trace["y"][0] < in_progress_trace["y"][1]  # type: ignore


class TestSprintChartsIntegration:
    def test_full_chart_generation_flow(
        self, mock_sprint_data, mock_issues, mock_status_changelog
    ):
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            mock_status_changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        assert len(snapshots) > 0

        burnup_fig = create_sprint_burnup_chart(
            snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert burnup_fig is not None
        assert (
            len(burnup_fig["data"]) >= 2  # type: ignore[arg-type]
        )

        cfd_fig = create_sprint_cfd_chart(
            snapshots,
            sprint_name="Sprint 23",
        )

        assert cfd_fig is not None
        assert len(cfd_fig["data"]) > 0  # type: ignore

    def test_chart_data_accuracy(self, mock_issues):
        sprint_data = {
            "name": "Sprint Accuracy Test",
            "current_issues": ["PROJ-1", "PROJ-2"],
            "added_issues": [],
            "removed_issues": [],
            "issue_states": {
                "PROJ-1": {"status": "Done", "story_points": 5},
                "PROJ-2": {"status": "In Progress", "story_points": 3},
            },
        }

        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": "2026-02-02T14:00:00Z",
                "field_name": "status",
                "old_value": "To Do",
                "new_value": "Done",
            }
        ]

        snapshots = calculate_daily_sprint_snapshots(
            sprint_data,
            mock_issues[:2],
            changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        assert snapshots[0]["total_scope"] == 8
        assert snapshots[0]["completed_points"] == 0
        assert snapshots[1]["completed_points"] == 0
        assert snapshots[2]["completed_points"] == 5

        fig = create_sprint_burnup_chart(
            snapshots,
            sprint_name="Sprint Accuracy Test",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        completed_trace = next(
            t
            for t in fig["data"]
            if t["name"] == "Completed Points"  # type: ignore
        )

        assert completed_trace["y"][0] == 0  # type: ignore
        assert completed_trace["y"][1] == 0  # type: ignore
        assert completed_trace["y"][2] == 5  # type: ignore
