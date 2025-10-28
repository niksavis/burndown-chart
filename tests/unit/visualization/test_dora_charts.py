"""Unit tests for DORA metrics chart generation.

T052: Unit test for trend chart generation.
Tests the DORA visualization functions including trend charts added in Phase 7.
"""

import pytest
from datetime import datetime, timedelta
from visualization.dora_charts import (
    create_deployment_frequency_trend,
    create_lead_time_trend,
    create_deployment_frequency_chart,
    create_lead_time_chart,
)


class TestCreateDeploymentFrequencyTrend:
    """Test deployment frequency trend chart generation."""

    def test_trend_chart_with_valid_data(self):
        """Test that trend chart is created with valid historical data."""
        # Create sample trend data
        base_date = datetime(2025, 1, 1)
        trend_data = [
            {
                "date": (base_date + timedelta(days=i * 7)).isoformat(),
                "value": 25 + i * 2,
            }
            for i in range(8)  # 8 weeks of data
        ]

        metric_data = {
            "value": 39.0,
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        # Verify figure was created
        assert figure is not None
        assert len(figure.data) > 0  # Should have at least one trace

        # Verify it's a line chart
        assert figure.data[0].type == "scatter"
        assert figure.data[0].mode == "lines+markers"

    def test_trend_chart_with_empty_data(self):
        """Test that trend chart handles empty data gracefully."""
        trend_data = []
        metric_data = {"value": 0, "performance_tier": "Low"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        # Should still return a figure with a message
        assert figure is not None
        assert len(figure.layout.annotations) > 0  # Should have "no data" message

    def test_trend_chart_with_single_data_point(self):
        """Test that trend chart handles single data point."""
        trend_data = [{"date": "2025-01-01", "value": 30.5}]
        metric_data = {"value": 30.5, "performance_tier": "Elite"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        # Should create figure with single point
        assert figure is not None
        assert len(figure.data) > 0


class TestCreateLeadTimeTrend:
    """Test lead time trend chart generation."""

    def test_trend_chart_with_valid_data(self):
        """Test that lead time trend chart is created with valid data."""
        base_date = datetime(2025, 1, 1)
        trend_data = [
            {
                "date": (base_date + timedelta(days=i * 7)).isoformat(),
                "value": 5.0 - i * 0.3,
            }
            for i in range(8)
        ]

        metric_data = {
            "value": 2.9,
            "performance_tier": "High",
            "performance_tier_color": "yellow",
        }

        figure = create_lead_time_trend(trend_data, metric_data)

        # Verify figure was created
        assert figure is not None
        assert len(figure.data) > 0

        # Verify it's a line chart
        assert figure.data[0].type == "scatter"
        assert figure.data[0].mode == "lines+markers"

    def test_trend_chart_with_empty_data(self):
        """Test that lead time trend chart handles empty data."""
        trend_data = []
        metric_data = {"value": 0, "performance_tier": "Low"}

        figure = create_lead_time_trend(trend_data, metric_data)

        # Should still return a figure
        assert figure is not None
        assert len(figure.layout.annotations) > 0


class TestExistingChartFunctions:
    """Test existing chart generation functions still work."""

    def test_deployment_frequency_chart_current_value(self):
        """Test deployment frequency chart with current value only."""
        metric_data = {
            "value": 35.0,
            "unit": "per month",
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        figure = create_deployment_frequency_chart(metric_data)

        # Should create a figure
        assert figure is not None
        assert len(figure.data) > 0

    def test_deployment_frequency_chart_with_historical(self):
        """Test deployment frequency chart with historical data."""
        metric_data = {
            "value": 35.0,
            "unit": "per month",
            "performance_tier": "Elite",
            "performance_tier_color": "green",
        }

        historical_data = [
            {"date": "2025-01-01", "value": 30.0},
            {"date": "2025-01-08", "value": 32.0},
            {"date": "2025-01-15", "value": 35.0},
        ]

        figure = create_deployment_frequency_chart(metric_data, historical_data)

        # Should create a figure with trend
        assert figure is not None
        assert len(figure.data) > 0

    def test_lead_time_chart_current_value(self):
        """Test lead time chart with current value only."""
        metric_data = {
            "value": 2.5,
            "unit": "days",
            "performance_tier": "High",
            "performance_tier_color": "yellow",
        }

        figure = create_lead_time_chart(metric_data)

        # Should create a figure
        assert figure is not None
        assert len(figure.data) > 0


class TestTrendChartBenchmarks:
    """Test that trend charts include performance benchmarks."""

    def test_deployment_frequency_has_benchmark_lines(self):
        """Test that deployment frequency trend includes benchmark lines."""
        trend_data = [
            {"date": "2025-01-01", "value": 25.0},
            {"date": "2025-01-08", "value": 30.0},
            {"date": "2025-01-15", "value": 35.0},
        ]
        metric_data = {"value": 35.0, "performance_tier": "Elite"}

        figure = create_deployment_frequency_trend(trend_data, metric_data)

        # Check for horizontal lines (benchmarks)
        # Plotly adds shapes for hlines
        assert figure.layout.shapes is not None
        assert len(figure.layout.shapes) > 0

    def test_lead_time_has_benchmark_lines(self):
        """Test that lead time trend includes benchmark lines."""
        trend_data = [
            {"date": "2025-01-01", "value": 5.0},
            {"date": "2025-01-08", "value": 3.0},
            {"date": "2025-01-15", "value": 2.0},
        ]
        metric_data = {"value": 2.0, "performance_tier": "High"}

        figure = create_lead_time_trend(trend_data, metric_data)

        # Check for horizontal lines (benchmarks)
        assert figure.layout.shapes is not None
        assert len(figure.layout.shapes) > 0
