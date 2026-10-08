from datetime import datetime

import pytest

from data.processing import calculate_dashboard_metrics, calculate_pert_timeline


class TestCalculateDashboardMetrics:
    def test_normal_data(self, sample_statistics_data, sample_settings):

        metrics = calculate_dashboard_metrics(sample_statistics_data, sample_settings)

        assert "completion_forecast_date" in metrics
        assert "completion_confidence" in metrics
        assert "days_to_completion" in metrics
        assert "days_to_deadline" in metrics
        assert "completion_percentage" in metrics
        assert "remaining_items" in metrics
        assert "remaining_points" in metrics
        assert "current_velocity_items" in metrics
        assert "current_velocity_points" in metrics
        assert "velocity_trend" in metrics
        assert "last_updated" in metrics

        assert metrics["current_velocity_items"] > 0
        assert metrics["current_velocity_points"] > 0
        assert metrics["completion_percentage"] >= 0
        assert metrics["remaining_items"] >= 0
        assert metrics["remaining_points"] >= 0

    def test_completion_percentage_calculation(
        self, sample_statistics_data, sample_settings
    ):

        settings = sample_settings.copy()
        settings["estimated_total_items"] = 100

        stats = [
            {"date": "2025-01-01", "completed_items": 68, "completed_points": 340.0}
        ]

        metrics = calculate_dashboard_metrics(stats, settings)

        assert metrics["completion_percentage"] == pytest.approx(68.0, rel=0.01)

    def test_velocity_calculation(self, sample_statistics_data, sample_settings):

        metrics = calculate_dashboard_metrics(sample_statistics_data, sample_settings)

        assert metrics["current_velocity_items"] > 0
        assert metrics["current_velocity_points"] > 0

        assert metrics["current_velocity_items"] < 100
        assert metrics["current_velocity_points"] < 500

    def test_forecast_date_calculation(self, sample_statistics_data, sample_settings):

        metrics = calculate_dashboard_metrics(sample_statistics_data, sample_settings)

        assert metrics["completion_forecast_date"] is not None

        forecast_date = datetime.fromisoformat(metrics["completion_forecast_date"])
        assert isinstance(forecast_date, datetime)

        last_data_date = datetime.fromisoformat(sample_statistics_data[-1]["date"])
        assert forecast_date >= last_data_date

    def test_empty_statistics(self, empty_statistics_data, sample_settings):

        metrics = calculate_dashboard_metrics(empty_statistics_data, sample_settings)

        assert metrics["completion_forecast_date"] is None
        assert (
            metrics["completion_confidence"] is None
            or metrics["completion_confidence"] == 0
        )
        assert metrics["days_to_completion"] is None
        assert metrics["current_velocity_items"] == 0
        assert metrics["current_velocity_points"] == 0
        assert metrics["completion_percentage"] >= 0
        assert metrics["velocity_trend"] in ["unknown", "stable", ""]

    def test_single_data_point(self, minimal_statistics_data, sample_settings):

        metrics = calculate_dashboard_metrics(minimal_statistics_data, sample_settings)

        assert metrics is not None
        assert "velocity_trend" in metrics
        assert metrics["velocity_trend"] in [
            "unknown",
            "stable",
            "increasing",
            "decreasing",
        ]

    def test_zero_velocity(self, zero_velocity_data, sample_settings):

        metrics = calculate_dashboard_metrics(zero_velocity_data, sample_settings)

        assert (
            metrics["completion_forecast_date"] is None
            or metrics["days_to_completion"] is None
        )
        assert metrics["current_velocity_items"] == 0
        assert metrics["current_velocity_points"] == 0

    def test_no_deadline(self, sample_statistics_data, no_deadline_settings):

        metrics = calculate_dashboard_metrics(
            sample_statistics_data, no_deadline_settings
        )

        assert metrics["days_to_deadline"] is None

    def test_completion_exceeds_100(self, completion_exceeds_100_data):

        statistics, settings = completion_exceeds_100_data
        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["completion_percentage"] >= 100.0

    def test_negative_days_to_deadline(
        self, sample_statistics_data, past_deadline_settings
    ):

        metrics = calculate_dashboard_metrics(
            sample_statistics_data, past_deadline_settings
        )

        if metrics["days_to_deadline"] is not None:
            assert metrics["days_to_deadline"] < 0

    def test_velocity_trend_increasing(self, increasing_velocity_data, sample_settings):

        metrics = calculate_dashboard_metrics(increasing_velocity_data, sample_settings)

        assert metrics["velocity_trend"] in ["increasing", "stable"]

    def test_velocity_trend_stable(self, stable_velocity_data, sample_settings):

        metrics = calculate_dashboard_metrics(stable_velocity_data, sample_settings)

        assert metrics["velocity_trend"] in ["stable", "unknown"]


