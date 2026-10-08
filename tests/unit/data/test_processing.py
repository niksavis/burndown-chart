import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.processing import (
    calculate_performance_trend,
    calculate_rates,
    calculate_weekly_averages,
    daily_forecast,
    daily_forecast_burnup,
    generate_weekly_forecast,
)


class TestCalculateRatesNormalDataset(unittest.TestCase):
    def setUp(self):
        self.weekly_data = pd.DataFrame(
            {
                "completed_items": [5, 7, 8, 6, 9],
                "completed_points": [20, 35, 40, 25, 45],
            }
        )
        self.total_items = 30
        self.total_points = 150

    def test_pert_calculation_formula(self):
        pert_factor = 1
        result = calculate_rates(
            self.weekly_data, self.total_items, self.total_points, pert_factor
        )

        (
            pert_time_items,
            optimistic_items_rate,
            pessimistic_items_rate,
            pert_time_points,
            optimistic_points_rate,
            pessimistic_points_rate,
        ) = result

        days_per_week = 7.0
        optimistic_items_expected = (
            max(self.weekly_data["completed_items"]) / days_per_week
        )
        pessimistic_items_expected = (
            min(self.weekly_data["completed_items"]) / days_per_week
        )
        most_likely_items_expected = (
            self.weekly_data["completed_items"].mean() / days_per_week
        )

        optimistic_time_items = self.total_items / optimistic_items_expected
        most_likely_time_items = self.total_items / most_likely_items_expected
        pessimistic_time_items = self.total_items / pessimistic_items_expected

        expected_pert_time_items = (
            optimistic_time_items + 4 * most_likely_time_items + pessimistic_time_items
        ) / 6

        self.assertAlmostEqual(pert_time_items, expected_pert_time_items, places=2)

        self.assertAlmostEqual(
            optimistic_items_rate, optimistic_items_expected, places=2
        )
        self.assertAlmostEqual(
            pessimistic_items_rate, pessimistic_items_expected, places=2
        )

    def test_different_pert_factors(self):
        result_factor_1 = calculate_rates(
            self.weekly_data, self.total_items, self.total_points, 1
        )

        result_factor_2 = calculate_rates(
            self.weekly_data, self.total_items, self.total_points, 2
        )

        calculate_rates(self.weekly_data, self.total_items, self.total_points, 3)

        max_valid_factor = len(self.weekly_data) // 3
        max_valid_factor = max(max_valid_factor, 1)

        result_factor_large = calculate_rates(
            self.weekly_data, self.total_items, self.total_points, 10
        )

        if len(self.weekly_data) >= 6:
            self.assertNotEqual(
                round(result_factor_1[0], 2), round(result_factor_2[0], 2)
            )

        self.assertEqual(
            round(result_factor_large[0], 2),
            round(
                calculate_rates(
                    self.weekly_data,
                    self.total_items,
                    self.total_points,
                    max_valid_factor,
                )[0],
                2,
            ),
        )

    def test_nonzero_rates(self):
        result = calculate_rates(
            self.weekly_data, self.total_items, self.total_points, 3
        )

        self.assertGreater(result[1], 0)
        self.assertGreater(result[2], 0)
        self.assertGreater(result[4], 0)
        self.assertGreater(result[5], 0)

        min_rate = 0.001
        self.assertGreaterEqual(result[1], min_rate)
        self.assertGreaterEqual(result[2], min_rate)
        self.assertGreaterEqual(result[4], min_rate)
        self.assertGreaterEqual(result[5], min_rate)


