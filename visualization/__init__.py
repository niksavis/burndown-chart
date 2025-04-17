"""
Visualization Package

This package provides chart creation and visualization utilities.
"""

from visualization.charts import (
    create_forecast_plot,
    create_weekly_items_chart,
    create_weekly_points_chart,
    create_combined_weekly_chart,
    create_weekly_items_forecast_chart,
    create_weekly_points_forecast_chart,
)

from visualization.elements import (
    create_historical_trace,
    create_forecast_trace,
    add_deadline_marker,
    add_metric_annotation,
    empty_figure,
)

# Define public API
__all__ = [
    "create_forecast_plot",
    "create_weekly_items_chart",
    "create_weekly_points_chart",
    "create_combined_weekly_chart",
    "create_weekly_items_forecast_chart",
    "create_weekly_points_forecast_chart",
    "create_historical_trace",
    "create_forecast_trace",
    "add_deadline_marker",
    "add_metric_annotation",
    "empty_figure",
]
