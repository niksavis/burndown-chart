"""Unit tests for DORA/Flow JIRA compatibility validation.

Tests the validate_dora_jira_compatibility() function that detects
inappropriate field mappings and recommends validation modes.
"""

from data.field_mapper import validate_dora_jira_compatibility


class TestDoraJiraCompatibilityValidation:
    """Test JIRA data source validation for DORA/Flow metrics."""

    def test_devops_tracking_with_proper_fields(self):
        """Test validation with proper DevOps-specific custom fields."""
        field_mappings = {
            "deployment_date": "customfield_10100_deployment_date",
            "deployment_successful": "customfield_10101_deployment_status",
            "incident_detected_at": "customfield_10102_incident_start",
            "incident_resolved_at": "customfield_10103_incident_end",
        }

        result = validate_dora_jira_compatibility(field_mappings)

        assert result["validation_mode"] == "devops"
        assert result["compatibility_level"] == "full"
        assert result["devops_field_count"] >= 3
        assert result["error_count"] == 0
        assert result["alternative_metrics_available"] is False

    def test_issue_tracker_with_proxy_fields(self):
        """Test validation with standard JIRA fields as proxies (Apache Kafka scenario)."""
        field_mappings = {
            "deployment_date": "resolutiondate",
            "incident_detected_at": "created",
            "incident_resolved_at": "resolutiondate",
        }

        result = validate_dora_jira_compatibility(field_mappings)

        assert result["validation_mode"] == "issue_tracker"
        assert result["compatibility_level"] == "unsuitable"
        assert result["proxy_field_count"] >= 2
        assert result["error_count"] >= 2
        assert result["alternative_metrics_available"] is True

        # Check for specific warnings
        warnings = result["warnings"]
        deployment_warning = next(
            (w for w in warnings if w["field"] == "deployment_date"), None
        )
        assert deployment_warning is not None
        assert deployment_warning["severity"] == "error"
        assert "resolved issues" in deployment_warning["issue"].lower()

    def test_recommended_interpretations_for_issue_tracker(self):
        """Test that alternative metric interpretations are provided for issue trackers."""
        field_mappings = {
            "deployment_date": "resolutiondate",
            "incident_detected_at": "created",
        }

        result = validate_dora_jira_compatibility(field_mappings)

        assert result["validation_mode"] == "issue_tracker"
        interpretations = result["recommended_interpretation"]

        assert "deployment_frequency" in interpretations
        assert interpretations["deployment_frequency"] == "Issue Resolution Frequency"
        assert (
            interpretations["lead_time_for_changes"]
            == "Issue Cycle Time (Created → Resolved)"
        )
        assert "Not Applicable" in interpretations["change_failure_rate"]

    def test_missing_field_mappings(self):
        """Test validation with missing required fields."""
        field_mappings = {
            "flow_item_type": "issuetype",
            # Missing deployment and incident fields
        }

        result = validate_dora_jira_compatibility(field_mappings)

        warnings = result["warnings"]
        missing_warnings = [
            w for w in warnings if w["mapped_to"] is None and w["severity"] == "warning"
        ]
        assert len(missing_warnings) >= 3  # deployment_date, incident fields, etc.

    def test_partial_devops_tracking(self):
        """Test validation with mix of proper and proxy fields."""
        field_mappings = {
            "deployment_date": "customfield_10100_deployment",  # Good
            "deployment_successful": "customfield_10101_status",  # Good
            "incident_detected_at": "created",  # Bad proxy
            "incident_resolved_at": "resolutiondate",  # Bad proxy
        }

        result = validate_dora_jira_compatibility(field_mappings)

        assert result["validation_mode"] == "devops"
        assert result["compatibility_level"] == "partial"
        assert result["devops_field_count"] >= 1
        assert result["error_count"] >= 1
        assert result["error_count"] <= 2

    def test_custom_field_unclear_purpose(self):
        """Test validation with custom fields that don't match DevOps patterns."""
        field_mappings = {
            "deployment_date": "customfield_10200",  # Custom but unclear
            "flow_item_type": "customfield_10201",
        }

        result = validate_dora_jira_compatibility(field_mappings)

        warnings = result["warnings"]
        unclear_warnings = [
            w
            for w in warnings
            if w["severity"] == "warning" and "Verify this field" in w["issue"]
        ]
        assert len(unclear_warnings) >= 1

    def test_validation_result_structure(self):
        """Test that validation result has all required keys."""
        field_mappings = {"deployment_date": "resolutiondate"}

        result = validate_dora_jira_compatibility(field_mappings)

        # Check required keys
        required_keys = [
            "validation_mode",
            "compatibility_level",
            "devops_field_count",
            "proxy_field_count",
            "error_count",
            "warning_count",
            "warnings",
            "recommended_interpretation",
            "alternative_metrics_available",
        ]

        for key in required_keys:
            assert key in result, f"Missing required key: {key}"

        # Check warning structure
        if result["warnings"]:
            warning = result["warnings"][0]
            assert "severity" in warning
            assert "field" in warning
            assert "mapped_to" in warning
            assert "recommendation" in warning

    def test_empty_field_mappings(self):
        """Test validation with no field mappings."""
        field_mappings = {}

        result = validate_dora_jira_compatibility(field_mappings)

        assert result["validation_mode"] == "unknown"
        assert result["devops_field_count"] == 0
        assert result["proxy_field_count"] == 0
        # Should have warnings about missing fields
        assert result["warning_count"] >= 4