class TestCalculateRatesSmallDataset(unittest.TestCase):
    def test_single_data_point(self):
        single_data = pd.DataFrame(
            {
                "completed_items": [4],
                "completed_points": [20],
            }
        )
        result = calculate_rates(single_data, 30, 150, 3)

        self.assertEqual(result[1], result[2])
        self.assertEqual(result[4], result[5])

        expected_items_rate = 4 / 7
        expected_points_rate = 20 / 7

        self.assertAlmostEqual(result[1], expected_items_rate, places=3)
        self.assertAlmostEqual(result[4], expected_points_rate, places=3)

    def test_two_data_points(self):
        two_data = pd.DataFrame(
            {
                "completed_items": [3, 7],
                "completed_points": [15, 35],
            }
        )
        result = calculate_rates(two_data, 30, 150, 3)

        expected_items_mean = two_data["completed_items"].mean() / 7

        self.assertAlmostEqual(result[1], expected_items_mean, places=3)
        self.assertAlmostEqual(result[2], expected_items_mean, places=3)

    def test_three_data_points(self):
        three_data = pd.DataFrame(
            {
                "completed_items": [3, 5, 7],
                "completed_points": [15, 25, 35],
            }
        )

        result = calculate_rates(three_data, 30, 150, 3)

        expected_items_mean = three_data["completed_items"].mean() / 7

        self.assertAlmostEqual(result[1], expected_items_mean, places=3)
        self.assertAlmostEqual(result[2], expected_items_mean, places=3)

        min_rate = min(three_data["completed_items"]) / 7
        max_rate = max(three_data["completed_items"]) / 7

        self.assertNotEqual(min_rate, max_rate)
        self.assertEqual(round(result[1], 4), round(result[2], 4))


class TestCalculateRatesEdgeCases(unittest.TestCase):
    def test_empty_dataset(self):
        empty_data = pd.DataFrame(columns=["completed_items", "completed_points"])
        result = calculate_rates(empty_data, 30, 150, 3)

        self.assertEqual(result, (0, 0, 0, 0, 0, 0))

    def test_dataset_with_zeros(self):
        zero_data = pd.DataFrame(
            {
                "completed_items": [0, 5, 0, 7],
                "completed_points": [0, 25, 0, 35],
            }
        )
        result = calculate_rates(zero_data, 30, 150, 3)

        self.assertGreater(result[1], 0)
        self.assertGreater(result[2], 0)

        min_rate = 0.001
        self.assertGreaterEqual(result[2], min_rate)

    def test_dataset_with_negative_values(self):
        negative_data = pd.DataFrame(
            {
                "completed_items": [-2, 5, 7],
                "completed_points": [-10, 25, 35],
            }
        )
        result = calculate_rates(negative_data, 30, 150, 3)

        min_rate = 0.001
        self.assertGreaterEqual(result[1], min_rate)
        self.assertGreaterEqual(result[2], min_rate)
        self.assertGreaterEqual(result[4], min_rate)
        self.assertGreaterEqual(result[5], min_rate)

    def test_zero_remaining_work(self):
        result = calculate_rates(
            pd.DataFrame({"completed_items": [5], "completed_points": [25]}), 0, 150, 3
        )

        self.assertGreaterEqual(result[1], 0)

        result = calculate_rates(
            pd.DataFrame({"completed_items": [5], "completed_points": [25]}), 30, 0, 3
        )

        self.assertGreaterEqual(result[4], 0)

    def test_very_large_numbers(self):
        large_data = pd.DataFrame(
            {
                "completed_items": [1000000, 2000000],
                "completed_points": [5000000, 10000000],
            }
        )
        large_total = 100000000

        result = calculate_rates(large_data, large_total, large_total, 3)

        self.assertIsNotNone(result)
        self.assertFalse(any(pd.isna(r) for r in result))
        self.assertTrue(all(isinstance(r, (int, float)) for r in result))


