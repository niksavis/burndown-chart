"""Tests for metrics helper functions."""

import re

from data.metrics.helpers import get_current_iso_week


def test_get_current_iso_week_format_includes_w():
    label = get_current_iso_week()

    assert re.match(r"^\d{4}-W\d{2}$", label)
