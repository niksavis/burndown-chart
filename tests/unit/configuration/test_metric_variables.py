"""Unit tests for metric variable definitions catalog.

Tests verify that all default variable mappings are properly configured
and that helper functions work correctly.
"""

from data.variable_mapping.models import VariableMappingCollection
from configuration.metric_variables import (
    create_default_dora_variables,
    create_default_flow_variables,
    create_default_common_variables,
    create_default_variable_collection,
    get_variables_by_metric,
    DEFAULT_VARIABLE_COLLECTION,
)


class TestDORAVariables:
    """Test DORA metric variable definitions."""

    def test_dora_variables_count(self):
        """Test correct number of DORA variables defined."""
        dora_vars = create_default_dora_variables()

        # Should have at least deployment, commit, incident variables
        assert len(dora_vars) >= 7

    def test_deployment_event_variable(self):
        """Test deployment_event variable is properly configured."""
        dora_vars = create_default_dora_variables()

        assert "deployment_event" in dora_vars
        var = dora_vars["deployment_event"]

        assert var.variable_type == "boolean"
        assert var.metric_category == "dora"
        assert var.required is True
        assert len(var.sources) >= 2  # Multiple source options
        # fallback_source is optional - variable may not have one

    def test_deployment_timestamp_variable(self):
        """Test deployment_timestamp has multiple sources."""
        dora_vars = create_default_dora_variables()

        assert "deployment_timestamp" in dora_vars
        var = dora_vars["deployment_timestamp"]

        assert var.variable_type == "datetime"
        assert var.required is True
        assert len(var.sources) >= 2

        # Check priority ordering
        priorities = [rule.priority for rule in var.sources]
        assert priorities == sorted(priorities)

    def test_commit_timestamp_variable(self):
        """Test commit_timestamp for lead time calculation."""
        dora_vars = create_default_dora_variables()

        assert "commit_timestamp" in dora_vars
        var = dora_vars["commit_timestamp"]

        assert var.variable_type == "datetime"
        assert var.metric_category == "dora"

    def test_incident_variables(self):
        """Test incident-related variables for CFR and MTTR."""
        dora_vars = create_default_dora_variables()

        required_incident_vars = [
            "is_incident",
            "incident_start_timestamp",
            "incident_resolved_timestamp",
        ]

        for var_name in required_incident_vars:
            assert var_name in dora_vars, f"Missing variable: {var_name}"
            var = dora_vars[var_name]
            assert var.metric_category == "dora"


class TestFlowVariables:
    """Test Flow metric variable definitions."""

    def test_flow_variables_count(self):
        """Test correct number of Flow variables defined."""
        flow_vars = create_default_flow_variables()

        # Should have completion, time, efficiency, load, distribution vars
        assert len(flow_vars) >= 9

    def test_is_completed_variable(self):
        """Test is_completed variable for velocity."""
        flow_vars = create_default_flow_variables()

        assert "is_completed" in flow_vars
        var = flow_vars["is_completed"]

        assert var.variable_type == "boolean"
        assert var.metric_category == "flow"
        assert var.required is True

    def test_work_item_size_variable(self):
        """Test work_item_size has fallback for unestimated items."""
        flow_vars = create_default_flow_variables()

        assert "work_item_size" in flow_vars
        var = flow_vars["work_item_size"]

        assert var.variable_type == "number"
        assert var.required is False  # Optional since items may be unestimated
        assert var.fallback_source is not None

    def test_flow_time_variables(self):
        """Test flow time calculation variables."""
        flow_vars = create_default_flow_variables()

        assert "work_started_timestamp" in flow_vars
        assert "work_completed_timestamp" in flow_vars

        start_var = flow_vars["work_started_timestamp"]
        end_var = flow_vars["work_completed_timestamp"]

        assert start_var.variable_type == "datetime"
        assert end_var.variable_type == "datetime"

    def test_flow_efficiency_variables(self):
        """Test flow efficiency calculation variables."""
        flow_vars = create_default_flow_variables()

        assert "active_time" in flow_vars
        assert "total_time" in flow_vars

        active_var = flow_vars["active_time"]
        total_var = flow_vars["total_time"]

        assert active_var.variable_type == "duration"
        assert total_var.variable_type == "duration"

        # Active time should use calculated source (sum of changelog durations)
        assert len(active_var.sources) >= 1
        assert active_var.sources[0].source.type == "calculated"

    def test_work_type_category_variable(self):
        """Test work type distribution variable."""
        flow_vars = create_default_flow_variables()

        assert "work_type_category" in flow_vars
        var = flow_vars["work_type_category"]

        assert var.variable_type == "category"
        assert var.required is True
        assert var.category_mapping is not None

        # Check category mapping exists
        assert "Story" in var.category_mapping
        assert "Bug" in var.category_mapping
        assert var.category_mapping["Story"] == ["Feature"]


