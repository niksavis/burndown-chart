"""
Unit tests for Flow metrics calculator.

Tests Flow metric calculations (Velocity, Time, Efficiency, Load, Distribution)
to ensure accurate calculations and proper error handling.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List
from data.flow_calculator import (
    calculate_flow_velocity,
    calculate_flow_time,
    calculate_flow_efficiency,
    calculate_flow_load,
    calculate_flow_distribution,
    calculate_all_flow_metrics,
)


class TestFlowVelocityCalculation:
    """Test Flow Velocity metric calculation."""

    def test_flow_velocity_with_valid_issues(self):
        """Test velocity calculation with completed issues."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10007": {"value": "Feature"},  # flow_item_type
                    "resolutiondate": "2025-01-15T10:00:00.000Z",  # completed_date
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10007": {"value": "Defect"},
                    "resolutiondate": "2025-01-20T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "customfield_10007": {"value": "Feature"},
                    "resolutiondate": "2025-01-25T10:00:00.000Z",
                },
            },
        ]

        field_mappings = {
            "flow_item_type": "customfield_10007",
            "completed_date": "resolutiondate",
        }

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_flow_velocity(issues, field_mappings, start_date, end_date)

        assert result["metric_name"] == "flow_velocity"
        assert result["value"] == 3
        assert result["unit"] == "items/month"
        assert result["error_state"] == "success"
        assert result["total_issue_count"] == 3
        assert result["excluded_issue_count"] == 0

        # Check breakdown by type
        assert "details" in result
        assert "by_type" in result["details"]
        assert result["details"]["by_type"]["Feature"] == 2
        assert result["details"]["by_type"]["Defect"] == 1

    def test_flow_velocity_with_missing_field_mapping(self):
        """Test velocity calculation with missing field mapping."""
        issues = [{"key": "TEST-1", "fields": {}}]
        field_mappings = {}  # Missing required mappings

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_flow_velocity(issues, field_mappings, start_date, end_date)

        assert result["error_state"] == "missing_mapping"
        assert result["value"] is None
        assert result["error_message"] is not None

    def test_flow_velocity_with_no_completed_issues(self):
        """Test velocity calculation with no completed issues in period."""
        issues = []
        field_mappings = {
            "flow_item_type": "customfield_10007",
            "completed_date": "resolutiondate",
        }

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_flow_velocity(issues, field_mappings, start_date, end_date)

        assert result["error_state"] == "no_data"
        assert result["value"] is None  # No data returns None, not 0
        assert result["total_issue_count"] == 0


class TestFlowTimeCalculation:
    """Test Flow Time metric calculation."""

    def test_flow_time_with_valid_issues(self):
        """Test flow time calculation with valid start and end dates."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10201": "2025-01-10T10:00:00.000Z",  # work_started_date
                    "customfield_10202": "2025-01-15T10:00:00.000Z",  # work_completed_date
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10201": "2025-01-12T10:00:00.000Z",
                    "customfield_10202": "2025-01-20T10:00:00.000Z",
                },
            },
        ]

        field_mappings = {
            "work_started_date": "customfield_10201",
            "work_completed_date": "customfield_10202",
        }

        result = calculate_flow_time(issues, field_mappings)

        assert result["metric_name"] == "flow_time"
        assert result["value"] > 0  # Average of 5 days and 8 days = 6.5 days
        assert result["unit"] == "days"
        assert result["error_state"] == "success"
        assert result["total_issue_count"] == 2
        assert result["excluded_issue_count"] == 0

    def test_flow_time_with_missing_dates(self):
        """Test flow time excludes issues with missing dates."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10201": "2025-01-10T10:00:00.000Z",
                    "customfield_10202": "2025-01-15T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10201": "2025-01-12T10:00:00.000Z",
                    # Missing work_completed_date
                },
            },
        ]

        field_mappings = {
            "work_started_date": "customfield_10201",
            "work_completed_date": "customfield_10202",
        }

        result = calculate_flow_time(issues, field_mappings)

        assert result["error_state"] == "success"
        assert result["excluded_issue_count"] == 1
        assert result["total_issue_count"] == 2


