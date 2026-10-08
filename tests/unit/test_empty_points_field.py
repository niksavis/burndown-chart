import unittest

from data.jira.scope_calculator import calculate_jira_project_scope


class TestEmptyPointsField(unittest.TestCase):
    def setUp(self):
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
        result = calculate_jira_project_scope(self.sample_issues, "")

        self.assertFalse(result["points_field_available"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)
        self.assertEqual(result["estimated_points"], 0)
        self.assertEqual(result["remaining_total_points"], 0.0)

        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)
        self.assertEqual(result["estimated_items"], 0)

    def test_whitespace_points_field(self):
        result = calculate_jira_project_scope(self.sample_issues, "   ")

        self.assertFalse(result["points_field_available"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)
        self.assertEqual(result["estimated_points"], 0)
        self.assertEqual(result["remaining_total_points"], 0.0)

        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)
        self.assertEqual(result["estimated_items"], 0)

    def test_valid_points_field_comparison(self):
        result = calculate_jira_project_scope(self.sample_issues, "customfield_10002")

        self.assertTrue(result["points_field_available"])
        self.assertEqual(result["total_points"], 16)
        self.assertEqual(result["completed_points"], 8)
        self.assertEqual(result["remaining_points"], 8)
        self.assertEqual(result["estimated_points"], 8)
        self.assertEqual(result["remaining_total_points"], 8.0)

        self.assertEqual(result["total_items"], 3)
        self.assertEqual(result["completed_items"], 1)
        self.assertEqual(result["remaining_items"], 2)
        self.assertEqual(result["estimated_items"], 2)

    def test_empty_points_field_with_many_issues(self):
        large_issues = []

        for i in range(145):
            large_issues.append(
                {
                    "key": f"TEST-{i + 1}",
                    "fields": {
                        "status": {"name": "Done", "statusCategory": {"key": "done"}},
                        "customfield_10002": None,
                    },
                }
            )

        for i in range(50):
            status_name = "In Progress" if i < 25 else "To Do"
            status_key = "indeterminate" if i < 25 else "new"
            large_issues.append(
                {
                    "key": f"TEST-{i + 146}",
                    "fields": {
                        "status": {
                            "name": status_name,
                            "statusCategory": {"key": status_key},
                        },
                        "customfield_10002": None,
                    },
                }
            )

        result = calculate_jira_project_scope(large_issues, "")

        self.assertFalse(result["points_field_available"])
        self.assertEqual(result["total_points"], 0)
        self.assertEqual(result["completed_points"], 0)
        self.assertEqual(result["remaining_points"], 0)
        self.assertEqual(result["estimated_points"], 0)
        self.assertEqual(result["remaining_total_points"], 0.0)
        self.assertEqual(result["estimated_items"], 0)

        self.assertEqual(result["total_items"], 195)
        self.assertEqual(result["completed_items"], 145)
        self.assertEqual(result["remaining_items"], 50)


if __name__ == "__main__":
    unittest.main()
