import pytest

from data.jira.scope_calculator import calculate_jira_project_scope


class TestJiraProjectScopeCalculation:
    def test_basic_scope_calculation_with_votes(self):
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

        assert result["total_items"] == 3
        assert result["total_points"] == 16

        assert result["completed_items"] == 1
        assert result["completed_points"] == 5

        assert result["remaining_items"] == 2
        assert result["remaining_points"] == 11

        assert "Done" in result["status_breakdown"]
        assert result["status_breakdown"]["Done"]["items"] == 1
        assert result["status_breakdown"]["Done"]["points"] == 5

    def test_no_story_points_calculation(self):
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "votes": None,
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "To Do", "statusCategory": {"key": "new"}},
                    "votes": None,
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "votes")

        assert result["total_items"] == 2
        assert result["total_points"] == 0
        assert result["completed_items"] == 1
        assert result["completed_points"] == 0
        assert result["remaining_items"] == 1
        assert result["remaining_points"] == 0
        assert result["points_field_available"] is True

    def test_custom_status_configuration(self):
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {
                        "name": "Deployed",
                        "statusCategory": {"key": "new"},
                    },
                    "votes": {"votes": 10},
                },
            }
        ]

        status_config = {
            "method": "status_names",
            "completed_statuses": ["Deployed"],
            "in_progress_statuses": [],
            "todo_statuses": [],
        }

        result = calculate_jira_project_scope(issues, "votes", status_config)

        assert result["completed_items"] == 1
        assert result["completed_points"] == 10
        assert result["remaining_items"] == 0
        assert result["remaining_points"] == 0

    def test_mixed_story_points_fields(self):
        issues = [
            {
                "key": "PROJ-1",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": 15.0,
                },
            },
            {
                "key": "PROJ-2",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": "8",
                },
            },
            {
                "key": "PROJ-3",
                "fields": {
                    "status": {"name": "Done", "statusCategory": {"key": "done"}},
                    "customfield_10002": {"value": 5},
                },
            },
        ]

        result = calculate_jira_project_scope(issues, "customfield_10002")

        assert result["total_items"] == 3
        assert result["completed_items"] == 3
        assert result["completed_points"] == 28

    def test_empty_issues_list(self):
        result = calculate_jira_project_scope([], "votes")

        assert result["total_items"] == 0
        assert result["total_points"] == 0
        assert result["completed_items"] == 0
        assert result["completed_points"] == 0
        assert result["remaining_items"] == 0
        assert result["remaining_points"] == 0
        assert result["status_breakdown"] == {}

    def test_malformed_issue_handling(self):
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

        assert result["total_items"] == 2
        assert result["total_points"] == 12
        assert result["completed_items"] == 1
        assert result["remaining_items"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
