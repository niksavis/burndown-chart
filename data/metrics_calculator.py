"""
Metrics Calculator for Flow and DORA Metrics

[DEPRECATED - Use data.metrics package instead]

This module is maintained for backward compatibility only.
All functionality has been moved to the data.metrics package:
- data.metrics.helpers: Utility functions
- data.metrics.forecast_calculator: Forecast and trend analysis
- data.metrics.weekly_calculator: Main weekly metrics calculation
- data.metrics.historical_calculator: Multi-week calculation

Created: October 31, 2025
Refactored: February 1, 2026 - Split into modular package
"""

# Re-export all functions for backward compatibility
from data.metrics import (
    get_current_iso_week,
    calculate_and_save_weekly_metrics,
    calculate_metrics_for_last_n_weeks,
    calculate_forecast,
    calculate_trend_vs_forecast,
    calculate_flow_load_range,
)

__all__ = [
    "get_current_iso_week",
    "calculate_and_save_weekly_metrics",
    "calculate_metrics_for_last_n_weeks",
    "calculate_forecast",
    "calculate_trend_vs_forecast",
    "calculate_flow_load_range",
]
