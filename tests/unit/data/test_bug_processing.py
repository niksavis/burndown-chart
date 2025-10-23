"""Unit tests for bug data processing functions.

Tests bug filtering, statistics calculation, metrics aggregation, and forecasting.
"""

import pytest
from datetime import datetime
from data.bug_processing import (
    filter_bug_issues,
    calculate_bug_metrics_summary,
)
from tests.utils.mock_bug_data import generate_mock_bug_data


class TestBugFiltering:
    """Test suite for filter_bug_issues function."""

    def test_filter_bug_issues_basic(self):
        """Test basic bug filtering with default mappings."""
        # Generate mock data with bugs and other issue types
        bugs = generate_mock_bug_data(num_weeks=2, seed=42)

        # Add some non-bug issues
        non_bugs = [
            {
                "key": "STORY-1",
                "fields": {
                    "issuetype": {"name": "Story"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "In Progress"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": "2025-01-05T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 3,
                },
            },
        ]

        all_issues = bugs + non_bugs

        # Filter for bugs only
        bug_type_mappings = {"Bug": "bug", "Defect": "bug", "Incident": "bug"}
        filtered_bugs = filter_bug_issues(all_issues, bug_type_mappings)

        # Verify only bugs returned
        assert len(filtered_bugs) == len(bugs)
        assert all(
            issue["fields"]["issuetype"]["name"] in bug_type_mappings
            for issue in filtered_bugs
        )
        assert not any(
            issue["fields"]["issuetype"]["name"] in ["Story", "Task"]
            for issue in filtered_bugs
        )

    def test_filter_bug_issues_mixed_types(self):
        """Test filtering bugs from mixed issue types (T014)."""
        issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "STORY-1",
                "fields": {
                    "issuetype": {"name": "Story"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 8,
                },
            },
            {
                "key": "DEFECT-1",
                "fields": {
                    "issuetype": {"name": "Defect"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": "2025-01-05T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "created": "2025-01-03T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "To Do"},
                    "customfield_10016": 2,
                },
            },
        ]

        bug_type_mappings = {"Bug": "bug", "Defect": "bug"}
        filtered = filter_bug_issues(issues, bug_type_mappings)

        assert len(filtered) == 2  # BUG-1 and DEFECT-1
        assert filtered[0]["key"] == "BUG-1"
        assert filtered[1]["key"] == "DEFECT-1"

    def test_filter_bug_issues_no_bugs(self):
        """Test empty result when no bugs exist (T015)."""
        issues = [
            {
                "key": "STORY-1",
                "fields": {
                    "issuetype": {"name": "Story"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "TASK-1",
                "fields": {
                    "issuetype": {"name": "Task"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 3,
                },
            },
        ]

        bug_type_mappings = {"Bug": "bug", "Defect": "bug"}
        filtered = filter_bug_issues(issues, bug_type_mappings)

        assert len(filtered) == 0
        assert filtered == []

    def test_filter_bug_issues_custom_mappings(self):
        """Test custom type mappings (Defect, Incident) (T016)."""
        issues = [
            {
                "key": "INCIDENT-1",
                "fields": {
                    "issuetype": {"name": "Incident"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "DEFECT-1",
                "fields": {
                    "issuetype": {"name": "Defect"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": "2025-01-10T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "CRITICAL-BUG-1",
                "fields": {
                    "issuetype": {"name": "Critical Bug"},
                    "created": "2025-01-03T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "In Progress"},
                    "customfield_10016": 8,
                },
            },
        ]

        # Custom mappings for organization that uses different names
        bug_type_mappings = {
            "Incident": "bug",
            "Defect": "bug",
            "Critical Bug": "bug",
        }
        filtered = filter_bug_issues(issues, bug_type_mappings)

        assert len(filtered) == 3
        assert all(
            issue["key"] in ["INCIDENT-1", "DEFECT-1", "CRITICAL-BUG-1"]
            for issue in filtered
        )

    def test_filter_bug_issues_with_date_range(self):
        """Test filtering bugs within date range."""
        issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2024-12-01T10:00:00.000+0000",  # Outside range
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-15T10:00:00.000+0000",  # Inside range
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-02-01T10:00:00.000+0000",  # Outside range
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 2,
                },
            },
        ]

        bug_type_mappings = {"Bug": "bug"}
        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        filtered = filter_bug_issues(issues, bug_type_mappings, date_from, date_to)

        assert len(filtered) == 1
        assert filtered[0]["key"] == "BUG-2"


class TestBugMetricsSummary:
    """Test suite for calculate_bug_metrics_summary function."""

    def test_calculate_bug_metrics_summary(self):
        """Test total/open/closed bug calculation (T017)."""
        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": "2025-01-05T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "issuetype": {"name": "Defect"},
                    "created": "2025-01-03T10:00:00.000+0000",
                    "resolutiondate": "2025-01-10T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 8,
                },
            },
            {
                "key": "BUG-4",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-04T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "In Progress"},
                    "customfield_10016": 2,
                },
            },
        ]

        weekly_stats = []  # Not needed for basic summary

        summary = calculate_bug_metrics_summary(bug_issues, weekly_stats)

        assert summary["total_bugs"] == 4
        assert summary["open_bugs"] == 2  # BUG-2 and BUG-4
        assert summary["closed_bugs"] == 2  # BUG-1 and BUG-3
        assert summary["total_bugs"] == summary["open_bugs"] + summary["closed_bugs"]

    def test_bug_metrics_resolution_rate(self):
        """Test resolution rate percentage calculation (T018)."""
        bug_issues = [
            {
                "key": f"BUG-{i}",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": f"2025-01-{i:02d}T10:00:00.000+0000",
                    "resolutiondate": f"2025-01-{i + 5:02d}T10:00:00.000+0000"
                    if i <= 7
                    else None,
                    "status": {"name": "Done" if i <= 7 else "Open"},
                    "customfield_10016": 5,
                },
            }
            for i in range(1, 11)  # 10 bugs total
        ]

        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, weekly_stats)

        assert summary["total_bugs"] == 10
        assert summary["closed_bugs"] == 7
        assert summary["open_bugs"] == 3
        assert summary["resolution_rate"] == 0.7  # 70% resolved
        assert 0.0 <= summary["resolution_rate"] <= 1.0

    def test_bug_metrics_with_story_points(self):
        """Test metrics calculation includes story points."""
        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-01T10:00:00.000+0000",
                    "resolutiondate": "2025-01-05T10:00:00.000+0000",
                    "status": {"name": "Done"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-02T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 8,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-03T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": None,  # No points
                },
            },
        ]

        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, weekly_stats)

        assert summary["total_bug_points"] == 13  # 5 + 8 + 0
        assert summary["open_bug_points"] == 8  # Only BUG-2 has points and is open

    def test_bug_metrics_zero_bugs(self):
        """Test metrics with no bugs."""
        bug_issues = []
        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, weekly_stats)

        assert summary["total_bugs"] == 0
        assert summary["open_bugs"] == 0
        assert summary["closed_bugs"] == 0
        assert summary["resolution_rate"] == 0.0


