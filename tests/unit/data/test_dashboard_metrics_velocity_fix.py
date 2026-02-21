"""Tests for dashboard metrics velocity calculation fix.

This test suite validates that calculate_dashboard_metrics now uses the corrected
velocity calculation method that counts actual weeks instead of date range.
"""

from datetime import datetime, timedelta

from data.processing import calculate_dashboard_metrics


class TestDashboardMetricsVelocityFix:
    """Test that dashboard metrics use corrected velocity calculation."""

    def test_velocity_with_continuous_weekly_data(self):
        """Test velocity calculation with continuous weekly data."""
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

        # 42 items / 4 weeks = 10.5 items/week
        assert metrics["current_velocity_items"] == 10.5
        # 210 points / 4 weeks = 52.5 points/week
        assert metrics["current_velocity_points"] == 52.5

    def test_velocity_with_sparse_data_gaps(self):
        """Test velocity calculation with sparse data (critical bug fix test).

        This test validates the fix for the original bug where velocity was
        deflated when data had gaps.
        """
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {
                "date": "2025-03-10",
                "completed_items": 10,
                "completed_points": 50,
            },  # 9 weeks later
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        # Should be 20 items / 2 weeks = 10.0 items/week (CORRECT)
        # OLD BUG: Would calculate 20 items / 9 weeks = 2.2 items/week
        assert metrics["current_velocity_items"] == 10.0
        assert metrics["current_velocity_points"] == 50.0

    def test_velocity_trend_with_sparse_data(self):
        """Test velocity trend calculation with sparse data."""
        # 6 data points with gaps: older half has weeks 1,2,3;
        # recent half has weeks 8,9,10.
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

        # Older half: 25 items / 3 weeks = 8.3 items/week
        # Recent half: 39 items / 3 weeks = 13.0 items/week
        # Change: (13.0 - 8.3) / 8.3 = 56.6% increase (> 10% threshold)
        assert metrics["velocity_trend"] == "increasing"

    def test_velocity_trend_stable(self):
        """Test velocity trend detection for stable velocity."""
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

        # Older half: 31 items / 3 weeks = 10.3 items/week
        # Recent half: 30 items / 3 weeks = 10.0 items/week
        # Change: (10.0 - 10.3) / 10.3 = -2.9% (< 10% threshold)
        assert metrics["velocity_trend"] == "stable"

    def test_velocity_trend_decreasing(self):
        """Test velocity trend detection for decreasing velocity."""
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

        # Older half: 42 items / 3 weeks = 14.0 items/week
        # Recent half: 24 items / 3 weeks = 8.0 items/week
        # Change: (8.0 - 14.0) / 14.0 = -42.9% (< -10% threshold)
        assert metrics["velocity_trend"] == "decreasing"

    def test_completion_forecast_uses_correct_velocity(self):
        """Test that completion forecast uses the corrected velocity."""
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {
                "date": "2025-03-10",
                "completed_items": 10,
                "completed_points": 50,
            },  # Sparse data
        ]
        settings = {
            "estimated_total_items": 100,
            "estimated_total_points": 500,
            "pert_factor": 1.5,
            "data_points_count": 10,
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        # Completed: 20 items, Remaining: 80 items
        # Velocity: 10.0 items/week (CORRECT)
        # Weeks remaining: 80 / 10.0 = 8 weeks
        # With PERT factor 1.5: 8 * 1.5 = 12 weeks = 84 days

        assert metrics["remaining_items"] == 80
        assert metrics["current_velocity_items"] == 10.0
        assert metrics["days_to_completion"] == 84

        # OLD BUG: Would calculate velocity as 2.2 items/week
        # Would forecast: 80 / 2.2 * 1.5 = 54.5 weeks = 381 days (WRONG!)

    def test_insufficient_data_for_trend(self):
        """Test that trend requires at least 6 data points."""
        statistics = [
            {"date": "2025-01-06", "completed_items": 10, "completed_points": 50},
            {"date": "2025-01-13", "completed_items": 12, "completed_points": 60},
            {"date": "2025-01-20", "completed_items": 11, "completed_points": 55},
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        # With < 6 data points, trend should be "unknown"
        assert metrics["velocity_trend"] == "unknown"


class TestDashboardMetricsVelocityEdgeCases:
    """Test edge cases for velocity calculation in dashboard metrics."""

    def test_single_data_point(self):
        """Test velocity calculation with single data point."""
        statistics = [
            {"date": "2025-01-06", "completed_items": 15, "completed_points": 75}
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        # Should calculate velocity as 15 items / 1 week
        assert metrics["current_velocity_items"] == 15.0
        assert metrics["current_velocity_points"] == 75.0

    def test_empty_statistics(self):
        """Test that empty statistics returns default metrics."""
        statistics = []
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 0.0
        assert metrics["current_velocity_points"] == 0.0
        assert metrics["velocity_trend"] == "unknown"
        assert metrics["completion_forecast_date"] is None

    def test_zero_velocity(self):
        """Test handling of zero velocity (no work completed)."""
        statistics = [
            {"date": "2025-01-06", "completed_items": 0, "completed_points": 0},
            {"date": "2025-01-13", "completed_items": 0, "completed_points": 0},
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        assert metrics["current_velocity_items"] == 0.0
        assert metrics["current_velocity_points"] == 0.0
        # With zero velocity, cannot forecast completion
        assert metrics["completion_forecast_date"] is None


class TestDashboardMetricsBackwardCompatibility:
    """Test that fix doesn't break existing behavior for continuous data."""

    def test_daily_data_rollup(self):
        """Test velocity with daily data points within same week.

        Note: Multiple entries in the same week are counted as one week,
        so total items are divided by 1 week (not number of days).
        """
        # 7 daily data points (all within Week 1 of 2025)
        statistics = [
            {"date": f"2025-01-0{i}", "completed_items": 2, "completed_points": 10}
            for i in range(1, 8)
        ]
        settings = {"estimated_total_items": 100, "estimated_total_points": 500}

        metrics = calculate_dashboard_metrics(statistics, settings)

        # All 7 days are in the same ISO week (Week 1)
        # 14 items / 1 unique week = 14.0 items/week... BUT
        # Jan 1-5 are Week 53 of 2024, Jan 6-12 are Week 1 of 2025
        # So we actually have 2 distinct weeks in the data
        # 14 items / 2 weeks = 7.0 items/week
        assert metrics["current_velocity_items"] == 7.0

    def test_respects_data_points_count_setting(self):
        """Test that data_points_count setting limits velocity window."""
        # 15 weeks of data, but only last 5 should be used
        statistics = [
            {
                "date": (datetime(2025, 1, 6) + timedelta(weeks=i)).strftime(
                    "%Y-%m-%d"
                ),
                "completed_items": 10 if i >= 10 else 5,  # Recent weeks higher
                "completed_points": 50 if i >= 10 else 25,
            }
            for i in range(15)
        ]
        settings = {
            "estimated_total_items": 200,
            "estimated_total_points": 1000,
            "data_points_count": 5,  # Only use last 5 data points
        }

        metrics = calculate_dashboard_metrics(statistics, settings)

        # Last 5 weeks: 50 items / 5 weeks = 10.0 items/week
        assert metrics["current_velocity_items"] == 10.0
        # Not: 125 items / 15 weeks = 8.3 items/week
