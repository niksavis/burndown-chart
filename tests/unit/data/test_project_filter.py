"""Tests for project filtering utilities.

This test suite validates that issues are correctly filtered based on
project type (Development vs DevOps) for different metric calculations.
"""

from data.project_filter import (
    filter_deployment_issues,
    filter_development_issues,
    filter_devops_issues,
    filter_incident_issues,
    filter_work_items,
    get_issue_project_key,
    get_issue_type,
    get_project_summary,
    is_development_issue,
    is_devops_issue,
)


class TestProjectKeyExtraction:
    """Test extraction of project key from issues."""

    def test_extract_project_key_normal(self):
        """Test extracting project key from normal issue."""
        issue = {
            "key": "DEV1-123",
            "fields": {"project": {"key": "DEV1", "name": "Development Project"}},
        }
        assert get_issue_project_key(issue) == "DEV1"

    def test_extract_project_key_devops(self):
        """Test extracting project key from DevOps issue."""
        issue = {
            "key": "DEVOPS-456",
            "fields": {"project": {"key": "DEVOPS", "name": "DevOps Project"}},
        }
        assert get_issue_project_key(issue) == "DEVOPS"

    def test_extract_project_key_missing_fields(self):
        """Test handling missing fields - fallback to parsing issue key."""
        issue = {"key": "TEST-1"}
        assert get_issue_project_key(issue) == "TEST"

    def test_extract_project_key_empty_dict(self):
        """Test handling empty issue dict."""
        issue = {}
        assert get_issue_project_key(issue) == ""


class TestIssueTypeExtraction:
    """Test extraction of issue type from issues."""

    def test_extract_issue_type_story(self):
        """Test extracting Story type."""
        issue = {"fields": {"issuetype": {"name": "Story", "id": "10001"}}}
        assert get_issue_type(issue) == "Story"

    def test_extract_issue_type_operational_task(self):
        """Test extracting Operational Task type."""
        issue = {"fields": {"issuetype": {"name": "Operational Task", "id": "10008"}}}
        assert get_issue_type(issue) == "Operational Task"

    def test_extract_issue_type_bug(self):
        """Test extracting Bug type."""
        issue = {"fields": {"issuetype": {"name": "Bug", "id": "10004"}}}
        assert get_issue_type(issue) == "Bug"

    def test_extract_issue_type_missing(self):
        """Test handling missing issue type."""
        issue = {"fields": {}}
        assert get_issue_type(issue) == ""


class TestDevOpsProjectDetection:
    """Test detection of DevOps vs Development projects."""

    def test_is_devops_issue_true(self):
        """Test identifying DevOps issue."""
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_devops_issue(issue, ["DEVOPS"]) is True

    def test_is_devops_issue_false(self):
        """Test identifying non-DevOps issue."""
        issue = {"fields": {"project": {"key": "DEV1"}}}
        assert is_devops_issue(issue, ["DEVOPS"]) is False

    def test_is_devops_issue_multiple_devops_projects(self):
        """Test with multiple DevOps projects."""
        issue_ri = {"fields": {"project": {"key": "DEVOPS"}}}
        issue_ops = {"fields": {"project": {"key": "OPS"}}}
        issue_dev = {"fields": {"project": {"key": "DEV1"}}}

        devops_projects = ["DEVOPS", "OPS"]

        assert is_devops_issue(issue_ri, devops_projects) is True
        assert is_devops_issue(issue_ops, devops_projects) is True
        assert is_devops_issue(issue_dev, devops_projects) is False

    def test_is_devops_issue_empty_list(self):
        """Test with no DevOps projects configured."""
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_devops_issue(issue, []) is False

    def test_is_development_issue_true(self):
        """Test identifying development issue (blacklist mode)."""
        issue = {"fields": {"project": {"key": "DEV1"}}}
        assert is_development_issue(issue, devops_projects=["DEVOPS"]) is True

    def test_is_development_issue_false(self):
        """Test identifying non-development issue."""
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_development_issue(issue, devops_projects=["DEVOPS"]) is False

    def test_is_development_issue_with_whitelist(self):
        """Test development issue check with whitelist."""
        issue = {"fields": {"project": {"key": "DEV1"}}}
        # Should be True - DEV1 is in whitelist
        assert (
            is_development_issue(issue, development_projects=["DEV1", "DEV2"]) is True
        )
        # Should be False - DEV1 not in whitelist
        assert is_development_issue(issue, development_projects=["DEV2"]) is False


