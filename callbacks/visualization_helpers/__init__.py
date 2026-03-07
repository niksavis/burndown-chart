"""
Visualization Helper Functions

This module contains helper functions extracted from visualization.py
to improve maintainability and adhere to the 500-line file limit.

All Dash callbacks remain in visualization.py for proper registration order.
"""

from callbacks.visualization_helpers.burndown_tab import _render_burndown_tab
from callbacks.visualization_helpers.dashboard_tab import _render_dashboard_tab
from callbacks.visualization_helpers.data_checks import (
    check_has_points_in_period,
    filter_df_by_week_labels,
)
from callbacks.visualization_helpers.extended_metrics import load_extended_metrics
from callbacks.visualization_helpers.pill_components import create_forecast_pill
from callbacks.visualization_helpers.tab_content import (
    create_burndown_tab_content,
    create_items_tab_content,
    create_points_tab_content,
    create_scope_tracking_tab_content,
)
from callbacks.visualization_helpers.trend_data import prepare_trend_data
from callbacks.visualization_helpers.ui_builders import (
    create_trend_header_with_forecasts,
)

__all__ = [
    "create_forecast_pill",
    "check_has_points_in_period",
    "filter_df_by_week_labels",
    "prepare_trend_data",
    "create_trend_header_with_forecasts",
    "create_burndown_tab_content",
    "create_items_tab_content",
    "create_points_tab_content",
    "create_scope_tracking_tab_content",
    "_render_dashboard_tab",
    "_render_burndown_tab",
    "load_extended_metrics",
]
