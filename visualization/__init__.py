"""
Visualization Package

This package provides chart creation and visualization utilities.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# None

# Third-party library imports
# None

# Application imports
from visualization.charts import (
    create_forecast_plot,
    create_weekly_items_chart,
    create_weekly_items_forecast_chart,
    create_weekly_points_chart,
    create_weekly_points_forecast_chart,
    create_burnup_chart,
)
from visualization.elements import (
    add_deadline_marker,
    create_empty_figure,
    create_forecast_trace,
    create_historical_trace,
)
from visualization.helpers import (
    safe_numeric_convert,
    parse_deadline_milestone,
    get_weekly_metrics,
    calculate_forecast_completion_dates,
    prepare_metrics_data,
    generate_burndown_forecast,
    format_hover_template_fix,
    handle_forecast_error,
    identify_significant_scope_growth,
)

# Define public API
__all__ = [
    # Chart creation functions
    "create_forecast_plot",
    "create_weekly_items_chart",
    "create_weekly_points_chart",
    "create_weekly_items_forecast_chart",
    "create_weekly_points_forecast_chart",
    "create_burnup_chart",
    # Element creation functions
    "create_historical_trace",
    "create_forecast_trace",
    "add_deadline_marker",
    "create_empty_figure",
    # Helper functions
    "safe_numeric_convert",
    "parse_deadline_milestone",
    "get_weekly_metrics",
    "calculate_forecast_completion_dates",
    "prepare_metrics_data",
    "generate_burndown_forecast",
    "format_hover_template_fix",
    "handle_forecast_error",
    "identify_significant_scope_growth",
]
