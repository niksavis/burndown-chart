"""
Unit tests for data/time_period_calculator.py

Pure date-math functions — no I/O, no database, no network.
"""

from datetime import date, datetime

from data.time_period_calculator import (
    filter_by_week_range,
    format_year_week,
    generate_week_range,
    get_iso_week,
    get_recent_weeks,
    get_week_end_date,
    get_week_start_date,
    get_year_week_label,
    group_by_week,
    is_current_week,
    parse_year_week_label,
)

###############################################################################
# get_iso_week
###############################################################################


class TestGetIsoWeek:
    def test_known_date(self) -> None:
        dt = datetime(2025, 10, 27)  # Monday, ISO week 44 of 2025
        assert get_iso_week(dt) == (2025, 44)

    def test_year_boundary_early_january(self) -> None:
        # 2025-01-01 is Wednesday in ISO week 1 of 2025
        dt = datetime(2025, 1, 1)
        year, week = get_iso_week(dt)
        assert year == 2025
        assert week == 1

    def test_year_boundary_last_days_december(self) -> None:
        # 2020-12-31 is Thursday in ISO week 53 of 2020
        dt = datetime(2020, 12, 31)
        year, week = get_iso_week(dt)
        assert year == 2020
        assert week == 53

    def test_returns_tuple(self) -> None:
        dt = datetime(2025, 6, 15)
        result = get_iso_week(dt)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_none_returns_default(self) -> None:
        result = get_iso_week(None)  # type: ignore[arg-type]
        assert isinstance(result, tuple)


###############################################################################
# format_year_week
###############################################################################


class TestFormatYearWeek:
    def test_double_digit_week(self) -> None:
        assert format_year_week(2025, 44) == "2025-W44"

    def test_single_digit_week_zero_padded(self) -> None:
        assert format_year_week(2025, 1) == "2025-W01"

    def test_week_53(self) -> None:
        assert format_year_week(2020, 53) == "2020-W53"


###############################################################################
# get_year_week_label
###############################################################################


class TestGetYearWeekLabel:
    def test_combines_iso_week_and_format(self) -> None:
        dt = datetime(2025, 10, 27)
        assert get_year_week_label(dt) == "2025-W44"

    def test_single_digit_week_zero_padded(self) -> None:
        dt = datetime(2025, 1, 1)  # week 1
        label = get_year_week_label(dt)
        assert label == "2025-W01"


###############################################################################
# parse_year_week_label
###############################################################################


class TestParseYearWeekLabel:
    def test_iso_format_with_w_prefix(self) -> None:
        assert parse_year_week_label("2025-W44") == (2025, 44)

    def test_legacy_format_without_w_prefix(self) -> None:
        assert parse_year_week_label("2025-44") == (2025, 44)

    def test_single_digit_week(self) -> None:
        assert parse_year_week_label("2025-W01") == (2025, 1)

    def test_empty_string_returns_zero_tuple(self) -> None:
        assert parse_year_week_label("") == (0, 0)

    def test_none_returns_zero_tuple(self) -> None:
        assert parse_year_week_label(None) == (0, 0)  # type: ignore[arg-type]

    def test_no_hyphen_returns_zero_tuple(self) -> None:
        assert parse_year_week_label("invalid") == (0, 0)

    def test_invalid_numbers_return_zero_tuple(self) -> None:
        assert parse_year_week_label("AAAA-Wxx") == (0, 0)


###############################################################################
# get_week_start_date
###############################################################################


class TestGetWeekStartDate:
    def test_known_week(self) -> None:
        # ISO week 44 of 2025 starts Monday 2025-10-27
        result = get_week_start_date(2025, 44)
        assert result == date(2025, 10, 27)
        assert result.weekday() == 0  # Monday

    def test_week_1(self) -> None:
        # ISO week 1 of 2025 starts Monday 2024-12-30
        result = get_week_start_date(2025, 1)
        assert result.weekday() == 0  # Must be a Monday

    def test_zero_values_return_today(self) -> None:
        result = get_week_start_date(0, 0)
        assert result == date.today()


###############################################################################
# get_week_end_date
###############################################################################


class TestGetWeekEndDate:
    def test_known_week_ends_sunday(self) -> None:
        # ISO week 44 of 2025: Mon 2025-10-27 → Sun 2025-11-02
        result = get_week_end_date(2025, 44)
        assert result == date(2025, 11, 2)
        assert result.weekday() == 6  # Sunday

    def test_end_date_is_6_days_after_start(self) -> None:
        start = get_week_start_date(2025, 20)
        end = get_week_end_date(2025, 20)
        assert (end - start).days == 6

    def test_zero_values_return_today(self) -> None:
        result = get_week_end_date(0, 0)
        assert result == date.today()


###############################################################################
# is_current_week
###############################################################################


class TestIsCurrentWeek:
    def test_current_week_is_current(self) -> None:
        today = datetime.now()
        year, week = today.isocalendar()[:2]
        assert is_current_week(year, week) is True

    def test_past_week_is_not_current(self) -> None:
        assert is_current_week(2000, 1) is False

    def test_future_week_is_not_current(self) -> None:
        assert is_current_week(2099, 1) is False

    def test_zero_year_returns_false(self) -> None:
        assert is_current_week(0, 1) is False

    def test_zero_week_returns_false(self) -> None:
        assert is_current_week(2025, 0) is False


###############################################################################
# generate_week_range
###############################################################################


