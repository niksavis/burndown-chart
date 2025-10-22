"""Unit tests for bug data processing functions.

Tests bug filtering, statistics calculation, metrics aggregation, and forecasting.
"""

import pytest
from datetime import datetime, timedelta
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
