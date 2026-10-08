from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from visualization.data_preparation import prepare_visualization_data


@pytest.fixture
def sample_dataframe():
    return pd.DataFrame(
        {
            "date": pd.date_range(start="2025-01-01", periods=10),
            "completed_items": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "completed_points": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
            "cum_items": [100, 90, 80, 70, 60, 50, 40, 30, 20, 10],
            "cum_points": [200, 180, 160, 140, 120, 100, 80, 60, 40, 20],
        }
    )


@pytest.fixture
def sample_dict_list():
    return [
        {
            "date": "2025-01-01",
            "completed_items": 1,
            "completed_points": 2,
            "cum_items": 100,
            "cum_points": 200,
        },
        {
            "date": "2025-01-02",
            "completed_items": 2,
            "completed_points": 4,
            "cum_items": 90,
            "cum_points": 180,
        },
        {
            "date": "2025-01-03",
            "completed_items": 3,
            "completed_points": 6,
            "cum_items": 80,
            "cum_points": 160,
        },
    ]


def test_prepare_visualization_data_with_dataframe(sample_dataframe):
    with (
        patch("visualization.data_preparation.calculate_rates") as mock_calculate_rates,
        patch(
            "visualization.data_preparation.compute_weekly_throughput"
        ) as mock_compute_weekly_throughput,
        patch(
            "visualization.data_preparation.daily_forecast_burnup"
        ) as mock_daily_forecast_burnup,
        patch(
            "visualization.data_preparation.generate_burndown_forecast"
        ) as mock_generate_burndown_forecast,
    ):
        mock_calculate_rates.return_value = (10.0, 1.0, 0.5, 20.0, 2.0, 1.0)

        mock_compute_weekly_throughput.return_value = pd.DataFrame(
            {
                "year_week": ["2025-1", "2025-2"],
                "completed_items": [10, 15],
                "completed_points": [20, 30],
            }
        )

        mock_daily_forecast_burnup.return_value = ([datetime.now()], [10.0])
        mock_generate_burndown_forecast.return_value = {
            "avg": ([datetime.now()], [10.0]),
            "opt": ([datetime.now()], [15.0]),
            "pes": ([datetime.now()], [5.0]),
        }

        result = prepare_visualization_data(
            sample_dataframe, total_items=100, total_points=200, pert_factor=3
        )

        args, kwargs = mock_calculate_rates.call_args
        assert isinstance(args[0], pd.DataFrame), (
            "calculate_rates should be called with a DataFrame"
        )

        assert isinstance(result, dict), "Result should be a dictionary"
        assert "df_calc" in result, "Result should contain df_calc key"
        assert "pert_time_items" in result, "Result should contain pert_time_items key"
        assert "items_forecasts" in result, "Result should contain items_forecasts key"
        assert "points_forecasts" in result, (
            "Result should contain points_forecasts key"
        )


def test_prepare_visualization_data_with_dict_list(sample_dict_list):
    with (
        patch("visualization.data_preparation.calculate_rates") as mock_calculate_rates,
        patch(
            "visualization.data_preparation.compute_weekly_throughput"
        ) as mock_compute_weekly_throughput,
        patch(
            "visualization.data_preparation.daily_forecast_burnup"
        ) as mock_daily_forecast_burnup,
        patch(
            "visualization.data_preparation.generate_burndown_forecast"
        ) as mock_generate_burndown_forecast,
    ):
        mock_calculate_rates.return_value = (10.0, 1.0, 0.5, 20.0, 2.0, 1.0)

        mock_compute_weekly_throughput.return_value = [
            {"year_week": "2025-1", "completed_items": 10, "completed_points": 20},
            {"year_week": "2025-2", "completed_items": 15, "completed_points": 30},
        ]

        mock_daily_forecast_burnup.return_value = ([datetime.now()], [10.0])
        mock_generate_burndown_forecast.return_value = {
            "avg": ([datetime.now()], [10.0]),
            "opt": ([datetime.now()], [15.0]),
            "pes": ([datetime.now()], [5.0]),
        }

        result = prepare_visualization_data(
            sample_dict_list, total_items=100, total_points=200, pert_factor=3
        )

        args, kwargs = mock_calculate_rates.call_args
        assert isinstance(args[0], pd.DataFrame), (
            "calculate_rates should be called with a DataFrame "
            "(converted from input list)"
        )

        assert isinstance(result, dict), "Result should be a dictionary"
        assert "df_calc" in result, "Result should contain df_calc key"
        assert "pert_time_items" in result, "Result should contain pert_time_items key"
        assert "items_forecasts" in result, "Result should contain items_forecasts key"
        assert "points_forecasts" in result, (
            "Result should contain points_forecasts key"
        )


def test_prepare_visualization_data_empty_input():
    result = prepare_visualization_data(
        pd.DataFrame(), total_items=100, total_points=200, pert_factor=3
    )

    assert isinstance(result, dict), "Result should be a dictionary"
    assert "df_calc" in result, "Result should contain df_calc key"
    assert "pert_time_items" in result, "Result should contain pert_time_items key"
    assert result["pert_time_items"] == 0, "pert_time_items should be 0 for empty input"
    assert "items_forecasts" in result, "Result should contain items_forecasts key"
    assert "points_forecasts" in result, "Result should contain points_forecasts key"