class TestFlowEfficiencyCalculation:
    """Test Flow Efficiency metric calculation."""

    def test_flow_efficiency_with_valid_data(self):
        """Test efficiency calculation with valid active hours and flow time."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10204": 40,  # active_work_hours
                    "customfield_10205": 10,  # flow_time_days (240 hours)
                },
            },
        ]

        field_mappings = {
            "active_work_hours": "customfield_10204",
            "flow_time_days": "customfield_10205",
        }

        result = calculate_flow_efficiency(issues, field_mappings)

        assert result["metric_name"] == "flow_efficiency"
        assert result["unit"] == "percentage"
        assert result["error_state"] == "success"
        # Efficiency = (40 / (10 * 24)) * 100 = 16.67%
        assert 15 < result["value"] < 18

    def test_flow_efficiency_with_no_data(self):
        """Test efficiency calculation with no valid data."""
        issues = []
        field_mappings = {
            "active_work_hours": "customfield_10204",
            "flow_time_days": "customfield_10205",
        }

        result = calculate_flow_efficiency(issues, field_mappings)

        assert result["error_state"] == "no_data"
        assert result["value"] is None


class TestFlowLoadCalculation:
    """Test Flow Load (WIP) metric calculation."""

    def test_flow_load_with_in_progress_issues(self):
        """Test WIP count with issues in various statuses."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "In Progress"},
                    "customfield_10007": {"value": "Feature"},
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {"name": "In Progress"},
                    "customfield_10007": {"value": "Defect"},
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "Done"},
                    "customfield_10007": {"value": "Feature"},
                },
            },
        ]

        field_mappings = {
            "status": "status",
            "flow_item_type": "customfield_10007",
        }

        result = calculate_flow_load(issues, field_mappings)

        assert result["metric_name"] == "flow_load"
        assert result["value"] == 2  # Only "In Progress" items
        assert result["unit"] == "items"
        assert result["error_state"] == "success"

        # Check breakdown by type
        assert result["details"]["by_type"]["Feature"] == 1
        assert result["details"]["by_type"]["Defect"] == 1


