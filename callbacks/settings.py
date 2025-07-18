"""
Settings Callbacks Module

This module handles callbacks related to application settings and parameters.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from datetime import datetime

# Third-party library imports
import dash
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

# Application imports
from configuration import (
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_POINTS,
    logger,
)
from data import calculate_total_points, save_settings

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
            Input("milestone-toggle", "value"),  # Added milestone toggle input
            Input("milestone-picker", "date"),  # Added milestone picker input
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
        show_milestone,  # Added parameter
        milestone,  # Added parameter
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
            "show_milestone": show_milestone,  # Added to settings
            "milestone": milestone,  # Added to settings
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
            show_milestone,  # Added parameter
            milestone,  # Added parameter
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

    # Add a clientside callback for the PERT Factor slider to enhance tooltip behavior
    app.clientside_callback(
        """
        function(value) {
            // Format the info text based on the PERT Factor value
            let infoText = "";
            
            if (value <= 5) {
                infoText = "Low confidence range (value: " + value + ")";
            } else if (value <= 10) {
                infoText = "Medium confidence range (value: " + value + ")";
            } else {
                infoText = "High confidence range (value: " + value + ")";
            }
            
            // Also trigger slider tooltip display when slider is updated automatically
            const slider = document.getElementById('pert-factor-slider');
            if (slider) {
                // Force the tooltip to update its position and value
                const event = new Event('mousemove');
                slider.dispatchEvent(event);
            }
            
            return infoText;
        }
        """,
        dash.Output("pert-factor-info", "children"),
        [dash.Input("pert-factor-slider", "value")],
    )

    # Add a callback to enable/disable the milestone date picker based on toggle state
    @app.callback(
        Output("milestone-picker", "disabled"),
        Input("milestone-toggle", "value"),
    )
    def toggle_milestone_picker(show_milestone):
        """
        Enable or disable the milestone date picker based on the toggle state.

        Args:
            show_milestone: Boolean value from the milestone toggle switch

        Returns:
            Boolean: True if the picker should be disabled, False if it should be enabled
        """
        # When show_milestone is True, we want disabled to be False and vice versa
        return not show_milestone

    # JIRA Integration Callbacks
    @app.callback(
        Output("jira-config-container", "style"),
        Input("data-source-selection", "value"),
    )
    def toggle_jira_config(data_source):
        """
        Toggle visibility of JIRA configuration inputs based on data source selection.

        Args:
            data_source: Selected data source ("CSV" or "JIRA")

        Returns:
            Dict: Style dictionary to show/hide JIRA configuration
        """
        if data_source == "JIRA":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("csv-upload-container", "style"), Input("data-source-selection", "value")
    )
    def toggle_csv_upload(data_source):
        """
        Toggle visibility of CSV upload container based on data source selection.

        Args:
            data_source: Selected data source ("CSV" or "JIRA")

        Returns:
            Dict: Style dictionary to show/hide CSV upload container
        """
        if data_source == "CSV":
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        [
            Output("jira-cache-status", "children"),
            Output("jira-validation-errors", "children"),
        ],
        [
            Input("refresh-jira-cache", "n_clicks"),
            Input("jira-url", "value"),
            Input("jira-projects", "value"),
            Input("jira-date-from", "date"),
            Input("jira-date-to", "date"),
        ],
        prevent_initial_call=True,
    )
    def update_jira_cache_and_validation(n_clicks, url, projects, date_from, date_to):
        """
        Update JIRA cache and show validation errors.

        Args:
            n_clicks: Number of refresh button clicks
            url: JIRA URL
            projects: JIRA projects (comma-separated)
            date_from: Start date for JIRA query
            date_to: End date for JIRA query

        Returns:
            Tuple: (cache_status, validation_errors)
        """
        ctx = dash.callback_context

        # Initialize return values
        cache_status = ""
        validation_errors = ""

        try:
            from data.jira_simple import (
                get_cache_status,
                sync_jira_data,
                validate_jira_config,
                get_jira_config,
            )

            # Get current cache status
            cache_status = get_cache_status()

            # If refresh button was clicked, try to sync data
            if (
                n_clicks
                and ctx.triggered
                and ctx.triggered[0]["prop_id"] == "refresh-jira-cache.n_clicks"
            ):
                try:
                    # When refreshing, use environment variables + any UI overrides
                    config = get_jira_config()

                    # Apply UI overrides only if they have non-empty values
                    if date_from and date_from.strip():
                        config["date_from"] = date_from
                    if date_to and date_to.strip():
                        config["date_to"] = date_to
                    if url and url.strip():
                        config["url"] = url
                    if projects and projects.strip():
                        config["projects"] = [
                            p.strip() for p in projects.split(",") if p.strip()
                        ]

                    # Validate and sync with the merged config
                    is_valid, error_message = validate_jira_config(config)
                    if not is_valid:
                        validation_errors = html.Div(
                            [
                                html.I(className="fas fa-exclamation-triangle me-2"),
                                f"Configuration error: {error_message}",
                            ],
                            className="text-danger small",
                        )
                    else:
                        # Temporarily set the config for this sync
                        import os

                        original_env = {}
                        try:
                            # Backup original env vars
                            for key in [
                                "JIRA_URL",
                                "JIRA_PROJECTS",
                                "JIRA_DATE_FROM",
                                "JIRA_DATE_TO",
                            ]:
                                original_env[key] = os.environ.get(key)

                            # Set temporary env vars
                            os.environ["JIRA_URL"] = config["url"]
                            os.environ["JIRA_PROJECTS"] = ",".join(config["projects"])
                            os.environ["JIRA_DATE_FROM"] = config["date_from"]
                            os.environ["JIRA_DATE_TO"] = config["date_to"]

                            # Now sync
                            success, message = sync_jira_data()
                            if success:
                                cache_status = get_cache_status()
                                validation_errors = html.Div(
                                    [
                                        html.I(className="fas fa-check-circle me-2"),
                                        f"Cache refreshed successfully: {message}",
                                    ],
                                    className="text-success small",
                                )
                            else:
                                validation_errors = html.Div(
                                    [
                                        html.I(
                                            className="fas fa-exclamation-triangle me-2"
                                        ),
                                        f"Cache refresh failed: {message}",
                                    ],
                                    className="text-danger small",
                                )
                        finally:
                            # Restore original env vars
                            for key, value in original_env.items():
                                if value is not None:
                                    os.environ[key] = value
                                elif key in os.environ:
                                    del os.environ[key]
                except Exception as e:
                    validation_errors = html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Cache refresh failed: {str(e)}",
                        ],
                        className="text-danger small",
                    )
            else:
                # Only validate configuration if any inputs are provided AND not refreshing
                if url or projects or date_from or date_to:
                    # Start with the base config from environment variables
                    config = get_jira_config()

                    # Override with UI inputs if provided (only non-empty values)
                    if url:
                        config["url"] = url
                    if projects:
                        config["projects"] = [
                            p.strip() for p in projects.split(",") if p.strip()
                        ]
                    if date_from:
                        config["date_from"] = date_from
                    if date_to:
                        config["date_to"] = date_to

                    # Validate configuration
                    is_valid, error_message = validate_jira_config(config)
                    if not is_valid:
                        validation_errors = html.Div(
                            [
                                html.I(className="fas fa-exclamation-triangle me-2"),
                                f"Configuration error: {error_message}",
                            ],
                            className="text-danger small",
                        )

            # Format cache status for display
            if cache_status:
                cache_status_display = html.Div(
                    [
                        html.I(className="fas fa-database me-2"),
                        f"Cache: {cache_status}",
                    ],
                    className="text-muted small",
                )
            else:
                cache_status_display = html.Div(
                    [html.I(className="fas fa-database me-2"), "No cache available"],
                    className="text-muted small",
                )

            return (
                cache_status_display,
                validation_errors,
            )

        except ImportError:
            # JIRA integration not available
            return html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "JIRA integration not available",
                ],
                className="text-warning small",
            ), ""
        except Exception as e:
            logger.error(f"Error in JIRA cache callback: {e}")
            return html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error: {str(e)}",
                ],
                className="text-danger small",
            ), ""

    # Add a callback to trigger JIRA data loading when data source is selected
    @app.callback(
        Output("jira-data-loader", "data"),
        [
            Input("data-source-selection", "value"),
            Input("refresh-jira-cache", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def trigger_jira_data_loading(data_source, n_clicks):
        """
        Trigger JIRA data loading when data source is selected or cache is refreshed.

        Args:
            data_source: Selected data source ("CSV" or "JIRA")
            n_clicks: Number of refresh button clicks

        Returns:
            Trigger signal for JIRA data loading, updated statistics data, and timestamp
        """
        ctx = dash.callback_context

        # Only proceed if JIRA is selected
        if data_source != "JIRA":
            raise PreventUpdate

        try:
            from data.jira_simple import sync_jira_data
            from data.persistence import load_statistics

            # If refresh button was clicked, sync data first
            if (
                n_clicks
                and ctx.triggered
                and ctx.triggered[0]["prop_id"] == "refresh-jira-cache.n_clicks"
            ):
                success, message = sync_jira_data()
                if not success:
                    logger.error(f"Failed to sync JIRA data: {message}")
                    raise PreventUpdate

            # Load statistics (this will automatically load JIRA data if configured)
            statistics, _ = load_statistics()

            # Return timestamp to trigger other callbacks
            timestamp = int(datetime.now().timestamp() * 1000)
            return timestamp

        except ImportError:
            logger.error("JIRA integration not available")
            raise PreventUpdate
        except Exception as e:
            logger.error(f"Error loading JIRA data: {e}")
            raise PreventUpdate
