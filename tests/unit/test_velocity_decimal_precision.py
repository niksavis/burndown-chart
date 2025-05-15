"""
Unit tests for decimal precision in velocity metrics.

These tests ensure that velocity metrics maintain the correct decimal precision
throughout the data processing pipeline and in the UI components.
"""

import pytest
import pandas as pd
from datetime import datetime

from data.processing import calculate_weekly_averages
from visualization.charts import _get_weekly_metrics, _prepare_metrics_data
from ui.components import _create_velocity_metric_card


@pytest.fixture
def sample_velocity_data():
    """Create sample velocity data with decimal values."""
    return [
        {"date": "2023-01-01", "completed_items": 8.7, "completed_points": 30.6},
        {"date": "2023-01-08", "completed_items": 7.5, "completed_points": 25.0},
        {"date": "2023-01-15", "completed_items": 9.2, "completed_points": 32.4},
        {"date": "2023-01-22", "completed_items": 8.4, "completed_points": 29.8},
        {"date": "2023-01-29", "completed_items": 10.1, "completed_points": 35.3},
        {"date": "2023-02-05", "completed_items": 7.9, "completed_points": 27.7},
        {"date": "2023-02-12", "completed_items": 9.5, "completed_points": 33.2},
        {"date": "2023-02-19", "completed_items": 7.2, "completed_points": 25.4},
        {"date": "2023-02-26", "completed_items": 8.9, "completed_points": 31.1},
        {"date": "2023-03-05", "completed_items": 9.8, "completed_points": 34.3},
    ]


@pytest.fixture
def sample_dataframe(sample_velocity_data):
    """Convert sample data to DataFrame."""
    df = pd.DataFrame(sample_velocity_data)
    df["date"] = pd.to_datetime(df["date"])
    return df


class TestDecimalPrecision:
    """Test cases for decimal precision in velocity metrics."""

    def test_calculate_weekly_averages_precision(self, sample_velocity_data):
        """Test that calculate_weekly_averages preserves decimal precision."""
        avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
            sample_velocity_data
        )

        # Check that values have decimal precision
        assert isinstance(avg_items, float)
        assert isinstance(avg_points, float)
        assert isinstance(med_items, float)
        assert isinstance(med_points, float)

        # Verify the expected values to 2 decimal places
        # Note: Using round() to handle potential floating point precision issues
        assert round(avg_items, 2) == 8.72
        assert round(avg_points, 2) == 30.48
        assert round(med_items, 2) == 8.80
        assert round(med_points, 2) == 30.85

    def test_get_weekly_metrics_precision(self, sample_dataframe):
        """Test that _get_weekly_metrics preserves decimal precision."""
        g_avg_items, g_avg_points, g_med_items, g_med_points = _get_weekly_metrics(
            sample_dataframe
        )

        # Check that values have decimal precision
        assert isinstance(g_avg_items, float)
        assert isinstance(g_avg_points, float)
        assert isinstance(g_med_items, float)
        assert isinstance(g_med_points, float)

        # Verify the expected values to 2 decimal places
        assert round(g_avg_items, 2) == 8.72
        assert round(g_avg_points, 2) == 30.48
        assert round(g_med_items, 2) == 8.80
        assert round(g_med_points, 2) == 30.85

    def test_prepare_metrics_data_precision(self, sample_dataframe):
        """Test that _prepare_metrics_data preserves decimal precision."""
        metrics_data = _prepare_metrics_data(
            total_items=50,
            total_points=150,
            deadline=pd.Timestamp("2023-06-30"),
            pert_time_items=25,
            pert_time_points=30,
            data_points_count=10,
            df=sample_dataframe,
            items_completion_enhanced="2023-05-01",
            points_completion_enhanced="2023-05-15",
            avg_weekly_items=8.7,
            avg_weekly_points=30.6,
            med_weekly_items=7.5,
            med_weekly_points=25.0,
        )

        # Check that input values are preserved
        assert abs(metrics_data["avg_weekly_items"] - 8.7) < 0.01
        assert abs(metrics_data["avg_weekly_points"] - 30.6) < 0.01
        assert abs(metrics_data["med_weekly_items"] - 7.5) < 0.01
        assert abs(metrics_data["med_weekly_points"] - 25.0) < 0.01


class TestUIComponentsFormatting:
    """Test cases for UI component formatting of decimal values."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (8.7, "8.7"),  # Value with one decimal place
            (7.0, "7.0"),  # Integer-like value with zero decimal
            (8.75, "8.8"),  # Value with two decimals (should round to one)
            (9.99, "10.0"),  # Value close to integer (rounds up)
            (10, "10.0"),  # Integer value (should show one decimal)
            (0.1, "0.1"),  # Small decimal value
            (123.456, "123.5"),  # Larger value with multiple decimals
        ],
    )
    def test_velocity_card_decimal_formatting(self, value, expected):
        """Test that velocity metric card formats values with one decimal place."""
        card = _create_velocity_metric_card(
            title="Test",
            value=value,
            trend=5,
            trend_icon="fas fa-arrow-up",
            trend_color="green",
            color="blue",
            is_mini=False,
        )

        # Extract the formatted value from the card
        formatted_value = card.children[1].children.children

        # Verify it has one decimal place
        assert formatted_value == expected, (
            f"Value {value} should format as {expected}, got {formatted_value}"
        )

        # Check that the string format uses one decimal place
        assert formatted_value.count(".") <= 1, "Should have at most one decimal point"
        if "." in formatted_value:
            integer_part, decimal_part = formatted_value.split(".")
            assert len(decimal_part) == 1, (
                "Should have exactly one digit after decimal point"
            )
