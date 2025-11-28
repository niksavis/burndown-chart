"""Unit tests for namespace parser.

Tests namespace syntax parsing and translation to SourceRule objects.

Reference: specs/namespace-syntax-analysis.md
"""

import pytest

from data.namespace_parser import (
    NamespaceParseError,
    NamespaceParser,
    ParsedNamespace,
    namespace_to_source_rule,
    parse_namespace,
    validate_namespace_syntax,
)
from data.variable_mapping.models import (
    ChangelogEventSource,
    ChangelogTimestampSource,
    FieldValueSource,
    MappingFilter,
)


class TestNamespaceParserBasicParsing:
    """Test basic parsing of namespace paths."""

    def test_parse_simple_field_wildcard_project(self):
        """Test parsing simple field with wildcard project."""
        parser = NamespaceParser()
        parsed = parser.parse("*.created")

        assert parsed.project_filter == ["*"]
        assert parsed.field_name == "created"
        assert parsed.property_path is None
        assert parsed.changelog_value is None
        assert parsed.extractor is None
        assert parsed.value_type == "datetime"

    def test_parse_simple_field_specific_project(self):
        """Test parsing field with specific project."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps.customfield_10100")

        assert parsed.project_filter == ["DevOps"]
        assert parsed.field_name == "customfield_10100"
        assert parsed.property_path is None
        assert parsed.value_type == "string"

    def test_parse_field_with_property(self):
        """Test parsing field with object property."""
        parser = NamespaceParser()
        parsed = parser.parse("*.status.name")

        assert parsed.project_filter == ["*"]
        assert parsed.field_name == "status"
        assert parsed.property_path == "name"
        assert parsed.value_type == "string"

    def test_parse_nested_property_path(self):
        """Test parsing field with nested property path."""
        parser = NamespaceParser()
        parsed = parser.parse("*.status.statusCategory.key")

        assert parsed.field_name == "status"
        assert parsed.property_path == "statusCategory.key"
        assert parsed.value_type == "string"

    def test_parse_multi_project_filter(self):
        """Test parsing with multiple projects (pipe delimiter)."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps|Platform.customfield_10100")

        assert parsed.project_filter == ["DevOps", "Platform"]
        assert parsed.field_name == "customfield_10100"

    def test_parse_multi_project_with_wildcard(self):
        """Test parsing with wildcard in multi-project list."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps|*.resolutiondate")

        assert parsed.project_filter == ["DevOps", "*"]
        assert parsed.field_name == "resolutiondate"


class TestNamespaceParserChangelogSyntax:
    """Test changelog syntax parsing."""

    def test_parse_changelog_timestamp(self):
        """Test parsing changelog with DateTime extractor."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:Deployed.DateTime")

        assert parsed.field_name == "Status"
        assert parsed.changelog_value == "Deployed"
        assert parsed.extractor == "DateTime"
        assert parsed.value_type == "datetime"

    def test_parse_changelog_event(self):
        """Test parsing changelog with Occurred extractor."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:InProgress.Occurred")

        assert parsed.field_name == "Status"
        assert parsed.changelog_value == "InProgress"
        assert parsed.extractor == "Occurred"
        assert parsed.value_type == "boolean"

    def test_parse_changelog_duration(self):
        """Test parsing changelog with Duration extractor."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:Done.Duration")

        assert parsed.field_name == "Status"
        assert parsed.changelog_value == "Done"
        assert parsed.extractor == "Duration"
        assert parsed.value_type == "number"

    def test_parse_changelog_with_spaces_in_value(self):
        """Test parsing changelog with spaces in transition value."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:In Progress.DateTime")

        assert parsed.changelog_value == "In Progress"
        assert parsed.extractor == "DateTime"

    def test_parse_changelog_with_project_filter(self):
        """Test parsing changelog with specific project."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps.Status:Deployed.DateTime")

        assert parsed.project_filter == ["DevOps"]
        assert parsed.field_name == "Status"
        assert parsed.changelog_value == "Deployed"


class TestNamespaceParserValueTypeInference:
    """Test automatic value type inference."""

    def test_datetime_field_inference(self):
        """Test datetime type inference for standard fields."""
        parser = NamespaceParser()

        # Standard datetime fields
        for field in ["created", "updated", "resolutiondate", "duedate"]:
            parsed = parser.parse(f"*.{field}")
            assert parsed.value_type == "datetime", f"Failed for {field}"

    def test_number_field_inference(self):
        """Test number type inference for standard fields."""
        parser = NamespaceParser()

        parsed = parser.parse("*.timeestimate")
        assert parsed.value_type == "number"

    def test_property_type_inference(self):
        """Test type inference from property path."""
        parser = NamespaceParser()

        # String properties
        parsed = parser.parse("*.status.name")
        assert parsed.value_type == "string"

        # ID properties (stored as strings in JIRA)
        parsed = parser.parse("*.status.id")
        assert parsed.value_type == "string"

        # Release date is datetime
        parsed = parser.parse("*.fixVersions.releaseDate")
        assert parsed.value_type == "datetime"

        # Released is boolean
        parsed = parser.parse("*.fixVersions.released")
        assert parsed.value_type == "boolean"

    def test_custom_field_default_type(self):
        """Test custom fields default to string type."""
        parser = NamespaceParser()
        parsed = parser.parse("*.customfield_10100")

        assert parsed.value_type == "string"


