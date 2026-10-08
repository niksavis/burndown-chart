import time

import pytest

from data.metrics_calculator import (
    calculate_ewma_forecast,
    calculate_flow_load_range,
    calculate_forecast,
    calculate_trend_vs_forecast,
)


class TestCalculateForecast:
    def test_standard_4_week_forecast(self):
        historical_values = [10.0, 12.0, 11.0, 13.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        assert result["forecast_value"] == 11.9
        assert result["confidence"] == "established"
        assert result["weeks_available"] == 4
        assert result["weights_applied"] == [0.1, 0.2, 0.3, 0.4]

    def test_building_baseline_2_weeks(self):
        historical_values = [10.0, 12.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        assert result["forecast_value"] == 11.0
        assert result["confidence"] == "building"
        assert result["weeks_available"] == 2
        assert result["weights_applied"] == [0.5, 0.5]

    def test_building_baseline_3_weeks(self):
        historical_values = [10.0, 11.0, 12.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        expected = (10.0 + 11.0 + 12.0) / 3.0
        assert result["forecast_value"] == round(expected, 1)
        assert result["confidence"] == "building"
        assert result["weeks_available"] == 3

    def test_insufficient_data_1_week(self):
        historical_values = [10.0]
        result = calculate_forecast(historical_values, min_weeks=2)

        assert result is None

    def test_zero_values_in_history(self):
        historical_values = [10.0, 0.0, 11.0, 13.0]
        result = calculate_forecast(historical_values)

        assert result is not None
        expected = 10 * 0.1 + 0 * 0.2 + 11 * 0.3 + 13 * 0.4
        assert result["forecast_value"] == round(expected, 1)
        assert result["confidence"] == "established"

    def test_negative_values_raise_error(self):
        historical_values = [10.0, 12.0, -5.0, 13.0]

        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_forecast(historical_values)


class TestCalculateTrendVsForecast:
    def test_higher_better_above_threshold(self):
        result = calculate_trend_vs_forecast(
            current_value=16.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↗"
        assert result["deviation_percent"] == pytest.approx(23.1, abs=0.1)
        assert result["status_text"] == "+23% above forecast"
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True

    def test_higher_better_below_threshold(self):
        result = calculate_trend_vs_forecast(
            current_value=5.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-61.5, abs=0.1)
        assert "-62% vs forecast" in result["status_text"]
        assert result["color_class"] == "text-danger"
        assert result["is_good"] is False

    def test_lower_better_below_threshold(self):
        result = calculate_trend_vs_forecast(
            current_value=2.0, forecast_value=3.0, metric_type="lower_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-33.3, abs=0.1)
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True

    def test_higher_better_on_track(self):
        result = calculate_trend_vs_forecast(
            current_value=14.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "→"
        assert result["status_text"] == "On track"
        assert result["color_class"] == "text-success"
        assert result["is_good"] is True

    def test_zero_current_value_monday(self):

        result = calculate_trend_vs_forecast(
            current_value=0.0, forecast_value=13.0, metric_type="higher_better"
        )

        assert result["direction"] == "↘"
        assert result["deviation_percent"] == pytest.approx(-100.0)
        assert result["status_text"] == "Week starting..."
        assert result["color_class"] == "text-secondary"
        assert result["is_good"] is True


class TestCalculateEwmaForecast:
    def test_ewma_forecast_value(self):
        historical_values = [10.0, 12.0, 14.0]
        result = calculate_ewma_forecast(historical_values, alpha=0.3)

        assert result is not None
        assert result["forecast_value"] == 11.6
        assert result["weeks_available"] == 3

    def test_ewma_invalid_alpha(self):
        historical_values = [10.0, 12.0]

        with pytest.raises(ValueError, match="alpha must be between 0 and 1"):
            calculate_ewma_forecast(historical_values, alpha=1.0)


class TestCalculateFlowLoadRange:
    def test_standard_range_calculation(self):
        result = calculate_flow_load_range(forecast_value=15.0)

        assert result["lower"] == 12.0
        assert result["upper"] == 18.0

    def test_custom_range_30_percent(self):
        result = calculate_flow_load_range(forecast_value=10.0, range_percent=0.30)

        assert result["lower"] == 7.0
        assert result["upper"] == 13.0

    def test_zero_forecast_raises_error(self):
        with pytest.raises(ValueError, match="must be positive"):
            calculate_flow_load_range(forecast_value=0.0)


@pytest.mark.performance
class TestForecastPerformance:
    def test_forecast_calculation_meets_performance_target(self):

        historical = [10.0, 12.0, 11.0, 13.0]

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

        avg_per_metric = total_time / 9
        assert avg_per_metric < 5.0, (
            f"Average per metric {avg_per_metric:.3f}ms exceeds 5ms target"
        )
        assert total_time < 50.0, (
            f"Total overhead {total_time:.3f}ms exceeds 50ms target"
        )
