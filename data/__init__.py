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
# NOTE: Persistence adapters are NOT imported here to avoid circular imports
# Import them directly where needed: from data.persistence.adapters import ...
from data.processing import (
    calculate_performance_trend,
    calculate_total_points,
    calculate_weekly_averages,
    compute_cumulative_values,
    generate_weekly_forecast,
)

# Define public API
__all__ = [
    "calculate_total_points",
    "compute_cumulative_values",
    "calculate_weekly_averages",
    "generate_weekly_forecast",
    "calculate_performance_trend",
]
