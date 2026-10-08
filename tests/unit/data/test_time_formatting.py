from datetime import UTC, datetime, timedelta

from data.time_formatting import format_datetime_for_display, get_relative_time_string


class TestGetRelativeTimeString:
    def test_none_input_returns_none(self):
        assert get_relative_time_string(None) is None

    def test_empty_string_returns_none(self):
        assert get_relative_time_string("") is None

    def test_invalid_timestamp_returns_none(self):
        assert get_relative_time_string("not-a-timestamp") is None

    def test_just_now_less_than_one_minute(self):
        now = datetime.now(UTC)
        thirty_seconds_ago = now - timedelta(seconds=30)
        result = get_relative_time_string(thirty_seconds_ago.isoformat())
        assert result == "Just now"

    def test_minutes_ago(self):
        now = datetime.now(UTC)

        five_min_ago = now - timedelta(minutes=5)
        assert get_relative_time_string(five_min_ago.isoformat()) == "5m ago"

        thirty_min_ago = now - timedelta(minutes=30)
        assert get_relative_time_string(thirty_min_ago.isoformat()) == "30m ago"

        fifty_nine_min_ago = now - timedelta(minutes=59)
        assert get_relative_time_string(fifty_nine_min_ago.isoformat()) == "59m ago"

    def test_hours_ago(self):
        now = datetime.now(UTC)

        two_hours_ago = now - timedelta(hours=2)
        assert get_relative_time_string(two_hours_ago.isoformat()) == "2h ago"

        twelve_hours_ago = now - timedelta(hours=12)
        assert get_relative_time_string(twelve_hours_ago.isoformat()) == "12h ago"

        twenty_three_hours_ago = now - timedelta(hours=23)
        assert get_relative_time_string(twenty_three_hours_ago.isoformat()) == "23h ago"

    def test_days_ago(self):
        now = datetime.now(UTC)

        one_day_ago = now - timedelta(days=1)
        assert get_relative_time_string(one_day_ago.isoformat()) == "1d ago"

        three_days_ago = now - timedelta(days=3)
        assert get_relative_time_string(three_days_ago.isoformat()) == "3d ago"

        six_days_ago = now - timedelta(days=6)
        assert get_relative_time_string(six_days_ago.isoformat()) == "6d ago"

    def test_weeks_ago(self):
        now = datetime.now(UTC)

        one_week_ago = now - timedelta(days=7)
        assert get_relative_time_string(one_week_ago.isoformat()) == "1w ago"

        two_weeks_ago = now - timedelta(days=14)
        assert get_relative_time_string(two_weeks_ago.isoformat()) == "2w ago"

        three_weeks_ago = now - timedelta(days=21)
        assert get_relative_time_string(three_weeks_ago.isoformat()) == "3w ago"

    def test_month_day_same_year(self):
        from datetime import datetime

        now = datetime.now(UTC)
        forty_days_ago = now - timedelta(days=40)

        if forty_days_ago.year == now.year:
            result = get_relative_time_string(forty_days_ago.isoformat())

            assert result is not None
            parts = result.split()
            assert len(parts) == 2
            assert parts[0][0].isupper()
            assert any(c.isdigit() for c in parts[1])
        else:
            result = get_relative_time_string(forty_days_ago.isoformat())
            assert result is not None
            assert "'" in result

    def test_month_year_previous_year(self):
        past_date = datetime(2025, 12, 20, tzinfo=UTC)
        result = get_relative_time_string(past_date.isoformat())

        assert result is not None
        assert "'25" in result or "Dec" in result

    def test_handles_z_suffix(self):
        timestamp_with_z = "2026-01-29T14:30:00Z"
        result = get_relative_time_string(timestamp_with_z)
        assert result is not None

    def test_handles_timezone_offset(self):
        timestamp_with_offset = "2026-01-29T14:30:00+00:00"
        result = get_relative_time_string(timestamp_with_offset)
        assert result is not None

    def test_future_timestamp_returns_just_now(self):
        now = datetime.now(UTC)
        future = now + timedelta(minutes=5)
        result = get_relative_time_string(future.isoformat())
        assert result == "Just now"


class TestFormatDatetimeForDisplay:
    def test_none_returns_never(self):
        assert format_datetime_for_display(None) == "Never"

    def test_empty_string_returns_never(self):
        assert format_datetime_for_display("") == "Never"

    def test_invalid_format_returns_invalid_date(self):
        assert format_datetime_for_display("not-a-date") == "Invalid date"

    def test_valid_timestamp_formatted_correctly(self):
        timestamp = "2026-01-29T14:30:00Z"
        result = format_datetime_for_display(timestamp)

        assert "Jan" in result
        assert "29" in result
        assert "2026" in result
        assert ":" in result

    def test_handles_timezone_suffix(self):
        timestamp_z = "2026-01-29T14:30:00Z"
        timestamp_offset = "2026-01-29T14:30:00+00:00"

        result_z = format_datetime_for_display(timestamp_z)
        result_offset = format_datetime_for_display(timestamp_offset)

        assert result_z != "Invalid date"
        assert result_offset != "Invalid date"
