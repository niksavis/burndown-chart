import sys
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.scope_metrics import calculate_weekly_scope_growth


class TestBaselineWithScopeCreep(unittest.TestCase):
    def setUp(self):
        self.statistics_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=20, freq="W"),
                "completed_items": [
                    2,
                    3,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                ],
                "completed_points": [
                    10,
                    15,
                    20,
                    25,
                    30,
                    35,
                    40,
                    45,
                    50,
                    55,
                    60,
                    65,
                    70,
                    75,
                    80,
                    85,
                    90,
                    95,
                    100,
                    105,
                ],
                "created_items": [
                    10,
                    8,
                    6,
                    5,
                    4,
                    3,
                    2,
                    1,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
                "created_points": [
                    50,
                    40,
                    30,
                    25,
                    20,
                    15,
                    10,
                    5,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ],
            }
        )

        self.remaining_items = 50
        self.remaining_points = 250

    def test_baseline_calculation_with_filtered_window(self):

        df_filtered = self.statistics_df.tail(12).copy()

        current_items = self.remaining_items
        total_completed = df_filtered["completed_items"].sum()
        total_created = df_filtered["created_items"].sum()

        baseline = current_items + total_completed - total_created

        self.assertEqual(baseline, 236)

        old_baseline = current_items + total_completed
        self.assertEqual(old_baseline, 236)

        df_early = self.statistics_df.head(8).copy()

        hypothetical_remaining = 100
        early_completed = df_early["completed_items"].sum()
        early_created = df_early["created_items"].sum()

        correct_baseline = hypothetical_remaining + early_completed - early_created
        self.assertEqual(correct_baseline, 105)

        wrong_baseline = hypothetical_remaining + early_completed
        self.assertEqual(wrong_baseline, 144)

        self.assertEqual(wrong_baseline - correct_baseline, early_created)

    def test_cumulative_chart_cannot_go_negative(self):

        weekly_data = calculate_weekly_scope_growth(self.statistics_df)

        df_filtered = self.statistics_df.tail(10).copy()
        current_items = self.remaining_items
        total_completed = df_filtered["completed_items"].sum()
        total_created = df_filtered["created_items"].sum()

        baseline = current_items + total_completed - total_created

        weekly_filtered = weekly_data.tail(10).copy()
        weekly_filtered["items_growth"] = (
            weekly_filtered["created_items"] - weekly_filtered["completed_items"]
        )
        weekly_filtered["cum_items_growth"] = weekly_filtered["items_growth"].cumsum()

        weekly_filtered["actual_remaining"] = (
            baseline + weekly_filtered["cum_items_growth"]
        )

        final_remaining = weekly_filtered["actual_remaining"].iloc[-1]

        self.assertAlmostEqual(final_remaining, current_items, delta=1)

        min_remaining = weekly_filtered["actual_remaining"].min()
        self.assertGreaterEqual(
            min_remaining,
            0,
            "Chart shows negative remaining work, which is impossible!",
        )

    def test_old_baseline_causes_wrong_values(self):

        df_early = self.statistics_df.head(8).copy()

        hypothetical_current = 100
        early_completed = df_early["completed_items"].sum()
        early_created = df_early["created_items"].sum()

        wrong_baseline = hypothetical_current + early_completed

        correct_baseline = hypothetical_current + early_completed - early_created

        self.assertEqual(wrong_baseline - correct_baseline, early_created)

        weekly_data = calculate_weekly_scope_growth(df_early)
        weekly_data["items_growth"] = (
            weekly_data["created_items"] - weekly_data["completed_items"]
        )
        weekly_data["cum_items_growth"] = weekly_data["items_growth"].cumsum()

        weekly_data["wrong_chart"] = wrong_baseline + weekly_data["cum_items_growth"]

        final_wrong = weekly_data["wrong_chart"].iloc[-1]

        self.assertAlmostEqual(final_wrong, 139, delta=1)

        self.assertNotAlmostEqual(final_wrong, hypothetical_current, delta=1)


if __name__ == "__main__":
    unittest.main()
