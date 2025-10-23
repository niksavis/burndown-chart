"""
DEPRECATED - Callbacks for scope metrics.

⚠️ WARNING: This module is DEPRECATED and NO LONGER USED.

This module contained an orphaned callback that caused a critical bug where
scope change content would render in all tabs after the scope tab was first activated.

The callback depended on a non-existent 'forecast-data-store', causing it to fire
on every interaction once 'scope-dashboard-container' existed in the DOM.

CURRENT IMPLEMENTATION:
Scope metrics are now properly handled in callbacks/visualization.py via the
_create_scope_tracking_tab_content() function, which is called when the
tab-scope-tracking tab is active.

This file is kept for reference only and should NOT be registered in callbacks/__init__.py

See: docs/scope-change-tab-bug-fix.md for full details of the bug and fix.
"""

import pandas as pd
from dash.dependencies import Input, Output
from dash import html
from data.scope_metrics import (
    calculate_scope_creep_rate,
    calculate_weekly_scope_growth,
    calculate_scope_stability_index,
)
from data.schema import DEFAULT_SETTINGS  # Import DEFAULT_SETTINGS
from ui.scope_metrics import create_scope_metrics_dashboard

import logging

logger = logging.getLogger(__name__)


def register(app):
    """Register callbacks for scope metrics."""

    @app.callback(
        Output("scope-dashboard-container", "children"),
        [Input("forecast-data-store", "data"), Input("settings-store", "data")],
    )
    def update_scope_metrics_dashboard(stored_data, settings_data):
        """Update the scope metrics dashboard when data changes."""
        try:
            if not stored_data or "data" not in stored_data:
                return html.Div("No data available")

            data = pd.DataFrame(stored_data["data"])

            if data.empty:
                return html.Div("No data available")

            # Calculate the scope creep rate
            baseline_items = stored_data["baseline"]["items"]
            baseline_points = stored_data["baseline"]["points"]
            scope_creep_rate = calculate_scope_creep_rate(
                data, baseline_items, baseline_points
            )

            # Calculate weekly scope growth
            weekly_growth_data = calculate_weekly_scope_growth(data)

            # Calculate scope stability index
            stability_index = calculate_scope_stability_index(
                data, baseline_items, baseline_points
            )

            # Get scope creep threshold from settings or use default
            scope_creep_threshold = (
                settings_data.get(
                    "scope_creep_threshold", DEFAULT_SETTINGS["scope_creep_threshold"]
                )
                if settings_data
                else DEFAULT_SETTINGS["scope_creep_threshold"]
            )

            # Create the dashboard component
            return create_scope_metrics_dashboard(
                scope_creep_rate,
                weekly_growth_data,
                stability_index,
                scope_creep_threshold,
            )
        except Exception as e:
            logger.exception(f"Error updating scope metrics dashboard: {e}")
            return html.Div(f"Error updating scope metrics: {str(e)}")