class TestNamespaceParserErrorHandling:
    """Test error handling and validation."""

    def test_empty_namespace_raises_error(self):
        """Test empty namespace path raises error."""
        parser = NamespaceParser()

        with pytest.raises(NamespaceParseError, match="cannot be empty"):
            parser.parse("")

        with pytest.raises(NamespaceParseError, match="cannot be empty"):
            parser.parse("   ")

    def test_invalid_syntax_raises_error(self):
        """Test invalid syntax raises error."""
        parser = NamespaceParser()

        # Missing field name
        with pytest.raises(NamespaceParseError, match="Invalid namespace syntax"):
            parser.parse("DevOps.")

        # Invalid characters
        with pytest.raises(NamespaceParseError, match="Invalid namespace syntax"):
            parser.parse("*.field-name")

        # Double dots
        with pytest.raises(NamespaceParseError, match="Invalid namespace syntax"):
            parser.parse("*.field..property")

    def test_invalid_project_key_format(self):
        """Test invalid project key format raises error."""
        parser = NamespaceParser()

        # Lowercase first segment is treated as FIELD NAME, not project key
        # So "devops.field" parses as field="devops" with property="field"
        # This is valid syntax, not an error
        parsed = parser.parse("devops.field")
        assert parsed.field_name == "devops"
        assert parsed.property_path == "field"
        assert parsed.project_filter == ["*"]  # No project filter

        # Project key starting with number should raise error
        with pytest.raises(NamespaceParseError, match="Invalid namespace syntax"):
            parser.parse("1DEVOPS.field")

    def test_validate_namespace_syntax_valid(self):
        """Test syntax validation for valid paths."""
        result = validate_namespace_syntax("*.created")
        assert result["valid"] is True
        assert result["error_message"] == ""

    def test_validate_namespace_syntax_invalid(self):
        """Test syntax validation for invalid paths."""
        result = validate_namespace_syntax("invalid..path")
        assert result["valid"] is False
        error_msg = result["error_message"]
        assert isinstance(error_msg, str) and "Invalid namespace syntax" in error_msg


class TestNamespaceParserSourceRuleTranslation:
    """Test translation from parsed namespace to SourceRule objects."""

    def test_translate_simple_field_to_field_value_source(self):
        """Test translating simple field to FieldValueSource."""
        parser = NamespaceParser()
        parsed = parser.parse("*.created")
        rule = parser.translate_to_source_rule(parsed)

        assert rule.priority == 1
        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "created"
        assert rule.source.value_type == "datetime"
        assert rule.filters is None  # Wildcard project = no filter

    def test_translate_with_project_filter(self):
        """Test translating with project filter."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps.customfield_10100")
        rule = parser.translate_to_source_rule(parsed)

        assert rule.filters is not None
        assert isinstance(rule.filters, MappingFilter)
        assert rule.filters.project == ["DevOps"]

    def test_translate_multi_project_filter(self):
        """Test translating with multiple projects."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps|Platform.resolutiondate")
        rule = parser.translate_to_source_rule(parsed)

        assert rule.filters is not None
        assert rule.filters.project == ["DevOps", "Platform"]

    def test_translate_field_with_property_path(self):
        """Test translating field with property path."""
        parser = NamespaceParser()
        parsed = parser.parse("*.status.name")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "status.name"
        assert rule.source.value_type == "string"

    def test_translate_changelog_timestamp(self):
        """Test translating changelog to ChangelogTimestampSource."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:Deployed.DateTime")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, ChangelogTimestampSource)
        assert rule.source.field == "Status"
        assert rule.source.condition == {"transition_to": "Deployed"}

    def test_translate_changelog_event(self):
        """Test translating changelog to ChangelogEventSource."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:Done.Occurred")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, ChangelogEventSource)
        assert rule.source.field == "Status"
        assert rule.source.condition == {"transition_to": "Done"}

    def test_translate_with_custom_priority(self):
        """Test translating with custom priority."""
        parser = NamespaceParser()
        parsed = parser.parse("*.created")
        rule = parser.translate_to_source_rule(parsed, priority=5)

        assert rule.priority == 5


