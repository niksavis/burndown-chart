"""Unit tests for variable mapping Pydantic models.

Tests validate:
- Model construction and validation
- Field validators (unique priorities, required fields)
- Helper methods (get_mapping, add_mapping, etc.)
- Serialization/deserialization
- Edge cases and error handling
"""

import pytest
from pydantic import ValidationError
from data.variable_mapping.models import (
    FieldValueSource,
    FieldValueMatchSource,
    ChangelogEventSource,
    ChangelogTimestampSource,
    FixVersionSource,
    CalculatedSource,
    SourceRule,
    MappingFilter,
    VariableMapping,
    VariableMappingCollection,
)


class TestFieldValueSource:
    """Test FieldValueSource model."""

    def test_create_valid_field_value_source(self):
        """Test creating valid field value source."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        assert source.field == "customfield_10100"
        assert source.type == "field_value"
        assert source.value_type == "datetime"

    def test_field_value_source_default_value_type(self):
        """Test default value_type is string."""
        source = FieldValueSource(type="field_value", field="status.name")
        assert source.value_type == "string"


class TestFieldValueMatchSource:
    """Test FieldValueMatchSource model."""

    def test_create_valid_match_source(self):
        """Test creating valid field value match source."""
        source = FieldValueMatchSource(
            type="field_value_match",
            field="status.name",
            operator="equals",
            value="Deployed",
        )
        assert source.field == "status.name"
        assert source.operator == "equals"
        assert source.value == "Deployed"

    def test_match_source_with_in_operator(self):
        """Test match source with 'in' operator and list values."""
        source = FieldValueMatchSource(
            type="field_value_match",
            field="issuetype.name",
            operator="in",
            value=["Bug", "Defect", "Incident"],
        )
        assert source.operator == "in"
        assert source.value == ["Bug", "Defect", "Incident"]


class TestChangelogEventSource:
    """Test ChangelogEventSource model."""

    def test_create_valid_changelog_event(self):
        """Test creating valid changelog event source."""
        source = ChangelogEventSource(
            type="changelog_event", field="status", condition={"transition_to": "Done"}
        )
        assert source.field == "status"
        assert source.condition == {"transition_to": "Done"}


class TestChangelogTimestampSource:
    """Test ChangelogTimestampSource model."""

    def test_create_valid_changelog_timestamp(self):
        """Test creating valid changelog timestamp source."""
        source = ChangelogTimestampSource(
            type="changelog_timestamp",
            field="status",
            condition={"transition_to": "Deployed"},
        )
        assert source.field == "status"
        assert source.condition == {"transition_to": "Deployed"}


class TestFixVersionSource:
    """Test FixVersionSource model."""

    def test_create_valid_fixversion_source(self):
        """Test creating valid fixVersion source with default selector."""
        source = FixVersionSource(type="fixversion_releasedate", selector="first")
        assert source.field == "fixVersions"
        assert source.selector == "first"


class TestCalculatedSource:
    """Test CalculatedSource model."""

    def test_create_valid_calculated_source(self):
        """Test creating valid calculated source."""
        source = CalculatedSource(
            type="calculated",
            calculation="sum_changelog_durations",
            inputs={"field": "status", "statuses": ["In Progress", "In Review"]},
        )
        assert source.calculation == "sum_changelog_durations"
        assert source.inputs["field"] == "status"


class TestMappingFilter:
    """Test MappingFilter model."""

    def test_create_empty_filter(self):
        """Test creating filter with no conditions."""
        filter_obj = MappingFilter()
        assert filter_obj.project is None
        assert filter_obj.issuetype is None

    def test_create_filter_with_project(self):
        """Test creating filter with project condition."""
        filter_obj = MappingFilter(project=["PROJ", "MYPROJECT"])
        assert filter_obj.project == ["PROJ", "MYPROJECT"]


class TestSourceRule:
    """Test SourceRule model."""

    def test_create_source_rule_with_field_value(self):
        """Test creating source rule with FieldValueSource."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule = SourceRule(source=source, priority=1)
        assert rule.priority == 1
        assert isinstance(rule.source, FieldValueSource)
        assert rule.filters is None