class TestCommonVariables:
    """Test common variable definitions."""

    def test_common_variables_count(self):
        """Test common variables are defined."""
        common_vars = create_default_common_variables()

        assert len(common_vars) >= 3

    def test_project_key_variable(self):
        """Test project_key variable."""
        common_vars = create_default_common_variables()

        assert "project_key" in common_vars
        var = common_vars["project_key"]

        assert var.metric_category == "common"
        assert var.required is True

    def test_created_timestamp_variable(self):
        """Test created_timestamp variable."""
        common_vars = create_default_common_variables()

        assert "created_timestamp" in common_vars
        var = common_vars["created_timestamp"]

        assert var.variable_type == "datetime"
        assert var.metric_category == "common"


class TestDefaultCollection:
    """Test default variable collection."""

    def test_collection_creation(self):
        """Test creating default collection."""
        collection = create_default_variable_collection()

        assert isinstance(collection, VariableMappingCollection)
        assert collection.version == "1.0"
        assert len(collection.mappings) > 0

    def test_collection_contains_all_categories(self):
        """Test collection contains DORA, Flow, and common variables."""
        collection = create_default_variable_collection()

        dora_vars = collection.get_mappings_by_category("dora")
        flow_vars = collection.get_mappings_by_category("flow")
        common_vars = collection.get_mappings_by_category("common")

        assert len(dora_vars) > 0
        assert len(flow_vars) > 0
        assert len(common_vars) > 0

    def test_collection_all_variables_valid(self):
        """Test all variables in collection are valid."""
        collection = create_default_variable_collection()

        for var_name, var_mapping in collection.mappings.items():
            # Check basic properties
            assert var_mapping.variable_name == var_name
            assert var_mapping.variable_type in [
                "boolean",
                "datetime",
                "number",
                "duration",
                "category",
                "count",
            ]
            assert var_mapping.metric_category in ["dora", "flow", "common"]
            assert len(var_mapping.sources) > 0

            # Check priority uniqueness
            priorities = [rule.priority for rule in var_mapping.sources]
            assert len(priorities) == len(set(priorities)), (
                f"Duplicate priorities in {var_name}"
            )

    def test_default_collection_singleton(self):
        """Test DEFAULT_VARIABLE_COLLECTION is properly initialized."""
        assert isinstance(DEFAULT_VARIABLE_COLLECTION, VariableMappingCollection)
        assert len(DEFAULT_VARIABLE_COLLECTION.mappings) > 0


class TestGetVariablesByMetric:
    """Test metric-specific variable retrieval."""

    def test_deployment_frequency_variables(self):
        """Test getting variables for deployment frequency metric."""
        vars_dict = get_variables_by_metric("deployment_frequency")

        assert "deployment_event" in vars_dict
        assert "deployment_timestamp" in vars_dict
        assert "deployment_successful" in vars_dict
        assert "project_key" in vars_dict

    def test_lead_time_variables(self):
        """Test getting variables for lead time metric."""
        vars_dict = get_variables_by_metric("lead_time_for_changes")

        assert "commit_timestamp" in vars_dict
        assert "deployment_timestamp" in vars_dict

    def test_change_failure_rate_variables(self):
        """Test getting variables for change failure rate."""
        vars_dict = get_variables_by_metric("change_failure_rate")

        assert "deployment_event" in vars_dict
        assert "is_incident" in vars_dict
        assert "incident_start_timestamp" in vars_dict

    def test_mttr_variables(self):
        """Test getting variables for mean time to recovery."""
        vars_dict = get_variables_by_metric("mean_time_to_recovery")

        assert "is_incident" in vars_dict
        assert "incident_start_timestamp" in vars_dict
        assert "incident_resolved_timestamp" in vars_dict

    def test_flow_velocity_variables(self):
        """Test getting variables for flow velocity."""
        vars_dict = get_variables_by_metric("flow_velocity")

        assert "is_completed" in vars_dict
        assert "completion_timestamp" in vars_dict
        assert "work_type_category" in vars_dict

    def test_flow_time_variables(self):
        """Test getting variables for flow time."""
        vars_dict = get_variables_by_metric("flow_time")

        assert "work_started_timestamp" in vars_dict
        assert "work_completed_timestamp" in vars_dict
        assert "is_completed" in vars_dict

    def test_flow_efficiency_variables(self):
        """Test getting variables for flow efficiency."""
        vars_dict = get_variables_by_metric("flow_efficiency")

        assert "active_time" in vars_dict
        assert "total_time" in vars_dict

    def test_flow_load_variables(self):
        """Test getting variables for flow load."""
        vars_dict = get_variables_by_metric("flow_load")

        assert "is_in_progress" in vars_dict

    def test_flow_distribution_variables(self):
        """Test getting variables for flow distribution."""
        vars_dict = get_variables_by_metric("flow_distribution")

        assert "work_type_category" in vars_dict
        assert "is_completed" in vars_dict

    def test_unknown_metric_returns_empty(self):
        """Test unknown metric returns empty dict."""
        vars_dict = get_variables_by_metric("unknown_metric")

        assert vars_dict == {}


