"""Unit tests for VariableExtractor.

Tests cover all extraction source types, filter evaluation, priority fallback,
and edge cases using mock JIRA issue data.
"""

import pytest
from typing import Dict, Any

from data.variable_mapping.models import (
    VariableMapping,
    VariableMappingCollection,
    SourceRule,
    MappingFilter,
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
)
from data.variable_mapping.extractor import VariableExtractor


@pytest.fixture
def sample_issue() -> Dict[str, Any]:
    """Sample JIRA issue for testing."""
    return {
        "key": "TEST-123",
        "fields": {
            "project": {"key": "TEST", "name": "Test Project"},
            "issuetype": {"name": "Story"},
            "status": {"name": "Done"},
            "created": "2025-01-01T10:00:00.000Z",
            "resolutiondate": "2025-01-15T14:30:00.000Z",
            "customfield_10001": "Production",
            "customfield_10002": 5,  # Story points
            "customfield_10003": True,  # Deployment successful
            "fixVersions": [
                {"name": "v1.0", "releaseDate": "2025-01-10"},
                {"name": "v1.1", "releaseDate": "2025-01-20"},
            ],
        },
    }


@pytest.fixture
def sample_changelog() -> list:
    """Sample JIRA changelog for testing."""
    return [
        {
            "created": "2025-01-05T09:00:00.000Z",
            "items": [
                {"field": "status", "fromString": "To Do", "toString": "In Progress"}
            ],
        },
        {
            "created": "2025-01-10T15:00:00.000Z",
            "items": [
                {"field": "status", "fromString": "In Progress", "toString": "Done"}
            ],
        },
        {
            "created": "2025-01-12T10:00:00.000Z",
            "items": [
                {
                    "field": "customfield_10003",
                    "fromString": "false",
                    "toString": "true",
                }
            ],
        },
    ]


