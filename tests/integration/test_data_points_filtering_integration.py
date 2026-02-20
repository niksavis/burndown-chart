"""
Integration tests for data points filtering across all data processing functions.

This module tests the integration between different data processing functions
with the data_points_count parameter to ensure they work together correctly
and provide consistent filtering behavior across the application.
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

# Add the project root to the Python path so we can import the application modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the functions to test
from data.processing import (
    calculate_performance_trend,
    calculate_weekly_averages,
    generate_weekly_forecast,
)
from data.scope_metrics import (
    calculate_scope_creep_rate,
    calculate_scope_stability_index,
    calculate_weekly_scope_growth,
)


class TestDataPointsFilteringIntegration(unittest.TestCase):
    """Integration tests for data_points_count parameter implementation across data processing layer."""

    def setUp(self):
        """Set up comprehensive test data."""
        # Create realistic test data representing 12 weeks of project history
        self.statistics_data = [
            {
                "date": "2024-10-01",
                "completed_items": 3,
                "completed_points": 15,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2024-10-08",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2024-10-15",
                "completed_items": 7,
                "completed_points": 35,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2024-10-22",
                "completed_items": 4,
                "completed_points": 20,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2024-10-29",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2024-11-05",
                "completed_items": 6,
                "completed_points": 30,
                "created_items": 4,
                "created_points": 20,
            },
            {
                "date": "2024-11-12",
                "completed_items": 10,
                "completed_points": 50,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2024-11-19",
                "completed_items": 9,
                "completed_points": 45,
                "created_items": 5,
                "created_points": 25,
            },
            {
                "date": "2024-11-26",
                "completed_items": 12,
                "completed_points": 60,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2024-12-03",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2024-12-10",
                "completed_items": 15,
                "completed_points": 75,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2024-12-17",
                "completed_items": 11,
                "completed_points": 55,
                "created_items": 6,
                "created_points": 30,
            },
        ]

        # Create DataFrame version for scope metrics
        self.df = pd.DataFrame(self.statistics_data)
        self.df["date"] = pd.to_datetime(self.df["date"])

        # Baseline values for scope calculations
        self.baseline_items = 100
        self.baseline_points = 500

    def test_consistent_filtering_across_all_functions(self):
        """Test that all functions filter data consistently when given same data_points_count."""
        data_points_count = 6

        # Test all processing functions with same filtering
        weekly_avg = calculate_weekly_averages(
            self.statistics_data, data_points_count=data_points_count
        )
        forecast = generate_weekly_forecast(
            self.statistics_data, pert_factor=3, data_points_count=data_points_count
        )
        trend = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            2,
            data_points_count=data_points_count,
        )

        # Test all scope functions with same filtering
        scope_rate = calculate_scope_creep_rate(
            self.df,
            self.baseline_items,
            self.baseline_points,
            data_points_count=data_points_count,
        )
        scope_growth = calculate_weekly_scope_growth(
            self.df, data_points_count=data_points_count
        )
        scope_stability = calculate_scope_stability_index(
            self.df,
            self.baseline_items,
            self.baseline_points,
            data_points_count=data_points_count,
        )

        # All functions should return valid results
        self.assertIsInstance(weekly_avg, tuple)
        self.assertEqual(len(weekly_avg), 4)

        self.assertIsInstance(forecast, dict)
        self.assertIn("items", forecast)
        self.assertIn("points", forecast)

        self.assertIsInstance(trend, dict)
        self.assertIn("trend_direction", trend)

        self.assertIsInstance(scope_rate, dict)
        self.assertIn("items_rate", scope_rate)

        self.assertIsInstance(scope_growth, pd.DataFrame)
        self.assertLessEqual(len(scope_growth), data_points_count)

        self.assertIsInstance(scope_stability, dict)
        self.assertIn("items_stability", scope_stability)

    def test_progressive_filtering_consistency(self):
        """Test that progressively smaller data_points_count produces consistent results."""
        # Test with different filtering levels
        filter_sizes = [12, 8, 6, 4]  # From all data down to 4 weeks

        weekly_avgs = []
        forecasts = []

        for size in filter_sizes:
            avg = calculate_weekly_averages(
                self.statistics_data, data_points_count=size
            )
            forecast = generate_weekly_forecast(
                self.statistics_data, pert_factor=2, data_points_count=size
            )

            weekly_avgs.append(avg)
            forecasts.append(forecast["items"]["most_likely_value"])

        # Results should be different as we use less data
        for i in range(1, len(weekly_avgs)):
            # At least one metric should change as we filter more data
            self.assertTrue(
                weekly_avgs[i] != weekly_avgs[i - 1]
                or forecasts[i] != forecasts[i - 1],
                f"Results should differ between {filter_sizes[i - 1]} and {filter_sizes[i]} data points",
            )

    def test_forecast_and_velocity_consistency(self):
        """Test that forecast and velocity calculations use the same filtered data."""
        data_points_count = 5

        # Get velocity from weekly averages
        avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
            self.statistics_data, data_points_count=data_points_count
        )

        # Get forecast values
        forecast = generate_weekly_forecast(
            self.statistics_data, pert_factor=3, data_points_count=data_points_count
        )

        # Forecast most_likely should be related to average velocity
        # (They use the same underlying data, though different calculations)
        forecast_items = forecast["items"]["most_likely_value"]

        # Both should be positive and reasonable
        self.assertGreater(avg_items, 0)
        self.assertGreater(forecast_items, 0)

        # Forecast should be in a reasonable range relative to average
        # (allowing for PERT calculation differences)
        self.assertLess(abs(forecast_items - avg_items) / avg_items, 2.0)  # Within 200%

    def test_trend_and_scope_consistency(self):
        """Test that trend analysis and scope metrics use consistent filtering."""
        data_points_count = 4

        # Get trend for items
        trend_items = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            2,
            data_points_count=data_points_count,
        )

        # Get scope growth for same period
        scope_growth = calculate_weekly_scope_growth(
            self.df, data_points_count=data_points_count
        )

        # Both should analyze the same time period
        self.assertLessEqual(len(scope_growth), data_points_count)

        # Trend should have valid analysis
        self.assertIn(trend_items["trend_direction"], ["up", "down", "stable"])
        self.assertIsInstance(trend_items["percent_change"], (int, float))

    def test_all_functions_handle_edge_cases_consistently(self):
        """Test that all functions handle edge cases consistently."""
        edge_cases = [
            {"name": "None", "data_points_count": None},
            {"name": "Zero", "data_points_count": 0},
            {"name": "Negative", "data_points_count": -5},
            {"name": "Larger than available", "data_points_count": 50},
        ]

        for case in edge_cases:
            dpc = case["data_points_count"]

            # All functions should handle edge case without errors
            try:
                avg = calculate_weekly_averages(
                    self.statistics_data, data_points_count=dpc
                )
                forecast = generate_weekly_forecast(
                    self.statistics_data, pert_factor=2, data_points_count=dpc
                )
                trend = calculate_performance_trend(
                    self.statistics_data, "completed_items", 2, data_points_count=dpc
                )

                scope_rate = calculate_scope_creep_rate(
                    self.df,
                    self.baseline_items,
                    self.baseline_points,
                    data_points_count=dpc,
                )
                scope_growth = calculate_weekly_scope_growth(
                    self.df, data_points_count=dpc
                )
                scope_stability = calculate_scope_stability_index(
                    self.df,
                    self.baseline_items,
                    self.baseline_points,
                    data_points_count=dpc,
                )

                # All should return valid structures
                self.assertIsInstance(avg, tuple)
                self.assertIsInstance(forecast, dict)
                self.assertIsInstance(trend, dict)
                self.assertIsInstance(scope_rate, dict)
                self.assertIsInstance(scope_growth, pd.DataFrame)
                self.assertIsInstance(scope_stability, dict)

            except Exception as e:
                self.fail(
                    f"Function failed with edge case '{case['name']}' (data_points_count={dpc}): {e}"
                )

    def test_backward_compatibility_integration(self):
        """Test that all functions maintain backward compatibility when used together."""
        # Test calling all functions without data_points_count (old way)
        try:
            avg_old = calculate_weekly_averages(self.statistics_data)
            forecast_old = generate_weekly_forecast(self.statistics_data, pert_factor=3)
            trend_old = calculate_performance_trend(
                self.statistics_data, "completed_items", 2
            )

            scope_rate_old = calculate_scope_creep_rate(
                self.df, self.baseline_items, self.baseline_points
            )
            scope_growth_old = calculate_weekly_scope_growth(self.df)
            scope_stability_old = calculate_scope_stability_index(
                self.df, self.baseline_items, self.baseline_points
            )

        except Exception as e:
            self.fail(f"Backward compatibility broken: {e}")

        # Test calling all functions with data_points_count=None (should be same as old way)
        avg_none = calculate_weekly_averages(
            self.statistics_data, data_points_count=None
        )
        forecast_none = generate_weekly_forecast(
            self.statistics_data, pert_factor=3, data_points_count=None
        )
        trend_none = calculate_performance_trend(
            self.statistics_data, "completed_items", 2, data_points_count=None
        )

        scope_rate_none = calculate_scope_creep_rate(
            self.df, self.baseline_items, self.baseline_points, data_points_count=None
        )
        scope_growth_none = calculate_weekly_scope_growth(
            self.df, data_points_count=None
        )
        scope_stability_none = calculate_scope_stability_index(
            self.df, self.baseline_items, self.baseline_points, data_points_count=None
        )

        # Results should be identical
        self.assertEqual(avg_old, avg_none)
        self.assertEqual(
            forecast_old["items"]["most_likely_value"],
            forecast_none["items"]["most_likely_value"],
        )
        self.assertEqual(trend_old, trend_none)
        self.assertEqual(scope_rate_old, scope_rate_none)
        pd.testing.assert_frame_equal(scope_growth_old, scope_growth_none)
        self.assertEqual(scope_stability_old, scope_stability_none)

    def test_data_type_consistency_list_vs_dataframe(self):
        """Test that functions handle both list and DataFrame inputs consistently."""
        data_points_count = 6

        # Test with list input
        avg_list = calculate_weekly_averages(
            self.statistics_data, data_points_count=data_points_count
        )
        forecast_list = generate_weekly_forecast(
            self.statistics_data, pert_factor=2, data_points_count=data_points_count
        )
        trend_list = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            2,
            data_points_count=data_points_count,
        )

        # Test with DataFrame input (where applicable)
        df_stats = pd.DataFrame(self.statistics_data)
        avg_df = calculate_weekly_averages(
            df_stats, data_points_count=data_points_count
        )
        forecast_df = generate_weekly_forecast(
            df_stats, pert_factor=2, data_points_count=data_points_count
        )
        trend_df = calculate_performance_trend(
            df_stats, "completed_items", 2, data_points_count=data_points_count
        )

        # Results should be the same regardless of input type
        self.assertEqual(avg_list, avg_df)
        self.assertEqual(
            forecast_list["items"]["most_likely_value"],
            forecast_df["items"]["most_likely_value"],
        )
        self.assertEqual(trend_list, trend_df)

    def test_realistic_project_scenario(self):
        """Test a realistic project scenario with various data_points_count values."""
        # Simulate different analysis scenarios
        scenarios = [
            {
                "name": "Full project history",
                "data_points_count": None,
                "description": "Use all available data",
            },
            {
                "name": "Recent quarter",
                "data_points_count": 12,
                "description": "Last 3 months",
            },
            {
                "name": "Recent month",
                "data_points_count": 4,
                "description": "Last month only",
            },
            {
                "name": "Recent sprint",
                "data_points_count": 2,
                "description": "Last 2 weeks",
            },
        ]

        results = []

        for scenario in scenarios:
            dpc = scenario["data_points_count"]

            # Calculate all metrics for this scenario
            avg = calculate_weekly_averages(self.statistics_data, data_points_count=dpc)
            forecast = generate_weekly_forecast(
                self.statistics_data, pert_factor=3, data_points_count=dpc
            )
            trend = calculate_performance_trend(
                self.statistics_data, "completed_items", 2, data_points_count=dpc
            )

            scope_rate = calculate_scope_creep_rate(
                self.df,
                self.baseline_items,
                self.baseline_points,
                data_points_count=dpc,
            )

            result = {
                "scenario": scenario["name"],
                "avg_velocity": avg[0],  # avg_items
                "forecast_velocity": forecast["items"]["most_likely_value"],
                "trend": trend["trend_direction"],
                "scope_rate": scope_rate["items_rate"],
            }
            results.append(result)

        # Validate that scenarios produce reasonable and different results
        velocities = [r["avg_velocity"] for r in results]
        forecasts = [r["forecast_velocity"] for r in results]

        # All velocities should be positive
        for v in velocities:
            self.assertGreater(v, 0)

        # All forecasts should be positive
        for f in forecasts:
            self.assertGreater(f, 0)

        # At least some scenarios should produce different results
        # (unless data is perfectly uniform, which is unlikely)
        unique_velocities = len(set(f"{v:.2f}" for v in velocities))
        self.assertGreaterEqual(
            unique_velocities,
            2,
            "Different filtering scenarios should produce some variation in results",
        )


if __name__ == "__main__":
    unittest.main()
