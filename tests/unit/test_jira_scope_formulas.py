"""
Unit tests for JIRA scope calculation with various point configurations.
This test validates the scope calculation formulas and field definitions.
"""

import unittest
from data.jira.scope_calculator import calculate_jira_project_scope


class TestJiraScopeCalculationFormulas(unittest.TestCase):
    """Test JIRA scope calculation formulas and field definitions."""

    def setUp(self):
        """Set up test data with mixed point availability."""
        self.test_issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 8,
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
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": 3,
                },
            },
            {
                "key": "PROJ-4",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": None,  # No points assigned
                },
            },
        ]

    def test_scope_calculation_with_mixed_points(self):
        """Test scope calculation with mixed point availability."""
        result = calculate_jira_project_scope(self.test_issues, "customfield_10002")

        # Basic counts
        self.assertEqual(result["total_items"], 4, "Should count all 4 issues")
        self.assertEqual(
            result["completed_items"], 1, "Should count 1 completed item (PROJ-1)"
        )
        self.assertEqual(
            result["remaining_items"],
            3,
            "Should count 3 remaining items (PROJ-2, PROJ-3, PROJ-4)",
        )

        # Point calculations - only actual points, no fake data
        self.assertEqual(
            result["total_points"],
            16,
            "Total points: 8 + 5 + 3 = 16 (PROJ-4 has no points)",
        )
        self.assertEqual(
            result["completed_points"], 8, "Completed points: 8 from PROJ-1"
        )
        self.assertEqual(
            result["remaining_points"],
            8,
            "Remaining points: 5 + 3 = 8 (PROJ-4 has no points)",
        )

        # Estimated items and points (items with actual point values)
        self.assertEqual(
            result["estimated_items"],
            2,
            "Estimated items: PROJ-2 and PROJ-3 have points",
        )
        self.assertEqual(result["estimated_points"], 8, "Estimated points: 5 + 3 = 8")

        # Remaining total points calculation formula validation
        # Formula: Estimated Points + (avg_points_per_item × unestimated_items)
        # avg_points_per_item = estimated_points / estimated_items = 8 / 2 = 4.0
        # unestimated_items = remaining_items - estimated_items = 3 - 2 = 1
        # remaining_total_points = 8 + (4.0 × 1) = 12.0
        self.assertEqual(
            result["remaining_total_points"],
            12.0,
            "Remaining total points: 8 + (4.0 × 1) = 12.0",
        )

        self.assertTrue(
            result["points_field_available"], "Points field should be available"
        )

    def test_scope_field_definitions_validation(self):
        """Validate that field definitions match user requirements."""
        result = calculate_jira_project_scope(self.test_issues, "customfield_10002")

        # Field definition validations based on user requirements:

        # Remaining Estimated Items: items not completed AND have point values
        expected_estimated_items = (
            2  # PROJ-2 and PROJ-3 have points and are not completed
        )
        self.assertEqual(
            result["estimated_items"],
            expected_estimated_items,
            "Remaining Estimated Items: items not completed AND have point values",
        )

        # Remaining Total Items: total number of all items not completed
        expected_remaining_items = 3  # PROJ-2, PROJ-3, PROJ-4 are not completed
        self.assertEqual(
            result["remaining_items"],
            expected_remaining_items,
            "Remaining Total Items: total number of all items not completed",
        )

        # Remaining Estimated Points: sum of points from Remaining Estimated Items
        expected_estimated_points = 8  # 5 (PROJ-2) + 3 (PROJ-3) = 8
        self.assertEqual(
            result["estimated_points"],
            expected_estimated_points,
            "Remaining Estimated Points: sum of points from Remaining Estimated Items",
        )

        # Remaining Total Points: Estimated Points + (avg × unestimated items)
        expected_total_points = 12.0  # 8 + (4.0 × 1) = 12.0
        self.assertEqual(
            result["remaining_total_points"],
            expected_total_points,
            "Remaining Total Points: Estimated Points + (avg × unestimated items)",
        )

    def test_all_items_have_points(self):
        """Test scenario where all remaining items have point values."""
        issues_with_all_points = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 8,
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": 5,
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": 3,
                },
            },
        ]

        result = calculate_jira_project_scope(
            issues_with_all_points, "customfield_10002"
        )

        # When all remaining items have points, estimated = remaining for both items and points
        self.assertEqual(result["remaining_items"], 2, "2 remaining items")
        self.assertEqual(
            result["estimated_items"], 2, "All remaining items have points"
        )
        self.assertEqual(result["remaining_points"], 8, "Remaining points: 5 + 3 = 8")
        self.assertEqual(
            result["estimated_points"], 8, "All remaining points are estimated"
        )
        self.assertEqual(
            result["remaining_total_points"], 8.0, "No extrapolation needed"
        )

    def test_no_items_have_points(self):
        """Test scenario where no items have point values."""
        issues_without_points = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": None,
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "customfield_10002": None,
                },
            },
        ]

        result = calculate_jira_project_scope(
            issues_without_points, "customfield_10002"
        )

        # When no items have points, no fake data is created
        self.assertEqual(result["remaining_items"], 1, "1 remaining item")
        self.assertEqual(result["estimated_items"], 0, "No items have points")
        self.assertEqual(
            result["remaining_points"],
            0,
            "No points (no fake data created)",
        )
        self.assertEqual(result["estimated_points"], 0, "No estimated points")
        self.assertEqual(
            result["remaining_total_points"],
            0,
            "No points when no data exists",
        )
        self.assertTrue(
            result["points_field_available"],
            "Points field should be available when configured",
        )


if __name__ == "__main__":
    unittest.main()
