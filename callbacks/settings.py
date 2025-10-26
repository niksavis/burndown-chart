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
import dash_bootstrap_components as dbc
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

        # Update the calculation results store
        updated_calc_results = {
            "total_points": estimated_total_points,
            "avg_points_per_item": avg_points_per_item,
        }

        # Return updated values
        return (
            f"{estimated_total_points:.0f}",
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
            Input("pert-factor-slider", "value"),  # Parameter panel PERT factor slider
            Input("deadline-picker", "date"),  # Parameter panel deadline
            Input("milestone-picker", "date"),  # Parameter panel milestone (no toggle)
            Input("total-items-input", "value"),
            Input("calculation-results", "data"),
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("data-points-input", "value"),  # Parameter panel data points slider
            Input("points-toggle", "value"),  # Parameter panel points toggle
        ],
        [
            State("app-init-complete", "data"),
            # PERFORMANCE FIX: Move JQL query to State to prevent callback on every keystroke
            State(
                "jira-jql-query", "value"
            ),  # JQL textarea - only read on other input changes
        ],
    )
    def update_and_save_settings(
        pert_factor,  # Parameter panel PERT factor slider
        deadline,  # Parameter panel deadline
        milestone,  # Parameter panel milestone (no toggle needed)
        total_items,
        calc_results,
        estimated_items,
        estimated_points,
        data_points_count,  # Parameter panel data points slider
        show_points,  # Parameter panel points toggle
        # State parameters (read but don't trigger callback)
        init_complete,
        jql_query,  # PERFORMANCE FIX: JQL query moved to State to prevent keystroke lag
    ):
        """
        Update current settings and save to disk when changed.
        Handles both legacy inputs (from old Input Parameters card) and new parameter panel inputs.
        """
        ctx = dash.callback_context

        # Use parameter panel values directly (no legacy inputs to merge)
        # Milestone logic: activated if a valid date is entered (no toggle needed)
        show_milestone = (
            milestone is not None
        )  # Simplified: True if milestone date exists

        # Skip if not initialized or critical values are None
        if (
            not init_complete
            or not ctx.triggered
            or None
            in [
                pert_factor,
                deadline,
                total_items,
                data_points_count,
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
            "data_points_count": data_points_count,
            "show_milestone": show_milestone,  # Automatically set based on milestone date
            "milestone": milestone,
            "show_points": show_points,
        }

        # Save app-level settings - load JIRA values from jira_config (Feature 003-jira-config-separation)
        from data.persistence import save_app_settings

        save_app_settings(
            pert_factor,
            deadline,
            data_points_count,
            show_milestone,  # Automatically calculated
            milestone,
            show_points,  # Added parameter
            jql_query.strip()
            if jql_query and jql_query.strip()
            else "project = JRASERVER",  # Use current JQL input
            # Note: JIRA configuration is now managed separately via save_jira_configuration()
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

    # REMOVED: Legacy data points constraints callback - not needed with new parameter panel

    # REMOVED: Legacy PERT factor constraints callback - not needed with new parameter panel

    # REMOVED: Legacy data points value callback - not needed with new parameter panel

    # REMOVED: Legacy data points info clientside callback - not needed with new parameter panel

    # REMOVED: Legacy PERT factor info clientside callback - not needed with new parameter panel

    # REMOVED: Legacy milestone picker callback - not needed with new parameter panel

    # REMOVED: points-inputs-container callback - not needed with new parameter panel

    # REMOVED: JIRA Integration callbacks for old UI - not needed with new layout

    # PERFORMANCE FIX: Removed real-time JIRA validation callback that was causing keystroke lag
    # Validation now happens only when user attempts to use JIRA connection (Update Data/Calculate Scope)
    # This eliminates the callback that was triggering on every JQL query keystroke

    # REMOVED: Obsolete callback for data-source-selection (component doesn't exist in current layout)
    # Data source selection was part of old UI design and has been removed
    # JIRA data loading is now triggered directly by the "Update Data" button

    @app.callback(
        [
            Output("upload-data", "contents", allow_duplicate=True),
            Output("upload-data", "filename", allow_duplicate=True),
            Output("jira-cache-status", "children", allow_duplicate=True),
            Output("statistics-table", "data", allow_duplicate=True),
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
        ],
        [Input("update-data-unified", "n_clicks")],
        [
            State(
                "jira-jql-query", "value"
            ),  # JQL textarea uses standard "value" property
        ],
        prevent_initial_call=True,
    )
    def handle_unified_data_update(
        n_clicks,
        jql_query,
    ):
        """
        Handle unified data update button click (JIRA data source only).

        Args:
            n_clicks (int): Number of clicks on unified update button
            jql_query (str): JQL query for JIRA data source

        Returns:
            Tuple: Upload contents, filename, cache status, statistics table data
        """
        if not n_clicks:
            raise PreventUpdate

        try:
            # Handle JIRA data import (settings panel only uses JIRA)
            from data.jira_simple import validate_jira_config
            from data.persistence import load_app_settings

            # CRITICAL DEBUG: Log what we receive from the Store
            logger.info(
                f"[UPDATE DATA] Received jql_query from Store: '{jql_query}' (type: {type(jql_query)})"
            )

            # Load JIRA configuration from jira_config
            from data.persistence import load_jira_configuration

            jira_config = load_jira_configuration()

            # Check if JIRA is configured (FR-018: Error handling for unconfigured state)
            # Token is optional for public JIRA servers
            is_configured = (
                jira_config.get("configured", False)
                and jira_config.get("base_url", "").strip() != ""
            )

            if not is_configured:
                cache_status_message = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-warning"
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "⚠️ JIRA is not configured.",
                                    className="fw-bold d-block mb-1",
                                ),
                                html.Span(
                                    "Please click the 'Configure JIRA' button above to set up your JIRA connection before fetching data.",
                                    className="small",
                                ),
                            ]
                        ),
                    ],
                    className="text-warning small mt-2",
                )
                logger.warning("Attempted to update data without JIRA configuration")
                return (
                    None,
                    None,
                    cache_status_message,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

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

            # Load JIRA configuration values from jira_config and construct endpoint
            from data.jira_simple import construct_jira_endpoint

            base_url = jira_config.get("base_url", "https://jira.atlassian.com")
            api_version = jira_config.get("api_version", "v2")
            final_jira_api_endpoint = construct_jira_endpoint(base_url, api_version)
            final_jira_token = jira_config.get("token", "")
            final_story_points_field = jira_config.get("points_field", "")
            final_cache_max_size = jira_config.get("cache_size_mb", 100)
            final_max_results = jira_config.get("max_results_per_call", 1000)

            # Check if JQL query has changed and needs saving
            jql_changed = settings_jql != app_settings.get(
                "jql_query", "project = JRASERVER"
            )

            if jql_changed:
                from data.persistence import save_app_settings

                save_app_settings(
                    app_settings["pert_factor"],
                    app_settings["deadline"],
                    app_settings["data_points_count"],
                    app_settings["show_milestone"],
                    app_settings["milestone"],
                    app_settings["show_points"],
                    settings_jql,
                )
                logger.info(f"JQL query updated and saved: JQL='{settings_jql}'")

            # Create JIRA config for sync_jira_data (using loaded values)
            jira_config_for_sync = {
                "api_endpoint": final_jira_api_endpoint,
                "jql_query": settings_jql,
                "token": final_jira_token,
                "story_points_field": final_story_points_field,
                "cache_max_size_mb": final_cache_max_size,
                "max_results": final_max_results,
            }

            # Validate configuration
            is_valid, validation_message = validate_jira_config(jira_config_for_sync)
            if not is_valid:
                cache_status_message = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-danger"
                        ),
                        html.Div(
                            [
                                html.Span(
                                    "Configuration Error",
                                    className="fw-bold d-block mb-1",
                                ),
                                html.Span(validation_message, className="small"),
                            ]
                        ),
                    ],
                    className="text-danger small mt-2",
                )
                logger.error(
                    f"JIRA configuration validation failed: {validation_message}"
                )
                return None, None, cache_status_message, no_update

            # Use sync_jira_scope_and_data to get both scope data and message
            from data.jira_simple import sync_jira_scope_and_data

            success, message, scope_data = sync_jira_scope_and_data(
                settings_jql, jira_config_for_sync
            )

            if success:
                # Load the updated statistics data after JIRA import
                from data.persistence import load_statistics

                updated_statistics, _ = (
                    load_statistics()
                )  # Unpack tuple, ignore is_sample flag

                # Get count of weekly data points
                weekly_count = len(updated_statistics) if updated_statistics else 0

                # Get actual JIRA issue count from scope data
                issues_count = (
                    scope_data.get("calculation_metadata", {}).get(
                        "total_issues_processed", 0
                    )
                    if scope_data
                    else 0
                )

                # Create detailed success message showing both counts
                success_details = f"✓ Data loaded: {issues_count} issue{'s' if issues_count != 1 else ''} from JIRA (aggregated into {weekly_count} weekly data point{'s' if weekly_count != 1 else ''})"

                cache_status_message = html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Span(success_details, className="fw-medium"),
                    ],
                    className="text-success small text-center mt-2",
                )
                logger.info(
                    f"JIRA data import successful: {issues_count} issues loaded, {weekly_count} weekly data points created"
                )

                # Extract scope values from scope_data to update input fields
                # These values represent the total project scope calculated from JIRA
                total_items = scope_data.get("total_items", 0) if scope_data else 0
                estimated_items = (
                    scope_data.get("estimated_items", 0) if scope_data else 0
                )
                total_points = scope_data.get("total_points", 0) if scope_data else 0
                estimated_points = (
                    scope_data.get("estimated_points", 0) if scope_data else 0
                )

                # Format total_points as string since it's a text display field
                total_points_display = f"{total_points:.0f}"

                logger.info(
                    f"Scope calculated from JIRA: total_items={total_items}, "
                    f"estimated_items={estimated_items}, total_points={total_points}, "
                    f"estimated_points={estimated_points}"
                )

                # Return updated statistics AND scope values to refresh inputs
                return (
                    None,
                    None,
                    cache_status_message,
                    updated_statistics,
                    total_items,
                    estimated_items,
                    total_points_display,  # Text field, not number
                    estimated_points,
                )
            else:
                # Create detailed error message
                error_details = f"✗ Failed to import JIRA data: {message}"

                cache_status_message = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-danger"
                        ),
                        html.Span(error_details, className="fw-medium"),
                    ],
                    className="text-danger small text-center mt-2",
                )
                logger.error(f"JIRA data import failed: {message}")
                # Return no table update on failure, keep scope values unchanged
                return (
                    None,
                    None,
                    cache_status_message,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

        except ImportError:
            logger.error("JIRA integration not available")
            cache_status_message = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                    html.Div(
                        [
                            html.Span(
                                "Integration Error", className="fw-bold d-block mb-1"
                            ),
                            html.Span(
                                "JIRA integration module not available. Please check your installation.",
                                className="small",
                            ),
                        ]
                    ),
                ],
                className="text-danger small mt-2",
            )
            return (
                None,
                None,
                cache_status_message,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        except Exception as e:
            logger.error(f"Error in unified data update: {e}")
            cache_status_message = html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                    html.Div(
                        [
                            html.Span(
                                "Unexpected Error", className="fw-bold d-block mb-1"
                            ),
                            html.Span(f"{str(e)}", className="small"),
                        ]
                    ),
                ],
                className="text-danger small mt-2",
            )
            return (
                None,
                None,
                cache_status_message,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

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
                "jira-jql-query", "value"
            ),  # JQL textarea uses standard "value" property
        ],
        prevent_initial_call=True,
    )
    def calculate_jira_project_scope(
        n_clicks,
        jql_query,
    ):
        """
        Calculate project scope based on JIRA issues using status categories.
        """
        if not n_clicks or n_clicks == 0:
            raise PreventUpdate

        try:
            from data.persistence import (
                calculate_project_scope_from_jira,
                load_jira_configuration,
            )

            # Load JIRA configuration
            jira_config = load_jira_configuration()

            # Check if JIRA is configured (FR-018: Error handling for unconfigured state)
            # Token is optional for public JIRA servers
            is_configured = (
                jira_config.get("configured", False)
                and jira_config.get("base_url", "").strip() != ""
            )

            if not is_configured:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_message = "⚠️ JIRA is not configured. Please click the 'Configure JIRA' button to set up your JIRA connection before calculating project scope."
                return (
                    html.Div(status_message, className="text-warning"),
                    f"Last attempt: {current_time}",
                    no_update,
                    no_update,
                    no_update,
                )

            # Build UI config from loaded jira_config
            from data.jira_simple import construct_jira_endpoint

            base_url = jira_config.get("base_url", "https://jira.atlassian.com")
            api_version = jira_config.get("api_version", "v2")

            ui_config = {
                "jql_query": jql_query or "",
                "api_endpoint": construct_jira_endpoint(base_url, api_version),
                "token": jira_config.get("token", ""),
                "story_points_field": jira_config.get("points_field", ""),
                "cache_max_size_mb": jira_config.get("cache_size_mb", 100),
                "max_results": jira_config.get("max_results_per_call", 1000),
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

                    # Get points field from jira_config
                    points_field = jira_config.get("points_field", "")
                    if points_field and points_field.strip():
                        # Get detailed field statistics from the scope calculation
                        field_name = points_field.strip()
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
            State("jira-jql-query", "value"),
            State("save-jql-query-modal", "is_open"),
        ],  # JQL textarea uses standard "value" property
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
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            Output("jira-query-profile-selector-mobile", "value", allow_duplicate=True),
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
                "jira-jql-query", "value"
            ),  # JQL textarea uses standard "value" property
            State("save-query-set-default-checkbox", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_query_profile(
        save_clicks, query_name, description, jql_value, set_as_default
    ):
        """Save a new JQL query profile and select it in the dropdown."""
        if not save_clicks:
            raise PreventUpdate

        # Validate inputs
        if not query_name or not query_name.strip():
            return (
                no_update,
                no_update,
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

            # Get the saved profile ID to select it
            saved_profile_id = saved_profile["id"] if saved_profile else None

            # Clear form, hide validation, and select the newly saved query
            return (
                updated_options,  # Desktop dropdown options
                updated_options,  # Mobile dropdown options
                saved_profile_id,  # Desktop dropdown value (select the saved query)
                saved_profile_id,  # Mobile dropdown value
                "",  # Clear query name input
                "",  # Clear description input
                "",  # Clear validation message
                {"display": "none"},  # Hide validation
            )

        except Exception as e:
            logger.error(f"Error saving query profile: {e}")
            return (
                no_update,
                no_update,
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
        """Sync both dropdowns, show/hide profile action buttons, and persist selection."""
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

        # CRITICAL FIX: Persist the selected profile ID to app_settings.json
        # This ensures the selection is maintained on app restart/refresh
        try:
            from data.persistence import load_app_settings, save_app_settings

            app_settings = load_app_settings()
            current_profile_id = app_settings.get("active_jql_profile_id", "")

            # Only save if the profile ID has changed (avoid unnecessary file writes)
            if selected_profile_id != current_profile_id:
                save_app_settings(
                    pert_factor=app_settings["pert_factor"],
                    deadline=app_settings["deadline"],
                    data_points_count=app_settings.get("data_points_count"),
                    show_milestone=app_settings.get("show_milestone"),
                    milestone=app_settings.get("milestone"),
                    show_points=app_settings.get("show_points"),
                    jql_query=app_settings.get("jql_query"),
                    last_used_data_source=app_settings.get("last_used_data_source"),
                    active_jql_profile_id=selected_profile_id
                    or "",  # Persist the selection
                )
                logger.info(
                    f"Persisted selected query profile ID: {selected_profile_id}"
                )
        except Exception as e:
            logger.error(f"Error persisting profile selection: {e}")
            # Continue with button visibility logic even if persistence fails

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
            "jira-jql-query", "value"
        ),  # JQL textarea uses standard "value" property
        [Input("jira-query-profile-selector", "value")],
        prevent_initial_call=False,  # CRITICAL FIX: Allow initial call to load query on app start
    )
    def update_jql_from_profile(selected_profile_id):
        """Update JQL textarea when a profile is selected or on initial load."""
        if not selected_profile_id:
            raise PreventUpdate

        try:
            from data.jira_query_manager import get_query_profile_by_id

            profile = get_query_profile_by_id(selected_profile_id)
            if profile:
                logger.info(f"Loading JQL query from profile: {profile['name']}")
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
            Output("jira-jql-query", "value", allow_duplicate=True),
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
        """Update existing JQL query profile and refresh the editor."""
        if not edit_clicks or not current_profile_id or current_profile_id == "custom":
            raise PreventUpdate

        # Validate inputs
        if not query_name or not query_name.strip():
            return (
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
                "JQL query is required",
                {"display": "block"},
            )

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

                # Return updated options, JQL value, and clear validation
                return (
                    updated_options,
                    updated_options,
                    jql_value.strip(),  # Update JQL editor with edited query
                    "",
                    {"display": "none"},
                )
            else:
                return (
                    no_update,
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
                no_update,
                "Error updating query profile",
                {"display": "block"},
            )

    @app.callback(
        [
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            Output(
                "jira-jql-query", "value", allow_duplicate=True
            ),  # JQL textarea uses standard "value" property
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
    # PERFORMANCE FIX: Use client-side callback for character counting to avoid Python callback overhead
    # Updated to match create_character_count_display format and thresholds
    app.clientside_callback(
        """
        function(jql_value) {
            if (!jql_value) {
                jql_value = '';
            }
            const count = jql_value.length;
            const WARNING_THRESHOLD = 1800;  // Match Python constant
            const MAX_REFERENCE = 2000;      // Match Python constant
            const warning = count >= WARNING_THRESHOLD;
            
            // Format count with thousands separator for readability (simplified for JS)
            const countStr = count.toLocaleString();
            const limitStr = MAX_REFERENCE.toLocaleString();
            
            // Apply warning CSS class if needed (match Python function)
            const cssClasses = warning ? 
                'character-count-display character-count-warning' : 
                'character-count-display';
            
            // Return a proper Dash HTML component structure
            return {
                'namespace': 'dash_html_components',
                'type': 'Div',
                'props': {
                    'children': `${countStr} / ${limitStr} characters`,
                    'className': cssClasses,
                    'id': 'jql-character-count-display'
                }
            };
        }
        """,
        Output("jira-jql-character-count-container", "children"),
        Input("jira-jql-query", "value"),
    )

    # JQL Query Test Callback (Feature: ScriptRunner function validation)
    @app.callback(
        [
            Output("jql-test-results", "children"),
            Output("jql-test-results", "style"),
        ],
        [Input("test-jql-query-button", "n_clicks")],
        [
            State("jira-jql-query", "value"),
        ],
        prevent_initial_call=True,
    )
    def test_jql_query_validity(
        n_clicks,
        jql_query,
    ):
        """
        Test JQL query validity - useful for ScriptRunner function validation.
        """
        if not n_clicks:
            raise PreventUpdate

        if not jql_query or not jql_query.strip():
            return (
                html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-primary"
                        ),
                        html.Span(
                            "Please enter a JQL query to test.", className="text-dark"
                        ),
                    ],
                    className="alert alert-info mb-0 border-primary",
                ),
                {"display": "block"},
            )

        try:
            from data.jira_simple import test_jql_query, validate_jql_for_scriptrunner
            from data.persistence import load_jira_configuration

            # Load JIRA configuration
            loaded_jira_config = load_jira_configuration()

            # Check if JIRA is configured (FR-018: Error handling for unconfigured state)
            # Token is optional for public JIRA servers
            is_configured = (
                loaded_jira_config.get("configured", False)
                and loaded_jira_config.get("base_url", "").strip() != ""
            )

            if not is_configured:
                return (
                    html.Div(
                        [
                            html.I(
                                className="fas fa-exclamation-triangle me-2 text-warning"
                            ),
                            html.Strong("JIRA Not Configured", className="text-dark"),
                            html.Br(),
                            html.Small(
                                "Please click the 'Configure JIRA' button above to set up your JIRA connection before testing queries.",
                                className="text-dark opacity-75",
                            ),
                        ],
                        className="alert alert-light border-warning mb-0",
                    ),
                    {"display": "block"},
                )

            # Build JIRA config for testing with current JQL query
            from data.jira_simple import construct_jira_endpoint

            base_url = loaded_jira_config.get("base_url", "https://jira.atlassian.com")
            api_version = loaded_jira_config.get("api_version", "v2")

            jira_config = {
                "jql_query": jql_query.strip(),
                "api_endpoint": construct_jira_endpoint(base_url, api_version),
                "token": loaded_jira_config.get("token", ""),
                "story_points_field": loaded_jira_config.get("points_field", ""),
                "cache_max_size_mb": loaded_jira_config.get("cache_size_mb", 100),
                "max_results": loaded_jira_config.get("max_results_per_call", 1000),
            }

            # First, check for ScriptRunner function warnings
            is_compatible, scriptrunner_warning = validate_jql_for_scriptrunner(
                jql_query
            )

            # Test the query
            is_valid, test_message = test_jql_query(jira_config)

            if is_valid:
                if is_compatible:
                    # PURE SUCCESS: Gray background with green icon (consistent design)
                    success_content = [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Strong("JQL Query Valid", className="text-dark"),
                        html.Br(),
                        html.Small(test_message, className="text-dark opacity-75"),
                    ]
                    alert_class = "alert alert-light border-success mb-0"
                else:
                    # SUCCESS WITH WARNING: Gray background with colored icons
                    success_content = [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Strong("JQL Query Valid", className="text-dark"),
                        html.Br(),
                        html.Small(test_message, className="text-dark opacity-75"),
                        html.Br(),
                        html.Br(),
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-warning"
                        ),
                        html.Strong(
                            "ScriptRunner Functions Detected",
                            className="text-dark",
                        ),
                        html.Br(),
                        html.Small(
                            scriptrunner_warning, className="text-dark opacity-75"
                        ),
                    ]
                    alert_class = "alert alert-light border-warning mb-0"

                return (
                    html.Div(
                        success_content,
                        className=alert_class,
                    ),
                    {"display": "block"},
                )
            else:
                # Query validation failed - consistent gray background design
                error_content = [
                    html.I(className="fas fa-times-circle me-2 text-danger"),
                    html.Strong("JQL Query Invalid", className="text-dark"),
                    html.Br(),
                    html.Div(
                        [
                            html.Strong(
                                "JIRA API Error:", className="text-dark mt-2 d-block"
                            ),
                            html.Code(
                                test_message,
                                className="text-dark d-block p-2 bg-light border rounded mt-1",
                            ),
                        ]
                    ),
                ]

                # Add specific guidance for ScriptRunner issues with UI-appropriate colors
                if not is_compatible:
                    error_content.extend(
                        [
                            html.Br(),
                            html.Br(),
                            html.I(className="fas fa-lightbulb me-2 text-primary"),
                            html.Strong(
                                "ScriptRunner Functions Detected",
                                className="text-dark",
                            ),
                            html.Br(),
                            html.Small(
                                "Your query contains ScriptRunner functions (issueFunction, subtasksOf, epicsOf, etc.). "
                                "These require the ScriptRunner add-on to be installed on your JIRA instance. "
                                "If the error mentions 'function' or 'unknown function', ScriptRunner may not be available.",
                                className="text-dark",
                            ),
                        ]
                    )

                return (
                    html.Div(
                        error_content,
                        className="alert alert-light border-danger mb-0",  # Soft light background with danger border
                    ),
                    {"display": "block"},
                )

        except ImportError:
            return (
                html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-secondary"
                        ),
                        html.Span(
                            "JIRA integration not available - cannot test query.",
                            className="text-secondary",
                        ),
                    ],
                    className="alert alert-light border-secondary mb-0",
                ),
                {"display": "block"},
            )
        except Exception as e:
            logger.error(f"Error testing JQL query: {e}")
            return (
                html.Div(
                    [
                        html.I(className="fas fa-times-circle me-2 text-danger"),
                        html.Span(
                            f"Error testing query: {str(e)}", className="text-dark"
                        ),
                    ],
                    className="alert alert-light border-danger mb-0",
                ),
                {"display": "block"},
            )

    # Add clientside callback for Test Query button loading state
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks && n_clicks > 0) {
                setTimeout(function() {
                    const button = document.getElementById('test-jql-query-button');
                    const resultsArea = document.getElementById('jql-test-results');
                    
                    if (button) {
                        console.log('[JQL Test] Button clicked - setting lock to TRUE');
                        
                        // Lock test results to prevent hiding during test
                        if (typeof window.setJQLTestResultsLock === 'function') {
                            window.setJQLTestResultsLock(true);
                        }
                        
                        // Remove the hidden class to allow Dash callback to show results
                        if (resultsArea) {
                            console.log('[JQL Test] Removing hidden class from results area');
                            resultsArea.className = resultsArea.className.replace('jql-test-results-hidden', '').trim();
                        }
                        
                        // Set loading state
                        button.disabled = true;
                        button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
                        
                        // Reset after timeout or when operation completes
                        const resetButton = function() {
                            if (button && button.disabled) {
                                button.disabled = false;
                                button.innerHTML = '<i class="fas fa-check-circle me-1"></i><span class="d-none d-sm-inline">Test Query</span>';
                            }
                        };
                        
                        // Shorter timeout for test operations
                        setTimeout(resetButton, 5000);
                        
                        // Monitor for completion using children changes instead of style
                        const observer = new MutationObserver(function(mutations) {
                            if (resultsArea && resultsArea.children.length > 0) {
                                setTimeout(resetButton, 500); // Reset after results appear
                                observer.disconnect();
                            }
                        });
                        
                        if (resultsArea) {
                            observer.observe(resultsArea, { childList: true });
                        }
                    }
                }, 50);
            }
            return null;
        }
        """,
        Output("test-jql-query-button", "title"),
        [Input("test-jql-query-button", "n_clicks")],
        prevent_initial_call=True,
    )

    #######################################################################
    # PARAMETER PANEL CALLBACKS (User Story 1)
    #######################################################################

    @app.callback(
        [
            Output("parameter-collapse", "is_open"),
            Output("parameter-panel-state", "data"),
            Output("settings-collapse", "is_open", allow_duplicate=True),
        ],
        Input("btn-expand-parameters", "n_clicks"),
        [
            State("parameter-collapse", "is_open"),
            State("parameter-panel-state", "data"),
            State("settings-collapse", "is_open"),
        ],
        prevent_initial_call=True,
    )
    def toggle_parameter_panel(n_clicks, is_open, panel_state, settings_is_open):
        """
        Toggle parameter panel expand/collapse and persist state to localStorage.

        This callback supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
        It toggles the collapse state and persists the user preference to localStorage
        so the panel state is maintained across sessions.

        Also ensures only one flyout panel is open at a time by closing settings panel
        when parameter panel opens.

        Args:
            n_clicks: Number of times expand button was clicked
            is_open: Current state of the collapse component
            panel_state: Current parameter panel state from dcc.Store
            settings_is_open: Current settings panel state

        Returns:
            tuple: (new_is_open, updated_panel_state, new_settings_state)
        """
        from datetime import datetime

        if n_clicks:
            new_is_open = not is_open
            # Update panel state with new preference
            updated_state = {
                "is_open": new_is_open,
                "last_updated": datetime.now().isoformat(),
                "user_preference": True,
            }

            # If opening parameter panel and settings panel is open, close settings
            if new_is_open and settings_is_open:
                return new_is_open, updated_state, False

            return new_is_open, updated_state, no_update

        return is_open, panel_state, no_update

    @app.callback(
        Output("parameter-bar-collapsed", "children"),
        [
            Input("pert-factor-slider", "value"),  # FIXED: use correct component ID
            Input(
                "deadline-picker", "date"
            ),  # FIXED: use correct component and property
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input("current-settings", "modified_timestamp"),  # Add to get show_points
        ],
        [State("current-settings", "data")],
        prevent_initial_call=False,  # Update on initial load
    )
    def update_parameter_summary(
        pert_factor, deadline, scope_items, scope_points, settings_ts, settings
    ):
        """
        Update parameter summary in collapsed bar when values change.

        This callback supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
        It updates the collapsed bar display to show current parameter values immediately
        after user changes them in the expanded panel.

        Args:
            pert_factor: Current PERT factor value
            deadline: Current deadline date string
            scope_items: Total number of items in scope
            scope_points: Total story points in scope
            settings_ts: Timestamp of settings changes
            settings: Current app settings

        Returns:
            Dash components: Updated collapsed bar children
        """
        # Provide defaults for None values
        pert_factor = pert_factor or DEFAULT_PERT_FACTOR
        deadline = deadline or "2025-12-31"
        scope_items = scope_items or 0
        scope_points = scope_points or 0

        # Get show_points setting
        show_points = settings.get("show_points", True) if settings else True

        # Get remaining items/points from project scope if available
        from data.persistence import get_project_scope

        project_scope = get_project_scope()
        remaining_items = None
        remaining_points = None

        if project_scope:
            remaining_items = project_scope.get("remaining_items")
            # Use remaining_total_points (estimated) instead of remaining_points (raw count)
            # remaining_total_points accounts for items without estimates
            remaining_points = project_scope.get("remaining_total_points")

        return dbc.Row(
            [
                # Parameter Summary (left side)
                dbc.Col(
                    [
                        html.Div(
                            [
                                html.Span(
                                    [
                                        html.I(className="fas fa-sliders-h me-1"),
                                        f"PERT: {pert_factor}",
                                    ],
                                    className="param-summary-item me-3",
                                    title=f"PERT Factor: {pert_factor}",
                                ),
                                html.Span(
                                    [
                                        html.I(className="fas fa-calendar me-1"),
                                        html.Span(
                                            "Deadline:",
                                            className="text-muted d-none d-lg-inline me-1",
                                            style={"fontSize": "0.85em"},
                                        ),
                                        f"{deadline}",
                                    ],
                                    className="param-summary-item me-3",
                                    title=f"Project deadline: {deadline}",
                                ),
                                html.Span(
                                    [
                                        html.I(className="fas fa-tasks me-1"),
                                        html.Span(
                                            f"{'Remaining' if remaining_items is not None else 'Scope'}:",
                                            className="text-muted d-none d-md-inline me-1",
                                            style={"fontSize": "0.85em"},
                                        ),
                                        f"{(remaining_items if remaining_items is not None else scope_items):,}",
                                        html.Span(
                                            " items",
                                            className="d-none d-sm-inline",
                                        ),
                                    ],
                                    className="param-summary-item me-3",
                                    title=f"{'Remaining' if remaining_items is not None else 'Scope'}: {(remaining_items if remaining_items is not None else scope_items):,} items",
                                ),
                            ]
                            + (
                                [
                                    html.Span(
                                        [
                                            html.I(className="fas fa-chart-bar me-1"),
                                            html.Span(
                                                f"{'Remaining' if remaining_points is not None else 'Scope'}:",
                                                className="text-muted d-none d-md-inline me-1",
                                                style={"fontSize": "0.85em"},
                                            ),
                                            f"{(remaining_points if remaining_points is not None else scope_points):,}",
                                            html.Span(
                                                " pts",
                                                className="d-none d-sm-inline",
                                            ),
                                        ],
                                        className="param-summary-item",
                                        title=f"{'Remaining' if remaining_points is not None else 'Scope'}: {(remaining_points if remaining_points is not None else scope_points):,} points",
                                    ),
                                ]
                                if show_points
                                else []
                            ),
                            className="d-flex align-items-center flex-wrap",
                        ),
                    ],
                    xs=12,
                    md=9,
                    className="d-flex align-items-center",
                ),
                # Expand Button and Settings Button (right side)
                dbc.Col(
                    [
                        html.Div(
                            [
                                dbc.Button(
                                    [
                                        html.I(
                                            className="fas fa-chevron-down",
                                            style={
                                                "minWidth": "14px",
                                                "textAlign": "center",
                                            },
                                        ),
                                        html.Span(
                                            "Parameters",
                                            className="d-none d-lg-inline ms-2",
                                        ),
                                    ],
                                    id="btn-expand-parameters",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    className="me-2",
                                ),
                                dbc.Button(
                                    [
                                        html.I(
                                            className="fas fa-cog",
                                            style={
                                                "minWidth": "14px",
                                                "textAlign": "center",
                                            },
                                        ),
                                        html.Span(
                                            "Settings",
                                            className="d-none d-lg-inline ms-2",
                                        ),
                                    ],
                                    id="settings-button",
                                    color="primary",
                                    outline=True,
                                    size="sm",
                                    title="Configure data sources, import/export, and JQL queries",
                                ),
                            ],
                            className="d-flex justify-content-end align-items-center",
                        ),
                    ],
                    xs=12,
                    md=3,
                    className="d-flex align-items-center justify-content-end mt-2 mt-md-0",
                ),
            ],
            className="g-2",
        )
