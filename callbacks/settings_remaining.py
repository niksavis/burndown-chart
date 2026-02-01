"""
Settings Callbacks Module - Remaining Callbacks

This module contains callbacks that are yet to be refactored into focused modules.
These will be gradually migrated to the callbacks/settings package.

Remaining callback groups:
- Data update & JIRA integration (massive ~1000 line callback)
- Metrics calculation
- JIRA scope calculation
- JQL query profile management
- Parameter panel UI
"""

#######################################################################
# IMPORTS
#######################################################################

from dash import (
    Input,
    Output,
    State,
    html,
    no_update,
)
from dash.exceptions import PreventUpdate

from configuration import (
    DEFAULT_PERT_FACTOR,
    logger,
)
from ui.parameter_panel import create_parameter_bar_collapsed

# Import helper functions from refactored package
from callbacks.settings.helpers import (
    calculate_remaining_work_for_data_window,
)

#######################################################################
# CALLBACKS
#######################################################################


def register(app):
    """
    Register remaining settings callbacks that are yet to be refactored.

    Note: Core settings callbacks (total points calculation, settings reload/sync)
    are now in callbacks/settings/core_settings.py and should not be duplicated here.

    Args:
        app: Dash application instance
    """
    # NOTE: The following callbacks have been moved to refactored modules:
    # core_settings.py:
    #   - update_total_points_calculation
    #   - update_remaining_points_formula
    #   - reload_settings_after_import_or_switch
    #   - sync_ui_inputs_with_settings
    #   - update_and_save_settings
    # data_update.py:
    #   - handle_unified_data_update (massive ~980 line callback with background threading)
    #   - Clientside callback for force refresh detection
    # metrics.py:
    #   - auto_calculate_metrics_after_fetch (automatic DORA/Flow metrics calculation)
    # jira_scope.py:
    #   - calculate_jira_project_scope (calculate project scope from JIRA)
    # query_profiles.py:
    #   - JQL query profile management (save, edit, delete, sync)
    #   - Profile selection and persistence
    #   - Default query loading
    #   - Character count display (clientside)

    #######################################################################
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
            from data.jira import test_jql_query, validate_jql_for_scriptrunner
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
            from data.jira import construct_jira_endpoint

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

        # CRITICAL FIX: If deadline from picker is None, user may have entered invalid input
        # Use deadline from settings store (database) as fallback instead of hardcoded default
        # NOTE: Deadline is optional - health score uses schedule_variance with graceful degradation
        if deadline is None:
            deadline = settings.get("deadline") if settings else None
            if deadline is None:
                deadline = (
                    "2025-12-31"  # Final fallback prevents banner from showing "None"
                )
                logger.warning(
                    "[Banner] Deadline is None (possibly invalid input in date picker). "
                    "Using default: 2025-12-31 for banner display. "
                    "NOTE: Deadline is optional - health score and forecasts use graceful degradation."
                )
            else:
                logger.info(
                    f"[Banner] Deadline from picker is None, using stored value from database: {deadline}"
                )

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
