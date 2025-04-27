"""
Unit tests for the visualization charts module.

This module contains tests for functions that prepare data for
visualization and generate burndown/burnup chart data.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project root to the Python path so we can import the application modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the functions to test
from visualization.charts import prepare_visualization_data, generate_burndown_forecast


class TestPrepareVisualizationData(unittest.TestCase):
    """Test prepare_visualization_data() function."""

    def setUp(self):
        """Set up test data."""
        # Create sample data with realistic entries
        self.test_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=10, freq="W"),
                "completed_items": [5, 7, 4, 6, 8, 5, 9, 7, 3, 10],
                "completed_points": [25, 35, 20, 30, 40, 25, 45, 35, 15, 50],
                "created_items": [2, 3, 1, 2, 4, 1, 0, 3, 5, 2],
                "created_points": [10, 15, 5, 10, 20, 5, 0, 15, 25, 10],
                "remaining_items": [50, 45, 41, 35, 29, 24, 19, 12, 9, 0],
                "remaining_points": [250, 225, 205, 175, 145, 120, 95, 60, 45, 0],
            }
        )

        # Add the required cum_items and cum_points columns for the charts module
        self.test_data["cum_items"] = self.test_data["remaining_items"]
        self.test_data["cum_points"] = self.test_data["remaining_points"]

        # Total work values
        self.total_items = 50
        self.total_points = 250

        # Default PERT factor
        self.pert_factor = 3

    def test_basic_data_preparation(self):
        """Test basic functionality of data preparation."""
        result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=False,
        )

        # Verify the returned structure
        self.assertIsInstance(result, dict)
        expected_keys = [
            "df_calc",
            "items_forecasts",
            "points_forecasts",
            "pert_time_items",
            "pert_time_points",
        ]
        for key in expected_keys:
            self.assertIn(key, result)

        # Check that pert_time values are calculated
        self.assertIsInstance(result["pert_time_items"], (int, float, np.number))
        self.assertIsInstance(result["pert_time_points"], (int, float, np.number))

        # Check forecast sub-dictionaries
        self.assertIn("avg", result["items_forecasts"])
        self.assertIn("opt", result["items_forecasts"])
        self.assertIn("pes", result["items_forecasts"])

    def test_data_filtering(self):
        """Test that data filtering by count works correctly."""
        # Test with limited data points
        data_points_count = 5  # Use only the last 5 data points

        result_limited = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            data_points_count=data_points_count,
        )

        result_all = prepare_visualization_data(
            self.test_data, self.total_items, self.total_points, self.pert_factor
        )

        # The pert times should be different when using limited data vs all data
        self.assertNotEqual(
            result_limited["pert_time_items"], result_all["pert_time_items"]
        )

    def test_burnup_vs_burndown_mode(self):
        """Test differences between burnup and burndown modes."""
        # Get results in both modes
        burndown_result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=False,
        )

        # For burnup mode, we need to specify the scope_items and scope_points parameters
        burnup_result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=True,
            scope_items=self.total_items,  # For burnup, scope_items is required
            scope_points=self.total_points,  # For burnup, scope_points is required
        )

        # In burndown mode, the forecast should start from the remaining work
        # and go down to zero
        burndown_forecast_items = burndown_result["items_forecasts"]
        if len(burndown_forecast_items["avg"][1]) > 1:  # Check that we have values
            # Check that values are decreasing
            self.assertGreaterEqual(
                burndown_forecast_items["avg"][1][0],
                burndown_forecast_items["avg"][1][-1],
            )

        # In burnup mode, the forecast should start from the completed work
        # and go up to the total scope
        burnup_forecast_items = burnup_result["items_forecasts"]
        if len(burnup_forecast_items["avg"][1]) > 1:  # Check that we have values
            # Check that values are either stable or increasing (not decreasing)
            self.assertGreaterEqual(
                burnup_forecast_items["avg"][1][-1], burnup_forecast_items["avg"][1][0]
            )

    def test_empty_dataframe(self):
        """Test behavior with empty input data."""
        empty_df = pd.DataFrame(columns=["date", "completed_items", "completed_points"])

        # Function should handle empty data gracefully
        result = prepare_visualization_data(
            empty_df, self.total_items, self.total_points, self.pert_factor
        )

        # Result should still be a properly structured dictionary
        self.assertIsInstance(result, dict)
        self.assertIn("pert_time_items", result)
        self.assertIn("pert_time_points", result)
        self.assertIn("items_forecasts", result)
        self.assertIn("points_forecasts", result)

        # PERT times should be zero or very minimal defaults
        self.assertEqual(result["pert_time_items"], 0)
        self.assertEqual(result["pert_time_points"], 0)

    def test_scope_parameter_usage(self):
        """Test that scope_items and scope_points parameters are used correctly."""
        # Define custom scope values
        scope_items = 60  # Higher than total_items
        scope_points = 300  # Higher than total_points

        result = prepare_visualization_data(
            self.test_data,
            self.total_items,
            self.total_points,
            self.pert_factor,
            is_burnup=True,
            scope_items=scope_items,
            scope_points=scope_points,
        )

        # For burnup charts, the forecast should aim to reach the specified scope
        burnup_forecast_items = result["items_forecasts"]
        if len(burnup_forecast_items["avg"][1]) > 0:
            # The target (last value) should be close to the specified scope
            self.assertAlmostEqual(
                burnup_forecast_items["avg"][1][-1], scope_items, delta=1
            )


class TestGenerateBurndownForecast(unittest.TestCase):
    """Test generate_burndown_forecast() function."""

    def setUp(self):
        """Set up test data."""
        self.last_value = 50
        self.avg_rate = 1.0  # 1 item per day
        self.opt_rate = 1.5  # 1.5 items per day (optimistic)
        self.pes_rate = 0.5  # 0.5 items per day (pessimistic)
        self.start_date = datetime.now()
        self.end_date = self.start_date + timedelta(days=60)  # Far enough in future

    def test_basic_forecast_generation(self):
        """Test basic burndown forecast generation."""
        result = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            self.end_date,
        )

        # Verify result structure
        self.assertIn("avg", result)
        self.assertIn("opt", result)
        self.assertIn("pes", result)

        # Check that each forecast has dates and values
        for forecast_type in ["avg", "opt", "pes"]:
            dates, values = result[forecast_type]
            self.assertEqual(len(dates), len(values))
            self.assertGreaterEqual(len(dates), 2)  # At least start and end points

    def test_linear_decrease(self):
        """Test that values decrease linearly at the specified rates."""
        result = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            self.end_date,
        )

        # Check average rate forecast for linear decrease
        dates, values = result["avg"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.avg_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.01)

        # Check optimistic rate forecast (faster decrease)
        dates, values = result["opt"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.opt_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.01)

        # Check pessimistic rate forecast (slower decrease)
        dates, values = result["pes"]

        for i in range(1, len(values)):
            days_elapsed = (dates[i] - dates[0]).days
            expected_value = max(0, self.last_value - (self.pes_rate * days_elapsed))
            self.assertAlmostEqual(values[i], expected_value, delta=0.01)

    def test_zero_minimum(self):
        """Test that values never go below zero."""
        # Use a high rate to ensure we hit zero before the end date
        high_rate = 5.0

        result = generate_burndown_forecast(
            self.last_value,
            high_rate,
            high_rate,
            high_rate,
            self.start_date,
            self.end_date,
        )

        # Check that no value goes below zero
        for forecast_type in ["avg", "opt", "pes"]:
            dates, values = result[forecast_type]
            for value in values:
                self.assertGreaterEqual(value, 0)

    def test_date_range_generation(self):
        """Test that dates span from start_date to end_date."""
        result = generate_burndown_forecast(
            self.last_value,
            self.avg_rate,
            self.opt_rate,
            self.pes_rate,
            self.start_date,
            self.end_date,
        )

        for forecast_type in ["avg", "opt", "pes"]:
            dates, values = result[forecast_type]

            # First date should be the start date
            self.assertEqual(dates[0], self.start_date)

            # Last date should not exceed the end date
            self.assertLessEqual(dates[-1], self.end_date)

    def test_different_rates(self):
        """Test with different rate values."""
        # Use very different rates
        avg_rate = 1.0
        opt_rate = 2.0  # Twice as fast
        pes_rate = 0.5  # Half as fast

        result = generate_burndown_forecast(
            self.last_value,
            avg_rate,
            opt_rate,
            pes_rate,
            self.start_date,
            self.end_date,
        )

        # Check that optimistic forecast reaches zero faster
        dates_avg, values_avg = result["avg"]
        dates_opt, values_opt = result["opt"]
        dates_pes, values_pes = result["pes"]

        # Find days to completion for each forecast
        completion_day_avg = None
        completion_day_opt = None
        completion_day_pes = None

        for i, value in enumerate(values_avg):
            if value == 0:
                completion_day_avg = (dates_avg[i] - self.start_date).days
                break

        for i, value in enumerate(values_opt):
            if value == 0:
                completion_day_opt = (dates_opt[i] - self.start_date).days
                break

        for i, value in enumerate(values_pes):
            if value == 0:
                completion_day_pes = (dates_pes[i] - self.start_date).days
                break

        # If all forecasts reach completion in our time range
        if completion_day_avg and completion_day_opt and completion_day_pes:
            # Optimistic should complete first, pessimistic last
            self.assertLess(completion_day_opt, completion_day_avg)
            self.assertLess(completion_day_avg, completion_day_pes)


if __name__ == "__main__":
    unittest.main()
