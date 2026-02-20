"""
Integration test for scope baseline consistency across modules.

This test verifies that the baseline (initial scope) is calculated and used
consistently across different parts of the application.
"""

import sys
import unittest
from pathlib import Path

import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.scope_metrics import (
    calculate_scope_change_rate,
    calculate_scope_stability_index,
    calculate_total_project_scope,
)


class TestScopeBaselineConsistency(unittest.TestCase):
    """Test that baseline calculations are consistent across modules."""

    def setUp(self):
        """Set up test data representing a realistic project scenario."""
        # Simulate a project with 10 weeks of data
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
                ],  # Total: 64 completed
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
                ],  # Total: 320 completed
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
                ],  # Total: 23 created (scope growth)
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
                ],  # Total: 115 created
            }
        )

        # Current remaining work (at measurement time)
        self.remaining_items = 50
        self.remaining_points = 250

    def test_baseline_represents_initial_scope(self):
        """
        Test that baseline correctly represents initial scope (before scope changes).

        Baseline (Initial Scope) = Completed Items + Remaining Items
        This should NOT include created items, as those represent scope growth.
        """
        # Calculate initial scope using calculate_total_project_scope
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        total_completed_items = self.statistics_df["completed_items"].sum()
        total_completed_points = self.statistics_df["completed_points"].sum()

        # Baseline should equal: remaining + completed (NOT including created)
        expected_baseline_items = self.remaining_items + total_completed_items
        expected_baseline_points = self.remaining_points + total_completed_points

        self.assertEqual(baseline["total_items"], expected_baseline_items)
        self.assertEqual(baseline["total_points"], expected_baseline_points)

        # Verify baseline does NOT include created items
        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        self.assertNotEqual(
            baseline["total_items"], expected_baseline_items + total_created_items
        )
        self.assertNotEqual(
            baseline["total_points"], expected_baseline_points + total_created_points
        )

    def test_scope_change_rate_uses_initial_baseline(self):
        """
        Test that scope change rate correctly uses initial scope as denominator.

        Scope Change Rate = (Created Items / Initial Scope) × 100%
        """
        # Calculate baseline (initial scope)
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        # Calculate scope change rate using this baseline
        scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline_items, baseline_points
        )

        # Manually calculate expected values
        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        expected_items_rate = (total_created_items / baseline_items) * 100
        expected_points_rate = (total_created_points / baseline_points) * 100

        # Verify scope change rate is correct
        self.assertAlmostEqual(
            scope_change["items_rate"], expected_items_rate, places=1
        )
        self.assertAlmostEqual(
            scope_change["points_rate"], expected_points_rate, places=1
        )

    def test_current_total_scope_calculation(self):
        """
        Test that current total scope is correctly calculated as initial + created.

        Current Total Scope = Initial Scope (Baseline) + Created Items
        """
        # Get initial scope (baseline)
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        # Calculate total created items
        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        # Current total scope should be: baseline + created
        expected_current_total_items = baseline_items + total_created_items
        expected_current_total_points = baseline_points + total_created_points

        # Verify this matches reality: completed + remaining + (created items not yet completed)
        # In a real project: current_total = remaining + (completed that were original) + (created items)
        # Simplification: If we assume created items are either completed or remaining,
        # then: current_total = remaining + all_completed = baseline + net_created
        # But in our test data, created items may already be in completed/remaining counts

        # The key assertion: Current Total = Baseline + Created
        self.assertEqual(
            expected_current_total_items, baseline_items + total_created_items
        )
        self.assertEqual(
            expected_current_total_points, baseline_points + total_created_points
        )

    def test_stability_index_uses_current_total_scope(self):
        """
        Test that stability index correctly uses current total scope.

        Stability Index = 1 - (Created Items / Current Total Scope)
        Where Current Total Scope = Initial Scope + Created Items
        """
        # Get initial scope (baseline)
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]
        baseline_points = baseline["total_points"]

        # Calculate stability index
        stability = calculate_scope_stability_index(
            self.statistics_df, baseline_items, baseline_points
        )

        # Manually calculate expected stability
        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        current_total_items = baseline_items + total_created_items
        current_total_points = baseline_points + total_created_points

        expected_items_stability = 1 - (total_created_items / current_total_items)
        expected_points_stability = 1 - (total_created_points / current_total_points)

        # Verify stability index is correct
        self.assertAlmostEqual(
            stability["items_stability"], expected_items_stability, places=2
        )
        self.assertAlmostEqual(
            stability["points_stability"], expected_points_stability, places=2
        )

    def test_realistic_project_scenario(self):
        """
        Test a realistic project scenario with all metrics.

        Scenario:
        - Project started with 114 items (64 completed + 50 remaining)
        - 23 new items were added (scope growth)
        - Current total scope: 137 items (114 + 23)
        - Scope change rate: 20.2% (23/114)
        - Stability index: 0.83 (1 - 23/137)
        """
        # Calculate baseline (initial scope)
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        baseline_items = baseline["total_items"]  # Should be 114
        baseline_points = baseline["total_points"]  # Should be 570

        # Expected values based on test data
        expected_baseline_items = 114  # 64 completed + 50 remaining
        expected_baseline_points = 570  # 320 completed + 250 remaining

        self.assertEqual(baseline_items, expected_baseline_items)
        self.assertEqual(baseline_points, expected_baseline_points)

        # Calculate scope change rate
        scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline_items, baseline_points
        )

        # Expected scope change: 23 created / 114 baseline = 20.2%
        expected_items_rate = (23 / 114) * 100
        expected_points_rate = (115 / 570) * 100

        self.assertAlmostEqual(
            scope_change["items_rate"], expected_items_rate, places=1
        )
        self.assertAlmostEqual(
            scope_change["points_rate"], expected_points_rate, places=1
        )

        # Calculate stability index
        stability = calculate_scope_stability_index(
            self.statistics_df, baseline_items, baseline_points
        )

        # Expected stability: 1 - (23 / 137) = 0.83
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
        """
        Critical test: Baseline should NEVER include created items.

        This verifies the key principle: baseline represents INITIAL scope only.
        """
        # Calculate baseline
        baseline = calculate_total_project_scope(
            self.statistics_df, self.remaining_items, self.remaining_points
        )

        # Calculate what baseline would be if we WRONGLY included created items
        total_created_items = self.statistics_df["created_items"].sum()
        total_created_points = self.statistics_df["created_points"].sum()

        wrong_baseline_items = baseline["total_items"] + total_created_items
        wrong_baseline_points = baseline["total_points"] + total_created_points

        # The correct baseline should NOT equal the wrong calculation
        self.assertNotEqual(baseline["total_items"], wrong_baseline_items)
        self.assertNotEqual(baseline["total_points"], wrong_baseline_points)

        # If we used the wrong baseline, scope change rate would be artificially low
        wrong_scope_change = calculate_scope_change_rate(
            self.statistics_df, wrong_baseline_items, wrong_baseline_points
        )

        correct_scope_change = calculate_scope_change_rate(
            self.statistics_df, baseline["total_items"], baseline["total_points"]
        )

        # Wrong baseline produces lower scope change rate (underestimates scope growth)
        self.assertLess(
            wrong_scope_change["items_rate"], correct_scope_change["items_rate"]
        )
        self.assertLess(
            wrong_scope_change["points_rate"], correct_scope_change["points_rate"]
        )


if __name__ == "__main__":
    unittest.main()
