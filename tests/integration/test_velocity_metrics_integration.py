import pandas as pd
import pytest

from data.processing import calculate_weekly_averages
from tests.utils.ui_test_helpers import (
    extract_numeric_value_from_component,
    validate_component_structure,
)
from ui.pert_components import _create_velocity_metric_card, create_pert_info_table
from visualization.helpers import prepare_metrics_data as _prepare_metrics_data


@pytest.fixture
def sample_velocity_data():
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
    df = pd.DataFrame(sample_velocity_data)
    df["date"] = pd.to_datetime(df["date"])
    return df


class TestVelocityMetricsIntegration:
    def test_pert_info_table_decimal_formatting(self, sample_velocity_data):

        avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
            calculate_weekly_averages(sample_velocity_data)
        )

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

        str(pert_info)

        for value in [
            avg_weekly_items,
            med_weekly_items,
            avg_weekly_points,
            med_weekly_points,
        ]:
            card = _create_velocity_metric_card(
                title="Average",
                value=value,
                trend=5,
                trend_icon="fas fa-arrow-up",
                trend_color="green",
                color="blue",
                is_mini=False,
            )

            assert card is not None, "Card component should not be None"
            assert validate_component_structure(card, ["children"], min_children=2), (
                "Card should have a valid structure with at least 2 children"
            )

            children = getattr(card, "children", None)
            value_container = (
                children[1] if children is not None and len(children) > 1 else None
            )
            assert value_container is not None, "Value container should not be None"

            numeric_value = extract_numeric_value_from_component(value_container)
            assert numeric_value is not None, (
                f"Could not extract numeric value from {value_container}"
            )

            assert round(numeric_value, 1) == round(float(value), 1), (
                f"Value {numeric_value} should be rounded to {round(float(value), 1)}"
            )

            formatted_value = str(value_container)
            expected_format = f"{float(value):.1f}"
            assert expected_format in formatted_value, (
                f"Value {value} should be formatted as {expected_format}, "
                f"not found in {formatted_value}"
            )

    def test_end_to_end_metrics_flow(self, sample_dataframe):

        avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
            sample_dataframe.to_dict("records")
        )

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

        assert abs(metrics_data["avg_weekly_items"] - avg_items) < 0.01
        assert abs(metrics_data["avg_weekly_points"] - avg_points) < 0.01
        assert abs(metrics_data["med_weekly_items"] - med_items) < 0.01
        assert abs(metrics_data["med_weekly_points"] - med_points) < 0.01
        if "avg_weekly_items_str" in metrics_data:
            formatted_avg_items = metrics_data["avg_weekly_items_str"]
            if "." in formatted_avg_items:
                assert formatted_avg_items.replace(".", "").isdigit(), (
                    f"Formatted value {formatted_avg_items} should be a valid number"
                )
