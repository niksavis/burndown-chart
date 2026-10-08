from datetime import datetime, timedelta

import pytest

import data.velocity_projections as velocity_projections
from data.velocity_projections import (
    assess_pace_health,
    calculate_completion_projection,
    calculate_required_velocity,
    calculate_velocity_gap,
    get_pace_health_indicator,
)


class TestCalculateRequiredVelocity:
    def test_basic_calculation_weeks(self):
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == pytest.approx(12.5, rel=0.01)

    def test_basic_calculation_days(self):
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 2, 11)
        remaining_work = 20.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="day"
        )

        assert required == pytest.approx(2.0, rel=0.01)

    def test_deadline_passed(self):
        current_date = datetime(2026, 2, 10)
        deadline = datetime(2026, 2, 5)
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == float("inf")

    def test_deadline_today(self):
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 2, 1)
        remaining_work = 50.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == float("inf")

    def test_default_current_date(self, monkeypatch):
        fixed_now = datetime(2026, 2, 1, 12, 0, 0)

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is not None:
                    return fixed_now.replace(tzinfo=tz)
                return fixed_now

        monkeypatch.setattr(velocity_projections, "datetime", FixedDateTime)

        deadline = fixed_now + timedelta(days=14)
        remaining_work = 28.0

        required = calculate_required_velocity(
            remaining_work, deadline, time_unit="week"
        )

        assert required == pytest.approx(14.0, rel=0.01)

    def test_invalid_time_unit(self):
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)
        remaining_work = 50.0

        with pytest.raises(ValueError, match="Invalid time_unit"):
            calculate_required_velocity(
                remaining_work, deadline, current_date, time_unit="month"
            )

    def test_zero_remaining_work(self):
        current_date = datetime(2026, 2, 1)
        deadline = datetime(2026, 3, 1)
        remaining_work = 0.0

        required = calculate_required_velocity(
            remaining_work, deadline, current_date, time_unit="week"
        )

        assert required == 0.0


class TestCalculateVelocityGap:
    def test_behind_pace(self):
        current = 10.0
        required = 12.5

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == pytest.approx(2.5, rel=0.01)
        assert gap_data["percent"] == pytest.approx(20.0, rel=0.01)
        assert gap_data["ratio"] == pytest.approx(0.8, rel=0.01)

    def test_ahead_of_pace(self):
        current = 15.0
        required = 12.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == pytest.approx(-3.0, rel=0.01)
        assert gap_data["percent"] == pytest.approx(-25.0, rel=0.01)
        assert gap_data["ratio"] == pytest.approx(1.25, rel=0.01)

    def test_exactly_on_pace(self):
        current = 10.0
        required = 10.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == 0.0
        assert gap_data["percent"] == 0.0
        assert gap_data["ratio"] == 1.0

    def test_zero_required_velocity(self):
        current = 10.0
        required = 0.0

        gap_data = calculate_velocity_gap(current, required)

        assert gap_data["gap"] == 0.0
        assert gap_data["percent"] == 0.0
        assert gap_data["ratio"] == 1.0


class TestAssessPaceHealth:
    def test_healthy_status(self):
        current = 15.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "on_pace"
        assert health["indicator"] == "✓"
        assert health["color"] == "#28a745"
        assert "ahead" in health["message"].lower()
        assert health["ratio"] == pytest.approx(1.25, rel=0.01)

    def test_healthy_exactly_on_pace(self):
        current = 10.0
        required = 10.0

        health = assess_pace_health(current, required)

        assert health["status"] == "on_pace"
        assert health["indicator"] == "✓"
        assert health["ratio"] == 1.0

    def test_at_risk_status(self):
        current = 10.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "at_risk"
        assert health["indicator"] == "○"
        assert health["color"] == "#ffc107"
        assert "slightly below" in health["message"].lower()
        assert health["ratio"] == pytest.approx(0.833, rel=0.01)

    def test_behind_status(self):
        current = 8.0
        required = 12.0

        health = assess_pace_health(current, required)

        assert health["status"] == "behind_pace"
        assert health["indicator"] == "❄"
        assert health["color"] == "#dc3545"
        assert "significantly behind" in health["message"].lower()
        assert health["ratio"] == pytest.approx(0.667, rel=0.01)

    def test_zero_required_velocity(self):
        current = 10.0
        required = 0.0

        health = assess_pace_health(current, required)

        assert health["status"] == "unknown"
        assert health["indicator"] == "○"
        assert health["ratio"] == 0.0

    def test_deadline_passed(self):
        current = 10.0
        required = float("inf")

        health = assess_pace_health(current, required)

        assert health["status"] == "deadline_passed"
        assert health["indicator"] == "❄"
        assert health["color"] == "#dc3545"


class TestGetPaceHealthIndicator:
    def test_healthy_indicator(self):
        assert get_pace_health_indicator(1.0) == "✓"
        assert get_pace_health_indicator(1.5) == "✓"
        assert get_pace_health_indicator(2.0) == "✓"

    def test_at_risk_indicator(self):
        assert get_pace_health_indicator(0.8) == "○"
        assert get_pace_health_indicator(0.9) == "○"
        assert get_pace_health_indicator(0.99) == "○"

    def test_behind_indicator(self):
        assert get_pace_health_indicator(0.79) == "❄"
        assert get_pace_health_indicator(0.5) == "❄"
        assert get_pace_health_indicator(0.1) == "❄"


class TestCalculateCompletionProjection:
    def test_basic_projection(self):
        current_date = datetime(2026, 2, 1)
        remaining_work = 50.0
        current_velocity = 10.0

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="week"
        )

        assert projection["periods_remaining"] == 5.0
        assert projection["days_from_now"] == 35
        assert projection["projected_date"] == datetime(2026, 3, 8)

    def test_zero_velocity(self):
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
        current_date = datetime(2026, 2, 1)
        remaining_work = 50.0
        current_velocity = -5.0

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="week"
        )

        assert projection["projected_date"] is None

    def test_projection_with_days(self):
        current_date = datetime(2026, 2, 1)
        remaining_work = 20.0
        current_velocity = 2.0

        projection = calculate_completion_projection(
            remaining_work, current_velocity, current_date, time_unit="day"
        )

        assert projection["periods_remaining"] == 10.0
        assert projection["days_from_now"] == 10
        assert projection["projected_date"] == datetime(2026, 2, 11)
