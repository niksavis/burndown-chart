"""
Unit Tests for JIRA Scope Calculator

Test the core JIRA scope calculation functionality with various scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from data.jira_scope_calculator import calculate_jira_project_scope


class TestJiraProjectScopeCalculation:
    """Test cases for JIRA project scope calculation."""

    def test_basic_scope_calculation_with_votes(self):
        """Test basic scope calculation using votes field."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": {"votes": 5},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": "2023-01-05T00:00:00.000+0000",
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {"key": "indeterminate"},
                    },
                    "votes": {"votes": 8},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": None,
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "votes": {"votes": 3},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": None,
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "votes")

        # Verify totals
        assert result["total_items"] == 3
        assert result["total_points"] == 16  # 5 + 8 + 3

        # Verify completed
        assert result["completed_items"] == 1
        assert result["completed_points"] == 5

        # Verify remaining
        assert result["remaining_items"] == 2
        assert result["remaining_points"] == 11  # 8 + 3

        # Verify status breakdown
        assert "Done" in result["status_breakdown"]
        assert result["status_breakdown"]["Done"]["items"] == 1
        assert result["status_breakdown"]["Done"]["points"] == 5

    def test_no_story_points_calculation(self):
        """Test calculation when no story points are available."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": None,  # No points - no fake data created
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "votes": None,  # No points - no fake data created
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "votes")

        assert result["total_items"] == 2
        assert result["total_points"] == 0  # No story points exist
        assert result["completed_items"] == 1
        assert result["completed_points"] == 0  # No story points
        assert result["remaining_items"] == 1
        assert result["remaining_points"] == 0  # No story points
        assert result["points_field_available"] is False  # Field has no data

    def test_custom_status_configuration(self):
        """Test scope calculation with custom status mapping."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {
                        "name": "Deployed",
                        "statusCategory": {"key": "new"},  # Would normally be TODO
                    },
                    "votes": {"votes": 10},
                },
            }
        ]

        # Custom config that overrides status category
        status_config = {
            "method": "status_names",
            "completed_statuses": ["Deployed"],
            "in_progress_statuses": [],
            "todo_statuses": [],
        }

        result = calculate_jira_project_scope(issues, "votes", status_config)

        # Should be completed despite "new" category, because of custom config
        assert result["completed_items"] == 1
        assert result["completed_points"] == 10
        assert result["remaining_items"] == 0
        assert result["remaining_points"] == 0

    def test_mixed_story_points_fields(self):
        """Test handling of different story points field formats."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 15.0,  # Standard story points field
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": "8",  # String format
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": {"value": 5},  # Complex object
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "customfield_10002")

        assert result["total_items"] == 3
        assert result["completed_items"] == 3
        # Should handle all formats: 15.0 + 8 + 5 = 28
        assert result["completed_points"] == 28

    def test_empty_issues_list(self):
        """Test handling of empty issues list."""
        result = calculate_jira_project_scope([], "votes")

        assert result["total_items"] == 0
        assert result["total_points"] == 0
        assert result["completed_items"] == 0
        assert result["completed_points"] == 0
        assert result["remaining_items"] == 0
        assert result["remaining_points"] == 0
        assert result["status_breakdown"] == {}

    def test_malformed_issue_handling(self):
        """Test graceful handling of malformed issue data."""
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": {"votes": 5},
                },
            },
            {
                "key": "PROJ-2",
                # Missing status information - should be skipped
                "fields": {
                    "votes": {"votes": 3},
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {"key": "indeterminate"},
                    },
                    "votes": {"votes": 7},
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "votes")

        # Should process 2 valid issues and skip the malformed one
        assert result["total_items"] == 2  # Only valid issues counted
        assert result["total_points"] == 12  # 5 + 7
        assert result["completed_items"] == 1
        assert result["remaining_items"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
