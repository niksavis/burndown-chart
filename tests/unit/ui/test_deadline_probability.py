import sys
from pathlib import Path

import pytest
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ui.dashboard_enhanced import _calculate_deadline_probability


class TestDeadlineProbability:
    def test_deadline_probability_matches_normal_cdf(self):
        days_to_deadline = 70
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days
        z = (days_to_deadline - pert_forecast_days) / forecast_std
        expected_probability = stats.norm.cdf(z) * 100

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result == pytest.approx(expected_probability, abs=0.1)

    def test_deadline_probability_at_forecast_date(self):
        pert_forecast_days = 100
        days_to_deadline = 100
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result == pytest.approx(50.0, abs=1.0)

    def test_deadline_probability_well_before_forecast(self):
        pert_forecast_days = 100
        days_to_deadline = 60
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result < 5.0

    def test_deadline_probability_well_after_forecast(self):
        pert_forecast_days = 60
        days_to_deadline = 100
        velocity_mean = 10
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result > 95.0

    def test_deadline_probability_with_buffer(self):
        pert_forecast_days = 50
        days_to_deadline = 60
        velocity_mean = 10
        velocity_std = 3

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert 60 < result < 80

    def test_deadline_probability_with_zero_variance(self):
        pert_forecast_days = 50
        days_to_deadline = 60
        velocity_mean = 10
        velocity_std = 0

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result == 100.0

    def test_deadline_probability_with_zero_variance_before_deadline(self):
        pert_forecast_days = 70
        days_to_deadline = 60
        velocity_mean = 10
        velocity_std = 0

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result == 0.0

    def test_deadline_probability_with_zero_mean(self):
        pert_forecast_days = 50
        days_to_deadline = 60
        velocity_mean = 0
        velocity_std = 2

        result = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        assert result == 50.0

    def test_deadline_probability_bounds(self):
        test_scenarios = [
            (20, 100, 10, 2),
            (100, 100, 10, 2),
            (200, 100, 10, 2),
            (50, 40, 5, 10),
        ]

        for deadline, forecast, vel_mean, vel_std in test_scenarios:
            result = _calculate_deadline_probability(
                deadline, forecast, vel_std, vel_mean
            )

            assert 0 <= result <= 100, (
                f"Probability {result}% out of bounds for scenario "
                f"{(deadline, forecast, vel_mean, vel_std)}"
            )

    def test_deadline_probability_increases_with_deadline(self):
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        deadlines = [40, 50, 60, 70, 80, 90]
        probabilities = []

        for deadline in deadlines:
            prob = _calculate_deadline_probability(
                deadline, pert_forecast_days, velocity_std, velocity_mean
            )
            probabilities.append(prob)

        for i in range(len(probabilities) - 1):
            assert probabilities[i] <= probabilities[i + 1], (
                f"Probability should increase with deadline: {probabilities}"
            )

    def test_deadline_probability_with_high_variance(self):
        pert_forecast_days = 60
        days_to_deadline = 70
        velocity_mean = 10
        velocity_std = 5

        result_high_var = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        result_low_var = _calculate_deadline_probability(
            days_to_deadline,
            pert_forecast_days,
            2,
            velocity_mean,
        )

        assert result_low_var > result_high_var

    def test_deadline_probability_realistic_scenarios(self):
        scenarios = [
            (60, 50, 10, 3, (70, 85)),
            (55, 50, 10, 3, (55, 70)),
            (50, 50, 10, 3, (45, 55)),
            (45, 50, 10, 3, (30, 45)),
            (40, 50, 10, 3, (15, 30)),
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
        days_to_deadline = 75
        pert_forecast_days = 60
        velocity_mean = 10
        velocity_std = 3

        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days
        expected_z = (days_to_deadline - pert_forecast_days) / forecast_std

        result_prob = _calculate_deadline_probability(
            days_to_deadline, pert_forecast_days, velocity_std, velocity_mean
        )

        expected_prob = stats.norm.cdf(expected_z) * 100
        assert result_prob == pytest.approx(expected_prob, abs=0.1)

    def test_deadline_probability_symmetry(self):
        pert_forecast_days = 80
        velocity_mean = 10
        velocity_std = 4
        buffer_days = 15

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

        assert prob_before + prob_after == pytest.approx(100.0, abs=2.0)

    def test_deadline_probability_cv_impact(self):
        days_to_deadline = 70
        pert_forecast_days = 60

        scenarios = [
            (20, 2),
            (10, 2),
            (5, 2),
            (2.5, 2),
        ]

        probabilities = []
        for vel_mean, vel_std in scenarios:
            prob = _calculate_deadline_probability(
                days_to_deadline, pert_forecast_days, vel_std, vel_mean
            )
            probabilities.append(prob)

        for i in range(len(probabilities) - 1):
            assert probabilities[i] >= probabilities[i + 1], (
                f"Probability should decrease with increasing CV: {probabilities}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