class TestFieldValueExtraction:
    """Test direct field value extraction."""

    def test_extract_simple_field_value(self, sample_issue):
        """Test extracting a simple field value."""
        mapping = VariableMapping(
            variable_name="issue_status",
            variable_type="category",
            metric_category="common",
            description="Current issue status",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="status.name"),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"issue_status": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("issue_status", sample_issue)

        assert result["found"] is True
        assert result["value"] == "Done"
        assert result["source_priority"] == 1
        assert result["source_type"] == "field_value"

    def test_extract_custom_field(self, sample_issue):
        """Test extracting a custom field value."""
        mapping = VariableMapping(
            variable_name="story_points",
            variable_type="number",
            metric_category="flow",
            description="Story points for the issue",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10002",
                        value_type="number",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"story_points": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("story_points", sample_issue)

        assert result["found"] is True
        assert result["value"] == 5

    def test_extract_missing_field(self, sample_issue):
        """Test extracting a non-existent field."""
        mapping = VariableMapping(
            variable_name="missing_field",
            variable_type="category",
            metric_category="common",
            description="Non-existent field",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value", field="nonexistent.field"
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"missing_field": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("missing_field", sample_issue)

        assert result["found"] is False


class TestFieldValueMatchExtraction:
    """Test conditional field value matching."""

    def test_extract_equals_match(self, sample_issue):
        """Test equals operator matching."""
        mapping = VariableMapping(
            variable_name="is_done",
            variable_type="boolean",
            metric_category="common",
            description="Whether issue is done",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="equals",
                        value="Done",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"is_done": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("is_done", sample_issue)

        assert result["found"] is True
        assert result["value"] is True

    def test_extract_in_operator_match(self, sample_issue):
        """Test 'in' operator matching with list."""
        mapping = VariableMapping(
            variable_name="is_completed_state",
            variable_type="boolean",
            metric_category="flow",
            description="Whether issue is in completed states",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="in",
                        value=["Done", "Closed", "Resolved"],
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"is_completed_state": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("is_completed_state", sample_issue)

        assert result["found"] is True
        assert result["value"] is True

    def test_extract_not_equals_match(self, sample_issue):
        """Test not_equals operator."""
        mapping = VariableMapping(
            variable_name="is_not_todo",
            variable_type="boolean",
            metric_category="common",
            description="Whether issue is not To Do",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueMatchSource(
                        type="field_value_match",
                        field="status.name",
                        operator="not_equals",
                        value="To Do",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"is_not_todo": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("is_not_todo", sample_issue)

        assert result["found"] is True
        assert result["value"] is True


class TestChangelogEventExtraction:
    """Test changelog event detection."""

    def test_extract_transition_event(self, sample_issue, sample_changelog):
        """Test detecting a specific status transition."""
        mapping = VariableMapping(
            variable_name="was_in_progress",
            variable_type="boolean",
            metric_category="flow",
            description="Whether issue transitioned to In Progress",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogEventSource(
                        type="changelog_event",
                        field="status",
                        condition={"transition_to": "In Progress"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"was_in_progress": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "was_in_progress", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] is True

    def test_extract_specific_transition(self, sample_issue, sample_changelog):
        """Test detecting a specific from->to transition."""
        mapping = VariableMapping(
            variable_name="done_from_in_progress",
            variable_type="boolean",
            metric_category="flow",
            description="Whether issue went Done from In Progress",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogEventSource(
                        type="changelog_event",
                        field="status",
                        condition={
                            "transition_from": "In Progress",
                            "transition_to": "Done",
                        },
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(
            mappings={"done_from_in_progress": mapping}
        )
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "done_from_in_progress", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] is True

    def test_extract_non_existent_transition(self, sample_issue, sample_changelog):
        """Test transition that never occurred."""
        mapping = VariableMapping(
            variable_name="was_blocked",
            variable_type="boolean",
            metric_category="flow",
            description="Whether issue was blocked",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogEventSource(
                        type="changelog_event",
                        field="status",
                        condition={"transition_to": "Blocked"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"was_blocked": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "was_blocked", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] is False


class TestChangelogTimestampExtraction:
    """Test changelog timestamp extraction."""

    def test_extract_transition_timestamp(self, sample_issue, sample_changelog):
        """Test extracting timestamp when transition occurred."""
        mapping = VariableMapping(
            variable_name="started_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work started",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "In Progress"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"started_timestamp": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "started_timestamp", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] == "2025-01-05T09:00:00.000Z"

    def test_extract_specific_transition_timestamp(
        self, sample_issue, sample_changelog
    ):
        """Test extracting timestamp for specific from->to transition."""
        mapping = VariableMapping(
            variable_name="completed_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work completed",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={
                            "transition_from": "In Progress",
                            "transition_to": "Done",
                        },
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(
            mappings={"completed_timestamp": mapping}
        )
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "completed_timestamp", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] == "2025-01-10T15:00:00.000Z"


class TestFixVersionExtraction:
    """Test fixVersion release date extraction."""

    def test_extract_first_release_date(self, sample_issue):
        """Test extracting first release date."""
        mapping = VariableMapping(
            variable_name="release_date",
            variable_type="datetime",
            metric_category="dora",
            description="Release date",
            sources=[
                SourceRule(
                    priority=1,
                    source=FixVersionSource(
                        type="fixversion_releasedate",
                        field="fixVersions",
                        selector="first",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"release_date": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("release_date", sample_issue)

        assert result["found"] is True
        assert result["value"] == "2025-01-10"

    def test_extract_last_release_date(self, sample_issue):
        """Test extracting last release date."""
        mapping = VariableMapping(
            variable_name="latest_release",
            variable_type="datetime",
            metric_category="dora",
            description="Latest release date",
            sources=[
                SourceRule(
                    priority=1,
                    source=FixVersionSource(
                        type="fixversion_releasedate",
                        field="fixVersions",
                        selector="last",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"latest_release": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("latest_release", sample_issue)

        assert result["found"] is True
        assert result["value"] == "2025-01-20"

    def test_extract_all_release_dates(self, sample_issue):
        """Test extracting all release dates."""
        mapping = VariableMapping(
            variable_name="all_releases",
            variable_type="datetime",
            metric_category="dora",
            description="All release dates",
            sources=[
                SourceRule(
                    priority=1,
                    source=FixVersionSource(
                        type="fixversion_releasedate",
                        field="fixVersions",
                        selector="all",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"all_releases": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("all_releases", sample_issue)

        assert result["found"] is True
        assert result["value"] == ["2025-01-10", "2025-01-20"]


class TestCalculatedExtraction:
    """Test calculated/derived value extraction."""

    def test_extract_timestamp_diff(self, sample_issue):
        """Test calculating difference between timestamps."""
        mapping = VariableMapping(
            variable_name="cycle_time",
            variable_type="duration",
            metric_category="flow",
            description="Time from created to resolved",
            sources=[
                SourceRule(
                    priority=1,
                    source=CalculatedSource(
                        type="calculated",
                        calculation="timestamp_diff",
                        inputs={"start": "created", "end": "resolutiondate"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"cycle_time": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("cycle_time", sample_issue)

        assert result["found"] is True
        # Difference should be ~14 days 4.5 hours = ~1,230,000 seconds
        assert result["value"] > 1_200_000
        assert result["value"] < 1_300_000

    def test_extract_transition_count(self, sample_issue, sample_changelog):
        """Test counting transitions."""
        mapping = VariableMapping(
            variable_name="status_changes",
            variable_type="count",
            metric_category="flow",
            description="Number of status changes",
            sources=[
                SourceRule(
                    priority=1,
                    source=CalculatedSource(
                        type="calculated",
                        calculation="count_transitions",
                        inputs={"field": "status"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"status_changes": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "status_changes", sample_issue, sample_changelog
        )

        assert result["found"] is True
        assert result["value"] == 2  # Two status transitions in sample changelog


class TestFilterEvaluation:
    """Test conditional filter evaluation."""

    def test_filter_by_project(self, sample_issue):
        """Test filtering by project key."""
        mapping = VariableMapping(
            variable_name="test_status",
            variable_type="category",
            metric_category="common",
            description="Status for TEST project only",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="status.name"),
                    filters=MappingFilter(project=["TEST"]),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"test_status": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("test_status", sample_issue)

        assert result["found"] is True
        assert result["value"] == "Done"

    def test_filter_by_project_excluded(self, sample_issue):
        """Test issue excluded by project filter."""
        mapping = VariableMapping(
            variable_name="other_status",
            variable_type="category",
            metric_category="common",
            description="Status for OTHER project only",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="status.name"),
                    filters=MappingFilter(project=["OTHER"]),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"other_status": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("other_status", sample_issue)

        assert result["found"] is False

    def test_filter_by_issuetype(self, sample_issue):
        """Test filtering by issue type."""
        mapping = VariableMapping(
            variable_name="story_status",
            variable_type="category",
            metric_category="common",
            description="Status for stories only",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="status.name"),
                    filters=MappingFilter(issuetype=["Story"]),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"story_status": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("story_status", sample_issue)

        assert result["found"] is True

    def test_filter_by_environment(self, sample_issue):
        """Test filtering by environment field."""
        mapping = VariableMapping(
            variable_name="prod_status",
            variable_type="category",
            metric_category="dora",
            description="Status for production issues",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(type="field_value", field="status.name"),
                    filters=MappingFilter(
                        environment_field="customfield_10001",
                        environment_value="Production",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"prod_status": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("prod_status", sample_issue)

        assert result["found"] is True
        assert result["value"] == "Done"


class TestPriorityFallback:
    """Test priority-ordered fallback behavior."""

    def test_fallback_to_second_source(self, sample_issue):
        """Test falling back to second source when first fails."""
        mapping = VariableMapping(
            variable_name="completion_date",
            variable_type="datetime",
            metric_category="flow",
            description="Completion date from multiple sources",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10099",  # Non-existent field
                    ),
                ),
                SourceRule(
                    priority=2,
                    source=FieldValueSource(type="field_value", field="resolutiondate"),
                ),
            ],
        )
        collection = VariableMappingCollection(mappings={"completion_date": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("completion_date", sample_issue)

        assert result["found"] is True
        assert result["value"] == "2025-01-15T14:30:00.000Z"
        assert result["source_priority"] == 2

    def test_fallback_source_used(self, sample_issue):
        """Test using fallback source when all regular sources fail."""
        mapping = VariableMapping(
            variable_name="any_date",
            variable_type="datetime",
            metric_category="common",
            description="Any date with fallback to created",
            sources=[
                SourceRule(
                    priority=1,
                    source=FieldValueSource(
                        type="field_value",
                        field="customfield_10099",  # Non-existent
                    ),
                )
            ],
            fallback_source=SourceRule(
                priority=99,
                source=FieldValueSource(type="field_value", field="created"),
            ),
        )
        collection = VariableMappingCollection(mappings={"any_date": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("any_date", sample_issue)

        assert result["found"] is True
        assert result["value"] == "2025-01-01T10:00:00.000Z"
        assert result["from_fallback"] is True


class TestExtractAllVariables:
    """Test batch extraction of all variables."""

    def test_extract_all_by_category(self, sample_issue):
        """Test extracting all variables for a category."""
        mappings = {
            "issue_status": VariableMapping(
                variable_name="issue_status",
                variable_type="category",
                metric_category="common",
                description="Status",
                sources=[
                    SourceRule(
                        priority=1,
                        source=FieldValueSource(
                            type="field_value", field="status.name"
                        ),
                    )
                ],
            ),
            "story_points": VariableMapping(
                variable_name="story_points",
                variable_type="number",
                metric_category="flow",
                description="Story points",
                sources=[
                    SourceRule(
                        priority=1,
                        source=FieldValueSource(
                            type="field_value", field="customfield_10002"
                        ),
                    )
                ],
            ),
        }
        collection = VariableMappingCollection(mappings=mappings)
        extractor = VariableExtractor(collection)

        result = extractor.extract_all_variables(sample_issue, category="flow")

        assert "story_points" in result
        assert result["story_points"] == 5
        assert "issue_status" not in result  # Different category


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_extract_non_existent_variable(self, sample_issue):
        """Test extracting a variable that isn't configured."""
        collection = VariableMappingCollection()
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("non_existent", sample_issue)

        assert result["found"] is False
        assert "error" in result

    def test_extract_with_no_changelog(self, sample_issue):
        """Test changelog extraction with no changelog provided."""
        mapping = VariableMapping(
            variable_name="started_date",
            variable_type="datetime",
            metric_category="flow",
            description="When started",
            sources=[
                SourceRule(
                    priority=1,
                    source=ChangelogTimestampSource(
                        type="changelog_timestamp",
                        field="status",
                        condition={"transition_to": "In Progress"},
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"started_date": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable(
            "started_date", sample_issue, changelog=None
        )

        assert result["found"] is False

    def test_extract_with_empty_fixversions(self):
        """Test fixVersion extraction with no fixVersions."""
        issue = {"key": "TEST-456", "fields": {"fixVersions": []}}
        mapping = VariableMapping(
            variable_name="release_date",
            variable_type="datetime",
            metric_category="dora",
            description="Release date",
            sources=[
                SourceRule(
                    priority=1,
                    source=FixVersionSource(
                        type="fixversion_releasedate",
                        field="fixVersions",
                        selector="first",
                    ),
                )
            ],
        )
        collection = VariableMappingCollection(mappings={"release_date": mapping})
        extractor = VariableExtractor(collection)

        result = extractor.extract_variable("release_date", issue)

        assert result["found"] is False
