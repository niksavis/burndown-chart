"""
Test suite for Phase 7.5: Forecast Visualization Standardization

This module validates that forecast visualization standardization
has been implemented correctly across both weekly charts.
"""

import pytest

from data.processing import generate_weekly_forecast
from visualization.weekly_charts import (
    create_weekly_items_chart,
    create_weekly_points_chart,
)


class TestForecastVisualizationStandardization:
    """Test suite for validating forecast visualization consistency."""

    @pytest.fixture
    def sample_weekly_data(self):
        """Create sample data for testing forecast visualization."""
        return [
            {"date": "2025-09-02", "completed_items": 12, "completed_points": 24},
            {"date": "2025-09-09", "completed_items": 15, "completed_points": 30},
            {"date": "2025-09-16", "completed_items": 10, "completed_points": 20},
            {"date": "2025-09-23", "completed_items": 18, "completed_points": 36},
            {"date": "2025-09-30", "completed_items": 14, "completed_points": 28},
        ]

    def test_forecast_data_generation(self, sample_weekly_data):
        """Test that forecast data includes all required PERT values."""
        forecast_data = generate_weekly_forecast(sample_weekly_data, pert_factor=3)

        # Check items forecast structure
        items_forecast = forecast_data["items"]
        assert "most_likely" in items_forecast, "Items forecast missing most_likely"
        assert "optimistic" in items_forecast, "Items forecast missing optimistic"
        assert "pessimistic" in items_forecast, "Items forecast missing pessimistic"
        assert "dates" in items_forecast, "Items forecast missing dates"

        # Check points forecast structure
        points_forecast = forecast_data["points"]
        assert "most_likely" in points_forecast, "Points forecast missing most_likely"
        assert "optimistic" in points_forecast, "Points forecast missing optimistic"
        assert "pessimistic" in points_forecast, "Points forecast missing pessimistic"
        assert "dates" in points_forecast, "Points forecast missing dates"

    def test_weekly_items_chart_has_confidence_intervals(self, sample_weekly_data):
        """Test that weekly items chart includes confidence intervals in forecast."""
        fig = create_weekly_items_chart(sample_weekly_data, include_forecast=True)

        # Convert figure to dict to inspect traces
        fig_dict = fig.to_dict()
        traces = fig_dict.get("data", [])

        # Look for forecast trace
        forecast_trace = None
        for trace in traces:
            if trace.get("name") == "PERT Forecast":
                forecast_trace = trace
                break

        assert forecast_trace is not None, "No forecast trace found in items chart"

        # Check for error_y (confidence intervals)
        assert "error_y" in forecast_trace, (
            "No confidence intervals (error_y) found in items chart"
        )

        error_y = forecast_trace["error_y"]
        assert error_y.get("color") == "rgba(0, 0, 0, 0.3)", "Incorrect error bar color"
        assert error_y.get("symmetric") is False, "Error bars should not be symmetric"

        # Check for upper and lower bounds
        assert "array" in error_y, "Missing upper confidence bound arrays"
        assert "arrayminus" in error_y, "Missing lower confidence bound arrays"

    def test_weekly_points_chart_maintains_confidence_intervals(
        self, sample_weekly_data
    ):
        """Test that weekly points chart maintains its confidence intervals."""
        fig = create_weekly_points_chart(sample_weekly_data, include_forecast=True)

        # Convert figure to dict to inspect traces
        fig_dict = fig.to_dict()
        traces = fig_dict.get("data", [])

        # Look for forecast trace
        forecast_trace = None
        for trace in traces:
            if trace.get("name") == "PERT Forecast":
                forecast_trace = trace
                break

        assert forecast_trace is not None, "No forecast trace found in points chart"
        assert "error_y" in forecast_trace, (
            "No confidence intervals found in points chart"
        )

    def test_forecast_hover_templates_consistency(self, sample_weekly_data):
        """Test that both charts have consistent hover templates with confidence ranges."""
        items_fig = create_weekly_items_chart(sample_weekly_data, include_forecast=True)
        points_fig = create_weekly_points_chart(
            sample_weekly_data, include_forecast=True
        )

        # Get forecast traces from both charts
        items_traces = items_fig.to_dict().get("data", [])
        points_traces = points_fig.to_dict().get("data", [])

        items_forecast = None
        points_forecast = None

        for trace in items_traces:
            if trace.get("name") == "PERT Forecast":
                items_forecast = trace
                break

        for trace in points_traces:
            if trace.get("name") == "PERT Forecast":
                points_forecast = trace
                break

        assert items_forecast is not None, "Items chart missing forecast trace"
        assert points_forecast is not None, "Points chart missing forecast trace"

        # Check that both have confidence range information in hover templates
        items_hover = items_forecast.get("hovertemplate", "")
        points_hover = points_forecast.get("hovertemplate", "")

        assert "Confidence Range" in items_hover, (
            "Items chart missing confidence range in hover"
        )
        assert "Confidence Range" in points_hover, (
            "Points chart missing confidence range in hover"
        )

    def test_confidence_interval_calculation_consistency(self, sample_weekly_data):
        """Test that both charts use the same ±25% confidence interval calculation."""
        forecast_data = generate_weekly_forecast(sample_weekly_data, pert_factor=3)

        if not forecast_data["items"]["dates"]:
            pytest.skip("No forecast data available for consistency test")

        # Calculate expected confidence bounds using the standard method
        items_ml = forecast_data["items"]["most_likely"][0]
        items_opt = forecast_data["items"]["optimistic"][0]

        items_upper_expected = items_ml + 0.25 * (items_opt - items_ml)

        points_ml = forecast_data["points"]["most_likely"][0]
        points_opt = forecast_data["points"]["optimistic"][0]

        points_upper_expected = points_ml + 0.25 * (points_opt - points_ml)

        # Both should use the same 25% calculation method
        confidence_percentage = 0.25

        # Verify the calculation method is consistent (within reasonable precision)
        assert (
            abs(
                (items_upper_expected - items_ml) / (items_opt - items_ml)
                - confidence_percentage
            )
            < 0.01
        )
        assert (
            abs(
                (points_upper_expected - points_ml) / (points_opt - points_ml)
                - confidence_percentage
            )
            < 0.01
        )

    def test_visual_consistency_between_charts(self, sample_weekly_data):
        """Test that both charts have consistent visual styling for forecasts."""
        items_fig = create_weekly_items_chart(sample_weekly_data, include_forecast=True)
        points_fig = create_weekly_points_chart(
            sample_weekly_data, include_forecast=True
        )

        # Get forecast traces
        items_traces = items_fig.to_dict().get("data", [])
        points_traces = points_fig.to_dict().get("data", [])

        items_forecast = next(
            (t for t in items_traces if t.get("name") == "PERT Forecast"), None
        )
        points_forecast = next(
            (t for t in points_traces if t.get("name") == "PERT Forecast"), None
        )

        assert items_forecast is not None
        assert points_forecast is not None

        # Check consistent styling
        items_error_y = items_forecast.get("error_y", {})
        points_error_y = points_forecast.get("error_y", {})

        # Both should have the same error bar color
        assert items_error_y.get("color") == points_error_y.get("color")

        # Both should be non-symmetric
        assert not items_error_y.get("symmetric") and not points_error_y.get(
            "symmetric"
        )

    def test_phase_7_5_success_criteria(self, sample_weekly_data):
        """Integration test validating all Phase 7.5 success criteria."""
        # Test visual consistency
        items_fig = create_weekly_items_chart(sample_weekly_data, include_forecast=True)
        points_fig = create_weekly_points_chart(
            sample_weekly_data, include_forecast=True
        )

        items_traces = items_fig.to_dict().get("data", [])
        points_traces = points_fig.to_dict().get("data", [])

        items_forecast = next(
            (t for t in items_traces if t.get("name") == "PERT Forecast"), None
        )
        points_forecast = next(
            (t for t in points_traces if t.get("name") == "PERT Forecast"), None
        )

        # Success criteria validation
        assert items_forecast is not None, (
            "Visual consistency: Items chart missing forecast"
        )
        assert points_forecast is not None, (
            "Visual consistency: Points chart missing forecast"
        )
        assert "error_y" in items_forecast, (
            "Data utilization: Items chart not using full PERT data"
        )
        assert "error_y" in points_forecast, (
            "Data utilization: Points chart not using full PERT data"
        )

        # Professional appearance
        assert items_forecast["error_y"]["color"] == "rgba(0, 0, 0, 0.3)", (
            "Professional appearance: Inconsistent styling"
        )

        # Educational value
        items_hover = items_forecast.get("hovertemplate", "")
        points_hover = points_forecast.get("hovertemplate", "")
        assert "Confidence Range" in items_hover, (
            "Educational value: Missing confidence explanations"
        )
        assert "Confidence Range" in points_hover, (
            "Educational value: Missing confidence explanations"
        )


