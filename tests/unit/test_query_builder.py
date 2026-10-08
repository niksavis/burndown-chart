import pytest

from data.jira.query_builder import (
    _build_issuetype_clause,
    _parse_issue_types,
    build_jql_with_parent_types,
    extract_parent_types_from_config,
)


class TestParseIssueTypes:
    def test_simple_types(self):
        result = _parse_issue_types("Story, Bug, Task")
        assert result == ["Story", "Bug", "Task"]

    def test_quoted_types(self):
        result = _parse_issue_types('"Story", "Bug", "Task"')
        assert result == ["Story", "Bug", "Task"]

    def test_mixed_types(self):
        result = _parse_issue_types('"New Feature", Bug, Task')
        assert result == ["New Feature", "Bug", "Task"]

    def test_whitespace(self):
        result = _parse_issue_types("  Story  , Bug ,  Task  ")
        assert result == ["Story", "Bug", "Task"]

    def test_empty(self):
        result = _parse_issue_types("")
        assert result == []


class TestBuildIssueTypeClause:
    def test_simple_types(self):
        result = _build_issuetype_clause(["Story", "Bug", "Task"])
        assert result == "issuetype in (Story, Bug, Task)"

    def test_types_with_spaces(self):
        result = _build_issuetype_clause(["Story", "New Feature", "Bug"])
        assert result == 'issuetype in (Story, "New Feature", Bug)'

    def test_empty_list(self):
        result = _build_issuetype_clause([])
        assert result == "issuetype in ()"


class TestBuildJQLWithParentTypes:
    def test_add_single_parent_type(self):
        jql = "project = PROJ AND issuetype in (Story, Bug)"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert "issuetype in (Story, Bug, Epic)" in result

    def test_add_multiple_parent_types(self):
        jql = "project = PROJ AND issuetype in (Story)"
        result = build_jql_with_parent_types(jql, ["Epic", "Initiative"])
        assert "issuetype in (Story, Epic, Initiative)" in result

    def test_no_modification_when_already_present(self):
        jql = "project = PROJ AND issuetype in (Story, Bug, Epic)"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert result == jql

    def test_no_modification_without_type_filter(self):
        jql = "project = PROJ"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert result == jql

    def test_case_insensitive_matching(self):
        jql = "project = PROJ AND issuetype in (story, bug)"
        result = build_jql_with_parent_types(jql, ["Story", "Epic"])
        assert "Epic" in result
        assert result.lower().count("story") == 1

    def test_no_parent_types(self):
        jql = "project = PROJ AND issuetype in (Story, Bug)"
        result = build_jql_with_parent_types(jql, [])
        assert result == jql

    def test_empty_jql(self):
        result = build_jql_with_parent_types("", ["Epic"])
        assert result == ""

    def test_complex_jql(self):
        jql = (
            'issuesInEpics("key = EPIC-1") AND issuetype in (Story, Bug) '
            "AND status != Done"
        )
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert "issuetype in (Story, Bug, Epic)" in result
        assert 'issuesInEpics("key = EPIC-1")' in result
        assert "status != Done" in result

    def test_types_with_spaces(self):
        jql = "project = PROJ AND issuetype in (Story)"
        result = build_jql_with_parent_types(jql, ["New Feature"])
        assert '"New Feature"' in result or "New Feature" in result


class TestExtractParentTypesFromConfig:
    def test_valid_config(self):
        config = {
            "field_mappings": {
                "general": {"parent_issue_types": ["Epic", "Initiative"]}
            }
        }
        result = extract_parent_types_from_config(config)
        assert result == ["Epic", "Initiative"]

    def test_empty_config(self):
        config = {}
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_missing_field_mappings(self):
        config = {"other_key": "value"}
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_non_list_value(self):
        config = {"field_mappings": {"general": {"parent_issue_types": "Epic"}}}
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_filters_empty_strings(self):
        config = {
            "field_mappings": {
                "general": {"parent_issue_types": ["Epic", "", None, "Initiative"]}
            }
        }
        result = extract_parent_types_from_config(config)
        assert result == ["Epic", "Initiative"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
