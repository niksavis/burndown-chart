"""Metrics calculation package for Flow and DORA metrics.

This package splits metrics calculations into focused modules:
- helpers: Utility functions (ISO week labels)
- forecast_calculator: Forecast and trend analysis
- weekly_calculator: Main weekly metrics calculation
- historical_calculator: Multi-week calculation orchestration
"""

from data.metrics.helpers import get_current_iso_week
from data.metrics.forecast_calculator import (
    calculate_forecast,
    calculate_trend_vs_forecast,
    calculate_flow_load_range,
)
from data.metrics.weekly_calculator import calculate_and_save_weekly_metrics
from data.metrics.historical_calculator import calculate_metrics_for_last_n_weeks

__all__ = [
    "get_current_iso_week",
    "calculate_forecast",
    "calculate_trend_vs_forecast",
    "calculate_flow_load_range",
    "calculate_and_save_weekly_metrics",
    "calculate_metrics_for_last_n_weeks",
]