class TestNamespaceParserMultipleTranslation:
    """Test translating multiple namespace paths."""

    def test_translate_multiple_paths(self):
        """Test translating multiple paths with sequential priorities."""
        parser = NamespaceParser()
        paths = [
            "DevOps.customfield_10100",
            "*.resolutiondate",
            "Platform.Status:Done.DateTime",
        ]
        rules = parser.translate_multiple(paths)

        assert len(rules) == 3
        assert rules[0].priority == 1
        assert rules[1].priority == 2
        assert rules[2].priority == 3

        # Verify first rule
        assert isinstance(rules[0].source, FieldValueSource)
        assert rules[0].filters is not None
        assert rules[0].filters.project == ["DevOps"]

        # Verify second rule
        assert isinstance(rules[1].source, FieldValueSource)
        assert rules[1].source.field == "resolutiondate"
        assert rules[1].filters is None

        # Verify third rule
        assert isinstance(rules[2].source, ChangelogTimestampSource)
        assert rules[2].filters is not None
        assert rules[2].filters.project == ["Platform"]

    def test_translate_multiple_skips_invalid(self):
        """Test translating multiple paths skips invalid syntax."""
        parser = NamespaceParser()
        paths = [
            "*.created",
            "invalid..path",  # Invalid
            "*.status.name",
        ]
        rules = parser.translate_multiple(paths)

        # Should only return 2 valid rules
        assert len(rules) == 2
        assert isinstance(rules[0].source, FieldValueSource)
        assert rules[0].source.field == "created"
        assert isinstance(rules[1].source, FieldValueSource)
        assert rules[1].source.field == "status.name"


class TestNamespaceParserConvenienceFunctions:
    """Test convenience functions for common use cases."""

    def test_parse_namespace_function(self):
        """Test parse_namespace convenience function."""
        parsed = parse_namespace("*.created")

        assert isinstance(parsed, ParsedNamespace)
        assert parsed.field_name == "created"

    def test_namespace_to_source_rule_function(self):
        """Test namespace_to_source_rule convenience function."""
        rule = namespace_to_source_rule("DevOps.status.name", priority=3)

        assert rule.priority == 3
        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "status.name"
        assert rule.filters is not None
        assert rule.filters.project == ["DevOps"]


class TestNamespaceParserRealWorldExamples:
    """Test real-world namespace examples from specification."""

    def test_dora_deployment_timestamp(self):
        """Test DORA deployment timestamp example."""
        parser = NamespaceParser()

        # Traditional approach: DevOps.Status:Deployed.DateTime
        parsed = parser.parse("DevOps.Status:Deployed.DateTime")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, ChangelogTimestampSource)
        assert rule.source.field == "Status"
        assert rule.source.condition == {"transition_to": "Deployed"}
        assert rule.filters is not None
        assert rule.filters.project == ["DevOps"]

    def test_dora_code_commit_date(self):
        """Test DORA code commit date example."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps.customfield_10100")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "customfield_10100"

    def test_cross_project_velocity(self):
        """Test cross-project velocity example."""
        parser = NamespaceParser()
        parsed = parser.parse("DevOps|Platform|Mobile.customfield_10016")
        rule = parser.translate_to_source_rule(parsed)

        assert rule.filters is not None
        assert rule.filters.project == ["DevOps", "Platform", "Mobile"]
        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "customfield_10016"

    def test_release_planning_example(self):
        """Test release planning example."""
        parser = NamespaceParser()
        parsed = parser.parse("*.fixVersions.releaseDate")
        rule = parser.translate_to_source_rule(parsed)

        assert isinstance(rule.source, FieldValueSource)
        assert rule.source.field == "fixVersions.releaseDate"
        assert rule.source.value_type == "datetime"


class TestNamespaceParserEdgeCases:
    """Test edge cases and special scenarios."""

    def test_field_name_with_underscores(self):
        """Test parsing field names with underscores."""
        parser = NamespaceParser()
        parsed = parser.parse("*.custom_field_name")

        assert parsed.field_name == "custom_field_name"

    def test_project_key_with_numbers(self):
        """Test parsing project keys with numbers."""
        parser = NamespaceParser()
        parsed = parser.parse("DEVOPS123.field")

        assert parsed.project_filter == ["DEVOPS123"]

    def test_changelog_value_with_special_characters(self):
        """Test changelog values with special characters."""
        parser = NamespaceParser()
        parsed = parser.parse("*.Status:In-Progress/Review.DateTime")

        assert parsed.changelog_value == "In-Progress/Review"

    def test_no_project_implies_wildcard(self):
        """Test that omitting project defaults to wildcard."""
        parser = NamespaceParser()

        # Without explicit project
        parsed = parser.parse("created")
        assert parsed.project_filter == ["*"]

        # With explicit wildcard
        parsed_explicit = parser.parse("*.created")
        assert parsed_explicit.project_filter == ["*"]

    def test_repr_method(self):
        """Test ParsedNamespace string representation."""
        parsed = ParsedNamespace(
            project_filter=["DevOps"],
            field_name="status",
            property_path="name",
        )

        repr_str = repr(parsed)
        assert "DevOps.status" in repr_str
        assert ".name" in repr_str
