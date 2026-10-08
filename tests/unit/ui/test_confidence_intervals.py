import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ui.dashboard_enhanced import _calculate_confidence_intervals


class TestConfidenceIntervals:
    def test_confidence_intervals_use_correct_z_scores(self):
        pert_forecast_days = 100
        velocity_mean = 10
        velocity_std = 3
        remaining_work = 50

        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days

        expected_ci_50 = pert_forecast_days
        expected_ci_80 = pert_forecast_days + (0.84 * forecast_std)
        expected_ci_95 = pert_forecast_days + (1.65 * forecast_std)

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] == pytest.approx(expected_ci_50, abs=0.1)
        assert result["ci_80"] == pytest.approx(expected_ci_80, abs=0.1)
        assert result["ci_95"] == pytest.approx(expected_ci_95, abs=0.1)

    def test_confidence_intervals_are_properly_one_tailed(self):
        pert_forecast_days = 60
        velocity_mean = 8
        velocity_std = 2
        remaining_work = 40

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] <= result["ci_80"]
        assert result["ci_80"] <= result["ci_95"]

        assert result["ci_50"] == pert_forecast_days

    def test_confidence_intervals_with_zero_variance(self):
        pert_forecast_days = 50
        velocity_mean = 10
        velocity_std = 0
        remaining_work = 50

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] == pert_forecast_days
        assert result["ci_80"] == pert_forecast_days
        assert result["ci_95"] == pert_forecast_days

    def test_confidence_intervals_with_zero_mean(self):
        pert_forecast_days = 50
        velocity_mean = 0
        velocity_std = 2
        remaining_work = 50

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] == pert_forecast_days
        assert result["ci_80"] == pert_forecast_days
        assert result["ci_95"] == pert_forecast_days

    def test_confidence_intervals_with_high_variance(self):
        pert_forecast_days = 80
        velocity_mean = 5
        velocity_std = 3
        remaining_work = 40

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        ci_50_to_95_range = result["ci_95"] - result["ci_50"]
        forecast_std = (velocity_std / velocity_mean) * pert_forecast_days
        expected_range = 1.65 * forecast_std

        assert ci_50_to_95_range == pytest.approx(expected_range, abs=0.1)

        assert ci_50_to_95_range > (0.3 * pert_forecast_days)

    def test_confidence_intervals_with_low_variance(self):
        pert_forecast_days = 100
        velocity_mean = 15
        velocity_std = 2
        remaining_work = 75

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        ci_50_to_95_range = result["ci_95"] - result["ci_50"]

        assert ci_50_to_95_range < (0.25 * pert_forecast_days)

    def test_confidence_intervals_never_negative(self):
        pert_forecast_days = 10
        velocity_mean = 2
        velocity_std = 5
        remaining_work = 5

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] >= 0
        assert result["ci_80"] >= 0
        assert result["ci_95"] >= 0

    def test_confidence_intervals_percentile_ordering(self):
        test_scenarios = [
            (50, 10, 2, 30),
            (80, 8, 3, 50),
            (120, 5, 4, 60),
        ]

        for pert_days, vel_mean, vel_std, work in test_scenarios:
            result = _calculate_confidence_intervals(pert_days, vel_mean, vel_std, work)

            assert result["ci_50"] <= result["ci_80"], (
                f"50th percentile ({result['ci_50']}) should be <= "
                f"80th ({result['ci_80']})"
            )
            assert result["ci_80"] <= result["ci_95"], (
                f"80th percentile ({result['ci_80']}) should be <= "
                f"95th ({result['ci_95']})"
            )

    def test_confidence_intervals_mathematical_formula(self):
        pert_forecast_days = 75
        velocity_mean = 12
        velocity_std = 4
        remaining_work = 60

        cv = velocity_std / velocity_mean
        forecast_std = cv * pert_forecast_days

        expected_ci_50 = pert_forecast_days
        expected_ci_80 = pert_forecast_days + (0.84 * forecast_std)
        expected_ci_95 = pert_forecast_days + (1.65 * forecast_std)

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert result["ci_50"] == pytest.approx(expected_ci_50, abs=0.01)
        assert result["ci_80"] == pytest.approx(expected_ci_80, abs=0.01)
        assert result["ci_95"] == pytest.approx(expected_ci_95, abs=0.01)

    def test_confidence_intervals_realistic_scenario(self):
        pert_forecast_days = 50
        velocity_mean = 10
        velocity_std = 3
        remaining_work = 30

        result = _calculate_confidence_intervals(
            pert_forecast_days, velocity_mean, velocity_std, remaining_work
        )

        assert 40 < result["ci_50"] < 60, "50th percentile should be near forecast"
        assert 50 < result["ci_80"] < 80, "80th percentile should add buffer"
        assert 60 < result["ci_95"] < 100, "95th percentile should be conservative"

        buffer_80 = result["ci_80"] - result["ci_50"]
        buffer_95 = result["ci_95"] - result["ci_50"]

        ratio = buffer_95 / buffer_80 if buffer_80 > 0 else 0
        assert 1.8 < ratio < 2.2, "Buffer ratio should be approximately 2:1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
