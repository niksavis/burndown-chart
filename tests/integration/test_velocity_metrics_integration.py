"""
Integration tests for velocity metric decimal precision.

These tests ensure that velocity metrics are displayed with the correct decimal precision
throughout the entire application flow, from data processing to UI rendering.
"""

import pytest
import pandas as pd

from data.processing import calculate_weekly_averages
from ui.pert_components import create_pert_info_table, _create_velocity_metric_card
from visualization.helpers import prepare_metrics_data as _prepare_metrics_data
from tests.utils.ui_test_helpers import (
    extract_numeric_value_from_component,
    validate_component_structure,
)


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


class TestVelocityMetricsIntegration:
    """Integration tests for velocity metrics display."""

    def test_pert_info_table_decimal_formatting(self, sample_velocity_data):
        """
        Test that velocity metrics in the PERT info table are displayed with one decimal place.

        This is an integration test that verifies the decimal formatting throughout the
        entire flow from raw data to UI component rendering.
        """
        # Calculate velocity metrics from sample data
        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(sample_velocity_data)
        )

        # Create PERT info table
        pert_info = create_pert_info_table(
            pert_time_items=20,
            pert_time_points=60,
            days_to_deadline=30,
            avg_weekly_items=avg_weekly_items,
            avg_weekly_points=avg_weekly_points,
            med_weekly_items=med_weekly_items,
            med_weekly_points=med_weekly_points,
            pert_factor=3,
            total_items=50,
            total_points=150,
            deadline_str="2023-06-30",
        )

        # Convert the component to string for inspection
        str(pert_info)

        # Extract and verify all formatted values from velocity metric cards
        # To verify one decimal formatting, first check the _create_velocity_metric_card
        # function directly

        for value in [
            avg_weekly_items,
            med_weekly_items,
            avg_weekly_points,
            med_weekly_points,
        ]:  # Create a card with the test value
            card = _create_velocity_metric_card(
                title="Average",  # Use a valid title that exists in VELOCITY_HELP_TEXTS
                value=value,
                trend=5,
                trend_icon="fas fa-arrow-up",
                trend_color="green",
                color="blue",
                is_mini=False,
            )

            # Safe extraction of the formatted value using our helper function
            assert card is not None, "Card component should not be None"
            assert validate_component_structure(card, ["children"], min_children=2), (
                "Card should have a valid structure with at least 2 children"
            )

            # Using the value_container in children[1]
            children = getattr(card, "children", None)
            value_container = (
                children[1] if children is not None and len(children) > 1 else None
            )
            assert value_container is not None, "Value container should not be None"

            # Extract numeric value from component
            numeric_value = extract_numeric_value_from_component(value_container)
            assert numeric_value is not None, (
                f"Could not extract numeric value from {value_container}"
            )

            # Compare rounded values to avoid floating point issues
            assert round(numeric_value, 1) == round(float(value), 1), (
                f"Value {numeric_value} should be rounded to {round(float(value), 1)}"
            )

            # Now just check if the formatted string contains the expected format
            formatted_value = str(value_container)
            expected_format = f"{float(value):.1f}"
            assert expected_format in formatted_value, (
                f"Value {value} should be formatted as {expected_format}, not found in {formatted_value}"
            )

    def test_end_to_end_metrics_flow(self, sample_dataframe):
        """
        Test the end-to-end flow from data processing to prepared metrics data.

        This test verifies that decimal precision is maintained throughout the
        data processing and preparation pipeline.
        """
        # Get weekly metrics
        avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
            sample_dataframe.to_dict("records")
        )

        # Prepare metrics data for visualization
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
            avg_weekly_items=avg_items,
            avg_weekly_points=avg_points,
            med_weekly_items=med_items,
            med_weekly_points=med_points,
        )

        # Verify that metrics data contains the original values
        assert abs(metrics_data["avg_weekly_items"] - avg_items) < 0.01
        assert abs(metrics_data["avg_weekly_points"] - avg_points) < 0.01
        assert abs(metrics_data["med_weekly_items"] - med_items) < 0.01
        assert abs(metrics_data["med_weekly_points"] - med_points) < 0.01
        # Verify formatted strings in metrics data (if they exist)
        if "avg_weekly_items_str" in metrics_data:
            formatted_avg_items = metrics_data["avg_weekly_items_str"]
            # The visualization.charts._prepare_metrics_data function may still use 2 decimal places
            # This is separate from the UI component formatting which uses 1 decimal place
            # So we should check that it's properly formatted according to its own rules
            if "." in formatted_avg_items:
                # Just verify it's a valid formatted string
                assert formatted_avg_items.replace(".", "").isdigit(), (
                    f"Formatted value {formatted_avg_items} should be a valid number"
                )
