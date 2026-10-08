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
    def test_monday_weight(self):
        monday = datetime(2026, 2, 9, 10, 0, 0)
        assert monday.weekday() == 0
        weight = get_weekday_weight(monday)
        assert weight == 0.0

    def test_tuesday_weight(self):
        tuesday = datetime(2026, 2, 10, 10, 0, 0)
        assert tuesday.weekday() == 1
        weight = get_weekday_weight(tuesday)
        assert weight == 0.2

    def test_wednesday_weight(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        assert wednesday.weekday() == 2
        weight = get_weekday_weight(wednesday)
        assert weight == 0.4

    def test_thursday_weight(self):
        thursday = datetime(2026, 2, 12, 10, 0, 0)
        assert thursday.weekday() == 3
        weight = get_weekday_weight(thursday)
        assert weight == 0.6

    def test_friday_weight(self):
        friday = datetime(2026, 2, 13, 10, 0, 0)
        assert friday.weekday() == 4
        weight = get_weekday_weight(friday)
        assert weight == 0.8

    def test_saturday_weight(self):
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        assert saturday.weekday() == 5
        weight = get_weekday_weight(saturday)
        assert weight == 1.0

    def test_sunday_weight(self):
        sunday = datetime(2026, 2, 15, 10, 0, 0)
        assert sunday.weekday() == 6
        weight = get_weekday_weight(sunday)
        assert weight == 1.0

    def test_all_weekdays_mapped(self):
        assert len(WEEKDAY_WEIGHTS) == 7
        for day in range(7):
            assert day in WEEKDAY_WEIGHTS
            assert 0.0 <= WEEKDAY_WEIGHTS[day] <= 1.0


class TestCurrentWeekBlend:
    def test_monday_blend_pure_forecast(self):
        monday = datetime(2026, 2, 9, 10, 0, 0)
        actual = 0.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, monday)
        assert blended == pytest.approx(11.5, rel=0.01)

    def test_tuesday_blend_20_80(self):
        tuesday = datetime(2026, 2, 10, 10, 0, 0)
        actual = 2.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, tuesday)
        assert blended == pytest.approx(9.6, rel=0.01)

    def test_wednesday_blend_40_60(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        actual = 5.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, wednesday)
        assert blended == pytest.approx(8.9, rel=0.01)

    def test_thursday_blend_60_40(self):
        thursday = datetime(2026, 2, 12, 10, 0, 0)
        actual = 8.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, thursday)
        assert blended == pytest.approx(9.4, rel=0.01)

    def test_friday_blend_80_20(self):
        friday = datetime(2026, 2, 13, 10, 0, 0)
        actual = 10.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, friday)
        assert blended == pytest.approx(10.3, rel=0.01)

    def test_saturday_blend_pure_actual(self):
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        actual = 12.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, saturday)
        assert blended == pytest.approx(12.0, rel=0.01)

    def test_sunday_blend_pure_actual(self):
        sunday = datetime(2026, 2, 15, 10, 0, 0)
        actual = 12.0
        forecast = 11.5
        blended = calculate_current_week_blend(actual, forecast, sunday)
        assert blended == pytest.approx(12.0, rel=0.01)