class TestCalculatePertTimeline:
    def test_normal_data(self, sample_statistics_data, sample_settings):

        pert_timeline = calculate_pert_timeline(sample_statistics_data, sample_settings)

        assert "optimistic_date" in pert_timeline
        assert "pessimistic_date" in pert_timeline
        assert "most_likely_date" in pert_timeline
        assert "pert_estimate_date" in pert_timeline
        assert "optimistic_days" in pert_timeline
        assert "pessimistic_days" in pert_timeline
        assert "most_likely_days" in pert_timeline
        assert "confidence_range_days" in pert_timeline

    def test_pert_formula(self, sample_statistics_data, sample_settings):

        pert_timeline = calculate_pert_timeline(sample_statistics_data, sample_settings)

        if (
            pert_timeline["optimistic_days"] is not None
            and pert_timeline["most_likely_days"] is not None
            and pert_timeline["pessimistic_days"] is not None
        ):
            if pert_timeline["pert_estimate_date"] is not None:
                pert_date = datetime.fromisoformat(pert_timeline["pert_estimate_date"])
                opt_date = datetime.fromisoformat(pert_timeline["optimistic_date"])
                pess_date = datetime.fromisoformat(pert_timeline["pessimistic_date"])

                assert opt_date <= pert_date <= pess_date

    def test_confidence_range_calculation(
        self, sample_statistics_data, sample_settings
    ):
        pert_timeline = calculate_pert_timeline(sample_statistics_data, sample_settings)

        if (
            pert_timeline["optimistic_days"] is not None
            and pert_timeline["pessimistic_days"] is not None
        ):
            expected_range = (
                pert_timeline["pessimistic_days"] - pert_timeline["optimistic_days"]
            )

            if pert_timeline["confidence_range_days"] is not None:
                assert pert_timeline["confidence_range_days"] == pytest.approx(
                    expected_range, abs=1
                )

    def test_empty_statistics(self, empty_statistics_data, sample_settings):

        pert_timeline = calculate_pert_timeline(empty_statistics_data, sample_settings)

        assert (
            pert_timeline["optimistic_date"] is None
            or pert_timeline["optimistic_days"] == 0
        )
        assert (
            pert_timeline["pessimistic_date"] is None
            or pert_timeline["pessimistic_days"] == 0
        )

    def test_zero_velocity(self, zero_velocity_data, sample_settings):

        pert_timeline = calculate_pert_timeline(zero_velocity_data, sample_settings)

        assert (
            pert_timeline["optimistic_date"] is None
            or pert_timeline["pessimistic_date"] is None
        )

    def test_zero_remaining_work(self, completion_exceeds_100_data):

        statistics, settings = completion_exceeds_100_data
        pert_timeline = calculate_pert_timeline(statistics, settings)

        assert pert_timeline is not None

    def test_extreme_pert_factor(
        self, sample_statistics_data, extreme_pert_factor_settings
    ):

        pert_timeline = calculate_pert_timeline(
            sample_statistics_data, extreme_pert_factor_settings
        )

        assert pert_timeline is not None

        if (
            pert_timeline["optimistic_days"] is not None
            and pert_timeline["pessimistic_days"] is not None
        ):
            assert pert_timeline["pessimistic_days"] > pert_timeline["optimistic_days"]

    def test_date_ordering(self, sample_statistics_data, sample_settings):

        pert_timeline = calculate_pert_timeline(sample_statistics_data, sample_settings)

        if (
            pert_timeline["optimistic_date"]
            and pert_timeline["most_likely_date"]
            and pert_timeline["pessimistic_date"]
        ):
            opt_date = datetime.fromisoformat(pert_timeline["optimistic_date"])
            likely_date = datetime.fromisoformat(pert_timeline["most_likely_date"])
            pess_date = datetime.fromisoformat(pert_timeline["pessimistic_date"])

            assert opt_date <= likely_date <= pess_date
