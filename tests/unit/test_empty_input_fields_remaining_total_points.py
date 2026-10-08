import unittest

from data.processing import calculate_total_points


class TestEmptyInputFieldsRemainingTotalPointsEdgeCase(unittest.TestCase):
    def test_user_reported_bug_reproduction(self):

        total_items = 295
        estimated_items = 0
        estimated_points = 0

        historical_data = [
            {"date": "2025-01-01", "completed_items": 5, "completed_points": 50},
            {"date": "2025-01-02", "completed_items": 3, "completed_points": 30},
            {"date": "2025-01-03", "completed_items": 4, "completed_points": 40},
        ]

        buggy_total_points, buggy_avg = calculate_total_points(
            total_items, estimated_items, estimated_points, historical_data
        )

        fixed_total_points, fixed_avg = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            historical_data,
            use_fallback=False,
        )

        print("\n=== USER REPORTED BUG REPRODUCTION ===")
        print(
            "Scenario: "
            f"total_items={total_items}, "
            f"estimated_items={estimated_items}, "
            f"estimated_points={estimated_points}"
        )
        print(
            "Buggy behavior (use_fallback=True): "
            f"total_points={buggy_total_points}, avg={buggy_avg}"
        )
        print(
            "Fixed behavior (use_fallback=False): "
            f"total_points={fixed_total_points}, avg={fixed_avg}"
        )

        self.assertEqual(
            buggy_total_points, 2950.0, "Bug reproduces: uses historical average"
        )
        self.assertEqual(
            buggy_avg, 10.0, "Bug reproduces: calculates historical average"
        )

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

        total_items = 100

        explicit_zero_points, explicit_zero_avg = calculate_total_points(
            total_items, 0, 0, None, use_fallback=False
        )

        empty_treated_as_zero_points, empty_treated_as_zero_avg = (
            calculate_total_points(total_items, 0, 0, None, use_fallback=False)
        )

        print("\n=== EMPTY VS ZERO CONSISTENCY ===")
        print(
            "Explicit zero: "
            f"total_points={explicit_zero_points}, avg={explicit_zero_avg}"
        )
        print(
            "Empty->zero: "
            f"total_points={empty_treated_as_zero_points}, "
            f"avg={empty_treated_as_zero_avg}"
        )

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

        self.assertEqual(explicit_zero_points, 0.0, "Explicit zero should return 0")
        self.assertEqual(
            empty_treated_as_zero_points, 0.0, "Empty fields should return 0"
        )

    def test_ui_callback_integration_simulation(self):

        user_inputs = [
            {"total_items": 200, "estimated_items": None, "estimated_points": None},
            {"total_items": 150, "estimated_items": 0, "estimated_points": 0},
            {"total_items": 100, "estimated_items": 20, "estimated_points": 100},
        ]

        print("\n=== UI CALLBACK SIMULATION ===")

        for i, inputs in enumerate(user_inputs, 1):
            estimated_items = (
                0 if inputs["estimated_items"] is None else inputs["estimated_items"]
            )
            estimated_points = (
                0 if inputs["estimated_points"] is None else inputs["estimated_points"]
            )

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
                self.assertEqual(
                    total_points, 0.0, f"Case {i}: No estimates should return 0"
                )
                self.assertEqual(
                    avg, 0.0, f"Case {i}: No estimates should return 0 avg"
                )
            elif inputs["estimated_items"] > 0:
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

        total_items = 100
        estimated_items = 0
        estimated_points = 0

        old_behavior_points, old_behavior_avg = calculate_total_points(
            total_items, estimated_items, estimated_points
        )

        self.assertEqual(
            old_behavior_points, 1000.0, "Backward compatibility: should use fallback"
        )
        self.assertEqual(
            old_behavior_avg, 10.0, "Backward compatibility: should use default avg"
        )

        print("\n=== BACKWARD COMPATIBILITY ===")
        print(
            "Old behavior preserved: "
            f"total_points={old_behavior_points}, avg={old_behavior_avg}"
        )

    def test_edge_cases_after_fix(self):

        print("\n=== EDGE CASES TESTING ===")

        case1_points, case1_avg = calculate_total_points(
            100, 5, 0, None, use_fallback=False
        )
        print(f"Case 1 - items>0, points=0: {case1_points}, {case1_avg}")
        self.assertEqual(case1_points, 0.0, "Should be 0 when estimated_points=0")

        case2_points, case2_avg = calculate_total_points(
            100, 0, 50, None, use_fallback=False
        )
        print(f"Case 2 - items=0, points>0: {case2_points}, {case2_avg}")
        self.assertEqual(case2_points, 0.0, "Should be 0 when estimated_items=0")

        case3_points, case3_avg = calculate_total_points(
            100, -1, 0, None, use_fallback=False
        )
        print(f"Case 3 - negative items: {case3_points}, {case3_avg}")
        self.assertEqual(
            case3_points, 0.0, "Should handle negative estimated_items gracefully"
        )


if __name__ == "__main__":
    unittest.main()
