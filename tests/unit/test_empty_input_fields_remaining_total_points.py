"""
Test for empty input fields edge case with Remaining Total Points calculation.

User Reported Bug:
- Remaining Estimated Items: empty (primary suspect)
- Remaining Total Items: empty
- Remaining Estimated Points: empty
- But "Remaining Total Points" still shows calculated values instead of 0
- It behaves correctly when these fields are manually set to 0

Root Cause:
The calculate_total_points function in data/processing.py uses historical data fallback
when estimated_items <= 0, which creates unexpected behavior when users leave
input fields empty (expecting 0) versus when they want automatic estimation.

Fix:
Added use_fallback parameter to calculate_total_points function to control when
fallback calculation should be used. UI input callbacks use use_fallback=False
to respect user's explicit empty input choices.
"""

import unittest
from data.processing import calculate_total_points


class TestEmptyInputFieldsRemainingTotalPointsEdgeCase(unittest.TestCase):
    """Test empty input fields edge case with Remaining Total Points calculation."""

    def test_user_reported_bug_reproduction(self):
        """Reproduce the exact bug scenario reported by user."""

        # User's scenario: They have historical data, total items, but no estimates
        total_items = 295  # User's remaining items count
        estimated_items = 0  # User left "Remaining Estimated Items" empty
        estimated_points = 0  # User left "Remaining Estimated Points" empty

        # User has historical statistics (from their burndown data)
        historical_data = [
            {"date": "2025-01-01", "completed_items": 5, "completed_points": 50},
            {"date": "2025-01-02", "completed_items": 3, "completed_points": 30},
            {"date": "2025-01-03", "completed_items": 4, "completed_points": 40},
        ]

        # Original buggy behavior (still happens with default use_fallback=True)
        buggy_total_points, buggy_avg = calculate_total_points(
            total_items, estimated_items, estimated_points, historical_data
        )

        # Fixed behavior (happens with use_fallback=False)
        fixed_total_points, fixed_avg = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            historical_data,
            use_fallback=False,
        )

        print(f"\n=== USER REPORTED BUG REPRODUCTION ===")
        print(
            f"Scenario: total_items={total_items}, estimated_items={estimated_items}, estimated_points={estimated_points}"
        )
        print(
            f"Buggy behavior (use_fallback=True): total_points={buggy_total_points}, avg={buggy_avg}"
        )
        print(
            f"Fixed behavior (use_fallback=False): total_points={fixed_total_points}, avg={fixed_avg}"
        )

        # Bug: Default behavior uses historical data to calculate points
        # Historical avg = (50+30+40)/(5+3+4) = 120/12 = 10 points per item
        # So buggy result = 295 * 10 = 2950
        self.assertEqual(
            buggy_total_points, 2950.0, "Bug reproduces: uses historical average"
        )
        self.assertEqual(
            buggy_avg, 10.0, "Bug reproduces: calculates historical average"
        )

        # Fix: With use_fallback=False, respects user's empty input
        self.assertEqual(
            fixed_total_points,
            0.0,
            "Fix works: returns 0 when user provides no estimates",
        )
        self.assertEqual(
            fixed_avg,
            0.0,
            "Fix works: returns 0 average when user provides no estimates",
        )

    def test_empty_vs_zero_distinction(self):
        """Test that empty fields and explicit zero behave the same way with the fix."""

        total_items = 100

        # Scenario 1: User explicitly sets values to 0
        explicit_zero_points, explicit_zero_avg = calculate_total_points(
            total_items, 0, 0, None, use_fallback=False
        )

        # Scenario 2: UI interprets empty fields as 0 and calls with use_fallback=False
        empty_treated_as_zero_points, empty_treated_as_zero_avg = (
            calculate_total_points(total_items, 0, 0, None, use_fallback=False)
        )

        print(f"\n=== EMPTY VS ZERO CONSISTENCY ===")
        print(
            f"Explicit zero: total_points={explicit_zero_points}, avg={explicit_zero_avg}"
        )
        print(
            f"Empty->zero: total_points={empty_treated_as_zero_points}, avg={empty_treated_as_zero_avg}"
        )

        # Both should behave identically with the fix
        self.assertEqual(
            explicit_zero_points,
            empty_treated_as_zero_points,
            "Empty and explicit 0 should behave the same",
        )
        self.assertEqual(
            explicit_zero_avg,
            empty_treated_as_zero_avg,
            "Empty and explicit 0 should behave the same",
        )

        # Both should return 0
        self.assertEqual(explicit_zero_points, 0.0, "Explicit zero should return 0")
        self.assertEqual(
            empty_treated_as_zero_points, 0.0, "Empty fields should return 0"
        )

    def test_ui_callback_integration_simulation(self):
        """Simulate how the UI callback should behave after the fix."""

        # Simulate user input from UI form
        user_inputs = [
            # Case 1: User leaves all estimation fields empty
            {"total_items": 200, "estimated_items": None, "estimated_points": None},
            # Case 2: User explicitly sets estimation fields to 0
            {"total_items": 150, "estimated_items": 0, "estimated_points": 0},
            # Case 3: User provides partial estimates
            {"total_items": 100, "estimated_items": 20, "estimated_points": 100},
        ]

        print(f"\n=== UI CALLBACK SIMULATION ===")

        for i, inputs in enumerate(user_inputs, 1):
            # UI callback would convert None to 0
            estimated_items = (
                0 if inputs["estimated_items"] is None else inputs["estimated_items"]
            )
            estimated_points = (
                0 if inputs["estimated_points"] is None else inputs["estimated_points"]
            )

            # UI callback uses use_fallback=False to respect user input
            total_points, avg = calculate_total_points(
                inputs["total_items"],
                estimated_items,
                estimated_points,
                None,
                use_fallback=False,
            )

            print(
                f"Case {i}: inputs={inputs} -> total_points={total_points}, avg={avg}"
            )

            if inputs["estimated_items"] in [None, 0] and inputs[
                "estimated_points"
            ] in [None, 0]:
                # Should return 0 when no estimates provided
                self.assertEqual(
                    total_points, 0.0, f"Case {i}: No estimates should return 0"
                )
                self.assertEqual(
                    avg, 0.0, f"Case {i}: No estimates should return 0 avg"
                )
            elif inputs["estimated_items"] > 0:
                # Should calculate based on provided estimates
                expected_total = inputs["total_items"] * (
                    inputs["estimated_points"] / inputs["estimated_items"]
                )
                expected_avg = inputs["estimated_points"] / inputs["estimated_items"]
                self.assertEqual(
                    total_points,
                    expected_total,
                    f"Case {i}: Should calculate from estimates",
                )
                self.assertEqual(
                    avg, expected_avg, f"Case {i}: Should calculate avg from estimates"
                )

    def test_backward_compatibility_preserved(self):
        """Test that existing code using default behavior still works."""

        total_items = 100
        estimated_items = 0
        estimated_points = 0

        # Existing code that doesn't specify use_fallback (should default to True)
        old_behavior_points, old_behavior_avg = calculate_total_points(
            total_items, estimated_items, estimated_points
        )

        # Should still use fallback (10 points per item default)
        self.assertEqual(
            old_behavior_points, 1000.0, "Backward compatibility: should use fallback"
        )
        self.assertEqual(
            old_behavior_avg, 10.0, "Backward compatibility: should use default avg"
        )

        print(f"\n=== BACKWARD COMPATIBILITY ===")
        print(
            f"Old behavior preserved: total_points={old_behavior_points}, avg={old_behavior_avg}"
        )

    def test_edge_cases_after_fix(self):
        """Test various edge cases to ensure the fix is robust."""

        print(f"\n=== EDGE CASES TESTING ===")

        # Edge case 1: estimated_items > 0 but estimated_points = 0
        case1_points, case1_avg = calculate_total_points(
            100, 5, 0, None, use_fallback=False
        )
        print(f"Case 1 - items>0, points=0: {case1_points}, {case1_avg}")
        self.assertEqual(case1_points, 0.0, "Should be 0 when estimated_points=0")

        # Edge case 2: estimated_items = 0 but estimated_points > 0
        case2_points, case2_avg = calculate_total_points(
            100, 0, 50, None, use_fallback=False
        )
        print(f"Case 2 - items=0, points>0: {case2_points}, {case2_avg}")
        self.assertEqual(case2_points, 0.0, "Should be 0 when estimated_items=0")

        # Edge case 3: Negative values (shouldn't happen in UI but test robustness)
        case3_points, case3_avg = calculate_total_points(
            100, -1, 0, None, use_fallback=False
        )
        print(f"Case 3 - negative items: {case3_points}, {case3_avg}")
        self.assertEqual(
            case3_points, 0.0, "Should handle negative estimated_items gracefully"
        )


if __name__ == "__main__":
    unittest.main()
