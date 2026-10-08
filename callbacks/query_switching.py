import logging

from dash import Input, Output, State, callback, ctx, html, no_update
from dash.exceptions import PreventUpdate

from data.persistence import load_app_settings, load_unified_project_data
from data.query_manager import (
    create_query,
    get_active_profile_id,
    get_active_query_id,
    get_query_dropdown_options,
    list_queries_for_profile,
    switch_query,
)
from ui.query_selector import get_query_dropdown_options as build_query_options
from ui.toast_notifications import create_error_toast, create_success_toast

logger = logging.getLogger(__name__)


@callback(
    [
        Output("load-query-data-btn", "disabled"),
        Output("delete-query-btn", "disabled"),
    ],
    [Input("query-selector", "value")],
)
def manage_query_button_states(selected_query):

    disabled = not selected_query or selected_query == "__create_new__"
    return disabled, disabled


@callback(
    [
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-name-input", "value", allow_duplicate=True),
        Output("jira-jql-query", "value", allow_duplicate=True),
    ],
    [
        Input("url", "pathname"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call="initial_duplicate",
)
def populate_query_dropdown(_pathname, profile_id):

    try:
        if profile_id is None or profile_id == "":
            try:
                profile_id = get_active_profile_id()
            except ValueError:
                logger.debug(
                    "[Query] App state not initialized, returning empty dropdown"
                )

                return (
                    get_query_dropdown_options(None),
                    "",
                    "",
                    "",
                    "",
                )

        if not profile_id:
            logger.debug("[Query] No profile ID available, returning empty dropdown")

            return (
                get_query_dropdown_options(None),
                "",
                "",
                "",
                "",
            )

        queries = list_queries_for_profile(profile_id)

        options = get_query_dropdown_options(profile_id)
        active_value = ""
        active_jql = ""
        active_name = ""

        if not queries:
            return options, "__create_new__", "", "", ""

        for query in queries:
            if query.get("is_active", False):
                active_value = query.get("id", "")
                active_jql = query.get("jql", "")
                active_name = query.get("name", "")
                break

        logger.info(
            f"[Query] Populated dropdown: {len(options) - 1} queries + "
            f"Create New. Active: {active_value}"
        )

        return options, active_value, active_jql, active_name, active_jql

    except Exception as e:
        logger.error(f"[Query] Failed to populate dropdown: {type(e).__name__}: {e}")
        return (
            [{"label": "→ Create New Query", "value": "__create_new__"}],
            "",
            "",
            "",
            "",
        )


@callback(
    [
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-name-input", "value", allow_duplicate=True),
        Output("jira-jql-query", "value", allow_duplicate=True),
    ],
    Input("query-selector", "value"),
    State("query-selector", "options"),
    prevent_initial_call=True,
)
def switch_query_callback(selected_query_id, current_options):

    if not selected_query_id:
        raise PreventUpdate

    if not isinstance(selected_query_id, str):
        logger.warning(f"Invalid query ID type: {type(selected_query_id)}")
        raise PreventUpdate

    if selected_query_id == "__create_new__":
        logger.info("Create New Query selected - clearing fields")
        return no_update, "__create_new__", "", "", ""

    try:
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        options = get_query_dropdown_options(profile_id)
        selected_jql = ""
        selected_name = ""

        for query in queries:
            if query.get("id", "") == selected_query_id:
                selected_jql = query.get("jql", "")
                selected_name = query.get("name", "")
                break

        if not selected_jql and not selected_name:
            logger.error(
                f"Query selection failed: {selected_query_id} not found in profile"
            )
            raise PreventUpdate

        logger.info(
            f"[Query] Selected (not switched): '{selected_name}', "
            f"JQL length: {len(selected_jql)} chars. "
            f"Data will load when user clicks 'Load Query Data' button."
        )
        return (
            options,
            selected_query_id,
            selected_jql,
            selected_name,
            selected_jql,
        )

    except ValueError as e:
        logger.error(f"[Query] Validation error: {e}")
        return no_update, no_update, no_update, no_update, no_update

    except PreventUpdate:
        raise

    except Exception as e:
        logger.error(f"[Query] Switch failed: {type(e).__name__}: {e}")
        return no_update, no_update, no_update, no_update, no_update


@callback(
    [
        Output("edit-query-modal", "is_open"),
        Output("edit-query-name-input", "value"),
        Output("edit-query-description-input", "value"),
        Output("edit-query-jql-input", "value"),
    ],
    [
        Input("edit-query-btn", "n_clicks"),
        Input("cancel-edit-query-button", "n_clicks"),
        Input("confirm-edit-query-button", "n_clicks"),
    ],
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def toggle_edit_query_modal(
    edit_clicks, cancel_clicks, confirm_clicks, selected_query_id
):

    triggered = ctx.triggered_id

    if triggered == "edit-query-btn":
        if not selected_query_id:
            raise PreventUpdate

        try:
            profile_id = get_active_profile_id()
            queries = list_queries_for_profile(profile_id)

            query = next((q for q in queries if q.get("id") == selected_query_id), None)

            if not query:
                logger.error(f"[Query] Not found for editing: {selected_query_id}")
                raise PreventUpdate

            return (
                True,
                query.get("name", ""),
                query.get("description", ""),
                query.get("jql", ""),
            )

        except Exception as e:
            logger.error(f"[Query] Load for editing failed: {type(e).__name__}: {e}")
            raise PreventUpdate from e

    elif triggered in ("cancel-edit-query-button", "confirm-edit-query-button"):
        return False, "", "", ""

    raise PreventUpdate


@callback(
    Output("workspace-create-query-modal", "is_open"),
    [
        Input("create-query-btn", "n_clicks"),
        Input("workspace-save-create-query-button", "n_clicks"),
        Input("workspace-cancel-create-query-button", "n_clicks"),
    ],
    State("workspace-create-query-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_create_query_modal(create_clicks, save_clicks, cancel_clicks, is_open):

    triggered = ctx.triggered_id

    if triggered == "create-query-btn":
        return not is_open
    elif triggered in (
        "workspace-save-create-query-button",
        "workspace-cancel-create-query-button",
    ):
        return False

    return is_open


@callback(
    [
        Output("workspace-query-name-input", "value"),
        Output("workspace-query-jql-input", "value"),
        Output("workspace-query-creation-feedback", "children"),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("workspace-save-create-query-button", "n_clicks"),
    [
        State("workspace-query-name-input", "value"),
        State("workspace-query-jql-input", "value"),
    ],
    prevent_initial_call=True,
)
def create_new_query_callback(save_clicks, query_name, query_jql):

    if not save_clicks:
        raise PreventUpdate

    try:
        if not query_name or not query_name.strip():
            feedback = create_error_toast(
                "Query name is required",
                header="Validation Error",
            )
            return no_update, no_update, "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query is required",
                header="Validation Error",
            )
            return no_update, no_update, "", no_update, no_update, feedback

        profile_id = get_active_profile_id()

        query_id = create_query(profile_id, query_name.strip(), query_jql.strip())

        logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

        queries = list_queries_for_profile(profile_id)
        options = build_query_options(queries)

        toast = create_success_toast(
            f"Query '{query_name}' created successfully!",
            header="Query Created",
        )
        return "", "", "", options, query_id, toast

    except ValueError as e:
        logger.warning(f"[Query] Validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return no_update, no_update, "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"[Query] Creation failed: {type(e).__name__}: {e}")
        feedback = create_error_toast(
            f"Error creating query: {e}",
            header="Creation Failed",
        )
        return no_update, no_update, "", no_update, no_update, feedback


@callback(
    [
        Output("delete-jql-query-modal", "is_open", allow_duplicate=True),
        Output("delete-query-name", "children", allow_duplicate=True),
    ],
    Input("delete-query-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def trigger_delete_query_modal_from_selector(delete_clicks, selected_query_id):

    logger.info(
        f"[DELETE] Delete button clicked - "
        f"delete_clicks={delete_clicks}, selected_query_id='{selected_query_id}'"
    )

    if not delete_clicks or not selected_query_id:
        logger.warning(
            f"[DELETE] Preventing update - "
            f"delete_clicks={delete_clicks}, selected_query_id='{selected_query_id}'"
        )
        raise PreventUpdate

    if selected_query_id == "__create_new__":
        logger.warning("Cannot delete 'Create New Query' placeholder")
        raise PreventUpdate

    try:
        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found")
            raise PreventUpdate

        query_name = query.get("name", "Unnamed Query")
        active_query_id = get_active_query_id()
        is_active = active_query_id and selected_query_id == active_query_id
        is_last_query = len(queries) == 1

        display_parts = [query_name]

        if is_active and is_last_query:
            display_parts.append(
                " [!] ACTIVE & LAST QUERY - All charts will be cleared!"
            )
            logger.warning(f"[Query] Delete modal: ACTIVE AND LAST query: {query_name}")
        elif is_active:
            display_parts.append(" [ACTIVE] - Charts will be cleared")
            logger.warning(f"[Query] Delete modal: ACTIVE query: {query_name}")
        elif is_last_query:
            display_parts.append(" [!] LAST QUERY - Profile will have no queries")
            logger.warning(f"[Query] Delete modal: LAST query: {query_name}")
        else:
            logger.info(f"[Query] Delete modal opened: {query_name}")

        display_text = "".join(display_parts)

        return True, display_text

    except Exception as e:
        logger.error(f"[Query] Delete modal failed: {type(e).__name__}: {e}")
        raise PreventUpdate from e


@callback(
    [
        Output("total-items-input", "value", allow_duplicate=True),
        Output("estimated-items-input", "value", allow_duplicate=True),
        Output("total-points-display", "value", allow_duplicate=True),
        Output("estimated-points-input", "value", allow_duplicate=True),
        Output("current-settings", "data", allow_duplicate=True),
        Output("update-data-status", "children", allow_duplicate=True),
        Output("current-statistics", "data", allow_duplicate=True),
        Output("jira-cache-status", "children", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
    ],
    Input("load-query-data-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def load_query_cached_data(n_clicks, selected_query_id):

    if not n_clicks or not selected_query_id:
        raise PreventUpdate

    if selected_query_id == "__create_new__":
        logger.warning("Cannot load data for 'Create New Query' placeholder")
        status_message = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                "Please select an existing query to load data.",
            ],
            className="text-warning small mt-2",
        )
        raise PreventUpdate

    try:
        switch_query(selected_query_id)
        logger.info(f"Switched to query: {selected_query_id}")

        profile_id = get_active_profile_id()

        dropdown_options = get_query_dropdown_options(profile_id)

        unified_data = load_unified_project_data()

        statistics = unified_data.get("statistics", [])
        logger.info(
            f"[QUERY SWITCH] Loaded {len(statistics)} statistics "
            f"for query {selected_query_id}"
        )
        if statistics:
            logger.info(
                "[QUERY SWITCH] First stat: "
                f"{statistics[0].get('date', 'NO DATE')} - "
                f"items: {statistics[0].get('remaining_items', 'NO ITEMS')}, "
                f"points: {statistics[0].get('remaining_total_points', 'NO POINTS')}"
            )
            logger.info(
                "[QUERY SWITCH] Last stat: "
                f"{statistics[-1].get('date', 'NO DATE')} - "
                f"items: {statistics[-1].get('remaining_items', 'NO ITEMS')}, "
                f"points: {statistics[-1].get('remaining_total_points', 'NO POINTS')}"
            )

        scope = unified_data.get("project_scope", {})
        estimated_items = scope.get("estimated_items", 0)
        estimated_points = scope.get("estimated_points", 0)

        total_items = scope.get("remaining_items", 0)
        total_points = scope.get("remaining_total_points", 0)

        total_points_display = f"{total_points:.0f}"

        settings = load_app_settings()

        if scope:
            settings["total_items"] = total_items
            settings["total_points"] = total_points
            settings["estimated_items"] = estimated_items
            settings["estimated_points"] = estimated_points
            logger.info(
                f"[QUERY SWITCH] Updated settings with scope: "
                f"items={total_items}, points={total_points}"
            )

        data_points_count = len(statistics)
        status_message = html.Div(
            [
                html.I(className="fas fa-check-circle me-2 text-success"),
                html.Span(
                    "Loaded cached data: "
                    f"{data_points_count} weekly data point"
                    f"{'s' if data_points_count != 1 else ''}",
                    className="fw-medium",
                ),
            ],
            className="text-success small mt-2",
        )

        logger.info(
            f"[Query] Loaded cached data: {selected_query_id}, "
            f"{data_points_count} points, {total_items} items"
        )

        cache_status = html.Div(
            [
                html.I(className="fas fa-database me-2 text-muted"),
                html.Span("Cached data loaded", className="small"),
            ],
            className="text-muted small mt-2",
        )

        return (
            total_items,
            estimated_items,
            total_points_display,
            estimated_points,
            settings,
            status_message,
            statistics,
            cache_status,
            dropdown_options,
        )

    except Exception as e:
        logger.error(f"[Query] Load data failed: {type(e).__name__}: {e}")
        error_message = html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
                html.Span(
                    f"Failed to load cached data: {str(e)}", className="fw-medium"
                ),
            ],
            className="text-danger small mt-2",
        )
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            error_message,
            no_update,
            no_update,
            no_update,
        )
