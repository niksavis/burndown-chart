import logging
from datetime import datetime
from typing import Any

from dash import Input, Output, State, callback, ctx, no_update
from dash.exceptions import PreventUpdate

from data.query_manager import (
    create_query,
    delete_query,
    get_active_profile_id,
    list_queries_for_profile,
    update_query,
)
from data.query_name_generator import generate_query_name, validate_query_name

logger = logging.getLogger(__name__)


@callback(
    [
        Output("query-state-store", "data"),
        Output("query-unsaved-badge", "style"),
        Output("integrated-save-query-button", "disabled"),
        Output("integrated-revert-query-button", "style"),
        Output("query-name-suggestion", "children"),
        Output("query-name-suggestion-container", "style"),
    ],
    Input("integrated-jql-editor", "value"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def detect_jql_changes(
    current_jql: str,
    state: dict[str, Any],
) -> tuple:

    if state is None:
        state = {
            "activeQueryId": None,
            "activeQueryName": None,
            "savedJql": "",
            "currentJql": "",
            "hasUnsavedChanges": False,
            "lastModified": None,
            "suggestedName": "",
        }

    saved_jql = state.get("savedJql", "")
    current_jql = current_jql or ""

    has_unsaved_changes = current_jql.strip() != saved_jql.strip()

    suggested_name = ""
    if current_jql.strip():
        suggested_name = generate_query_name(current_jql)

    state["currentJql"] = current_jql
    state["hasUnsavedChanges"] = has_unsaved_changes
    state["suggestedName"] = suggested_name
    state["lastModified"] = datetime.now().isoformat()

    badge_style = (
        {"display": "inline-block"} if has_unsaved_changes else {"display": "none"}
    )
    save_disabled = not bool(current_jql.strip())
    revert_style = {"display": "block"} if has_unsaved_changes else {"display": "none"}
    suggestion_style = {"display": "block"} if suggested_name else {"display": "none"}

    return (
        state,
        badge_style,
        save_disabled,
        revert_style,
        suggested_name,
        suggestion_style,
    )


@callback(
    [
        Output("unsaved-changes-modal", "is_open"),
        Output("unsaved-changes-query-name", "children"),
        Output("unsaved-changes-jql-preview", "children"),
        Output("pending-query-switch-store", "data"),
    ],
    Input("integrated-query-selector", "value"),
    [
        State("query-state-store", "data"),
        State("unsaved-changes-modal", "is_open"),
    ],
    prevent_initial_call=True,
)
def handle_query_dropdown_change(
    selected_query_id: str | None,
    state: dict[str, Any],
    modal_is_open: bool,
) -> tuple:

    if not selected_query_id or not state:
        raise PreventUpdate

    if selected_query_id == state.get("activeQueryId"):
        raise PreventUpdate

    has_unsaved = state.get("hasUnsavedChanges", False)

    if has_unsaved:
        query_name = state.get("activeQueryName", "current query")
        current_jql = state.get("currentJql", "")

        return (
            True,
            query_name,
            current_jql,
            selected_query_id,
        )

    return no_update, no_update, no_update, selected_query_id


@callback(
    [
        Output("integrated-jql-editor", "value"),
        Output("query-state-store", "data", allow_duplicate=True),
        Output("integrated-delete-query-button", "disabled"),
        Output("query-last-saved-time", "children"),
        Output("query-last-saved-indicator", "style"),
    ],
    Input("pending-query-switch-store", "data"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def load_query_jql(
    query_id: str | None,
    state: dict[str, Any],
) -> tuple:

    if not query_id:
        raise PreventUpdate

    try:
        profile_id = get_active_profile_id()
        all_queries = list_queries_for_profile(profile_id)
        query = next((q for q in all_queries if q.get("id") == query_id), None)
        if not query:
            logger.warning(f"Query {query_id} not found")
            raise PreventUpdate

        query_name = query.get("name", "Unnamed")
        query_jql = query.get("jql", "")

        if state is None:
            state = {}

        state["activeQueryId"] = query_id
        state["activeQueryName"] = query_name
        state["savedJql"] = query_jql
        state["currentJql"] = query_jql
        state["hasUnsavedChanges"] = False
        state["lastModified"] = datetime.now().isoformat()

        last_saved_text = "Just now"

        return (
            query_jql,
            state,
            False,
            last_saved_text,
            {"display": "block"},
        )

    except Exception as e:
        logger.error(f"Error loading query {query_id}: {e}")
        raise PreventUpdate from e


@callback(
    [
        Output("unsaved-changes-modal", "is_open", allow_duplicate=True),
        Output("save-query-modal", "is_open"),
        Output("pending-query-switch-store", "data", allow_duplicate=True),
    ],
    [
        Input("unsaved-changes-save-button", "n_clicks"),
        Input("unsaved-changes-discard-button", "n_clicks"),
        Input("unsaved-changes-cancel-button", "n_clicks"),
    ],
    State("pending-query-switch-store", "data"),
    prevent_initial_call=True,
)
def handle_unsaved_changes_modal(
    save_clicks: int,
    discard_clicks: int,
    cancel_clicks: int,
    pending_query_id: str | None,
) -> tuple:

    triggered = ctx.triggered_id

    if triggered == "unsaved-changes-save-button":
        return False, True, pending_query_id

    elif triggered == "unsaved-changes-discard-button":
        return False, False, pending_query_id

    elif triggered == "unsaved-changes-cancel-button":
        return False, False, None

    raise PreventUpdate


@callback(
    [
        Output("save-query-modal", "is_open", allow_duplicate=True),
        Output("save-query-jql-preview", "children"),
        Output("save-query-name-input", "value"),
        Output("save-query-mode-radio", "value"),
        Output("save-query-mode-container", "style"),
    ],
    Input("integrated-save-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def open_save_query_modal(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:

    if not n_clicks or not state:
        raise PreventUpdate

    current_jql = state.get("currentJql", "")
    suggested_name = state.get("suggestedName", "")
    active_query_id = state.get("activeQueryId")

    if active_query_id:
        mode = "update"
    else:
        mode = "new"

    mode_container_style = (
        {"display": "block"} if active_query_id else {"display": "none"}
    )

    return (
        True,
        current_jql,
        suggested_name,
        mode,
        mode_container_style,
    )


@callback(
    [
        Output("save-query-modal", "is_open", allow_duplicate=True),
        Output("save-query-name-validation", "children"),
        Output("query-state-store", "data", allow_duplicate=True),
        Output("integrated-query-selector", "options"),
        Output("integrated-query-selector", "value"),
    ],
    Input("save-query-confirm-button", "n_clicks"),
    [
        State("save-query-name-input", "value"),
        State("save-query-mode-radio", "value"),
        State("query-state-store", "data"),
    ],
    prevent_initial_call=True,
)
def save_query_confirm(
    n_clicks: int,
    query_name: str,
    save_mode: str,
    state: dict[str, Any],
) -> tuple:

    if not n_clicks or not state:
        raise PreventUpdate

    try:
        profile_id = get_active_profile_id()
        all_queries = list_queries_for_profile(profile_id)
        existing_names = [q.get("name", "") for q in all_queries]

        if save_mode == "update" and state.get("activeQueryName"):
            existing_names = [
                n for n in existing_names if n != state.get("activeQueryName")
            ]

        is_valid, error_msg = validate_query_name(query_name, existing_names)
        if not is_valid:
            return no_update, error_msg, no_update, no_update, no_update

        current_jql = state.get("currentJql", "")

        if save_mode == "update":
            query_id = state.get("activeQueryId")
            if not query_id:
                return (
                    no_update,
                    "No active query to update",
                    no_update,
                    no_update,
                    no_update,
                )
            update_query(profile_id, query_id, name=query_name, jql=current_jql)
            logger.info(f"Updated query {query_id}: {query_name}")

            state["activeQueryName"] = query_name
            state["savedJql"] = current_jql
            state["hasUnsavedChanges"] = False

            selected_query_id = query_id

        else:
            query_id = create_query(profile_id, query_name, current_jql)
            logger.info(f"Created query {query_id}: {query_name}")

            state["activeQueryId"] = query_id
            state["activeQueryName"] = query_name
            state["savedJql"] = current_jql
            state["hasUnsavedChanges"] = False

            selected_query_id = query_id

        all_queries = list_queries_for_profile(profile_id)
        dropdown_options = [
            {
                "label": (
                    f"{q.get('name', 'Unnamed')} "
                    f"{'[Active]' if q.get('id') == selected_query_id else ''}"
                ),
                "value": q.get("id", ""),
            }
            for q in all_queries
        ]

        return (
            False,
            "",
            state,
            dropdown_options,
            selected_query_id,
        )

    except Exception as e:
        logger.error(f"Error saving query: {e}")
        return (
            no_update,
            f"Error saving query: {str(e)}",
            no_update,
            no_update,
            no_update,
        )


@callback(
    Output("save-query-modal", "is_open", allow_duplicate=True),
    Input("save-query-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_save_query_modal(n_clicks: int) -> bool:
    if not n_clicks:
        raise PreventUpdate
    return False


@callback(
    [
        Output("integrated-jql-editor", "value", allow_duplicate=True),
        Output("query-state-store", "data", allow_duplicate=True),
    ],
    Input("integrated-revert-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def revert_query_changes(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:

    if not n_clicks or not state:
        raise PreventUpdate

    saved_jql = state.get("savedJql", "")

    state["currentJql"] = saved_jql
    state["hasUnsavedChanges"] = False

    return saved_jql, state


@callback(
    [
        Output("delete-query-modal", "is_open"),
        Output("delete-query-name-display", "children"),
        Output("delete-query-jql-display", "children"),
    ],
    Input("integrated-delete-query-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def open_delete_query_modal(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:

    if not n_clicks or not state:
        raise PreventUpdate

    query_name = state.get("activeQueryName", "Unnamed")
    current_jql = state.get("currentJql", "")

    return True, query_name, current_jql


@callback(
    [
        Output("delete-query-modal", "is_open", allow_duplicate=True),
        Output("integrated-query-selector", "options", allow_duplicate=True),
        Output("integrated-query-selector", "value", allow_duplicate=True),
        Output("integrated-jql-editor", "value", allow_duplicate=True),
        Output("query-state-store", "data", allow_duplicate=True),
    ],
    Input("delete-query-confirm-button", "n_clicks"),
    State("query-state-store", "data"),
    prevent_initial_call=True,
)
def confirm_delete_query(
    n_clicks: int,
    state: dict[str, Any],
) -> tuple:

    if not n_clicks or not state:
        raise PreventUpdate

    try:
        query_id = state.get("activeQueryId")
        profile_id = get_active_profile_id()

        if not query_id:
            raise PreventUpdate
        delete_query(profile_id, query_id, allow_cascade=True)
        logger.info(f"Deleted query {query_id}")

        remaining_queries = list_queries_for_profile(profile_id)
        first_query = remaining_queries[0] if remaining_queries else None

        if first_query:
            first_query_id = first_query.get("id")
            first_query_jql = first_query.get("jql", "")
            first_query_name = first_query.get("name", "")

            state["activeQueryId"] = first_query_id
            state["activeQueryName"] = first_query_name
            state["savedJql"] = first_query_jql
            state["currentJql"] = first_query_jql
            state["hasUnsavedChanges"] = False

            dropdown_options = [
                {
                    "label": (
                        f"{q.get('name', 'Unnamed')} "
                        f"{'[Active]' if q.get('id') == first_query_id else ''}"
                    ),
                    "value": q.get("id", ""),
                }
                for q in remaining_queries
            ]

            return (
                False,
                dropdown_options,
                first_query_id,
                first_query_jql,
                state,
            )
        else:
            return (
                False,
                [],
                None,
                "",
                {
                    "activeQueryId": None,
                    "activeQueryName": None,
                    "savedJql": "",
                    "currentJql": "",
                    "hasUnsavedChanges": False,
                    "lastModified": None,
                    "suggestedName": "",
                },
            )

    except Exception as e:
        logger.error(f"Error deleting query: {e}")
        raise PreventUpdate from e


@callback(
    Output("delete-query-modal", "is_open", allow_duplicate=True),
    Input("delete-query-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_delete_query_modal(n_clicks: int) -> bool:
    if not n_clicks:
        raise PreventUpdate
    return False


@callback(
    [
        Output("integrated-query-selector", "options", allow_duplicate=True),
        Output("integrated-query-selector", "value", allow_duplicate=True),
    ],
    Input("query-state-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def initialize_query_dropdown(state: dict[str, Any]) -> tuple:

    try:
        profile_id = get_active_profile_id()
        if not profile_id:
            return [], None

        all_queries = list_queries_for_profile(profile_id)
        if not all_queries:
            return [], None

        active_query_id = state.get("activeQueryId") if state else None
        if not active_query_id and all_queries:
            active_query_id = all_queries[0].get("id")

        dropdown_options = [
            {
                "label": (
                    f"{q.get('name', 'Unnamed')} "
                    f"{'[Active]' if q.get('id') == active_query_id else ''}"
                ),
                "value": q.get("id", ""),
            }
            for q in all_queries
        ]

        return dropdown_options, active_query_id

    except Exception as e:
        logger.error(f"Error initializing query dropdown: {e}")
        return [], None
