"""Tests for time formatting utilities.

Tests relative time string generation and datetime formatting.
"""

from datetime import datetime, timedelta, timezone
from data.time_formatting import get_relative_time_string, format_datetime_for_display


class TestGetRelativeTimeString:
    """Test relative time string generation."""

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        assert get_relative_time_string(None) is None

    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        assert get_relative_time_string("") is None

    def test_invalid_timestamp_returns_none(self):
        """Test that invalid timestamp format returns None."""
        assert get_relative_time_string("not-a-timestamp") is None

    def test_just_now_less_than_one_minute(self):
        """Test 'Just now' for timestamps < 1 minute ago."""
        now = datetime.now(timezone.utc)
        thirty_seconds_ago = now - timedelta(seconds=30)
        result = get_relative_time_string(thirty_seconds_ago.isoformat())
        assert result == "Just now"

    def test_minutes_ago(self):
        """Test 'Xm ago' format for 1-59 minutes."""
        now = datetime.now(timezone.utc)

        # 5 minutes ago
        five_min_ago = now - timedelta(minutes=5)
        assert get_relative_time_string(five_min_ago.isoformat()) == "5m ago"

        # 30 minutes ago
        thirty_min_ago = now - timedelta(minutes=30)
        assert get_relative_time_string(thirty_min_ago.isoformat()) == "30m ago"

        # 59 minutes ago
        fifty_nine_min_ago = now - timedelta(minutes=59)
        assert get_relative_time_string(fifty_nine_min_ago.isoformat()) == "59m ago"

    def test_hours_ago(self):
        """Test 'Xh ago' format for 1-23 hours."""
        now = datetime.now(timezone.utc)

        # 2 hours ago
        two_hours_ago = now - timedelta(hours=2)
        assert get_relative_time_string(two_hours_ago.isoformat()) == "2h ago"

        # 12 hours ago
        twelve_hours_ago = now - timedelta(hours=12)
        assert get_relative_time_string(twelve_hours_ago.isoformat()) == "12h ago"

        # 23 hours ago
        twenty_three_hours_ago = now - timedelta(hours=23)
        assert get_relative_time_string(twenty_three_hours_ago.isoformat()) == "23h ago"

    def test_days_ago(self):
        """Test 'Xd ago' format for 1-6 days."""
        now = datetime.now(timezone.utc)

        # 1 day ago
        one_day_ago = now - timedelta(days=1)
        assert get_relative_time_string(one_day_ago.isoformat()) == "1d ago"

        # 3 days ago
        three_days_ago = now - timedelta(days=3)
        assert get_relative_time_string(three_days_ago.isoformat()) == "3d ago"

        # 6 days ago
        six_days_ago = now - timedelta(days=6)
        assert get_relative_time_string(six_days_ago.isoformat()) == "6d ago"

    def test_weeks_ago(self):
        """Test 'Xw ago' format for 7-28 days."""
        now = datetime.now(timezone.utc)

        # 1 week ago
        one_week_ago = now - timedelta(days=7)
        assert get_relative_time_string(one_week_ago.isoformat()) == "1w ago"

        # 2 weeks ago
        two_weeks_ago = now - timedelta(days=14)
        assert get_relative_time_string(two_weeks_ago.isoformat()) == "2w ago"

        # 3 weeks ago
        three_weeks_ago = now - timedelta(days=21)
        assert get_relative_time_string(three_weeks_ago.isoformat()) == "3w ago"

    def test_month_day_same_year(self):
        """Test 'Mon DD' format for >28 days, same year."""
        # Create a timestamp that is 40 days old but in the same year
        # Use current date and go back 40 days
        from datetime import datetime

        now = datetime.now(timezone.utc)
        forty_days_ago = now - timedelta(days=40)

        # Check if we crossed into previous year
        if forty_days_ago.year == now.year:
            result = get_relative_time_string(forty_days_ago.isoformat())

            # Should be "Mon DD" format
            assert result is not None
            parts = result.split()
            assert len(parts) == 2
            assert parts[0][0].isupper()  # Month starts with capital
            # Day part might have leading zero stripped, so just check it contains digits
            assert any(c.isdigit() for c in parts[1])
        else:
            # If we crossed years, should get "Mon 'YY" format instead
            result = get_relative_time_string(forty_days_ago.isoformat())
            assert result is not None
            assert "'" in result  # Year marker

    def test_month_year_previous_year(self):
        """Test 'Mon \\'YY' format for previous years."""
        # Fixed date in previous year
        past_date = datetime(2025, 12, 20, tzinfo=timezone.utc)
        result = get_relative_time_string(past_date.isoformat())

        # Should be "Mon 'YY" format
        assert result is not None
        assert "'25" in result or "Dec" in result

    def test_handles_z_suffix(self):
        """Test that 'Z' suffix in ISO format is handled correctly."""
        timestamp_with_z = "2026-01-29T14:30:00Z"
        result = get_relative_time_string(timestamp_with_z)
        assert result is not None

    def test_handles_timezone_offset(self):
        """Test that timezone offset format is handled correctly."""
        timestamp_with_offset = "2026-01-29T14:30:00+00:00"
        result = get_relative_time_string(timestamp_with_offset)
        assert result is not None

    def test_future_timestamp_returns_just_now(self):
        """Test that future timestamps return 'Just now' (clock skew tolerance)."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(minutes=5)
        result = get_relative_time_string(future.isoformat())
        assert result == "Just now"


class TestFormatDatetimeForDisplay:
    """Test human-readable datetime formatting."""

    def test_none_returns_never(self):
        """Test that None input returns 'Never'."""
        assert format_datetime_for_display(None) == "Never"

    def test_empty_string_returns_never(self):
        """Test that empty string returns 'Never'."""
        assert format_datetime_for_display("") == "Never"

    def test_invalid_format_returns_invalid_date(self):
        """Test that invalid format returns 'Invalid date'."""
        assert format_datetime_for_display("not-a-date") == "Invalid date"

    def test_valid_timestamp_formatted_correctly(self):
        """Test that valid timestamp is formatted correctly."""
        timestamp = "2026-01-29T14:30:00Z"
        result = format_datetime_for_display(timestamp)

        # Should contain month, day, year, and time
        assert "Jan" in result
        assert "29" in result
        assert "2026" in result
        assert ":" in result

    def test_handles_timezone_suffix(self):
        """Test handling of different timezone formats."""
        timestamp_z = "2026-01-29T14:30:00Z"
        timestamp_offset = "2026-01-29T14:30:00+00:00"

        result_z = format_datetime_for_display(timestamp_z)
        result_offset = format_datetime_for_display(timestamp_offset)

        assert result_z != "Invalid date"
        assert result_offset != "Invalid date"
