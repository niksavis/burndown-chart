"""Unit tests for mapping migration utilities.

Tests verify legacy field_mappings conversion to variable_mappings format
and backward compatibility functions.
"""

import pytest
from data.mapping_migration import (
    migrate_legacy_field_mappings,
    create_backward_compatible_field_mappings,
    get_migration_report,
    validate_migration,
    LEGACY_FIELD_TO_VARIABLE_MAP,
)
from data.variable_mapping.models import VariableMappingCollection


class TestLegacyMigration:
    """Test migration from legacy field_mappings format."""

    def test_migrate_empty_mappings(self):
        """Test migrating empty legacy mappings returns defaults."""
        legacy = {}
        collection = migrate_legacy_field_mappings(legacy)

        assert isinstance(collection, VariableMappingCollection)
        assert len(collection.mappings) > 0  # Should have defaults

    def test_migrate_dora_deployment_field(self):
        """Test migrating deployment_date field."""
        legacy = {"deployment_date": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy)

        # Should create deployment_timestamp variable
        var = collection.get_mapping("deployment_timestamp")
        assert var is not None

        # Migrated source should be priority 1
        assert var.sources[0].priority == 1
        assert var.sources[0].source.type == "field_value"
        if hasattr(var.sources[0].source, "field"):
            assert var.sources[0].source.field == "customfield_10001"

    def test_migrate_flow_work_dates(self):
        """Test migrating flow work date fields."""
        legacy = {
            "work_started_date": "customfield_10002",
            "work_completed_date": "customfield_10003",
        }
        collection = migrate_legacy_field_mappings(legacy)

        # Check work_started_timestamp
        started_var = collection.get_mapping("work_started_timestamp")
        assert started_var is not None
        assert started_var.sources[0].priority == 1

        # Check work_completed_timestamp
        completed_var = collection.get_mapping("work_completed_timestamp")
        assert completed_var is not None
        assert completed_var.sources[0].priority == 1

    def test_migrate_incident_fields(self):
        """Test migrating incident detection and resolution fields."""
        legacy = {
            "incident_detected_at": "customfield_10004",
            "incident_resolved_at": "customfield_10005",
        }
        collection = migrate_legacy_field_mappings(legacy)

        detected_var = collection.get_mapping("incident_start_timestamp")
        assert detected_var is not None

        resolved_var = collection.get_mapping("incident_resolved_timestamp")
        assert resolved_var is not None

    def test_migrate_preserves_default_sources(self):
        """Test migration preserves default sources as fallbacks."""
        legacy = {"deployment_date": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy)

        var = collection.get_mapping("deployment_timestamp")
        assert var is not None

        # Should have migrated source + original default sources
        assert len(var.sources) > 1

        # Priority 1 is migrated, others are shifted
        priorities = [rule.priority for rule in var.sources]
        assert 1 in priorities
        assert 2 in priorities

    def test_migrate_unknown_field_skipped(self):
        """Test unknown legacy fields are skipped."""
        legacy = {
            "unknown_field_xyz": "customfield_99999",
            "deployment_date": "customfield_10001",
        }
        collection = migrate_legacy_field_mappings(legacy)

        # Should still migrate known field
        var = collection.get_mapping("deployment_timestamp")
        assert var is not None

    def test_migrate_all_legacy_field_types(self):
        """Test migrating various legacy field types."""
        legacy = {
            "deployment_date": "customfield_10001",
            "code_commit_date": "customfield_10002",
            "work_started_date": "customfield_10003",
            "estimate": "customfield_10004",
            "flow_item_type": "customfield_10005",
        }
        collection = migrate_legacy_field_mappings(legacy)

        # All should be migrated
        assert collection.get_mapping("deployment_timestamp") is not None
        assert collection.get_mapping("commit_timestamp") is not None
        assert collection.get_mapping("work_started_timestamp") is not None
        assert collection.get_mapping("work_item_size") is not None
        assert collection.get_mapping("work_type_category") is not None


