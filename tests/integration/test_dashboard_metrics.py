import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.processing import (
    calculate_rates,
    calculate_weekly_averages,
)
from data.scope_metrics import calculate_total_project_scope
from visualization.data_preparation import prepare_visualization_data


class TestDashboardMetricsConsistency(unittest.TestCase):
    def setUp(self):
        start_date = datetime(2025, 1, 1)
        dates = [
            (start_date + timedelta(days=7 * i)).strftime("%Y-%m-%d") for i in range(10)
        ]

        self.statistics_data = pd.DataFrame(
            {
                "date": pd.to_datetime(dates),
                "completed_items": [5, 7, 4, 6, 8, 5, 9, 7, 3, 6],
                "completed_points": [25, 35, 20, 30, 40, 25, 45, 35, 15, 30],
                "created_items": [2, 3, 1, 2, 4, 1, 0, 3, 5, 2],
                "created_points": [10, 15, 5, 10, 20, 5, 0, 15, 25, 10],
                "remaining_items": [45, 40, 37, 33, 29, 25, 16, 12, 14, 10],
                "remaining_points": [225, 200, 185, 165, 145, 125, 80, 60, 70, 50],
            }
        )

        self.statistics_data["cum_items"] = self.statistics_data["remaining_items"]
        self.statistics_data["cum_points"] = self.statistics_data["remaining_points"]

        last_remaining_items = self.statistics_data["remaining_items"].iloc[-1]
        last_remaining_points = self.statistics_data["remaining_points"].iloc[-1]

        scope_result = calculate_total_project_scope(
            self.statistics_data, last_remaining_items, last_remaining_points
        )
        self.total_items = scope_result["total_items"]
        self.total_points = scope_result["total_points"]

        self.pert_factor = 3

    def test_weekly_rates_consistency(self):

        avg_weekly_items, avg_weekly_points, _, _ = calculate_weekly_averages(
            self.statistics_data
        )

        items_daily_rate = avg_weekly_items / 7

        df = pd.DataFrame(self.statistics_data)
        actual_daily_rate = df["completed_items"].mean() / 7

        tolerance = 0.9 if items_daily_rate > 0 else 0.001
        self.assertLessEqual(
            abs(actual_daily_rate - items_daily_rate) / items_daily_rate, tolerance
        )

    def test_pert_forecast_consistency(self):
        (
            pert_time_items,
            optimistic_items_rate,
            pessimistic_items_rate,
            pert_time_points,
            optimistic_points_rate,
            pessimistic_points_rate,
        ) = calculate_rates(
            self.statistics_data, self.total_items, self.total_points, self.pert_factor
        )

        viz_data = prepare_visualization_data(
            self.statistics_data, self.total_items, self.total_points, self.pert_factor
        )

        self.assertAlmostEqual(pert_time_items, viz_data["pert_time_items"], places=1)
        self.assertAlmostEqual(pert_time_points, viz_data["pert_time_points"], places=1)

    def test_forecast_calculations_consistency(self):
        rates = calculate_rates(
            self.statistics_data, self.total_items, self.total_points, self.pert_factor
        )
        items_daily_rate = rates[1]

        viz_data = prepare_visualization_data(
            self.statistics_data, self.total_items, self.total_points, self.pert_factor
        )

        if "items_forecasts" in viz_data and "opt" in viz_data["items_forecasts"]:
            dates, values = viz_data["items_forecasts"]["opt"]
            if len(dates) > 1 and len(values) > 1:
                values[0]
                days_elapsed = (dates[1] - dates[0]).days
                if days_elapsed > 0:
                    actual_daily_rate = (values[0] - values[1]) / days_elapsed

                    if items_daily_rate > 0:
                        ratio = actual_daily_rate / items_daily_rate
                        self.assertGreater(ratio, 0.5)
                        self.assertLess(ratio, 1.5)


if __name__ == "__main__":
    unittest.main()
