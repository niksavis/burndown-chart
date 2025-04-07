"""
Data Package

This package provides data persistence and processing functionality.
"""

# Data persistence
from data.persistence import (
    load_settings,
    save_settings,
    load_statistics,
    save_statistics,
)

# Data processing
from data.processing import (
    calculate_total_points,
    read_and_clean_data,
    compute_cumulative_values,
    calculate_weekly_averages,
    prepare_forecast_data,
)

# Define public API
__all__ = [
    "load_settings",
    "save_settings",
    "load_statistics",
    "save_statistics",
    "calculate_total_points",
    "read_and_clean_data",
    "compute_cumulative_values",
    "calculate_weekly_averages",
    "prepare_forecast_data",
]