class TestCalculateWeeklyAverages(unittest.TestCase):
    def setUp(self):
        self.statistics_data = [
            {
                "date": "2025-01-05",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-01-12",
                "completed_items": 7,
                "completed_points": 35,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2025-01-19",
                "completed_items": 4,
                "completed_points": 20,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2025-01-26",
                "completed_items": 6,
                "completed_points": 30,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-02-02",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2025-02-09",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-02-16",
                "completed_items": 9,
                "completed_points": 45,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2025-02-23",
                "completed_items": 7,
                "completed_points": 35,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2025-03-02",
                "completed_items": 3,
                "completed_points": 15,
                "created_items": 4,
                "created_points": 20,
            },
            {
                "date": "2025-03-09",
                "completed_items": 10,
                "completed_points": 50,
                "created_items": 1,
                "created_points": 5,
            },
        ]

    def test_basic_average_calculation(self):
        result = calculate_weekly_averages(self.statistics_data)

        self.assertEqual(len(result), 4)

        items = [entry["completed_items"] for entry in self.statistics_data]
        points = [entry["completed_points"] for entry in self.statistics_data]

        expected_avg_items = sum(items) / len(items)
        expected_avg_points = sum(points) / len(points)

        sorted_items = sorted(items)
        sorted_points = sorted(points)

        if len(sorted_items) % 2 == 0:
            mid_idx = len(sorted_items) // 2
            expected_med_items = (sorted_items[mid_idx - 1] + sorted_items[mid_idx]) / 2
            expected_med_points = (
                sorted_points[mid_idx - 1] + sorted_points[mid_idx]
            ) / 2
        else:
            mid_idx = len(sorted_items) // 2
            expected_med_items = sorted_items[mid_idx]
            expected_med_points = sorted_points[mid_idx]

        self.assertAlmostEqual(result[0], expected_avg_items, places=2)
        self.assertAlmostEqual(result[1], expected_avg_points, places=2)

        self.assertAlmostEqual(result[2], expected_med_items, places=2)
        self.assertAlmostEqual(result[3], expected_med_points, places=2)

    def test_empty_dataset(self):
        result = calculate_weekly_averages([])

        self.assertEqual(result, (0.0, 0.0, 0.0, 0.0))

    def test_single_data_point(self):
        single_data = [
            {"date": "2025-01-05", "completed_items": 5, "completed_points": 25}
        ]
        result = calculate_weekly_averages(single_data)

        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], 25.0)
        self.assertEqual(result[2], 5.0)
        self.assertEqual(result[3], 25.0)

    def test_extreme_values(self):
        extreme_data = self.statistics_data.copy()
        extreme_data.append(
            {"date": "2025-03-16", "completed_items": 100, "completed_points": 500}
        )
        extreme_data.append(
            {"date": "2025-03-23", "completed_items": 0, "completed_points": 0}
        )

        result = calculate_weekly_averages(extreme_data)

        items = [entry.get("completed_items", 0) for entry in extreme_data]
        points = [entry.get("completed_points", 0) for entry in extreme_data]

        expected_avg_items = sum(items) / len(extreme_data)
        expected_avg_points = sum(points) / len(extreme_data)

        self.assertAlmostEqual(result[0], expected_avg_items, delta=2.0)
        self.assertAlmostEqual(result[1], expected_avg_points, delta=10.0)

    def test_missing_data_fields(self):
        incomplete_data = [
            {"date": "2025-01-05", "completed_items": 5},
            {"date": "2025-01-12", "completed_points": 35},
            {"date": "2025-01-19"},
        ]

        result = calculate_weekly_averages(incomplete_data)

        items = [entry.get("completed_items", 0) for entry in incomplete_data]
        points = [entry.get("completed_points", 0) for entry in incomplete_data]

        expected_avg_items = sum(items) / len(incomplete_data)
        expected_avg_points = sum(points) / len(incomplete_data)

        self.assertAlmostEqual(result[0], expected_avg_items, delta=0.1)
        self.assertAlmostEqual(result[1], expected_avg_points, delta=0.1)


