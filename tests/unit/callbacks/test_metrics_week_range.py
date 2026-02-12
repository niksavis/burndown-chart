"""Tests for metrics week range calculation."""

from datetime import datetime, timedelta

from callbacks.settings.metrics import _calculate_weeks_from_statistics
from data.iso_week_bucketing import get_week_label


def test_calculate_weeks_from_statistics_includes_current_week():
    now = datetime.now()
    past_start = now - timedelta(days=30)
    past_end = now - timedelta(days=15)

    statistics = [
        {"date": past_start.date().isoformat()},
        {"date": past_end.date().isoformat()},
    ]

    total_weeks, custom_weeks = _calculate_weeks_from_statistics(statistics)

    assert total_weeks == len(custom_weeks)
    assert custom_weeks
    assert custom_weeks[-1][0] == get_week_label(now)
