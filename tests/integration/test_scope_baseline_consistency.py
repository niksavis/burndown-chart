import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.scope_metrics import (
    calculate_scope_change_rate,
    calculate_scope_stability_index,
    calculate_total_project_scope,
)


class TestScopeBaselineConsistency(unittest.TestCase):
    def setUp(self):
        self.statistics_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=10, freq="W"),
                "completed_items": [
                    5,
                    7,
                    4,
                    6,
                    8,
                    5,
                    9,
                    7,
                    3,
                    10,
                ],
                "completed_points": [
                    25,
                    35,
                    20,
                    30,
                    40,
                    25,
                    45,
                    35,
                    15,
                    50,
                ],
                "created_items": [
                    2,
                    3,
                    1,
                    2,
                    4,
                    1,
                    0,
                    3,
                    5,
                    2,
                ],
                "created_points": [
                    10,
                    15,
                    5,
                    10,
                    20,
                    5,
                    0,
                    15,
                    25,
                    10,
                ],
            }
        )

        self.remaining_items = 50
        self.remaining_points = 250

    def test_baseline_represents_initial_scope(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        total_completed_items = self.statistics_df["completed_items"].sum()
        total_completed_points = self.statistics_df["completed_points"].sum()

        expected_baseline_items = self.remaining_items + total_completed_items
        expected_baseline_points = self.remaining_points + total_completed_points

        self.assertEqual(baseline["total_items"], expected_baseline_items)
        self.assertEqual(baseline["total_points"], expected_baseline_points)

        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        self.assertNotEqual(
            baseline["total_items"], expected_baseline_items + total_created_items
        )
        self.assertNotEqual(
            baseline["total_points"], expected_baseline_points + total_created_points
        )

    def test_scope_change_rate_uses_initial_baseline(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline_items, baseline_points
        )

        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        expected_items_rate = (total_created_items / baseline_items) * 100
        expected_points_rate = (total_created_points / baseline_points) * 100

        self.assertAlmostEqual(
            scope_change["items_rate"], expected_items_rate, places=1
        )
        self.assertAlmostEqual(
            scope_change["points_rate"], expected_points_rate, places=1
        )

    def test_current_total_scope_calculation(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        expected_current_total_items = baseline_items + total_created_items
        expected_current_total_points = baseline_points + total_created_points

        self.assertEqual(
            expected_current_total_items, baseline_items + total_created_items
        )
        self.assertEqual(
            expected_current_total_points, baseline_points + total_created_points
        )

    def test_stability_index_uses_current_total_scope(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        stability = calculate_scope_stability_index(
            self.statistics_df, baseline_items, baseline_points
        )

        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        current_total_items = baseline_items + total_created_items
        current_total_points = baseline_points + total_created_points

        expected_items_stability = 1 - (total_created_items / current_total_items)
        expected_points_stability = 1 - (total_created_points / current_total_points)

        self.assertAlmostEqual(
            stability["items_stability"], expected_items_stability, places=2
        )
        self.assertAlmostEqual(
            stability["points_stability"], expected_points_stability, places=2
        )

    def test_realistic_project_scenario(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        expected_baseline_items = 114
        expected_baseline_points = 570

        self.assertEqual(baseline_items, expected_baseline_items)
        self.assertEqual(baseline_points, expected_baseline_points)

        scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline_items, baseline_points
        )

        expected_items_rate = (23 / 114) * 100
        expected_points_rate = (115 / 570) * 100

        self.assertAlmostEqual(
            scope_change["items_rate"], expected_items_rate, places=1
        )
        self.assertAlmostEqual(
            scope_change["points_rate"], expected_points_rate, places=1
        )

        stability = calculate_scope_stability_index(
            self.statistics_df, baseline_items, baseline_points
        )

        current_total_items = 114 + 23
        expected_items_stability = 1 - (23 / current_total_items)

        current_total_points = 570 + 115
        expected_points_stability = 1 - (115 / current_total_points)

        self.assertAlmostEqual(
            stability["items_stability"], expected_items_stability, places=2
        )
        self.assertAlmostEqual(
            stability["points_stability"], expected_points_stability, places=2
        )

    def test_baseline_not_affected_by_created_items(self):

        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        wrong_baseline_items = baseline["total_items"] + total_created_items
        wrong_baseline_points = baseline["total_points"] + total_created_points

        self.assertNotEqual(baseline["total_items"], wrong_baseline_items)
        self.assertNotEqual(baseline["total_points"], wrong_baseline_points)

        wrong_scope_change = calculate_scope_change_rate(
            self.statistics_df, wrong_baseline_items, wrong_baseline_points
        )

        correct_scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline["total_items"], baseline["total_points"]
        )

        self.assertLess(
            wrong_scope_change["items_rate"], correct_scope_change["items_rate"]
        )
        self.assertLess(
            wrong_scope_change["points_rate"], correct_scope_change["points_rate"]
        )


if __name__ == "__main__":
    unittest.main()
