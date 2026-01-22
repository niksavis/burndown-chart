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
from dash import (
    Input,
    Output,
    State,
    callback_context,
    html,
    no_update,
    ClientsideFunction,
)
from dash.exceptions import PreventUpdate

# Application imports
from ui.toast_notifications import create_success_toast
from configuration import (
    DEFAULT_ESTIMATED_ITEMS,
    DEFAULT_ESTIMATED_POINTS,
    DEFAULT_PERT_FACTOR,
    DEFAULT_TOTAL_POINTS,
    logger,
)
from data import calculate_total_points
from ui.components import create_parameter_bar_collapsed

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


def calculate_remaining_work_for_data_window(data_points_count, statistics):
    """
    Get current remaining work scope - this does NOT depend on the data window.

    The Data Points slider filters the time window for forecasting/statistics,
    but "Remaining" always means CURRENT remaining work (what's left to do now).

    Args:
        data_points_count: Number of data points (weeks) - used for logging only
        statistics: List of statistics data points - not used, kept for compatibility

    Returns:
        Tuple: (estimated_items, remaining_items, estimated_points, remaining_points_str, calc_results)
               or None if calculation cannot be performed
    """
    if not data_points_count:
        return None

    try:
        from data.persistence import load_unified_project_data

        # Load unified data to get current scope
        unified_data = load_unified_project_data()
        project_scope = unified_data.get("project_scope", {})

        # CRITICAL FIX: Parameter panel shows CURRENT remaining work, NOT windowed scope
        # The slider filters statistics for forecasting, but remaining work is always current
        estimated_items = project_scope.get("estimated_items", 0)
        remaining_items = project_scope.get("remaining_items", 0)
        estimated_points = project_scope.get("estimated_points", 0)
        remaining_points = project_scope.get("remaining_total_points", 0)

        # Calculate avg points per item for calc_results
        avg_points_per_item = 0
        if remaining_items > 0:
            avg_points_per_item = remaining_points / remaining_items

        logger.info("[PARAM PANEL] Current remaining work (independent of slider):")
        logger.info(
            f"  Estimated items: {estimated_items}, Remaining items: {remaining_items}"
        )
        logger.info(
            f"  Estimated points: {estimated_points:.1f}, Remaining points: {remaining_points:.1f}"
        )
        logger.info(f"  Avg: {avg_points_per_item:.2f} points/item")

        calc_results = {
            "total_points": remaining_points,
            "avg_points_per_item": avg_points_per_item,
        }

        return (
            estimated_items,
            int(remaining_items),
            estimated_points,
            f"{remaining_points:.0f}",
            calc_results,
        )

    except Exception as e:
        logger.error(f"Error calculating remaining work for data window: {e}")
        return None


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
            State("total-points-display", "value"),  # Check if already set by slider
        ],
    )
    def update_total_points_calculation(
        total_items,
        estimated_items,
        estimated_points,
        stats_ts,
        statistics,
        calc_results,
        current_total_points_display,
    ):
        """
        Update the total points calculation based on estimated items and points or historical data.

        Uses the same extrapolation formula as JIRA scope calculator:
        remaining_total_points = estimated_points + (avg_points_per_item × unestimated_items)

        This ensures consistency between JIRA and manual data entry workflows.
        Manual changes to inputs will always trigger recalculation, allowing users to
        adjust forecasts even when working with JIRA data.
        """
        # Input validation
        if None in [total_items, estimated_items, estimated_points]:
            # Use .get() method for dictionary lookups - this is the Python idiomatic way
            return (
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.1f}",
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
                f"{calc_results.get('total_points', DEFAULT_TOTAL_POINTS):.1f}",
                calc_results
                or {"total_points": DEFAULT_TOTAL_POINTS, "avg_points_per_item": 0},
            )

        # Calculate total points and average - use_fallback=False to respect user's explicit input
        # This is for MANUAL data entry workflow only
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
            f"{estimated_total_points:.1f}",
            updated_calc_results,
        )

    @app.callback(
        Output("remaining-points-formula", "children"),
        Input("calculation-results", "data"),
    )
    def update_remaining_points_formula(calc_results):
        """Update the formula display to show the actual avg coefficient being used."""
        if not calc_results:
            return "= Est. Points + (avg × unestimated)."

        avg = calc_results.get("avg_points_per_item", 0)
        if avg > 0:
            return f"= Est. Points + ({avg:.2f} × unestimated)."
        else:
            return "= Est. Points + (avg × unestimated)."

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
            Input("estimated-items-input", "value"),
            Input("estimated-points-input", "value"),
            Input(
                "data-points-input", "value"
            ),  # CRITICAL: Parameter panel data points slider - triggers settings update for visualizations
            Input("points-toggle", "value"),  # Parameter panel points toggle
        ],
        [
            State("app-init-complete", "data"),
            State(
                "current-statistics", "data"
            ),  # CRITICAL: Need statistics to recalculate windowed scope
            State(
                "calculation-results", "data"
            ),  # State, not Input - avoid race condition
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
        estimated_items,
        estimated_points,
        data_points_count,  # Parameter panel data points slider
        show_points,  # Parameter panel points toggle
        # State parameters (read but don't trigger callback)
        init_complete,
        statistics,  # CRITICAL: Statistics for recalculating windowed scope
        calc_results,  # State - read for fallback but doesn't trigger callback
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
        # NOTE: deadline and milestone are optional, so they're not in the required list
        if (
            not init_complete
            or not ctx.triggered
            or None
            in [
                pert_factor,
                total_items,
                data_points_count,
            ]
        ):
            raise PreventUpdate

        # CRITICAL FIX: Recalculate total_items and total_points based on windowed statistics
        # When data_points_count slider changes, scope must be recalculated from filtered data
        data_points_count = (
            int(data_points_count) if data_points_count is not None else 12
        )

        # Initialize with fallback values from calc_results or defaults
        total_points = (
            calc_results.get("total_points", DEFAULT_TOTAL_POINTS)
            if calc_results
            else DEFAULT_TOTAL_POINTS
        )

        # CRITICAL FIX: Use CURRENT remaining work from project_scope, not windowed values
        # The data_points slider filters the TIME WINDOW for velocity/forecasting calculations,
        # but "Remaining Items/Points" should ALWAYS reflect CURRENT work (what's left NOW),
        # not historical remaining work from the start of the time window.
        #
        # BUG: Previously used "earliest week's remaining" from filtered window, which gave
        # incorrect values like 304 items instead of actual current 169 items.
        #
        # FIX: Load current remaining work from project_scope (database source of truth)
        try:
            from data.persistence import load_unified_project_data

            unified_data = load_unified_project_data()
            project_scope = unified_data.get("project_scope", {})

            # Use CURRENT remaining work from project_scope
            total_items = project_scope.get("remaining_items", total_items)
            total_points = project_scope.get("remaining_total_points", total_points)

            logger.info(
                f"[Settings] Using CURRENT remaining work from project_scope: "
                f"{total_items} items, {total_points:.1f} points "
                f"(data_points slider: {data_points_count} weeks for velocity calculations)"
            )
        except Exception as e:
            logger.error(
                f"[Settings] Error loading current remaining work: {e}", exc_info=True
            )

        # Use consistent .get() pattern for all fallbacks - restored from previous implementation
        input_values = {
            "estimated_items": estimated_items,
            "estimated_points": estimated_points,
        }
        estimated_items = input_values.get("estimated_items", DEFAULT_ESTIMATED_ITEMS)
        estimated_points = input_values.get(
            "estimated_points", DEFAULT_ESTIMATED_POINTS
        )

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
            "show_points": bool(
                show_points and (show_points is True or "show" in show_points)
            ),  # Convert checklist to boolean
        }

        # Save app-level settings - load JIRA values from jira_config (Feature 003-jira-config-separation)
        from data.persistence import save_app_settings, load_app_settings

        # Load existing settings to preserve last_used_data_source and active_jql_profile_id
        existing_settings = load_app_settings()

        # JQL query change detection removed - JQL is now managed per-query in query.json
        # Cache invalidation based on JQL changes is handled in handle_unified_data_update

        save_app_settings(
            pert_factor,
            deadline,
            data_points_count,
            show_milestone,  # Automatically calculated
            milestone,
            settings[
                "show_points"
            ],  # Use the converted boolean from settings dict (NOT raw checklist value)
            jql_query.strip()
            if jql_query and jql_query.strip()
            else "project = JRASERVER",  # Use current JQL input
            existing_settings.get("last_used_data_source"),  # Preserve data source
            existing_settings.get("active_jql_profile_id"),  # Preserve profile ID
            # Note: JIRA configuration is now managed separately via save_jira_configuration()
        )

        # SOLUTION 1 FIX: NEVER save scope values (total_items, total_points, etc.) from UI inputs
        # to the database. These values are DERIVED from the data points slider and should be
        # calculated on-the-fly. Only the BASE scope (from JIRA) should be in the database.
        #
        # The parameter panel inputs show WINDOWED scope (based on data_points slider).
        # The database stores BASE scope (full JIRA data without filtering).
        # All visualizations calculate windowed values by reading current-settings store.
        #
        # This ensures:
        # 1. Moving the slider immediately recalculates all displayed values
        # 2. Database remains the source of truth for base data
        # 3. No callback collisions overwriting calculated values
        #
        logger.info(
            "[Settings] Scope values (total_items, total_points) are derived from slider - not saved to database"
        )
        logger.info(
            f"[Settings] Storing windowed scope in settings store for visualization: {total_items} items, {total_points:.1f} points"
        )

        # SOLUTION 1: Log which trigger caused the settings update for debugging
        trigger_id = (
            ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else "unknown"
        )
        logger.info(
            f"[Settings] Updated settings (triggered by {trigger_id}): data_points={data_points_count}, total_items={total_items}, total_points={total_points:.1f}"
        )
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

    # Clientside callback to detect force refresh from long-press
    app.clientside_callback(
        ClientsideFunction(namespace="forceRefresh", function_name="updateStore"),
        Output("force-refresh-store", "data"),
        Input("update-data-unified", "n_clicks"),
        prevent_initial_call=True,
    )

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
            Output("current-settings", "data", allow_duplicate=True),
            Output(
                "force-refresh-store", "data", allow_duplicate=True
            ),  # Reset store after use
            Output("update-data-unified", "disabled", allow_duplicate=True),
            Output("update-data-unified", "children", allow_duplicate=True),
            Output(
                "update-data-status", "children", allow_duplicate=True
            ),  # Loading spinner + status
            Output(
                "app-notifications", "children", allow_duplicate=True
            ),  # Toast notifications
            Output(
                "trigger-auto-metrics-calc", "data", allow_duplicate=True
            ),  # Trigger separate metrics calc
            Output(
                "progress-poll-interval", "disabled", allow_duplicate=True
            ),  # Enable polling for banner icons
            Output(
                "current-statistics", "data", allow_duplicate=True
            ),  # CRITICAL: Clear statistics on force refresh to prevent stale data display
        ],
        [
            Input("update-data-unified", "n_clicks"),
            Input("force-refresh-store", "data"),  # Force refresh from long-press store
        ],
        [
            State(
                "jira-jql-query", "value"
            ),  # JQL textarea uses standard "value" property
        ],
        prevent_initial_call="initial_duplicate",  # Run on initial load with duplicate outputs
    )
    def handle_unified_data_update(
        n_clicks,
        force_refresh,
        jql_query,
    ):
        """
        Handle unified data update button click (JIRA data source only).

        Args:
            n_clicks (int): Number of clicks on unified update button
            force_refresh (bool): Force cache refresh flag from clientside store
            jql_query (str): JQL query for JIRA data source

        Returns:
            Tuple: Upload contents, filename, cache status, statistics table data,
                   scope values, settings, button state
        """
        # Detect which input triggered the callback
        from dash import ctx

        triggered_id = ctx.triggered_id if ctx.triggered else None
        triggered_prop = ctx.triggered[0] if ctx.triggered else None
        logger.info("[UPDATE DATA] =========================================")
        logger.info(
            f"[UPDATE DATA] Callback triggered by: {triggered_id} - n_clicks={n_clicks}, force_refresh={force_refresh}"
        )
        logger.info(f"[UPDATE DATA] Full trigger info: {triggered_prop}")
        logger.info("[UPDATE DATA] =========================================")

        # Normal button state
        button_normal = [
            html.I(className="fas fa-sync-alt", style={"marginRight": "0.5rem"}),
            html.Span("Update Data"),
        ]

        # If triggered by force-refresh-store changing but button wasn't clicked, ignore
        if triggered_id == "force-refresh-store" and not n_clicks:
            raise PreventUpdate

        if not n_clicks:
            # Initial page load - return normal button state with icon
            return (
                None,  # upload contents
                None,  # upload filename
                "",  # cache status (empty)
                no_update,  # statistics table
                no_update,  # total items
                no_update,  # estimated items
                no_update,  # total points
                no_update,  # estimated points
                no_update,  # settings
                False,  # force refresh
                False,  # button disabled
                button_normal,  # button children with icon
                "",  # update-data-status (empty)
                "",  # toast notification (empty)
                None,  # metrics trigger
                True,  # progress-poll-interval disabled (no task)
                no_update,  # current-statistics
            )

        try:
            # Track task progress
            from data.task_progress import TaskProgress

            # Check if another task is already running
            is_running, existing_task = TaskProgress.is_task_running()
            if is_running:
                logger.warning(
                    f"Update Data clicked but task already running: {existing_task}"
                )
                return (
                    None,  # upload-data contents
                    None,  # upload-data filename
                    html.Div(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            f"Operation already in progress: {existing_task}",
                        ],
                        className="text-warning small",
                    ),  # jira-cache-status
                    no_update,  # statistics-table
                    no_update,  # total-items-input
                    no_update,  # estimated-items-input
                    no_update,  # total-points-display
                    no_update,  # estimated-points-input
                    no_update,  # current-settings
                    False,  # force-refresh-store (reset)
                    False,  # update-data-unified disabled (enable button)
                    button_normal,  # update-data-unified children
                    html.Div(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            f"Operation already in progress: {existing_task}",
                        ],
                        className="text-warning small",
                    ),  # update-data-status
                    "",  # app-notifications (no toast)
                    None,  # trigger-auto-metrics-calc
                    True,  # progress-poll-interval disabled (already running)
                    no_update,  # current-statistics
                )

            # Start the task - returns False if can't start
            if not TaskProgress.start_task("update_data", "Updating data from JIRA"):
                logger.error("Failed to start Update Data task")
                return (
                    None,  # upload-data contents
                    None,  # upload-data filename
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Failed to start operation",
                        ],
                        className="text-danger small",
                    ),  # jira-cache-status
                    no_update,  # statistics-table
                    no_update,  # total-items-input
                    no_update,  # estimated-items-input
                    no_update,  # total-points-display
                    no_update,  # estimated-points-input
                    no_update,  # current-settings
                    False,  # force-refresh-store (reset)
                    False,  # update-data-unified disabled (enable button)
                    button_normal,  # update-data-unified children
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Failed to start operation",
                        ],
                        className="text-danger small",
                    ),  # update-data-status
                    "",  # app-notifications (no toast)
                    None,  # trigger-auto-metrics-calc
                    True,  # progress-poll-interval disabled (failed to start)
                    no_update,  # current-statistics
                )

            # Handle JIRA data import (settings panel only uses JIRA)
            from data.jira_simple import validate_jira_config
            from data.persistence import load_app_settings

            # CRITICAL DEBUG: Log what we receive from the Store
            logger.info(
                f"[Settings] Received jql_query from Store: '{jql_query}' (type: {type(jql_query)})"
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
                                    "[!] JIRA is not configured.",
                                    className="fw-bold d-block mb-1",
                                ),
                                html.Span(
                                    "Please click the 'Configure JIRA' button above to set up your JIRA connection before fetching data.",
                                    className="small",
                                ),
                            ]
                        ),
                    ],
                    className="text-warning small",
                )
                logger.warning(
                    "[Settings] Attempted to update data without JIRA configuration"
                )
                # Clear task progress
                TaskProgress.complete_task("update_data", "❌ JIRA not configured")
                return (
                    None,
                    None,
                    cache_status_message,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,  # Don't update settings
                    False,  # Reset force refresh
                    False,  # Enable button
                    button_normal,  # Reset button text
                    cache_status_message,  # Show error in status area
                    "",  # Toast notification (empty)
                    None,  # metrics trigger
                    False,  # progress-poll-interval enabled (task completed with error)
                    no_update,  # current-statistics
                    no_update,  # current-statistics
                )

            # Use JQL query from input or fall back to active query's JQL
            app_settings = load_app_settings()

            # Get JQL from active query if input is empty
            if not jql_query or not jql_query.strip():
                try:
                    from data.persistence.factory import get_backend

                    backend = get_backend()
                    active_query_id = backend.get_app_state("active_query_id")
                    active_profile_id = backend.get_app_state("active_profile_id")

                    if active_query_id and active_profile_id:
                        # Load query from database
                        query_data = backend.get_query(
                            active_profile_id, active_query_id
                        )
                        if query_data:
                            settings_jql = query_data.get("jql", "")
                            logger.info(
                                f"[Settings] Using JQL from active query '{active_query_id}': '{settings_jql}'"
                            )
                        else:
                            settings_jql = app_settings.get(
                                "jql_query", "project = JRASERVER"
                            )
                            logger.warning(
                                f"[Settings] Query not found in database: {active_query_id}, using fallback JQL"
                            )
                    else:
                        # No active query, use default
                        settings_jql = app_settings.get(
                            "jql_query", "project = JRASERVER"
                        )
                        logger.warning(
                            f"[Settings] No active query, using fallback JQL: '{settings_jql}'"
                        )
                except Exception as e:
                    logger.error(
                        f"[Settings] Failed to load JQL from active query: {e}"
                    )
                    settings_jql = app_settings.get("jql_query", "project = JRASERVER")
            else:
                settings_jql = jql_query.strip()

            logger.info(
                f"[Settings] JQL Query - Input: '{jql_query}', Final: '{settings_jql}'"
            )

            # Load JIRA configuration values from jira_config and construct endpoint
            from data.jira_simple import construct_jira_endpoint

            base_url = jira_config.get("base_url", "https://jira.atlassian.com")
            api_version = jira_config.get("api_version", "v2")
            final_jira_api_endpoint = construct_jira_endpoint(base_url, api_version)
            final_jira_token = jira_config.get("token", "")
            # Defensive: Ensure points_field is a string (not dict from field_mappings)
            points_field_raw = jira_config.get("points_field", "")
            final_story_points_field = (
                points_field_raw if isinstance(points_field_raw, str) else ""
            )
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
                    app_settings.get("last_used_data_source"),  # Preserve data source
                    app_settings.get("active_jql_profile_id"),  # Preserve profile ID
                )
                logger.info(
                    f"[Settings] JQL query updated and saved: JQL='{settings_jql}'"
                )

            # Create JIRA config for sync_jira_data (using loaded values)
            jira_config_for_sync = {
                "api_endpoint": final_jira_api_endpoint,
                "jql_query": settings_jql,
                "token": final_jira_token,
                "story_points_field": final_story_points_field,
                "cache_max_size_mb": final_cache_max_size,
                "max_results": final_max_results,
                "devops_projects": app_settings.get(
                    "devops_projects", []
                ),  # Add DevOps filtering config
                "devops_task_types": app_settings.get(
                    "devops_task_types", []
                ),  # Add DevOps task types for two-phase fetch
                "field_mappings": app_settings.get(
                    "field_mappings", {}
                ),  # Add field mappings for DORA/Flow metrics
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
                    className="text-danger small",
                )
                logger.error(
                    f"[Settings] JIRA configuration validation failed: {validation_message}"
                )
                # Clear task progress
                TaskProgress.complete_task("update_data")
                return (
                    None,
                    None,
                    cache_status_message,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,  # Don't update settings
                    False,  # Reset force refresh
                    False,  # Enable button
                    button_normal,  # Reset button text
                    cache_status_message,  # Show error in status area
                    "",  # Toast notification
                    None,  # metrics trigger
                    False,  # progress-poll-interval enabled (task completed with error)
                )

            # Use sync_jira_scope_and_data to get both scope data and message
            from data.jira_simple import sync_jira_scope_and_data

            # Convert checkbox value to boolean (None = False)
            # The force_refresh comes from the clientside callback that reads _forceRefreshPending flag
            force_refresh_bool = bool(force_refresh)

            # DEBUG: Log what we received from the store
            logger.info(
                f"[Settings] force_refresh value = {force_refresh}, bool = {force_refresh_bool}"
            )

            # IMPORTANT: If force_refresh is still False, the clientside callback might not have fired yet
            # This can happen if callbacks execute in parallel - log a warning
            if not force_refresh_bool and n_clicks:
                logger.debug(
                    f"[Settings] Force refresh flag is False on click #{n_clicks}. "
                    "If long-press was used, this might indicate a timing issue."
                )

            # CRITICAL FIX: For NEW queries with no existing data, treat Update Data as Force Refresh
            # Check if JIRA cache exists in database - this is the definitive indicator of a new query
            if not force_refresh_bool:
                from data.persistence.factory import get_backend

                backend = get_backend()
                active_profile_id = backend.get_app_state("active_profile_id")
                active_query_id = backend.get_app_state("active_query_id")

                # Check if any issues exist in database for this query
                if active_profile_id and active_query_id:
                    issues = backend.get_issues(
                        active_profile_id, active_query_id, limit=1
                    )
                    if not issues:
                        logger.info(
                            "[Settings] New query detected (no issues in database), treating Update Data as Force Refresh"
                        )
                        force_refresh_bool = True

            if force_refresh_bool:
                logger.info("=" * 60)
                logger.info(
                    "[Settings] FORCE REFRESH ENABLED - COMPLETE DATA WIPE FOR THIS QUERY"
                )
                logger.info(
                    "[Settings] This is a self-repair mechanism to recover from bad data"
                )
                logger.info("=" * 60)

                # SELF-REPAIR MECHANISM: Complete data wipe for the active query
                # This removes ALL data associated with this query from database and cache
                # to give the user a clean slate when they suspect data corruption
                from data.persistence.factory import get_backend

                backend = get_backend()
                active_profile_id = backend.get_app_state("active_profile_id")
                active_query_id = backend.get_app_state("active_query_id")

                if active_profile_id and active_query_id:
                    try:
                        logger.info(
                            f"[Settings] Wiping ALL data for query: {active_profile_id}/{active_query_id}"
                        )

                        # Import database connection manager
                        from data.database import get_db_connection

                        # Step 1: Delete JIRA issues for this query (CASCADE deletes changelog too)
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM jira_issues WHERE profile_id = ? AND query_id = ?",
                                (active_profile_id, active_query_id),
                            )
                            issues_deleted = cursor.rowcount
                            conn.commit()
                            logger.info(
                                f"[Settings] ✓ Deleted {issues_deleted} JIRA issues"
                            )

                        # Step 2: Delete project statistics for this query
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                                (active_profile_id, active_query_id),
                            )
                            stats_deleted = cursor.rowcount
                            conn.commit()
                            logger.info(
                                f"[Settings] ✓ Deleted {stats_deleted} project statistics"
                            )

                        # Step 3: Delete JIRA cache for this query
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute(
                                "DELETE FROM jira_cache WHERE profile_id = ? AND query_id = ?",
                                (active_profile_id, active_query_id),
                            )
                            cache_deleted = cursor.rowcount
                            conn.commit()
                            logger.info(
                                f"[Settings] ✓ Deleted {cache_deleted} JIRA cache entries"
                            )

                        # Step 4: Invalidate global cache files
                        from data.cache_manager import invalidate_all_cache

                        invalidate_all_cache()
                        logger.info("[Settings] ✓ All global cache files invalidated")

                        # Step 5: Delete metrics for this query (clears cached calculations)
                        try:
                            deleted_count = backend.delete_metrics(
                                active_profile_id, active_query_id
                            )
                            logger.info(
                                f"[Settings] ✓ Deleted {deleted_count} cached metrics"
                            )
                        except Exception as e:
                            logger.warning(f"[Settings] Failed to delete metrics: {e}")

                        # Step 6: Clear in-memory snapshots cache (used by Flow/DORA tabs)
                        try:
                            from data.metrics_snapshots import clear_snapshots_cache

                            clear_snapshots_cache()
                            logger.info(
                                "[Settings] ✓ Cleared in-memory snapshots cache"
                            )
                        except Exception as e:
                            logger.warning(
                                f"[Settings] Failed to clear snapshots cache: {e}"
                            )

                        # Step 7: Delete profile-specific cache files
                        from data.profile_manager import get_active_query_workspace

                        query_workspace = get_active_query_workspace()
                        if query_workspace and query_workspace.exists():
                            jira_cache = query_workspace / "jira_cache.json"
                            if jira_cache.exists():
                                jira_cache.unlink()
                                logger.info(
                                    "[Settings] ✓ Deleted query workspace jira_cache.json"
                                )

                        logger.info("=" * 60)
                        logger.info("[Settings] ✅ COMPLETE DATA WIPE SUCCESSFUL")
                        logger.info(
                            f"[Settings] Deleted: {issues_deleted} issues, {stats_deleted} stats, {cache_deleted} cache"
                        )
                        logger.info(
                            "[Settings] All data will be re-fetched fresh from JIRA"
                        )
                        logger.info("=" * 60)

                    except Exception as e:
                        logger.error(
                            f"[Settings] ❌ Data wipe error: {e}", exc_info=True
                        )
                        # Continue anyway - partial cleanup is better than none
                else:
                    logger.warning(
                        "[Settings] No active query found - skipping data wipe"
                    )

            # CRITICAL FIX: Clear changelog cache only on force refresh
            # Changelog is issue-specific (keyed by issue key), not query-specific
            # Reusing changelog saves 1-2 minutes on subsequent operations
            # NOTE: After database migration, changelog is in DB, not files
            # Force refresh will cause jira_simple.py to delete and re-fetch from JIRA
            if force_refresh_bool:
                logger.info(
                    "[Settings] Force refresh: Changelog will be re-fetched from JIRA"
                )
            else:
                logger.info(
                    "[Settings] Normal refresh: Keeping changelog cache for reuse (saves 1-2 minutes)"
                )

            # Run sync in background thread to allow progress polling
            import threading

            def background_sync():
                """Background thread for JIRA data fetch."""
                logger.info("=" * 70)
                logger.info("[BACKGROUND SYNC] Thread started")
                logger.info(f"[BACKGROUND SYNC] JQL: {settings_jql}")
                logger.info(f"[BACKGROUND SYNC] Force refresh: {force_refresh_bool}")
                logger.info(
                    f"[BACKGROUND SYNC] JIRA endpoint: {final_jira_api_endpoint}"
                )
                logger.info("=" * 70)

                try:
                    logger.info("[BACKGROUND SYNC] Calling sync_jira_scope_and_data...")
                    success, message, scope_data = sync_jira_scope_and_data(
                        settings_jql,
                        jira_config_for_sync,
                        force_refresh=force_refresh_bool,
                    )
                    logger.info(
                        f"[BACKGROUND SYNC] sync_jira_scope_and_data returned: success={success}, message={message}"
                    )

                    if not success:
                        logger.error(f"[BACKGROUND SYNC] Fetch failed: {message}")
                        TaskProgress.fail_task("update_data", message)
                    else:
                        # Fetch completed successfully - now trigger metrics calculation
                        # The progress polling callback will detect "calculate" phase and trigger metrics
                        logger.info(
                            "[BACKGROUND SYNC] Fetch complete, transitioning to calculate phase"
                        )
                        TaskProgress.update_progress(
                            "update_data",
                            "calculate",
                            0,
                            100,
                            "Fetch complete, starting metrics calculation...",
                        )
                except Exception as e:
                    logger.error(f"[BACKGROUND SYNC] Exception: {e}", exc_info=True)
                    TaskProgress.fail_task("update_data", f"Error: {str(e)}")
                finally:
                    logger.info("[BACKGROUND SYNC] Thread exiting")

            logger.info("[Settings] Starting background sync thread...")
            thread = threading.Thread(target=background_sync, daemon=True)
            thread.start()
            logger.info(
                f"[Settings] Background thread started: {thread.name} (alive={thread.is_alive()})"
            )

            # Return immediately to show progress bar - polling will track completion
            return (
                None,  # upload contents
                None,  # filename
                html.Div(
                    [
                        html.I(className="fas fa-spinner fa-spin me-2"),
                        "Fetching data from JIRA...",
                    ],
                    className="text-info small",
                ),  # cache status
                no_update,  # statistics-table
                no_update,  # total-items-input
                no_update,  # estimated-items-input
                no_update,  # total-points-display
                no_update,  # estimated-points-input
                no_update,  # current-settings
                False,  # force-refresh-store (reset)
                True,  # update-data-unified disabled (operation in progress)
                button_normal,  # update-data-unified children
                html.Div(
                    [html.I(className="fas fa-spinner fa-spin me-2"), "Starting..."],
                    className="text-info small",
                ),  # update-data-status
                "",  # app-notifications
                None,  # trigger-auto-metrics-calc
                False,  # progress-poll-interval enabled (start polling)
                []
                if force_refresh_bool
                else no_update,  # current-statistics: CLEAR on force refresh to prevent stale data display
            )

            # OLD SYNCHRONOUS CODE BELOW - NOT REACHED
            if False:
                success = False
                message = ""
                scope_data = {}

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

                # Create detailed success message showing both counts (icon shows success, no text checkmark needed)
                success_details = f"Data loaded: {issues_count} issue{'s' if issues_count != 1 else ''} from JIRA (aggregated into {weekly_count} weekly data point{'s' if weekly_count != 1 else ''})"

                cache_status_message = html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        html.Span(success_details, className="fw-medium"),
                    ],
                    className="text-success small text-center mt-2",
                )
                logger.info(
                    f"[JIRA] Data import successful: {issues_count} issues loaded, {weekly_count} weekly data points created"
                )

                # AUTOMATIC METRICS CALCULATION
                # After database migration, always calculate metrics after data update
                # TODO: Implement changed_keys tracking in database schema for optimization
                should_calculate = True

                logger.info(
                    "[Settings] Post-migration: Always calculating metrics after data update"
                )

                # Metrics calculation will happen in separate callback triggered by store
                # This allows the Update Data callback to return quickly, enabling progress bar updates
                logger.info(
                    f"[Settings] Metrics calculation decision: should_calculate={should_calculate}, force_refresh={force_refresh_bool}"
                )

                # Extract scope values from scope_data to update input fields
                # CRITICAL: Use "remaining_*" fields, NOT "total_*" fields
                # - remaining_items = open/incomplete items (what we want to show)
                # - total_items = ALL items including completed (wrong for parameter panel)
                total_items = scope_data.get("remaining_items", 0) if scope_data else 0
                estimated_items = (
                    scope_data.get("estimated_items", 0) if scope_data else 0
                )
                # Use remaining_total_points (includes extrapolation) not total_points
                total_points = (
                    scope_data.get("remaining_total_points", 0) if scope_data else 0
                )
                estimated_points = (
                    scope_data.get("estimated_points", 0) if scope_data else 0
                )

                # Use actual remaining values from JIRA scope (no window adjustments)
                logger.info(
                    f"[Settings] Using JIRA scope values: {total_items} items, {total_points:.1f} points"
                )

                # Format total_points as string since it's a text display field
                total_points_display = f"{total_points:.1f}"

                logger.info(
                    f"[Settings] Final scope for UI: total_items={total_items}, estimated_items={estimated_items}, total_points={total_points:.1f}, estimated_points={estimated_points}"
                )

                # Update the settings store with new values to trigger dashboard refresh
                from data.persistence import load_app_settings

                current_settings = load_app_settings()
                updated_settings = current_settings.copy()
                updated_settings.update(
                    {
                        "total_items": total_items,
                        "total_points": total_points,
                        "estimated_items": estimated_items,
                        "estimated_points": estimated_points,
                    }
                )

                logger.info(
                    f"[Settings] Updating Store with window-based values: {total_items} items, {total_points:.1f} points"
                )
                logger.info(
                    f"[Settings] Before: total_items={current_settings.get('total_items')}, after: {updated_settings.get('total_items')}"
                )

                # DON'T mark task complete yet if metrics calculation is needed
                # The separate metrics callback will mark it complete
                if not should_calculate:
                    # CRITICAL: Update fetch progress to 100% before completing
                    # When delta fetch finds 0 changes, fetch never updates progress
                    # Must show fetch complete before calling complete_task()
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        issues_count,
                        issues_count,
                        "Delta check complete - no changes",
                    )
                    TaskProgress.complete_task("update_data", f"✓ {success_details}")
                else:
                    # Mark fetch as 100% complete BEFORE transitioning to calculate phase
                    # This ensures progress tracking shows fetch completed and prevents "stuck" detection
                    TaskProgress.update_progress(
                        "update_data",
                        "fetch",
                        issues_count,
                        issues_count,
                        "Fetch complete, preparing metrics...",
                    )

                    # Transition to calculate phase BEFORE returning so progress bar doesn't hide
                    # The separate callback will start calculating immediately after this returns
                    TaskProgress.update_progress(
                        "update_data",
                        "calculate",
                        0,
                        0,
                        "Preparing metrics calculation...",
                    )

                # No delay needed - progress bar polls frequently (250ms) and will detect phase change
                logger.info(
                    "[Settings] Transitioned to calculate phase, returning to trigger metrics callback"
                )

                # Create success toast notification
                success_toast = create_success_toast(
                    success_details,
                    header="Data Updated",
                    duration=5000,
                )

                # Trigger metrics calculation if needed
                import time

                # Use timestamp for calculate, 0 for skip (not None - None is default/uninitialized)
                metrics_trigger = int(time.time() * 1000) if should_calculate else 0

                # Return updated statistics AND scope values to refresh inputs AND settings store
                return (
                    None,
                    None,
                    cache_status_message,
                    updated_statistics,
                    total_items,
                    estimated_items,
                    total_points_display,  # Text field, not number
                    estimated_points,
                    updated_settings,  # Updated settings to trigger dashboard refresh
                    False,  # Reset force refresh store
                    False,  # Enable button
                    button_normal,  # Reset button text
                    "",  # Clear status area (toast shows message now)
                    success_toast,  # Toast notification
                    metrics_trigger,  # Trigger separate metrics calculation
                    False,  # progress-poll-interval enabled (metrics will run)
                    no_update,  # current-statistics
                )
            else:
                # Create detailed error message
                error_details = f"[X] Failed to import JIRA data: {message}"

                cache_status_message = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-danger"
                        ),
                        html.Span(error_details, className="fw-medium"),
                    ],
                    className="text-danger small text-center mt-2",
                )
                error_status_message = html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-danger"
                        ),
                        html.Span(error_details, className="fw-medium"),
                    ],
                    className="text-danger small",
                )
                logger.error(f"[JIRA] Data import failed: {message}")
                # Clear task progress
                TaskProgress.complete_task("update_data", f"❌ {message}")
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
                    no_update,  # Don't update settings on error
                    False,  # Reset force refresh store
                    False,  # Enable button
                    button_normal,  # Reset button text
                    error_status_message,  # Show error in status area
                    "",  # Toast notification (empty)
                    None,  # trigger-auto-metrics-calc
                    False,  # progress-poll-interval enabled (task completed with error)
                    no_update,  # current-statistics
                )

        except ImportError:
            logger.error("[Settings] JIRA integration not available")
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
                className="text-danger small",
            )
            # Clear task progress
            from data.task_progress import TaskProgress

            TaskProgress.complete_task("update_data")
            return (
                None,
                None,
                cache_status_message,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,  # Don't update settings on error
                False,  # Reset force refresh store
                False,  # Enable button
                button_normal,  # Reset button text
                cache_status_message,  # Show error in status area
                "",  # Toast notification (empty)
                None,  # metrics trigger
            )
        except Exception as e:
            logger.error(f"[Settings] Error in unified data update: {e}")
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
                className="text-danger small",
            )
            # Clear task progress
            from data.task_progress import TaskProgress

            TaskProgress.complete_task("update_data")
            return (
                None,
                None,
                cache_status_message,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,  # Don't update settings on error
                False,  # Reset force refresh store
                False,  # Enable button
                button_normal,  # Reset button text
                cache_status_message,  # Show error in status area
                "",  # Toast notification (empty)
                None,  # metrics trigger
                False,  # progress-poll-interval enabled (task completed with error)
                no_update,  # current-statistics
            )

    #######################################################################
    # AUTO METRICS CALCULATION CALLBACK (Triggered after data fetch)
    #######################################################################

    @app.callback(
        [
            Output("trigger-auto-metrics-calc", "data", allow_duplicate=True),
            Output(
                "metrics-refresh-trigger", "data", allow_duplicate=True
            ),  # Refresh DORA/Flow tabs
        ],
        Input("trigger-auto-metrics-calc", "data"),
        prevent_initial_call=True,
    )
    def auto_calculate_metrics_after_fetch(trigger_timestamp):
        """
        Automatically calculate DORA/Flow metrics after data fetch completes.

        This runs in a separate callback to allow the Update Data callback to return quickly,
        enabling progress bar updates during the calculation phase.
        """
        logger.info(
            f"[Settings] Auto-metrics callback triggered with timestamp: {trigger_timestamp}"
        )

        # Import TaskProgress before checking trigger
        from data.task_progress import TaskProgress

        # Check if there's actually an active task in calculate phase
        # This prevents spurious triggers from page refreshes or store resets
        active_task = TaskProgress.get_active_task()
        if not active_task or active_task.get("task_id") != "update_data":
            logger.info(
                "[Settings] No active update_data task, ignoring metrics trigger"
            )
            raise PreventUpdate

        # CRITICAL: Check if metrics calculation already started
        # This prevents multiple triggers from polling callback
        # Only allow if message is initial transition message OR hasn't been set yet
        calc_progress = active_task.get("calculate_progress", {})
        calc_message = calc_progress.get("message", "")
        allowed_messages = ["", "Fetch complete, starting metrics calculation..."]
        if calc_message not in allowed_messages:
            logger.info(
                f"[Settings] Metrics already started (message='{calc_message[:50]}'), ignoring duplicate trigger"
            )
            raise PreventUpdate

        if trigger_timestamp is None:
            # None means no trigger - this is the initial/default store state
            # Don't take any action
            logger.info(
                "[Settings] Trigger timestamp is None (initial store state), ignoring"
            )
            return None, None

        if trigger_timestamp == 0:
            # 0 means fetch completed but explicitly skipped metrics calculation
            # Complete the task without calculating metrics
            logger.info(
                "[Settings] Trigger timestamp is 0 - fetch completed, no metrics calculation needed"
            )
            TaskProgress.complete_task(
                "update_data",
                "✓ Data updated (no metrics recalculation needed)",
            )
            return None, None

        logger.info(
            "[Settings] Auto-metrics calculation triggered by data fetch completion"
        )

        try:
            # Load statistics first to verify fetch completed successfully
            from data.persistence import load_statistics

            statistics, _ = load_statistics()

            # If no statistics exist, the fetch was interrupted - fail the task
            if not statistics or len(statistics) == 0:
                logger.error(
                    "[Settings] No statistics found - fetch was likely interrupted during app restart"
                )
                TaskProgress.fail_task(
                    "update_data",
                    "Fetch incomplete - please restart the Update Data operation",
                )
                return None, None

            # Calculate total weeks FIRST so we can show accurate progress immediately
            from data.iso_week_bucketing import get_weeks_from_date_range
            from datetime import datetime

            # Extract date range from statistics
            dates = [datetime.fromisoformat(stat["date"]) for stat in statistics]
            start_date = min(dates)
            end_date = max(dates)

            # Get weeks covering the actual data range
            custom_weeks = get_weeks_from_date_range(start_date, end_date)
            total_weeks = len(custom_weeks)

            # Phase transition already done by the fetch callback before it returned
            # Update progress with correct total to show accurate progress bar
            TaskProgress.update_progress(
                "update_data",
                "calculate",
                0,
                total_weeks,
                "Starting metrics calculation...",
            )

            # Clear existing metrics for this query to force fresh calculation
            # This ensures field mapping and configuration changes are reflected
            logger.info(
                "[Settings] Clearing existing metrics for active query to force fresh calculation"
            )
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_profile_id = backend.get_app_state("active_profile_id")
            active_query_id = backend.get_app_state("active_query_id")

            if active_profile_id and active_query_id:
                try:
                    # Delete metrics for this specific profile/query combination
                    backend.delete_metrics(active_profile_id, active_query_id)
                    # Also clear in-memory snapshots cache (used by Flow/DORA tabs)
                    from data.metrics_snapshots import clear_snapshots_cache

                    clear_snapshots_cache()
                    logger.info(
                        f"[Settings] Deleted existing metrics and cleared snapshots cache for {active_profile_id}/{active_query_id}"
                    )
                except Exception as e:
                    logger.warning(f"[Settings] Failed to clear metrics cache: {e}")

            logger.info("[Settings] Metrics will be recalculated and saved to database")

            # Statistics already validated above - proceed with calculation
            from data.metrics_calculator import calculate_metrics_for_last_n_weeks

            def metrics_progress_callback(message: str):
                """Update TaskProgress during metrics calculation."""
                logger.debug(f"[Metrics Progress] {message}")
                # Extract week number from message if present (e.g., "Week 2025-W51")
                import re

                week_match = re.search(r"Week (\d{4}-W\d{2})", message)
                if week_match:
                    # Find which week we're on
                    current_week = week_match.group(1)
                    for idx, week in enumerate(custom_weeks, start=1):
                        if week == current_week:
                            TaskProgress.update_progress(
                                "update_data",
                                "calculate",
                                idx,
                                total_weeks,
                                message,
                            )
                            break
                # CRITICAL: Do NOT update progress for inner messages (e.g., "[Filter] ...")
                # These don't have week numbers, and updating with current=0 resets the progress bar
                # Only update when we have actual week progress to report

            # Run metrics calculation in background thread to prevent blocking
            import threading

            def background_metrics():
                try:
                    metrics_success, metrics_message = (
                        calculate_metrics_for_last_n_weeks(
                            custom_weeks=custom_weeks,
                            progress_callback=metrics_progress_callback,
                        )
                    )

                    if metrics_success:
                        logger.info(
                            f"[Settings] Auto-calculated metrics: {metrics_message}"
                        )
                        TaskProgress.complete_task(
                            "update_data", "✓ Data and metrics updated successfully"
                        )
                    else:
                        logger.warning(
                            f"[Settings] Metrics calculation had issues: {metrics_message}"
                        )
                        TaskProgress.complete_task(
                            "update_data",
                            "⚠ Data updated, metrics calculation had issues",
                        )
                except Exception as e:
                    logger.error(
                        f"[Settings] Background metrics calculation failed: {e}",
                        exc_info=True,
                    )
                    TaskProgress.fail_task(
                        "update_data", "⚠ Data updated, metrics calculation failed"
                    )

            thread = threading.Thread(target=background_metrics, daemon=True)
            thread.start()
            logger.info("[Settings] Metrics calculation started in background thread")

        except Exception as e:
            logger.error(f"[Settings] Auto-metrics setup failed: {e}", exc_info=True)
            TaskProgress.fail_task(
                "update_data", "⚠ Data updated, metrics calculation failed"
            )

        # Return immediately - background thread will complete the task
        return None, None

    @app.callback(
        [],
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
                status_message = "[!] JIRA is not configured. Please click the 'Configure JIRA' button to set up your JIRA connection before calculating project scope."
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
            from data.persistence import calculate_project_scope_from_jira

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
                            status_message = f"[!] Points field '{field_name}' not found in any JIRA issues. Only total item count ({total_items}) calculated. Check if '{field_name}' exists in your JIRA project and verify your JQL query includes issues with this field."
                        elif field_coverage < 50:
                            status_message = f"[!] Points field '{field_name}' has insufficient coverage ({field_coverage:.0f}% of issues have the field, need ≥50%). Found in {field_exists_count} of {sample_size} sample issues, with {valid_points_count} having point values. Only total item count ({total_items}) calculated. Consider refining your JQL query to include more issues with this field, or verify '{field_name}' is the correct custom field name."
                        else:
                            # This shouldn't happen if points_field_available is False, but just in case
                            status_message = f"[!] Points field '{field_name}' validation failed unexpectedly ({field_coverage:.0f}% coverage). Only total item count ({total_items}) calculated."
                    else:
                        status_message = f"[!] No points field configured. Only total item count ({total_items}) calculated. Configure a valid points field for full scope calculation."

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

                # Use actual remaining values from JIRA scope (no window adjustments)
                logger.info(
                    f"[Settings] Using JIRA scope values: {total_items} items, {estimated_points:.1f} points"
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
            logger.error(f"[Settings] Error in JIRA scope calculation callback: {e}")
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
            Output("jira-query-profile-selector", "options", allow_duplicate=True),
            Output(
                "jira-query-profile-selector-mobile", "options", allow_duplicate=True
            ),
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            Output("jira-query-profile-selector-mobile", "value", allow_duplicate=True),
            Output("query-name-input", "value", allow_duplicate=True),
            Output("query-description-input", "value", allow_duplicate=True),
            Output("query-name-validation", "children", allow_duplicate=True),
            Output("query-name-validation", "style", allow_duplicate=True),
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
                    label += " [Default]"  # Add indicator for default
                updated_options.append({"label": label, "value": profile["id"]})

            # Get the saved profile ID to select it
            saved_profile_id = saved_profile["id"] if saved_profile else None

            logger.info(
                f"[SAVE CALLBACK] Returning {len(updated_options)} options, selecting profile ID: {saved_profile_id}"
            )
            logger.info(
                f"[SaveProfile] Options being returned: {[opt['label'] for opt in updated_options]}"
            )

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
            logger.error(f"[Settings] Error saving query profile: {e}")
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
        prevent_initial_call="initial_duplicate",  # Allow initial call while using allow_duplicate
    )
    def sync_dropdowns_and_show_buttons(desktop_profile_id, mobile_profile_id):
        """Sync both dropdowns, show/hide profile action buttons, and persist selection."""
        # Determine which dropdown triggered the change
        ctx = callback_context

        # Handle initial call (no trigger) - use desktop dropdown value
        if not ctx.triggered:
            logger.info(
                "DEBUG: sync_dropdowns_and_show_buttons - initial call, using desktop dropdown value"
            )
            selected_profile_id = desktop_profile_id
            # Don't sync dropdowns on initial call, only set button visibility
            trigger_id = None
        else:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

            # Determine which dropdown value to use based on trigger
            if trigger_id == "jira-query-profile-selector-mobile":
                selected_profile_id = mobile_profile_id
            elif trigger_id == "jira-query-profile-selector":
                selected_profile_id = desktop_profile_id
            else:
                # Unknown trigger, don't sync
                logger.info(
                    f"[Settings] DEBUG: Unknown trigger: {trigger_id}, skipping sync"
                )
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )

        logger.info(
            f"DEBUG: sync_dropdowns_and_show_buttons called with profile_id: {selected_profile_id}"
        )

        # Persist the selected profile ID and JQL to app_settings.json
        # When user selects a profile from dropdown, save both the profile ID and its JQL
        try:
            from data.persistence import load_app_settings, save_app_settings
            from data.jira_query_manager import get_query_profile_by_id

            app_settings = load_app_settings()
            current_profile_id = app_settings.get("active_jql_profile_id", "")

            # Only save if triggered by user interaction (not initial load)
            if trigger_id is not None and selected_profile_id != current_profile_id:
                # Get the JQL from the selected profile
                jql_to_save = app_settings.get("jql_query", "")
                if selected_profile_id:
                    profile = get_query_profile_by_id(selected_profile_id)
                    if profile:
                        jql_to_save = profile.get("jql", jql_to_save)
                        logger.info(
                            f"[Settings] Saving JQL from profile: {profile.get('name')}"
                        )

                save_app_settings(
                    pert_factor=app_settings["pert_factor"],
                    deadline=app_settings["deadline"],
                    data_points_count=app_settings.get("data_points_count"),
                    show_milestone=app_settings.get("show_milestone"),
                    milestone=app_settings.get("milestone"),
                    show_points=app_settings.get("show_points"),
                    jql_query=jql_to_save,  # Save the profile's JQL
                    last_used_data_source=app_settings.get("last_used_data_source"),
                    active_jql_profile_id=selected_profile_id or "",
                )
                logger.info(
                    f"Persisted profile ID: {selected_profile_id} with JQL: {jql_to_save[:50]}..."
                )
        except Exception as e:
            logger.error(f"[Settings] Error persisting profile selection: {e}")
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
                logger.info(
                    "[Settings] DEBUG: No profile selected, hiding management buttons"
                )
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

                # On initial call, don't update dropdown values (they're already set in UI)
                desktop_value = no_update if trigger_id is None else selected_profile_id
                mobile_value = no_update if trigger_id is None else selected_profile_id

                return (
                    desktop_value,  # desktop dropdown
                    mobile_value,  # mobile dropdown
                    visible_style,  # edit button
                    load_default_style,  # load default button
                    visible_style,  # delete button
                    selected_profile["name"],  # delete query name
                )
            else:
                # Profile not found - hide action buttons
                logger.info("[Settings] DEBUG: Profile not found, hiding buttons")

                # Show load default button if there's a default query
                load_default_style = visible_style if default_query else hidden_style

                # On initial call, don't update dropdown values (they're already set in UI)
                desktop_value = no_update if trigger_id is None else selected_profile_id
                mobile_value = no_update if trigger_id is None else selected_profile_id

                return (
                    desktop_value,  # desktop dropdown
                    mobile_value,  # mobile dropdown
                    hidden_style,  # edit button
                    load_default_style,  # load default button
                    hidden_style,  # delete button
                    "",  # delete query name
                )

        except Exception as e:
            logger.error(f"[Settings] Error in sync_dropdowns_and_show_buttons: {e}")
            return (
                selected_profile_id,
                selected_profile_id,
                hidden_style,
                hidden_style,
                hidden_style,
                "",
            )

    @app.callback(
        Output("delete-jql-query-modal", "is_open", allow_duplicate=True),
        [Input("cancel-delete-query-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def handle_delete_query_modal_cancel(cancel_clicks):
        """Close modal when cancel button clicked."""
        if not cancel_clicks:
            raise PreventUpdate
        # Close modal
        return False

    # REMOVED: Confirmation text validation - users can now delete with just a button click

    @app.callback(
        Output("jira-query-profile-selector", "options", allow_duplicate=True),
        Output("jira-query-profile-selector", "value"),
        [Input("confirm-delete-query-button", "n_clicks")],
        [
            State("jira-query-profile-selector", "value"),
            State("delete-query-name", "children"),
        ],
        prevent_initial_call=True,
    )
    def delete_query_profile(delete_clicks, current_profile_id, query_name):
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
                    label += " [Default]"  # Add indicator for default
                updated_options.append({"label": label, "value": profile["id"]})

            # Keep dropdown clean for saved queries only

            # Set to first profile or None if none exist
            default_value = profiles[0]["id"] if profiles else None

            return updated_options, default_value

        except Exception as e:
            logger.error(f"[Settings] Error deleting query profile: {e}")
            raise PreventUpdate

    @app.callback(
        [
            Output("query-selector", "options", allow_duplicate=True),
            Output("query-selector", "value", allow_duplicate=True),
            Output("query-jql-editor", "value", allow_duplicate=True),
            Output("query-name-input", "value", allow_duplicate=True),
            Output("jira-jql-query", "value", allow_duplicate=True),
            Output("delete-jql-query-modal", "is_open", allow_duplicate=True),
        ],
        [Input("confirm-delete-query-button", "n_clicks")],
        [
            State("query-selector", "value"),
            State("delete-query-name", "children"),
        ],
        prevent_initial_call=True,
    )
    def delete_query_from_selector(delete_clicks, current_query_id, query_name):
        """Delete the selected query from query selector."""
        if not delete_clicks or not current_query_id:
            raise PreventUpdate

        try:
            from data.query_manager import (
                delete_query,
                list_queries_for_profile,
                get_active_profile_id,
                get_active_query_id,
                switch_query,
            )

            profile_id = get_active_profile_id()
            active_query_id = get_active_query_id()

            # If trying to delete the active query, switch to a different query first (if available)
            if current_query_id == active_query_id:
                queries = list_queries_for_profile(profile_id)
                other_queries = [q for q in queries if q.get("id") != current_query_id]

                if other_queries:
                    # Switch to the first available query
                    new_active_query_id = other_queries[0].get("id")
                    if new_active_query_id:
                        switch_query(new_active_query_id)
                # If no other queries, we'll end up with no active query (empty state)

            # Delete the query (allow deletion of last query)
            delete_query(profile_id, current_query_id, allow_cascade=True)

            logger.info(
                f"Deleted query '{current_query_id}' from profile '{profile_id}' via modal"
            )

            # Reload query selector options and get active query data
            updated_queries = list_queries_for_profile(profile_id)
            options = [{"label": "→ Create New Query", "value": "__create_new__"}]
            active_value = ""
            active_jql = ""
            active_name = ""

            for query in updated_queries:
                label = query.get("name", "Unnamed Query")
                value = query.get("id", "")
                if query.get("is_active", False):
                    label += " [Active]"
                    active_value = value
                    active_jql = query.get("jql", "")
                    active_name = query.get("name", "")
                options.append({"label": label, "value": value})

            # Return: options, value, jql_editor, name_input, legacy_jql, modal_closed
            return options, active_value, active_jql, active_name, active_jql, False

        except Exception as e:
            logger.error(f"[Settings] Error deleting query from selector: {e}")
            raise PreventUpdate

    @app.callback(
        Output(
            "jira-jql-query", "value"
        ),  # JQL textarea uses standard "value" property
        [Input("jira-query-profile-selector", "value")],
        prevent_initial_call=True,  # Only load when user explicitly selects a profile
    )
    def update_jql_from_profile(selected_profile_id):
        """Update JQL textarea when a profile is selected by the user."""
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
            logger.error(f"[Settings] Error loading profile JQL: {e}")
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
                status_text = f"[List] Using saved query: {profile['name']}"
                if profile.get("is_default", False):
                    status_text += " [*]"
                return status_text
            else:
                return ""

        except Exception as e:
            logger.error(f"[Settings] Error getting profile status: {e}")
            return ""

    # NOTE: Old edit query modal callback removed - replaced by query_switching.py callback
    # Old callback used edit-jql-query-button which doesn't exist in Phase 4 UI
    # New callback in query_switching.py uses edit-query-btn and query_manager functions

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
        ],
        prevent_initial_call=True,
    )
    def update_query_profile(
        edit_clicks,
        query_name,
        description,
        jql_value,
        current_profile_id,
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
                save_query_profile,
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

                # Reload options
                updated_options = []
                profiles = load_query_profiles()
                for profile in profiles:
                    label = profile["name"]
                    if profile.get("is_default", False):
                        label += " [Default]"  # Add indicator for default
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
            logger.error(f"[Settings] Error updating query profile: {e}")
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
            Output("import-export-collapse", "is_open", allow_duplicate=True),
        ],
        Input("btn-expand-parameters", "n_clicks"),
        [
            State("parameter-collapse", "is_open"),
            State("parameter-panel-state", "data"),
            State("settings-collapse", "is_open"),
            State("import-export-collapse", "is_open"),
        ],
        prevent_initial_call=True,
    )
    def toggle_parameter_panel(
        n_clicks, is_open, panel_state, settings_is_open, import_export_is_open
    ):
        """
        Toggle parameter panel expand/collapse and persist state to localStorage.

        This callback supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
        It toggles the collapse state and persists the user preference to localStorage
        so the panel state is maintained across sessions.

        Also ensures only one flyout panel is open at a time by closing other panels
        when parameter panel opens.

        Args:
            n_clicks: Number of times expand button was clicked
            is_open: Current state of the collapse component
            panel_state: Current parameter panel state from dcc.Store
            settings_is_open: Current settings panel state
            import_export_is_open: Current import/export panel state

        Returns:
            tuple: (new_is_open, updated_panel_state, new_settings_state, new_import_export_state)
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

            # If opening parameter panel, close other panels
            new_settings_state = no_update
            new_import_export_state = no_update

            if new_is_open:
                if settings_is_open:
                    new_settings_state = False
                if import_export_is_open:
                    new_import_export_state = False

            return (
                new_is_open,
                updated_state,
                new_settings_state,
                new_import_export_state,
            )

        return is_open, panel_state, no_update, no_update

    @app.callback(
        Output("parameter-bar-collapsed", "children"),
        [
            Input("pert-factor-slider", "value"),  # FIXED: use correct component ID
            Input(
                "deadline-picker", "date"
            ),  # FIXED: use correct component and property
            Input(
                "total-items-input", "value"
            ),  # FIXED: use Remaining Items (not Estimated Items)
            Input(
                "total-points-display", "value"
            ),  # FIXED: use Remaining Points (auto) - the calculated total
            Input("data-points-input", "value"),  # Add data points input
            Input("current-settings", "modified_timestamp"),  # Add to get show_points
        ],
        [State("current-settings", "data")],
        prevent_initial_call=False,  # Update on initial load
    )
    def update_parameter_summary(
        pert_factor,
        deadline,
        scope_items,
        scope_points,
        data_points,
        settings_ts,
        settings,
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

        # Parse scope_points - it comes from total-points-display which is a text input
        # Value may be a string like "1064" or a float
        try:
            scope_points = float(scope_points) if scope_points else 0
        except (ValueError, TypeError):
            scope_points = 0

        # Get show_points setting
        show_points = settings.get("show_points", True) if settings else True

        # Use the scope_items and scope_points directly:
        # - scope_items comes from total-items-input (Remaining Items at START of window)
        # - scope_points comes from total-points-display (Remaining Points auto-calculated)
        # Both values are already calculated in serve_layout() and the slider callback
        remaining_items = scope_items if scope_items > 0 else None
        remaining_points = scope_points if scope_points > 0 else None

        logger.info(
            f"Banner callback - remaining_items: {remaining_items}, remaining_points: {remaining_points}"
        )

        # Get active profile and query names for display
        from data.profile_manager import get_active_profile_and_query_display_names

        display_names = get_active_profile_and_query_display_names()
        profile_name = display_names.get("profile_name")
        query_name = display_names.get("query_name")

        # Use the shared function to create the banner - no more duplicate code!
        banner_content = create_parameter_bar_collapsed(
            pert_factor=pert_factor,
            deadline=deadline,
            scope_items=scope_items,
            scope_points=round(scope_points, 1),  # type: ignore[arg-type]
            remaining_items=scope_items,  # Display as Remaining
            remaining_points=round(scope_points, 1),  # type: ignore[arg-type]
            total_items=scope_items,  # Remaining Items
            total_points=round(scope_points, 1),  # type: ignore[arg-type]
            show_points=show_points,
            data_points=data_points,
            profile_name=profile_name,
            query_name=query_name,
        )

        # Extract just the Row children from the returned html.Div
        # Type note: create_parameter_bar_collapsed always returns html.Div with children
        return banner_content.children[0]  # type: ignore[index]

    # Callback to update Data Points slider marks dynamically when statistics change
    @app.callback(
        [
            Output("data-points-input", "max"),
            Output("data-points-input", "marks"),
            Output("data-points-input", "value"),
        ],
        [Input("current-statistics", "data")],
        [State("data-points-input", "value")],
        prevent_initial_call=False,
    )
    def update_data_points_slider_marks(statistics, current_value):
        """
        Update Data Points slider max, marks, and value when statistics data changes.

        This ensures the slider reflects the current data size after fetching
        new data from JIRA or importing data. The slider value is clamped to the
        new maximum to prevent invalid states when switching between queries.

        Args:
            statistics: List of statistics data points
            current_value: Current slider value (to be clamped if needed)

        Returns:
            Tuple: (max_value, marks_dict, clamped_value) for the data points slider
        """
        # Calculate max data points from statistics
        max_data_points = 52  # Default max
        if statistics and len(statistics) > 0:
            max_data_points = len(statistics)

        # Calculate dynamic marks for Data Points slider
        # For small datasets, show all values. For larger datasets, show 5 evenly spaced marks.
        min_data_points = 4
        range_size = max_data_points - min_data_points

        # If range is small (<=12 weeks), show all intermediate values
        # This provides better granularity for datasets up to 16 weeks total (4-16)
        if range_size <= 12:
            data_points_marks = {
                i: {"label": str(i)}
                for i in range(min_data_points, max_data_points + 1)
            }
        else:
            # For larger ranges, calculate 5 evenly-spaced marks using rounding
            # This avoids skipping values and provides better distribution
            quarter_point = round(min_data_points + range_size / 4)
            middle_point = round(min_data_points + range_size / 2)
            three_quarter_point = round(min_data_points + 3 * range_size / 4)

            # Ensure no duplicates by using a set, then convert to dict
            mark_values = sorted(
                {
                    min_data_points,
                    quarter_point,
                    middle_point,
                    three_quarter_point,
                    max_data_points,
                }
            )
            data_points_marks = {val: {"label": str(val)} for val in mark_values}

        # Clamp current value to new maximum
        # This prevents the slider value from being higher than the available data
        # when switching from a query with more weeks to one with fewer weeks
        clamped_value = current_value if current_value else max_data_points
        if clamped_value > max_data_points:
            clamped_value = max_data_points
            logger.info(
                f"Data Points slider value clamped from {current_value} to {clamped_value} (max={max_data_points})"
            )

        logger.info(
            f"Data Points slider updated: max={max_data_points}, marks={list(data_points_marks.keys())}, value={clamped_value}"
        )

        return max_data_points, data_points_marks, clamped_value

    # NOTE: Initial values are now calculated directly in ui/layout.py serve_layout()
    # This ensures consistent values between app load and slider interaction
    # No separate initialization callback needed

    # Callback to reload remaining work scope after metrics calculation completes
    @app.callback(
        [
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("calculation-results", "data", allow_duplicate=True),
        ],
        [Input("metrics-refresh-trigger", "data")],
        [State("current-statistics", "data"), State("data-points-input", "value")],
        prevent_initial_call=True,
    )
    def reload_scope_after_metrics(refresh_trigger, statistics, data_points_count):
        """
        Reload scope data from database after metrics calculation completes.

        SOLUTION 1: This callback reloads the BASE scope from database (full JIRA data)
        and then recalculates the WINDOWED scope based on the current data points slider value.
        This ensures parameter panel shows values consistent with the selected time window.

        Args:
            refresh_trigger: Timestamp when metrics calculation completed
            statistics: Current statistics data
            data_points_count: Current data points slider value

        Returns:
            Tuple: (estimated_items, remaining_items, estimated_points, remaining_points_display, calc_results)
        """
        if not refresh_trigger:
            raise PreventUpdate

        logger.info(
            f"[Settings] Reloading BASE scope from database after metrics, then calculating WINDOWED scope for {data_points_count} data points"
        )

        # SOLUTION 1: Calculate windowed scope based on current slider position
        # This ensures the parameter panel always shows values for the selected time window
        result = calculate_remaining_work_for_data_window(data_points_count, statistics)

        if result:
            logger.info(
                f"[Settings] Scope reloaded and windowed: estimated_items={result[0]}, remaining_items={result[1]}, estimated_points={result[2]}, remaining_points={result[3]}"
            )
            return result
        else:
            logger.warning(
                "[Settings] Failed to calculate windowed scope after metrics reload"
            )
            raise PreventUpdate

    # Callback to recalculate remaining work scope when data points slider changes
    @app.callback(
        [
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("calculation-results", "data", allow_duplicate=True),
        ],
        [Input("data-points-input", "value")],
        [
            State("current-statistics", "data"),
            State("app-init-complete", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_remaining_work_on_data_points_change(
        data_points_count, statistics, init_complete
    ):
        """
        SOLUTION 1: Recalculate WINDOWED remaining work scope when Data Points slider changes.

        This is the PRIMARY callback that ensures parameter panel values reflect the selected
        time window. All values are calculated on-the-fly from base statistics data.

        When the user adjusts the Data Points slider to use fewer historical weeks,
        the remaining work should reflect the scope at the START of that time window.
        For example, if using the last 10 weeks of data, show the remaining items/points
        as they were 10 weeks ago, not the current values.

        Args:
            data_points_count: Number of data points selected on the slider
            statistics: List of statistics data points
            init_complete: Whether app initialization is complete

        Returns:
            Tuple: (estimated_items, remaining_items, estimated_points, remaining_points, calc_results)
        """
        logger.info(
            f"[Settings] Data Points slider callback fired: data_points={data_points_count}, "
            f"init_complete={init_complete}, statistics count={len(statistics) if statistics else 0}"
        )

        if not init_complete or not statistics or not data_points_count:
            raise PreventUpdate

        # Use the helper function to calculate remaining work
        result = calculate_remaining_work_for_data_window(data_points_count, statistics)

        if result:
            return result
        else:
            raise PreventUpdate

    #######################################################################
    # TASK PROGRESS RESTORATION ON PAGE LOAD
    #######################################################################

    @app.callback(
        [
            Output("jira-cache-status", "children", allow_duplicate=True),
            Output(
                "progress-poll-interval", "disabled", allow_duplicate=True
            ),  # Enable progress polling
            Output(
                "update-data-progress-container", "style", allow_duplicate=True
            ),  # Show progress bar
            Output(
                "update-data-unified", "style", allow_duplicate=True
            ),  # Button visibility
            Output(
                "cancel-operation-btn", "style", allow_duplicate=True
            ),  # Button visibility
            Output(
                "trigger-auto-metrics-calc", "data", allow_duplicate=True
            ),  # Trigger metrics if in calculate phase
        ],
        Input("url", "pathname"),
        prevent_initial_call="initial_duplicate",  # Run on initial page load with duplicates
    )
    def restore_update_data_progress(pathname):
        """Restore progress bar, button visibility, and polling if task is in progress on page load.

        This callback runs on page load to check if an Update Data task
        was in progress before the page was refreshed or app restarted.
        If so, it restores button visibility from ui_state and enables progress bar polling.

        Args:
            pathname: Current URL pathname (triggers on page load)

        Returns:
            Tuple of (status message, polling enabled, progress bar style, update button style, cancel button style, metrics trigger)
        """
        from data.task_progress import TaskProgress
        from pathlib import Path
        import time

        # Check if app was just restarted (stale task cleanup ran)
        restart_marker = Path("task_progress.json.restart")
        if restart_marker.exists():
            try:
                import json

                marker_data = json.loads(restart_marker.read_text())
                restart_time = marker_data.get("restart_time", 0)
                # If restart was within last 5 seconds, don't restore progress
                if time.time() - restart_time < 5:
                    logger.info(
                        "[Settings] App restart detected - not restoring stale task progress"
                    )
                    restart_marker.unlink()  # Clean up marker
                    raise PreventUpdate
                else:
                    # Old marker, ignore it
                    restart_marker.unlink()
            except Exception as e:
                logger.debug(f"Restart marker check failed: {e}")

        # Check if Update Data task is active
        active_task = TaskProgress.get_active_task()

        # CRITICAL: get_active_task() only returns in_progress tasks, filters out complete/error
        # This prevents restoring stale completed tasks after page refresh
        if (
            active_task
            and active_task.get("task_id") == "update_data"
            and active_task.get("status") == "in_progress"
        ):
            # Task is in progress - enable progress bar polling
            # Button visibility will be automatically restored by polling callback reading ui_state
            logger.info(
                "[Settings] Restoring Update Data progress state on page load - enabling progress bar polling"
            )

            status_message = html.Div(
                [
                    html.I(className="fas fa-spinner fa-spin me-2 text-primary"),
                    html.Span(
                        TaskProgress.get_task_status_message("update_data")
                        or "Updating data...",
                        className="fw-medium",
                    ),
                ],
                className="text-primary small text-center mt-2",
            )

            # Check if we're in calculate phase and need to trigger metrics
            metrics_trigger = None
            phase = active_task.get("phase")
            fetch_progress = active_task.get("fetch_progress", {})
            fetch_percent = fetch_progress.get("percent", 0)

            logger.info(
                f"[Settings] Recovery check: phase={phase}, fetch_percent={fetch_percent}"
            )

            if phase == "calculate":
                # Page was refreshed during or after fetch - trigger metrics calculation
                logger.info(
                    "Task in calculate phase on page load - triggering metrics calculation"
                )
                metrics_trigger = int(time.time() * 1000)
            elif phase == "fetch" and fetch_percent == 0:
                # RECOVERY: Stuck in fetch phase with 0% progress
                # After migration, always assume changes exist and calculate metrics
                logger.warning(
                    "[Settings] Recovery: Task stuck at fetch 0%. Post-migration assumes changes exist."
                )

                # Update progress to show fetch complete
                TaskProgress.update_progress(
                    "update_data",
                    "calculate",
                    0,
                    0,
                    "Preparing metrics calculation...",
                )
                metrics_trigger = int(time.time() * 1000)

            # Read button visibility from ui_state (immediate restore on page load)
            ui_state = active_task.get("ui_state", {})
            operation_in_progress = ui_state.get("operation_in_progress", True)

            update_data_style = {"display": "none"} if operation_in_progress else {}
            cancel_button_style = {} if operation_in_progress else {"display": "none"}

            logger.info(
                f"[Settings] Restoring button visibility: operation_in_progress={operation_in_progress}"
            )

            # Enable progress polling and show progress bar with correct button visibility
            return (
                status_message,  # Show status
                False,  # Enable progress polling
                {"display": "block", "minHeight": "60px"},  # Show progress bar
                update_data_style,  # Button visibility from ui_state
                cancel_button_style,  # Button visibility from ui_state
                metrics_trigger,  # Trigger metrics if in calculate phase
            )

        # No active task - return normal state
        return (
            "",  # No status message
            True,  # Disable progress polling
            {"display": "none"},  # Hide progress bar
            {},  # Show Update Data button
            {"display": "none"},  # Hide Cancel button
            no_update,  # No metrics trigger
        )
