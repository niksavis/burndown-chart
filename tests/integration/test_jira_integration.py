"""
Integration Tests for JIRA Scope Calculation

Test the full workflow from JIRA API to scope calculation and persistence.
"""

import pytest
from unittest.mock import patch, MagicMock
import json

from data.jira_simple import sync_jira_scope_and_data
from data.persistence import update_project_scope_from_jira, load_unified_project_data


class TestJiraIntegration:
    """Integration tests for JIRA scope calculation workflow."""

    @patch("data.jira_simple.fetch_jira_issues")
    @patch("data.jira_simple.get_jira_config")
    def test_full_jira_scope_workflow(self, mock_get_config, mock_fetch_issues):
        """Test complete workflow from JIRA fetch to scope persistence."""

        # Mock JIRA configuration
        mock_config = {
            "jql_query": "project = TEST",
            "base_url": "https://test-jira.com",
            "token": "test-token",
            "story_points_field": "votes",
            "cache_max_size_mb": 50,
        }
        mock_get_config.return_value = mock_config

        # Mock JIRA API response
        mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": {"votes": 8},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": "2023-01-10T00:00:00.000+0000",
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {"key": "indeterminate"},
                    },
                    "votes": {"votes": 5},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": None,
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "votes": {"votes": 3},
                    "created": "2023-01-01T00:00:00.000+0000",
                    "resolutiondate": None,
                },
            },
        ]
        mock_fetch_issues.return_value = (True, mock_issues)

        # Execute the full workflow
        success, message, scope_data = sync_jira_scope_and_data()

        # Verify success
        assert success is True
        assert "scope calculation" in message.lower()

        # Verify scope data
        assert scope_data["total_items"] == 3
        assert scope_data["total_points"] == 16  # 8 + 5 + 3
        assert scope_data["completed_items"] == 1
        assert scope_data["completed_points"] == 8
        assert scope_data["remaining_items"] == 2
        assert scope_data["remaining_points"] == 8  # 5 + 3

        # Verify status breakdown
        assert len(scope_data["status_breakdown"]) == 3
        assert "Done" in scope_data["status_breakdown"]
        assert "In Progress" in scope_data["status_breakdown"]
        assert "To Do" in scope_data["status_breakdown"]

    @patch("data.jira_simple.sync_jira_scope_and_data")
    def test_project_scope_persistence(self, mock_sync):
        """Test that JIRA scope data is properly persisted."""

        # Mock successful JIRA scope sync
        mock_scope_data = {
            "total_items": 10,
            "total_points": 50,
            "completed_items": 3,
            "completed_points": 15,
            "remaining_items": 7,
            "remaining_points": 35,
            "status_breakdown": {
                "Done": {"items": 3, "points": 15, "classification": "COMPLETED"},
                "In Progress": {
                    "items": 4,
                    "points": 20,
                    "classification": "IN_PROGRESS",
                },
                "To Do": {"items": 3, "points": 15, "classification": "TODO"},
            },
        }
        mock_sync.return_value = (True, "Success", mock_scope_data)

        # Test persistence update
        success, message = update_project_scope_from_jira()

        assert success is True
        assert "JIRA" in message

        # Verify data was persisted (this would require reading the actual file)
        # In a real test, you'd verify the JSON file was updated correctly


class TestJiraApiMocking:
    """Test with various JIRA API response scenarios."""

    def test_jira_api_failure_handling(self):
        """Test graceful handling of JIRA API failures."""
        with patch("data.jira_simple.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (False, [])

            success, message, scope_data = sync_jira_scope_and_data()

            assert success is False
            assert "Failed to fetch JIRA data" in message
            assert scope_data == {}

    def test_empty_jira_response(self):
        """Test handling of empty JIRA response."""
        with patch("data.jira_simple.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, [])  # Empty issues list

            success, message, scope_data = sync_jira_scope_and_data()

            # Should succeed but with zero values
            assert success is True
            assert scope_data["total_items"] == 0
            assert scope_data["total_points"] == 0

    @patch("data.jira_simple.fetch_jira_issues")
    @patch("data.jira_simple.get_jira_config")
    def test_empty_points_field_integration(self, mock_get_config, mock_fetch_issues):
        """Test integration workflow with empty points field configuration."""

        # Mock configuration with empty points field
        mock_config = {
            "jql_query": "project = TEST",
            "base_url": "https://test-jira.com",
            "token": "test-token",
            "story_points_field": "",  # Empty points field
            "cache_max_size_mb": 50,
        }
        mock_get_config.return_value = mock_config

        # Mock JIRA issues with point values that should be ignored
        mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 8,  # Should be ignored
                    "votes": {"votes": 2},  # Should be ignored
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": 5,  # Should be ignored
                },
            },
        ]
        mock_fetch_issues.return_value = (True, mock_issues)

        # Execute the sync workflow
        success, message, scope_data = sync_jira_scope_and_data()

        # Verify success
        assert success is True
        assert message  # Just check that there's a success message

        # Verify that points field being empty results in zero points
        assert scope_data["points_field_available"] is False
        assert scope_data["total_points"] == 0
        assert scope_data["completed_points"] == 0
        assert scope_data["remaining_points"] == 0
        assert scope_data["estimated_points"] == 0
        assert scope_data["remaining_total_points"] == 0.0

        # Items should still be counted correctly
        assert scope_data["total_items"] == 2
        assert scope_data["completed_items"] == 1  # TEST-1 is Done
        assert scope_data["remaining_items"] == 1  # TEST-2 is To Do
        assert scope_data["estimated_items"] == 1  # Fallback: remaining items


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
