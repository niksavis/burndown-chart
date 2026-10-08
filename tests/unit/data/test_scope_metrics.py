import sys
import unittest
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data.scope_metrics import (
    calculate_scope_change_rate,
    calculate_scope_creep_rate,
    calculate_scope_stability_index,
    calculate_total_project_scope,
    calculate_weekly_scope_growth,
    check_scope_change_threshold,
    check_scope_creep_threshold,
    get_week_start_date,
)


class TestCalculateScopeChangeRate(unittest.TestCase):
    def setUp(self):
        self.scope_change_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=10, freq="W"),
                "completed_items": [5, 7, 4, 6, 8, 5, 9, 7, 3, 10],
                "completed_points": [25, 35, 20, 30, 40, 25, 45, 35, 15, 50],
                "created_items": [2, 3, 1, 2, 4, 1, 0, 3, 5, 2],
                "created_points": [10, 15, 5, 10, 20, 5, 0, 15, 25, 10],
            }
        )

        self.baseline_items = 50
        self.baseline_points = 250

    def test_basic_calculation(self):
        result = calculate_scope_change_rate(
            self.scope_change_data, self.baseline_items, self.baseline_points
        )

        self.assertIn("items_rate", result)
        self.assertIn("points_rate", result)
        self.assertIn("throughput_ratio", result)

        total_created_items = self.scope_change_data["created_items"].sum()
        total_created_points = self.scope_change_data["created_points"].sum()
        total_completed_items = self.scope_change_data["completed_items"].sum()
        total_completed_points = self.scope_change_data["completed_points"].sum()

        expected_items_rate = round(
            (total_created_items / self.baseline_items) * 100, 1
        )
        expected_points_rate = round(
            (total_created_points / self.baseline_points) * 100, 1
        )

        expected_items_throughput_ratio = round(
            total_created_items / total_completed_items, 2
        )
        expected_points_throughput_ratio = round(
            total_created_points / total_completed_points, 2
        )

        self.assertEqual(result["items_rate"], expected_items_rate)
        self.assertEqual(result["points_rate"], expected_points_rate)
        self.assertEqual(
            result["throughput_ratio"]["items"], expected_items_throughput_ratio
        )
        self.assertEqual(
            result["throughput_ratio"]["points"], expected_points_throughput_ratio
        )

    def test_zero_baseline_values(self):
        result = calculate_scope_change_rate(self.scope_change_data, 0, 0)

        self.assertEqual(result["items_rate"], 0)
        self.assertEqual(result["points_rate"], 0)

        total_created_items = self.scope_change_data["created_items"].sum()
        total_created_points = self.scope_change_data["created_points"].sum()
        total_completed_items = self.scope_change_data["completed_items"].sum()
        total_completed_points = self.scope_change_data["completed_points"].sum()

        expected_items_throughput_ratio = round(
            total_created_items / total_completed_items, 2
        )
        expected_points_throughput_ratio = round(
            total_created_points / total_completed_points, 2
        )

        self.assertEqual(
            result["throughput_ratio"]["items"], expected_items_throughput_ratio
        )
        self.assertEqual(
            result["throughput_ratio"]["points"], expected_points_throughput_ratio
        )

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )
        result = calculate_scope_change_rate(
            empty_df, self.baseline_items, self.baseline_points
        )

        self.assertEqual(result["items_rate"], 0)
        self.assertEqual(result["points_rate"], 0)
        self.assertEqual(result["throughput_ratio"]["items"], 0)
        self.assertEqual(result["throughput_ratio"]["points"], 0)

    def test_no_scope_change(self):
        no_change_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="W"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [0, 0, 0, 0, 0],
                "created_points": [0, 0, 0, 0, 0],
            }
        )

        result = calculate_scope_change_rate(
            no_change_data, self.baseline_items, self.baseline_points
        )

        self.assertEqual(result["items_rate"], 0.0)
        self.assertEqual(result["points_rate"], 0.0)
        self.assertEqual(result["throughput_ratio"]["items"], 0)
        self.assertEqual(result["throughput_ratio"]["points"], 0)

    def test_negative_scope_change(self):
        negative_change_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="W"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [-1, 0, 2, -3, 5],
                "created_points": [-5, 0, 10, -15, 25],
            }
        )

        result = calculate_scope_change_rate(
            negative_change_data, self.baseline_items, self.baseline_points
        )

        total_created_items = negative_change_data["created_items"].sum()
        total_created_points = negative_change_data["created_points"].sum()
        total_completed_items = negative_change_data["completed_items"].sum()
        total_completed_points = negative_change_data["completed_points"].sum()

        actual_baseline_items = self.baseline_items
        actual_baseline_points = self.baseline_points
        expected_items_rate = round(
            (total_created_items / actual_baseline_items) * 100, 1
        )
        expected_points_rate = round(
            (total_created_points / actual_baseline_points) * 100, 1
        )

        expected_items_throughput_ratio = (
            round(total_created_items / total_completed_items, 2)
            if total_completed_items > 0
            else 0
        )
        expected_points_throughput_ratio = (
            round(total_created_points / total_completed_points, 2)
            if total_completed_points > 0
            else 0
        )

        self.assertEqual(result["items_rate"], expected_items_rate)
        self.assertEqual(result["points_rate"], expected_points_rate)
        self.assertEqual(
            result["throughput_ratio"]["items"], expected_items_throughput_ratio
        )
        self.assertEqual(
            result["throughput_ratio"]["points"], expected_points_throughput_ratio
        )

    def test_zero_completed(self):
        zero_completed_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=3, freq="W"),
                "completed_items": [0, 0, 0],
                "completed_points": [0, 0, 0],
                "created_items": [2, 3, 1],
                "created_points": [10, 15, 5],
            }
        )

        result = calculate_scope_change_rate(
            zero_completed_data, self.baseline_items, self.baseline_points
        )

        total_created_items = zero_completed_data["created_items"].sum()
        total_created_points = zero_completed_data["created_points"].sum()

        expected_items_rate = round(
            (total_created_items / self.baseline_items) * 100, 1
        )
        expected_points_rate = round(
            (total_created_points / self.baseline_points) * 100, 1
        )

        self.assertEqual(result["items_rate"], expected_items_rate)
        self.assertEqual(result["points_rate"], expected_points_rate)
        self.assertEqual(result["throughput_ratio"]["items"], float("inf"))
        self.assertEqual(result["throughput_ratio"]["points"], float("inf"))

    def test_backward_compatibility(self):
        result1 = calculate_scope_change_rate(
            self.scope_change_data, self.baseline_items, self.baseline_points
        )
        result2 = calculate_scope_creep_rate(
            self.scope_change_data, self.baseline_items, self.baseline_points
        )

        self.assertEqual(result1["items_rate"], result2["items_rate"])
        self.assertEqual(result1["points_rate"], result2["points_rate"])
        self.assertEqual(result1["throughput_ratio"], result2["throughput_ratio"])


