"""
Integration tests for JIRA scope calculation workflows.
Tests the complete flow from UI buttons to data persistence.
"""

import unittest
from unittest.mock import patch
import json
import tempfile
import os


class TestJiraScopeWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete JIRA scope calculation workflows."""

    def setUp(self):
        """Set up test environment with temporary cache file."""
        # Create a temporary directory for cache files
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "jira_cache.json")

        # Mock JIRA issues for testing
        self.mock_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "created": "2025-01-01T10:00:00.000Z",
                    "resolutiondate": "2025-01-02T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {"key": "indeterminate"},
                    },
                    "created": "2025-01-01T10:00:00.000Z",
                    "resolutiondate": None,
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "created": "2025-01-01T10:00:00.000Z",
                    "resolutiondate": None,
                },
            },
        ]

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.cache_file):
            os.unlink(self.cache_file)
        os.rmdir(self.temp_dir)

    @patch("data.jira_simple.fetch_jira_issues")
    @patch("data.jira_simple.JIRA_CACHE_FILE", new_callable=lambda: None)
    def test_update_data_with_empty_points_field(
        self, mock_cache_file_constant, mock_fetch
    ):
        """Test 'Update Data' button workflow with empty points field."""
        # Patch the cache file constant to use our temp file
        with patch("data.jira_simple.JIRA_CACHE_FILE", self.cache_file):
            mock_fetch.return_value = (True, self.mock_issues)

        from data.jira_simple import sync_jira_data

        # Simulate clicking 'Update Data' with empty points field
        success, message = sync_jira_data("project = TEST")

        self.assertTrue(success, f"Update Data should succeed: {message}")

        # Verify cache was created correctly without votes field
        self.assertTrue(os.path.exists(self.cache_file), "Cache file should be created")

        with open(self.cache_file, "r") as f:
            cache_data = json.load(f)

        # Verify cache contains correct field configuration
        self.assertEqual(
            cache_data.get("fields_requested"),
            "key,created,resolutiondate,status",
            "Cache should only contain basic fields when no points field configured",
        )

        # Verify issues in cache don't have votes field
        if cache_data.get("issues"):
            sample_issue = cache_data["issues"][0]
            self.assertNotIn(
                "votes",
                sample_issue.get("fields", {}),
                "Issues should not contain votes field when points field is empty",
            )

    @patch("data.jira_simple.fetch_jira_issues")
    @patch("data.jira_simple.JIRA_CACHE_FILE")
    def test_calculate_scope_with_empty_points_field(self, mock_cache_file, mock_fetch):
        """Test 'Calculate Scope' button workflow with empty points field."""
        mock_cache_file.return_value = self.cache_file
        mock_fetch.return_value = (True, self.mock_issues)

        from data.persistence import update_project_scope_from_jira

        # UI config that would be created by the fixed Calculate Scope callback
        ui_config = {
            "jql_query": "project = TEST",
            "base_url": "https://jira.atlassian.com",
            "token": "",
            "story_points_field": "",  # Empty - should not default to votes
            "cache_max_size_mb": 50,
        }

        # Simulate clicking 'Calculate Scope' with empty points field
        success, message = update_project_scope_from_jira(
            ui_config["jql_query"], ui_config
        )

        self.assertTrue(success, f"Calculate Scope should succeed: {message}")

        # Verify cache was created with correct field configuration
        self.assertTrue(os.path.exists(self.cache_file), "Cache file should be created")

        with open(self.cache_file, "r") as f:
            cache_data = json.load(f)

        # This is the key test - Calculate Scope should NOT add votes field
        self.assertEqual(
            cache_data.get("fields_requested"),
            "key,created,resolutiondate,status",
            "Calculate Scope should not add votes field when points field is empty",
        )

        # Verify project scope calculations are correct
        from data.persistence import get_project_scope

        scope = get_project_scope()

        self.assertFalse(
            scope.get("points_field_available", True),
            "Points field should not be available",
        )
        self.assertEqual(
            scope.get("estimated_items", -1), 0, "Should have 0 estimated items"
        )
        self.assertEqual(
            scope.get("estimated_points", -1), 0, "Should have 0 estimated points"
        )
        self.assertEqual(
            scope.get("remaining_total_points", -1), 0, "Should have 0 total points"
        )

    @patch("data.jira_simple.fetch_jira_issues")
    @patch("data.jira_simple.JIRA_CACHE_FILE")
    def test_cache_invalidation_on_field_change(self, mock_cache_file, mock_fetch):
        """Test that cache is properly invalidated when field configuration changes."""
        mock_cache_file.return_value = self.cache_file
        mock_fetch.return_value = (True, self.mock_issues)

        from data.jira_simple import sync_jira_data, load_jira_cache

        # First, create cache with votes field
        mock_issues_with_votes = []
        for issue in self.mock_issues:
            issue_copy = issue.copy()
            issue_copy["fields"] = issue["fields"].copy()
            issue_copy["fields"]["votes"] = {"votes": 0, "hasVoted": False}
            mock_issues_with_votes.append(issue_copy)

        mock_fetch.return_value = (True, mock_issues_with_votes)

        # Simulate previous call that used votes field
        with patch("data.jira_simple.get_jira_config") as mock_config:
            mock_config.return_value = {"story_points_field": "votes"}
            sync_jira_data("project = TEST")

        # Verify cache was created with votes field
        with open(self.cache_file, "r") as f:
            cache_data = json.load(f)
        self.assertIn("votes", cache_data.get("fields_requested", ""))

        # Now test cache invalidation when field changes to empty
        mock_fetch.return_value = (True, self.mock_issues)  # No votes field
        cache_valid, issues = load_jira_cache(
            current_jql_query="project = TEST",
            current_fields="key,created,resolutiondate,status",  # No votes
        )

        # Cache should be invalidated due to field mismatch
        self.assertFalse(cache_valid, "Cache should be invalidated when fields change")
        self.assertEqual(
            len(issues), 0, "Should return empty issues when cache invalidated"
        )


if __name__ == "__main__":
    unittest.main()
