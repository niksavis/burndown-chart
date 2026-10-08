import logging

from dash import Input, Output, State, callback, callback_context, html, no_update
from dash.exceptions import PreventUpdate

from data.query_manager import (
    create_query,
    get_active_profile_id,
    get_query_dropdown_options,
    list_queries_for_profile,
    switch_query,
    update_query,
)
from data.query_name_generator import generate_query_name
from ui.toast_notifications import (
    create_error_toast,
    create_success_toast,
    create_warning_toast,
)

logger = logging.getLogger(__name__)


@callback(
    [
        Output("save-query-btn", "disabled"),
        Output("save-as-query-btn", "disabled"),
        Output("discard-query-changes-btn", "disabled"),
        Output("data-operations-alert", "is_open", allow_duplicate=True),
    ],
    [
        Input("query-name-input", "value"),
        Input("query-jql-editor", "value"),
        Input("query-selector", "value"),
    ],
    [
        State("query-selector", "options"),
    ],
    prevent_initial_call="initial_duplicate",
)
def manage_button_states(
    current_name: str,
    current_jql: str,
    selected_query_id: str,
    dropdown_options: list,
) -> tuple[bool, bool, bool, bool]:

    logger.info(
        f"[QueryManagement] CALLBACK FIRED - selected_query_id='{selected_query_id}', "
        "current_name='"
        f"{current_name}', "
        f"current_jql='{current_jql[:60] if current_jql else '(empty)'}...'"
    )

    ctx = callback_context
    triggered_by_selector = False
    if ctx.triggered:
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        triggered_by_selector = trigger_id == "query-selector"
        if triggered_by_selector:
            logger.info(
                "[QueryManagement] Query switch in progress - "
                "suppressing alert to avoid race condition"
            )

    try:
        if selected_query_id == "__create_new__":
            has_name = bool(current_name and current_name.strip())
            has_jql = bool(current_jql and current_jql.strip())
            has_any_content = has_name or has_jql

            save_disabled = not has_jql
            save_as_disabled = not has_jql
            discard_disabled = not has_any_content

            logger.info(
                "[QueryManagement] Create New mode - "
                f"Name: '{current_name}', "
                f"JQL: '{current_jql[:50] if current_jql else ''}...', "
                f"Save: {not save_disabled}, Save As: {not save_as_disabled}, "
                f"Discard: {not discard_disabled}"
            )

            logger.info(
                "[QueryManagement] RETURNING: "
                f"save_disabled={save_disabled}, "
                f"save_as_disabled={save_as_disabled}, "
                f"discard_disabled={discard_disabled}, alert={has_any_content}"
            )

            show_alert = has_any_content and not triggered_by_selector

            return save_disabled, save_as_disabled, discard_disabled, show_alert

        if not selected_query_id:
            has_name = bool(current_name and current_name.strip())
            has_jql = bool(current_jql and current_jql.strip())
            has_any_content = has_name or has_jql

            save_disabled = not has_jql
            save_as_disabled = not has_jql
            discard_disabled = not has_any_content

            logger.info(
                "[QueryManagement] First query mode (no selection) - "
                f"Name: '{current_name}', "
                f"JQL: '{current_jql[:50] if current_jql else ''}...', "
                f"Save: {not save_disabled}, Save As: {not save_as_disabled}, "
                f"Discard: {not discard_disabled}"
            )

            logger.info(
                "[QueryManagement] RETURNING: "
                f"save_disabled={save_disabled}, "
                f"save_as_disabled={save_as_disabled}, "
                f"discard_disabled={discard_disabled}, alert={has_any_content}"
            )

            show_alert = has_any_content and not triggered_by_selector

            return save_disabled, save_as_disabled, discard_disabled, show_alert

        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found in profile")
            return True, True, True, False

        original_name = query.get("name", "")
        original_jql = query.get("jql", "")

        name_changed = (current_name or "") != original_name
        jql_changed = (current_jql or "") != original_jql
        any_changes = name_changed or jql_changed

        save_disabled = not jql_changed
        save_as_disabled = not any_changes
        discard_disabled = not any_changes

        show_alert = any_changes and not triggered_by_selector

        logger.debug(
            f"Button states - Save: {not save_disabled}, "
            f"Save As: {not save_as_disabled}, "
            f"Discard: {not discard_disabled}, Alert: {show_alert} "
            f"(triggered_by_selector: {triggered_by_selector})"
        )

        return save_disabled, save_as_disabled, discard_disabled, show_alert

    except Exception as e:
        logger.error(f"Failed to manage button states: {e}")
        return True, True, True, False