class TestCalculateTotalProjectScope(unittest.TestCase):
    def setUp(self):
        self.project_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="W"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [2, 3, 1, 2, 4],
                "created_points": [10, 15, 5, 10, 20],
            }
        )

        self.remaining_items = 30
        self.remaining_points = 150

    def test_basic_calculation(self):
        result = calculate_total_project_scope(
            self.project_data, self.remaining_items, self.remaining_points
        )

        self.assertIn("total_items", result)
        self.assertIn("total_points", result)

        total_completed_items = self.project_data["completed_items"].sum()
        total_completed_points = self.project_data["completed_points"].sum()
        expected_total_items = self.remaining_items + total_completed_items
        expected_total_points = self.remaining_points + total_completed_points

        self.assertEqual(result["total_items"], int(expected_total_items))
        self.assertEqual(result["total_points"], int(expected_total_points))

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(columns=["date", "completed_items", "completed_points"])
        result = calculate_total_project_scope(
            empty_df, self.remaining_items, self.remaining_points
        )

        self.assertEqual(result["total_items"], int(self.remaining_items))
        self.assertEqual(result["total_points"], int(self.remaining_points))

    def test_zero_remaining_work(self):
        result = calculate_total_project_scope(self.project_data, 0, 0)

        total_completed_items = self.project_data["completed_items"].sum()
        total_completed_points = self.project_data["completed_points"].sum()

        self.assertEqual(result["total_items"], int(total_completed_items))
        self.assertEqual(result["total_points"], int(total_completed_points))

    def test_type_conversion(self):
        float_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=2, freq="W"),
                "completed_items": [5.5, 7.2],
                "completed_points": [25.3, 35.7],
            }
        )

        result = calculate_total_project_scope(float_data, 10.3, 50.6)  # type: ignore[arg-type]

        self.assertIsInstance(result["total_items"], int)
        self.assertIsInstance(result["total_points"], int)

        total_completed_items = float_data["completed_items"].sum()
        total_completed_points = float_data["completed_points"].sum()
        expected_total_items = int(10.3 + total_completed_items)
        expected_total_points = int(50.6 + total_completed_points)

        self.assertEqual(result["total_items"], expected_total_items)
        self.assertEqual(result["total_points"], expected_total_points)


