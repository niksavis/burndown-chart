import unittest

from data.jira.scope_calculator import calculate_jira_project_scope


class TestJiraScopeCalculationFormulas(unittest.TestCase):
    def setUp(self):
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
                    "customfield_10002": None,
                },
            },
        ]

    def test_scope_calculation_with_mixed_points(self):
        result = calculate_jira_project_scope(self.test_issues, "customfield_10002")

        self.assertEqual(result["total_items"], 4, "Should count all 4 issues")
        self.assertEqual(
            result["completed_items"], 1, "Should count 1 completed item (PROJ-1)"
        )
        self.assertEqual(
            result["remaining_items"],
            3,
            "Should count 3 remaining items (PROJ-2, PROJ-3, PROJ-4)",
        )

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

        self.assertEqual(
            result["estimated_items"],
            2,
            "Estimated items: PROJ-2 and PROJ-3 have points",
        )
        self.assertEqual(result["estimated_points"], 8, "Estimated points: 5 + 3 = 8")

        self.assertEqual(
            result["remaining_total_points"],
            12.0,
            "Remaining total points: 8 + (4.0 × 1) = 12.0",
        )

        self.assertTrue(
            result["points_field_available"], "Points field should be available"
        )

    def test_scope_field_definitions_validation(self):
        result = calculate_jira_project_scope(self.test_issues, "customfield_10002")

        expected_estimated_items = 2
        self.assertEqual(
            result["estimated_items"],
            expected_estimated_items,
            "Remaining Estimated Items: items not completed AND have point values",
        )

        expected_remaining_items = 3
        self.assertEqual(
            result["remaining_items"],
            expected_remaining_items,
            "Remaining Total Items: total number of all items not completed",
        )

        expected_estimated_points = 8
        self.assertEqual(
            result["estimated_points"],
            expected_estimated_points,
            "Remaining Estimated Points: sum of points from Remaining Estimated Items",
        )

        expected_total_points = 12.0
        self.assertEqual(
            result["remaining_total_points"],
            expected_total_points,
            "Remaining Total Points: Estimated Points + (avg × unestimated items)",
        )

    def test_all_items_have_points(self):
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