class TestGenerateWeekRange:
    def test_single_week_range(self) -> None:
        start = date(2025, 10, 27)  # Monday W44
        end = date(2025, 10, 27)
        result = generate_week_range(start, end, include_partial_current=True)
        assert len(result) >= 1
        assert "2025-W44" in result

    def test_multi_week_range(self) -> None:
        # The generator walks by 7-day steps from start; W43 is hit on 2025-10-22
        start = date(2025, 10, 1)  # W40
        end = date(2025, 10, 22)  # lands on W43 in the 7-day step sequence
        result = generate_week_range(start, end, include_partial_current=True)
        assert "2025-W40" in result
        assert "2025-W43" in result

    def test_reversed_dates_returns_empty(self) -> None:
        result = generate_week_range(date(2025, 10, 31), date(2025, 10, 1))
        assert result == []

    def test_none_dates_return_empty(self) -> None:
        result = generate_week_range(None, None)  # type: ignore[arg-type]
        assert result == []

    def test_no_duplicate_labels(self) -> None:
        start = date(2025, 10, 1)
        end = date(2025, 10, 31)
        result = generate_week_range(start, end, include_partial_current=True)
        assert len(result) == len(set(result))

    def test_labels_in_iso_format(self) -> None:
        start = date(2025, 10, 1)
        end = date(2025, 10, 7)
        result = generate_week_range(start, end, include_partial_current=True)
        for label in result:
            assert "W" in label


###############################################################################
# get_recent_weeks
###############################################################################


class TestGetRecentWeeks:
    def test_returns_list_of_strings(self) -> None:
        result = get_recent_weeks(4)
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_zero_or_negative_returns_empty(self) -> None:
        assert get_recent_weeks(0) == []
        assert get_recent_weeks(-1) == []

    def test_single_week_contains_current(self) -> None:
        result = get_recent_weeks(1, include_partial_current=True)
        today = datetime.now()
        year, week = today.isocalendar()[:2]
        expected = format_year_week(year, week)
        assert expected in result

    def test_labels_are_in_iso_format(self) -> None:
        result = get_recent_weeks(3, include_partial_current=True)
        for label in result:
            assert "W" in label


###############################################################################
# filter_by_week_range
###############################################################################


class TestFilterByWeekRange:
    _items = [
        {"key": "A-1", "date": "2025-10-27T10:00:00"},  # W44
        {"key": "A-2", "date": "2025-11-03T15:00:00"},  # W45
        {"key": "A-3", "date": "2025-10-28T08:00:00"},  # W44
    ]

    def test_filters_to_single_week(self) -> None:
        result = filter_by_week_range(self._items, "date", ["2025-W44"])
        keys = [item["key"] for item in result]
        assert "A-1" in keys
        assert "A-3" in keys
        assert "A-2" not in keys

    def test_empty_items_returns_empty(self) -> None:
        assert filter_by_week_range([], "date", ["2025-W44"]) == []

    def test_empty_week_labels_returns_all_items(self) -> None:
        result = filter_by_week_range(self._items, "date", [])
        assert result == self._items

    def test_items_without_date_field_excluded(self) -> None:
        items = [{"key": "A-1"}, {"key": "A-2", "date": "2025-10-27T10:00:00"}]
        result = filter_by_week_range(items, "date", ["2025-W44"])
        assert len(result) == 1
        assert result[0]["key"] == "A-2"

    def test_z_suffix_date_parsed(self) -> None:
        items = [{"key": "A-1", "date": "2025-10-27T10:00:00Z"}]
        result = filter_by_week_range(items, "date", ["2025-W44"])
        assert len(result) == 1

    def test_datetime_object_supported(self) -> None:
        items = [{"key": "A-1", "date": datetime(2025, 10, 27, 10, 0)}]
        result = filter_by_week_range(items, "date", ["2025-W44"])
        assert len(result) == 1

    def test_date_object_supported(self) -> None:
        items = [{"key": "A-1", "date": date(2025, 10, 27)}]
        result = filter_by_week_range(items, "date", ["2025-W44"])
        assert len(result) == 1


###############################################################################
# group_by_week
###############################################################################


class TestGroupByWeek:
    def test_groups_items_by_week(self) -> None:
        items = [
            {"key": "A-1", "date": "2025-10-27T10:00:00"},  # W44
            {"key": "A-2", "date": "2025-10-28T15:00:00"},  # W44
            {"key": "A-3", "date": "2025-11-03T08:00:00"},  # W45
        ]
        result = group_by_week(items, "date")
        assert "2025-W44" in result
        assert len(result["2025-W44"]) == 2
        assert "2025-W45" in result
        assert len(result["2025-W45"]) == 1

    def test_empty_items_returns_empty_dict(self) -> None:
        assert group_by_week([], "date") == {}

    def test_items_missing_date_field_excluded(self) -> None:
        items = [{"key": "A-1"}, {"key": "A-2", "date": "2025-10-27T10:00:00"}]
        result = group_by_week(items, "date")
        # Only A-2 should appear
        all_items = [item for group in result.values() for item in group]
        assert len(all_items) == 1
        assert all_items[0]["key"] == "A-2"

    def test_invalid_date_excluded(self) -> None:
        items = [
            {"key": "A-1", "date": "not-a-date"},
            {"key": "A-2", "date": "2025-10-27T10:00:00"},
        ]
        result = group_by_week(items, "date")
        all_items = [item for group in result.values() for item in group]
        keys = [item["key"] for item in all_items]
        assert "A-1" not in keys
        assert "A-2" in keys
