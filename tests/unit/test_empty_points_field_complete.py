"""
Unit tests for JIRA scope calculation with empty points field scenarios.
This test validates the complete fix for the empty points field issue.
"""

import unittest
from unittest.mock import patch
from data.jira_scope_calculator import calculate_jira_project_scope
from data.persistence import update_project_scope_from_jira, get_project_scope


class TestEmptyPointsFieldComplete(unittest.TestCase):
    """Test comprehensive scenarios for empty points field handling."""

    def test_user_reported_scenario_reproduction(self):
        """
        Test scenario that reproduces the user's original report:
        - JQL: project = JRASERVER AND created > endOfMonth(-4)
        - Points Field: left empty
        - Expected: All point calculations should be 0, not extrapolated values
        """
        # Create mock JIRA issues similar to what would come from the user's JQL
        mock_issues = []

        # Add 145 completed issues (matching user's completed count)
        for i in range(145):
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 1}",
                    "fields": {
                        "status": {"name": "Done", "statusCategory": {"key": "done"}},
                        "created": "2024-09-01T10:00:00.000Z",
                    },
                }
            )

        # Add 50 remaining issues (25 In Progress, 25 To Do)
        for i in range(50):
            status_name = "In Progress" if i < 25 else "To Do"
            status_key = "indeterminate" if i < 25 else "new"
            mock_issues.append(
                {
                    "key": f"JRASERVER-{i + 146}",
                    "fields": {
                        "status": {
                            "name": status_name,
                            "statusCategory": {"key": status_key},
                        },
                        "created": "2024-10-01T10:00:00.000Z",
                    },
                }
            )

        # Test with empty points field (as user reported)
        result = calculate_jira_project_scope(mock_issues, "")

        # Validate the fix: all point calculations should be 0 when no points field
        self.assertFalse(
            result["points_field_available"],
            "Points field should not be available when empty",
        )

        # These were the problematic values the user reported:
        self.assertEqual(
            result["estimated_items"],
            0,
            "Should have 0 estimated items, not 50 (user's original issue)",
        )
        self.assertEqual(
            result["estimated_points"],
            0,
            "Should have 0 estimated points, not 279 (user's original issue)",
        )
        self.assertEqual(
            result["remaining_total_points"],
            0.0,
            "Should have 0 remaining total points, not 1088 (user's original issue)",
        )

        # But item counts should still be accurate
        self.assertEqual(result["total_items"], 195, "Total items should be 195")
        self.assertEqual(
            result["completed_items"], 145, "Should have 145 completed items"
        )
        self.assertEqual(
            result["remaining_items"], 50, "Should have 50 remaining items"
        )

        # All point-related fields should be 0 when no points field is configured
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)

    def test_calculate_scope_button_fix(self):
        """
        Test that the 'Calculate Scope' button no longer defaults empty points field to 'votes'.
        This test validates the UI callback fix.
        """
        # Simulate the UI config that would be created by the fixed callback
        ui_config = {
            "jql_query": "project = TEST",
            "base_url": "https://jira.atlassian.com",
            "token": "",
            "story_points_field": "",  # Empty - should NOT default to votes anymore
            "cache_max_size_mb": 50,
        }

        # Mock the JIRA API response with basic fields (no votes)
        mock_issues = [
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
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "created": "2025-01-01T10:00:00.000Z",
                    "resolutiondate": None,
                },
            },
        ]

        with patch("data.jira_simple.fetch_jira_issues") as mock_fetch:
            mock_fetch.return_value = (True, mock_issues)

            # This simulates clicking "Calculate Scope" with empty points field
            success, message = update_project_scope_from_jira(
                ui_config["jql_query"], ui_config
            )

            # Verify the operation succeeded
            self.assertTrue(success, f"Calculate Scope should succeed: {message}")

            # Verify project scope calculations are correct (all point values = 0)
            scope = get_project_scope()

            self.assertFalse(
                scope.get("points_field_available", True),
                "Points field should not be available when empty",
            )
            self.assertEqual(
                scope.get("estimated_items", -1),
                0,
                "Should have 0 estimated items, not defaulted value",
            )
            self.assertEqual(
                scope.get("estimated_points", -1),
                0,
                "Should have 0 estimated points, not calculated from votes",
            )
            self.assertEqual(
                scope.get("remaining_total_points", -1),
                0,
                "Should have 0 total points, not extrapolated",
            )

            # But item counts should still work
            self.assertEqual(
                scope.get("total_items", -1), 2, "Should count 2 total items"
            )
            self.assertEqual(
                scope.get("completed_items", -1), 1, "Should count 1 completed item"
            )
            self.assertEqual(
                scope.get("remaining_items", -1), 1, "Should count 1 remaining item"
            )


if __name__ == "__main__":
    unittest.main()
