"""Unit tests for velocity projections module."""

import pytest
from datetime import datetime, timedelta
from data.velocity_projections import (
    calculate_required_velocity,
    calculate_velocity_gap,
    assess_pace_health,
    get_pace_health_indicator,
    calculate_completion_projection,
)


class TestCalculateRequiredVelocity:
    """Tests for calculate_required_velocity function."""

    def test_basic_calculation_weeks(self):
        """Test basic required velocity calculation in weeks."""
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)  # 28 days = 4 weeks
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == pytest.approx(12.5, rel=0.01)  # 50 / 4 = 12.5

    def test_basic_calculation_days(self):
        """Test basic required velocity calculation in days."""
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 2, 11)  # 10 days
        remaining_work = 20.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="day"
        )

        assert required == pytest.approx(2.0, rel=0.01)  # 20 / 10 = 2.0

    def test_deadline_passed(self):
        """Test when deadline has already passed."""
        current_date = datetime(2026, 2, 10)
        deadline = datetime(2026, 2, 5)  # 5 days ago
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == float("inf")

    def test_deadline_today(self):
        """Test when deadline is today."""
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 2, 1)  # Same day
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == float("inf")

    def test_default_current_date(self):
        """Test with default current_date (now)."""
        deadline = datetime.now() + timedelta(days=14)
        remaining_work = 28.0

        required = calculate_required_velocity(
            remaining_work, deadline, time_unit="week"
        )

        # Current implementation uses integer day difference
        assert 15.0 <= required <= 16.0

    def test_invalid_time_unit(self):
        """Test with invalid time unit."""
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)
        remaining_work = 50.0

        with pytest.raises(ValueError, match="Invalid time_unit"):
            calculate_required_velocity(
                remaining_work, deadline, current_date, time_unit="month"
            )

    def test_zero_remaining_work(self):
        """Test with zero remaining work."""
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)
        remaining_work = 0.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == 0.0


class TestCalculateVelocityGap:
    """Tests for calculate_velocity_gap function."""

    def test_behind_pace(self):
        """Test when current velocity is behind required."""
        current = 10.0
        required = 12.5

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == pytest.approx(2.5, rel=0.01)
        assert gap_data["percent"] == pytest.approx(20.0, rel=0.01)
        assert gap_data["ratio"] == pytest.approx(0.8, rel=0.01)

    def test_ahead_of_pace(self):
        """Test when current velocity is ahead of required."""
        current = 15.0
        required = 12.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == pytest.approx(-3.0, rel=0.01)
        assert gap_data["percent"] == pytest.approx(-25.0, rel=0.01)
        assert gap_data["ratio"] == pytest.approx(1.25, rel=0.01)

    def test_exactly_on_pace(self):
        """Test when current velocity exactly matches required."""
        current = 10.0
        required = 10.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == 0.0
        assert gap_data["percent"] == 0.0
        assert gap_data["ratio"] == 1.0

    def test_zero_required_velocity(self):
        """Test edge case with zero required velocity."""
        current = 10.0
        required = 0.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == 0.0
        assert gap_data["percent"] == 0.0
        assert gap_data["ratio"] == 1.0


class TestAssessPaceHealth:
    """Tests for assess_pace_health function."""

    def test_healthy_status(self):
        """Test healthy status (>=100% of required)."""
        current = 15.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "on_pace"
        assert health["indicator"] == "✓"
        assert health["color"] == "#28a745"
        assert "ahead" in health["message"].lower()
        assert health["ratio"] == pytest.approx(1.25, rel=0.01)

    def test_healthy_exactly_on_pace(self):
        """Test healthy status when exactly on pace."""
        current = 10.0
        required = 10.0

        health = assess_pace_health(current, required)

        assert health["status"] == "on_pace"
        assert health["indicator"] == "✓"
        assert health["ratio"] == 1.0

    def test_at_risk_status(self):
        """Test at risk status (80-99% of required)."""
        current = 10.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "at_risk"
        assert health["indicator"] == "○"
        assert health["color"] == "#ffc107"
        assert "slightly below" in health["message"].lower()
        assert health["ratio"] == pytest.approx(0.833, rel=0.01)

    def test_behind_status(self):
        """Test behind status (<80% of required)."""
        current = 8.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "behind_pace"
        assert health["indicator"] == "❄"
        assert health["color"] == "#dc3545"
        assert "significantly behind" in health["message"].lower()
        assert health["ratio"] == pytest.approx(0.667, rel=0.01)

    def test_zero_required_velocity(self):
        """Test with zero required velocity."""
        current = 10.0
        required = 0.0

        health = assess_pace_health(current, required)

        assert health["status"] == "unknown"
        assert health["indicator"] == "○"
        assert health["ratio"] == 0.0

    def test_deadline_passed(self):
        """Test with infinity required velocity (deadline passed)."""
        current = 10.0
        required = float("inf")

        health = assess_pace_health(current, required)

        assert health["status"] == "deadline_passed"
        assert health["indicator"] == "❄"
        assert health["color"] == "#dc3545"


class TestGetPaceHealthIndicator:
    """Tests for get_pace_health_indicator function."""

    def test_healthy_indicator(self):
        """Test healthy indicator."""
        assert get_pace_health_indicator(1.0) == "✓"
        assert get_pace_health_indicator(1.5) == "✓"
        assert get_pace_health_indicator(2.0) == "✓"

    def test_at_risk_indicator(self):
        """Test at risk indicator."""
        assert get_pace_health_indicator(0.8) == "○"
        assert get_pace_health_indicator(0.9) == "○"
        assert get_pace_health_indicator(0.99) == "○"

    def test_behind_indicator(self):
        """Test behind indicator."""
        assert get_pace_health_indicator(0.79) == "❄"
        assert get_pace_health_indicator(0.5) == "❄"
        assert get_pace_health_indicator(0.1) == "❄"


class TestCalculateCompletionProjection:
    """Tests for calculate_completion_projection function."""

    def test_basic_projection(self):
        """Test basic completion projection."""
        current_date = datetime(2026, 2, 1)
        remaining_work = 50.0
        current_velocity = 10.0  # 10 items/week

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="week"
        )

        # 50 / 10 = 5 weeks = 35 days
        assert projection["periods_remaining"] == 5.0
        assert projection["days_from_now"] == 35
        assert projection["projected_date"] == datetime(2026, 3, 8)

    def test_zero_velocity(self):
        """Test with zero current velocity."""
        current_date = datetime(2026, 2, 1)
        remaining_work = 50.0
        current_velocity = 0.0

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="week"
        )

        assert projection["projected_date"] is None
        assert projection["days_from_now"] is None
        assert projection["periods_remaining"] is None

    def test_negative_velocity(self):
        """Test with negative current velocity."""
        current_date = datetime(2026, 2, 1)
        remaining_work = 50.0
        current_velocity = -5.0

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="week"
        )

        assert projection["projected_date"] is None

    def test_projection_with_days(self):
        """Test projection using days as time unit."""
        current_date = datetime(2026, 2, 1)
        remaining_work = 20.0
        current_velocity = 2.0  # 2 items/day

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="day"
        )

        # 20 / 2 = 10 days
        assert projection["periods_remaining"] == 10.0
        assert projection["days_from_now"] == 10
        assert projection["projected_date"] == datetime(2026, 2, 11)
