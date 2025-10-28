"""Unit tests for trend calculation in DORA and Flow metrics.

Tests T058: Verify that metric calculators include trend_direction and trend_percentage.
"""

import pytest
from data.dora_calculator import (
    calculate_deployment_frequency,
    calculate_lead_time_for_changes,
    calculate_change_failure_rate,
    calculate_mean_time_to_recovery,
    _calculate_trend,
)


class TestTrendCalculation:
    """Test trend calculation helper function."""

    def test_upward_trend(self):
        """Test upward trend detection."""
        trend = _calculate_trend(current_value=120.0, previous_value=100.0)
        assert trend["trend_direction"] == "up"
        assert trend["trend_percentage"] == 20.0

    def test_downward_trend(self):
        """Test downward trend detection."""
        trend = _calculate_trend(current_value=80.0, previous_value=100.0)
        assert trend["trend_direction"] == "down"
        assert trend["trend_percentage"] == -20.0

    def test_stable_trend(self):
        """Test stable trend detection (< 5% change)."""
        trend = _calculate_trend(current_value=102.0, previous_value=100.0)
        assert trend["trend_direction"] == "stable"
        assert trend["trend_percentage"] == 2.0

    def test_no_previous_value(self):
        """Test trend when previous value is None."""
        trend = _calculate_trend(current_value=100.0, previous_value=None)
        assert trend["trend_direction"] == "stable"
        assert trend["trend_percentage"] == 0.0

    def test_zero_previous_value(self):
        """Test trend when previous value is zero."""
        trend = _calculate_trend(current_value=100.0, previous_value=0)
        assert trend["trend_direction"] == "stable"
        assert trend["trend_percentage"] == 0.0


class TestDORAMetricTrends:
    """Test that all DORA metrics include trend data in returns."""

    def test_deployment_frequency_with_trend(self):
        """Test deployment frequency includes trend data."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10001": "2025-10-15T10:00:00.000",
                    "customfield_10002": True,
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10001": "2025-10-20T10:00:00.000",
                    "customfield_10002": True,
                },
            },
        ]

        field_mappings = {
            "deployment_date": "customfield_10001",
            "deployment_successful": "customfield_10002",
        }

        result = calculate_deployment_frequency(
            issues, field_mappings, time_period_days=30, previous_period_value=1.5
        )

        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["trend_direction"] in ["up", "down", "stable"]
        assert isinstance(result["trend_percentage"], (int, float))

    def test_deployment_frequency_error_includes_trend(self):
        """Test deployment frequency error state includes trend data."""
        issues = []
        field_mappings = {}  # Missing required field

        result = calculate_deployment_frequency(issues, field_mappings)

        assert result["error_state"] == "missing_mapping"
        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0

    def test_lead_time_includes_trend(self):
        """Test lead time for changes includes trend data."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_20001": "2025-10-01T10:00:00.000Z",
                    "customfield_20002": "2025-10-03T10:00:00.000Z",
                },
            }
        ]

        field_mappings = {
            "code_commit_date": "customfield_20001",
            "deployed_to_production_date": "customfield_20002",
        }

        result = calculate_lead_time_for_changes(
            issues, field_mappings, previous_period_value=2.5
        )

        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["error_state"] == "success"

    def test_change_failure_rate_includes_trend(self):
        """Test change failure rate includes trend data."""
        deployment_issues = [{"key": "DEP-1"}, {"key": "DEP-2"}]
        incident_issues = [{"key": "INC-1"}]

        field_mappings = {"deployment_date": "customfield_30001"}

        result = calculate_change_failure_rate(
            deployment_issues,
            incident_issues,
            field_mappings,
            previous_period_value=25.0,
        )

        assert "trend_direction" in result
        assert "trend_percentage" in result

    def test_mttr_includes_trend(self):
        """Test mean time to recovery includes trend data."""
        issues = [
            {
                "key": "INC-1",
                "fields": {
                    "customfield_40001": "2025-10-15T10:00:00.000Z",
                    "customfield_40002": "2025-10-15T14:00:00.000Z",
                },
            }
        ]

        field_mappings = {
            "incident_detected_at": "customfield_40001",
            "incident_resolved_at": "customfield_40002",
        }

        result = calculate_mean_time_to_recovery(
            issues, field_mappings, previous_period_value=5.0
        )

        assert "trend_direction" in result
        assert "trend_percentage" in result
        assert result["error_state"] == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
