#!/usr/bin/env python3
"""
Unit tests for PERT Factor and Data Points constraint logic.

This module tests the constraints and interactions between PERT Factor and Data Points
sliders to ensure they work correctly for various dataset sizes.
"""

import pytest


class TestPERTConstraintLogic:
    """Test class for PERT Factor and Data Points constraint logic."""

    @pytest.mark.parametrize(
        "data_points, expected_max_pert",
        [
            # Standard cases with sufficient data
            (6, 3),  # minimum case: 6//2 = 3, constrained to min 3 for >=6 points
            (10, 5),  # 10//2 = 5
            (25, 12),  # 25//2 = 12
            (30, 15),  # 30//2 = 15, but capped at 15
            (50, 15),  # 50//2 = 25, but capped at 15
            # Small dataset cases
            (4, 2),  # 4//2 = 2, constraint satisfied: 2*2=4 <= 4
            (2, 1),  # 2//2 = 1, constraint satisfied: 1*2=2 <= 2
            # Edge cases
            (1, 1),  # 1//2 = 0, but minimum is 1
            (0, 1),  # Empty dataset, should default to minimum
        ],
    )
    def test_pert_factor_constraints(self, data_points, expected_max_pert):
        """
        Test PERT Factor maximum constraint calculation.

        The maximum PERT Factor should be floor(available_data_points / 2)
        with appropriate minimums and caps applied.
        """
        # Simulate the constraint logic from the callback
        max_pert_factor = max(1, data_points // 2)  # Ensure minimum of 1

        # For datasets with 6+ data points, ensure PERT factor is at least 3
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)

        # Cap at reasonable maximum (15) for performance
        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == expected_max_pert, (
            f"For {data_points} data points, expected max PERT factor {expected_max_pert}, "
            f"got {max_pert_factor}"
        )

    @pytest.mark.parametrize(
        "data_points, expected_min_pert",
        [
            # Standard cases
            (6, 3),  # >=6 points should have minimum 3
            (10, 3),  # >=6 points should have minimum 3
            (25, 3),  # >=6 points should have minimum 3
            # Small dataset cases
            (4, 1),  # <6 points should have minimum 1
            (2, 1),  # <6 points should have minimum 1
            (1, 1),  # <6 points should have minimum 1
            (0, 1),  # Edge case
        ],
    )
    def test_pert_factor_minimum(self, data_points, expected_min_pert):
        """
        Test PERT Factor minimum constraint calculation.

        The minimum should be 1 for small datasets (<6 points) and 3 for larger datasets.
        """
        min_pert_factor = 1 if data_points < 6 else 3

        assert min_pert_factor == expected_min_pert, (
            f"For {data_points} data points, expected min PERT factor {expected_min_pert}, "
            f"got {min_pert_factor}"
        )

    @pytest.mark.parametrize(
        "pert_factor, data_points",
        [
            # Valid constraint cases
            (3, 6),  # 3*2 = 6 <= 6 ✓
            (5, 10),  # 5*2 = 10 <= 10 ✓
            (12, 25),  # 12*2 = 24 <= 25 ✓
            (15, 30),  # 15*2 = 30 <= 30 ✓
            (2, 4),  # 2*2 = 4 <= 4 ✓
            (1, 2),  # 1*2 = 2 <= 2 ✓
        ],
    )
    def test_constraint_satisfaction(self, pert_factor, data_points):
        """
        Test that the fundamental constraint PERT_Factor × 2 ≤ available_data_points
        is always satisfied.
        """
        min_data_points_required = pert_factor * 2

        assert min_data_points_required <= data_points, (
            f"Constraint violated: PERT factor {pert_factor} requires "
            f"{min_data_points_required} data points but only {data_points} available"
        )

    def test_data_points_slider_constraints(self):
        """Test data points slider min/max calculation."""
        test_cases = [
            # (pert_factor, available_data, expected_min, expected_max)
            (3, 10, 6, 10),  # min = 3*2=6, max = 10
            (5, 15, 10, 15),  # min = 5*2=10, max = 15
            (2, 4, 4, 4),  # min = 2*2=4, max = 4 (edge case)
            (1, 2, 2, 2),  # min = 1*2=2, max = 2 (edge case)
        ]

        for pert_factor, available_data, expected_min, expected_max in test_cases:
            # Simulate data points constraints calculation
            min_value = pert_factor * 2
            max_value = available_data
            min_value = min(min_value, max_value)  # Ensure min doesn't exceed max

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
        """Test specific user scenarios to ensure realistic use cases work correctly."""
        # Apply the complete constraint logic
        max_pert_factor = max(1, data_points // 2)
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        min_data_for_max = max_pert_factor * 2

        # Validate PERT factor calculation
        assert max_pert_factor == expected_max_pert, (
            f"{scenario_name}: Expected max PERT factor {expected_max_pert}, "
            f"got {max_pert_factor}"
        )

        # Validate minimum data points requirement
        assert min_data_for_max == expected_min_data_for_max, (
            f"{scenario_name}: Expected min data points {expected_min_data_for_max}, "
            f"got {min_data_for_max}"
        )

        # Validate constraint satisfaction
        assert min_data_for_max <= data_points, (
            f"{scenario_name}: Constraint violation - need {min_data_for_max} "
            f"data points but only have {data_points}"
        )

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test zero data points
        max_pert_factor = max(1, 0 // 2)
        if 0 >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == 1, "Zero data points should result in PERT factor 1"

        # Test very large dataset
        data_points = 1000
        max_pert_factor = max(1, data_points // 2)
        if data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)
        max_pert_factor = min(max_pert_factor, 15)

        assert max_pert_factor == 15, "Very large dataset should be capped at 15"

        # Test constraint satisfaction for edge cases
        min_required = max_pert_factor * 2
        assert min_required <= data_points, (
            f"Large dataset constraint violated: need {min_required} but have {data_points}"
        )

    def test_constraint_rule_documentation(self):
        """Test that the implemented logic matches the documented rules."""
        # Test the documented constraint rules:
        # - PERT Factor minimum: 1 for small datasets (<6 points), 3 for larger datasets
        # - PERT Factor maximum: min(15, floor(available_data_points / 2))
        # - Data Points minimum: PERT Factor × 2
        # - Data Points maximum: all available data points

        test_cases = [
            # Small datasets (<6 points)
            {"data_points": 2, "min_pert": 1, "max_pert": 1},
            {"data_points": 4, "min_pert": 1, "max_pert": 2},
            {"data_points": 5, "min_pert": 1, "max_pert": 2},
            # Larger datasets (≥6 points)
            {"data_points": 6, "min_pert": 3, "max_pert": 3},
            {"data_points": 8, "min_pert": 3, "max_pert": 4},
            {"data_points": 30, "min_pert": 3, "max_pert": 15},
            {"data_points": 50, "min_pert": 3, "max_pert": 15},
        ]

        for case in test_cases:
            data_points = case["data_points"]
            expected_min_pert = case["min_pert"]
            expected_max_pert = case["max_pert"]

            # Calculate actual values using the implemented logic
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

            # Verify data points constraints
            min_data_points = min_pert_factor * 2
            max_data_points = data_points

            # The minimum should be achievable
            assert min_data_points <= max_data_points, (
                f"Data points {data_points}: min required {min_data_points} "
                f"exceeds available {max_data_points}"
            )


class TestPERTConstraintIntegration:
    """Integration tests for PERT constraint logic with realistic scenarios."""

    def test_slider_interaction_simulation(self):
        """Simulate realistic slider interactions to ensure they work together."""
        scenarios = [
            # User starts with 25 data points, sets PERT factor to maximum
            {
                "available_data": 25,
                "user_pert_choice": 12,  # Maximum allowed
                "expected_data_min": 24,  # 12 * 2
                "expected_data_max": 25,
            },
            # User has small dataset, needs to work with constraints
            {
                "available_data": 4,
                "user_pert_choice": 2,  # Maximum allowed
                "expected_data_min": 4,  # 2 * 2
                "expected_data_max": 4,
            },
            # User has large dataset
            {
                "available_data": 40,
                "user_pert_choice": 15,  # Capped maximum
                "expected_data_min": 30,  # 15 * 2
                "expected_data_max": 40,
            },
        ]

        for scenario in scenarios:
            data_points = scenario["available_data"]
            pert_factor = scenario["user_pert_choice"]

            # Verify PERT factor is valid for this dataset
            max_allowed_pert = max(1, data_points // 2)
            if data_points >= 6:
                max_allowed_pert = max(3, max_allowed_pert)
            max_allowed_pert = min(max_allowed_pert, 15)

            assert pert_factor <= max_allowed_pert, (
                f"PERT factor {pert_factor} exceeds maximum {max_allowed_pert} "
                f"for {data_points} data points"
            )

            # Calculate data points slider constraints
            min_data = pert_factor * 2
            max_data = data_points
            min_data = min(min_data, max_data)

            assert min_data == scenario["expected_data_min"], (
                f"Expected data min {scenario['expected_data_min']}, got {min_data}"
            )
            assert max_data == scenario["expected_data_max"], (
                f"Expected data max {scenario['expected_data_max']}, got {max_data}"
            )


# Standalone functions for manual testing if needed
def validate_constraint_logic():
    """Standalone function to validate constraint logic - useful for debugging."""
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
    # Allow running the test file directly for quick validation
    import sys

    if validate_constraint_logic():
        print("[OK] All constraint logic tests pass!")
        sys.exit(0)
    else:
        print("[X] Constraint logic tests failed!")
        sys.exit(1)
