"""
Test for the empty input fields edge case with Remaining Total Points calculation.

This test covers the bug where:
- Remaining Estimated Items: empty
- Remaining Total Items: empty
- Remaining Estimated Points: empty
- But "Remaining Total Points" shows calculated values instead of 0
- It behaves correctly when these fields are set manually to 0

The fix ensures that when user explicitly sets inputs to empty/0 and no fallback
is requested, the calculation respects that intent and returns 0.
"""

import unittest
from unittest.mock import patch

from data.processing import calculate_total_points


class TestEmptyInputFieldsRemainingTotalPoints(unittest.TestCase):
    """Test edge cases with empty input fields for Remaining Total Points calculation."""

    def test_fix_empty_estimated_items_and_points(self):
        """Test that explicitly setting both estimated_items and estimated_points to 0 returns 0."""

        # Mock historical statistics data
        historical_data = [
            {"date": "2025-01-01", "completed_items": 5, "completed_points": 50},
            {"date": "2025-01-02", "completed_items": 3, "completed_points": 30},
        ]

        total_items = 100
        estimated_items = 0
        estimated_points = 0

        # Test with the new behavior (use_fallback=False) - this is the fix
        total_points_no_fallback, avg_no_fallback = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            historical_data,
            use_fallback=False,
        )

        # Should return 0, 0 when both estimated_items and estimated_points are 0
        self.assertEqual(
            total_points_no_fallback,
            0.0,
            "Should return 0 when both estimates are 0 and no fallback",
        )
        self.assertEqual(
            avg_no_fallback,
            0.0,
            "Should return 0 average when both estimates are 0 and no fallback",
        )

        # Test with the old behavior (use_fallback=True) for backwards compatibility
        total_points_with_fallback, avg_with_fallback = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            historical_data,
            use_fallback=True,
        )

        # Should still use fallback when explicitly requested
        self.assertGreater(
            total_points_with_fallback,
            0.0,
            "Should use fallback when use_fallback=True",
        )
        self.assertGreater(
            avg_with_fallback, 0.0, "Should use positive average when use_fallback=True"
        )

    def test_edge_cases_with_fix(self):
        """Test various edge cases with the fix."""

        # Case 1: estimated_items > 0 but estimated_points = 0
        total_points, avg = calculate_total_points(100, 5, 0, None, use_fallback=False)
        self.assertEqual(
            total_points, 0.0, "Should calculate 0 when estimated_points=0"
        )
        self.assertEqual(avg, 0.0, "Should have 0 average when estimated_points=0")

        # Case 2: Normal valid estimates (should work as before)
        total_points, avg = calculate_total_points(
            100, 10, 50, None, use_fallback=False
        )
        self.assertEqual(
            total_points, 500.0, "Should calculate normally: 100 * (50/10)"
        )
        self.assertEqual(avg, 5.0, "Should calculate avg normally: 50/10")

        # Case 3: Only estimated_items is 0 (but not both)
        total_points, avg = calculate_total_points(100, 0, 50, None, use_fallback=False)
        self.assertEqual(
            total_points, 0.0, "Should return 0 when estimated_items=0 and no fallback"
        )
        self.assertEqual(
            avg, 0.0, "Should return 0 when estimated_items=0 and no fallback"
        )

    def test_backward_compatibility_preserved(self):
        """Test that existing behavior is preserved for backward compatibility."""

        # Default behavior (use_fallback=True by default)
        total_points_default, avg_default = calculate_total_points(100, 0, 0)

        # Explicit fallback
        total_points_explicit, avg_explicit = calculate_total_points(
            100, 0, 0, None, use_fallback=True
        )

        # Both should use fallback (default 10 points per item)
        self.assertEqual(total_points_default, 1000.0, "Default should use fallback")
        self.assertEqual(
            total_points_explicit, 1000.0, "Explicit fallback=True should use fallback"
        )
        self.assertEqual(
            avg_default, 10.0, "Default should use 10 points per item fallback"
        )
        self.assertEqual(
            avg_explicit, 10.0, "Explicit fallback should use 10 points per item"
        )

    def test_user_workflow_scenario(self):
        """Test the complete user workflow scenario that was causing the bug."""

        # Simulate user inputs in the UI
        test_scenarios = [
            {
                "name": "User sets everything to 0 explicitly",
                "total_items": 100,
                "estimated_items": 0,
                "estimated_points": 0,
                "expected_total_points": 0.0,
                "expected_avg": 0.0,
            },
            {
                "name": "User leaves estimated items empty but has total items",
                "total_items": 50,
                "estimated_items": 0,
                "estimated_points": 0,
                "expected_total_points": 0.0,
                "expected_avg": 0.0,
            },
        ]

        historical_data = [
            {"date": "2025-01-01", "completed_items": 2, "completed_points": 20},
        ]

        for scenario in test_scenarios:
            with self.subTest(scenario=scenario["name"]):
                # This is how the settings callback calls it (with use_fallback=False)
                total_points, avg = calculate_total_points(
                    scenario["total_items"],
                    scenario["estimated_items"],
                    scenario["estimated_points"],
                    historical_data,
                    use_fallback=False,
                )

                self.assertEqual(
                    total_points,
                    scenario["expected_total_points"],
                    f"Scenario '{scenario['name']}' should return expected total points",
                )
                self.assertEqual(
                    avg,
                    scenario["expected_avg"],
                    f"Scenario '{scenario['name']}' should return expected average",
                )

    def test_settings_callback_integration(self):
        """Test that the fix works correctly in the settings callback context."""

        # This simulates what happens when the user sets input fields to empty/0
        # and the settings callback processes them with use_fallback=False

        with patch("data.processing.pd.DataFrame") as mock_df:
            # Mock empty historical data
            mock_df.return_value.empty = True

            # Test the scenario that was causing the bug
            from data.processing import calculate_total_points

            total_items = 100
            estimated_items = 0  # User left empty
            estimated_points = 0  # User left empty
            statistics = []  # No historical data

            # This is how callbacks/settings.py now calls it
            estimated_total_points, avg_points_per_item = calculate_total_points(
                total_items,
                estimated_items,
                estimated_points,
                statistics,
                use_fallback=False,
            )

            # The fix: should return 0, not calculated values
            self.assertEqual(
                estimated_total_points,
                0.0,
                "Settings callback should get 0 for empty inputs",
            )
            self.assertEqual(
                avg_points_per_item,
                0.0,
                "Settings callback should get 0 average for empty inputs",
            )


if __name__ == "__main__":
    unittest.main()
