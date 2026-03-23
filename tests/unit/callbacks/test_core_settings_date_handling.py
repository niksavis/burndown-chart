"""Regression tests for timeline date handling in core settings callbacks."""

from datetime import date, datetime

from callbacks.settings.core_settings import _normalize_date_picker_value


def test_normalize_date_picker_value_handles_none_and_empty() -> None:
    """None/empty date picker values should normalize to None."""
    assert _normalize_date_picker_value(None) is None
    assert _normalize_date_picker_value("") is None
    assert _normalize_date_picker_value("   ") is None


def test_normalize_date_picker_value_handles_iso_strings() -> None:
    """Date strings and ISO datetime strings should normalize to YYYY-MM-DD."""
    assert _normalize_date_picker_value("2026-05-01") == "2026-05-01"
    assert _normalize_date_picker_value("2026-05-01T00:00:00") == "2026-05-01"
    assert _normalize_date_picker_value("2026-05-01 00:00:00") == "2026-05-01"


def test_normalize_date_picker_value_handles_date_objects() -> None:
    """date and datetime objects should normalize safely for persistence."""
    assert _normalize_date_picker_value(date(2026, 5, 1)) == "2026-05-01"
    assert _normalize_date_picker_value(datetime(2026, 5, 1, 12, 30, 0)) == "2026-05-01"
