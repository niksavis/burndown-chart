"""
Callbacks for scope creep metrics visualization.
"""

import pandas as pd
from dash import Input, Output, State, callback, html
import dash_bootstrap_components as dbc

from data.scope_metrics import (
    calculate_scope_creep_rate,
    calculate_weekly_scope_growth,
    calculate_scope_stability_index,
    check_scope_creep_threshold,
    calculate_total_project_scope,  # Import our new function
)
from ui.scope_metrics import create_scope_metrics_dashboard  # Updated import path


def register(app):
    """Register all callbacks related to scope metrics."""

    @app.callback(
        Output("scope-metrics-container", "children"),
        [
            Input("current-statistics", "modified_timestamp"),
            Input("current-settings", "modified_timestamp"),
        ],
        [State("current-statistics", "data"), State("current-settings", "data")],
    )
    def update_scope_metrics(stats_ts, settings_ts, statistics_data, settings_data):
        """Update scope metrics based on current statistics and settings."""
        if not statistics_data or not statistics_data.get("data"):
            # Return empty placeholder if no data
            return html.Div(
                "No data available. Please add statistics data.",
                className="text-center text-muted my-5",
            )

        # Get baseline values
        baseline = statistics_data.get("baseline", {})
        baseline_items = baseline.get("items", 0) or 0
        baseline_points = baseline.get("points", 0) or 0

        # Get threshold setting
        threshold = (
            settings_data.get("scope_creep_threshold", 15) if settings_data else 15
        )

        # Convert statistics to DataFrame
        df = pd.DataFrame(statistics_data["data"])

        if df.empty:
            # Return empty placeholder if DataFrame is empty
            return html.Div(
                "No data available. Please add statistics data.",
                className="text-center text-muted my-5",
            )

        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])

        # Get remaining items/points from settings
        remaining_items = settings_data.get("total_items", 34) if settings_data else 34
        remaining_points = (
            settings_data.get("total_points", 154) if settings_data else 154
        )

        # Calculate total project scope using our new function
        project_scope = calculate_total_project_scope(
            df, remaining_items, remaining_points
        )

        # Calculate metrics
        scope_creep_rate = calculate_scope_creep_rate(
            df, baseline_items, baseline_points
        )
        weekly_growth_data = calculate_weekly_scope_growth(df)
        stability_index = calculate_scope_stability_index(
            df, baseline_items, baseline_points
        )

        # Create dashboard component with project scope data
        dashboard = create_scope_metrics_dashboard(
            scope_creep_rate,
            weekly_growth_data,
            stability_index,
            threshold,
            project_scope["total_items"],
            project_scope["total_points"],
        )

        return dashboard
