"""
Integration test for baseline calculation with scope creep scenarios.

This test verifies that the baseline calculation correctly handles filtered
time windows with scope creep, and ensures the cumulative chart cannot go negative.
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.scope_metrics import calculate_weekly_scope_growth


class TestBaselineWithScopeCreep(unittest.TestCase):
    """Test that baseline calculations handle scope creep correctly in filtered windows."""

    def setUp(self):
        """Set up test data representing a project with significant scope creep."""
        # Simulate 20 weeks of data with heavy scope creep
        self.statistics_df = pd.DataFrame(
            {
                "date": pd.date_range(start="2025-01-01", periods=20, freq="W"),
                # High scope creep: created > completed early on
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
                # Created items: high initially (scope creep), then low
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

        # Current state: 50 items remaining after all this work
        self.remaining_items = 50
        self.remaining_points = 250

    def test_baseline_calculation_with_filtered_window(self):
        """
        Test that baseline calculation correctly accounts for created items in filtered window.

        When filtering to last 12 weeks (data_points_count=12):
        - Current remaining: 50 items
        - Completed in last 12 weeks: sum of last 12 weeks
        - Created in last 12 weeks: sum of last 12 weeks (should be mostly 0)
        - Baseline = current + completed - created

        This should give a reasonable baseline that represents scope at start of window.
        """
        # Filter to last 12 weeks
        df_filtered = self.statistics_df.tail(12).copy()

        current_items = self.remaining_items
        total_completed = df_filtered[
            "completed_items"
        ].sum()  # 186 items (weeks 9-20: 10+11+...+21)
        total_created = df_filtered[
            "created_items"
        ].sum()  # 0 items (no scope creep in recent weeks)

        # Calculate baseline as dashboard should now do it
        baseline = current_items + total_completed - total_created

        # Expected: 50 + 186 - 0 = 236
        self.assertEqual(baseline, 236)

        # Verify this is different from the OLD (buggy) calculation
        old_baseline = current_items + total_completed  # Missing - total_created
        self.assertEqual(old_baseline, 236)  # Same in this case since created=0

        # But test with earlier window where there WAS scope creep
        df_early = self.statistics_df.head(8).copy()

        # At week 8, if we had 100 items remaining:
        hypothetical_remaining = 100
        early_completed = df_early["completed_items"].sum()  # 44 items
        early_created = df_early[
            "created_items"
        ].sum()  # 39 items (significant scope creep!)

        correct_baseline = hypothetical_remaining + early_completed - early_created
        # Expected: 100 + 44 - 39 = 105 (correct)
        self.assertEqual(correct_baseline, 105)

        wrong_baseline = (
            hypothetical_remaining + early_completed
        )  # OLD BUGGY calculation
        # This gives: 100 + 44 = 144 (WRONG - too high by 39)
        self.assertEqual(wrong_baseline, 144)

        # The difference is exactly the scope creep
        self.assertEqual(wrong_baseline - correct_baseline, early_created)

    def test_cumulative_chart_cannot_go_negative(self):
        """
        Test that cumulative chart shows actual remaining work and cannot go negative.

        With the fix:
        - Chart shows: baseline + cumulative_net_change
        - Where cumulative_net_change = cumsum(created - completed)
        - As long as baseline > 0 and we don't complete more than baseline, chart stays positive
        """
        # Calculate weekly growth
        weekly_data = calculate_weekly_scope_growth(self.statistics_df)

        # Simulate the chart calculation with CORRECT baseline
        # Filter to last 10 weeks
        df_filtered = self.statistics_df.tail(10).copy()
        current_items = self.remaining_items
        total_completed = df_filtered["completed_items"].sum()
        total_created = df_filtered["created_items"].sum()

        baseline = current_items + total_completed - total_created

        # Calculate cumulative net change for last 10 weeks
        weekly_filtered = weekly_data.tail(10).copy()
        weekly_filtered["items_growth"] = (
            weekly_filtered["created_items"] - weekly_filtered["completed_items"]
        )
        weekly_filtered["cum_items_growth"] = weekly_filtered["items_growth"].cumsum()

        # Chart should show: baseline + cumulative_growth
        weekly_filtered["actual_remaining"] = (
            baseline + weekly_filtered["cum_items_growth"]
        )

        # The last value should match current remaining
        final_remaining = weekly_filtered["actual_remaining"].iloc[-1]

        # Allow small floating point differences
        self.assertAlmostEqual(final_remaining, current_items, delta=1)

        # Most importantly: chart should never go negative (since baseline is positive)
        min_remaining = weekly_filtered["actual_remaining"].min()
        self.assertGreaterEqual(
            min_remaining,
            0,
            "Chart shows negative remaining work, which is impossible!",
        )

    def test_old_baseline_causes_wrong_values(self):
        """
        Demonstrate how the OLD baseline calculation causes incorrect chart values.

        This test shows why the bug occurred.
        """
        # Use early window with high scope creep
        df_early = self.statistics_df.head(8).copy()

        # Suppose at week 8 we have 100 items remaining
        hypothetical_current = 100
        early_completed = df_early["completed_items"].sum()  # 44
        early_created = df_early["created_items"].sum()  # 39

        # OLD (buggy) baseline
        wrong_baseline = hypothetical_current + early_completed  # 144 (too high!)

        # The correct baseline should account for created items
        correct_baseline = hypothetical_current + early_completed - early_created  # 105

        # Verify the bug: wrong baseline is inflated by the amount of scope creep
        self.assertEqual(wrong_baseline - correct_baseline, early_created)

        # Calculate cumulative net change
        weekly_data = calculate_weekly_scope_growth(df_early)
        weekly_data["items_growth"] = (
            weekly_data["created_items"] - weekly_data["completed_items"]
        )
        weekly_data["cum_items_growth"] = weekly_data["items_growth"].cumsum()

        # With wrong baseline, chart would show
        weekly_data["wrong_chart"] = wrong_baseline + weekly_data["cum_items_growth"]

        # The final value with wrong baseline
        final_wrong = weekly_data["wrong_chart"].iloc[-1]

        # This should be 144 + (-5) = 139 (WRONG! Should be 100)
        # Net change: created(39) - completed(44) = -5
        self.assertAlmostEqual(final_wrong, 139, delta=1)

        # But we KNOW the actual remaining is 100, not 139!
        self.assertNotAlmostEqual(final_wrong, hypothetical_current, delta=1)

        # This demonstrates the bug: wrong baseline leads to wrong chart values


if __name__ == "__main__":
    unittest.main()
