"""
Unit tests for forecast calculation functions in metrics_calculator.py (Feature 009).

Tests cover:
- calculate_forecast(): 4-week weighted average with building baseline support
- calculate_trend_vs_forecast(): Trend direction and deviation calculation
- calculate_flow_load_range(): WIP range calculation for Flow Load
- Performance benchmarks: <5ms per metric, <50ms for all 9 metrics

Test organization follows TDD approach with test classes per function.
"""

import time

import pytest

from data.metrics_calculator import (
    calculate_ewma_forecast,
    calculate_flow_load_range,
    calculate_forecast,
    calculate_trend_vs_forecast,
)


class TestCalculateForecast:
    """Tests for calculate_forecast() function."""

    def test_standard_4_week_forecast(self):
        """T008: Test standard 4-week weighted forecast calculation."""
        historical_values = [10.0, 12.0, 11.0, 13.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        assert result["forecast_value"] == 11.9  # (10*0.1 + 12*0.2 + 11*0.3 + 13*0.4)
        assert result["confidence"] == "established"
        assert result["weeks_available"] == 4
        assert result["weights_applied"] == [0.1, 0.2, 0.3, 0.4]

    def test_building_baseline_2_weeks(self):
        """T009: Test forecast with 2-week baseline (equal weighting)."""
        historical_values = [10.0, 12.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        assert result["forecast_value"] == 11.0  # (10*0.5 + 12*0.5)
        assert result["confidence"] == "building"
        assert result["weeks_available"] == 2
        assert result["weights_applied"] == [0.5, 0.5]

    def test_building_baseline_3_weeks(self):
        """T010: Test forecast with 3-week baseline (equal weighting)."""
        historical_values = [10.0, 11.0, 12.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        # Equal weights: each week gets 1/3 ≈ 0.333...
        expected = (10.0 + 11.0 + 12.0) / 3.0
        assert result["forecast_value"] == round(expected, 1)  # 11.0
        assert result["confidence"] == "building"
        assert result["weeks_available"] == 3

    def test_insufficient_data_1_week(self):
        """T011: Test forecast returns None with <2 weeks of data."""
        historical_values = [10.0]
        result = calculate_forecast(historical_values, min_weeks=2)

        assert result is None

    def test_zero_values_in_history(self):
        """T012: Test forecast handles zero values correctly."""
        historical_values = [10.0, 0.0, 11.0, 13.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        expected = 10 * 0.1 + 0 * 0.2 + 11 * 0.3 + 13 * 0.4  # = 8.5
        assert result["forecast_value"] == round(expected, 1)
        assert result["confidence"] == "established"

    def test_negative_values_raise_error(self):
        """T013: Test forecast raises ValueError for negative values."""
        historical_values = [10.0, 12.0, -5.0, 13.0]

        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_forecast(historical_values)


class TestCalculateTrendVsForecast:
    """Tests for calculate_trend_vs_forecast() function."""

    def test_higher_better_above_threshold(self):
        """T014: Test higher_better metric performing above forecast."""
        result = calculate_trend_vs_forecast(
            current_value=16.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↗"
        assert result["deviation_percent"] == pytest.approx(23.1, abs=0.1)
        assert result["status_text"] == "+23% above forecast"
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True

    def test_higher_better_below_threshold(self):
        """T015: Test higher_better metric performing below forecast."""
        result = calculate_trend_vs_forecast(
            current_value=5.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-61.5, abs=0.1)
        assert "-62% vs forecast" in result["status_text"]
        assert result["color_class"] == "text-danger"
        assert result["is_good"] is False

    def test_lower_better_below_threshold(self):
        """T016: Test lower_better metric (e.g., Lead Time) below forecast."""
        result = calculate_trend_vs_forecast(
            current_value=2.0, forecast_value=3.0, metric_type="lower_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-33.3, abs=0.1)
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True

    def test_higher_better_on_track(self):
        """T017: Test metric within ±10% threshold (on track)."""
        result = calculate_trend_vs_forecast(
            current_value=14.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "→"
        assert result["status_text"] == "On track"
        assert result["color_class"] == "text-success"  # On track is good performance
        assert result["is_good"] is True

    def test_zero_current_value_monday(self):
        """T018: Monday morning scenario with zero current value.

        Feature 009 - T046.
        """
        result = calculate_trend_vs_forecast(
            current_value=0.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-100.0)
        assert (
            result["status_text"] == "Week starting..."
        )  # Special message for Monday morning
        assert result["color_class"] == "text-secondary"  # Neutral, not danger
        assert result["is_good"] is True  # Week starting is not a failure


class TestCalculateEwmaForecast:
    """Tests for calculate_ewma_forecast() function."""

    def test_ewma_forecast_value(self):
        """T053: Test EWMA forecast calculation."""
        historical_values = [10.0, 12.0, 14.0]
        result = calculate_ewma_forecast(historical_values, alpha=0.3)

        assert result is not None
        assert result["forecast_value"] == 11.6
        assert result["weeks_available"] == 3

    def test_ewma_invalid_alpha(self):
        """T054: Test EWMA forecast rejects invalid alpha."""
        historical_values = [10.0, 12.0]

        with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
            calculate_ewma_forecast(historical_values, alpha=1.0)


class TestCalculateFlowLoadRange:
    """Tests for calculate_flow_load_range() function."""

    def test_standard_range_calculation(self):
        """T019: Test standard ±20% range calculation."""
        result = calculate_flow_load_range(forecast_value=15.0)

        assert result["lower"] == 12.0  # 15 * 0.8
        assert result["upper"] == 18.0  # 15 * 1.2

    def test_custom_range_30_percent(self):
        """T020: Test custom range percentage (30%)."""
        result = calculate_flow_load_range(forecast_value=10.0, range_percent=0.30)

        assert result["lower"] == 7.0  # 10 * 0.7
        assert result["upper"] == 13.0  # 10 * 1.3

    def test_zero_forecast_raises_error(self):
        """T021: Test forecast=0 raises ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            calculate_flow_load_range(forecast_value=0.0)


@pytest.mark.performance
class TestForecastPerformance:
    """Performance tests for forecast calculations (Feature 009 - T083)."""

    def test_forecast_calculation_meets_performance_target(self):
        """T083: Verify forecast performance targets.

        Target: <5ms per metric, <50ms total.
        """
        historical = [10.0, 12.0, 11.0, 13.0]

        # Measure total overhead for all 9 metrics
        total_time = 0
        for _i in range(9):
            start = time.perf_counter()
            forecast = calculate_forecast(historical)
            if forecast is not None:
                _ = calculate_trend_vs_forecast(
                    15.0, forecast["forecast_value"], "higher_better"
                )
            elapsed = (time.perf_counter() - start) * 1000
            total_time += elapsed

        # Assert performance targets
        avg_per_metric = total_time / 9
        assert avg_per_metric < 5.0, (
            f"Average per metric {avg_per_metric:.3f}ms exceeds 5ms target"
        )
        assert total_time < 50.0, (
            f"Total overhead {total_time:.3f}ms exceeds 50ms target"
        )
