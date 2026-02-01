"""Test for show_points normalization function."""

import pytest
from callbacks.settings.helpers import normalize_show_points


class TestNormalizeShowPoints:
    """Test normalize_show_points helper function."""

    def test_normalize_checkbox_checked(self):
        """Test checkbox format when checked."""
        assert normalize_show_points(["show"]) is True

    def test_normalize_checkbox_unchecked(self):
        """Test checkbox format when unchecked."""
        assert normalize_show_points([]) is False

    def test_normalize_integer_true(self):
        """Test database integer format for True."""
        assert normalize_show_points(1) is True

    def test_normalize_integer_false(self):
        """Test database integer format for False."""
        assert normalize_show_points(0) is False

    def test_normalize_boolean_true(self):
        """Test boolean True."""
        assert normalize_show_points(True) is True

    def test_normalize_boolean_false(self):
        """Test boolean False."""
        assert normalize_show_points(False) is False

    def test_normalize_unknown_type(self):
        """Test unknown type defaults to False."""
        assert normalize_show_points("invalid") is False
        assert normalize_show_points(None) is False
        assert normalize_show_points({}) is False
