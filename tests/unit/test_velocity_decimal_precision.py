import re

import pandas as pd
import pytest

from data.processing import calculate_weekly_averages
from tests.utils.ui_test_helpers import (
    extract_formatted_value_from_component,
    validate_component_structure,
)
from ui.dashboard_cards import create_metric_card


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


class TestDecimalPrecision:
    def test_calculate_weekly_averages_precision(self, sample_velocity_data):
        avg_items, avg_points, med_items, med_points = calculate_weekly_averages(
            sample_velocity_data
        )

        assert isinstance(avg_items, float)
        assert isinstance(avg_points, float)
        assert isinstance(med_items, float)
        assert isinstance(med_points, float)

        assert round(avg_items, 2) == 8.72
        assert round(avg_points, 2) == 30.48
        assert round(med_items, 2) == 8.80
        assert round(med_points, 2) == 30.85


class TestUIComponentsFormatting:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (8.7, "8.70"),
            (7.0, "7.00"),
            (8.75, "8.75"),
            (9.99, "9.99"),
            (10, "10.00"),
            (0.1, "0.10"),
            (123.456, "123.46"),
        ],
    )
    def test_velocity_card_decimal_formatting(self, value, expected):
        metric_data = {
            "title": "Average",
            "value": value,
            "trend": 5,
            "trend_icon": "fas fa-arrow-up",
            "trend_color": "green",
            "color": "blue",
            "is_mini": False,
        }
        card = create_metric_card(metric_data)

        assert validate_component_structure(card, ["children"], min_children=2), (
            "Card should have a valid structure with at least 2 children"
        )

        formatted_value = None
        children = getattr(card, "children", None)
        if children is not None and len(children) > 1:
            value_container = children[1]
            if (
                hasattr(value_container, "children")
                and value_container.children is not None
            ):
                if hasattr(value_container.children, "children"):
                    formatted_value = value_container.children.children

        if not formatted_value:
            formatted_value = extract_formatted_value_from_component(
                children[1] if children is not None and len(children) > 1 else card,
                property_path=["children", "children"],
            )

        if not formatted_value:
            value_str = str(card)
            matches = re.findall(r"\d+\.\d+|\d+", value_str)
            if matches:
                formatted_value = matches[0]
                if "." not in formatted_value:
                    formatted_value += ".0"

        assert formatted_value is not None, (
            "Could not extract formatted value from card"
        )
        assert formatted_value == expected, (
            f"Value {value} should format as {expected}, got {formatted_value}"
        )

        assert formatted_value.count(".") <= 1, "Should have at most one decimal point"
        if "." in formatted_value:
            integer_part, decimal_part = formatted_value.split(".")
            assert len(decimal_part) == 2, (
                "Should have exactly two digits after decimal point"
            )
