"""
Unit tests for confidence interval calculations.

This module verifies that the confidence interval calculations use
statistically correct formulas based on normal distribution percentiles.
"""

import sys
from pathlib import Path

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ui.dashboard_enhanced import _calculate_confidence_intervals


class TestConfidenceIntervals:
    """Test confidence interval calculations for statistical correctness."""

    def test_confidence_intervals_use_correct_z_scores(self):
        """Verify CI calculations use correct statistical Z-scores."""
        # Test scenario with known values
        pert_forecast_days = 100
        velocity_mean = 10  # items/week
        velocity_std = 3  # items/week
        remaining_work = 50

        # Calculate expected values
        cv = velocity_std / velocity_mean  # = 0.3
        forecast_std = cv * pert_forecast_days  # = 30 days

        # Expected values using correct percentiles
        expected_ci_50 = pert_forecast_days  # 100 days (median)
        expected_ci_80 = pert_forecast_days + (0.84 * forecast_std)  # 125.2 days
        expected_ci_95 = pert_forecast_days + (1.65 * forecast_std)  # 149.5 days

        # Calculate actual values
        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # Verify results match statistical definitions
        assert result["ci_50"] == pytest.approx(expected_ci_50, abs=0.1)
        assert result["ci_80"] == pytest.approx(expected_ci_80, abs=0.1)
        assert result["ci_95"] == pytest.approx(expected_ci_95, abs=0.1)

    def test_confidence_intervals_are_properly_one_tailed(self):
        """Verify we're using one-tailed percentiles (completion by dates)."""
        pert_forecast_days = 60
        velocity_mean = 8
        velocity_std = 2
        remaining_work = 40

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # All percentiles should be >= the median (50th percentile)
        # This confirms we're using one-tailed "completion by" dates
        assert result["ci_50"] <= result["ci_80"]
        assert result["ci_80"] <= result["ci_95"]

        # 50th percentile should equal the PERT forecast (median)
        assert result["ci_50"] == pert_forecast_days

    def test_confidence_intervals_with_zero_variance(self):
        """Test edge case: zero velocity variance (deterministic)."""
        pert_forecast_days = 50
        velocity_mean = 10
        velocity_std = 0  # No variance
        remaining_work = 50

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # With no variance, all CIs should equal the forecast
        assert result["ci_50"] == pert_forecast_days
        assert result["ci_80"] == pert_forecast_days
        assert result["ci_95"] == pert_forecast_days

    def test_confidence_intervals_with_zero_mean(self):
        """Test edge case: zero velocity mean."""
        pert_forecast_days = 50
        velocity_mean = 0  # No velocity
        velocity_std = 2
        remaining_work = 50

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # Should return forecast as fallback
        assert result["ci_50"] == pert_forecast_days
        assert result["ci_80"] == pert_forecast_days
        assert result["ci_95"] == pert_forecast_days

    def test_confidence_intervals_with_high_variance(self):
        """Test with high velocity variance (CV > 0.5)."""
        pert_forecast_days = 80
        velocity_mean = 5
        velocity_std = 3  # CV = 0.6 (high variance)
        remaining_work = 40

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # With high variance, CIs should be widely spread
        ci_50_to_95_range = result["ci_95"] - result["ci_50"]
        forecast_std = (velocity_std / velocity_mean) * pert_forecast_days
        expected_range = 1.65 * forecast_std

        assert ci_50_to_95_range == pytest.approx(expected_range, abs=0.1)

        # Range should be substantial (>30% of forecast)
        assert ci_50_to_95_range > (0.3 * pert_forecast_days)

    def test_confidence_intervals_with_low_variance(self):
        """Test with low velocity variance (CV < 0.2)."""
        pert_forecast_days = 100
        velocity_mean = 15
        velocity_std = 2  # CV = 0.133 (low variance)
        remaining_work = 75

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # With low variance, CIs should be tightly clustered
        ci_50_to_95_range = result["ci_95"] - result["ci_50"]

        # Range should be small (<25% of forecast)
        assert ci_50_to_95_range < (0.25 * pert_forecast_days)

    def test_confidence_intervals_never_negative(self):
        """Verify CIs are clamped to non-negative values."""
        # Create scenario where naive calculation might yield negative
        pert_forecast_days = 10  # Very short forecast
        velocity_mean = 2
        velocity_std = 5  # Very high variance relative to mean
        remaining_work = 5

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # All CIs should be non-negative
        assert result["ci_50"] >= 0
        assert result["ci_80"] >= 0
        assert result["ci_95"] >= 0

    def test_confidence_intervals_percentile_ordering(self):
        """Verify percentiles are properly ordered: 50th < 80th < 95th."""
        test_scenarios = [
            (50, 10, 2, 30),  # Low variance
            (80, 8, 3, 50),  # Medium variance
            (120, 5, 4, 60),  # High variance
        ]

        for pert_days, vel_mean, vel_std, work in test_scenarios:
            result = _calculate_confidence_intervals(pert_days, vel_mean, vel_std, work)

            # Strict ordering
            assert result["ci_50"] <= result["ci_80"], (
                f"50th percentile ({result['ci_50']}) should be <= "
                f"80th ({result['ci_80']})"
            )
            assert result["ci_80"] <= result["ci_95"], (
                f"80th percentile ({result['ci_80']}) should be <= "
                f"95th ({result['ci_95']})"
            )

    def test_confidence_intervals_mathematical_formula(self):
        """Test the exact mathematical formula: ci_p = μ + z_p * σ."""
        pert_forecast_days = 75
        velocity_mean = 12
        velocity_std = 4
        remaining_work = 60

        # Calculate components manually
        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days

        # Expected CIs using exact formula
        expected_ci_50 = pert_forecast_days  # z = 0.00
        expected_ci_80 = pert_forecast_days + (0.84 * forecast_std)  # z = 0.84
        expected_ci_95 = pert_forecast_days + (1.65 * forecast_std)  # z = 1.65

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # Verify exact formula implementation
        assert result["ci_50"] == pytest.approx(expected_ci_50, abs=0.01)
        assert result["ci_80"] == pytest.approx(expected_ci_80, abs=0.01)
        assert result["ci_95"] == pytest.approx(expected_ci_95, abs=0.01)

    def test_confidence_intervals_realistic_scenario(self):
        """Test with realistic agile team data."""
        # Scenario: Team averaging 10 items/week with ±3 items variance
        # PERT forecast: 50 days to complete remaining 30 items
        pert_forecast_days = 50
        velocity_mean = 10
        velocity_std = 3
        remaining_work = 30

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        # Sanity checks for realistic values
        assert 40 < result["ci_50"] < 60, "50th percentile should be near forecast"
        assert 50 < result["ci_80"] < 80, "80th percentile should add buffer"
        assert 60 < result["ci_95"] < 100, "95th percentile should be conservative"

        # Verify spacing makes sense
        buffer_80 = result["ci_80"] - result["ci_50"]
        buffer_95 = result["ci_95"] - result["ci_50"]

        # 95th percentile buffer should be roughly 2x the 80th percentile buffer
        # (since 1.65/0.84 ≈ 1.96)
        ratio = buffer_95 / buffer_80 if buffer_80 > 0 else 0
        assert 1.8 < ratio < 2.2, "Buffer ratio should be approximately 2:1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