class TestBugStatistics:
    """Test suite for calculate_bug_statistics function (Phase 4)."""

    def test_calculate_bug_statistics_weekly_bins(self):
        """Test weekly binning of bug creation and resolution (T028)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        # Create bugs across multiple weeks
        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",  # Week 2
                    "resolutiondate": "2025-01-13T10:00:00.000+0000",  # Week 3
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,  # Open
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",  # Week 3
                    "resolutiondate": "2025-01-20T10:00:00.000+0000",  # Week 4
                    "customfield_10016": None,  # No points
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Verify we have stats for all 5 weeks in January 2025
        assert len(stats) == 5

        # Verify Week 2 stats (2 bugs created, 0 resolved)
        week2 = next((s for s in stats if s["week"] == "2025-W02"), None)
        assert week2 is not None
        assert week2["bugs_created"] == 2
        assert week2["bugs_resolved"] == 0
        assert week2["bugs_points_created"] == 8  # 3 + 5
        assert week2["bugs_points_resolved"] == 0

        # Verify Week 3 stats (1 bug created, 1 resolved)
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["bugs_created"] == 1
        assert week3["bugs_resolved"] == 1
        assert week3["bugs_points_created"] == 0  # BUG-3 has no points
        assert week3["bugs_points_resolved"] == 3  # BUG-1

    def test_bug_statistics_iso_week_assignment(self):
        """Test ISO week assignment logic (T029)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        # Create bug on Sunday (end of week) and Monday (start of week)
        bug_issues = [
            {
                "key": "BUG-SUNDAY",
                "fields": {
                    "created": "2025-01-12T23:59:59.000+0000",  # Sunday of Week 2
                    "resolutiondate": None,
                    "customfield_10016": 1,
                },
            },
            {
                "key": "BUG-MONDAY",
                "fields": {
                    "created": "2025-01-13T00:00:00.000+0000",  # Monday of Week 3
                    "resolutiondate": None,
                    "customfield_10016": 1,
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Verify Sunday bug is in Week 2
        week2 = next((s for s in stats if s["week"] == "2025-W02"), None)
        assert week2 is not None
        assert week2["bugs_created"] == 1  # BUG-SUNDAY

        # Verify Monday bug is in Week 3
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["bugs_created"] == 1  # BUG-MONDAY

    def test_bug_statistics_cumulative_open(self):
        """Test cumulative open bugs running total (T030)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,  # Open
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,  # Open
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",  # Week 3
                    "resolutiondate": "2025-01-20T10:00:00.000+0000",  # Week 4
                    "customfield_10016": 2,
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Week 1: 0 bugs created, cumulative = 0
        week1 = next((s for s in stats if s["week"] == "2025-W01"), None)
        assert week1 is not None
        assert week1["cumulative_open_bugs"] == 0

        # Week 2: 2 bugs created, 0 resolved, cumulative = 2
        week2 = next((s for s in stats if s["week"] == "2025-W02"), None)
        assert week2 is not None
        assert week2["net_bugs"] == 2
        assert week2["cumulative_open_bugs"] == 2

        # Week 3: 1 bug created, 0 resolved, cumulative = 3
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["net_bugs"] == 1
        assert week3["cumulative_open_bugs"] == 3

        # Week 4: 0 bugs created, 1 resolved, cumulative = 2
        week4 = next((s for s in stats if s["week"] == "2025-W04"), None)
        assert week4 is not None
        assert week4["net_bugs"] == -1
        assert week4["cumulative_open_bugs"] == 2

    def test_bug_statistics_empty_weeks(self):
        """Test weeks with zero bug activity (T031)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        # Create bugs only in Week 2 and Week 4
        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-22T10:00:00.000+0000",  # Week 4
                    "resolutiondate": None,
                    "customfield_10016": 5,
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Verify all 5 weeks are included even if empty
        assert len(stats) == 5

        # Verify Week 1 has zero activity but is still present
        week1 = next((s for s in stats if s["week"] == "2025-W01"), None)
        assert week1 is not None
        assert week1["bugs_created"] == 0
        assert week1["bugs_resolved"] == 0
        assert week1["net_bugs"] == 0

        # Verify Week 3 has zero activity but is still present
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["bugs_created"] == 0
        assert week3["bugs_resolved"] == 0
        assert week3["net_bugs"] == 0


class TestBugStatisticsWithStoryPoints:
    """Test suite for bug statistics with story points (User Story 3)."""

    def test_bug_statistics_with_story_points(self):
        """Test story points aggregation in weekly statistics (T043)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",  # Week 2
                    "resolutiondate": "2025-01-13T10:00:00.000+0000",  # Week 3
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,  # Open
                    "customfield_10016": 8,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",  # Week 3
                    "resolutiondate": "2025-01-20T10:00:00.000+0000",  # Week 4
                    "customfield_10016": 3,
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Verify Week 2 story points (2 bugs created with 5 + 8 = 13 points)
        week2 = next((s for s in stats if s["week"] == "2025-W02"), None)
        assert week2 is not None
        assert week2["bugs_points_created"] == 13
        assert week2["bugs_points_resolved"] == 0
        assert week2["net_points"] == 13

        # Verify Week 3 story points (1 bug created with 3 points, 1 resolved with 5 points)
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["bugs_points_created"] == 3
        assert week3["bugs_points_resolved"] == 5
        assert week3["net_points"] == -2

        # Verify Week 4 story points (0 created, 1 resolved with 3 points)
        week4 = next((s for s in stats if s["week"] == "2025-W04"), None)
        assert week4 is not None
        assert week4["bugs_points_created"] == 0
        assert week4["bugs_points_resolved"] == 3
        assert week4["net_points"] == -3

    def test_bug_statistics_null_story_points(self):
        """Test handling of null/missing story points (T044)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",  # Week 2
                    "resolutiondate": "2025-01-13T10:00:00.000+0000",  # Week 3
                    "customfield_10016": None,  # Null points
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",  # Week 2
                    "resolutiondate": None,
                    # Missing customfield_10016 entirely
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",  # Week 3
                    "resolutiondate": "2025-01-20T10:00:00.000+0000",  # Week 4
                    "customfield_10016": 5,  # Has points
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Verify Week 2: 2 bugs created but 0 points (both have null/missing)
        week2 = next((s for s in stats if s["week"] == "2025-W02"), None)
        assert week2 is not None
        assert week2["bugs_created"] == 2  # Items always counted
        assert week2["bugs_points_created"] == 0  # Null treated as 0

        # Verify Week 3: 1 bug created with 5 points, 1 resolved with 0 points
        week3 = next((s for s in stats if s["week"] == "2025-W03"), None)
        assert week3 is not None
        assert week3["bugs_created"] == 1
        assert week3["bugs_points_created"] == 5
        assert week3["bugs_resolved"] == 1  # BUG-1
        assert week3["bugs_points_resolved"] == 0  # BUG-1 had null points

    def test_bug_investment_calculation(self):
        """Test bug investment points aggregation (T045)."""
        from datetime import datetime
        from data.bug_processing import calculate_bug_statistics

        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",
                    "resolutiondate": None,
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",
                    "resolutiondate": "2025-01-15T10:00:00.000+0000",
                    "customfield_10016": 8,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",
                    "resolutiondate": "2025-01-22T10:00:00.000+0000",
                    "customfield_10016": 13,
                },
            },
        ]

        date_from = datetime(2025, 1, 1)
        date_to = datetime(2025, 1, 31)

        stats = calculate_bug_statistics(bug_issues, date_from, date_to)

        # Calculate total points invested (created)
        total_points_created = sum(s["bugs_points_created"] for s in stats)
        assert total_points_created == 26  # 5 + 8 + 13

        # Calculate total points resolved
        total_points_resolved = sum(s["bugs_points_resolved"] for s in stats)
        assert total_points_resolved == 21  # 8 + 13

        # Verify net points calculation across all weeks
        total_net_points = sum(s["net_points"] for s in stats)
        assert total_net_points == 5  # 26 - 21 (BUG-1 still open with 5 points)

    def test_capacity_percentage_calculation(self):
        """Test bug capacity consumption metric (T046)."""
        from data.bug_processing import calculate_bug_metrics_summary

        # Create bug issues with story points
        bug_issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "created": "2025-01-06T10:00:00.000+0000",
                    "resolutiondate": None,  # Open
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "created": "2025-01-08T10:00:00.000+0000",
                    "resolutiondate": "2025-01-15T10:00:00.000+0000",  # Closed
                    "customfield_10016": 8,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "created": "2025-01-15T10:00:00.000+0000",
                    "resolutiondate": None,  # Open
                    "customfield_10016": 3,
                },
            },
        ]

        weekly_stats = []  # Not used for this test

        summary = calculate_bug_metrics_summary(bug_issues, weekly_stats)

        # Verify total bug points
        assert summary["total_bug_points"] == 16  # 5 + 8 + 3

        # Verify open bug points
        assert summary["open_bug_points"] == 8  # 5 + 3 (only open bugs)

        # Note: capacity_consumed_by_bugs requires total project points
        # which would be calculated externally and divided into this metric


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