class TestCalculateWeeklyScopeGrowth(unittest.TestCase):
    def setUp(self):
        self.scope_data = pd.DataFrame(
            {
                "date": [
                    "2025-01-06",
                    "2025-01-08",
                    "2025-01-10",
                    "2025-01-13",
                    "2025-01-15",
                    "2025-01-17",
                    "2025-01-20",
                    "2025-01-22",
                    "2025-01-24",
                ],
                "completed_items": [3, 2, 5, 4, 3, 2, 6, 4, 3],
                "completed_points": [15, 10, 25, 20, 15, 10, 30, 20, 15],
                "created_items": [1, 0, 2, 0, 2, 1, 0, 1, 3],
                "created_points": [5, 0, 10, 0, 10, 5, 0, 5, 15],
            }
        )

        self.scope_data["date"] = pd.to_datetime(self.scope_data["date"])

    def test_weekly_grouping(self):
        result = calculate_weekly_scope_growth(self.scope_data)

        self.assertEqual(len(result), 3)

        expected_columns = ["week_label", "items_growth", "points_growth", "start_date"]
        for column in expected_columns:
            self.assertIn(column, result.columns)

    def test_growth_calculation(self):
        result = calculate_weekly_scope_growth(self.scope_data)

        week_column = "week" if "week" in result.columns else "week_label"
        week2_row = result[result[week_column] == "2025-W02"]
        self.assertFalse(week2_row.empty)

        actual_items_growth = week2_row.iloc[0]["items_growth"]
        actual_points_growth = week2_row.iloc[0]["points_growth"]

        self.assertEqual(actual_items_growth, -7)
        self.assertEqual(actual_points_growth, -35)

    def test_iso_week_format(self):
        result = calculate_weekly_scope_growth(self.scope_data)

        for week_label in result["week_label"]:
            self.assertRegex(week_label, r"^\d{4}-W\d{2}$")

    def test_start_date_generation(self):
        result = calculate_weekly_scope_growth(self.scope_data)

        for date in result["start_date"]:
            self.assertEqual(date.weekday(), 0)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )
        result = calculate_weekly_scope_growth(empty_df)

        self.assertTrue(result.empty)

        self.assertIn("items_growth", result.columns)
        self.assertIn("points_growth", result.columns)

        self.assertTrue("week" in result.columns or "week_label" in result.columns)