class TestFlowDistributionCalculation:
    """Test Flow Distribution metric calculation."""

    def test_flow_distribution_with_all_types(self):
        """Test distribution calculation with all work types."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10007": {"value": "Feature"},
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10007": {"value": "Feature"},
                    "resolutiondate": "2025-01-16T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "customfield_10007": {"value": "Defect"},
                    "resolutiondate": "2025-01-17T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-4",
                "fields": {
                    "customfield_10007": {"value": "Risk"},
                    "resolutiondate": "2025-01-18T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-5",
                "fields": {
                    "customfield_10007": {"value": "Technical_Debt"},
                    "resolutiondate": "2025-01-19T10:00:00.000Z",
                },
            },
        ]

        field_mappings = {
            "flow_item_type": "customfield_10007",
            "completed_date": "resolutiondate",
        }

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_flow_distribution(
            issues, field_mappings, start_date, end_date
        )

        assert result["metric_name"] == "flow_distribution"
        assert result["value"] == 100  # Total percentage
        assert result["unit"] == "percentage"
        assert result["error_state"] == "success"

        # Check distribution breakdown
        breakdown = result["distribution_breakdown"]
        assert breakdown["Feature"]["count"] == 2
        assert breakdown["Feature"]["percentage"] == 40.0
        assert "within_range" in breakdown["Feature"]

        assert breakdown["Defect"]["count"] == 1
        assert breakdown["Risk"]["count"] == 1
        assert breakdown["Technical_Debt"]["count"] == 1

    def test_flow_distribution_checks_recommended_ranges(self):
        """Test distribution validates against recommended ranges."""
        # 80% Feature work (exceeds recommended 40-50%)
        issues = [
            {
                "key": f"TEST-{i}",
                "fields": {
                    "customfield_10007": {"value": "Feature"},
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                },
            }
            for i in range(8)
        ] + [
            {
                "key": "TEST-9",
                "fields": {
                    "customfield_10007": {"value": "Defect"},
                    "resolutiondate": "2025-01-16T10:00:00.000Z",
                },
            },
            {
                "key": "TEST-10",
                "fields": {
                    "customfield_10007": {"value": "Risk"},
                    "resolutiondate": "2025-01-17T10:00:00.000Z",
                },
            },
        ]

        field_mappings = {
            "flow_item_type": "customfield_10007",
            "completed_date": "resolutiondate",
        }

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_flow_distribution(
            issues, field_mappings, start_date, end_date
        )

        breakdown = result["distribution_breakdown"]
        # Feature should be marked as outside recommended range
        assert breakdown["Feature"]["percentage"] == 80.0
        assert breakdown["Feature"]["within_range"] is False


@pytest.mark.parametrize(
    "issues,field_mappings,expected_error",
    [
        # Missing work type field
        (
            [
                {
                    "key": "TEST-1",
                    "fields": {"resolutiondate": "2025-01-15T10:00:00.000Z"},
                }
            ],
            {"completed_date": "resolutiondate"},
            "missing_mapping",
        ),
        # Empty issues list
        ([], {"flow_item_type": "cf1", "completed_date": "cf2"}, "no_data"),
        # Invalid date format
        (
            [
                {
                    "key": "TEST-1",
                    "fields": {
                        "customfield_10201": "invalid-date",
                        "customfield_10202": "2025-01-15T10:00:00.000Z",
                    },
                }
            ],
            {
                "work_started_date": "customfield_10201",
                "work_completed_date": "customfield_10202",
            },
            "calculation_error",
        ),
    ],
)
class TestFlowCalculatorEdgeCases:
    """Test edge cases and error conditions."""

    def test_edge_cases(self, issues, field_mappings, expected_error):
        """Test various edge cases across all flow metrics."""
        # Test with flow_velocity as example
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        if expected_error == "calculation_error":
            # Test flow_time which uses date parsing
            result = calculate_flow_time(issues, field_mappings)
        else:
            result = calculate_flow_velocity(
                issues, field_mappings, start_date, end_date
            )

        assert result["error_state"] in [expected_error, "no_data"]


class TestCalculateAllFlowMetrics:
    """Test calculation of all Flow metrics at once."""

    def test_calculate_all_metrics_success(self):
        """Test calculating all Flow metrics together."""
        issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "customfield_10007": {"value": "Feature"},
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                    "customfield_10201": "2025-01-10T10:00:00.000Z",
                    "customfield_10202": "2025-01-15T10:00:00.000Z",
                    "customfield_10204": 40,
                    "customfield_10205": 5,
                    "status": {"name": "Done"},
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "customfield_10007": {"value": "Defect"},
                    "resolutiondate": "2025-01-20T10:00:00.000Z",
                    "customfield_10201": "2025-01-15T10:00:00.000Z",
                    "customfield_10202": "2025-01-20T10:00:00.000Z",
                    "customfield_10204": 30,
                    "customfield_10205": 5,
                    "status": {"name": "In Progress"},
                },
            },
        ]

        field_mappings = {
            "flow_item_type": "customfield_10007",
            "completed_date": "resolutiondate",
            "work_started_date": "customfield_10201",
            "work_completed_date": "customfield_10202",
            "active_work_hours": "customfield_10204",
            "flow_time_days": "customfield_10205",
            "status": "status",
        }

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_all_flow_metrics(
            issues, field_mappings, start_date, end_date
        )

        # Verify all five metrics are present
        assert "flow_velocity" in result
        assert "flow_time" in result
        assert "flow_efficiency" in result
        assert "flow_load" in result
        assert "flow_distribution" in result

        # Verify each metric has required structure
        for metric_name, metric_data in result.items():
            assert "metric_name" in metric_data
            assert "value" in metric_data
            assert "unit" in metric_data
            assert "error_state" in metric_data

    def test_calculate_all_metrics_with_missing_mappings(self):
        """Test that metrics gracefully handle missing field mappings."""
        issues = []
        field_mappings = {}  # No mappings configured

        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        result = calculate_all_flow_metrics(
            issues, field_mappings, start_date, end_date
        )

        # All metrics should have error_state
        for metric_data in result.values():
            assert metric_data["error_state"] in ["missing_mapping", "no_data"]
