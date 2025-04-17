"""
Data Package

This package provides data processing and persistence utilities.
"""

from data.persistence import (
    load_settings,
    save_settings,
    load_statistics,
    save_statistics,
    generate_realistic_sample_data,
    read_and_clean_data,
)

from data.processing import (
    calculate_total_points,
    compute_cumulative_values,
    calculate_weekly_averages,
    prepare_forecast_data,
    generate_weekly_forecast,
    calculate_performance_trend,
)

# Define public API
__all__ = [
    "load_settings",
    "save_settings",
    "load_statistics",
    "save_statistics",
    "read_and_clean_data",
    "generate_realistic_sample_data",
    "calculate_total_points",
    "compute_cumulative_values",
    "calculate_weekly_averages",
    "prepare_forecast_data",
    "generate_weekly_forecast",
    "calculate_performance_trend",
]
