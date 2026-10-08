import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.processing import (
    calculate_performance_trend,
    calculate_rates,
    calculate_weekly_averages,
    generate_weekly_forecast,
)
from data.scope_metrics import (
    calculate_total_project_scope,
    calculate_weekly_scope_growth,
)
from visualization.data_preparation import prepare_visualization_data


def compute_weekly_throughput(df):
    return df


class TestMalformedInputData(unittest.TestCase):
    def test_missing_dates(self):
        data = pd.DataFrame(
            {
                "date": ["2025-01-01", None, "2025-01-15", "2025-01-22", ""],
                "completed_items": [5, 7, 8, 6, 9],
                "completed_points": [20, 35, 40, 25, 45],
                "remaining_items": [45, 38, 30, 24, 15],
                "remaining_points": [225, 190, 150, 125, 80],
            }
        )

        try:
            result = calculate_total_project_scope(data, 15, 80)

            self.assertIsNotNone(result)
            self.assertIn("total_items", result)
            self.assertIn("total_points", result)
        except Exception as e:
            self.fail(
                f"calculate_total_project_scope raised {type(e).__name__} unexpectedly!"
            )

    def test_non_numeric_values(self):
        data = pd.DataFrame(
            {
                "date": [
                    "2025-01-01",
                    "2025-01-08",
                    "2025-01-15",
                    "2025-01-22",
                    "2025-01-29",
                ],
                "completed_items": [5, "seven", 4, 6, 8],
                "completed_points": [
                    25,
                    35,
                    "twenty",
                    30,
                    40,
                ],
                "created_items": [2, 3, 1, "two", 4],
                "created_points": [10, 15, 5, 10, "twenty"],
                "remaining_items": [45, 40, 37, 33, 29],
                "remaining_points": [225, 200, 185, 165, 145],
            }
        )

        data["date"] = pd.to_datetime(data["date"], errors="coerce")

        try:
            data_list = data.to_dict("records")

            avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
                data_list
            )

            self.assertIsInstance(avg_items, (int, float))
            self.assertFalse(pd.isna(avg_items))
            self.assertFalse(pd.isna(avg_points))

        except Exception as e:
            self.fail(
                f"calculate_weekly_averages raised {type(e).__name__} unexpectedly!"
            )

    def test_out_of_order_dates(self):
        data = pd.DataFrame(
            {
                "date": [
                    "2025-01-29",
                    "2025-01-08",
                    "2025-01-22",
                    "2025-01-01",
                    "2025-01-15",
                ],
                "completed_items": [8, 7, 6, 5, 4],
                "completed_points": [40, 35, 30, 25, 20],
                "created_items": [4, 3, 2, 2, 1],
                "created_points": [20, 15, 10, 10, 5],
                "remaining_items": [29, 40, 33, 45, 37],
                "remaining_points": [145, 200, 165, 225, 185],
            }
        )

        data["date"] = pd.to_datetime(data["date"])

        try:
            result = calculate_weekly_scope_growth(data)

            self.assertIsNotNone(result)
            if len(result) > 0:
                dates = result["start_date"].tolist()
                sorted_dates = sorted(dates)
                self.assertEqual(dates, sorted_dates)

        except Exception as e:
            self.fail(
                f"calculate_weekly_scope_growth raised {type(e).__name__} unexpectedly!"
            )

    def test_extreme_values(self):
        data = pd.DataFrame(
            {
                "date": [
                    "2025-01-01",
                    "2025-01-08",
                    "2025-01-15",
                    "2025-01-22",
                    "2025-01-29",
                ],
                "completed_items": [5, 7, 4, 6, 99999],
                "completed_points": [25, 35, 20, 30, 999999],
                "created_items": [2, 3, 1, 2, 4],
                "created_points": [10, 15, 5, 10, 20],
                "remaining_items": [45, 40, 37, 33, 29],
                "remaining_points": [225, 200, 185, 165, 145],
            }
        )

        data["date"] = pd.to_datetime(data["date"])

        try:
            data_dict_list = data.to_dict("records")

            trend = calculate_performance_trend(data_dict_list, "completed_items")

            self.assertIsNotNone(trend)
            self.assertIn("trend_direction", trend)
            self.assertIn(trend["trend_direction"], ["up", "down", "stable"])

        except Exception as e:
            self.fail(
                f"calculate_performance_trend raised {type(e).__name__} unexpectedly!"
            )