@callback(
    Output("query-name-input", "value", allow_duplicate=True),
    Input("query-jql-editor", "value"),
    [State("query-selector", "value"), State("query-name-input", "value")],
    prevent_initial_call=True,
)
def auto_generate_query_name(
    jql_query: str, selected_query_id: str, current_name: str
) -> str:

    if selected_query_id and selected_query_id != "__create_new__":
        raise PreventUpdate

    if current_name and current_name.strip():
        raise PreventUpdate

    if not jql_query or not jql_query.strip():
        raise PreventUpdate

    try:
        generated_name = generate_query_name(jql_query)
        logger.info(f"[QueryManagement] Auto-generated query name: {generated_name}")
        return generated_name

    except Exception as e:
        logger.error(f"[QueryManagement] Failed to auto-generate query name: {e}")
        raise PreventUpdate from e


@callback(
    [
        Output("query-save-status", "children", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("save-query-btn", "n_clicks"),
    [
        State("query-name-input", "value"),
        State("query-jql-editor", "value"),
        State("query-selector", "value"),
    ],
    prevent_initial_call=True,
)
def save_query_overwrite(
    n_clicks: int,
    query_name: str,
    query_jql: str,
    selected_query_id: str,
) -> tuple:

    if not n_clicks:
        raise PreventUpdate

    try:
        if not selected_query_id:
            if not query_jql or not query_jql.strip():
                feedback = create_error_toast(
                    "JQL query cannot be empty",
                    header="Validation Error",
                )
                return "", no_update, no_update, feedback

            if not query_name or not query_name.strip():
                query_name = generate_query_name(query_jql.strip())
                logger.info(
                    "[QueryManagement] Auto-generated name for first query: "
                    f"'{query_name}'"
                )

            profile_id = get_active_profile_id()
            new_query_id = create_query(profile_id, query_name, query_jql.strip())
            switch_query(new_query_id)

            logger.info(
                f"[QueryManagement] Created first query '{new_query_id}' "
                f"in profile '{profile_id}'"
            )

            options = get_query_dropdown_options(profile_id)

            toast = create_success_toast(
                f"Query '{query_name}' created successfully!",
                header="Query Created",
            )

            return "", options, new_query_id, toast

        if selected_query_id == "__create_new__":
            if not query_jql or not query_jql.strip():
                feedback = create_error_toast(
                    "JQL query cannot be empty",
                    header="Validation Error",
                )
                return "", no_update, no_update, feedback

            if not query_name or not query_name.strip():
                query_name = generate_query_name(query_jql.strip())
                logger.info(
                    "[QueryManagement] Auto-generated name for new query: "
                    f"'{query_name}'"
                )

            profile_id = get_active_profile_id()

            queries = list_queries_for_profile(profile_id)
            for query in queries:
                if query.get("name", "").strip() == query_name.strip():
                    feedback = create_warning_toast(
                        "Query name "
                        f"'{query_name}' already exists. "
                        "Please choose a different name.",
                        header="Name Collision",
                    )
                    return "", no_update, no_update, feedback

            new_query_id = create_query(profile_id, query_name, query_jql.strip())
            switch_query(new_query_id)

            logger.info(
                f"[QueryManagement] Created new query '{new_query_id}' "
                f"in profile '{profile_id}'"
            )

            options = get_query_dropdown_options(profile_id)

            toast = create_success_toast(
                f"Query '{query_name}' created successfully!",
                header="Query Created",
            )

            return "", options, new_query_id, toast

        if not query_name or not query_name.strip():
            feedback = create_error_toast(
                "Query name cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        profile_id = get_active_profile_id()

        queries = list_queries_for_profile(profile_id)
        for query in queries:
            if (
                query.get("id") != selected_query_id
                and query.get("name", "").strip() == query_name.strip()
            ):
                feedback = create_warning_toast(
                    "Query name "
                    f"'{query_name}' already exists. "
                    "Please choose a different name.",
                    header="Name Collision",
                )
                return "", no_update, no_update, feedback

        update_query(
            profile_id, selected_query_id, query_name.strip(), query_jql.strip()
        )

        logger.info(f"Query '{selected_query_id}' updated successfully")

        options = get_query_dropdown_options(profile_id)

        toast = create_success_toast(
            f"Query '{query_name}' saved successfully!",
            header="Query Saved",
        )

        return "", options, selected_query_id, toast

    except ValueError as e:
        logger.warning(f"Query save validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"Failed to save query: {e}")
        feedback = create_error_toast(f"Error saving query: {e}", header="Save Failed")
        return "", no_update, no_update, feedback


@callback(
    [
        Output("query-save-status", "children", allow_duplicate=True),
        Output("query-selector", "options", allow_duplicate=True),
        Output("query-selector", "value", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("save-as-query-btn", "n_clicks"),
    [
        State("query-name-input", "value"),
        State("query-jql-editor", "value"),
    ],
    prevent_initial_call=True,
)
def save_query_as_new(
    n_clicks: int,
    query_name: str,
    query_jql: str,
) -> tuple:

    if not n_clicks:
        raise PreventUpdate

    try:
        if not query_name or not query_name.strip():
            feedback = create_error_toast(
                "Query name cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        if not query_jql or not query_jql.strip():
            feedback = create_error_toast(
                "JQL query cannot be empty",
                header="Validation Error",
            )
            return "", no_update, no_update, feedback

        profile_id = get_active_profile_id()

        queries = list_queries_for_profile(profile_id)
        for query in queries:
            if query.get("name", "").strip() == query_name.strip():
                feedback = create_warning_toast(
                    "Query name "
                    f"'{query_name}' already exists. "
                    "Please choose a different name.",
                    header="Name Collision",
                )
                return "", no_update, no_update, feedback

        query_id = create_query(profile_id, query_name.strip(), query_jql.strip())

        logger.info(f"New query '{query_id}' created successfully")

        options = get_query_dropdown_options(profile_id)

        toast = create_success_toast(
            f"New query '{query_name}' created successfully!",
            header="Query Created",
        )

        return "", options, query_id, toast

    except ValueError as e:
        logger.warning(f"Query creation validation failed: {e}")
        feedback = create_error_toast(str(e), header="Validation Error")
        return "", no_update, no_update, feedback

    except Exception as e:
        logger.error(f"Failed to create query: {e}")
        feedback = create_error_toast(
            f"Error creating query: {e}",
            header="Creation Failed",
        )
        return "", no_update, no_update, feedback


@callback(
    [
        Output("query-name-input", "value", allow_duplicate=True),
        Output("query-jql-editor", "value", allow_duplicate=True),
        Output("query-save-status", "children", allow_duplicate=True),
    ],
    Input("discard-query-changes-btn", "n_clicks"),
    State("query-selector", "value"),
    prevent_initial_call=True,
)
def discard_query_changes(n_clicks: int, selected_query_id: str) -> tuple:

    if not n_clicks:
        raise PreventUpdate

    try:
        if selected_query_id == "__create_new__":
            feedback = html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "Fields cleared",
                ],
                className="alert alert-info",
            )
            return "", "", feedback

        profile_id = get_active_profile_id()
        queries = list_queries_for_profile(profile_id)

        query = next((q for q in queries if q.get("id") == selected_query_id), None)
        if not query:
            logger.warning(f"Query {selected_query_id} not found")
            raise PreventUpdate

        original_name = query.get("name", "")
        original_jql = query.get("jql", "")

        feedback = html.Div(
            [
                html.I(className="fas fa-undo me-2"),
                "Changes discarded",
            ],
            className="alert alert-info",
        )

        logger.info(f"Discarded changes for query '{selected_query_id}'")
        return original_name, original_jql, feedback

    except Exception as e:
        logger.error(f"Failed to discard changes: {e}")
        raise PreventUpdate from e
