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
    def test_extract_project_key_normal(self):
        issue = {
            "key": "DEV1-123",
            "fields": {"project": {"key": "DEV1", "name": "Development Project"}},
        }
        assert get_issue_project_key(issue) == "DEV1"

    def test_extract_project_key_devops(self):
        issue = {
            "key": "DEVOPS-456",
            "fields": {"project": {"key": "DEVOPS", "name": "DevOps Project"}},
        }
        assert get_issue_project_key(issue) == "DEVOPS"

    def test_extract_project_key_missing_fields(self):
        issue = {"key": "TEST-1"}
        assert get_issue_project_key(issue) == "TEST"

    def test_extract_project_key_empty_dict(self):
        issue = {}
        assert get_issue_project_key(issue) == ""


class TestIssueTypeExtraction:
    def test_extract_issue_type_story(self):
        issue = {"fields": {"issuetype": {"name": "Story", "id": "10001"}}}
        assert get_issue_type(issue) == "Story"

    def test_extract_issue_type_operational_task(self):
        issue = {"fields": {"issuetype": {"name": "Operational Task", "id": "10008"}}}
        assert get_issue_type(issue) == "Operational Task"

    def test_extract_issue_type_bug(self):
        issue = {"fields": {"issuetype": {"name": "Bug", "id": "10004"}}}
        assert get_issue_type(issue) == "Bug"

    def test_extract_issue_type_missing(self):
        issue = {"fields": {}}
        assert get_issue_type(issue) == ""


class TestDevOpsProjectDetection:
    def test_is_devops_issue_true(self):
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_devops_issue(issue, ["DEVOPS"]) is True

    def test_is_devops_issue_false(self):
        issue = {"fields": {"project": {"key": "DEV1"}}}
        assert is_devops_issue(issue, ["DEVOPS"]) is False

    def test_is_devops_issue_multiple_devops_projects(self):
        issue_ri = {"fields": {"project": {"key": "DEVOPS"}}}
        issue_ops = {"fields": {"project": {"key": "OPS"}}}
        issue_dev = {"fields": {"project": {"key": "DEV1"}}}

        devops_projects = ["DEVOPS", "OPS"]

        assert is_devops_issue(issue_ri, devops_projects) is True
        assert is_devops_issue(issue_ops, devops_projects) is True
        assert is_devops_issue(issue_dev, devops_projects) is False

    def test_is_devops_issue_empty_list(self):
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_devops_issue(issue, []) is False

    def test_is_development_issue_true(self):
        issue = {"fields": {"project": {"key": "DEV1"}}}
        assert is_development_issue(issue, devops_projects=["DEVOPS"]) is True

    def test_is_development_issue_false(self):
        issue = {"fields": {"project": {"key": "DEVOPS"}}}
        assert is_development_issue(issue, devops_projects=["DEVOPS"]) is False

    def test_is_development_issue_with_whitelist(self):
        issue = {"fields": {"project": {"key": "DEV1"}}}
        assert (
            is_development_issue(issue, development_projects=["DEV1", "DEV2"]) is True
        )
        assert is_development_issue(issue, development_projects=["DEV2"]) is False


class TestDevelopmentIssueFiltering:
    def test_filter_development_issues_excludes_devops(self):
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
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEV2-1", "fields": {"project": {"key": "DEV2"}}},
            {"key": "OTHER-1", "fields": {"project": {"key": "OTHER"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        filtered = filter_development_issues(
            issues, development_projects=["DEV1", "DEV2"]
        )

        assert len(filtered) == 2
        project_keys = {get_issue_project_key(i) for i in filtered}
        assert project_keys == {"DEV1", "DEV2"}

    def test_filter_development_issues_no_devops_configured(self):
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        filtered = filter_development_issues(issues)

        assert len(filtered) == 2

    def test_filter_development_issues_empty_list(self):
        filtered = filter_development_issues([], devops_projects=["DEVOPS"])
        assert len(filtered) == 0

    def test_filter_development_issues_multiple_dev_projects(self):
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
    def test_filter_devops_issues_includes_only_devops(self):
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
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
        ]

        filtered = filter_devops_issues(issues, [])

        assert len(filtered) == 0

    def test_filter_devops_issues_multiple_devops_projects(self):
        issues = [
            {"key": "DEV1-1", "fields": {"project": {"key": "DEV1"}}},
            {"key": "DEVOPS-1", "fields": {"project": {"key": "DEVOPS"}}},
            {"key": "OPS-1", "fields": {"project": {"key": "OPS"}}},
        ]

        filtered = filter_devops_issues(issues, ["DEVOPS", "OPS"])

        assert len(filtered) == 2


class TestDeploymentIssueFiltering:
    def test_filter_deployment_issues_operational_tasks_only(self):
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
                    "issuetype": {"name": "Bug"},
                },
            },
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Operational Task"},
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
        issues = [
            {
                "key": "DEV1-1",
                "fields": {"project": {"key": "DEV1"}, "issuetype": {"name": "Story"}},
            }
        ]

        filtered = filter_deployment_issues(issues, ["DEVOPS"])

        assert len(filtered) == 0


class TestIncidentIssueFiltering:
    def test_filter_incident_issues_production_bugs_only(self):
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},
                },
            },
            {
                "key": "DEV1-2",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "DEV"},
                },
            },
            {
                "key": "DEV1-3",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Story"},
                    "customfield_11309": {"value": "PROD"},
                },
            },
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},
                },
            },
            {
                "key": "DEV1-4",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "PROD"},
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
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": "PROD",
                },
            }
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_11309"
        )

        assert len(filtered) == 1

    def test_filter_incident_issues_case_insensitive(self):
        issues = [
            {
                "key": "DEV1-1",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": {"value": "prod"},
                },
            },
            {
                "key": "DEV1-2",
                "fields": {
                    "project": {"key": "DEV1"},
                    "issuetype": {"name": "Bug"},
                    "customfield_11309": "Prod",
                },
            },
        ]

        filtered = filter_incident_issues(
            issues, ["DEVOPS"], production_environment_field="customfield_11309"
        )

        assert len(filtered) == 2

    def test_filter_incident_issues_custom_environment_field(self):
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
    def test_filter_work_items_default_types(self):
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
                    "issuetype": {"name": "Bug"},
                },
            },
            {
                "key": "DEVOPS-1",
                "fields": {
                    "project": {"key": "DEVOPS"},
                    "issuetype": {"name": "Story"},
                },
            },
        ]

        filtered = filter_work_items(issues, ["DEVOPS"])

        assert len(filtered) == 2
        assert get_issue_type(filtered[0]) in ["Story", "Task"]
        assert get_issue_type(filtered[1]) in ["Story", "Task"]

    def test_filter_work_items_custom_types(self):
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
    def test_get_project_summary_mixed_projects(self):
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
        summary = get_project_summary([], ["DEVOPS"])

        assert summary["total_issues"] == 0
        assert summary["development_issues"] == 0
        assert summary["devops_issues"] == 0
        assert len(summary["projects"]) == 0
        assert len(summary["issue_types"]) == 0
