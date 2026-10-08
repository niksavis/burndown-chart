#!/usr/bin/env python3


import pytest


class TestPERTConstraintLogic:
    @pytest.mark.parametrize(
        "data_points, expected_max_pert",
        [
            (6, 3),
            (10, 5),
            (25, 12),
            (30, 15),
            (50, 15),
            (4, 2),
            (2, 1),
            (1, 1),
            (0, 1),
        ],
    )
    def test_pert_factor_constraints(self, data_points, expected_max_pert):

        max_pert_factor = max(1, data_points // 2)

        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)

        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == expected_max_pert, (
            f"For {data_points} data points, "
            f"expected max PERT factor {expected_max_pert}, "
            f"got {max_pert_factor}"
        )

    @pytest.mark.parametrize(
        "data_points, expected_min_pert",
        [
            (6, 3),
            (10, 3),
            (25, 3),
            (4, 1),
            (2, 1),
            (1, 1),
            (0, 1),
        ],
    )
    def test_pert_factor_minimum(self, data_points, expected_min_pert):

        min_pert_factor = 1 if data_points < 6 else 3

        assert min_pert_factor == expected_min_pert, (
            f"For {data_points} data points, "
            f"expected min PERT factor {expected_min_pert}, "
            f"got {min_pert_factor}"
        )

    @pytest.mark.parametrize(
        "pert_factor, data_points",
        [
            (3, 6),
            (5, 10),
            (12, 25),
            (15, 30),
            (2, 4),
            (1, 2),
        ],
    )
    def test_constraint_satisfaction(self, pert_factor, data_points):
        min_data_points_required = pert_factor * 2

        assert min_data_points_required <= data_points, (
            f"Constraint violated: PERT factor {pert_factor} requires "
            f"{min_data_points_required} data points but only {data_points} available"
        )

    def test_data_points_slider_constraints(self):
        test_cases = [
            (3, 10, 6, 10),
            (5, 15, 10, 15),
            (2, 4, 4, 4),
            (1, 2, 2, 2),
        ]

        for pert_factor, available_data, expected_min, expected_max in test_cases:
            min_value = pert_factor * 2
            max_value = available_data
            min_value = min(min_value, max_value)

            assert min_value == expected_min, (
                f"For PERT factor {pert_factor} and {available_data} data points, "
                f"expected min {expected_min}, got {min_value}"
            )
            assert max_value == expected_max, (
                f"For PERT factor {pert_factor} and {available_data} data points, "
                f"expected max {expected_max}, got {max_value}"
            )

    @pytest.mark.parametrize(
        "scenario_name, data_points, expected_max_pert, expected_min_data_for_max",
        [
            ("User's Example: 25 data points", 25, 12, 24),
            ("Small dataset: 8 data points", 8, 4, 8),
            ("Large dataset: 40 data points", 40, 15, 30),
            ("Tiny dataset: 3 data points", 3, 1, 2),
        ],
    )
    def test_user_scenarios(
        self, scenario_name, data_points, expected_max_pert, expected_min_data_for_max
    ):
        max_pert_factor = max(1, data_points // 2)
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        min_data_for_max = max_pert_factor * 2

        assert max_pert_factor == expected_max_pert, (
            f"{scenario_name}: Expected max PERT factor {expected_max_pert}, "
            f"got {max_pert_factor}"
        )

        assert min_data_for_max == expected_min_data_for_max, (
            f"{scenario_name}: Expected min data points {expected_min_data_for_max}, "
            f"got {min_data_for_max}"
        )

        assert min_data_for_max <= data_points, (
            f"{scenario_name}: Constraint violation - need {min_data_for_max} "
            f"data points but only have {data_points}"
        )

    def test_edge_cases(self):
        max_pert_factor = max(1, 0 // 2)
        if 0 >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == 1, "Zero data points should result in PERT factor 1"

        data_points = 1000
        max_pert_factor = max(1, data_points // 2)
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == 15, "Very large dataset should be capped at 15"

        min_required = max_pert_factor * 2
        assert min_required <= data_points, (
            "Large dataset constraint violated: "
            f"need {min_required} but have {data_points}"
        )

    def test_constraint_rule_documentation(self):

        test_cases = [
            {"data_points": 2, "min_pert": 1, "max_pert": 1},
            {"data_points": 4, "min_pert": 1, "max_pert": 2},
            {"data_points": 5, "min_pert": 1, "max_pert": 2},
            {"data_points": 6, "min_pert": 3, "max_pert": 3},
            {"data_points": 8, "min_pert": 3, "max_pert": 4},
            {"data_points": 30, "min_pert": 3, "max_pert": 15},
            {"data_points": 50, "min_pert": 3, "max_pert": 15},
        ]

        for case in test_cases:
            data_points = case["data_points"]
            expected_min_pert = case["min_pert"]
            expected_max_pert = case["max_pert"]

            min_pert_factor = 1 if data_points < 6 else 3
            max_pert_factor = max(1, data_points // 2)
            if data_points >= 6:
                max_pert_factor = max(3, max_pert_factor)
            max_pert_factor = min(max_pert_factor, 15)

            assert min_pert_factor == expected_min_pert, (
                f"Data points {data_points}: expected min PERT {expected_min_pert}, "
                f"got {min_pert_factor}"
            )
            assert max_pert_factor == expected_max_pert, (
                f"Data points {data_points}: expected max PERT {expected_max_pert}, "
                f"got {max_pert_factor}"
            )

            min_data_points = min_pert_factor * 2
            max_data_points = data_points

            assert min_data_points <= max_data_points, (
                f"Data points {data_points}: min required {min_data_points} "
                f"exceeds available {max_data_points}"
            )


class TestPERTConstraintIntegration:
    def test_slider_interaction_simulation(self):
        scenarios = [
            {
                "available_data": 25,
                "user_pert_choice": 12,
                "expected_data_min": 24,
                "expected_data_max": 25,
            },
            {
                "available_data": 4,
                "user_pert_choice": 2,
                "expected_data_min": 4,
                "expected_data_max": 4,
            },
            {
                "available_data": 40,
                "user_pert_choice": 15,
                "expected_data_min": 30,
                "expected_data_max": 40,
            },
        ]

        for scenario in scenarios:
            data_points = scenario["available_data"]
            pert_factor = scenario["user_pert_choice"]

            max_allowed_pert = max(1, data_points // 2)
            if data_points >= 6:
                max_allowed_pert = max(3, max_allowed_pert)
            max_allowed_pert = min(max_allowed_pert, 15)

            assert pert_factor <= max_allowed_pert, (
                f"PERT factor {pert_factor} exceeds maximum {max_allowed_pert} "
                f"for {data_points} data points"
            )

            min_data = pert_factor * 2
            max_data = data_points
            min_data = min(min_data, max_data)

            assert min_data == scenario["expected_data_min"], (
                f"Expected data min {scenario['expected_data_min']}, got {min_data}"
            )
            assert max_data == scenario["expected_data_max"], (
                f"Expected data max {scenario['expected_data_max']}, got {max_data}"
            )


def validate_constraint_logic():
    test_cases = [(6, 3), (10, 5), (25, 12), (30, 15), (50, 15), (4, 2), (2, 1)]

    all_passed = True
    for data_points, expected_max_pert in test_cases:
        max_pert_factor = max(1, data_points // 2)
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        min_data_points = max_pert_factor * 2
        constraint_satisfied = min_data_points <= data_points

        if max_pert_factor != expected_max_pert or not constraint_satisfied:
            all_passed = False
            break

    return all_passed


if __name__ == "__main__":
    import sys

    if validate_constraint_logic():
        print("[OK] All constraint logic tests pass!")
        sys.exit(0)
    else:
        print("[X] Constraint logic tests failed!")
        sys.exit(1)
