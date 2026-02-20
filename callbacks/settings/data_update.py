"""
Data Update Callbacks

This module handles JIRA data synchronization callbacks:
- handle_unified_data_update: Main data fetch callback with background threading
- Clientside callback for force refresh detection

This is a large callback (~980 lines) that coordinates:
- JIRA connection validation
- Query switching
- Force refresh/data wipe logic
- Background threading for data fetch
- Progress tracking integration
"""

import threading

from dash import ClientsideFunction, Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate

from configuration import logger


def register(app):
    """
    Register data update callbacks.

    Args:
        app: Dash application instance
    """

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
            Output("total-items-input", "value", allow_duplicate=True),
            Output("estimated-items-input", "value", allow_duplicate=True),
            Output("total-points-display", "value", allow_duplicate=True),
            Output("estimated-points-input", "value", allow_duplicate=True),
            Output("current-settings", "data", allow_duplicate=True),
            Output("force-refresh-store", "data", allow_duplicate=True),
            Output("update-data-unified", "disabled", allow_duplicate=True),
            Output("update-data-unified", "children", allow_duplicate=True),
            Output("update-data-status", "children", allow_duplicate=True),
            Output("app-notifications", "children", allow_duplicate=True),
            Output("trigger-auto-metrics-calc", "data", allow_duplicate=True),
            Output("progress-poll-interval", "disabled", allow_duplicate=True),
            Output("current-statistics", "data", allow_duplicate=True),
        ],
        [
            Input("update-data-unified", "n_clicks"),
            Input("force-refresh-store", "data"),
        ],
        [
            State("jira-jql-query", "value"),
            State("query-selector", "value"),
        ],
        prevent_initial_call="initial_duplicate",
    )
    def handle_unified_data_update(
        n_clicks,
        force_refresh,
        jql_query,
        selected_query_id,
    ):
        """
        Handle unified data update button click (JIRA data source only).

        This callback coordinates the entire data fetch workflow:
        1. Validates JIRA configuration
        2. Switches to selected query
        3. Optionally performs data wipe (force refresh)
        4. Launches background thread for JIRA sync
        5. Returns immediately to enable progress polling

        Args:
            n_clicks: Number of clicks on unified update button
            force_refresh: Force cache refresh flag from clientside store
            jql_query: JQL query for JIRA data source
            selected_query_id: Currently selected query from dropdown

        Returns:
            Tuple of 16 outputs for UI state management
        """
        from dash import ctx

        from data.task_progress import TaskProgress

        triggered_id = ctx.triggered_id if ctx.triggered else None
        triggered_prop = ctx.triggered[0] if ctx.triggered else None

        logger.info("[UPDATE DATA] =========================================")
        logger.info(
            f"[UPDATE DATA] Callback triggered by: {triggered_id} - "
            f"n_clicks={n_clicks}, force_refresh={force_refresh}"
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
            return _initial_state(button_normal)

        try:
            # Check if another task is already running
            is_running, existing_task = TaskProgress.is_task_running()
            if is_running:
                logger.warning(
                    f"Update Data clicked but task already running: {existing_task}"
                )
                return _task_already_running(existing_task, button_normal)

            # Start the task
            if not TaskProgress.start_task("update_data", "Updating data from JIRA"):
                logger.error("Failed to start Update Data task")
                return _task_start_failed(button_normal)

            # Validate JIRA configuration and prepare sync
            result = _prepare_jira_sync(
                jql_query, selected_query_id, force_refresh, button_normal
            )

            if result is not None:
                return result  # Error occurred during preparation

            # All validation passed - get final config and start background sync
            return _start_background_sync(
                jql_query, selected_query_id, force_refresh, button_normal
            )

        except ImportError:
            logger.error("[Settings] JIRA integration not available")
            TaskProgress.complete_task("update_data")
            return _jira_import_error(button_normal)

        except Exception as e:
            logger.error(f"[Settings] Error in unified data update: {e}")
            TaskProgress.complete_task("update_data")
            return _unexpected_error(e, button_normal)


def _initial_state(button_normal):
    """Return initial state for page load."""
    return (
        None,  # upload contents
        None,  # upload filename
        "",  # cache status (empty)
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


def _task_already_running(existing_task, button_normal):
    """Return state when task is already running."""
    message_div = html.Div(
        [
            html.I(className="fas fa-info-circle me-2"),
            f"Operation already in progress: {existing_task}",
        ],
        className="text-warning small",
    )

    return (
        None,  # upload-data contents
        None,  # upload-data filename
        message_div,  # jira-cache-status
        no_update,  # total-items-input
        no_update,  # estimated-items-input
        no_update,  # total-points-display
        no_update,  # estimated-points-input
        no_update,  # current-settings
        False,  # force-refresh-store (reset)
        False,  # update-data-unified disabled (enable button)
        button_normal,  # update-data-unified children
        message_div,  # update-data-status
        "",  # app-notifications (no toast)
        None,  # trigger-auto-metrics-calc
        True,  # progress-poll-interval disabled (already running)
        no_update,  # current-statistics
    )


def _task_start_failed(button_normal):
    """Return state when task fails to start."""
    message_div = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Failed to start operation",
        ],
        className="text-danger small",
    )

    return (
        None,
        None,
        message_div,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        False,
        button_normal,
        message_div,
        "",
        None,
        True,
        no_update,
    )


