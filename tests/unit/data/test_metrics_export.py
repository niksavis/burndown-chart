"""Unit tests for metrics export functionality.

Tests CSV and JSON export for both DORA and Flow metrics.
"""

import csv
import json
from datetime import datetime
from io import StringIO


class TestExportDORAMetricsToCSV:
    """Test DORA metrics CSV export."""

    def test_export_dora_metrics_to_csv(self):
        """Test DORA metrics export to CSV format."""
        from data.metrics_export import export_dora_to_csv

        # Sample DORA metrics data
        dora_metrics = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 12.5,
                "unit": "deployments/month",
                "performance_tier": "High",
                "performance_tier_color": "warning",
                "trend_direction": "up",
                "trend_percentage": 15.2,
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": 3.2,
                "unit": "days",
                "performance_tier": "Elite",
                "performance_tier_color": "success",
                "trend_direction": "down",
                "trend_percentage": -8.5,
            },
            "change_failure_rate": {
                "metric_name": "change_failure_rate",
                "value": 8.5,
                "unit": "%",
                "performance_tier": "Medium",
                "performance_tier_color": "warning",
                "trend_direction": "stable",
                "trend_percentage": 2.1,
            },
            "mean_time_to_recovery": {
                "metric_name": "mean_time_to_recovery",
                "value": 4.1,
                "unit": "hours",
                "performance_tier": "High",
                "performance_tier_color": "warning",
                "trend_direction": "up",
                "trend_percentage": 12.3,
            },
        }

        time_period = "30 days"
        csv_content = export_dora_to_csv(dora_metrics, time_period)

        # Parse CSV content
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)

        # Verify structure
        assert len(rows) == 4, "Should have 4 DORA metrics"

        # Verify headers
        expected_headers = [
            "Metric",
            "Value",
            "Unit",
            "Performance Tier",
            "Trend Direction",
            "Trend %",
            "Time Period",
        ]
        assert list(rows[0].keys()) == expected_headers

        # Verify first row (deployment frequency)
        assert rows[0]["Metric"] == "Deployment Frequency"
        assert rows[0]["Value"] == "12.5"
        assert rows[0]["Unit"] == "deployments/month"
        assert rows[0]["Performance Tier"] == "High"
        assert rows[0]["Trend Direction"] == "up"
        assert rows[0]["Trend %"] == "15.2"
        assert rows[0]["Time Period"] == "30 days"

    def test_export_dora_metrics_csv_with_errors(self):
        """Test DORA metrics CSV export handles error states."""
        from data.metrics_export import export_dora_to_csv

        dora_metrics = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": None,
                "error_state": "missing_mapping",
                "error_message": "Configure 'Deployment Date' field mapping",
                "performance_tier": None,
                "trend_direction": "stable",
                "trend_percentage": 0.0,
            },
        }

        csv_content = export_dora_to_csv(dora_metrics, "30 days")

        # Parse CSV content
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)

        # Verify error handling
        assert rows[0]["Value"] == "Error"
        assert rows[0]["Performance Tier"] == "N/A"

    def test_export_dora_metrics_csv_empty(self):
        """Test CSV export with empty metrics."""
        from data.metrics_export import export_dora_to_csv

        csv_content = export_dora_to_csv({}, "30 days")

        # Parse CSV content
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)

        # Should have headers but no data rows
        assert len(rows) == 0


class TestExportFlowMetricsToCSV:
    """Test Flow metrics CSV export."""

    def test_export_flow_metrics_to_csv(self):
        """Test Flow metrics export to CSV format."""
        from data.metrics_export import export_flow_to_csv

        # Sample Flow metrics data
        flow_metrics = {
            "velocity": {
                "metric_name": "velocity",
                "value": 45.0,
                "unit": "items/week",
                "trend_direction": "up",
                "trend_percentage": 10.5,
            },
            "flow_time": {
                "metric_name": "flow_time",
                "value": 8.3,
                "unit": "days",
                "trend_direction": "down",
                "trend_percentage": -5.2,
            },
            "flow_efficiency": {
                "metric_name": "flow_efficiency",
                "value": 42.5,
                "unit": "%",
                "trend_direction": "up",
                "trend_percentage": 7.8,
            },
            "flow_load": {
                "metric_name": "flow_load",
                "value": 125,
                "unit": "items",
                "trend_direction": "stable",
                "trend_percentage": 1.2,
            },
            "flow_distribution": {
                "metric_name": "flow_distribution",
                "value": {
                    "Feature": 65.0,
                    "Bug": 20.0,
                    "Technical Debt": 10.0,
                    "Risk": 5.0,
                },
                "unit": "%",
                "trend_direction": "stable",
                "trend_percentage": 2.1,
            },
        }

        time_period = "30 days"
        csv_content = export_flow_to_csv(flow_metrics, time_period)

        # Parse CSV content
        csv_reader = csv.DictReader(StringIO(csv_content))
        rows = list(csv_reader)

        # Verify structure (5 metrics total)
        assert len(rows) == 5, "Should have 5 Flow metrics"

        # Verify headers
        expected_headers = [
            "Metric",
            "Value",
            "Unit",
            "Trend Direction",
            "Trend %",
            "Time Period",
        ]
        assert list(rows[0].keys()) == expected_headers

        # Verify first row (velocity)
        assert rows[0]["Metric"] == "Flow Velocity"
        assert rows[0]["Value"] == "45.0"
        assert rows[0]["Unit"] == "items/week"
        assert rows[0]["Trend Direction"] == "up"
        assert rows[0]["Trend %"] == "10.5"

        # Verify distribution row (should serialize dict as JSON string)
        distribution_row = [r for r in rows if r["Metric"] == "Flow Distribution"][0]
        assert "Feature" in distribution_row["Value"]
        assert "65.0" in distribution_row["Value"]


