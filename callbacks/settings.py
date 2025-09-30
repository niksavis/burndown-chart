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
from dash import Input, Output, State, html, no_update
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
            Input("jira-jql-query", "value"),
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
            Input("jira-jql-query", "value"),
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
            State("jira-jql-query", "value"),
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
                    sync_jira_data,
                    get_cache_status,
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
            State("jira-jql-query", "value"),
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
                        status_message = f"⚠️ Points field '{story_points_field.strip()}' not found or no meaningful point values. Only total item count ({total_items}) calculated. Configure a valid points field for full scope calculation."
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