class TestVariableMapping:
    """Test VariableMapping model."""

    def test_create_minimal_variable_mapping(self):
        """Test creating variable mapping with minimum required fields."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When deployment occurred",
            sources=[rule],
        )
        assert mapping.variable_name == "deployment_timestamp"
        assert mapping.variable_type == "datetime"
        assert len(mapping.sources) == 1
        assert mapping.required is True  # Default is True

    def test_create_variable_mapping_optional_required(self):
        """Test creating variable mapping with required=False."""
        source = FieldValueSource(
            type="field_value", field="status.name", value_type="boolean"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="deployment_event",
            variable_type="boolean",
            metric_category="dora",
            description="Indicates if deployment occurred",
            sources=[rule],
            required=False,
        )
        assert mapping.required is False
        assert mapping.description == "Indicates if deployment occurred"
        assert mapping.metric_category == "dora"

    def test_variable_mapping_multiple_sources(self):
        """Test variable mapping with multiple sources (priority fallback)."""
        source1 = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        source2 = FieldValueSource(
            type="field_value", field="customfield_10101", value_type="datetime"
        )
        source3 = FieldValueSource(
            type="field_value", field="created", value_type="datetime"
        )

        rule1 = SourceRule(source=source1, priority=1)
        rule2 = SourceRule(source=source2, priority=2)
        rule3 = SourceRule(source=source3, priority=3)

        mapping = VariableMapping(
            variable_name="work_started_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work started",
            sources=[rule1, rule2, rule3],
        )
        assert len(mapping.sources) == 3
        assert mapping.sources[0].priority == 1
        assert mapping.sources[2].priority == 3

    def test_variable_mapping_unique_priorities(self):
        """Test that duplicate priorities are rejected."""
        source1 = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="number"
        )
        source2 = FieldValueSource(
            type="field_value", field="customfield_10101", value_type="number"
        )

        rule1 = SourceRule(source=source1, priority=1)
        rule2 = SourceRule(source=source2, priority=1)  # Duplicate priority

        with pytest.raises(ValidationError) as exc_info:
            VariableMapping(
                variable_name="test_variable",
                variable_type="number",
                metric_category="common",
                description="Test variable",
                sources=[rule1, rule2],
            )

        assert "unique priorities" in str(exc_info.value).lower()

    def test_variable_mapping_empty_sources(self):
        """Test that empty sources list is rejected."""
        with pytest.raises(ValidationError):
            VariableMapping(
                variable_name="test_variable",
                variable_type="number",
                metric_category="common",
                description="Test variable",
                sources=[],
            )


class TestVariableMappingCollection:
    """Test VariableMappingCollection model."""

    def test_create_empty_collection(self):
        """Test creating empty variable mapping collection."""
        collection = VariableMappingCollection(mappings={})
        assert len(collection.mappings) == 0
        assert collection.version == "1.0"

    def test_create_collection_with_mappings(self):
        """Test creating collection with multiple mappings."""
        source1 = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule1 = SourceRule(source=source1, priority=1)
        mapping1 = VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When deployment occurred",
            sources=[rule1],
        )

        source2 = FieldValueSource(
            type="field_value", field="status.name", value_type="boolean"
        )
        rule2 = SourceRule(source=source2, priority=1)
        mapping2 = VariableMapping(
            variable_name="is_completed",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work is completed",
            sources=[rule2],
        )

        collection = VariableMappingCollection(
            mappings={"deployment_timestamp": mapping1, "is_completed": mapping2}
        )
        assert len(collection.mappings) == 2

    def test_get_mapping_by_name(self):
        """Test get_mapping() helper method."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When deployment occurred",
            sources=[rule],
        )

        collection = VariableMappingCollection(
            mappings={"deployment_timestamp": mapping}
        )
        result = collection.get_mapping("deployment_timestamp")
        assert result is not None
        assert result.variable_name == "deployment_timestamp"

    def test_get_mapping_not_found(self):
        """Test get_mapping() returns None for non-existent variable."""
        collection = VariableMappingCollection(mappings={})
        result = collection.get_mapping("nonexistent")
        assert result is None

    def test_add_mapping(self):
        """Test add_mapping() helper method."""
        collection = VariableMappingCollection(mappings={})
        assert len(collection.mappings) == 0

        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="number"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="test_variable",
            variable_type="number",
            metric_category="common",
            description="Test variable",
            sources=[rule],
        )

        collection.add_mapping(mapping)
        assert len(collection.mappings) == 1
        assert collection.get_mapping("test_variable") is not None

    def test_get_mappings_by_category(self):
        """Test get_mappings_by_category() helper method."""
        # Create DORA mapping
        source1 = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule1 = SourceRule(source=source1, priority=1)
        dora_mapping = VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When deployment occurred",
            sources=[rule1],
        )

        # Create Flow mapping
        source2 = FieldValueSource(
            type="field_value", field="status.name", value_type="boolean"
        )
        rule2 = SourceRule(source=source2, priority=1)
        flow_mapping = VariableMapping(
            variable_name="is_completed",
            variable_type="boolean",
            metric_category="flow",
            description="Whether work is completed",
            sources=[rule2],
        )

        # Create Common mapping
        source3 = FieldValueSource(
            type="field_value", field="created", value_type="datetime"
        )
        rule3 = SourceRule(source=source3, priority=1)
        common_mapping = VariableMapping(
            variable_name="created_date",
            variable_type="datetime",
            metric_category="common",
            description="When issue was created",
            sources=[rule3],
        )

        collection = VariableMappingCollection(
            mappings={
                "deployment_timestamp": dora_mapping,
                "is_completed": flow_mapping,
                "created_date": common_mapping,
            }
        )

        # Test filtering by category
        dora_results = collection.get_mappings_by_category("dora")
        assert len(dora_results) == 1
        assert "deployment_timestamp" in dora_results

        flow_results = collection.get_mappings_by_category("flow")
        assert len(flow_results) == 1
        assert "is_completed" in flow_results

    def test_get_required_mappings(self):
        """Test get_required_mappings() helper method."""
        # Create required mapping
        source1 = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule1 = SourceRule(source=source1, priority=1)
        required_mapping = VariableMapping(
            variable_name="deployment_timestamp",
            variable_type="datetime",
            metric_category="dora",
            description="When deployment occurred",
            sources=[rule1],
            required=True,
        )

        # Create optional mapping
        source2 = FieldValueSource(
            type="field_value", field="status.name", value_type="boolean"
        )
        rule2 = SourceRule(source=source2, priority=1)
        optional_mapping = VariableMapping(
            variable_name="deployment_event",
            variable_type="boolean",
            metric_category="dora",
            description="Whether deployment occurred",
            sources=[rule2],
            required=False,
        )

        collection = VariableMappingCollection(
            mappings={
                "deployment_timestamp": required_mapping,
                "deployment_event": optional_mapping,
            }
        )

        # Test filtering by required flag
        required_results = collection.get_required_mappings()
        assert len(required_results) == 1
        assert "deployment_timestamp" in required_results

    def test_remove_mapping(self):
        """Test remove_mapping() helper method."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="test_variable",
            variable_type="datetime",
            metric_category="common",
            description="Test variable",
            sources=[rule],
        )

        collection = VariableMappingCollection(mappings={"test_variable": mapping})
        assert len(collection.mappings) == 1

        # Remove existing mapping
        result = collection.remove_mapping("test_variable")
        assert result is True
        assert len(collection.mappings) == 0

        # Try to remove non-existent mapping
        result = collection.remove_mapping("nonexistent")
        assert result is False

    def test_collection_serialization(self):
        """Test serialization to dict."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="number"
        )
        rule = SourceRule(source=source, priority=1)
        mapping = VariableMapping(
            variable_name="test_variable",
            variable_type="number",
            metric_category="common",
            description="Test variable",
            sources=[rule],
        )

        collection = VariableMappingCollection(
            mappings={"test_variable": mapping}, version="1.0"
        )
        data = collection.model_dump()
        assert data["version"] == "1.0"
        assert "test_variable" in data["mappings"]
        assert data["mappings"]["test_variable"]["variable_name"] == "test_variable"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_variable_mapping_with_all_source_types(self):
        """Test variable mapping with all 6 source types."""
        sources = [
            SourceRule(
                source=FieldValueSource(
                    type="field_value", field="customfield_10100", value_type="datetime"
                ),
                priority=1,
            ),
            SourceRule(
                source=FieldValueMatchSource(
                    type="field_value_match",
                    field="status.name",
                    operator="equals",
                    value="Deployed",
                ),
                priority=2,
            ),
            SourceRule(
                source=ChangelogEventSource(
                    type="changelog_event",
                    field="status",
                    condition={"transition_to": "Done"},
                ),
                priority=3,
            ),
            SourceRule(
                source=ChangelogTimestampSource(
                    type="changelog_timestamp",
                    field="status",
                    condition={"transition_to": "Deployed"},
                ),
                priority=4,
            ),
            SourceRule(
                source=FixVersionSource(
                    type="fixversion_releasedate", selector="first"
                ),
                priority=5,
            ),
            SourceRule(
                source=CalculatedSource(
                    type="calculated",
                    calculation="sum_changelog_durations",
                    inputs={
                        "field": "status",
                        "from_status": "In Progress",
                        "to_status": "Done",
                    },
                ),
                priority=6,
            ),
        ]

        mapping = VariableMapping(
            variable_name="complex_variable",
            variable_type="duration",
            metric_category="flow",
            description="Complex multi-source variable",
            sources=sources,
        )
        assert len(mapping.sources) == 6

    def test_complex_filter_combinations(self):
        """Test source rule with complex filter combinations."""
        source = FieldValueSource(
            type="field_value", field="customfield_10100", value_type="datetime"
        )
        filter_obj = MappingFilter(
            project=["PROJ"],
            issuetype=["Bug"],
            environment_field="customfield_10200",
            environment_value="production",
            custom_jql='labels = "critical" AND priority = "High"',
        )
        rule = SourceRule(source=source, priority=1, filters=filter_obj)

        assert rule.filters is not None
        assert rule.filters.project == ["PROJ"]
        assert rule.filters.issuetype == ["Bug"]
        assert rule.filters.environment_field == "customfield_10200"
        assert rule.filters.environment_value == "production"
        assert rule.filters.custom_jql is not None
        assert "critical" in rule.filters.custom_jql

    def test_round_trip_serialization(self):
        """Test complete serialization round-trip."""
        # Create complex mapping
        source = ChangelogTimestampSource(
            type="changelog_timestamp",
            field="status",
            condition={"transition_from": "In Progress", "transition_to": "Done"},
        )
        filter_obj = MappingFilter(project=["PROJ"], issuetype=["Story"])
        rule = SourceRule(source=source, priority=1, filters=filter_obj)
        mapping = VariableMapping(
            variable_name="completion_timestamp",
            variable_type="datetime",
            metric_category="flow",
            description="When work was completed",
            sources=[rule],
            required=True,
        )
        collection = VariableMappingCollection(
            mappings={"completion_timestamp": mapping}
        )

        # Serialize to dict
        data = collection.model_dump()

        # Deserialize back
        restored = VariableMappingCollection(**data)

        # Verify equality
        assert restored.version == collection.version
        assert len(restored.mappings) == len(collection.mappings)
        assert "completion_timestamp" in restored.mappings
        restored_mapping = restored.mappings["completion_timestamp"]
        assert restored_mapping.variable_name == mapping.variable_name
        assert restored_mapping.sources[0].priority == rule.priority
        assert isinstance(restored_mapping.sources[0].source, ChangelogTimestampSource)