class TestGenerateWeeklyForecast(unittest.TestCase):
    def setUp(self):
        self.statistics_data = [
            {
                "date": "2025-01-05",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-01-12",
                "completed_items": 7,
                "completed_points": 35,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2025-01-19",
                "completed_items": 4,
                "completed_points": 20,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2025-01-26",
                "completed_items": 6,
                "completed_points": 30,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-02-02",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2025-02-09",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2025-02-16",
                "completed_items": 9,
                "completed_points": 45,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2025-02-23",
                "completed_items": 7,
                "completed_points": 35,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2025-03-02",
                "completed_items": 3,
                "completed_points": 15,
                "created_items": 4,
                "created_points": 20,
            },
            {
                "date": "2025-03-09",
                "completed_items": 10,
                "completed_points": 50,
                "created_items": 1,
                "created_points": 5,
            },
        ]

    def test_forecast_data_structure(self):
        forecast = generate_weekly_forecast(self.statistics_data)

        self.assertIn("items", forecast)
        self.assertIn("points", forecast)

        for section in ["items", "points"]:
            self.assertIn("dates", forecast[section])
            self.assertIn("most_likely", forecast[section])
            self.assertIn("optimistic", forecast[section])
            self.assertIn("pessimistic", forecast[section])

        items_length = len(forecast["items"]["dates"])
        self.assertEqual(len(forecast["items"]["most_likely"]), items_length)
        self.assertEqual(len(forecast["items"]["optimistic"]), items_length)
        self.assertEqual(len(forecast["items"]["pessimistic"]), items_length)

        self.assertGreaterEqual(items_length, 1)

    def test_forecast_values(self):
        forecast = generate_weekly_forecast(self.statistics_data, pert_factor=2)

        items_values = [entry["completed_items"] for entry in self.statistics_data]
        points_values = [entry["completed_points"] for entry in self.statistics_data]

        if len(forecast["items"]["most_likely"]) > 0:
            forecast_most_likely_items = forecast["items"]["most_likely"][0]
            forecast_most_likely_points = forecast["points"]["most_likely"][0]

            self.assertGreater(forecast_most_likely_items, min(items_values) * 0.5)
            self.assertLess(forecast_most_likely_items, max(items_values) * 1.5)

            self.assertGreater(forecast_most_likely_points, min(points_values) * 0.5)
            self.assertLess(forecast_most_likely_points, max(points_values) * 1.5)

    def test_multiple_forecast_weeks(self):
        forecast = generate_weekly_forecast(self.statistics_data)

        self.assertGreaterEqual(len(forecast["items"]["dates"]), 1)

        if len(forecast["items"]["dates"]) > 0:
            date_str = forecast["items"]["dates"][0]
            if isinstance(date_str, str):
                self.assertTrue(
                    len(date_str) >= 5, f"Date string '{date_str}' is too short"
                )

    def test_empty_data(self):
        forecast = generate_weekly_forecast([])

        self.assertEqual(forecast["items"]["dates"], [])
        self.assertEqual(forecast["items"]["most_likely"], [])
        self.assertEqual(forecast["items"]["optimistic"], [])
        self.assertEqual(forecast["items"]["pessimistic"], [])
        self.assertEqual(forecast["points"]["dates"], [])
        self.assertEqual(forecast["points"]["most_likely"], [])
        self.assertEqual(forecast["points"]["optimistic"], [])
        self.assertEqual(forecast["points"]["pessimistic"], [])

    def test_single_data_point(self):
        single_data = [
            {"date": "2025-01-05", "completed_items": 5, "completed_points": 25}
        ]
        forecast = generate_weekly_forecast(single_data)

        self.assertTrue(len(forecast["items"]["dates"]) > 0)
        self.assertTrue(len(forecast["items"]["most_likely"]) > 0)

        if len(forecast["items"]["most_likely"]) > 0:
            most_likely = forecast["items"]["most_likely"][0]
            optimistic = forecast["items"]["optimistic"][0]
            pessimistic = forecast["items"]["pessimistic"][0]

            self.assertAlmostEqual(optimistic, most_likely * 1.2, delta=0.1)

            self.assertAlmostEqual(pessimistic, most_likely * 0.8, delta=0.1)