class TestVariableSourceConfiguration:
    """Test specific source configurations."""

    def test_deployment_event_has_environment_filter(self):
        """Test deployment_event filters by environment."""
        dora_vars = create_default_dora_variables()
        var = dora_vars["deployment_event"]

        # First source should have production environment filter
        first_source = var.sources[0]
        assert first_source.filters is not None
        assert first_source.filters.environment_value == "Production"

    def test_active_time_uses_changelog_calculation(self):
        """Test active_time uses sum_changelog_durations calculation."""
        flow_vars = create_default_flow_variables()
        var = flow_vars["active_time"]

        calc_source = var.sources[0].source
        assert calc_source.type == "calculated"
        assert calc_source.calculation == "sum_changelog_durations"
        assert "statuses" in calc_source.inputs

    def test_work_type_has_category_mapping(self):
        """Test work_type_category has proper mapping."""
        flow_vars = create_default_flow_variables()
        var = flow_vars["work_type_category"]

        mapping = var.category_mapping
        assert mapping is not None

        # Test specific mappings
        assert mapping["Bug"] == ["Bug"]
        assert mapping["Technical Debt"] == ["Tech Debt"]
        assert mapping["Epic"] == ["Feature"]


class TestVariableRequirements:
    """Test required vs optional variable configuration."""

    def test_required_dora_variables(self):
        """Test critical DORA variables are marked required."""
        dora_vars = create_default_dora_variables()

        required_vars = [
            "deployment_event",
            "deployment_timestamp",
            "deployment_successful",
            "commit_timestamp",
            "is_incident",
            "incident_start_timestamp",
            "incident_resolved_timestamp",
        ]

        for var_name in required_vars:
            var = dora_vars[var_name]
            assert var.required is True, f"{var_name} should be required"

    def test_required_flow_variables(self):
        """Test critical Flow variables are marked required."""
        flow_vars = create_default_flow_variables()

        required_vars = [
            "is_completed",
            "work_started_timestamp",
            "work_completed_timestamp",
            "active_time",
            "total_time",
            "is_in_progress",
            "work_type_category",
        ]

        for var_name in required_vars:
            var = flow_vars[var_name]
            assert var.required is True, f"{var_name} should be required"

    def test_optional_variables(self):
        """Test optional variables are marked correctly."""
        all_vars = create_default_variable_collection()

        optional_vars = ["work_item_size", "environment", "related_deployment"]

        for var_name in optional_vars:
            var = all_vars.get_mapping(var_name)
            if var:  # May not exist in default collection
                assert var.required is False, f"{var_name} should be optional"


class TestCollectionSerialization:
    """Test that collection can be serialized/deserialized."""

    def test_collection_to_dict(self):
        """Test collection can be converted to dict."""
        collection = create_default_variable_collection()

        # Pydantic model_dump should work
        data = collection.model_dump()

        assert "mappings" in data
        assert "version" in data
        assert isinstance(data["mappings"], dict)

    def test_collection_roundtrip(self):
        """Test collection can be serialized and deserialized."""
        original = create_default_variable_collection()

        # Serialize
        data = original.model_dump()

        # Deserialize
        restored = VariableMappingCollection(**data)

        assert len(restored.mappings) == len(original.mappings)
        assert restored.version == original.version
