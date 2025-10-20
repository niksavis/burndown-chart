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
from dash import Input, Output, State, callback_context, html, no_update
from dash.exceptions import PreventUpdate

# Application imports
from configuration import (
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_POINTS,
    logger,
)
from data import calculate_total_points

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

        # Calculate total points and average - use_fallback=False to respect user's explicit input
        estimated_total_points, avg_points_per_item = calculate_total_points(
            total_items,
            estimated_items,
            estimated_points,
            statistics,
            use_fallback=False,
        )

        # Prepare info text with source of calculation and styling
        style = {"color": "inherit"}  # Default styling
        if estimated_items <= 0:
            if estimated_items == 0 and estimated_points == 0:
                info_text = "No estimates provided - total points set to 0"
            else:
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
            Input("points-toggle", "value"),  # Added points toggle input
            # Add all JIRA inputs for immediate saving
            Input(
                "jira-jql-query", "data"
            ),  # Note: JQL editor uses dcc.Store with 'data' property
            Input("jira-url", "value"),
            Input("jira-token", "value"),
            Input("jira-story-points-field", "value"),
            Input("jira-cache-max-size", "value"),
            Input("jira-max-results", "value"),
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
        show_points,  # Added parameter
        # Add all JIRA parameters for immediate saving
        jql_query,
        jira_api_endpoint,
        jira_token,
        jira_story_points_field,
        jira_cache_max_size,
        jira_max_results,
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
            "show_points": show_points,  # Added to settings
        }

        # Save app-level settings - use current JIRA input values for immediate persistence
        from data.persistence import save_app_settings

        save_app_settings(
            pert_factor,
            deadline,
            data_points_count,  # Added parameter
            show_milestone,  # Added parameter
            milestone,  # Added parameter
            show_points,  # Added parameter
            jql_query.strip()
            if jql_query and jql_query.strip()
            else "project = JRASERVER",  # Use current JQL input
            jira_api_endpoint.strip()
            if jira_api_endpoint and jira_api_endpoint.strip()
            else "https://jira.atlassian.com/rest/api/2/search",  # Use current JIRA API endpoint input
            jira_token.strip() if jira_token else "",  # Use current JIRA token input
            jira_story_points_field.strip()
            if jira_story_points_field
            else "",  # Use current story points field input
            jira_cache_max_size
            if jira_cache_max_size is not None
            else 100,  # Use current cache size input
            jira_max_results
            if jira_max_results is not None
            else 1000,  # Use current max results input
        )

        # Save project data using unified format
        from data.persistence import load_unified_project_data, update_project_scope

        # Get current unified data to check if it's from JIRA
        unified_data = load_unified_project_data()
        data_source = unified_data.get("metadata", {}).get("source", "")

        # Only update project scope if it's NOT from JIRA (to avoid overriding JIRA data)
        if data_source != "jira_calculated":
            update_project_scope(
                {
                    "total_items": total_items,
                    "total_points": total_points,
                    "estimated_items": estimated_items,
                    "estimated_points": estimated_points,
                    "remaining_items": total_items,  # Default assumption for manual data
                    "remaining_points": total_points,
                }
            )
        else:
            # CRITICAL FIX: If data is from JIRA, DO NOT override any JIRA-calculated values
            # The estimation fields should only be updated through JIRA scope calculation, not UI inputs
            logger.info(
                "Preserving JIRA project scope data - UI input changes do not override JIRA calculations"
            )
            # JIRA project scope should ONLY be updated by JIRA operations, never by UI inputs

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
        [
            Output("pert-factor-slider", "min"),
            Output("pert-factor-slider", "max"),
            Output("pert-factor-slider", "marks"),
            Output("pert-factor-slider", "value"),
        ],
        [
            Input("statistics-table", "data"),
        ],
        [State("pert-factor-slider", "value")],
    )
    def update_pert_factor_constraints(statistics_data, current_pert_factor):
        """
        Update the max constraint and marks for the PERT factor slider based on available data points.
        PERT Factor maximum should be floor(available_data_points / 2) to ensure minimum 2x constraint.

        Args:
            statistics_data: Current statistics data
            current_pert_factor: Current PERT factor value

        Returns:
            Tuple of (max_value, marks, adjusted_value)
        """
        if current_pert_factor is None:
            current_pert_factor = DEFAULT_PERT_FACTOR

        # Calculate minimum and maximum PERT factor based on available data points
        max_data_points = len(statistics_data) if statistics_data else 6

        # Calculate minimum PERT factor
        min_pert_factor = 1 if max_data_points < 6 else 3

        # Calculate maximum PERT factor to ensure 2x constraint is always satisfied
        # PERT_Factor × 2 ≤ available_data_points
        # Therefore: PERT_Factor ≤ floor(available_data_points / 2)
        max_pert_factor = max_data_points // 2

        # Ensure minimum PERT factor of 1 (never 0)
        max_pert_factor = max(min_pert_factor, max_pert_factor)

        # For datasets with 6+ data points, ensure PERT factor is at least 3 for meaningful analysis
        if max_data_points >= 6:
            max_pert_factor = max(3, max_pert_factor)

        # Cap at reasonable maximum (15) for performance
        max_pert_factor = min(max_pert_factor, 15)

        # Create marks for the slider
        marks = {}
        start_val = min_pert_factor

        # Create a reasonable number of marks based on the range
        range_size = max_pert_factor - start_val
        if range_size <= 5:
            # Small range - show all values
            for i in range(start_val, max_pert_factor + 1):
                marks[i] = {"label": str(i)}
        else:
            # Larger range - show key values
            step = max(1, range_size // 4)
            for i in range(start_val, max_pert_factor + 1, step):
                marks[i] = {"label": str(i)}

        # Always include start value and maximum value in marks
        marks[start_val] = {"label": str(start_val)}
        marks[max_pert_factor] = {"label": str(max_pert_factor)}

        # Adjust current value if it exceeds the new maximum or is below new minimum
        adjusted_value = max(min_pert_factor, min(current_pert_factor, max_pert_factor))

        # Log the constraint adjustment for debugging
        if adjusted_value != current_pert_factor:
            logger.info(
                f"Adjusting PERT factor from {current_pert_factor} to {adjusted_value} "
                f"(max data points: {max_data_points}, PERT factor range: {min_pert_factor}-{max_pert_factor})"
            )

        return min_pert_factor, max_pert_factor, marks, adjusted_value

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
        Output("data-points-info", "children"),
        [
            Input("data-points-input", "value"),
            Input("data-points-input", "min"),
            Input("data-points-input", "max"),
        ],
    )

    # Add a clientside callback for the PERT Factor slider to enhance tooltip behavior and show constraints
    app.clientside_callback(
        """
        function(value, max_value, statistics_data) {
            // Format the info text based on the PERT Factor value and constraints
            let infoText = "";
            const dataPoints = statistics_data ? statistics_data.length : 0;
            
            if (dataPoints === 0) {
                infoText = "No data available - PERT Factor: " + value;
            } else if (value === max_value && max_value < 15) {
                infoText = "Maximum PERT Factor for " + dataPoints + " data points (value: " + value + ")";
            } else if (value <= 5) {
                infoText = "Narrow confidence range - more responsive (value: " + value + ")";
            } else if (value <= 10) {
                infoText = "Medium confidence range - balanced (value: " + value + ")";
            } else {
                infoText = "Wide confidence range - more stable (value: " + value + ")";
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
        Output("pert-factor-info", "children"),
        [
            Input("pert-factor-slider", "value"),
            Input("pert-factor-slider", "max"),
            Input("statistics-table", "data"),
        ],
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

    @app.callback(
        Output("points-inputs-container", "style"),
        Input("points-toggle", "value"),
    )
    def toggle_points_inputs_container(show_points):
        """
        Show or hide the points inputs container based on the toggle state.

        Args:
            show_points: Boolean value from the points toggle switch

        Returns:
            Dict: Style dictionary to show/hide points inputs container
        """
        return {"display": "block" if show_points else "none"}

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
            Input("jira-url", "value"),
            Input(
                "jira-jql-query", "data"
            ),  # Note: JQL editor uses dcc.Store with 'data' property
        ],
        [
            State("jira-token", "value"),
            State("jira-story-points-field", "value"),
            State("jira-cache-max-size", "value"),
            State("jira-max-results", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_jira_cache_and_validation(
        api_endpoint,
        jql_query,
        jira_token,
        story_points_field,
        cache_max_size,
        jira_max_results,
    ):
        """
        Update JIRA cache status and show validation information.

        Args:
            api_endpoint: JIRA API endpoint URL
            jql_query: JQL query for filtering issues
            jira_token: Personal access token
            story_points_field: Custom field ID for story points mapping (optional)
            cache_max_size: Maximum cache size in MB

        Returns:
            Tuple containing cache status and validation errors
        """
        # Initialize return values
        cache_status = ""
        validation_errors = ""

        try:
            from data.jira_simple import (
                get_cache_status,
                validate_jira_config,
            )

            # Get current cache status
            cache_status = get_cache_status()

            # Create JIRA config from UI inputs (same logic as unified button)
            jira_config = {
                "api_endpoint": api_endpoint
                or "https://jira.atlassian.com/rest/api/2/search",
                "jql_query": jql_query or "project = JRASERVER",
                "token": jira_token or "",
                "story_points_field": story_points_field.strip()
                if story_points_field and story_points_field.strip()
                else "",
                "cache_max_size_mb": cache_max_size or 100,
            }

            # Show current validation status using UI config
            is_valid, error_message = validate_jira_config(jira_config)

            if is_valid:
                validation_errors = html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        "JIRA configuration is valid",
                    ],
                    className="text-success small",
                )
            else:
                validation_errors = html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        f"Configuration invalid: {error_message}",
                    ],
                    className="text-warning small",
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
        [
            Output("jira-data-loader", "data"),
            Output("jira-data-reload-trigger", "data"),
        ],
        [
            Input("data-source-selection", "value"),
        ],
        prevent_initial_call=True,
    )
    def trigger_jira_data_loading(data_source):
        """
        Trigger JIRA data loading when data source is selected.
        Also trigger a reload of statistics data.

        Args:
            data_source: Selected data source ("CSV" or "JIRA")

        Returns:
            Tuple: (timestamp, reload_trigger)
        """
        # Only proceed for data source selection if JIRA is selected
        if data_source == "JIRA":
            # Return timestamp to trigger other callbacks
            timestamp = int(datetime.now().timestamp() * 1000)
            return timestamp, timestamp
        else:
            # If data source is not JIRA, prevent update
            raise PreventUpdate

    @app.callback(
        [
            Output("upload-data", "contents", allow_duplicate=True),
            Output("upload-data", "filename", allow_duplicate=True),
            Output("jira-cache-status", "children", allow_duplicate=True),
            Output("jira-validation-errors", "children", allow_duplicate=True),
            Output("statistics-table", "data", allow_duplicate=True),
        ],
        [Input("update-data-unified", "n_clicks")],
        [
            State("data-source-selection", "value"),
            State(
                "jira-jql-query", "data"
            ),  # Note: JQL editor uses dcc.Store with 'data' property
            State("jira-url", "value"),
            State("jira-token", "value"),
            State("jira-story-points-field", "value"),
            State("jira-cache-max-size", "value"),
            State("jira-max-results", "value"),
        ],
        prevent_initial_call=True,
    )
    def handle_unified_data_update(
        n_clicks,
        data_source,
        jql_query,
        jira_api_endpoint,
        jira_token,
        story_points_field,
        cache_max_size,
        jira_max_results,
    ):
        """
        Handle unified data update button click.
        Routes to appropriate handler based on selected data source.

        Args:
            n_clicks (int): Number of clicks on unified update button
            data_source (str): Selected data source ("CSV" or "JIRA")
            jql_query (str): JQL query for JIRA data source
            jira_api_endpoint (str): JIRA API endpoint URL
            jira_token (str): Personal access token
            story_points_field (str): Custom field ID for story points mapping (optional)
            cache_max_size (int): Maximum cache size in MB

        Returns:
            Tuple: Upload contents, filename, cache status, validation errors
        """
        if not n_clicks:
            raise PreventUpdate

        try:
            if data_source == "JIRA":
                # Handle JIRA data import
                from data.jira_simple import (
                    get_cache_status,
                    sync_jira_data,
                    validate_jira_config,
                )
                from data.persistence import load_app_settings

                # Use JQL query from input or fall back to settings
                app_settings = load_app_settings()
                settings_jql = (
                    jql_query.strip()
                    if jql_query and jql_query.strip()
                    else app_settings.get("jql_query", "project = JRASERVER")
                )

                logger.info(
                    f"JQL Query - Input: '{jql_query}', Settings: '{app_settings.get('jql_query', 'N/A')}', Final: '{settings_jql}'"
                )

                # Process and clean JIRA configuration inputs
                final_jira_api_endpoint = (
                    jira_api_endpoint.strip()
                    if jira_api_endpoint and jira_api_endpoint.strip()
                    else "https://jira.atlassian.com/rest/api/2/search"
                )
                final_jira_token = jira_token.strip() if jira_token else ""
                final_story_points_field = (
                    story_points_field.strip() if story_points_field else ""
                )
                final_cache_max_size = (
                    cache_max_size if cache_max_size and cache_max_size > 0 else 100
                )
                final_max_results = (
                    jira_max_results
                    if jira_max_results and jira_max_results > 0
                    else 1000
                )

                # Check if any JIRA settings have changed and need saving
                settings_changed = (
                    settings_jql != app_settings.get("jql_query", "project = JRASERVER")
                    or final_jira_api_endpoint
                    != app_settings.get(
                        "jira_api_endpoint",
                        "https://jira.atlassian.com/rest/api/2/search",
                    )
                    or final_jira_token != app_settings.get("jira_token", "")
                    or final_story_points_field
                    != app_settings.get("jira_story_points_field", "")
                    or final_cache_max_size
                    != app_settings.get("jira_cache_max_size", 100)
                    or final_max_results != app_settings.get("jira_max_results", 1000)
                )

                if settings_changed:
                    from data.persistence import save_app_settings

                    save_app_settings(
                        app_settings["pert_factor"],
                        app_settings["deadline"],
                        app_settings["data_points_count"],
                        app_settings["show_milestone"],
                        app_settings["milestone"],
                        app_settings["show_points"],
                        settings_jql,
                        final_jira_api_endpoint,
                        final_jira_token,
                        final_story_points_field,
                        final_cache_max_size,
                        final_max_results,  # Use current UI input
                    )
                    logger.info(
                        f"JIRA configuration updated and saved: JQL='{settings_jql}', API Endpoint='{final_jira_api_endpoint}', Points Field='{final_story_points_field}', Cache Size={final_cache_max_size}, Max Results={final_max_results}"
                    )

                # Create JIRA config from UI inputs (override environment/settings)
                jira_config = {
                    "api_endpoint": final_jira_api_endpoint,
                    "jql_query": settings_jql,
                    "token": final_jira_token,
                    "story_points_field": final_story_points_field,
                    "cache_max_size_mb": final_cache_max_size,
                    "max_results": final_max_results,
                }

                # Validate configuration
                is_valid, validation_message = validate_jira_config(jira_config)
                if not is_valid:
                    cache_status = get_cache_status()
                    validation_errors = html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Configuration invalid: {validation_message}",
                        ],
                        className="text-danger small",
                    )
                    return None, None, cache_status, validation_errors, no_update

                # Use sync_jira_data with the UI configuration
                success, message = sync_jira_data(settings_jql, jira_config)
                cache_status = get_cache_status()
                if success:
                    # Load the updated statistics data after JIRA import
                    from data.persistence import load_statistics

                    updated_statistics, _ = (
                        load_statistics()
                    )  # Unpack tuple, ignore is_sample flag

                    validation_errors = html.Div(
                        [
                            html.I(className="fas fa-check-circle me-2"),
                            f"JIRA data imported successfully: {message}",
                        ],
                        className="text-success small",
                    )
                    # Return updated statistics to refresh the table
                    return (
                        None,
                        None,
                        cache_status,
                        validation_errors,
                        updated_statistics,
                    )
                else:
                    validation_errors = html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            f"Failed to import JIRA data: {message}",
                        ],
                        className="text-danger small",
                    )
                    # Return no table update on failure
                    return None, None, cache_status, validation_errors, no_update

            elif data_source == "CSV":
                # For CSV data source, we need to trigger the file upload dialog
                # This is handled by the existing upload-data component
                # We can't programmatically trigger a file dialog, so we show a message
                validation_errors = html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "Please use the file upload area above to select your CSV file.",
                    ],
                    className="text-info small",
                )
                return None, None, None, validation_errors, no_update

            else:
                validation_errors = html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        "Please select a data source first.",
                    ],
                    className="text-warning small",
                )
                return None, None, None, validation_errors, no_update

        except ImportError:
            logger.error("JIRA integration not available")
            validation_errors = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "JIRA integration not available",
                ],
                className="text-danger small",
            )
            return None, None, None, validation_errors, no_update
        except Exception as e:
            logger.error(f"Error in unified data update: {e}")
            validation_errors = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error updating data: {str(e)}",
                ],
                className="text-danger small",
            )
            return None, None, None, validation_errors, no_update

    #######################################################################
    # JIRA SCOPE CALCULATION CALLBACK
    #######################################################################

    @app.callback(
        [
            Output("jira-scope-status", "children"),
            Output("jira-scope-update-time", "children"),
            Output("estimated-items-input", "value"),
            Output("total-items-input", "value"),
            Output("estimated-points-input", "value"),
        ],
        [Input("jira-scope-calculate-btn", "n_clicks")],
        [
            State(
                "jira-jql-query", "data"
            ),  # Note: JQL editor uses dcc.Store with 'data' property
            State("jira-url", "value"),
            State("jira-token", "value"),
            State("jira-story-points-field", "value"),
            State("jira-cache-max-size", "value"),
            State("jira-max-results", "value"),
        ],
        prevent_initial_call=True,
    )
    def calculate_jira_project_scope(
        n_clicks,
        jql_query,
        jira_api_endpoint,
        jira_token,
        story_points_field,
        cache_max_size,
        jira_max_results,
    ):
        """
        Calculate project scope based on JIRA issues using status categories.
        """
        if not n_clicks or n_clicks == 0:
            raise PreventUpdate

        try:
            from data.persistence import calculate_project_scope_from_jira

            # Build UI config from form inputs
            ui_config = {
                "jql_query": jql_query or "",
                "api_endpoint": jira_api_endpoint
                or "https://jira.atlassian.com/rest/api/2/search",
                "token": jira_token or "",
                "story_points_field": story_points_field.strip()
                if story_points_field
                else "",
                "cache_max_size_mb": int(cache_max_size) if cache_max_size else 50,
                "max_results": int(jira_max_results) if jira_max_results else 1000,
            }

            # Calculate project scope from JIRA (no saving to file!)
            success, message, scope_data = calculate_project_scope_from_jira(
                jql_query, ui_config
            )

            # Update timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if success:
                # Use the calculated scope values directly (no file loading!)
                project_scope = scope_data

                # Get the updated values for UI fields based on new calculation logic
                # Check if points field was available for proper calculations
                points_field_available = project_scope.get(
                    "points_field_available", False
                )

                if points_field_available:
                    # Use proper calculated values when points field is available
                    estimated_items = project_scope.get(
                        "estimated_items", 0
                    )  # Items with point values
                    total_items = project_scope.get(
                        "remaining_items", 0
                    )  # All remaining items
                    estimated_points = project_scope.get(
                        "estimated_points", 0
                    )  # Points from estimated items

                    status_message = f"Project scope calculated from JIRA with {estimated_items} estimated items out of {total_items} total remaining items."
                else:
                    # Fallback when points field is not available
                    estimated_items = 0  # Can't determine which items are estimated
                    total_items = project_scope.get(
                        "remaining_items", 0
                    )  # Still get total remaining
                    estimated_points = 0  # Can't determine estimated points

                    if story_points_field and story_points_field.strip():
                        # Get detailed field statistics from the scope calculation
                        field_name = story_points_field.strip()
                        metadata = project_scope.get("calculation_metadata", {})
                        field_stats = metadata.get("field_stats", {})

                        # Provide detailed explanation based on field statistics
                        sample_size = field_stats.get("sample_size", 0)
                        field_exists_count = field_stats.get("field_exists_count", 0)
                        valid_points_count = field_stats.get("valid_points_count", 0)

                        field_coverage = field_stats.get("field_coverage_percent", 0)

                        if field_exists_count == 0:
                            status_message = f"⚠️ Points field '{field_name}' not found in any JIRA issues. Only total item count ({total_items}) calculated. Check if '{field_name}' exists in your JIRA project and verify your JQL query includes issues with this field."
                        elif field_coverage < 50:
                            status_message = f"⚠️ Points field '{field_name}' has insufficient coverage ({field_coverage:.0f}% of issues have the field, need ≥50%). Found in {field_exists_count} of {sample_size} sample issues, with {valid_points_count} having point values. Only total item count ({total_items}) calculated. Consider refining your JQL query to include more issues with this field, or verify '{field_name}' is the correct custom field name."
                        else:
                            # This shouldn't happen if points_field_available is False, but just in case
                            status_message = f"⚠️ Points field '{field_name}' validation failed unexpectedly ({field_coverage:.0f}% coverage). Only total item count ({total_items}) calculated."
                    else:
                        status_message = f"⚠️ No points field configured. Only total item count ({total_items}) calculated. Configure a valid points field for full scope calculation."

                status_content = html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Span(
                            status_message,
                            className="text-success"
                            if points_field_available
                            else "text-warning",
                        ),
                    ],
                    className="mb-2",
                )
                time_content = html.Small(
                    f"Last updated: {current_time}", className="text-muted"
                )

                return (
                    status_content,
                    time_content,
                    estimated_items,
                    total_items,
                    estimated_points,
                )
            else:
                # On error, don't update the input fields (use no_update)
                status_content = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-danger"
                        ),
                        html.Span(f"Error: {message}", className="text-danger"),
                    ],
                    className="mb-2",
                )
                time_content = html.Small(
                    f"Last attempt: {current_time}", className="text-muted"
                )

                return (
                    status_content,
                    time_content,
                    no_update,
                    no_update,
                    no_update,
                )

        except Exception as e:
            logger.error(f"Error in JIRA scope calculation callback: {e}")
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            status_content = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                    html.Span(f"Unexpected error: {str(e)}", className="text-danger"),
                ],
                className="mb-2",
            )
            time_content = html.Small(f"Error at: {error_time}", className="text-muted")
            return status_content, time_content, no_update, no_update, no_update

    # Add clientside callbacks for button loading states
    # These callbacks use a simple approach that directly manages button states
    # without conflicting with existing Dash callback outputs

    app.clientside_callback(
        """
        function(n_clicks) {
            // Simple button state management for Update Data button
            if (n_clicks && n_clicks > 0) {
                setTimeout(function() {
                    const button = document.getElementById('update-data-unified');
                    if (button) {
                        const originalHTML = button.innerHTML;
                        const originalDisabled = button.disabled;
                        
                        // Set loading state
                        button.disabled = true;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
                        
                        // Reset after timeout or when operation completes
                        const resetButton = function() {
                            if (button && button.disabled) {
                                button.disabled = false;
                                button.innerHTML = '<i class="fas fa-sync-alt me-2"></i>Update Data';
                            }
                        };
                        
                        // Shorter timeout since operations complete quickly
                        setTimeout(resetButton, 8000);
                        
                        // Try to detect when operation completes by monitoring DOM changes
                        const observer = new MutationObserver(function(mutations) {
                            // Look for success/error messages in validation area
                            const validationArea = document.getElementById('jira-validation-errors');
                            if (validationArea) {
                                const content = validationArea.innerHTML.toLowerCase();
                                // Detect success, error, or completion messages
                                if (content.includes('successfully') || 
                                    content.includes('imported') || 
                                    content.includes('completed') ||
                                    content.includes('error') || 
                                    content.includes('failed')) {
                                    setTimeout(resetButton, 1000); // Reset 1 second after message appears
                                    observer.disconnect();
                                }
                            }
                        });
                        
                        const targetNode = document.getElementById('jira-validation-errors');
                        if (targetNode) {
                            observer.observe(targetNode, { childList: true, subtree: true });
                            // Also check immediately if message is already there
                            setTimeout(function() {
                                const content = targetNode.innerHTML.toLowerCase();
                                if (content.includes('successfully') || 
                                    content.includes('imported') || 
                                    content.includes('completed') ||
                                    content.includes('error') || 
                                    content.includes('failed')) {
                                    setTimeout(resetButton, 1000);
                                    observer.disconnect();
                                }
                            }, 1000);
                        }
                    }
                }, 50); // Small delay to ensure this runs after the click
            }
            return null; // Don't update any output
        }
        """,
        Output(
            "update-data-unified", "title"
        ),  # Use title as a safe output that won't conflict
        [Input("update-data-unified", "n_clicks")],
        prevent_initial_call=True,
    )

    app.clientside_callback(
        """
        function(n_clicks) {
            // Simple button state management for Calculate Scope button
            if (n_clicks && n_clicks > 0) {
                setTimeout(function() {
                    const button = document.getElementById('jira-scope-calculate-btn');
                    if (button) {
                        const originalHTML = button.innerHTML;
                        const originalDisabled = button.disabled;
                        
                        // Set loading state
                        button.disabled = true;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Calculating...';
                        
                        // Reset after timeout or when operation completes
                        const resetButton = function() {
                            if (button && button.disabled) {
                                button.disabled = false;
                                button.innerHTML = '<i class="fas fa-calculator me-2"></i>Calculate Scope';
                            }
                        };
                        
                        // Shorter timeout since operations complete quickly
                        setTimeout(resetButton, 8000);
                        
                        // Try to detect when operation completes by monitoring DOM changes
                        const observer = new MutationObserver(function(mutations) {
                            // Look for success/error messages in scope status area
                            const statusArea = document.getElementById('jira-scope-status');
                            if (statusArea) {
                                const content = statusArea.innerHTML.toLowerCase();
                                // Detect completion messages
                                if (content.includes('calculated') || 
                                    content.includes('error') || 
                                    content.includes('⚠️') ||
                                    content.includes('updated') ||
                                    content.includes('completed')) {
                                    setTimeout(resetButton, 1000); // Reset 1 second after completion
                                    observer.disconnect();
                                }
                            }
                        });
                        
                        const targetNode = document.getElementById('jira-scope-status');
                        if (targetNode) {
                            observer.observe(targetNode, { childList: true, subtree: true });
                            // Also check immediately if message is already there
                            setTimeout(function() {
                                const content = targetNode.innerHTML.toLowerCase();
                                if (content.includes('calculated') || 
                                    content.includes('error') || 
                                    content.includes('⚠️') ||
                                    content.includes('updated') ||
                                    content.includes('completed')) {
                                    setTimeout(resetButton, 1000);
                                    observer.disconnect();
                                }
                            }, 1000);
                        }
                    }
                }, 50); // Small delay to ensure this runs after the click
            }
            return null; // Don't update any output
        }
        """,
        Output(
            "jira-scope-calculate-btn", "title"
        ),  # Use title as a safe output that won't conflict
        [Input("jira-scope-calculate-btn", "n_clicks")],
        prevent_initial_call=True,
    )

    #######################################################################
    # JQL QUERY PROFILE MANAGEMENT CALLBACKS
    #######################################################################

    @app.callback(
        Output("save-jql-query-modal", "is_open"),
        Output("jql-preview-display", "children"),
        [
            Input("save-jql-query-button", "n_clicks"),
            Input("cancel-save-query-button", "n_clicks"),
            Input("confirm-save-query-button", "n_clicks"),
        ],
        [
            State("jira-jql-query", "data"),
            State("save-jql-query-modal", "is_open"),
        ],  # Note: JQL editor uses dcc.Store with 'data' property
        prevent_initial_call=True,
    )
    def handle_save_query_modal(
        save_clicks, cancel_clicks, confirm_clicks, jql_value, is_open
    ):
        """Handle opening and closing of the save query modal."""
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Open modal when save button clicked
        if trigger_id == "save-jql-query-button" and save_clicks:
            jql_preview = jql_value or "No JQL query entered"
            return True, jql_preview

        # Close modal when cancel or confirm clicked
        elif trigger_id in ["cancel-save-query-button", "confirm-save-query-button"]:
            return False, no_update

        raise PreventUpdate

    @app.callback(
        [
            Output("jira-query-profile-selector", "options"),
            Output(
                "jira-query-profile-selector-mobile", "options", allow_duplicate=True
            ),
            Output("query-name-input", "value"),
            Output("query-description-input", "value"),
            Output("query-name-validation", "children"),
            Output("query-name-validation", "style"),
        ],
        [Input("confirm-save-query-button", "n_clicks")],
        [
            State("query-name-input", "value"),
            State("query-description-input", "value"),
            State(
                "jira-jql-query", "data"
            ),  # Note: JQL editor uses dcc.Store with 'data' property
            State("save-query-set-default-checkbox", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_query_profile(
        save_clicks, query_name, description, jql_value, set_as_default
    ):
        """Save a new JQL query profile."""
        if not save_clicks:
            raise PreventUpdate

        # Validate inputs
        if not query_name or not query_name.strip():
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                "Query name is required",
                {"display": "block"},
            )

        if not jql_value or not jql_value.strip():
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                "JQL query cannot be empty",
                {"display": "block"},
            )

        try:
            from data.jira_query_manager import (
                load_query_profiles,
                set_default_query,
            )
            from data.jira_query_manager import (
                save_query_profile as save_profile_func,
            )

            # Save the profile
            saved_profile = save_profile_func(
                name=query_name.strip(),
                jql=jql_value.strip(),
                description=description.strip() if description else "",
            )

            # Set as default if checkbox is checked
            if set_as_default and saved_profile:
                set_default_query(saved_profile["id"])

            # Reload options
            updated_options = []
            profiles = load_query_profiles()
            for profile in profiles:
                label = profile["name"]
                if profile.get("is_default", False):
                    label += " ★"  # Add star indicator for default
                updated_options.append({"label": label, "value": profile["id"]})

            # Keep dropdown clean for saved queries only - no "New Query" option needed

            # Clear form and hide validation
            return (
                updated_options,  # Desktop dropdown
                updated_options,  # Mobile dropdown
                "",
                "",
                "",
                {"display": "none"},
            )

        except Exception as e:
            logger.error(f"Error saving query profile: {e}")
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                f"Error saving query: {str(e)}",
                {"display": "block"},
            )

    @app.callback(
        [
            # Desktop dropdown sync
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            # Mobile dropdown sync
            Output("jira-query-profile-selector-mobile", "value"),
            # Button visibility
            Output("edit-jql-query-button", "style"),
            Output("load-default-jql-query-button", "style"),
            Output("delete-jql-query-button", "style"),
            Output("delete-query-name", "children"),
        ],
        [
            Input("jira-query-profile-selector", "value"),
            Input("jira-query-profile-selector-mobile", "value"),
        ],
        prevent_initial_call=True,
    )
    def sync_dropdowns_and_show_buttons(desktop_profile_id, mobile_profile_id):
        """Sync both dropdowns and show/hide profile action buttons."""
        # Determine which dropdown triggered the change
        ctx = callback_context
        if not ctx.triggered:
            # Initial load - use desktop value
            selected_profile_id = desktop_profile_id
        else:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if trigger_id == "jira-query-profile-selector-mobile":
                selected_profile_id = mobile_profile_id
            else:
                selected_profile_id = desktop_profile_id

        logger.info(
            f"DEBUG: sync_dropdowns_and_show_buttons called with profile_id: {selected_profile_id}"
        )

        # Base button styles
        hidden_style = {"display": "none"}
        visible_style = {"display": "inline-block"}

        try:
            from data.jira_query_manager import get_default_query, load_query_profiles

            profiles = load_query_profiles()
            default_query = get_default_query()
            logger.info(
                f"DEBUG: Loaded {len(profiles)} profiles, has default: {default_query is not None}"
            )

            if not selected_profile_id:
                logger.info("DEBUG: No profile selected, hiding management buttons")
                return (
                    selected_profile_id,  # desktop dropdown
                    selected_profile_id,  # mobile dropdown
                    hidden_style,  # edit button
                    hidden_style,  # load default button
                    hidden_style,  # delete button
                    "",  # delete query name
                )

            selected_profile = next(
                (p for p in profiles if p["id"] == selected_profile_id), None
            )

            logger.info(
                f"DEBUG: Selected profile: {selected_profile['name'] if selected_profile else 'None'}"
            )

            if selected_profile:
                # User-created profile - show edit and delete buttons
                logger.info(
                    f"DEBUG: Showing buttons for user profile: {selected_profile['name']}"
                )

                # Show load default button if there's a default query that's not the current selection
                load_default_style = (
                    visible_style
                    if default_query and default_query.get("id") != selected_profile_id
                    else hidden_style
                )

                return (
                    selected_profile_id,  # desktop dropdown
                    selected_profile_id,  # mobile dropdown
                    visible_style,  # edit button
                    load_default_style,  # load default button
                    visible_style,  # delete button
                    selected_profile["name"],  # delete query name
                )
            else:
                # Profile not found - hide action buttons
                logger.info("DEBUG: Profile not found, hiding buttons")

                # Show load default button if there's a default query
                load_default_style = visible_style if default_query else hidden_style

                return (
                    selected_profile_id,  # desktop dropdown
                    selected_profile_id,  # mobile dropdown
                    hidden_style,  # edit button
                    load_default_style,  # load default button
                    hidden_style,  # delete button
                    "",  # delete query name
                )

        except Exception as e:
            logger.error(f"Error in sync_dropdowns_and_show_buttons: {e}")
            return (
                selected_profile_id,
                selected_profile_id,
                hidden_style,
                hidden_style,
                hidden_style,
                "",
            )

    @app.callback(
        Output("delete-jql-query-modal", "is_open"),
        [
            Input("delete-jql-query-button", "n_clicks"),
            Input("cancel-delete-query-button", "n_clicks"),
            Input("confirm-delete-query-button", "n_clicks"),
        ],
        [State("delete-jql-query-modal", "is_open")],
        prevent_initial_call=True,
    )
    def handle_delete_query_modal(
        delete_clicks, cancel_clicks, confirm_clicks, is_open
    ):
        """Handle opening and closing of the delete query modal."""
        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # Open modal when delete button clicked
        if trigger_id == "delete-jql-query-button" and delete_clicks:
            return True

        # Close modal when cancel or confirm clicked
        elif trigger_id in [
            "cancel-delete-query-button",
            "confirm-delete-query-button",
        ]:
            return False

        raise PreventUpdate

    @app.callback(
        Output("jira-query-profile-selector", "options", allow_duplicate=True),
        Output("jira-query-profile-selector", "value"),
        [Input("confirm-delete-query-button", "n_clicks")],
        [State("jira-query-profile-selector", "value")],
        prevent_initial_call=True,
    )
    def delete_query_profile(delete_clicks, current_profile_id):
        """Delete the selected query profile."""
        if not delete_clicks or not current_profile_id:
            raise PreventUpdate

        try:
            from data.jira_query_manager import (
                delete_query_profile,
                load_query_profiles,
            )

            # Delete the profile
            delete_query_profile(current_profile_id)

            # Reload options
            updated_options = []
            profiles = load_query_profiles()
            for profile in profiles:
                label = profile["name"]
                if profile.get("is_default", False):
                    label += " ★"  # Add star indicator for default
                updated_options.append({"label": label, "value": profile["id"]})

            # Keep dropdown clean for saved queries only

            # Set to first profile or None if none exist
            default_value = profiles[0]["id"] if profiles else None

            return updated_options, default_value

        except Exception as e:
            logger.error(f"Error deleting query profile: {e}")
            raise PreventUpdate

    @app.callback(
        Output(
            "jira-jql-query", "data"
        ),  # Note: JQL editor uses dcc.Store with 'data' property
        [Input("jira-query-profile-selector", "value")],
        prevent_initial_call=True,
    )
    def update_jql_from_profile(selected_profile_id):
        """Update JQL textarea when a profile is selected."""
        if not selected_profile_id:
            raise PreventUpdate

        try:
            from data.jira_query_manager import get_query_profile_by_id

            profile = get_query_profile_by_id(selected_profile_id)
            if profile:
                return profile["jql"]
            else:
                raise PreventUpdate

        except Exception as e:
            logger.error(f"Error loading profile JQL: {e}")
            raise PreventUpdate

    @app.callback(
        Output("query-profile-status", "children"),
        [
            Input("jira-query-profile-selector", "value"),
            Input("jira-query-profile-selector-mobile", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_query_status_message(desktop_value, mobile_value):
        """Update the query status message based on selected profile."""
        # Use whichever dropdown has a value (sync between desktop/mobile)
        selected_profile_id = desktop_value or mobile_value

        if not selected_profile_id:
            return ""  # Empty when no query is selected

        try:
            from data.jira_query_manager import get_query_profile_by_id

            profile = get_query_profile_by_id(selected_profile_id)
            if profile:
                status_text = f"📋 Using saved query: {profile['name']}"
                if profile.get("is_default", False):
                    status_text += " ⭐"
                return status_text
            else:
                return ""

        except Exception as e:
            logger.error(f"Error getting profile status: {e}")
            return ""

    @app.callback(
        [
            Output("edit-query-modal", "is_open"),
            Output("edit-query-name-input", "value"),
            Output("edit-query-description-input", "value"),
            Output("edit-query-jql-input", "value"),
            Output("edit-query-set-default-checkbox", "value"),
        ],
        [
            Input("edit-jql-query-button", "n_clicks"),
            Input("cancel-edit-query-button", "n_clicks"),
            Input("confirm-edit-query-button", "n_clicks"),
        ],
        [State("jira-query-profile-selector", "value")],
        prevent_initial_call=True,
    )
    def handle_edit_query_modal(
        edit_clicks, cancel_clicks, confirm_clicks, current_profile_id
    ):
        """Handle opening/closing edit query modal and populate fields."""
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "edit-jql-query-button":
            if not current_profile_id or current_profile_id == "custom":
                raise PreventUpdate

            try:
                from data.jira_query_manager import get_query_profile_by_id

                profile = get_query_profile_by_id(current_profile_id)
                if profile:
                    return (
                        True,
                        profile["name"],
                        profile.get("description", ""),
                        profile["jql"],
                        profile.get("is_default", False),
                    )
                else:
                    raise PreventUpdate

            except Exception as e:
                logger.error(f"Error loading profile for edit: {e}")
                raise PreventUpdate

        # Close modal when cancel or confirm clicked
        elif trigger_id in ["cancel-edit-query-button", "confirm-edit-query-button"]:
            return False, no_update, no_update, no_update, no_update

        raise PreventUpdate

    @app.callback(
        [
            Output("jira-query-profile-selector", "options", allow_duplicate=True),
            Output(
                "jira-query-profile-selector-mobile", "options", allow_duplicate=True
            ),
            Output("edit-query-name-validation", "children"),
            Output("edit-query-name-validation", "style"),
        ],
        [Input("confirm-edit-query-button", "n_clicks")],
        [
            State("edit-query-name-input", "value"),
            State("edit-query-description-input", "value"),
            State("edit-query-jql-input", "value"),
            State("jira-query-profile-selector", "value"),
            State("edit-query-set-default-checkbox", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_query_profile(
        edit_clicks,
        query_name,
        description,
        jql_value,
        current_profile_id,
        set_as_default,
    ):
        """Update existing JQL query profile."""
        if not edit_clicks or not current_profile_id or current_profile_id == "custom":
            raise PreventUpdate

        # Validate inputs
        if not query_name or not query_name.strip():
            return no_update, no_update, "Query name is required", {"display": "block"}

        if not jql_value or not jql_value.strip():
            return no_update, no_update, "JQL query is required", {"display": "block"}

        try:
            from data.jira_query_manager import (
                load_query_profiles,
                remove_default_query,
                save_query_profile,
                set_default_query,
            )

            # Update the profile
            updated_profile = save_query_profile(
                name=query_name.strip(),
                jql=jql_value.strip(),
                description=description.strip() if description else "",
                profile_id=current_profile_id,
            )

            if updated_profile:
                logger.info(f"Updated query profile: {updated_profile['name']}")

                # Handle default setting
                if set_as_default:
                    set_default_query(current_profile_id)
                else:
                    # If profile was default but checkbox is unchecked, remove default
                    profiles = load_query_profiles()
                    current_profile = next(
                        (p for p in profiles if p["id"] == current_profile_id), None
                    )
                    if current_profile and current_profile.get("is_default"):
                        remove_default_query()

                # Reload options
                updated_options = []
                profiles = load_query_profiles()
                for profile in profiles:
                    label = profile["name"]
                    if profile.get("is_default", False):
                        label += " ★"  # Add star indicator for default
                    updated_options.append({"label": label, "value": profile["id"]})

                # Keep dropdown clean for saved queries only

                return updated_options, updated_options, "", {"display": "none"}
            else:
                return (
                    no_update,
                    no_update,
                    "Failed to update query profile",
                    {"display": "block"},
                )

        except Exception as e:
            logger.error(f"Error updating query profile: {e}")
            return (
                no_update,
                no_update,
                "Error updating query profile",
                {"display": "block"},
            )

    @app.callback(
        [
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            Output(
                "jira-jql-query", "data", allow_duplicate=True
            ),  # Note: JQL editor uses dcc.Store with 'data' property
        ],
        [Input("load-default-jql-query-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def load_default_query(load_default_clicks):
        """Load the default query profile."""
        if not load_default_clicks:
            raise PreventUpdate

        try:
            from data.jira_query_manager import get_default_query

            default_query = get_default_query()
            if default_query:
                logger.info(f"Loading default query: {default_query['name']}")
                return default_query["id"], default_query["jql"]
            else:
                logger.warning("No default query found")
                raise PreventUpdate

        except Exception as e:
            logger.error(f"Error loading default query: {e}")
            raise PreventUpdate

    # JQL Character Count Callback (Feature 001-add-jql-query, TASK-108)
    @app.callback(
        Output("jira-jql-character-count-container", "children"),
        Input(
            "jira-jql-query", "data"
        ),  # Note: JQL editor uses dcc.Store with 'data' property
        prevent_initial_call=False,
    )
    def update_jql_character_count(jql_value):
        """
        Update character count display when JQL query changes.

        Per FR-002: Shows warning when approaching 1800 chars (JIRA's limit is 2000).
        Provides instant feedback without debouncing (updates are lightweight).

        Args:
            jql_value: Current JQL query text

        Returns:
            Updated character count display component
        """
        from ui.components import (
            count_jql_characters,
            create_character_count_display,
            should_show_character_warning,
        )

        if jql_value is None:
            jql_value = ""

        count = count_jql_characters(jql_value)
        warning = should_show_character_warning(jql_value)

        return create_character_count_display(count=count, warning=warning)
