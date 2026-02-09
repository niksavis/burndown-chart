"""Unit tests for sprint charts sorting logic."""

from datetime import datetime, timezone, timedelta

from visualization.sprint_charts import (
    _calculate_issue_health_priority,
    _sort_issues_by_health_priority,
)


class TestCalculateIssueHealthPriority:
    """Test suite for _calculate_issue_health_priority function."""

    def test_completed_issue_returns_bucket_1_priority_5(self):
        """Completed issues should be in bucket 1 with priority 5."""
        issue_state = {"status": "Done"}
        flow_end_statuses = ["Done", "Closed"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, [], flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 1
        assert priority == 5
        assert (
            days_in_completed == 999999.0
        )  # Sentinel value for unknown completion date

    def test_blocked_issue_returns_bucket_0_priority_1(self):
        """Blocked issues (5+ days) should be in bucket 0 with priority 1."""
        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        issue_state = {"status": "In Progress"}
        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": seven_days_ago.isoformat(),
            }
        ]
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 1
        assert days_in_completed == 0.0  # Not completed

    def test_aging_issue_returns_bucket_0_priority_2(self):
        """Aging issues (3-4 days) should be in bucket 0 with priority 2."""
        now = datetime.now(timezone.utc)
        four_days_ago = now - timedelta(days=4)

        issue_state = {"status": "In Progress"}
        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": four_days_ago.isoformat(),
            }
        ]
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 2
        assert days_in_completed == 0.0  # Not completed

    def test_active_wip_returns_bucket_0_priority_3(self):
        """Active WIP (changed recently) should be in bucket 0 with priority 3."""
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        issue_state = {"status": "In Progress"}
        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": yesterday.isoformat(),
            }
        ]
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 3
        assert days_in_completed == 0.0  # Not completed

    def test_todo_issue_returns_bucket_0_priority_4(self):
        """To Do issues should be in bucket 0 with priority 4."""
        issue_state = {"status": "To Do"}
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, [], flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 4
        assert days_in_completed == 0.0  # Not completed

    def test_no_changelog_uses_created_date(self):
        """When no changelog exists, should fall back to created date."""
        now = datetime.now(timezone.utc)
        six_days_ago = now - timedelta(days=6)

        issue_state = {
            "status": "In Progress",
            "created": six_days_ago.isoformat(),
        }
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, [], flow_end_statuses, flow_wip_statuses
        )

        # Should be blocked since created 6 days ago
        assert bucket == 0
        assert priority == 1
        assert days_in_completed == 0.0  # Not completed

    def test_handles_z_suffix_in_timestamps(self):
        """Should handle timestamps with Z suffix."""
        now = datetime.now(timezone.utc)
        five_days_ago = now - timedelta(days=5)

        issue_state = {"status": "In Progress"}
        # Format timestamp with Z suffix (strip timezone info first)
        timestamp_str = five_days_ago.replace(tzinfo=None).isoformat() + "Z"
        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": timestamp_str,
            }
        ]
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 1  # Blocked at 5 days
        assert days_in_completed == 0.0  # Not completed

    def test_wip_status_without_changelog_treated_as_active(self):
        """WIP status without changelog should be treated as active WIP."""
        issue_state = {"status": "In Progress"}
        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        bucket, priority, days_in_completed = _calculate_issue_health_priority(
            "PROJ-1", issue_state, [], flow_end_statuses, flow_wip_statuses
        )

        assert bucket == 0
        assert priority == 3  # Active WIP (default for WIP without dates)
        assert days_in_completed == 0.0  # Not completed