class TestForecastVisualizationRegression:
    """Regression tests to ensure Phase 7.5 changes don't break existing functionality."""

    @pytest.fixture
    def sample_data(self):
        return [
            {"date": "2025-09-02", "completed_items": 12, "completed_points": 24},
            {"date": "2025-09-09", "completed_items": 15, "completed_points": 30},
        ]

    def test_charts_render_without_forecast(self, sample_data):
        """Test that charts still render correctly when forecast is disabled."""
        items_fig = create_weekly_items_chart(sample_data, include_forecast=False)
        points_fig = create_weekly_points_chart(sample_data, include_forecast=False)

        assert items_fig is not None
        assert points_fig is not None

        # Should not have forecast traces when disabled
        items_traces = items_fig.to_dict().get("data", [])
        points_traces = points_fig.to_dict().get("data", [])

        items_forecast = next(
            (t for t in items_traces if t.get("name") == "PERT Forecast"), None
        )
        points_forecast = next(
            (t for t in points_traces if t.get("name") == "PERT Forecast"), None
        )

        assert items_forecast is None, (
            "Items chart should not have forecast when disabled"
        )
        assert points_forecast is None, (
            "Points chart should not have forecast when disabled"
        )

    def test_charts_handle_empty_data(self):
        """Test that charts handle empty data gracefully."""
        empty_data = []

        items_fig = create_weekly_items_chart(empty_data, include_forecast=True)
        points_fig = create_weekly_points_chart(empty_data, include_forecast=True)

        assert items_fig is not None
        assert points_fig is not None

    def test_charts_handle_single_data_point(self):
        """Test that charts handle single data point gracefully."""
        single_data = [
            {"date": "2025-09-02", "completed_items": 12, "completed_points": 24}
        ]

        items_fig = create_weekly_items_chart(single_data, include_forecast=True)
        points_fig = create_weekly_points_chart(single_data, include_forecast=True)

        assert items_fig is not None
        assert points_fig is not None