class TestDailyForecast(unittest.TestCase):
    def test_daily_forecast_basic(self):
        start_val = 30
        daily_rate = 1.0
        start_date = datetime.now()

        x_vals, y_vals = daily_forecast(start_val, daily_rate, start_date)

        self.assertEqual(len(x_vals), len(y_vals))
        self.assertEqual(len(x_vals), 31)

        self.assertEqual(y_vals[0], start_val)

        self.assertEqual(y_vals[-1], 0)

        for i in range(1, len(y_vals)):
            expected_val = max(0, start_val - (daily_rate * i))
            self.assertAlmostEqual(y_vals[i], expected_val, places=2)

        for i in range(1, len(x_vals)):
            days_diff = (x_vals[i] - x_vals[i - 1]).days
            self.assertEqual(days_diff, 1)

    def test_daily_forecast_burnup_basic(self):
        start_val = 10
        daily_rate = 1.0
        start_date = datetime.now()
        target_val = 40

        x_vals, y_vals = daily_forecast_burnup(
            start_val, daily_rate, start_date, target_val
        )

        self.assertEqual(len(x_vals), len(y_vals))
        self.assertEqual(len(x_vals), 31)

        self.assertEqual(y_vals[0], start_val)

        self.assertEqual(y_vals[-1], target_val)

        for i in range(1, len(y_vals) - 1):
            expected_val = min(target_val, start_val + (daily_rate * i))
            self.assertAlmostEqual(y_vals[i], expected_val, places=2)

    def test_zero_rate(self):
        start_val = 30
        daily_rate = 0
        start_date = datetime.now()

        x_vals, y_vals = daily_forecast(start_val, daily_rate, start_date)
        self.assertGreaterEqual(len(x_vals), 1)
        self.assertEqual(y_vals[0], start_val)
        x_vals, y_vals = daily_forecast_burnup(start_val, daily_rate, start_date, 40)
        self.assertGreaterEqual(len(x_vals), 1)
        self.assertEqual(y_vals[0], start_val)

    def test_very_small_rate(self):
        start_val = 30
        daily_rate = 0.0001
        start_date = datetime.now()

        x_vals, y_vals = daily_forecast(start_val, daily_rate, start_date)

        self.assertLess(len(x_vals), 5000)

        x_vals, y_vals = daily_forecast_burnup(start_val, daily_rate, start_date, 40)
        self.assertLess(len(x_vals), 5000)

    def test_max_forecast_limit(self):
        start_val = 1000
        daily_rate = 0.1
        start_date = datetime.now()

        x_vals, y_vals = daily_forecast(start_val, daily_rate, start_date)

        max_days = (x_vals[-1] - x_vals[0]).days
        self.assertLessEqual(max_days, 3653)

        target_val = 1000
        start_val = 0
        x_vals, y_vals = daily_forecast_burnup(
            start_val, daily_rate, start_date, target_val
        )

        max_days = (x_vals[-1] - x_vals[0]).days
        self.assertLessEqual(max_days, 3653)