class TestCalculateScopeStabilityIndex(unittest.TestCase):
    def setUp(self):
        self.high_stability_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="D"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [1, 0, 0, 1, 0],
                "created_points": [5, 0, 0, 5, 0],
            }
        )

        self.medium_stability_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="D"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [2, 3, 1, 2, 4],
                "created_points": [10, 15, 5, 10, 20],
            }
        )

        self.low_stability_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=5, freq="D"),
                "completed_items": [5, 7, 4, 6, 8],
                "completed_points": [25, 35, 20, 30, 40],
                "created_items": [8, 10, 6, 9, 12],
                "created_points": [40, 50, 30, 45, 60],
            }
        )

        self.baseline_items = 50
        self.baseline_points = 250

    def test_high_stability(self):
        result = calculate_scope_stability_index(
            self.high_stability_data, self.baseline_items, self.baseline_points
        )

        self.assertIn("items_stability", result)
        self.assertIn("points_stability", result)

        self.assertGreater(result["items_stability"], 0.8)
        self.assertGreater(result["points_stability"], 0.8)

    def test_medium_stability(self):
        result = calculate_scope_stability_index(
            self.medium_stability_data, self.baseline_items, self.baseline_points
        )

        self.assertGreaterEqual(result["items_stability"], 0.8)
        self.assertLess(result["items_stability"], 0.9)

    def test_low_stability(self):
        result = calculate_scope_stability_index(
            self.low_stability_data, self.baseline_items, self.baseline_points
        )

        self.assertGreaterEqual(result["items_stability"], 0.5)
        self.assertLess(result["items_stability"], 0.6)

    def test_bounding_in_range(self):
        extreme_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=3, freq="D"),
                "completed_items": [5, 7, 4],
                "completed_points": [25, 35, 20],
                "created_items": [50, 70, 40],
                "created_points": [250, 350, 200],
            }
        )

        result = calculate_scope_stability_index(extreme_data, 10, 50)

        self.assertGreaterEqual(result["items_stability"], 0.0)
        self.assertLessEqual(result["items_stability"], 1.0)
        self.assertGreaterEqual(result["points_stability"], 0.0)
        self.assertLessEqual(result["points_stability"], 1.0)

    def test_empty_dataframe(self):
        empty_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )
        result = calculate_scope_stability_index(
            empty_df, self.baseline_items, self.baseline_points
        )

        self.assertEqual(result["items_stability"], 1.0)
        self.assertEqual(result["points_stability"], 1.0)

    def test_zero_baseline(self):
        result = calculate_scope_stability_index(self.medium_stability_data, 0, 0)

        self.assertEqual(result["items_stability"], 1.0)
        self.assertEqual(result["points_stability"], 1.0)

    def test_precision(self):
        data = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=1, freq="D"),
                "completed_items": [3],
                "completed_points": [15],
                "created_items": [1],
                "created_points": [5],
            }
        )

        result = calculate_scope_stability_index(data, 10, 50)

        self.assertEqual(len(str(result["items_stability"]).split(".")[-1]), 2)
        self.assertEqual(len(str(result["points_stability"]).split(".")[-1]), 2)


class TestCheckScopeChangeThreshold(unittest.TestCase):
    def test_below_threshold(self):
        scope_change_rate = {
            "items_rate": 5.0,
            "points_rate": 8.0,
            "throughput_ratio": {"items": 0.5, "points": 0.7},
        }
        threshold = 10.0

        result = check_scope_change_threshold(scope_change_rate, threshold)

        self.assertEqual(result["status"], "info")
        self.assertEqual(result["message"], "")

    def test_above_threshold_below_throughput(self):
        scope_change_rate = {
            "items_rate": 15.0,
            "points_rate": 8.0,
            "throughput_ratio": {"items": 0.5, "points": 0.7},
        }
        threshold = 10.0

        result = check_scope_change_threshold(scope_change_rate, threshold)

        self.assertEqual(result["status"], "info")

    def test_above_threshold_above_throughput(self):
        scope_change_rate = {
            "items_rate": 15.0,
            "points_rate": 8.0,
            "throughput_ratio": {"items": 1.2, "points": 0.7},
        }
        threshold = 10.0

        result = check_scope_change_threshold(scope_change_rate, threshold)

        self.assertEqual(result["status"], "warning")
        self.assertIn("Items scope growth (15.0%)", result["message"])
        self.assertIn(
            "Scope is growing 1.2x faster than items completion", result["message"]
        )

    def test_points_exceeds_threshold_and_throughput(self):
        scope_change_rate = {
            "items_rate": 5.0,
            "points_rate": 15.0,
            "throughput_ratio": {"items": 0.5, "points": 1.5},
        }
        threshold = 10.0

        result = check_scope_change_threshold(scope_change_rate, threshold)

        self.assertEqual(result["status"], "warning")
        self.assertIn("Points scope growth (15.0%)", result["message"])
        self.assertIn(
            "Scope is growing 1.5x faster than points completion", result["message"]
        )

    def test_both_exceed_threshold_and_throughput(self):
        scope_change_rate = {
            "items_rate": 15.0,
            "points_rate": 20.0,
            "throughput_ratio": {"items": 1.2, "points": 1.8},
        }
        threshold = 10.0

        result = check_scope_change_threshold(scope_change_rate, threshold)

        self.assertEqual(result["status"], "warning")
        self.assertIn("Items scope growth (15.0%)", result["message"])
        self.assertIn("Points scope growth (20.0%)", result["message"])
        self.assertIn(
            "Scope is growing 1.2x faster than items completion "
            "and 1.8x faster than points completion",
            result["message"],
        )

    def test_backward_compatibility(self):
        scope_change_rate = {
            "items_rate": 15.0,
            "points_rate": 20.0,
            "throughput_ratio": {"items": 1.2, "points": 1.8},
        }
        threshold = 10.0

        result1 = check_scope_change_threshold(scope_change_rate, threshold)
        result2 = check_scope_creep_threshold(scope_change_rate, threshold)

        self.assertEqual(result1["status"], result2["status"])
        self.assertEqual(result1["message"], result2["message"])


