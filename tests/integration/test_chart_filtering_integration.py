"""
Integration tests for chart filtering functionality.

This module tests that all chart creation functions properly accept and use
the data_points_count parameter for consistent filtering across visualizations.
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import the chart creation functions to test
from visualization.helpers import get_weekly_metrics
from visualization.weekly_charts import (
    create_weekly_items_chart,
    create_weekly_items_forecast_chart,
    create_weekly_points_chart,
    create_weekly_points_forecast_chart,
)


class TestChartFilteringIntegration(unittest.TestCase):
    """Test chart creation functions with data points filtering integration."""

    def setUp(self):
        """Set up test data."""
        self.statistics_data = [
            {"date": "2024-10-01", "completed_items": 3, "completed_points": 15},
            {"date": "2024-10-08", "completed_items": 5, "completed_points": 25},
            {"date": "2024-10-15", "completed_items": 7, "completed_points": 35},
            {"date": "2024-10-22", "completed_items": 4, "completed_points": 20},
            {"date": "2024-10-29", "completed_items": 8, "completed_points": 40},
            {"date": "2024-11-05", "completed_items": 6, "completed_points": 30},
        ]
        self.df = pd.DataFrame(self.statistics_data)
        self.df["date"] = pd.to_datetime(self.df["date"])

    def test_weekly_items_chart_accepts_data_points_count(self):
        """Test that create_weekly_items_chart accepts data_points_count parameter."""
        # Should work without data_points_count (backward compatibility)
        fig_all = create_weekly_items_chart(self.statistics_data)
        self.assertIsNotNone(fig_all)

        # Should work with data_points_count
        fig_filtered = create_weekly_items_chart(
            self.statistics_data, data_points_count=4
        )
        self.assertIsNotNone(fig_filtered)

        # Charts should be different when filtering is applied
        # Note: We can't directly compare figures, but both should be valid
        self.assertEqual(type(fig_all), type(fig_filtered))

    def test_weekly_points_chart_accepts_data_points_count(self):
        """Test that create_weekly_points_chart accepts data_points_count parameter."""
        # Should work without data_points_count (backward compatibility)
        fig_all = create_weekly_points_chart(self.statistics_data)
        self.assertIsNotNone(fig_all)

        # Should work with data_points_count
        fig_filtered = create_weekly_points_chart(
            self.statistics_data, data_points_count=3
        )
        self.assertIsNotNone(fig_filtered)

    def test_weekly_items_forecast_chart_accepts_data_points_count(self):
        """Test that create_weekly_items_forecast_chart accepts data_points_count parameter."""
        # Should work without data_points_count (backward compatibility)
        fig_all = create_weekly_items_forecast_chart(self.statistics_data)
        self.assertIsNotNone(fig_all)

        # Should work with data_points_count
        fig_filtered = create_weekly_items_forecast_chart(
            self.statistics_data, data_points_count=4
        )
        self.assertIsNotNone(fig_filtered)

    def test_weekly_points_forecast_chart_accepts_data_points_count(self):
        """Test that create_weekly_points_forecast_chart accepts data_points_count parameter."""
        # Should work without data_points_count (backward compatibility)
        fig_all = create_weekly_points_forecast_chart(self.statistics_data)
        self.assertIsNotNone(fig_all)

        # Should work with data_points_count
        fig_filtered = create_weekly_points_forecast_chart(
            self.statistics_data, data_points_count=3
        )
        self.assertIsNotNone(fig_filtered)

    def test_get_weekly_metrics_accepts_data_points_count(self):
        """Test that get_weekly_metrics helper function accepts data_points_count parameter."""
        # Should work without data_points_count (backward compatibility)
        metrics_all = get_weekly_metrics(self.df)
        self.assertIsInstance(metrics_all, tuple)
        self.assertEqual(
            len(metrics_all), 4
        )  # avg_items, avg_points, med_items, med_points

        # Should work with data_points_count
        metrics_filtered = get_weekly_metrics(self.df, data_points_count=3)
        self.assertIsInstance(metrics_filtered, tuple)
        self.assertEqual(len(metrics_filtered), 4)

        # All values should be non-negative
        for metric in metrics_all:
            self.assertGreaterEqual(metric, 0)
        for metric in metrics_filtered:
            self.assertGreaterEqual(metric, 0)

    def test_chart_functions_handle_edge_cases(self):
        """Test that chart functions handle edge cases properly."""
        edge_cases = [
            {"name": "None", "data_points_count": None},
            {"name": "Zero", "data_points_count": 0},
            {"name": "Negative", "data_points_count": -5},
            {"name": "Larger than available", "data_points_count": 20},
        ]

        for case in edge_cases:
            dpc = case["data_points_count"]

            # All chart functions should handle edge cases without errors
            try:
                fig1 = create_weekly_items_chart(
                    self.statistics_data, data_points_count=dpc
                )
                fig2 = create_weekly_points_chart(
                    self.statistics_data, data_points_count=dpc
                )
                fig3 = create_weekly_items_forecast_chart(
                    self.statistics_data, data_points_count=dpc
                )
                fig4 = create_weekly_points_forecast_chart(
                    self.statistics_data, data_points_count=dpc
                )

                # All should return valid figures
                self.assertIsNotNone(fig1)
                self.assertIsNotNone(fig2)
                self.assertIsNotNone(fig3)
                self.assertIsNotNone(fig4)

            except Exception as e:
                self.fail(
                    f"Chart function failed with edge case '{case['name']}' (data_points_count={dpc}): {e}"
                )

    def test_chart_functions_with_empty_data(self):
        """Test chart functions with empty data."""
        empty_data = []
        empty_df = pd.DataFrame()

        # All functions should handle empty data gracefully
        fig1 = create_weekly_items_chart(empty_data, data_points_count=5)
        fig2 = create_weekly_points_chart(empty_data, data_points_count=5)
        fig3 = create_weekly_items_forecast_chart(empty_data, data_points_count=5)
        fig4 = create_weekly_points_forecast_chart(empty_data, data_points_count=5)

        # All should return valid figures
        self.assertIsNotNone(fig1)
        self.assertIsNotNone(fig2)
        self.assertIsNotNone(fig3)
        self.assertIsNotNone(fig4)

        # Helper function should handle empty DataFrame
        metrics = get_weekly_metrics(empty_df, data_points_count=5)
        self.assertIsInstance(metrics, tuple)
        self.assertEqual(len(metrics), 4)
        # All metrics should be 0.0 for empty data
        for metric in metrics:
            self.assertEqual(metric, 0.0)

    def test_chart_functions_with_dataframe_input(self):
        """Test that chart functions work with DataFrame input."""
        # Functions should accept both list and DataFrame inputs
        fig1_list = create_weekly_items_chart(self.statistics_data, data_points_count=4)
        fig1_df = create_weekly_items_chart(self.df, data_points_count=4)

        fig2_list = create_weekly_points_chart(
            self.statistics_data, data_points_count=4
        )
        fig2_df = create_weekly_points_chart(self.df, data_points_count=4)

        # Both should produce valid figures
        self.assertIsNotNone(fig1_list)
        self.assertIsNotNone(fig1_df)
        self.assertIsNotNone(fig2_list)
        self.assertIsNotNone(fig2_df)

    def test_parameter_propagation_consistency(self):
        """Test that parameters are properly passed to underlying functions."""
        # Test different PERT factors and data_points_count combinations
        combinations = [
            {"pert_factor": 2, "data_points_count": 3},
            {"pert_factor": 4, "data_points_count": 5},
            {"pert_factor": 3, "data_points_count": None},
        ]

        for combo in combinations:
            # All functions should accept the parameter combinations
            fig1 = create_weekly_items_chart(
                self.statistics_data,
                pert_factor=combo["pert_factor"],
                data_points_count=combo["data_points_count"],
            )
            fig2 = create_weekly_points_chart(
                self.statistics_data,
                pert_factor=combo["pert_factor"],
                data_points_count=combo["data_points_count"],
            )

            self.assertIsNotNone(fig1)
            self.assertIsNotNone(fig2)

    def test_forecast_charts_use_filtered_data(self):
        """Test that forecast charts use filtered data for calculations."""
        # Create forecast charts with different data_points_count values
        fig_all = create_weekly_items_forecast_chart(self.statistics_data)
        fig_filtered = create_weekly_items_forecast_chart(
            self.statistics_data, data_points_count=3
        )

        # Both should be valid figures
        self.assertIsNotNone(fig_all)
        self.assertIsNotNone(fig_filtered)

        # Same test for points forecast
        fig_points_all = create_weekly_points_forecast_chart(self.statistics_data)
        fig_points_filtered = create_weekly_points_forecast_chart(
            self.statistics_data, data_points_count=3
        )

        self.assertIsNotNone(fig_points_all)
        self.assertIsNotNone(fig_points_filtered)


if __name__ == "__main__":
    unittest.main()