class TestExportDORAMetricsToJSON:
    """Test DORA metrics JSON export."""

    def test_export_dora_metrics_to_json(self):
        """Test DORA metrics export to JSON format."""
        from data.metrics_export import export_dora_to_json

        # Sample DORA metrics data
        dora_metrics = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 12.5,
                "unit": "deployments/month",
                "performance_tier": "High",
                "trend_direction": "up",
                "trend_percentage": 15.2,
            },
            "lead_time_for_changes": {
                "metric_name": "lead_time_for_changes",
                "value": 3.2,
                "unit": "days",
                "performance_tier": "Elite",
                "trend_direction": "down",
                "trend_percentage": -8.5,
            },
        }

        time_period = "30 days"
        json_content = export_dora_to_json(dora_metrics, time_period)

        # Parse JSON content
        data = json.loads(json_content)

        # Verify structure
        assert "export_date" in data
        assert "time_period" in data
        assert "metrics" in data
        assert data["time_period"] == "30 days"

        # Verify metrics
        assert "deployment_frequency" in data["metrics"]
        assert data["metrics"]["deployment_frequency"]["value"] == 12.5
        assert data["metrics"]["deployment_frequency"]["performance_tier"] == "High"
        assert data["metrics"]["deployment_frequency"]["trend_direction"] == "up"

    def test_export_dora_metrics_json_includes_metadata(self):
        """Test JSON export includes export metadata."""
        from data.metrics_export import export_dora_to_json

        dora_metrics = {
            "deployment_frequency": {
                "metric_name": "deployment_frequency",
                "value": 12.5,
                "unit": "deployments/month",
            }
        }

        json_content = export_dora_to_json(dora_metrics, "30 days")
        data = json.loads(json_content)

        # Verify metadata
        assert "export_date" in data
        assert "metric_type" in data
        assert data["metric_type"] == "DORA"

        # Verify export_date is valid ISO format
        datetime.fromisoformat(data["export_date"])


class TestExportFlowMetricsToJSON:
    """Test Flow metrics JSON export."""

    def test_export_flow_metrics_to_json(self):
        """Test Flow metrics export to JSON format."""
        from data.metrics_export import export_flow_to_json

        # Sample Flow metrics data
        flow_metrics = {
            "velocity": {
                "metric_name": "velocity",
                "value": 45.0,
                "unit": "items/week",
                "trend_direction": "up",
                "trend_percentage": 10.5,
            },
            "flow_distribution": {
                "metric_name": "flow_distribution",
                "value": {
                    "Feature": 65.0,
                    "Bug": 20.0,
                },
                "unit": "%",
            },
        }

        time_period = "90 days"
        json_content = export_flow_to_json(flow_metrics, time_period)

        # Parse JSON content
        data = json.loads(json_content)

        # Verify structure
        assert "export_date" in data
        assert "time_period" in data
        assert "metric_type" in data
        assert data["metric_type"] == "Flow"
        assert data["time_period"] == "90 days"

        # Verify metrics
        assert "velocity" in data["metrics"]
        assert data["metrics"]["velocity"]["value"] == 45.0

        # Verify distribution preserves nested structure
        assert "flow_distribution" in data["metrics"]
        assert isinstance(data["metrics"]["flow_distribution"]["value"], dict)
        assert data["metrics"]["flow_distribution"]["value"]["Feature"] == 65.0


class TestExportHelperFunctions:
    """Test export helper functions."""

    def test_format_metric_name_for_display(self):
        """Test metric name formatting for display."""
        from data.metrics_export import _format_metric_name

        assert _format_metric_name("deployment_frequency") == "Deployment Frequency"
        assert _format_metric_name("lead_time_for_changes") == "Lead Time for Changes"
        assert _format_metric_name("flow_velocity") == "Flow Velocity"
        assert _format_metric_name("mean_time_to_recovery") == "Mean Time to Recovery"

    def test_format_value_for_csv(self):
        """Test value formatting for CSV output."""
        from data.metrics_export import _format_value_for_csv

        # Simple values
        assert _format_value_for_csv(12.5) == "12.5"
        assert _format_value_for_csv(None) == "Error"

        # Dict values (for distribution)
        value_dict = {"Feature": 65.0, "Bug": 20.0}
        result = _format_value_for_csv(value_dict)
        assert "Feature: 65.0" in result
        assert "Bug: 20.0" in result
