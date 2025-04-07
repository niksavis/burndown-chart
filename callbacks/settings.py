"""
Settings Callbacks Module

This module handles callbacks related to application settings and parameters.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash
from dash import html, Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime

# Import from application modules
from configuration import (
    logger,
    DEFAULT_TOTAL_POINTS,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
)
from data import save_settings, calculate_total_points

#######################################################################
# CALLBACKS
#######################################################################


def register(app):
    """
    Register all settings-related callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [
            Output("total-points-display", "value"),
            Output("points-calculation-info", "children"),
            Output("calculation-results", "data"),
        ],
        [
            Input("total-items-input", "value"),
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("current-statistics", "modified_timestamp"),
        ],
        [
            State("current-statistics", "data"),
            State("calculation-results", "data"),
        ],
    )
    def update_total_points_calculation(
        total_items,
        estimated_items,
        estimated_points,
        stats_ts,
        statistics,
        calc_results,
    ):
        """
        Update the total points calculation based on estimated items and points or historical data.
        """
        # Input validation
        if None in [total_items, estimated_items, estimated_points]:
            # Use .get() method for dictionary lookups - this is the Python idiomatic way
            return (
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.0f}",
                f"Using {calc_results.get('avg_points_per_item', 0):.1f} points per item for calculation",
                calc_results
                or {"total_points": DEFAULT_TOTAL_POINTS, "avg_points_per_item": 0},
            )

        # Handle invalid inputs by converting to numbers
        try:
            total_items = int(total_items)
            estimated_items = int(estimated_items)
            estimated_points = float(estimated_points)
        except (ValueError, TypeError):
            # Return previous values if conversion fails
            return (
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.0f}",
                f"Using {calc_results.get('avg_points_per_item', 0):.1f} points per item for calculation",
                calc_results
                or {"total_points": DEFAULT_TOTAL_POINTS, "avg_points_per_item": 0},
            )

        # Calculate total points and average
        estimated_total_points, avg_points_per_item = calculate_total_points(
            total_items, estimated_items, estimated_points, statistics
        )

        # Prepare info text with source of calculation and styling
        style = {"color": "inherit"}  # Default styling
        if estimated_items <= 0:
            info_text = f"Using {avg_points_per_item:.1f} points per item (based on historical data)"
        else:
            # If estimated items exceeds total, show a warning
            if estimated_items > total_items:
                info_text = (
                    f"Warning: Estimated items ({estimated_items}) exceeds total items ({total_items}). "
                    f"Using {avg_points_per_item:.1f} points per item."
                )
                style = {"color": "#dc3545"}  # Bootstrap danger red
            else:
                percent_estimated = (
                    (estimated_items / total_items) * 100 if total_items > 0 else 0
                )
                # Add confidence level based on percentage estimated
                confidence = "low"
                if percent_estimated >= 75:
                    confidence = "high"
                    style = {"color": "#28a745"}  # Bootstrap success green
                elif percent_estimated >= 30:
                    confidence = "medium"
                    style = {"color": "#ffc107"}  # Bootstrap warning yellow

                info_text = (
                    f"Using {avg_points_per_item:.1f} points per item "
                    f"({percent_estimated:.0f}% of items estimated, {confidence} confidence)"
                )

        # Update the calculation results store
        updated_calc_results = {
            "total_points": estimated_total_points,
            "avg_points_per_item": avg_points_per_item,
        }

        # Return with styled info text
        return (
            f"{estimated_total_points:.0f}",
            html.Span(info_text, style=style),
            updated_calc_results,
        )

    @app.callback(
        [
            Output("current-settings", "data"),
            Output("current-settings", "modified_timestamp"),
        ],
        [
            Input("pert-factor-slider", "value"),
            Input("deadline-picker", "date"),
            Input("total-items-input", "value"),
            Input("calculation-results", "data"),  # Use calculated total points
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
        ],
        [State("app-init-complete", "data")],
    )
    def update_and_save_settings(
        pert_factor,
        deadline,
        total_items,
        calc_results,
        estimated_items,
        estimated_points,
        init_complete,
    ):
        """
        Update current settings and save to disk when changed.
        """
        ctx = dash.callback_context

        # Skip if not initialized or values are None
        if (
            not init_complete
            or not ctx.triggered
            or None
            in [pert_factor, deadline, total_items, estimated_items, estimated_points]
        ):
            raise PreventUpdate

        # Get total points from calculation results
        total_points = calc_results.get("total_points", DEFAULT_TOTAL_POINTS)

        # Use consistent .get() pattern for all fallbacks
        input_values = {
            "estimated_items": estimated_items,
            "estimated_points": estimated_points,
        }
        estimated_items = input_values.get("estimated_items", DEFAULT_ESTIMATED_ITEMS)
        estimated_points = input_values.get(
            "estimated_points", DEFAULT_ESTIMATED_POINTS
        )

        # Create updated settings
        settings = {
            "pert_factor": pert_factor,
            "deadline": deadline,
            "total_items": total_items,
            "total_points": total_points,
            "estimated_items": estimated_items,
            "estimated_points": estimated_points,
        }

        # Save to disk
        save_settings(
            pert_factor,
            deadline,
            total_items,
            total_points,
            estimated_items,
            estimated_points,
        )

        logger.info(f"Settings updated and saved: {settings}")
        return settings, int(datetime.now().timestamp() * 1000)
