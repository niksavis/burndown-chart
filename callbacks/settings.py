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
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_POINTS,
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
)
from data import save_settings, calculate_total_points

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def get_data_points_info(value, min_val, max_val):
    """Helper function to generate info text about data points selection"""
    if min_val == max_val:
        return "Using all available data points"

    percent = (
        ((value - min_val) / (max_val - min_val) * 100) if max_val > min_val else 100
    )

    if value == min_val:
        return f"Using minimum data points ({value} points, most recent data only)"
    elif value == max_val:
        return f"Using all available data points ({value} points)"
    else:
        return (
            f"Using {value} most recent data points ({percent:.0f}% of available data)"
        )


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

    # REMOVED: The Python callback for data-points-info that was causing the duplicate output error
    # This functionality is now handled by the clientside callback below

    @app.callback(
        [
            Output("current-settings", "data"),
            Output("current-settings", "modified_timestamp"),
        ],
        [
            Input("pert-factor-slider", "value"),
            Input("deadline-picker", "date"),
            Input("total-items-input", "value"),
            Input("calculation-results", "data"),
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("data-points-input", "value"),  # Added data_points_count input
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
        data_points_count,  # Added parameter
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
            in [
                pert_factor,
                deadline,
                total_items,
                # Remove these from None check since we'll provide defaults
                # estimated_items,
                # estimated_points,
                data_points_count,  # Added check
            ]
        ):
            raise PreventUpdate

        # Get total points from calculation results
        total_points = calc_results.get("total_points", DEFAULT_TOTAL_POINTS)

        # Use consistent .get() pattern for all fallbacks - restored from previous implementation
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
            "data_points_count": data_points_count,  # Added to settings
        }

        # Save to disk
        save_settings(
            pert_factor,
            deadline,
            total_items,
            total_points,
            estimated_items,
            estimated_points,
            data_points_count,  # Added parameter
        )

        logger.info(f"Settings updated and saved: {settings}")
        return settings, int(datetime.now().timestamp() * 1000)

    @app.callback(
        [
            Output("data-points-input", "min"),
            Output("data-points-input", "max"),
            Output("data-points-input", "marks"),
        ],
        [
            Input("pert-factor-slider", "value"),
            Input("statistics-table", "data"),
        ],
    )
    def update_data_points_constraints(pert_factor, statistics_data):
        """
        Update the min, max constraints, and marks for the data points slider.
        """
        if pert_factor is None:
            pert_factor = DEFAULT_PERT_FACTOR

        min_value = pert_factor * 2
        max_value = len(statistics_data) if statistics_data else min_value

        # Ensure min doesn't exceed max
        min_value = min(min_value, max_value)

        # Calculate percentage positions
        range_size = max_value - min_value
        p25 = min_value + int(range_size * 0.25)
        p50 = min_value + int(range_size * 0.5)
        p75 = min_value + int(range_size * 0.75)

        # Create marks for min, 25%, 50%, 75%, and max
        marks = {}

        # Only add percentage marks if there's enough range
        if range_size > 3:
            marks = {
                min_value: {"label": str(min_value)},
                p25: {"label": str(p25)},
                p50: {"label": str(p50)},
                p75: {"label": str(p75)},
                max_value: {"label": str(max_value)},
            }
        else:
            # If range is small, just show min and max
            marks = {
                min_value: {"label": str(min_value)},
                max_value: {"label": str(max_value)},
            }

        return min_value, max_value, marks

    @app.callback(
        Output("data-points-input", "value"),
        [
            Input("pert-factor-slider", "value"),
            Input("data-points-input", "min"),
        ],
        [State("data-points-input", "value")],
    )
    def update_data_points_value(pert_factor, min_required, current_value):
        """
        Update the data points value when PERT factor changes, ensuring it's at least 2x the PERT Factor.

        Args:
            pert_factor: Current PERT factor value
            min_required: Minimum required data points (already calculated as 2x PERT Factor)
            current_value: Current value of the data points slider

        Returns:
            Updated value for the data points slider
        """
        if current_value is None or min_required is None:
            # Use safe default values
            return min_required or (pert_factor * 2 if pert_factor else 6)

        # Check if current value is below the new minimum
        if current_value < min_required:
            logger.info(
                f"Updating data points from {current_value} to minimum {min_required}"
            )
            return min_required

        # Current value is already valid
        return current_value

    # Add a clientside callback to enhance slider interactions and synchronize slider value with the displayed text
    app.clientside_callback(
        """
        function(value, min_value, max_value) {
            // Format the info text
            let infoText = "";
            
            if (min_value === max_value) {
                infoText = "Using all available data points (" + value + " points)";
            } else if (value === min_value) {
                infoText = "Using minimum data points (" + value + " points, most recent data only)";
            } else if (value === max_value) {
                infoText = "Using all available data points (" + value + " points)";
            } else {
                // Calculate percentage
                const percent = Math.round(((value - min_value) / (max_value - min_value)) * 100);
                infoText = "Using " + value + " most recent data points (" + percent + "% of available data)";
            }
            
            // Also trigger slider tooltip display when slider is updated automatically
            const slider = document.getElementById('data-points-input');
            if (slider) {
                // Force the tooltip to update its position and value
                const event = new Event('mousemove');
                slider.dispatchEvent(event);
            }
            
            return infoText;
        }
        """,
        dash.Output("data-points-info", "children"),
        [
            dash.Input("data-points-input", "value"),
            dash.Input("data-points-input", "min"),
            dash.Input("data-points-input", "max"),
        ],
    )
