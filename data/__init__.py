"""
Data Package

This package provides data processing and persistence utilities.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# None

# Third-party library imports
# None

# Application imports
from data.persistence import (
    generate_realistic_sample_data,
    load_settings,
    load_statistics,
    read_and_clean_data,
    save_settings,
    save_statistics,
)
from data.processing import (
    calculate_performance_trend,
    calculate_total_points,
    calculate_weekly_averages,
    compute_cumulative_values,
    generate_weekly_forecast,
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
    "generate_weekly_forecast",
    "calculate_performance_trend",
]
