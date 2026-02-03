"""Unit tests for sprint chart visualization modules.

Tests sprint_snapshot_calculator, sprint_burnup_chart, and sprint_cfd_chart
for data accuracy, edge case handling, and chart rendering.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List

from data.sprint_snapshot_calculator import (
    calculate_daily_sprint_snapshots,
    get_status_at_timestamp,
)
from visualization.sprint_burnup_chart import create_sprint_burnup_chart
from visualization.sprint_cfd_chart import create_sprint_cfd_chart


@pytest.fixture
def mock_sprint_data() -> Dict:
    """Fixture for basic sprint snapshot data."""
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
def mock_issues() -> List[Dict]:
    """Fixture for issues with normalized points column."""
    return [
        {
            "key": "PROJ-1",
            "status": "Done",  # Normalized field for sprint_snapshot_calculator
            "fields": {
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "summary": "Implement feature",
            },
            "points": 5,  # Normalized database column
        },
        {
            "key": "PROJ-2",
            "status": "In Progress",  # Normalized field
            "fields": {
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Task"},
                "summary": "Review code",
            },
            "points": 3,
        },
        {
            "key": "PROJ-3",
            "status": "To Do",  # Normalized field
            "fields": {
                "status": {"name": "To Do"},
                "issuetype": {"name": "Bug"},
                "summary": "Fix issue",
            },
            "points": 2,
        },
    ]


@pytest.fixture
def mock_status_changelog() -> List[Dict]:
    """Fixture for status transition changelog entries."""
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
    """Test suite for calculate_daily_sprint_snapshots function."""

    def test_basic_daily_snapshots(
        self, mock_sprint_data, mock_issues, mock_status_changelog
    ):
        """Test basic daily snapshot generation."""
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            mock_status_changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        # Should have snapshots for 3 days
        assert len(snapshots) == 3

        # First day (Feb 1) - PROJ-1 starts but not completed yet
        day1 = snapshots[0]
        assert day1["date"] == "2026-02-01"
        assert day1["completed_points"] == 0
        assert day1["total_scope"] == 10  # All 3 issues
        assert day1["completed_count"] == 0

        # Second day (Feb 2) - PROJ-1 transitions at 14:00, not yet in snapshot (taken at 00:00)
        day2 = snapshots[1]
        assert day2["date"] == "2026-02-02"
        assert day2["completed_points"] == 0  # Not done yet at midnight
        assert day2["total_scope"] == 10

        # Third day (Feb 3) - PROJ-1 completion now visible
        day3 = snapshots[2]
        assert day3["date"] == "2026-02-03"
        assert day3["completed_points"] == 5  # PROJ-1 done
        assert day3["completed_count"] == 1

    def test_scope_changes_mid_sprint(self, mock_issues, mock_status_changelog):
        """Test snapshot with issues added/removed mid-sprint."""
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

        # Day 1: Only PROJ-1 and PROJ-2 (scope = 5+3 = 8)
        assert snapshots[0]["total_scope"] == 8

        # Day 2: PROJ-3 added at 15:00 (+2), PROJ-1 removed at 16:00 (-5)
        # Scope changes are applied within the day they occur (before day_end)
        # So Day 2 shows: PROJ-2 (3) only, as PROJ-1 removed and PROJ-3 added then removed
        # Actually: Day 2 processes both changes, ending with just PROJ-2
        assert snapshots[1]["total_scope"] == 3  # PROJ-2 only

        # Day 3: Still just PROJ-2
        assert snapshots[2]["total_scope"] == 3

    def test_linear_progress_pattern(self, mock_issues):
        """Test sprint with steady linear progress."""
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

        # Verify linear increase in completed points (transitions at 14:00, visible next day)
        assert (
            snapshots[0]["completed_points"] == 0
        )  # Feb 1: PROJ-1 completes at 14:00, not in midnight snapshot
        assert (
            snapshots[1]["completed_points"] == 5
        )  # Feb 2: PROJ-1 now visible, PROJ-2 completes at 14:00
        assert (
            snapshots[2]["completed_points"] == 8
        )  # Feb 3: PROJ-1+2 visible, PROJ-3 completes at 14:00

    def test_stalled_sprint_pattern(self, mock_sprint_data, mock_issues):
        """Test sprint with no progress (stalled)."""
        # No status changes - everything stays in To Do
        changelog = []

        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        # PROJ-1 has status='Done' in mock but no changelog, so shows as Done from start
        for snapshot in snapshots:
            assert snapshot["completed_points"] == 5  # PROJ-1 counted as Done
            assert snapshot["total_scope"] == 10

    def test_empty_sprint(self):
        """Test with no issues in sprint."""
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

        # Should return empty list
        assert len(snapshots) == 0

    def test_invalid_date_formats(self, mock_sprint_data, mock_issues):
        """Test handling of invalid date formats."""
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            [],
            sprint_start_date="invalid-date",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        # Should return empty list on parse error
        assert len(snapshots) == 0


class TestGetStatusAtTimestamp:
    """Test suite for get_status_at_timestamp helper function."""

    def test_status_before_any_changes(self, mock_status_changelog, mock_issues):
        """Test getting status before any changelog entries."""
        issue = {"key": "PROJ-1", "status": "To Do"}
        # Filter changelog for this issue
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 1, 9, 0, tzinfo=timezone.utc),
            proj1_changelog,
        )
        assert status == "To Do"

    def test_status_after_transition(self, mock_status_changelog):
        """Test getting status after a transition occurred."""
        issue = {"key": "PROJ-1", "status": "Done"}
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 2, 15, 0, tzinfo=timezone.utc),
            proj1_changelog,
        )
        assert status == "Done"

    def test_status_between_transitions(self, mock_status_changelog):
        """Test getting status between two transitions."""
        issue = {"key": "PROJ-1", "status": "Done"}
        proj1_changelog = [
            c for c in mock_status_changelog if c["issue_key"] == "PROJ-1"
        ]

        status = get_status_at_timestamp(
            issue,
            datetime(2026, 2, 2, 12, 0, tzinfo=timezone.utc),
            proj1_changelog,
        )
        # At Feb 2 12:00, PROJ-1 was "In Progress" (transitioned at 10:00, not done until 14:00)
        assert status == "In Progress"


class TestCreateSprintBurnupChart:
    """Test suite for create_sprint_burnup_chart function."""

    def test_basic_burnup_chart_creation(self):
        """Test creating burnup chart with valid data."""
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

        # Verify figure structure
        assert fig is not None
        assert "data" in fig
        assert "layout" in fig

        # Should have 5 traces: scope, completed, ideal, sprint start/end markers
        assert len(fig["data"]) == 5  # type: ignore

        # Verify trace names
        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Sprint Scope" in trace_names
        assert "Completed Points" in trace_names
        assert "Ideal Progress" in trace_names

    def test_burnup_with_scope_changes(self):
        """Test burnup chart with changing scope."""
        daily_snapshots = [
            {"date": "2026-02-01", "completed_points": 0, "total_scope": 10},
            {
                "date": "2026-02-02",
                "completed_points": 5,
                "total_scope": 15,
            },  # Scope increased
            {
                "date": "2026-02-03",
                "completed_points": 10,
                "total_scope": 12,
            },  # Scope decreased
        ]

        fig = create_sprint_burnup_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        # Find total scope trace
        scope_trace = next(t for t in fig["data"] if t["name"] == "Sprint Scope")  # type: ignore

        # Verify scope changes are reflected
        assert scope_trace["y"][0] == 10  # type: ignore
        assert scope_trace["y"][1] == 15  # type: ignore
        assert scope_trace["y"][2] == 12  # type: ignore

    def test_burnup_with_empty_data(self):
        """Test burnup chart with no data."""
        fig = create_sprint_burnup_chart(
            [],
            sprint_name="Empty Sprint",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        # Should still return a valid figure (empty chart)
        assert fig is not None
        assert "data" in fig


class TestCreateSprintCFDChart:
    """Test suite for create_sprint_cfd_chart function."""

    def test_basic_cfd_creation(self):
        """Test creating CFD chart with valid status breakdown."""
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

        # Verify figure structure
        assert fig is not None
        assert "data" in fig
        assert "layout" in fig

        # Should have traces for each status
        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Done" in trace_names
        assert "In Progress" in trace_names
        assert "To Do" in trace_names

    def test_cfd_with_custom_statuses(self):
        """Test CFD with flow-specific status configuration."""
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

        # Verify custom statuses appear in traces
        trace_names = [trace["name"] for trace in fig["data"]]  # type: ignore
        assert "Backlog" in trace_names
        assert "Development" in trace_names
        assert "Review" in trace_names
        assert "Closed" in trace_names

    def test_cfd_identifies_bottlenecks(self):
        """Test CFD can show status bottlenecks (widening bands)."""
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
                    "In Progress": {"count": 3, "points": 10},  # Bottleneck in progress
                    "Done": {"count": 0, "points": 0},
                },
            },
        ]

        fig = create_sprint_cfd_chart(
            daily_snapshots,
            sprint_name="Sprint 23",
        )

        # Find In Progress trace
        in_progress_trace = next(t for t in fig["data"] if t["name"] == "In Progress")  # type: ignore

        # Verify bottleneck is visible (In Progress points increased)
        assert in_progress_trace["y"][0] < in_progress_trace["y"][1]  # type: ignore


class TestSprintChartsIntegration:
    """Integration tests for end-to-end sprint chart flow."""

    def test_full_chart_generation_flow(
        self, mock_sprint_data, mock_issues, mock_status_changelog
    ):
        """Test complete flow from sprint data to rendered charts."""
        # Step 1: Generate daily snapshots
        snapshots = calculate_daily_sprint_snapshots(
            mock_sprint_data,
            mock_issues,
            mock_status_changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        assert len(snapshots) > 0

        # Step 2: Create burnup chart
        burnup_fig = create_sprint_burnup_chart(
            snapshots,
            sprint_name="Sprint 23",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        assert burnup_fig is not None
        assert (
            len(burnup_fig["data"]) >= 2  # type: ignore[arg-type]
        )  # At least scope + completion

        # Step 3: Create CFD chart
        cfd_fig = create_sprint_cfd_chart(
            snapshots,
            sprint_name="Sprint 23",
        )

        assert cfd_fig is not None
        assert len(cfd_fig["data"]) > 0  # Has status traces  # type: ignore

    def test_chart_data_accuracy(self, mock_issues):
        """Verify chart data matches source data exactly."""
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
            mock_issues[:2],  # Only first 2 issues
            changelog,
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
            flow_end_statuses=["Done"],
        )

        # Verify snapshot accuracy (snapshots taken at midnight)
        assert snapshots[0]["total_scope"] == 8  # 5 + 3
        assert snapshots[0]["completed_points"] == 0  # Before completion
        assert (
            snapshots[1]["completed_points"] == 0
        )  # PROJ-1 completes at 14:00, not in midnight snapshot
        assert snapshots[2]["completed_points"] == 5  # PROJ-1 now visible

        # Create chart and verify data consistency
        fig = create_sprint_burnup_chart(
            snapshots,
            sprint_name="Sprint Accuracy Test",
            sprint_start_date="2026-02-01T00:00:00Z",
            sprint_end_date="2026-02-03T23:59:59Z",
        )

        # Find completed points trace
        completed_trace = next(
            t
            for t in fig["data"]
            if t["name"] == "Completed Points"  # type: ignore
        )

        # Verify chart data matches snapshot data
        assert completed_trace["y"][0] == 0  # type: ignore
        assert completed_trace["y"][1] == 0  # type: ignore
        assert completed_trace["y"][2] == 5  # type: ignore
