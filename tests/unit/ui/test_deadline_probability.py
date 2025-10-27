"""
Unit tests for deadline probability calculations.

This module verifies that deadline probability calculations use
correct normal distribution CDF and produce statistically valid results.
"""

import pytest
import sys
from pathlib import Path
from scipy import stats

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ui.dashboard_enhanced import _calculate_deadline_probability


class TestDeadlineProbability:
    """Test deadline probability calculations for statistical correctness."""

    def test_deadline_probability_matches_normal_cdf(self):
        """Verify probability calculation uses correct normal CDF."""
        # Test scenario
        days_to_deadline = 70
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        # Calculate expected probability manually
        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days
        z = (days_to_deadline - pert_forecast_days) / forecast_std
        expected_probability = stats.norm.cdf(z) * 100

        # Calculate actual probability
        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Verify it matches statistical definition
        assert result == pytest.approx(expected_probability, abs=0.1)

    def test_deadline_probability_at_forecast_date(self):
        """Test probability at exactly the forecast date (should be ~50%)."""
        pert_forecast_days = 100
        days_to_deadline = 100  # Same as forecast
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # At the median (forecast), probability should be 50%
        assert result == pytest.approx(50.0, abs=1.0)

    def test_deadline_probability_well_before_forecast(self):
        """Test deadline well before forecast (should be low probability)."""
        pert_forecast_days = 100
        days_to_deadline = 60  # 40 days before forecast
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Should be very low probability (<5%)
        assert result < 5.0

    def test_deadline_probability_well_after_forecast(self):
        """Test deadline well after forecast (should be high probability)."""
        pert_forecast_days = 60
        days_to_deadline = 100  # 40 days after forecast
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Should be very high probability (>95%)
        assert result > 95.0

    def test_deadline_probability_with_buffer(self):
        """Test realistic scenario with reasonable buffer."""
        pert_forecast_days = 50
        days_to_deadline = 60  # 10 days buffer
        velocity_mean = 10
        velocity_std = 3

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # With buffer, should be good probability (60-80%)
        assert 60 < result < 80

    def test_deadline_probability_with_zero_variance(self):
        """Test edge case: zero velocity variance (deterministic)."""
        pert_forecast_days = 50
        days_to_deadline = 60
        velocity_mean = 10
        velocity_std = 0  # No variance

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # With no variance, should be 100% (deadline after forecast)
        assert result == 100.0

    def test_deadline_probability_with_zero_variance_before_deadline(self):
        """Test deterministic case where deadline is before forecast."""
        pert_forecast_days = 70
        days_to_deadline = 60  # Before forecast
        velocity_mean = 10
        velocity_std = 0  # No variance

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # With no variance, should be 0% (deadline before forecast)
        assert result == 0.0

    def test_deadline_probability_with_zero_mean(self):
        """Test edge case: zero velocity mean."""
        pert_forecast_days = 50
        days_to_deadline = 60
        velocity_mean = 0  # No velocity
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Should return 50% as fallback
        assert result == 50.0

    def test_deadline_probability_bounds(self):
        """Verify probability is always between 0 and 100."""
        test_scenarios = [
            (20, 100, 10, 2),  # Very early deadline
            (100, 100, 10, 2),  # At forecast
            (200, 100, 10, 2),  # Very late deadline
            (50, 40, 5, 10),  # High variance scenario
        ]

        for deadline, forecast, vel_mean, vel_std in test_scenarios:
            result = _calculate_deadline_probability(
                deadline, forecast, vel_std, vel_mean
            )

            # Probability must be in [0, 100]
            assert 0 <= result <= 100, (
                f"Probability {result}% out of bounds for scenario {(deadline, forecast, vel_mean, vel_std)}"
            )

    def test_deadline_probability_increases_with_deadline(self):
        """Verify probability increases as deadline moves further out."""
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        # Test deadlines at increasing distances
        deadlines = [40, 50, 60, 70, 80, 90]
        probabilities = []

        for deadline in deadlines:
            prob = _calculate_deadline_probability(
                deadline, pert_forecast_days, velocity_std, velocity_mean
            )
            probabilities.append(prob)

        # Probabilities should be monotonically increasing
        for i in range(len(probabilities) - 1):
            assert probabilities[i] <= probabilities[i + 1], (
                f"Probability should increase with deadline: {probabilities}"
            )

    def test_deadline_probability_with_high_variance(self):
        """Test with high velocity variance (more uncertainty)."""
        pert_forecast_days = 60
        days_to_deadline = 70  # 10 days buffer
        velocity_mean = 10
        velocity_std = 5  # High variance (CV = 0.5)

        result_high_var = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Compare with low variance scenario
        result_low_var = _calculate_deadline_probability(
            days_to_deadline,
            pert_forecast_days,
            2,
            velocity_mean,  # velocity_std = 2
        )

        # Lower variance should give higher probability (more confidence)
        assert result_low_var > result_high_var

    def test_deadline_probability_realistic_scenarios(self):
        """Test with realistic agile team scenarios."""
        scenarios = [
            # (days_to_deadline, pert_forecast, vel_mean, vel_std, expected_range)
            (60, 50, 10, 3, (70, 85)),  # Good buffer, should be high probability
            (55, 50, 10, 3, (55, 70)),  # Small buffer, moderate probability
            (50, 50, 10, 3, (45, 55)),  # No buffer, ~50% probability
            (45, 50, 10, 3, (30, 45)),  # Negative buffer, lower probability
            (40, 50, 10, 3, (15, 30)),  # Large negative buffer, low probability
        ]

        for deadline, forecast, vel_mean, vel_std, (min_prob, max_prob) in scenarios:
            result = _calculate_deadline_probability(
                deadline, forecast, vel_std, vel_mean
            )

            assert min_prob <= result <= max_prob, (
                f"Probability {result}% not in expected range [{min_prob}, {max_prob}] "
                f"for scenario: deadline={deadline}, forecast={forecast}"
            )

    def test_deadline_probability_z_score_calculation(self):
        """Verify Z-score is calculated correctly."""
        days_to_deadline = 75
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        # Calculate Z-score manually
        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days
        expected_z = (days_to_deadline - pert_forecast_days) / forecast_std

        # Get probability and reverse-engineer Z-score
        result_prob = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        # Verify by checking against manual calculation
        expected_prob = stats.norm.cdf(expected_z) * 100
        assert result_prob == pytest.approx(expected_prob, abs=0.1)

    def test_deadline_probability_symmetry(self):
        """Test that probabilities are symmetric around the forecast."""
        pert_forecast_days = 80
        velocity_mean = 10
        velocity_std = 4
        buffer_days = 15

        # Test deadline before and after forecast by same amount
        prob_before = _calculate_deadline_probability(
            pert_forecast_days - buffer_days,
            pert_forecast_days,
            velocity_std,
            velocity_mean,
        )
        prob_after = _calculate_deadline_probability(
            pert_forecast_days + buffer_days,
            pert_forecast_days,
            velocity_std,
            velocity_mean,
        )

        # They should be symmetric: prob_before + prob_after ≈ 100%
        # (with small tolerance for numerical precision)
        assert prob_before + prob_after == pytest.approx(100.0, abs=2.0)

    def test_deadline_probability_cv_impact(self):
        """Test how coefficient of variation affects probability."""
        days_to_deadline = 70
        pert_forecast_days = 60

        # Test different CVs with same absolute std relative to forecast
        scenarios = [
            (20, 2),  # CV = 0.1 (very stable)
            (10, 2),  # CV = 0.2 (stable)
            (5, 2),  # CV = 0.4 (moderate variance)
            (2.5, 2),  # CV = 0.8 (high variance)
        ]

        probabilities = []
        for vel_mean, vel_std in scenarios:
            prob = _calculate_deadline_probability(
                days_to_deadline, pert_forecast_days, vel_std, vel_mean
            )
            probabilities.append(prob)

        # Higher CV → lower probability (less confidence)
        for i in range(len(probabilities) - 1):
            assert probabilities[i] >= probabilities[i + 1], (
                f"Probability should decrease with increasing CV: {probabilities}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
