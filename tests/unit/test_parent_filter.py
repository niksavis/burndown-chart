import pytest

from data.jira.parent_filter import (
    extract_parent_types_from_issues,
    filter_out_parent_types,
)


class TestFilterOutParentTypes:
    def test_filter_epic_from_mixed_issues(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "Task"}}, "key": "PROJ-2"},
            {"fields": {"issuetype": {"name": "Bug"}}, "key": "PROJ-3"},
        ]

        result = filter_out_parent_types(issues, ["Epic"])

        assert len(result) == 3
        assert all(issue["fields"]["issuetype"]["name"] != "Epic" for issue in result)
        assert result[0]["key"] == "PROJ-1"
        assert result[1]["key"] == "PROJ-2"
        assert result[2]["key"] == "PROJ-3"

    def test_filter_multiple_parent_types(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "Initiative"}}, "key": "INIT-1"},
            {"fields": {"issuetype": {"name": "Task"}}, "key": "PROJ-2"},
        ]

        result = filter_out_parent_types(issues, ["Epic", "Initiative"])

        assert len(result) == 2
        assert result[0]["key"] == "PROJ-1"
        assert result[1]["key"] == "PROJ-2"

    def test_case_insensitive_filtering(self):
        issues = [
            {"fields": {"issuetype": {"name": "EPIC"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "epic"}}, "key": "EPIC-2"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-3"},
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
        ]

        result = filter_out_parent_types(issues, ["Epic"])

        assert len(result) == 1
        assert result[0]["key"] == "PROJ-1"

    def test_flat_format_issues(self):
        issues = [
            {"issue_type": "Story", "key": "PROJ-1"},
            {"issue_type": "Epic", "key": "EPIC-1"},
            {"issue_type": "Task", "key": "PROJ-2"},
        ]

        result = filter_out_parent_types(issues, ["Epic"])

        assert len(result) == 2
        assert result[0]["key"] == "PROJ-1"
        assert result[1]["key"] == "PROJ-2"

    def test_empty_parent_types_list(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
        ]

        result = filter_out_parent_types(issues, [])

        assert len(result) == 2
        assert result == issues

    def test_no_parent_types_in_list(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Task"}}, "key": "PROJ-2"},
            {"fields": {"issuetype": {"name": "Bug"}}, "key": "PROJ-3"},
        ]

        result = filter_out_parent_types(issues, ["Epic", "Initiative"])

        assert len(result) == 3
        assert result == issues

    def test_all_issues_are_parents(self):
        issues = [
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "Initiative"}}, "key": "INIT-1"},
        ]

        result = filter_out_parent_types(issues, ["Epic", "Initiative"])

        assert len(result) == 0

    def test_malformed_issue_included_with_warning(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"key": "BAD-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
        ]

        result = filter_out_parent_types(issues, ["Epic"])

        assert len(result) == 2
        assert result[0]["key"] == "PROJ-1"
        assert result[1]["key"] == "BAD-1"

    def test_parent_types_with_spaces(self):
        issues = [
            {"fields": {"issuetype": {"name": "New Feature"}}, "key": "FEAT-1"},
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
        ]

        result = filter_out_parent_types(issues, ["New Feature"])

        assert len(result) == 1
        assert result[0]["key"] == "PROJ-1"


class TestExtractParentTypesFromIssues:
    def test_extract_unique_types(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-2"},
            {"fields": {"issuetype": {"name": "Task"}}, "key": "PROJ-3"},
        ]

        result = extract_parent_types_from_issues(issues)

        assert len(result) == 3
        type_names = [t["name"] for t in result]
        assert "Epic" in type_names
        assert "Story" in type_names
        assert "Task" in type_names

    def test_sorted_alphabetically(self):
        issues = [
            {"fields": {"issuetype": {"name": "Task"}}, "key": "PROJ-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
            {"fields": {"issuetype": {"name": "Bug"}}, "key": "PROJ-2"},
        ]

        result = extract_parent_types_from_issues(issues)

        assert result[0]["name"] == "Bug"
        assert result[1]["name"] == "Epic"
        assert result[2]["name"] == "Task"

    def test_flat_format(self):
        issues = [
            {"issue_type": "Story", "key": "PROJ-1"},
            {"issue_type": "Epic", "key": "EPIC-1"},
        ]

        result = extract_parent_types_from_issues(issues)

        assert len(result) == 2
        type_names = [t["name"] for t in result]
        assert "Epic" in type_names
        assert "Story" in type_names

    def test_empty_list(self):
        result = extract_parent_types_from_issues([])
        assert result == []

    def test_malformed_issues_skipped(self):
        issues = [
            {"fields": {"issuetype": {"name": "Story"}}, "key": "PROJ-1"},
            {"key": "BAD-1"},
            {"fields": {"issuetype": {"name": "Epic"}}, "key": "EPIC-1"},
        ]

        result = extract_parent_types_from_issues(issues)

        assert len(result) == 2
        type_names = [t["name"] for t in result]
        assert "Story" in type_names
        assert "Epic" in type_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
