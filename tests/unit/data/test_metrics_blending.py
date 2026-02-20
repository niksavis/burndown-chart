"""Unit tests for progressive current week blending algorithm.

Tests the f(forecast, actual) blending with day-of-week weights to ensure:
- Correct weight calculation for each weekday (Mon-Sun)
- Proper blending formula application
- Metadata generation for UI transparency
- Boundary conditions (zero actual, zero forecast)

Created: 2026-02-10
Related: Feature burndown-chart-a1vn
"""

from datetime import datetime

import pytest

from data.metrics.blending import (
    DAY_NAMES,
    WEEKDAY_WEIGHTS,
    calculate_current_week_blend,
    format_blend_description,
    get_blend_metadata,
    get_weekday_weight,
)


class TestWeekdayWeight:
    """Test weekday weight calculation."""

    def test_monday_weight(self):
        """Monday should return 0.0 (100% forecast)."""
        monday = datetime(2026, 2, 9, 10, 0, 0)  # Monday, Feb 9, 2026
        assert monday.weekday() == 0
        weight = get_weekday_weight(monday)
        assert weight == 0.0

    def test_tuesday_weight(self):
        """Tuesday should return 0.2 (80% forecast, 20% actual)."""
        tuesday = datetime(2026, 2, 10, 10, 0, 0)  # Tuesday, Feb 10, 2026
        assert tuesday.weekday() == 1
        weight = get_weekday_weight(tuesday)
        assert weight == 0.2

    def test_wednesday_weight(self):
        """Wednesday should return 0.4 (60% forecast, 40% actual)."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)  # Wednesday, Feb 11, 2026
        assert wednesday.weekday() == 2
        weight = get_weekday_weight(wednesday)
        assert weight == 0.4

    def test_thursday_weight(self):
        """Thursday should return 0.6 (40% forecast, 60% actual)."""
        thursday = datetime(2026, 2, 12, 10, 0, 0)  # Thursday, Feb 12, 2026
        assert thursday.weekday() == 3
        weight = get_weekday_weight(thursday)
        assert weight == 0.6

    def test_friday_weight(self):
        """Friday should return 0.8 (20% forecast, 80% actual)."""
        friday = datetime(2026, 2, 13, 10, 0, 0)  # Friday, Feb 13, 2026
        assert friday.weekday() == 4
        weight = get_weekday_weight(friday)
        assert weight == 0.8

    def test_saturday_weight(self):
        """Saturday should return 1.0 (work week complete)."""
        saturday = datetime(2026, 2, 14, 10, 0, 0)  # Saturday, Feb 14, 2026
        assert saturday.weekday() == 5
        weight = get_weekday_weight(saturday)
        assert weight == 1.0

    def test_sunday_weight(self):
        """Sunday should return 1.0 (work week complete)."""
        sunday = datetime(2026, 2, 15, 10, 0, 0)  # Sunday, Feb 15, 2026
        assert sunday.weekday() == 6
        weight = get_weekday_weight(sunday)
        assert weight == 1.0

    def test_all_weekdays_mapped(self):
        """Verify all 7 weekdays have defined weights."""
        assert len(WEEKDAY_WEIGHTS) == 7
        for day in range(7):
            assert day in WEEKDAY_WEIGHTS
            assert 0.0 <= WEEKDAY_WEIGHTS[day] <= 1.0


class TestCurrentWeekBlend:
    """Test blended value calculation."""

    def test_monday_blend_pure_forecast(self):
        """Monday: 0% actual, 100% forecast."""
        monday = datetime(2026, 2, 9, 10, 0, 0)
        actual = 0.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, monday)
        assert blended == pytest.approx(11.5, rel=0.01)

    def test_tuesday_blend_20_80(self):
        """Tuesday: 20% actual, 80% forecast."""
        tuesday = datetime(2026, 2, 10, 10, 0, 0)
        actual = 2.0
        forecast = 11.5
        # Expected: (2 × 0.2) + (11.5 × 0.8) = 0.4 + 9.2 = 9.6
        blended = calculate_current_week_blend(actual, forecast, tuesday)
        assert blended == pytest.approx(9.6, rel=0.01)

    def test_wednesday_blend_40_60(self):
        """Wednesday: 40% actual, 60% forecast."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        actual = 5.0
        forecast = 11.5
        # Expected: (5 × 0.4) + (11.5 × 0.6) = 2.0 + 6.9 = 8.9
        blended = calculate_current_week_blend(actual, forecast, wednesday)
        assert blended == pytest.approx(8.9, rel=0.01)

    def test_thursday_blend_60_40(self):
        """Thursday: 60% actual, 40% forecast."""
        thursday = datetime(2026, 2, 12, 10, 0, 0)
        actual = 8.0
        forecast = 11.5
        # Expected: (8 × 0.6) + (11.5 × 0.4) = 4.8 + 4.6 = 9.4
        blended = calculate_current_week_blend(actual, forecast, thursday)
        assert blended == pytest.approx(9.4, rel=0.01)

    def test_friday_blend_80_20(self):
        """Friday: 80% actual, 20% forecast."""
        friday = datetime(2026, 2, 13, 10, 0, 0)
        actual = 10.0
        forecast = 11.5
        # Expected: (10 × 0.8) + (11.5 × 0.2) = 8.0 + 2.3 = 10.3
        blended = calculate_current_week_blend(actual, forecast, friday)
        assert blended == pytest.approx(10.3, rel=0.01)

    def test_saturday_blend_pure_actual(self):
        """Saturday: 100% actual (work week complete)."""
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        actual = 12.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, saturday)
        assert blended == pytest.approx(12.0, rel=0.01)

    def test_sunday_blend_pure_actual(self):
        """Sunday: 100% actual (work week complete)."""
        sunday = datetime(2026, 2, 15, 10, 0, 0)
        actual = 12.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, sunday)
        assert blended == pytest.approx(12.0, rel=0.01)


