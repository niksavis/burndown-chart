from datetime import datetime, timedelta

from data.processing import calculate_dashboard_metrics


class TestDashboardMetricsVelocityFix:
    def test_velocity_with_continuous_weekly_data(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-13", "completed_items": 12, "completed_points": 60},
            {"date": "2025-01-20", "completed_items": 11, "completed_points": 55},
            {"date": "2025-01-27", "completed_items": 9, "completed_points": 45},
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 10.5
        assert metrics["current_velocity_points"] == 52.5

    def test_velocity_with_sparse_data_gaps(self):

        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {
                "date": "2025-03-10",
                "completed_items": 10,
                "completed_points": 50,
            },
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 10.0
        assert metrics["current_velocity_points"] == 50.0

    def test_velocity_trend_with_sparse_data(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 8, "completed_points": 40},
            {"date": "2025-01-13", "completed_items": 9, "completed_points": 45},
            {"date": "2025-01-20", "completed_items": 8, "completed_points": 40},
            {"date": "2025-02-24", "completed_items": 12, "completed_points": 60},
            {"date": "2025-03-03", "completed_items": 13, "completed_points": 65},
            {"date": "2025-03-10", "completed_items": 14, "completed_points": 70},
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["velocity_trend"] == "increasing"

    def test_velocity_trend_stable(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-13", "completed_items": 11, "completed_points": 55},
            {"date": "2025-01-20", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-27", "completed_items": 9, "completed_points": 45},
            {"date": "2025-02-03", "completed_items": 11, "completed_points": 55},
            {"date": "2025-02-10", "completed_items": 10, "completed_points": 50},
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["velocity_trend"] == "stable"

    def test_velocity_trend_decreasing(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 15, "completed_points": 75},
            {"date": "2025-01-13", "completed_items": 14, "completed_points": 70},
            {"date": "2025-01-20", "completed_items": 13, "completed_points": 65},
            {"date": "2025-01-27", "completed_items": 9, "completed_points": 45},
            {"date": "2025-02-03", "completed_items": 8, "completed_points": 40},
            {"date": "2025-02-10", "completed_items": 7, "completed_points": 35},
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["velocity_trend"] == "decreasing"

    def test_completion_forecast_uses_correct_velocity(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {
                "date": "2025-03-10",
                "completed_items": 10,
                "completed_points": 50,
            },
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["remaining_items"] == 80
        assert metrics["current_velocity_items"] == 10.0
        assert metrics["days_to_completion"] == 84

    def test_insufficient_data_for_trend(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-13", "completed_items": 12, "completed_points": 60},
            {"date": "2025-01-20", "completed_items": 11, "completed_points": 55},
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["velocity_trend"] == "unknown"


class TestDashboardMetricsVelocityEdgeCases:
    def test_single_data_point(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 15, "completed_points": 75}
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 15.0
        assert metrics["current_velocity_points"] == 75.0

    def test_empty_statistics(self):
        statistics = []
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 0.0
        assert metrics["current_velocity_points"] == 0.0
        assert metrics["velocity_trend"] == "unknown"
        assert metrics["completion_forecast_date"] is None

    def test_zero_velocity(self):
        statistics = [
            {"date": "2025-01-06", "completed_items": 0, "completed_points": 0},
            {"date": "2025-01-13", "completed_items": 0, "completed_points": 0},
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 0.0
        assert metrics["current_velocity_points"] == 0.0
        assert metrics["completion_forecast_date"] is None


class TestDashboardMetricsBackwardCompatibility:
    def test_daily_data_rollup(self):

        statistics = [
            {"date": f"2025-01-0{i}", "completed_items": 2, "completed_points": 10}
            for i in range(1, 8)
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 7.0

    def test_respects_data_points_count_setting(self):
        statistics = [
            {
                "date": (datetime(2025, 1, 6) + timedelta(weeks=i)).strftime(
                    "%Y-%m-%d"
                ),
                "completed_items": 10 if i >= 10 else 5,
                "completed_points": 50 if i >= 10 else 25,
            }
            for i in range(15)
        ]
        settings = {
            "estimated_total_items": 200,
            "estimated_total_points": 1000,
            "data_points_count": 5,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 10.0