class TestCalculatePerformanceTrend(unittest.TestCase):
    def setUp(self):
        self.upward_trend_data = [
            {"date": "2025-01-05", "completed_items": 3, "completed_points": 15},
            {"date": "2025-01-12", "completed_items": 4, "completed_points": 20},
            {"date": "2025-01-19", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-26", "completed_items": 6, "completed_points": 30},
            {"date": "2025-02-02", "completed_items": 7, "completed_points": 35},
            {"date": "2025-02-09", "completed_items": 8, "completed_points": 40},
            {"date": "2025-02-16", "completed_items": 9, "completed_points": 45},
            {"date": "2025-02-23", "completed_items": 10, "completed_points": 50},
        ]

        self.downward_trend_data = [
            {"date": "2025-01-05", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-12", "completed_items": 9, "completed_points": 45},
            {"date": "2025-01-19", "completed_items": 8, "completed_points": 40},
            {"date": "2025-01-26", "completed_items": 7, "completed_points": 35},
            {"date": "2025-02-02", "completed_items": 6, "completed_points": 30},
            {"date": "2025-02-09", "completed_items": 5, "completed_points": 25},
            {"date": "2025-02-16", "completed_items": 4, "completed_points": 20},
            {"date": "2025-02-23", "completed_items": 3, "completed_points": 15},
        ]

        self.stable_trend_data = [
            {"date": "2025-01-05", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-12", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-19", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-26", "completed_items": 5, "completed_points": 25},
            {"date": "2025-02-02", "completed_items": 5, "completed_points": 25},
            {"date": "2025-02-09", "completed_items": 5, "completed_points": 25},
            {"date": "2025-02-16", "completed_items": 5, "completed_points": 25},
            {"date": "2025-02-23", "completed_items": 5, "completed_points": 25},
        ]

    def test_upward_trend(self):
        result = calculate_performance_trend(
            self.upward_trend_data, metric="completed_items"
        )

        self.assertEqual(result["trend_direction"], "up")
        self.assertGreater(result["percent_change"], 0)

        result = calculate_performance_trend(
            self.upward_trend_data, metric="completed_points"
        )

        self.assertEqual(result["trend_direction"], "up")
        self.assertGreater(result["percent_change"], 0)

    def test_downward_trend(self):
        result = calculate_performance_trend(
            self.downward_trend_data, metric="completed_items"
        )

        self.assertEqual(result["trend_direction"], "down")
        self.assertLess(result["percent_change"], 0)

        result = calculate_performance_trend(
            self.downward_trend_data, metric="completed_points"
        )

        self.assertEqual(result["trend_direction"], "down")
        self.assertLess(result["percent_change"], 0)

    def test_stable_trend(self):
        result = calculate_performance_trend(
            self.stable_trend_data, metric="completed_items"
        )

        self.assertEqual(result["trend_direction"], "stable")
        self.assertEqual(result["percent_change"], 0)

    def test_different_comparison_windows(self):
        result = calculate_performance_trend(
            self.upward_trend_data, metric="completed_items", weeks_to_compare=2
        )

        self.assertEqual(result["trend_direction"], "up")

        small_window_change = result["percent_change"]

        result = calculate_performance_trend(
            self.upward_trend_data, metric="completed_items", weeks_to_compare=4
        )
        large_window_change = result["percent_change"]

        self.assertNotEqual(small_window_change, large_window_change)

    def test_empty_data(self):
        result = calculate_performance_trend([], metric="completed_items")

        self.assertEqual(result["trend_direction"], "stable")
        self.assertEqual(result["percent_change"], 0)
        self.assertEqual(result["is_significant"], False)

    def test_significance_threshold(self):
        small_variation_data = [
            {"date": "2025-01-05", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-12", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-19", "completed_items": 5, "completed_points": 25},
            {"date": "2025-01-26", "completed_items": 5, "completed_points": 25},
            {
                "date": "2025-02-02",
                "completed_items": 6,
                "completed_points": 30,
            },
            {"date": "2025-02-09", "completed_items": 6, "completed_points": 30},
            {"date": "2025-02-16", "completed_items": 6, "completed_points": 30},
            {"date": "2025-02-23", "completed_items": 6, "completed_points": 30},
        ]

        result = calculate_performance_trend(
            small_variation_data, metric="completed_items"
        )

        self.assertEqual(result["trend_direction"], "up")
        self.assertEqual(result["is_significant"], True)

        self.assertGreaterEqual(result["percent_change"], 20)


if __name__ == "__main__":
    unittest.main()


class TestCalculateWeeklyAveragesDataPointsFiltering(unittest.TestCase):
    def setUp(self):
        self.statistics_data = [
            {
                "date": "2024-12-01",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2024-12-08",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2024-12-15",
                "completed_items": 12,
                "completed_points": 60,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2024-12-22",
                "completed_items": 6,
                "completed_points": 30,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2024-12-29",
                "completed_items": 10,
                "completed_points": 50,
                "created_items": 4,
                "created_points": 20,
            },
            {
                "date": "2025-01-05",
                "completed_items": 15,
                "completed_points": 75,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2025-01-12",
                "completed_items": 9,
                "completed_points": 45,
                "created_items": 5,
                "created_points": 25,
            },
            {
                "date": "2025-01-19",
                "completed_items": 11,
                "completed_points": 55,
                "created_items": 1,
                "created_points": 5,
            },
        ]

    def test_data_points_count_filtering_basic(self):
        result_all = calculate_weekly_averages(self.statistics_data)

        result_filtered = calculate_weekly_averages(
            self.statistics_data, data_points_count=4
        )

        self.assertNotEqual(result_all, result_filtered)

        self.assertEqual(len(result_all), 4)
        self.assertEqual(len(result_filtered), 4)

        for value in result_filtered:
            self.assertIsInstance(value, (int, float))
            self.assertGreaterEqual(value, 0)

    @patch("data.processing_averages.get_metric_weekly_values", return_value=[])
    def test_data_points_count_larger_than_available(self, mock_snapshots):
        result_large = calculate_weekly_averages(
            self.statistics_data, data_points_count=20
        )
        result_all = calculate_weekly_averages(self.statistics_data)

        self.assertEqual(result_large, result_all)

    def test_data_points_count_zero_and_negative(self):
        result_all = calculate_weekly_averages(self.statistics_data)

        result_zero = calculate_weekly_averages(
            self.statistics_data, data_points_count=0
        )
        self.assertEqual(result_zero, result_all)

        result_negative = calculate_weekly_averages(
            self.statistics_data, data_points_count=-5
        )
        self.assertEqual(result_negative, result_all)

    def test_data_points_count_none_backward_compatibility(self):
        result_none = calculate_weekly_averages(
            self.statistics_data, data_points_count=None
        )
        result_default = calculate_weekly_averages(self.statistics_data)

        self.assertEqual(result_none, result_default)

    def test_data_points_count_with_dataframe(self):
        df = pd.DataFrame(self.statistics_data)

        result_all = calculate_weekly_averages(df)

        result_filtered = calculate_weekly_averages(df, data_points_count=4)

        self.assertNotEqual(result_all, result_filtered)

    @patch("data.processing_averages.get_metric_weekly_values", return_value=[])
    def test_data_points_count_single_value(self, mock_snapshots):
        single_data = [self.statistics_data[0]]

        result = calculate_weekly_averages(single_data, data_points_count=1)

        self.assertEqual(len(result), 4)
        self.assertEqual(result[0], 5.0)
        self.assertEqual(result[1], 25.0)
        self.assertEqual(result[2], 5.0)
        self.assertEqual(result[3], 25.0)

    def test_data_points_count_empty_data(self):
        result = calculate_weekly_averages([], data_points_count=5)

        self.assertEqual(result, (0, 0, 0, 0))

    @patch("data.processing_averages.get_metric_weekly_values", return_value=[])
    def test_data_points_count_specific_values(self, mock_snapshots):
        result_filtered = calculate_weekly_averages(
            self.statistics_data, data_points_count=2
        )

        self.assertAlmostEqual(result_filtered[0], 10.0, places=1)
        self.assertAlmostEqual(result_filtered[1], 50.0, places=1)
        self.assertAlmostEqual(result_filtered[2], 10.0, places=1)
        self.assertAlmostEqual(result_filtered[3], 50.0, places=1)


class TestGenerateWeeklyForecastDataPointsFiltering(unittest.TestCase):
    def setUp(self):
        self.statistics_data = [
            {
                "date": "2024-12-01",
                "completed_items": 5,
                "completed_points": 25,
                "created_items": 1,
                "created_points": 5,
            },
            {
                "date": "2024-12-08",
                "completed_items": 8,
                "completed_points": 40,
                "created_items": 2,
                "created_points": 10,
            },
            {
                "date": "2024-12-15",
                "completed_items": 12,
                "completed_points": 60,
                "created_items": 3,
                "created_points": 15,
            },
            {
                "date": "2024-12-22",
                "completed_items": 6,
                "completed_points": 30,
                "created_items": 0,
                "created_points": 0,
            },
            {
                "date": "2024-12-29",
                "completed_items": 10,
                "completed_points": 50,
                "created_items": 4,
                "created_points": 20,
            },
            {
                "date": "2025-01-05",
                "completed_items": 15,
                "completed_points": 75,
                "created_items": 2,
                "created_points": 10,
            },
        ]

    def test_forecast_with_data_points_filtering(self):
        forecast_all = generate_weekly_forecast(self.statistics_data, pert_factor=2)

        forecast_filtered = generate_weekly_forecast(
            self.statistics_data, pert_factor=2, data_points_count=3
        )

        self.assertNotEqual(
            forecast_all["items"]["most_likely_value"],
            forecast_filtered["items"]["most_likely_value"],
        )

        self.assertIn("items", forecast_filtered)
        self.assertIn("points", forecast_filtered)
        self.assertIn("most_likely_value", forecast_filtered["items"])
        self.assertIn("optimistic_value", forecast_filtered["items"])
        self.assertIn("pessimistic_value", forecast_filtered["items"])

    def test_forecast_backward_compatibility(self):
        forecast_none = generate_weekly_forecast(
            self.statistics_data, pert_factor=2, data_points_count=None
        )
        forecast_default = generate_weekly_forecast(self.statistics_data, pert_factor=2)

        self.assertEqual(
            forecast_none["items"]["most_likely_value"],
            forecast_default["items"]["most_likely_value"],
        )

    def test_forecast_with_small_dataset(self):
        forecast = generate_weekly_forecast(
            self.statistics_data, pert_factor=2, data_points_count=1
        )

        self.assertIn("items", forecast)
        self.assertIn("points", forecast)
        self.assertIsInstance(forecast["items"]["most_likely_value"], (int, float))
        self.assertGreaterEqual(forecast["items"]["most_likely_value"], 0)

    def test_forecast_with_dataframe_input(self):
        df = pd.DataFrame(self.statistics_data)

        forecast_all = generate_weekly_forecast(df, pert_factor=2)
        forecast_filtered = generate_weekly_forecast(
            df, pert_factor=2, data_points_count=3
        )

        self.assertNotEqual(
            forecast_all["items"]["most_likely_value"],
            forecast_filtered["items"]["most_likely_value"],
        )


class TestCalculatePerformanceTrendDataPointsFiltering(unittest.TestCase):
    def setUp(self):
        self.statistics_data = [
            {"date": "2024-11-01", "completed_items": 2, "completed_points": 10},
            {"date": "2024-11-08", "completed_items": 4, "completed_points": 20},
            {"date": "2024-11-15", "completed_items": 6, "completed_points": 30},
            {"date": "2024-11-22", "completed_items": 8, "completed_points": 40},
            {"date": "2024-11-29", "completed_items": 10, "completed_points": 50},
            {"date": "2024-12-06", "completed_items": 12, "completed_points": 60},
            {"date": "2024-12-13", "completed_items": 14, "completed_points": 70},
            {"date": "2024-12-20", "completed_items": 16, "completed_points": 80},
        ]

    def test_trend_with_data_points_filtering(self):
        trend_all = calculate_performance_trend(
            self.statistics_data, "completed_items", weeks_to_compare=2
        )

        trend_filtered = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            weeks_to_compare=2,
            data_points_count=6,
        )

        self.assertIn(trend_all["trend_direction"], ["up", "stable"])
        self.assertIn(trend_filtered["trend_direction"], ["up", "stable"])

        self.assertIn("percent_change", trend_filtered)
        self.assertIn("current_avg", trend_filtered)
        self.assertIn("previous_avg", trend_filtered)
        self.assertIn("is_significant", trend_filtered)

    def test_trend_backward_compatibility(self):
        trend_none = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            weeks_to_compare=2,
            data_points_count=None,
        )
        trend_default = calculate_performance_trend(
            self.statistics_data, "completed_items", weeks_to_compare=2
        )

        self.assertEqual(trend_none, trend_default)

    def test_trend_insufficient_data(self):
        trend = calculate_performance_trend(
            self.statistics_data,
            "completed_items",
            weeks_to_compare=4,
            data_points_count=3,
        )

        self.assertEqual(trend["trend_direction"], "stable")
        self.assertEqual(trend["percent_change"], 0)

    def test_trend_with_dataframe_input(self):
        df = pd.DataFrame(self.statistics_data)

        trend_all = calculate_performance_trend(
            df, "completed_items", weeks_to_compare=2
        )
        trend_filtered = calculate_performance_trend(
            df, "completed_items", weeks_to_compare=2, data_points_count=6
        )

        self.assertIsInstance(trend_all["percent_change"], (int, float))
        self.assertIsInstance(trend_filtered["percent_change"], (int, float))