class TestDevelopmentIssueFiltering:
    """Test filtering to development project issues."""

    def test_filter_development_issues_excludes_devops(self):
        """Test that DevOps issues are excluded (blacklist mode)."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEV1-2", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "DEV1-3", "fields": {"project": {"key": "DEV1"}}},
        ]

        filtered = filter_development_issues(issues, devops_projects=["DEVOPS"])

        assert len(filtered) == 3
        assert all(get_issue_project_key(i) == "DEV1" for i in filtered)

    def test_filter_development_issues_whitelist_mode(self):
        """Test filtering with development_projects whitelist."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEV2-1", "fields": {"project": {"key": "DEV2"}}},
            {"key": "OTHER-1", "fields": {"project": {"key": "OTHER"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        # ONLY include DEV1 and DEV2
        filtered = filter_development_issues(
            issues, development_projects=["DEV1", "DEV2"]
        )

        assert len(filtered) == 2
        project_keys = {get_issue_project_key(i) for i in filtered}
        assert project_keys == {"DEV1", "DEV2"}

    def test_filter_development_issues_no_devops_configured(self):
        """Test with no DevOps projects - all issues returned."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        filtered = filter_development_issues(issues)

        assert len(filtered) == 2

    def test_filter_development_issues_empty_list(self):
        """Test with empty issue list."""
        filtered = filter_development_issues([], devops_projects=["DEVOPS"])
        assert len(filtered) == 0

    def test_filter_development_issues_multiple_dev_projects(self):
        """Test filtering with multiple development projects (blacklist mode)."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEV2-1", "fields": {"project": {"key": "DEV2"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "DEV1-2", "fields": {"project": {"key": "DEV1"}}},
        ]

        filtered = filter_development_issues(issues, devops_projects=["DEVOPS"])

        assert len(filtered) == 3
        assert get_issue_project_key(filtered[0]) == "DEV1"
        assert get_issue_project_key(filtered[1]) == "DEV2"
        assert get_issue_project_key(filtered[2]) == "DEV1"


class TestDevOpsIssueFiltering:
    """Test filtering to DevOps project issues."""

    def test_filter_devops_issues_includes_only_devops(self):
        """Test that only DevOps issues are included."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "DEVOPS-2", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "DEV1-2", "fields": {"project": {"key": "DEV1"}}},
        ]

        filtered = filter_devops_issues(issues, ["DEVOPS"])

        assert len(filtered) == 2
        assert all(get_issue_project_key(i) == "DEVOPS" for i in filtered)

    def test_filter_devops_issues_no_devops_configured(self):
        """Test with no DevOps projects - empty list returned."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        filtered = filter_devops_issues(issues, [])

        assert len(filtered) == 0

    def test_filter_devops_issues_multiple_devops_projects(self):
        """Test with multiple DevOps projects."""
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "OPS-1", "fields": {"project": {"key": "OPS"}}},
        ]

        filtered = filter_devops_issues(issues, ["DEVOPS", "OPS"])

        assert len(filtered) == 2


class TestDeploymentIssueFiltering:
    """Test filtering to deployment tracking issues."""

    def test_filter_deployment_issues_operational_tasks_only(self):
        """Test that only Operational Tasks from DevOps projects are included."""
        issues = [
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Operational Task"},
                },
            },
            {
                "key": "DEVOPS-2",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Bug"},  # Not deployment
                },
            },
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Operational Task"},  # Wrong project
                },
            },
            {
                "key": "DEVOPS-3",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Operational Task"},
                },
            },
        ]

        filtered = filter_deployment_issues(issues, ["DEVOPS"])

        assert len(filtered) == 2
        assert all(get_issue_project_key(i) == "DEVOPS" for i in filtered)
        assert all(get_issue_type(i) == "Operational Task" for i in filtered)

    def test_filter_deployment_issues_no_deployments(self):
        """Test when no deployment issues exist."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Story"}},
            }
        ]

        filtered = filter_deployment_issues(issues, ["DEVOPS"])

        assert len(filtered) == 0


class TestIncidentIssueFiltering:
    """Test filtering to production incident issues."""

    def test_filter_incident_issues_production_bugs_only(self):
        """Test that only production bugs from dev projects are included."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},  # Production bug
                },
            },
            {
                "key": "DEV1-2",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "DEV"},  # Not production
                },
            },
            {
                "key": "DEV1-3",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Story"},
                    "customfield_11309": {"value": "PROD"},  # Not a bug
                },
            },
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},  # Wrong project
                },
            },
            {
                "key": "DEV1-4",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},  # Production bug
                },
            },
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_11309"
        )

        assert len(filtered) == 2
        assert all(get_issue_project_key(i) == "DEV1" for i in filtered)
        assert all(get_issue_type(i) == "Bug" for i in filtered)

    def test_filter_incident_issues_string_environment_field(self):
        """Test with environment field as plain string."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": "PROD",  # String instead of dict
                },
            }
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_11309"
        )

        assert len(filtered) == 1

    def test_filter_incident_issues_case_insensitive(self):
        """Test that environment matching is case-insensitive."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "prod"},  # Lowercase
                },
            },
            {
                "key": "DEV1-2",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": "Prod",  # String, mixed case
                },
            },
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_11309"
        )

        assert len(filtered) == 2

    def test_filter_incident_issues_custom_environment_field(self):
        """Test with custom environment field ID."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_99999": {"value": "PROD"},
                },
            }
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_99999"
        )

        assert len(filtered) == 1


class TestWorkItemFiltering:
    """Test filtering to work items (Stories, Tasks)."""

    def test_filter_work_items_default_types(self):
        """Test filtering with default work item types."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Story"}},
            },
            {
                "key": "DEV1-2",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Task"}},
            },
            {
                "key": "DEV1-3",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},  # Not a work item
                },
            },
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Story"},  # Wrong project
                },
            },
        ]

        filtered = filter_work_items(issues, ["DEVOPS"])

        assert len(filtered) == 2
        assert get_issue_type(filtered[0]) in ["Story", "Task"]
        assert get_issue_type(filtered[1]) in ["Story", "Task"]

    def test_filter_work_items_custom_types(self):
        """Test filtering with custom work item types."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Feature"},
                },
            },
            {
                "key": "DEV1-2",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Story"}},
            },
        ]

        filtered = filter_work_items(
            issues, ["DEVOPS"], work_item_types=["Feature", "Story"]
        )

        assert len(filtered) == 2


class TestProjectSummary:
    """Test project summary statistics."""

    def test_get_project_summary_mixed_projects(self):
        """Test summary with mixed development and DevOps issues."""
        issues = [
            {
                "key": "DEV1-1",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Story"}},
            },
            {
                "key": "DEV1-2",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Bug"}},
            },
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Operational Task"},
                },
            },
            {
                "key": "DEV2-1",
                "fields": {"project": {"key": "DEV2"}, "issuetype": {"name": "Story"}},
            },
        ]

        summary = get_project_summary(issues, ["DEVOPS"])

        assert summary["total_issues"] == 4
        assert summary["development_issues"] == 3
        assert summary["devops_issues"] == 1
        assert summary["projects"]["DEV1"] == 2
        assert summary["projects"]["DEV2"] == 1
        assert summary["projects"]["DEVOPS"] == 1
        assert summary["issue_types"]["Story"] == 2
        assert summary["issue_types"]["Bug"] == 1
        assert summary["issue_types"]["Operational Task"] == 1
        assert summary["devops_projects"] == ["DEVOPS"]

    def test_get_project_summary_empty_issues(self):
        """Test summary with no issues."""
        summary = get_project_summary([], ["DEVOPS"])

        assert summary["total_issues"] == 0
        assert summary["development_issues"] == 0
        assert summary["devops_issues"] == 0
        assert len(summary["projects"]) == 0
        assert len(summary["issue_types"]) == 0