class TestLargeDatasets(unittest.TestCase):
    def setUp(self):
        num_points = 1000
        start_date = datetime(2020, 1, 1)

        dates = [start_date + timedelta(days=i) for i in range(num_points)]

        np.random.seed(42)

        initial_remaining = 5000
        daily_completion_rate = 5

        completed_items = []
        completed_points = []
        remaining_items = []
        remaining_points = []
        created_items = []
        created_points = []

        for i in range(num_points):
            day_completed = max(0, int(daily_completion_rate + np.random.normal(0, 2)))

            day_created = 0
            if np.random.random() < 0.2:
                day_created = max(0, int(np.random.normal(3, 2)))

            if i == 0:
                completed = day_completed
                remaining = initial_remaining - day_completed + day_created
            else:
                completed = day_completed
                remaining = remaining_items[-1] - day_completed + day_created

            completed_items.append(completed)
            completed_points.append(completed * 5)
            remaining_items.append(remaining)
            remaining_points.append(remaining * 5)
            created_items.append(day_created)
            created_points.append(day_created * 5)

        self.large_data = pd.DataFrame(
            {
                "date": dates,
                "completed_items": completed_items,
                "completed_points": completed_points,
                "created_items": created_items,
                "created_points": created_points,
                "remaining_items": remaining_items,
                "remaining_points": remaining_points,
            }
        )

        self.large_data["cum_items"] = self.large_data["remaining_items"]
        self.large_data["cum_points"] = self.large_data["remaining_points"]

        last_remaining_items = remaining_items[-1]
        last_remaining_points = remaining_points[-1]

        scope_result = calculate_total_project_scope(
            self.large_data, last_remaining_items, last_remaining_points
        )
        self.total_items = scope_result["total_items"]
        self.total_points = scope_result["total_points"]

    def test_performance_with_large_dataset(self):
        import time

        start_time = time.time()
        rates = calculate_rates(self.large_data, self.total_items, self.total_points, 3)
        rates_time = time.time() - start_time

        start_time = time.time()
        forecast = generate_weekly_forecast(self.large_data, 3, 12)
        forecast_time = time.time() - start_time

        start_time = time.time()
        viz_data = prepare_visualization_data(
            self.large_data, self.total_items, self.total_points, 3
        )
        viz_time = time.time() - start_time

        print(f"Large dataset ({len(self.large_data)} rows) processing times:")
        print(f"  Calculate rates: {rates_time:.4f}s")
        print(f"  Generate forecast: {forecast_time:.4f}s")
        print(f"  Prepare visualization: {viz_time:.4f}s")

        self.assertIsNotNone(rates)
        self.assertIsNotNone(forecast)
        self.assertIsNotNone(viz_data)


class TestMultiYearProjectData(unittest.TestCase):
    def setUp(self):
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 12, 31)

        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=7)

        num_weeks = len(dates)
        total_scope = 500
        weekly_progress = total_scope / num_weeks

        completed_items = []
        remaining_items = []

        for i in range(num_weeks):
            week_completed = int(weekly_progress)
            if i == 0:
                week_remaining = total_scope - week_completed
            else:
                week_remaining = remaining_items[-1] - week_completed

            completed_items.append(week_completed)
            remaining_items.append(week_remaining)

        self.multi_year_data = pd.DataFrame(
            {
                "date": dates,
                "completed_items": completed_items,
                "completed_points": [item * 5 for item in completed_items],
                "created_items": [0] * num_weeks,
                "created_points": [0] * num_weeks,
                "remaining_items": remaining_items,
                "remaining_points": [item * 5 for item in remaining_items],
            }
        )

    def test_year_transitions(self):
        growth_data = calculate_weekly_scope_growth(self.multi_year_data)

        self.assertTrue(all("W" in week for week in growth_data["week_label"]))
        self.assertTrue(all(len(week) >= 7 for week in growth_data["week_label"]))

        year_transitions = 0
        prev_year = None
        for week_label in growth_data["week_label"]:
            year = int(week_label.split("-")[0])
            if prev_year is not None and year != prev_year:
                year_transitions += 1
            prev_year = year

        self.assertGreaterEqual(year_transitions, 3)

    def test_date_formatting_multi_year(self):
        result = compute_weekly_throughput(self.multi_year_data)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("completed_items", result.columns)
        self.assertIn("completed_points", result.columns)


if __name__ == "__main__":
    unittest.main()