class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_zero_actual_monday(self):
        """Zero actual on Monday should return pure forecast."""
        monday = datetime(2026, 2, 9, 10, 0, 0)
        blended = calculate_current_week_blend(0.0, 11.5, monday)
        assert blended == pytest.approx(11.5, rel=0.01)

    def test_zero_forecast_friday(self):
        """Zero forecast on Friday should still blend (80% actual, 20% forecast)."""
        friday = datetime(2026, 2, 13, 10, 0, 0)
        blended = calculate_current_week_blend(10.0, 0.0, friday)
        # Expected: (10 × 0.8) + (0 × 0.2) = 8.0
        assert blended == pytest.approx(8.0, rel=0.01)

    def test_both_zero(self):
        """Both zero should return zero."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        blended = calculate_current_week_blend(0.0, 0.0, wednesday)
        assert blended == pytest.approx(0.0, abs=0.01)

    def test_negative_values_not_expected(self):
        """Negative values shouldn't occur but formula should handle."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        # If somehow negative values appear, formula still applies
        blended = calculate_current_week_blend(-5.0, 10.0, wednesday)
        # Expected: (-5 × 0.4) + (10 × 0.6) = -2.0 + 6.0 = 4.0
        assert blended == pytest.approx(4.0, rel=0.01)

    def test_large_values(self):
        """Large values should work correctly."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        blended = calculate_current_week_blend(1000.0, 1500.0, wednesday)
        # Expected: (1000 × 0.4) + (1500 × 0.6) = 400 + 900 = 1300
        assert blended == pytest.approx(1300.0, rel=0.01)


class TestBlendMetadata:
    """Test metadata generation for UI transparency."""

    def test_metadata_structure_wednesday(self):
        """Metadata should contain all required keys."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        meta = get_blend_metadata(5.0, 11.5, wednesday)

        required_keys = [
            "blended",
            "forecast",
            "actual",
            "actual_weight",
            "forecast_weight",
            "actual_percent",
            "forecast_percent",
            "weekday",
            "day_name",
            "is_blended",
        ]

        for key in required_keys:
            assert key in meta, f"Missing key: {key}"

    def test_metadata_values_wednesday(self):
        """Wednesday metadata should have correct values."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        meta = get_blend_metadata(5.0, 11.5, wednesday)

        assert meta["blended"] == pytest.approx(8.9, rel=0.01)
        assert meta["forecast"] == 11.5
        assert meta["actual"] == 5.0
        assert meta["actual_weight"] == 0.4
        assert meta["forecast_weight"] == 0.6
        assert meta["actual_percent"] == 40
        assert meta["forecast_percent"] == 60
        assert meta["weekday"] == 2
        assert meta["day_name"] == "Wednesday"
        assert meta["is_blended"] is True

    def test_metadata_monday_blending_active(self):
        """Monday should show blending active."""
        monday = datetime(2026, 2, 9, 10, 0, 0)
        meta = get_blend_metadata(0.0, 11.5, monday)

        assert meta["is_blended"] is True
        assert meta["actual_percent"] == 0
        assert meta["forecast_percent"] == 100
        assert meta["day_name"] == "Monday"

    def test_metadata_friday_blending_active(self):
        """Friday should show blending active (80% actual, 20% forecast)."""
        friday = datetime(2026, 2, 13, 10, 0, 0)
        meta = get_blend_metadata(10.0, 11.5, friday)

        assert meta["is_blended"] is True
        assert meta["actual_percent"] == 80
        assert meta["forecast_percent"] == 20
        assert meta["day_name"] == "Friday"

    def test_metadata_all_weekdays(self):
        """Test metadata for all weekdays."""
        dates = [
            datetime(2026, 2, 9, 10, 0, 0),  # Monday
            datetime(2026, 2, 10, 10, 0, 0),  # Tuesday
            datetime(2026, 2, 11, 10, 0, 0),  # Wednesday
            datetime(2026, 2, 12, 10, 0, 0),  # Thursday
            datetime(2026, 2, 13, 10, 0, 0),  # Friday
            datetime(2026, 2, 14, 10, 0, 0),  # Saturday
            datetime(2026, 2, 15, 10, 0, 0),  # Sunday
        ]

        for i, date in enumerate(dates):
            meta = get_blend_metadata(5.0, 11.5, date)
            assert meta["weekday"] == i
            assert meta["day_name"] == DAY_NAMES[i]


class TestBlendDescription:
    """Test human-readable description formatting."""

    def test_description_monday(self):
        """Monday description should show 0% actual, 100% forecast."""
        monday = datetime(2026, 2, 9, 10, 0, 0)
        meta = get_blend_metadata(0.0, 11.5, monday)
        desc = format_blend_description(meta)

        assert "0% actual" in desc
        assert "100% forecast" in desc
        assert "Monday" in desc

    def test_description_wednesday(self):
        """Wednesday description should show 40/60 split."""
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        meta = get_blend_metadata(5.0, 11.5, wednesday)
        desc = format_blend_description(meta)

        assert "40% actual" in desc
        assert "60% forecast" in desc
        assert "Wednesday" in desc

    def test_description_friday_blended(self):
        """Friday description should show 80/20 blend."""
        friday = datetime(2026, 2, 13, 10, 0, 0)
        meta = get_blend_metadata(10.0, 11.5, friday)
        desc = format_blend_description(meta)

        assert "80% actual" in desc
        assert "20% forecast" in desc
        assert "Friday" in desc

    def test_description_saturday_no_blend(self):
        """Saturday description should show pure actual."""
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        meta = get_blend_metadata(12.0, 11.5, saturday)
        desc = format_blend_description(meta)

        assert "Current week actual" in desc
        assert "Saturday" in desc


class TestProgressionThroughWeek:
    """Test smooth progression through entire week."""

    def test_monday_to_friday_progression(self):
        """Verify smooth transition from forecast to actual."""
        # Scenario: Team averages 11.5 items/week, current week varying actuals
        forecast = 11.5
        actuals = [0, 2, 5, 8, 10]  # Mon-Fri
        expected = [
            11.5,
            9.6,
            8.9,
            9.4,
            10.3,
        ]  # Expected blended values (linear progression)

        dates = [
            datetime(2026, 2, 9 + i, 10, 0, 0)
            for i in range(5)  # Mon-Fri
        ]

        for i, (date, actual, expected_blend) in enumerate(
            zip(dates, actuals, expected, strict=False)
        ):
            blended = calculate_current_week_blend(actual, forecast, date)
            assert blended == pytest.approx(expected_blend, rel=0.01), (
                f"{DAY_NAMES[i]} failed: got {blended}, expected {expected_blend}"
            )

    def test_no_monday_cliff(self):
        """Monday should show stable forecast, not low actual."""
        monday = datetime(2026, 2, 9, 10, 0, 0)
        friday_prev = datetime(2026, 2, 6, 10, 0, 0)

        forecast = 11.5
        friday_actual = 12.0  # Previous week ended at 12
        monday_actual = 0.0  # New week starts at 0

        friday_blend = calculate_current_week_blend(
            friday_actual, forecast, friday_prev
        )
        monday_blend = calculate_current_week_blend(monday_actual, forecast, monday)

        # Friday should show blended (80% actual, 20% forecast): 12*0.8 + 11.5*0.2 = 9.6 + 2.3 = 11.9
        assert friday_blend == pytest.approx(11.9, rel=0.01)
        # Monday should show forecast (11.5), NOT zero
        assert monday_blend == pytest.approx(11.5, rel=0.01)
        # Monday and Friday should be close (smooth transition, no cliff!)
        assert abs(monday_blend - friday_blend) / friday_blend <= 0.05


class TestWeekendBehavior:
    """Test Saturday/Sunday behavior (work week complete)."""

    def test_weekend_uses_actual_only(self):
        """Weekend should show 100% actual (work week complete)."""
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        sunday = datetime(2026, 2, 15, 10, 0, 0)

        forecast = 11.5
        actual = 12.0

        sat_blend = calculate_current_week_blend(actual, forecast, saturday)
        sun_blend = calculate_current_week_blend(actual, forecast, sunday)

        assert sat_blend == pytest.approx(12.0, rel=0.01)
        assert sun_blend == pytest.approx(12.0, rel=0.01)

    def test_weekend_metadata_not_blended(self):
        """Weekend metadata should show no blending."""
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        meta = get_blend_metadata(12.0, 11.5, saturday)

        assert meta["is_blended"] is False
        assert meta["actual_percent"] == 100
        assert meta["forecast_percent"] == 0
