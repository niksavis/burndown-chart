"""
Trend Data Calculation Helpers

This module contains helper functions for preparing trend indicators
and forecast data for visualizations.
"""

import pandas as pd

from data import (
    calculate_performance_trend,
    generate_weekly_forecast,
)


def prepare_trend_data(
    statistics: list | pd.DataFrame,
    pert_factor: int | float,
    data_points_count: int | None = None,
) -> tuple[dict, dict]:
    """
    Prepare trend and forecast data for visualizations.

    Args:
        statistics: Statistics data (list or DataFrame)
        pert_factor: PERT factor for forecasts (typically 1-5)
        data_points_count: Number of data points to use for calculations
            (None = all data)

    Returns:
        tuple: (items_trend, points_trend) dictionaries with trend and forecast data

    Example:
        >>> items_trend, points_trend = prepare_trend_data(stats, 2.5, 12)
        >>> print(items_trend['value'])  # Current trend value
        >>> print(points_trend['optimistic_forecast'])  # Optimistic forecast
    """
    # Calculate trend indicators for items and points with filtering
    items_trend = calculate_performance_trend(
        statistics, "completed_items", 4, data_points_count=data_points_count
    )
    points_trend = calculate_performance_trend(
        statistics, "completed_points", 4, data_points_count=data_points_count
    )

    # Generate weekly forecast data if statistics available
    if statistics is not None and (
        isinstance(statistics, pd.DataFrame)
        and not statistics.empty
        or isinstance(statistics, list)
        and len(statistics) > 0
    ):
        forecast_data = generate_weekly_forecast(
            statistics, int(pert_factor), data_points_count=data_points_count
        )

        # Add forecast info to trend data if available
        if forecast_data:
            # Process items forecast data
            if "items" in forecast_data:
                if "optimistic_value" in forecast_data["items"]:
                    items_trend["optimistic_forecast"] = forecast_data["items"][
                        "optimistic_value"
                    ]
                if "most_likely_value" in forecast_data["items"]:
                    items_trend["most_likely_forecast"] = forecast_data["items"][
                        "most_likely_value"
                    ]
                if "pessimistic_value" in forecast_data["items"]:
                    items_trend["pessimistic_forecast"] = forecast_data["items"][
                        "pessimistic_value"
                    ]

            # Process points forecast data
            if "points" in forecast_data:
                if "optimistic_value" in forecast_data["points"]:
                    points_trend["optimistic_forecast"] = forecast_data["points"][
                        "optimistic_value"
                    ]
                if "most_likely_value" in forecast_data["points"]:
                    points_trend["most_likely_forecast"] = forecast_data["points"][
                        "most_likely_value"
                    ]
                if "pessimistic_value" in forecast_data["points"]:
                    points_trend["pessimistic_forecast"] = forecast_data["points"][
                        "pessimistic_value"
                    ]

    return items_trend, points_trend