class TestSortIssuesByHealthPriority:
    """Test suite for _sort_issues_by_health_priority function."""

    def test_blocked_sorts_before_aging(self):
        """Blocked issues should appear before aging issues."""
        now = datetime.now(timezone.utc)

        issue_states = {
            "PROJ-1": {"status": "In Progress"},
            "PROJ-2": {"status": "In Progress"},
        }

        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": (now - timedelta(days=6)).isoformat(),
            },
            {
                "issue_key": "PROJ-2",
                "change_date": (now - timedelta(days=3)).isoformat(),
            },
        ]

        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        sorted_keys = _sort_issues_by_health_priority(
            issue_states, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert sorted_keys == ["PROJ-1", "PROJ-2"]

    def test_aging_sorts_before_active_wip(self):
        """Aging issues should appear before active WIP."""
        now = datetime.now(timezone.utc)

        issue_states = {
            "PROJ-1": {"status": "In Progress"},
            "PROJ-2": {"status": "In Progress"},
        }

        changelog = [
            {
                "issue_key": "PROJ-1",
                "change_date": (now - timedelta(days=1)).isoformat(),
            },
            {
                "issue_key": "PROJ-2",
                "change_date": (now - timedelta(days=4)).isoformat(),
            },
        ]

        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        sorted_keys = _sort_issues_by_health_priority(
            issue_states, changelog, flow_end_statuses, flow_wip_statuses
        )

        assert sorted_keys == ["PROJ-2", "PROJ-1"]

    def test_completed_issues_sort_to_bottom(self):
        """Completed issues should appear at the bottom."""
        now = datetime.now(timezone.utc)

        issue_states = {
            "PROJ-1": {"status": "Done"},
            "PROJ-2": {"status": "In Progress"},
            "PROJ-3": {"status": "To Do"},
        }

        changelog = [
            {
                "issue_key": "PROJ-2",
                "change_date": (now - timedelta(days=1)).isoformat(),
            },
        ]

        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        sorted_keys = _sort_issues_by_health_priority(
            issue_states, changelog, flow_end_statuses, flow_wip_statuses
        )

        # PROJ-2 (active WIP) and PROJ-3 (To Do) should come before PROJ-1 (Done)
        assert sorted_keys[-1] == "PROJ-1"
        assert "PROJ-2" in sorted_keys[:2]
        assert "PROJ-3" in sorted_keys[:2]

    def test_tie_breaker_by_issue_key_descending(self):
        """When same priority, higher issue numbers should come first."""
        issue_states = {
            "PROJ-100": {"status": "To Do"},
            "PROJ-200": {"status": "To Do"},
            "PROJ-150": {"status": "To Do"},
        }

        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        sorted_keys = _sort_issues_by_health_priority(
            issue_states, [], flow_end_statuses, flow_wip_statuses
        )

        # All same priority (To Do), so should sort by key descending
        assert sorted_keys == ["PROJ-200", "PROJ-150", "PROJ-100"]

    def test_complete_sorting_scenario(self):
        """Test complete sorting with all priority levels."""
        now = datetime.now(timezone.utc)

        issue_states = {
            "PROJ-101": {"status": "Done"},
            "PROJ-102": {"status": "In Progress"},
            "PROJ-103": {"status": "In Progress"},
            "PROJ-104": {"status": "In Progress"},
            "PROJ-105": {"status": "To Do"},
            "PROJ-106": {"status": "Done"},
        }

        changelog = [
            {
                "issue_key": "PROJ-102",
                "change_date": (now - timedelta(days=6)).isoformat(),
            },
            {
                "issue_key": "PROJ-103",
                "change_date": (now - timedelta(days=4)).isoformat(),
            },
            {
                "issue_key": "PROJ-104",
                "change_date": (now - timedelta(hours=12)).isoformat(),
            },
        ]

        flow_end_statuses = ["Done"]
        flow_wip_statuses = ["In Progress"]

        sorted_keys = _sort_issues_by_health_priority(
            issue_states, changelog, flow_end_statuses, flow_wip_statuses
        )

        # Expected order:
        # 1. PROJ-102 (blocked - 6 days)
        # 2. PROJ-103 (aging - 4 days)
        # 3. PROJ-104 (active WIP - 12 hours)
        # 4. PROJ-105 (To Do)
        # 5. PROJ-106 (Done - higher key)
        # 6. PROJ-101 (Done - lower key)
        assert sorted_keys == [
            "PROJ-102",
            "PROJ-103",
            "PROJ-104",
            "PROJ-105",
            "PROJ-106",
            "PROJ-101",
        ]

    def test_empty_issue_states(self):
        """Should handle empty issue states gracefully."""
        sorted_keys = _sort_issues_by_health_priority({}, [], ["Done"], ["In Progress"])

        assert sorted_keys == []

    def test_none_flow_statuses_use_defaults(self):
        """Should use defaults when flow statuses are None."""
        issue_states = {
            "PROJ-1": {"status": "Done"},
            "PROJ-2": {"status": "To Do"},
        }

        sorted_keys = _sort_issues_by_health_priority(issue_states, [], None, None)

        # Should still sort with defaults
        assert "PROJ-2" in sorted_keys
        assert "PROJ-1" in sorted_keys
        assert sorted_keys.index("PROJ-2") < sorted_keys.index("PROJ-1")
