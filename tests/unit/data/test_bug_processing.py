from datetime import datetime

import pytest

from data.bug_processing import (
    calculate_bug_metrics_summary,
    filter_bug_issues,
    get_max_iso_week_for_year,
)
from tests.utils.mock_bug_data import generate_mock_bug_data


class TestISOWeekHelpers:
    def test_get_max_iso_week_for_year_52_weeks(self):
        assert get_max_iso_week_for_year(2024) == 52
        assert get_max_iso_week_for_year(2025) == 52
        assert get_max_iso_week_for_year(2023) == 52
        assert get_max_iso_week_for_year(2022) == 52

    def test_get_max_iso_week_for_year_53_weeks(self):

        assert get_max_iso_week_for_year(2015) == 53
        assert get_max_iso_week_for_year(2020) == 53
        assert get_max_iso_week_for_year(2026) == 53

    def test_get_max_iso_week_consistency(self):
        for year in range(2015, 2026):
            max_week = get_max_iso_week_for_year(year)
            assert max_week in [52, 53], (
                f"Year {year} should have 52 or 53 weeks, got {max_week}"
            )

            dec_28 = datetime(year, 12, 28)
            assert dec_28.isocalendar()[1] == max_week


class TestBugFiltering:
    def test_filter_bug_issues_basic(self):
        bugs = generate_mock_bug_data(num_weeks=2, seed=42)

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

        bug_type_mappings = {"Bug": "bug", "Defect": "bug", "Incident": "bug"}
        filtered_bugs = filter_bug_issues(all_issues, bug_type_mappings)

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

        assert len(filtered) == 2
        assert filtered[0]["key"] == "BUG-1"
        assert filtered[1]["key"] == "DEFECT-1"

    def test_filter_bug_issues_no_bugs(self):
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
        issues = [
            {
                "key": "BUG-1",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2024-12-01T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 5,
                },
            },
            {
                "key": "BUG-2",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-01-15T10:00:00.000+0000",
                    "resolutiondate": None,
                    "status": {"name": "Open"},
                    "customfield_10016": 3,
                },
            },
            {
                "key": "BUG-3",
                "fields": {
                    "issuetype": {"name": "Bug"},
                    "created": "2025-02-01T10:00:00.000+0000",
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
    def test_calculate_bug_metrics_summary(self):
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

        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, bug_issues, weekly_stats)

        assert summary["total_bugs"] == 4
        assert summary["open_bugs"] == 2
        assert summary["closed_bugs"] == 2
        assert summary["total_bugs"] == summary["open_bugs"] + summary["closed_bugs"]

    def test_bug_metrics_resolution_rate(self):
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
            for i in range(1, 11)
        ]

        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, bug_issues, weekly_stats)

        assert summary["total_bugs"] == 10
        assert summary["closed_bugs"] == 7
        assert summary["open_bugs"] == 3
        assert summary["resolution_rate"] == 0.7
        assert 0.0 <= summary["resolution_rate"] <= 1.0

    def test_bug_metrics_with_story_points(self):
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
                    "customfield_10016": None,
                },
            },
        ]

        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, bug_issues, weekly_stats)

        assert summary["total_bug_points"] == 13
        assert summary["open_bug_points"] == 8

    def test_bug_metrics_zero_bugs(self):
        bug_issues = []
        weekly_stats = []

        summary = calculate_bug_metrics_summary(bug_issues, bug_issues, weekly_stats)

        assert summary["total_bugs"] == 0
        assert summary["open_bugs"] == 0
        assert summary["closed_bugs"] == 0
        assert summary["resolution_rate"] == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