def _prepare_jira_sync(jql_query, selected_query_id, force_refresh, button_normal):
    """
    Prepare JIRA sync by validating configuration and switching queries.

    Returns None if successful, or error tuple if validation fails.
    """
    from data.jira import validate_jira_config
    from data.persistence import load_app_settings, load_jira_configuration
    from data.task_progress import TaskProgress

    logger.info(
        f"[Settings] Received jql_query from Store: '{jql_query}' (type: {type(jql_query)})"
    )

    # Load JIRA configuration
    jira_config = load_jira_configuration()

    # Switch to selected query BEFORE fetching data
    if selected_query_id and selected_query_id != "__create_new__":
        try:
            from data.query_manager import switch_query

            switch_query(selected_query_id)
            logger.info(
                f"[Settings] Switched to query '{selected_query_id}' before Update Data"
            )
        except Exception as e:
            logger.error(f"[Settings] Failed to switch query before Update Data: {e}")

    # Check if JIRA is configured
    is_configured = (
        jira_config.get("configured", False)
        and jira_config.get("base_url", "").strip() != ""
    )

    if not is_configured:
        message_div = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
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
        logger.warning("[Settings] Attempted to update data without JIRA configuration")
        TaskProgress.complete_task("update_data", "❌ JIRA not configured")

        return (
            None,
            None,
            message_div,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            False,
            False,
            button_normal,
            message_div,
            "",
            None,
            False,
            no_update,
        )

    # Get JQL from active query if input is empty
    app_settings = load_app_settings()
    settings_jql = _resolve_jql_query(jql_query, app_settings)

    logger.info(f"[Settings] JQL Query - Input: '{jql_query}', Final: '{settings_jql}'")

    # Build JIRA config for validation
    jira_config_for_sync = _build_jira_config(jira_config, settings_jql, app_settings)

    # Validate configuration
    is_valid, validation_message = validate_jira_config(jira_config_for_sync)
    if not is_valid:
        message_div = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                html.Div(
                    [
                        html.Span(
                            "Configuration Error", className="fw-bold d-block mb-1"
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
        TaskProgress.complete_task("update_data")

        return (
            None,
            None,
            message_div,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            False,
            False,
            button_normal,
            message_div,
            "",
            None,
            False,
            no_update,
        )

    return None  # Success - no error


def _resolve_jql_query(jql_query, app_settings):
    """Resolve JQL query from input or active query."""
    if not jql_query or not jql_query.strip():
        try:
            from data.persistence.factory import get_backend

            backend = get_backend()
            active_query_id = backend.get_app_state("active_query_id")
            active_profile_id = backend.get_app_state("active_profile_id")

            if active_query_id and active_profile_id:
                query_data = backend.get_query(active_profile_id, active_query_id)
                if query_data:
                    settings_jql = query_data.get("jql", "")
                    logger.info(
                        f"[Settings] Using JQL from active query '{active_query_id}': '{settings_jql}'"
                    )
                    return settings_jql

            logger.warning("[Settings] No active query, using fallback JQL")
        except Exception as e:
            logger.error(f"[Settings] Failed to load JQL from active query: {e}")

        return app_settings.get("jql_query", "project = JRASERVER")

    return jql_query.strip()


def _build_jira_config(jira_config, settings_jql, app_settings):
    """Build JIRA configuration dictionary for sync."""
    from data.jira import construct_jira_endpoint

    base_url = jira_config.get("base_url", "https://jira.atlassian.com")
    api_version = jira_config.get("api_version", "v2")
    points_field_raw = jira_config.get("points_field", "")

    return {
        "api_endpoint": construct_jira_endpoint(base_url, api_version),
        "jql_query": settings_jql,
        "token": jira_config.get("token", ""),
        "story_points_field": points_field_raw
        if isinstance(points_field_raw, str)
        else "",
        "cache_max_size_mb": jira_config.get("cache_size_mb", 100),
        "max_results": jira_config.get("max_results_per_call", 1000),
        "development_projects": app_settings.get("development_projects", []),
        "devops_projects": app_settings.get("devops_projects", []),
        "devops_task_types": app_settings.get("devops_task_types", []),
        "field_mappings": app_settings.get("field_mappings", {}),
    }


def _start_background_sync(jql_query, selected_query_id, force_refresh, button_normal):
    """Start background thread for JIRA data synchronization."""
    from data.persistence import load_app_settings, load_jira_configuration
    from data.task_progress import TaskProgress

    # Reload config for background thread
    app_settings = load_app_settings()
    jira_config = load_jira_configuration()
    settings_jql = _resolve_jql_query(jql_query, app_settings)
    jira_config_for_sync = _build_jira_config(jira_config, settings_jql, app_settings)

    # Convert force_refresh to boolean and check for new queries
    force_refresh_bool = _should_force_refresh(force_refresh)

    # Perform data wipe if force refresh is enabled
    if force_refresh_bool:
        _perform_data_wipe()

    # Log changelog cache strategy
    if force_refresh_bool:
        logger.info("[Settings] Force refresh: Changelog will be re-fetched from JIRA")
    else:
        logger.info(
            "[Settings] Normal refresh: Keeping changelog cache for reuse (saves 1-2 minutes)"
        )

    # Start background thread
    def background_sync():
        """Background thread for JIRA data fetch."""
        from data.jira import sync_jira_scope_and_data

        logger.info("=" * 70)
        logger.info("[BACKGROUND SYNC] Thread started")
        logger.info(f"[BACKGROUND SYNC] JQL: {settings_jql}")
        logger.info(f"[BACKGROUND SYNC] Force refresh: {force_refresh_bool}")
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
                if scope_data.get("skip_metrics"):
                    logger.info(
                        "[BACKGROUND SYNC] No changes detected, skipping metrics calculation"
                    )
                    TaskProgress.start_postprocess(
                        "update_data",
                        message or "No changes detected - using cached data",
                    )
                    return
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

    # Return immediately to show progress bar
    return (
        None,  # upload contents
        None,  # filename
        html.Div(
            [
                html.I(className="fas fa-spinner fa-spin me-2"),
                "Fetching data from JIRA...",
            ],
            className="text-info small",
        ),
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
        ),
        "",  # app-notifications
        None,  # trigger-auto-metrics-calc
        False,  # progress-poll-interval enabled (start polling)
        [] if force_refresh_bool else no_update,  # current-statistics
    )


def _should_force_refresh(force_refresh):
    """Determine if force refresh should be enabled."""
    force_refresh_bool = bool(force_refresh)

    logger.info(
        f"[Settings] force_refresh value = {force_refresh}, bool = {force_refresh_bool}"
    )

    # Check for new queries with no existing data
    if not force_refresh_bool:
        from data.persistence.factory import get_backend

        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if active_profile_id and active_query_id:
            issues = backend.get_issues(active_profile_id, active_query_id, limit=1)
            if not issues:
                logger.info(
                    "[Settings] New query detected (no issues in database), "
                    "treating Update Data as Force Refresh"
                )
                force_refresh_bool = True

    return force_refresh_bool


def _perform_data_wipe():
    """Perform complete data wipe for active query."""
    from data.cache_manager import invalidate_all_cache
    from data.database import get_db_connection
    from data.persistence.factory import get_backend
    from data.profile_manager import get_active_query_workspace

    logger.info("=" * 60)
    logger.info("[Settings] FORCE REFRESH ENABLED - COMPLETE DATA WIPE FOR THIS QUERY")
    logger.info("[Settings] This is a self-repair mechanism to recover from bad data")
    logger.info("=" * 60)

    backend = get_backend()
    active_profile_id = backend.get_app_state("active_profile_id")
    active_query_id = backend.get_app_state("active_query_id")

    if not active_profile_id or not active_query_id:
        logger.warning("[Settings] No active query found - skipping data wipe")
        return

    try:
        logger.info(
            f"[Settings] Wiping ALL data for query: {active_profile_id}/{active_query_id}"
        )

        # Delete JIRA issues (CASCADE deletes changelog too)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM jira_issues WHERE profile_id = ? AND query_id = ?",
                (active_profile_id, active_query_id),
            )
            issues_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"[Settings] ✓ Deleted {issues_deleted} JIRA issues")

        # Delete project statistics
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                (active_profile_id, active_query_id),
            )
            stats_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"[Settings] ✓ Deleted {stats_deleted} project statistics")

        # Invalidate caches
        invalidate_all_cache()
        logger.info("[Settings] All global cache files invalidated")

        # Delete metrics
        try:
            deleted_count = backend.delete_metrics(active_profile_id, active_query_id)
            logger.info(f"[Settings] ✓ Deleted {deleted_count} cached metrics")
        except Exception as e:
            logger.warning(f"[Settings] Failed to delete metrics: {e}")

        # Clear snapshots cache
        try:
            from data.metrics_snapshots import clear_snapshots_cache

            clear_snapshots_cache()
            logger.info("[Settings] ✓ Cleared in-memory snapshots cache")
        except Exception as e:
            logger.warning(f"[Settings] Failed to clear snapshots cache: {e}")

        # Delete workspace cache files
        query_workspace = get_active_query_workspace()
        if query_workspace and query_workspace.exists():
            jira_cache = query_workspace / "jira_cache.json"
            if jira_cache.exists():
                jira_cache.unlink()
                logger.info("[Settings] ✓ Deleted query workspace jira_cache.json")

        logger.info("=" * 60)
        logger.info("[Settings] COMPLETE DATA WIPE SUCCESSFUL")
        logger.info(
            f"[Settings] Deleted: {issues_deleted} issues, {stats_deleted} stats from database"
        )
        logger.info("[Settings] All data will be re-fetched fresh from JIRA")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"[Settings] ❌ Data wipe error: {e}", exc_info=True)


def _jira_import_error(button_normal):
    """Return state for JIRA import error."""
    message_div = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            html.Div(
                [
                    html.Span("Integration Error", className="fw-bold d-block mb-1"),
                    html.Span(
                        "JIRA integration module not available. Please check your installation.",
                        className="small",
                    ),
                ]
            ),
        ],
        className="text-danger small",
    )

    return (
        None,
        None,
        message_div,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        False,
        button_normal,
        message_div,
        "",
        None,
        False,
        no_update,
    )


def _unexpected_error(error, button_normal):
    """Return state for unexpected error."""
    message_div = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            html.Div(
                [
                    html.Span("Unexpected Error", className="fw-bold d-block mb-1"),
                    html.Span(f"{str(error)}", className="small"),
                ]
            ),
        ],
        className="text-danger small",
    )

    return (
        None,
        None,
        message_div,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        False,
        button_normal,
        message_div,
        "",
        None,
        False,
        no_update,
    )
