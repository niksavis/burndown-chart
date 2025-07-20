"""
Test cases for empty/invalid points field scenarios in JIRA scope calculation.
"""

import unittest
from data.jira_scope_calculator import calculate_jira_project_scope


class TestEmptyPointsField(unittest.TestCase):
    """Test cases for handling empty or invalid points fields."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.sample_issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 8,
                    "votes": {"votes": 2},
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {
                        "name": "In Progress",
                        "statusCategory": {"key": "indeterminate"},
                    },
                    "customfield_10002": 5,
                    "votes": {"votes": 1},
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": 3,
                    "votes": {"votes": 1},
                },
            },
        ]

    def test_empty_string_points_field(self):
        """Test behavior with empty string points field."""
        result = calculate_jira_project_scope(self.sample_issues, "")

        # When points field is empty, no points should be calculated
        self.assertFalse(result["points_field_available"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)
        self.assertEqual(result["estimated_points"], 0)
        self.assertEqual(result["remaining_total_points"], 0.0)

        # Items should still be counted correctly
        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)
        self.assertEqual(result["estimated_items"], 2)  # Fallback when no points field

    def test_whitespace_points_field(self):
        """Test behavior with whitespace-only points field."""
        result = calculate_jira_project_scope(self.sample_issues, "   ")

        # Should behave same as empty string
        self.assertFalse(result["points_field_available"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)
        self.assertEqual(result["estimated_points"], 0)
        self.assertEqual(result["remaining_total_points"], 0.0)

        # Items should still be counted correctly
        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)

    def test_valid_points_field_comparison(self):
        """Test that valid points field works correctly for comparison."""
        result = calculate_jira_project_scope(self.sample_issues, "customfield_10002")

        # Should use actual point values
        self.assertTrue(result["points_field_available"])
        self.assertEqual(result["total_points"], 16)  # 8 + 5 + 3
        self.assertEqual(result["completed_points"], 8)  # PROJ-1
        self.assertEqual(result["remaining_points"], 8)  # PROJ-2 (5) + PROJ-3 (3)
        self.assertEqual(
            result["estimated_points"], 8
        )  # Same as remaining since all have points
        self.assertEqual(result["remaining_total_points"], 8.0)

        # Items should be counted correctly
        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)
        self.assertEqual(result["estimated_items"], 2)


if __name__ == "__main__":
    unittest.main()