class TestGetWeekStartDate(unittest.TestCase):
    def test_week_start_date(self):
        self.assertEqual(get_week_start_date(2025, 1), datetime(2024, 12, 30, 0, 0))
        self.assertEqual(get_week_start_date(2025, 2), datetime(2025, 1, 6, 0, 0))
        self.assertEqual(get_week_start_date(2025, 3), datetime(2025, 1, 13, 0, 0))

        self.assertEqual(get_week_start_date(2020, 53), datetime(2020, 12, 28, 0, 0))

    def test_first_monday(self):
        for year in range(2020, 2026):
            for week in range(1, 53):
                date = get_week_start_date(year, week)
                self.assertEqual(date.weekday(), 0)


class TestScopeMetricsDataPointsFiltering(unittest.TestCase):
    def setUp(self):
        self.scope_data = pd.DataFrame(
            {
                "date": [
                    "2024-12-01",
                    "2024-12-08",
                    "2024-12-15",
                    "2024-12-22",
                    "2024-12-29",
                    "2025-01-05",
                    "2025-01-12",
                    "2025-01-19",
                ],
                "completed_items": [10, 15, 8, 12, 20, 9, 14, 11],
                "completed_points": [50, 75, 40, 60, 100, 45, 70, 55],
                "created_items": [5, 3, 7, 2, 8, 4, 1, 6],
                "created_points": [25, 15, 35, 10, 40, 20, 5, 30],
            }
        )

        self.scope_data["date"] = pd.to_datetime(self.scope_data["date"])

        self.baseline_items = 100
        self.baseline_points = 500

    def test_scope_creep_rate_with_data_points_filtering(self):
        scope_all = calculate_scope_creep_rate(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        scope_filtered = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=4,
        )

        self.assertNotEqual(scope_all["items_rate"], scope_filtered["items_rate"])
        self.assertNotEqual(scope_all["points_rate"], scope_filtered["points_rate"])

        self.assertIn("items_rate", scope_filtered)
        self.assertIn("points_rate", scope_filtered)
        self.assertIn("throughput_ratio", scope_filtered)

        self.assertIsInstance(scope_filtered["items_rate"], (int, float))
        self.assertIsInstance(scope_filtered["points_rate"], (int, float))

    def test_scope_creep_rate_backward_compatibility(self):
        scope_none = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=None,
        )
        scope_default = calculate_scope_creep_rate(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        self.assertEqual(scope_none, scope_default)

    def test_scope_creep_rate_larger_than_available(self):
        scope_large = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=20,
        )
        scope_all = calculate_scope_creep_rate(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        self.assertEqual(scope_large, scope_all)

    def test_scope_creep_rate_edge_cases(self):
        scope_all = calculate_scope_creep_rate(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        scope_zero = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=0,
        )
        self.assertEqual(scope_zero, scope_all)

        scope_negative = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=-3,
        )
        self.assertEqual(scope_negative, scope_all)

    def test_weekly_scope_growth_with_data_points_filtering(self):
        growth_all = calculate_weekly_scope_growth(self.scope_data)

        growth_filtered = calculate_weekly_scope_growth(
            self.scope_data, data_points_count=4
        )

        self.assertNotEqual(len(growth_all), len(growth_filtered))
        self.assertEqual(len(growth_filtered), 4)

        expected_columns = ["week_label", "items_growth", "points_growth", "start_date"]
        for col in expected_columns:
            self.assertIn(col, growth_filtered.columns)

        self.assertTrue(growth_filtered["items_growth"].dtype.kind in "bifc")
        self.assertTrue(growth_filtered["points_growth"].dtype.kind in "bifc")

    def test_weekly_scope_growth_backward_compatibility(self):
        growth_none = calculate_weekly_scope_growth(
            self.scope_data, data_points_count=None
        )
        growth_default = calculate_weekly_scope_growth(self.scope_data)

        pd.testing.assert_frame_equal(growth_none, growth_default)

    def test_weekly_scope_growth_small_dataset(self):
        growth = calculate_weekly_scope_growth(self.scope_data, data_points_count=1)

        self.assertEqual(len(growth), 1)

        expected_columns = ["week_label", "items_growth", "points_growth", "start_date"]
        for col in expected_columns:
            self.assertIn(col, growth.columns)

    def test_scope_stability_index_with_data_points_filtering(self):
        stability_all = calculate_scope_stability_index(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        stability_filtered = calculate_scope_stability_index(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=4,
        )

        self.assertNotEqual(
            stability_all["items_stability"], stability_filtered["items_stability"]
        )
        self.assertNotEqual(
            stability_all["points_stability"], stability_filtered["points_stability"]
        )

        self.assertIn("items_stability", stability_filtered)
        self.assertIn("points_stability", stability_filtered)

        self.assertGreaterEqual(stability_filtered["items_stability"], 0)
        self.assertLessEqual(stability_filtered["items_stability"], 1)
        self.assertGreaterEqual(stability_filtered["points_stability"], 0)
        self.assertLessEqual(stability_filtered["points_stability"], 1)

    def test_scope_stability_index_backward_compatibility(self):
        stability_none = calculate_scope_stability_index(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=None,
        )
        stability_default = calculate_scope_stability_index(
            self.scope_data, self.baseline_items, self.baseline_points
        )

        self.assertEqual(stability_none, stability_default)

    def test_scope_stability_index_empty_filtered_data(self):
        empty_df = pd.DataFrame(
            columns=[
                "date",
                "completed_items",
                "completed_points",
                "created_items",
                "created_points",
            ]
        )

        stability = calculate_scope_stability_index(
            empty_df, self.baseline_items, self.baseline_points, data_points_count=5
        )

        self.assertEqual(stability["items_stability"], 1.0)
        self.assertEqual(stability["points_stability"], 1.0)

    def test_all_scope_functions_with_specific_filtering(self):
        data_points_count = 3

        scope_rate = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=data_points_count,
        )

        growth_data = calculate_weekly_scope_growth(
            self.scope_data, data_points_count=data_points_count
        )

        stability = calculate_scope_stability_index(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=data_points_count,
        )

        self.assertIsInstance(scope_rate["items_rate"], (int, float))
        self.assertEqual(len(growth_data), data_points_count)
        self.assertIsInstance(stability["items_stability"], (int, float))

        self.assertGreaterEqual(len(growth_data), 1)
        self.assertLessEqual(len(growth_data), data_points_count)

    def test_scope_functions_with_zero_baseline(self):
        scope_rate = calculate_scope_creep_rate(
            self.scope_data, baseline_items=0, baseline_points=0, data_points_count=4
        )

        self.assertEqual(scope_rate["items_rate"], 0)
        self.assertEqual(scope_rate["points_rate"], 0)
        self.assertIn("throughput_ratio", scope_rate)

    def test_backward_compatibility_alias_functions(self):
        creep_rate = calculate_scope_creep_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=4,
        )

        change_rate = calculate_scope_change_rate(
            self.scope_data,
            self.baseline_items,
            self.baseline_points,
            data_points_count=4,
        )

        self.assertEqual(creep_rate, change_rate)


if __name__ == "__main__":
    unittest.main()
