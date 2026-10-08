import threading

from dash import ClientsideFunction, Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate

from configuration import logger
from data.cache_manager import invalidate_all_cache
from data.database import get_db_connection
from data.jira import (
    build_sync_jira_config,
    sync_jira_scope_and_data,
    validate_jira_config,
)
from data.metrics_snapshots import clear_snapshots_cache
from data.persistence import load_app_settings, load_jira_configuration
from data.persistence.factory import get_backend
from data.profile_manager import get_active_query_workspace
from data.query_manager import (
    resolve_jql_query,
    switch_query,
)
from data.task_progress import TaskProgress


def register(app):

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

        triggered_id = ctx.triggered_id if ctx.triggered else None
        triggered_prop = ctx.triggered[0] if ctx.triggered else None

        logger.info("[UPDATE DATA] =========================================")
        logger.info(
            f"[UPDATE DATA] Callback triggered by: {triggered_id} - "
            f"n_clicks={n_clicks}, force_refresh={force_refresh}"
        )
        logger.info(f"[UPDATE DATA] Full trigger info: {triggered_prop}")
        logger.info("[UPDATE DATA] =========================================")

        button_normal = [
            html.I(className="fas fa-sync-alt", style={"marginRight": "0.5rem"}),
            html.Span("Update Data"),
        ]

        if triggered_id == "force-refresh-store" and not n_clicks:
            raise PreventUpdate

        if not n_clicks:
            return _initial_state(button_normal)

        try:
            is_running, existing_task = TaskProgress.is_task_running()
            if is_running:
                logger.warning(
                    f"Update Data clicked but task already running: {existing_task}"
                )
                return _task_already_running(existing_task, button_normal)

            if not TaskProgress.start_task("update_data", "Updating data from JIRA"):
                logger.error("Failed to start Update Data task")
                return _task_start_failed(button_normal)

            result = _prepare_jira_sync(
                jql_query, selected_query_id, force_refresh, button_normal
            )

            if result is not None:
                return result

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
    return (
        None,
        None,
        "",
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        False,
        button_normal,
        "",
        "",
        None,
        True,
        no_update,
    )


def _task_already_running(existing_task, button_normal):
    message_div = html.Div(
        [
            html.I(className="fas fa-info-circle me-2"),
            f"Operation already in progress: {existing_task}",
        ],
        className="text-warning small",
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


def _task_start_failed(button_normal):
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

    logger.info(
        "[Settings] Received jql_query from Store: "
        f"'{jql_query}' (type: {type(jql_query)})"
    )

    jira_config = load_jira_configuration()

    if selected_query_id and selected_query_id != "__create_new__":
        try:
            switch_query(selected_query_id)
            logger.info(
                f"[Settings] Switched to query '{selected_query_id}' before Update Data"
            )
        except Exception as e:
            logger.error(f"[Settings] Failed to switch query before Update Data: {e}")

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
                            "Please click the 'Configure JIRA' button above "
                            "to set up your JIRA connection before fetching "
                            "data.",
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

    app_settings = load_app_settings()
    settings_jql = resolve_jql_query(jql_query, app_settings)

    logger.info(f"[Settings] JQL Query - Input: '{jql_query}', Final: '{settings_jql}'")

    jira_config_for_sync = build_sync_jira_config(
        jira_config, settings_jql, app_settings
    )

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

    return None


def _start_background_sync(jql_query, selected_query_id, force_refresh, button_normal):
    app_settings = load_app_settings()
    jira_config = load_jira_configuration()
    settings_jql = resolve_jql_query(jql_query, app_settings)
    jira_config_for_sync = build_sync_jira_config(
        jira_config, settings_jql, app_settings
    )

    force_refresh_bool = _should_force_refresh(force_refresh)

    if force_refresh_bool:
        _perform_data_wipe()

    if force_refresh_bool:
        logger.info("[Settings] Force refresh: Changelog will be re-fetched from JIRA")
    else:
        logger.info(
            "[Settings] Normal refresh: Keeping changelog cache "
            "for reuse (saves 1-2 minutes)"
        )

    def background_sync():
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
                "[BACKGROUND SYNC] sync_jira_scope_and_data returned: "
                f"success={success}, message={message}"
            )

            if not success:
                logger.error(f"[BACKGROUND SYNC] Fetch failed: {message}")
                TaskProgress.fail_task("update_data", message)
            else:
                if scope_data.get("skip_metrics"):
                    logger.info(
                        "[BACKGROUND SYNC] No changes detected, "
                        "skipping metrics calculation"
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
        f"[Settings] Background thread started: {thread.name} "
        f"(alive={thread.is_alive()})"
    )

    return (
        None,
        None,
        html.Div(
            [
                html.I(className="fas fa-spinner fa-spin me-2"),
                "Fetching data from JIRA...",
            ],
            className="text-info small",
        ),
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        False,
        True,
        button_normal,
        html.Div(
            [html.I(className="fas fa-spinner fa-spin me-2"), "Starting..."],
            className="text-info small",
        ),
        "",
        None,
        False,
        [] if force_refresh_bool else no_update,
    )


def _should_force_refresh(force_refresh):
    force_refresh_bool = bool(force_refresh)

    logger.info(
        f"[Settings] force_refresh value = {force_refresh}, bool = {force_refresh_bool}"
    )

    if not force_refresh_bool:
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
            "[Settings] Wiping ALL data for query: "
            f"{active_profile_id}/{active_query_id}"
        )

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM jira_issues WHERE profile_id = ? AND query_id = ?",
                (active_profile_id, active_query_id),
            )
            issues_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"[Settings] ✓ Deleted {issues_deleted} JIRA issues")

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM project_statistics WHERE profile_id = ? AND query_id = ?",
                (active_profile_id, active_query_id),
            )
            stats_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"[Settings] ✓ Deleted {stats_deleted} project statistics")

        invalidate_all_cache()
        logger.info("[Settings] All global cache files invalidated")

        try:
            deleted_count = backend.delete_metrics(active_profile_id, active_query_id)
            logger.info(f"[Settings] ✓ Deleted {deleted_count} cached metrics")
        except Exception as e:
            logger.warning(f"[Settings] Failed to delete metrics: {e}")

        try:
            clear_snapshots_cache()
            logger.info("[Settings] ✓ Cleared in-memory snapshots cache")
        except Exception as e:
            logger.warning(f"[Settings] Failed to clear snapshots cache: {e}")

        query_workspace = get_active_query_workspace()
        if query_workspace and query_workspace.exists():
            jira_cache = query_workspace / "jira_cache.json"
            if jira_cache.exists():
                jira_cache.unlink()
                logger.info("[Settings] ✓ Deleted query workspace jira_cache.json")

        logger.info("=" * 60)
        logger.info("[Settings] COMPLETE DATA WIPE SUCCESSFUL")
        logger.info(
            f"[Settings] Deleted: {issues_deleted} issues, "
            f"{stats_deleted} stats from database"
        )
        logger.info("[Settings] All data will be re-fetched fresh from JIRA")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"[Settings] ❌ Data wipe error: {e}", exc_info=True)


def _jira_import_error(button_normal):
    message_div = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            html.Div(
                [
                    html.Span("Integration Error", className="fw-bold d-block mb-1"),
                    html.Span(
                        "JIRA integration module not available. "
                        "Please check your installation.",
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
