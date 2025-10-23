"""
Unit tests for bug resolution forecasting.

Tests the forecasting engine that predicts when open bugs will be resolved
based on historical closure rates.
"""

from datetime import datetime
from data.bug_processing import forecast_bug_resolution


class TestBugResolutionForecasting:
    """Test suite for bug resolution forecasting."""

    def test_forecast_normal_closure_rate(self):
        """Test forecast with normal closure rate."""
        # 10 open bugs, average 5 bugs/week closure rate
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 4},
            {"week_start": "2025-01-22", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-29", "bugs_created": 2, "bugs_resolved": 6},
            {"week_start": "2025-02-05", "bugs_created": 3, "bugs_resolved": 4},
            {"week_start": "2025-02-12", "bugs_created": 2, "bugs_resolved": 5},
            {"week_start": "2025-02-19", "bugs_created": 4, "bugs_resolved": 5},
        ]

        forecast = forecast_bug_resolution(open_bugs=10, weekly_stats=weekly_stats)

        # Should have forecast data
        assert "optimistic_weeks" in forecast
        assert "most_likely_weeks" in forecast
        assert "pessimistic_weeks" in forecast
        assert "optimistic_date" in forecast
        assert "most_likely_date" in forecast
        assert "pessimistic_date" in forecast
        assert "insufficient_data" in forecast
        assert "avg_closure_rate" in forecast

        # Should not be insufficient data
        assert forecast["insufficient_data"] is False

        # Optimistic should be <= likely <= pessimistic
        assert (
            forecast["optimistic_weeks"]
            <= forecast["most_likely_weeks"]
            <= forecast["pessimistic_weeks"]
        )

        # With 10 bugs and ~5 bugs/week, should be around 2 weeks
        assert 1 <= forecast["most_likely_weeks"] <= 4

    def test_forecast_zero_open_bugs(self):
        """Test forecast when all bugs are resolved."""
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 6},
        ]

        forecast = forecast_bug_resolution(open_bugs=0, weekly_stats=weekly_stats)

        # Should have immediate completion
        assert forecast["optimistic_weeks"] == 0
        assert forecast["most_likely_weeks"] == 0
        assert forecast["pessimistic_weeks"] == 0
        assert forecast["insufficient_data"] is False

    def test_forecast_zero_closure_rate(self):
        """Test forecast when no bugs are being closed."""
        # All weeks have 0 resolutions
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 0},
            {"week_start": "2025-01-08", "bugs_created": 3, "bugs_resolved": 0},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 0},
            {"week_start": "2025-01-22", "bugs_created": 2, "bugs_resolved": 0},
        ]

        forecast = forecast_bug_resolution(open_bugs=20, weekly_stats=weekly_stats)

        # Should indicate insufficient data (no progress)
        assert forecast["insufficient_data"] is True
        assert forecast["avg_closure_rate"] == 0

    def test_forecast_insufficient_history(self):
        """Test forecast with less than 4 weeks history."""
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 4},
        ]

        forecast = forecast_bug_resolution(open_bugs=10, weekly_stats=weekly_stats)

        # Should indicate insufficient data
        assert forecast["insufficient_data"] is True

    def test_forecast_date_calculation(self):
        """Test that forecast dates are calculated correctly."""
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 5},
            {"week_start": "2025-01-15", "bugs_created": 4, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 3, "bugs_resolved": 5},
        ]

        forecast = forecast_bug_resolution(open_bugs=10, weekly_stats=weekly_stats)

        # Dates should be in the future
        today = datetime.now().date()
        assert datetime.fromisoformat(forecast["optimistic_date"]).date() >= today
        assert datetime.fromisoformat(forecast["most_likely_date"]).date() >= today
        assert datetime.fromisoformat(forecast["pessimistic_date"]).date() >= today

    def test_forecast_week_ordering(self):
        """Test that optimistic <= likely <= pessimistic weeks."""
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 2, "bugs_resolved": 8},
            {"week_start": "2025-01-08", "bugs_created": 3, "bugs_resolved": 6},
            {"week_start": "2025-01-15", "bugs_created": 1, "bugs_resolved": 7},
            {"week_start": "2025-01-22", "bugs_created": 2, "bugs_resolved": 5},
            {"week_start": "2025-01-29", "bugs_created": 4, "bugs_resolved": 6},
        ]

        forecast = forecast_bug_resolution(open_bugs=20, weekly_stats=weekly_stats)

        # Verify ordering
        assert forecast["optimistic_weeks"] <= forecast["most_likely_weeks"]
        assert forecast["most_likely_weeks"] <= forecast["pessimistic_weeks"]

    def test_forecast_high_variance(self):
        """Test forecast with high variance in closure rates."""
        # Highly variable closure rates: 2, 10, 3, 9, 4, 8
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 1, "bugs_resolved": 2},
            {"week_start": "2025-01-08", "bugs_created": 2, "bugs_resolved": 10},
            {"week_start": "2025-01-15", "bugs_created": 1, "bugs_resolved": 3},
            {"week_start": "2025-01-22", "bugs_created": 2, "bugs_resolved": 9},
            {"week_start": "2025-01-29", "bugs_created": 1, "bugs_resolved": 4},
            {"week_start": "2025-02-05", "bugs_created": 2, "bugs_resolved": 8},
        ]

        forecast = forecast_bug_resolution(open_bugs=15, weekly_stats=weekly_stats)

        # High variance should result in wider spread between optimistic and pessimistic
        spread = forecast["pessimistic_weeks"] - forecast["optimistic_weeks"]
        assert spread >= 2  # Significant spread due to variance

    def test_forecast_consistent_closure(self):
        """Test forecast with very consistent closure rates."""
        # Consistent closure rate of 5 bugs/week
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 2, "bugs_resolved": 5},
            {"week_start": "2025-01-08", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-15", "bugs_created": 2, "bugs_resolved": 5},
            {"week_start": "2025-01-22", "bugs_created": 3, "bugs_resolved": 5},
            {"week_start": "2025-01-29", "bugs_created": 2, "bugs_resolved": 5},
        ]

        forecast = forecast_bug_resolution(open_bugs=15, weekly_stats=weekly_stats)

        # Low variance should result in narrow spread
        spread = forecast["pessimistic_weeks"] - forecast["optimistic_weeks"]
        assert spread <= 2  # Narrow spread due to consistency

    def test_forecast_empty_weekly_stats(self):
        """Test forecast with empty weekly statistics."""
        forecast = forecast_bug_resolution(open_bugs=10, weekly_stats=[])

        # Should indicate insufficient data
        assert forecast["insufficient_data"] is True

    def test_forecast_large_bug_backlog(self):
        """Test forecast with large bug backlog."""
        weekly_stats = [
            {"week_start": "2025-01-01", "bugs_created": 5, "bugs_resolved": 3},
            {"week_start": "2025-01-08", "bugs_created": 4, "bugs_resolved": 3},
            {"week_start": "2025-01-15", "bugs_created": 6, "bugs_resolved": 2},
            {"week_start": "2025-01-22", "bugs_created": 5, "bugs_resolved": 3},
        ]

        forecast = forecast_bug_resolution(open_bugs=100, weekly_stats=weekly_stats)

        # With 100 bugs and ~2.75 bugs/week closure, should take many weeks
        assert forecast["most_likely_weeks"] >= 30
        assert forecast["insufficient_data"] is False