class TestBoundaryConditions:
    def test_zero_actual_monday(self):
        monday = datetime(2026, 2, 9, 10, 0, 0)
        blended = calculate_current_week_blend(0.0, 11.5, monday)
        assert blended == pytest.approx(11.5, rel=0.01)

    def test_zero_forecast_friday(self):
        friday = datetime(2026, 2, 13, 10, 0, 0)
        blended = calculate_current_week_blend(10.0, 0.0, friday)
        assert blended == pytest.approx(8.0, rel=0.01)

    def test_both_zero(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        blended = calculate_current_week_blend(0.0, 0.0, wednesday)
        assert blended == pytest.approx(0.0, abs=0.01)

    def test_negative_values_not_expected(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        blended = calculate_current_week_blend(-5.0, 10.0, wednesday)
        assert blended == pytest.approx(4.0, rel=0.01)

    def test_large_values(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        blended = calculate_current_week_blend(1000.0, 1500.0, wednesday)
        assert blended == pytest.approx(1300.0, rel=0.01)


class TestBlendMetadata:
    def test_metadata_structure_wednesday(self):
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
        monday = datetime(2026, 2, 9, 10, 0, 0)
        meta = get_blend_metadata(0.0, 11.5, monday)

        assert meta["is_blended"] is True
        assert meta["actual_percent"] == 0
        assert meta["forecast_percent"] == 100
        assert meta["day_name"] == "Monday"

    def test_metadata_friday_blending_active(self):
        friday = datetime(2026, 2, 13, 10, 0, 0)
        meta = get_blend_metadata(10.0, 11.5, friday)

        assert meta["is_blended"] is True
        assert meta["actual_percent"] == 80
        assert meta["forecast_percent"] == 20
        assert meta["day_name"] == "Friday"

    def test_metadata_all_weekdays(self):
        dates = [
            datetime(2026, 2, 9, 10, 0, 0),
            datetime(2026, 2, 10, 10, 0, 0),
            datetime(2026, 2, 11, 10, 0, 0),
            datetime(2026, 2, 12, 10, 0, 0),
            datetime(2026, 2, 13, 10, 0, 0),
            datetime(2026, 2, 14, 10, 0, 0),
            datetime(2026, 2, 15, 10, 0, 0),
        ]

        for i, date in enumerate(dates):
            meta = get_blend_metadata(5.0, 11.5, date)
            assert meta["weekday"] == i
            assert meta["day_name"] == DAY_NAMES[i]


class TestBlendDescription:
    def test_description_monday(self):
        monday = datetime(2026, 2, 9, 10, 0, 0)
        meta = get_blend_metadata(0.0, 11.5, monday)
        desc = format_blend_description(meta)

        assert "0% actual" in desc
        assert "100% forecast" in desc
        assert "Monday" in desc

    def test_description_wednesday(self):
        wednesday = datetime(2026, 2, 11, 10, 0, 0)
        meta = get_blend_metadata(5.0, 11.5, wednesday)
        desc = format_blend_description(meta)

        assert "40% actual" in desc
        assert "60% forecast" in desc
        assert "Wednesday" in desc

    def test_description_friday_blended(self):
        friday = datetime(2026, 2, 13, 10, 0, 0)
        meta = get_blend_metadata(10.0, 11.5, friday)
        desc = format_blend_description(meta)

        assert "80% actual" in desc
        assert "20% forecast" in desc
        assert "Friday" in desc

    def test_description_saturday_no_blend(self):
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        meta = get_blend_metadata(12.0, 11.5, saturday)
        desc = format_blend_description(meta)

        assert "Current week actual" in desc
        assert "Saturday" in desc


class TestProgressionThroughWeek:
    def test_monday_to_friday_progression(self):
        forecast = 11.5
        actuals = [0, 2, 5, 8, 10]
        expected = [
            11.5,
            9.6,
            8.9,
            9.4,
            10.3,
        ]

        dates = [datetime(2026, 2, 9 + i, 10, 0, 0) for i in range(5)]

        for i, (date, actual, expected_blend) in enumerate(
            zip(dates, actuals, expected, strict=False)
        ):
            blended = calculate_current_week_blend(actual, forecast, date)
            assert blended == pytest.approx(expected_blend, rel=0.01), (
                f"{DAY_NAMES[i]} failed: got {blended}, expected {expected_blend}"
            )

    def test_no_monday_cliff(self):
        monday = datetime(2026, 2, 9, 10, 0, 0)
        friday_prev = datetime(2026, 2, 6, 10, 0, 0)

        forecast = 11.5
        friday_actual = 12.0
        monday_actual = 0.0

        friday_blend = calculate_current_week_blend(
            friday_actual, forecast, friday_prev
        )
        monday_blend = calculate_current_week_blend(monday_actual, forecast, monday)

        assert friday_blend == pytest.approx(11.9, rel=0.01)
        assert monday_blend == pytest.approx(11.5, rel=0.01)
        assert abs(monday_blend - friday_blend) / friday_blend <= 0.05


class TestWeekendBehavior:
    def test_weekend_uses_actual_only(self):
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        sunday = datetime(2026, 2, 15, 10, 0, 0)

        forecast = 11.5
        actual = 12.0

        sat_blend = calculate_current_week_blend(actual, forecast, saturday)
        sun_blend = calculate_current_week_blend(actual, forecast, sunday)

        assert sat_blend == pytest.approx(12.0, rel=0.01)
        assert sun_blend == pytest.approx(12.0, rel=0.01)

    def test_weekend_metadata_not_blended(self):
        saturday = datetime(2026, 2, 14, 10, 0, 0)
        meta = get_blend_metadata(12.0, 11.5, saturday)

        assert meta["is_blended"] is False
        assert meta["actual_percent"] == 100
        assert meta["forecast_percent"] == 0