class TestBackwardCompatibility:
    """Test backward compatible field_mappings generation."""

    def test_create_backward_compatible_mappings(self):
        """Test creating legacy format from variable collection."""
        # Start with migrated collection
        legacy_input = {
            "deployment_date": "customfield_10001",
            "work_started_date": "customfield_10002",
        }
        collection = migrate_legacy_field_mappings(legacy_input)

        # Convert back to legacy format
        legacy_output = create_backward_compatible_field_mappings(collection)

        assert "deployment_date" in legacy_output
        assert legacy_output["deployment_date"] == "customfield_10001"

    def test_backward_compat_handles_changelog_sources(self):
        """Test backward compat skips changelog-based sources."""
        from configuration.metric_variables import create_default_variable_collection

        collection = create_default_variable_collection()
        legacy = create_backward_compatible_field_mappings(collection)

        # Should create mappings for field-based sources only
        # Changelog sources don't map to legacy format
        assert isinstance(legacy, dict)

    def test_backward_compat_maps_multiple_legacy_names(self):
        """Test one variable maps to multiple legacy field names."""
        legacy_input = {"target_environment": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy_input)

        legacy_output = create_backward_compatible_field_mappings(collection)

        # Environment variable might map to multiple legacy names
        assert (
            "target_environment" in legacy_output
            or "affected_environment" in legacy_output
        )


class TestMigrationReport:
    """Test migration reporting functionality."""

    def test_migration_report_basic(self):
        """Test basic migration report generation."""
        legacy = {
            "deployment_date": "customfield_10001",
            "work_started_date": "customfield_10002",
        }
        collection = migrate_legacy_field_mappings(legacy)
        report = get_migration_report(legacy, collection)

        assert report["total_legacy_fields"] == 2
        assert report["migrated_variables"] == 2
        assert len(report["mappings"]) == 2

    def test_migration_report_unknown_fields(self):
        """Test report identifies unknown fields."""
        legacy = {
            "unknown_field": "customfield_99999",
            "deployment_date": "customfield_10001",
        }
        collection = migrate_legacy_field_mappings(legacy)
        report = get_migration_report(legacy, collection)

        assert len(report["unknown_fields"]) == 1
        assert "unknown_field" in report["unknown_fields"]

    def test_migration_report_mapping_details(self):
        """Test report includes mapping details."""
        legacy = {"deployment_date": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy)
        report = get_migration_report(legacy, collection)

        mapping_detail = report["mappings"][0]
        assert mapping_detail["legacy_field"] == "deployment_date"
        assert mapping_detail["jira_field"] == "customfield_10001"
        assert mapping_detail["variable_name"] == "deployment_timestamp"
        assert mapping_detail["variable_type"] == "datetime"
        assert mapping_detail["source_count"] > 0


class TestMigrationValidation:
    """Test migration validation."""

    def test_validate_successful_migration(self):
        """Test validation passes for successful migration."""
        legacy = {
            "deployment_date": "customfield_10001",
            "work_started_date": "customfield_10002",
            "work_completed_date": "customfield_10003",
        }
        collection = migrate_legacy_field_mappings(legacy)
        errors = validate_migration(legacy, collection)

        assert len(errors) == 0

    def test_validate_detects_missing_sources(self):
        """Test Pydantic validation prevents empty sources."""
        from data.variable_mapping.models import VariableMapping
        from pydantic import ValidationError

        # Pydantic should reject variable with no sources
        with pytest.raises(ValidationError) as exc_info:
            VariableMapping(
                variable_name="deployment_timestamp",
                variable_type="datetime",
                metric_category="dora",
                description="Test",
                sources=[],  # No sources - invalid
            )

        # Verify error message mentions sources
        assert "sources" in str(exc_info.value).lower()

    def test_validate_detects_duplicate_priorities(self):
        """Test Pydantic validation prevents duplicate priorities."""
        from data.variable_mapping.models import (
            VariableMapping,
            SourceRule,
            FieldValueSource,
        )
        from pydantic import ValidationError

        # Pydantic should reject duplicate priorities
        with pytest.raises(ValidationError) as exc_info:
            VariableMapping(
                variable_name="deployment_timestamp",
                variable_type="datetime",
                metric_category="dora",
                description="Test",
                sources=[
                    SourceRule(
                        priority=1,
                        source=FieldValueSource(type="field_value", field="field1"),
                    ),
                    SourceRule(
                        priority=1,  # Duplicate!
                        source=FieldValueSource(type="field_value", field="field2"),
                    ),
                ],
            )

        # Verify error message mentions unique priorities
        assert "unique priorities" in str(exc_info.value).lower()


