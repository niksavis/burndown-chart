"""
Unit tests for JIRA Query Builder Module

Tests JQL query modification to include parent issue types.
"""

import pytest

from data.jira.query_builder import (
    _build_issuetype_clause,
    _parse_issue_types,
    build_jql_with_parent_types,
    extract_parent_types_from_config,
)


class TestParseIssueTypes:
    """Test parsing of issue types from JQL clause."""

    def test_simple_types(self):
        """Parse unquoted types."""
        result = _parse_issue_types("Story, Bug, Task")
        assert result == ["Story", "Bug", "Task"]

    def test_quoted_types(self):
        """Parse quoted types."""
        result = _parse_issue_types('"Story", "Bug", "Task"')
        assert result == ["Story", "Bug", "Task"]

    def test_mixed_types(self):
        """Parse mix of quoted and unquoted types."""
        result = _parse_issue_types('"New Feature", Bug, Task')
        assert result == ["New Feature", "Bug", "Task"]

    def test_whitespace(self):
        """Handle extra whitespace."""
        result = _parse_issue_types("  Story  , Bug ,  Task  ")
        assert result == ["Story", "Bug", "Task"]

    def test_empty(self):
        """Handle empty string."""
        result = _parse_issue_types("")
        assert result == []


class TestBuildIssueTypeClause:
    """Test building JQL issuetype clause."""

    def test_simple_types(self):
        """Build clause for simple types."""
        result = _build_issuetype_clause(["Story", "Bug", "Task"])
        assert result == "issuetype in (Story, Bug, Task)"

    def test_types_with_spaces(self):
        """Quote types with spaces."""
        result = _build_issuetype_clause(["Story", "New Feature", "Bug"])
        assert result == 'issuetype in (Story, "New Feature", Bug)'

    def test_empty_list(self):
        """Handle empty list."""
        result = _build_issuetype_clause([])
        assert result == "issuetype in ()"


class TestBuildJQLWithParentTypes:
    """Test JQL query modification."""

    def test_add_single_parent_type(self):
        """Add single parent type to query."""
        jql = "project = PROJ AND issuetype in (Story, Bug)"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert "issuetype in (Story, Bug, Epic)" in result

    def test_add_multiple_parent_types(self):
        """Add multiple parent types to query."""
        jql = "project = PROJ AND issuetype in (Story)"
        result = build_jql_with_parent_types(jql, ["Epic", "Initiative"])
        assert "issuetype in (Story, Epic, Initiative)" in result

    def test_no_modification_when_already_present(self):
        """Don't modify if parent type already in query."""
        jql = "project = PROJ AND issuetype in (Story, Bug, Epic)"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert result == jql

    def test_no_modification_without_type_filter(self):
        """Don't modify if no issuetype clause."""
        jql = "project = PROJ"
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert result == jql

    def test_case_insensitive_matching(self):
        """Match existing types case-insensitively."""
        jql = "project = PROJ AND issuetype in (story, bug)"
        result = build_jql_with_parent_types(jql, ["Story", "Epic"])
        # Should only add Epic (Story already present)
        assert "Epic" in result
        assert result.lower().count("story") == 1  # Not duplicated

    def test_no_parent_types(self):
        """Return unchanged if no parent types provided."""
        jql = "project = PROJ AND issuetype in (Story, Bug)"
        result = build_jql_with_parent_types(jql, [])
        assert result == jql

    def test_empty_jql(self):
        """Handle empty JQL string."""
        result = build_jql_with_parent_types("", ["Epic"])
        assert result == ""

    def test_complex_jql(self):
        """Handle complex JQL with multiple clauses."""
        jql = 'issuesInEpics("key = EPIC-1") AND issuetype in (Story, Bug) AND status != Done'
        result = build_jql_with_parent_types(jql, ["Epic"])
        assert "issuetype in (Story, Bug, Epic)" in result
        assert 'issuesInEpics("key = EPIC-1")' in result
        assert "status != Done" in result

    def test_types_with_spaces(self):
        """Handle parent types with spaces."""
        jql = "project = PROJ AND issuetype in (Story)"
        result = build_jql_with_parent_types(jql, ["New Feature"])
        assert '"New Feature"' in result or "New Feature" in result


class TestExtractParentTypesFromConfig:
    """Test configuration extraction."""

    def test_valid_config(self):
        """Extract parent types from valid config."""
        config = {
            "field_mappings": {
                "general": {"parent_issue_types": ["Epic", "Initiative"]}
            }
        }
        result = extract_parent_types_from_config(config)
        assert result == ["Epic", "Initiative"]

    def test_empty_config(self):
        """Handle empty config."""
        config = {}
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_missing_field_mappings(self):
        """Handle missing field_mappings."""
        config = {"other_key": "value"}
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_non_list_value(self):
        """Handle non-list value."""
        config = {
            "field_mappings": {
                "general": {
                    "parent_issue_types": "Epic"  # String instead of list
                }
            }
        }
        result = extract_parent_types_from_config(config)
        assert result == []

    def test_filters_empty_strings(self):
        """Filter out empty strings and None."""
        config = {
            "field_mappings": {
                "general": {"parent_issue_types": ["Epic", "", None, "Initiative"]}
            }
        }
        result = extract_parent_types_from_config(config)
        assert result == ["Epic", "Initiative"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