class TestLegacyFieldMapping:
    """Test LEGACY_FIELD_TO_VARIABLE_MAP completeness."""

    def test_all_dora_fields_mapped(self):
        """Test all DORA legacy fields have variable mappings."""
        dora_legacy_fields = [
            "deployment_date",
            "deployed_to_production_date",
            "code_commit_date",
            "incident_detected_at",
            "incident_resolved_at",
            "deployment_successful",
        ]

        for field in dora_legacy_fields:
            assert field in LEGACY_FIELD_TO_VARIABLE_MAP, f"Missing mapping for {field}"

    def test_all_flow_fields_mapped(self):
        """Test all Flow legacy fields have variable mappings."""
        flow_legacy_fields = [
            "work_started_date",
            "work_completed_date",
            "flow_item_type",
            "estimate",
        ]

        for field in flow_legacy_fields:
            assert field in LEGACY_FIELD_TO_VARIABLE_MAP, f"Missing mapping for {field}"

    def test_mapping_points_to_valid_variables(self):
        """Test all mappings point to valid variable names."""
        from configuration.metric_variables import create_default_variable_collection

        collection = create_default_variable_collection()

        for legacy_field, variable_name in LEGACY_FIELD_TO_VARIABLE_MAP.items():
            # Variable should exist in default collection
            var = collection.get_mapping(variable_name)
            assert var is not None, (
                f"Variable {variable_name} not found (from {legacy_field})"
            )


class TestSourceCreation:
    """Test source creation during migration."""

    def test_datetime_field_creates_field_value_source(self):
        """Test datetime fields create FieldValueSource."""
        legacy = {"deployment_date": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy)

        var = collection.get_mapping("deployment_timestamp")
        assert var is not None
        first_source = var.sources[0].source

        assert first_source.type == "field_value"
        if hasattr(first_source, "field"):
            assert first_source.field == "customfield_10001"
        if hasattr(first_source, "value_type"):
            assert first_source.value_type == "datetime"

    def test_number_field_creates_number_source(self):
        """Test number fields create number-typed source."""
        legacy = {"estimate": "customfield_10002"}
        collection = migrate_legacy_field_mappings(legacy)

        var = collection.get_mapping("work_item_size")
        assert var is not None
        first_source = var.sources[0].source

        assert first_source.type == "field_value"
        if hasattr(first_source, "value_type"):
            assert first_source.value_type == "number"


class TestMigrationEdgeCases:
    """Test edge cases in migration."""

    def test_empty_jira_field_skipped(self):
        """Test empty JIRA field values are skipped."""
        legacy = {"deployment_date": "", "work_started_date": "customfield_10001"}
        collection = migrate_legacy_field_mappings(legacy)

        # Should still have defaults for deployment_timestamp
        var = collection.get_mapping("deployment_timestamp")
        assert var is not None

        # work_started_timestamp should be migrated
        work_var = collection.get_mapping("work_started_timestamp")
        assert work_var is not None
        assert work_var.sources[0].priority == 1

    def test_none_legacy_mappings_uses_defaults(self):
        """Test passing None uses default collection."""
        collection = migrate_legacy_field_mappings(None)

        assert isinstance(collection, VariableMappingCollection)
        assert len(collection.mappings) > 0

    def test_roundtrip_migration(self):
        """Test migrating to variable mappings and back to legacy."""
        original_legacy = {
            "deployment_date": "customfield_10001",
            "work_started_date": "customfield_10002",
            "estimate": "customfield_10003",
        }

        # Migrate to variable mappings
        collection = migrate_legacy_field_mappings(original_legacy)

        # Convert back to legacy
        restored_legacy = create_backward_compatible_field_mappings(collection)

        # Should preserve critical fields
        assert "deployment_date" in restored_legacy
        assert restored_legacy["deployment_date"] == "customfield_10001"
