from __future__ import annotations

import logging
from typing import Any

from dash import Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate

from data.jira.query_profiles import (
    delete_query_profile as _delete_jira_query_profile,
)
from data.jira.query_profiles import (
    get_default_query,
    get_query_profile_by_id,
    load_query_profiles,
    set_default_query,
)
from data.jira.query_profiles import (
    save_query_profile as _save_jira_query_profile,
)
from data.persistence import load_app_settings, save_app_settings
from data.query_manager import (
    delete_query,
    get_active_profile_id,
    get_active_query_id,
    list_queries_for_profile,
    switch_query,
)

logger = logging.getLogger(__name__)


def register(app: Any) -> None:

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
        ],
        prevent_initial_call=True,
    )
    def handle_save_query_modal(
        save_clicks: int | None,
        cancel_clicks: int | None,
        confirm_clicks: int | None,
        jql_value: str,
        is_open: bool,
    ) -> tuple:

        ctx = callback_context

        if not ctx.triggered:
            raise PreventUpdate

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "save-jql-query-button" and save_clicks:
            jql_preview = jql_value or "No JQL query entered"
            return True, jql_preview

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
            State("jira-jql-query", "value"),
            State("save-query-set-default-checkbox", "value"),
        ],
        prevent_initial_call=True,
    )
    def save_query_profile(
        save_clicks: int | None,
        query_name: str,
        description: str,
        jql_value: str,
        set_as_default: list,
    ) -> tuple:

        if not save_clicks:
            raise PreventUpdate

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
            saved_profile = _save_jira_query_profile(
                name=query_name.strip(),
                jql=jql_value.strip(),
                description=description.strip() if description else "",
            )
            if set_as_default and saved_profile:
                set_default_query(saved_profile["id"])

            updated_options = _build_profile_options()

            saved_profile_id = saved_profile["id"] if saved_profile else None

            logger.info(
                f"[SAVE CALLBACK] Returning {len(updated_options)} options, "
                f"selecting profile ID: {saved_profile_id}"
            )
            logger.info(
                f"[SaveProfile] Options being returned: "
                f"{[opt['label'] for opt in updated_options]}"
            )

            return (
                updated_options,
                updated_options,
                saved_profile_id,
                saved_profile_id,
                "",
                "",
                "",
                {"display": "none"},
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
            Output("jira-query-profile-selector", "value", allow_duplicate=True),
            Output("jira-query-profile-selector-mobile", "value"),
            Output("edit-jql-query-button", "style"),
            Output("load-default-jql-query-button", "style"),
            Output("delete-jql-query-button", "style"),
            Output("delete-query-name", "children"),
        ],
        [
            Input("jira-query-profile-selector", "value"),
            Input("jira-query-profile-selector-mobile", "value"),
        ],
        prevent_initial_call="initial_duplicate",
    )
    def sync_dropdowns_and_show_buttons(
        desktop_profile_id: str, mobile_profile_id: str
    ) -> tuple:

        ctx = callback_context

        if not ctx.triggered:
            logger.info(
                "DEBUG: sync_dropdowns_and_show_buttons - initial call, "
                "using desktop dropdown value"
            )
            selected_profile_id = desktop_profile_id
            trigger_id = None
        else:
            trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if trigger_id == "jira-query-profile-selector-mobile":
                selected_profile_id = mobile_profile_id
            elif trigger_id == "jira-query-profile-selector":
                selected_profile_id = desktop_profile_id
            else:
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
            f"DEBUG: sync_dropdowns_and_show_buttons called with "
            f"profile_id: {selected_profile_id}"
        )

        if trigger_id is not None:
            _persist_profile_selection(selected_profile_id)

        hidden_style = {"display": "none"}
        visible_style = {"display": "inline-block"}

        try:
            profiles = load_query_profiles()
            default_query = get_default_query()
            logger.info(
                f"DEBUG: Loaded {len(profiles)} profiles, "
                f"has default: {default_query is not None}"
            )

            if not selected_profile_id:
                logger.info(
                    "[Settings] DEBUG: No profile selected, hiding management buttons"
                )
                return (
                    selected_profile_id,
                    selected_profile_id,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    "",
                )

            selected_profile = next(
                (p for p in profiles if p["id"] == selected_profile_id), None
            )

            logger.info(
                f"DEBUG: Selected profile: "
                f"{selected_profile['name'] if selected_profile else 'None'}"
            )

            if selected_profile:
                logger.info(
                    "DEBUG: Showing buttons for user profile: "
                    f"{selected_profile['name']}"
                )

                load_default_style = (
                    visible_style
                    if default_query and default_query.get("id") != selected_profile_id
                    else hidden_style
                )

                desktop_value = no_update if trigger_id is None else selected_profile_id
                mobile_value = no_update if trigger_id is None else selected_profile_id

                return (
                    desktop_value,
                    mobile_value,
                    visible_style,
                    load_default_style,
                    visible_style,
                    selected_profile["name"],
                )
            else:
                logger.info("[Settings] DEBUG: Profile not found, hiding buttons")

                load_default_style = visible_style if default_query else hidden_style

                desktop_value = no_update if trigger_id is None else selected_profile_id
                mobile_value = no_update if trigger_id is None else selected_profile_id

                return (
                    desktop_value,
                    mobile_value,
                    hidden_style,
                    load_default_style,
                    hidden_style,
                    "",
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
    def handle_delete_query_modal_cancel(cancel_clicks: int | None) -> bool:

        if not cancel_clicks:
            raise PreventUpdate
        return False

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
    def delete_query_profile(
        delete_clicks: int | None, current_profile_id: str, query_name: str
    ) -> tuple[list[dict], str | None]:

        if not delete_clicks or not current_profile_id:
            raise PreventUpdate

        try:
            _delete_jira_query_profile(current_profile_id)

            updated_options = _build_profile_options()

            profiles = load_query_profiles()
            default_value = profiles[0]["id"] if profiles else None

            return updated_options, default_value

        except Exception as e:
            logger.error(f"[Settings] Error deleting query profile: {e}")
            raise PreventUpdate from e

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
    def delete_query_from_selector(
        delete_clicks: int | None, current_query_id: str, query_name: str
    ) -> tuple:

        if not delete_clicks or not current_query_id:
            raise PreventUpdate

        try:
            profile_id = get_active_profile_id()
            active_query_id = get_active_query_id()

            if current_query_id == active_query_id:
                queries = list_queries_for_profile(profile_id)
                other_queries = [q for q in queries if q.get("id") != current_query_id]

                if other_queries:
                    new_active_query_id = other_queries[0].get("id")
                    if new_active_query_id:
                        switch_query(new_active_query_id)

            delete_query(profile_id, current_query_id, allow_cascade=True)

            logger.info(
                "Deleted query "
                f"'{current_query_id}' from profile '{profile_id}' via modal"
            )

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

            return options, active_value, active_jql, active_name, active_jql, False

        except Exception as e:
            logger.error(f"[Settings] Error deleting query from selector: {e}")
            raise PreventUpdate from e

    @app.callback(
        Output("jira-jql-query", "value"),
        [Input("jira-query-profile-selector", "value")],
        prevent_initial_call=True,
    )
    def update_jql_from_profile(selected_profile_id: str) -> str:

        if not selected_profile_id:
            raise PreventUpdate

        try:
            profile = get_query_profile_by_id(selected_profile_id)
            if profile:
                logger.info(f"Loading JQL query from profile: {profile['name']}")
                return profile["jql"]
            else:
                raise PreventUpdate

        except Exception as e:
            logger.error(f"[Settings] Error loading profile JQL: {e}")
            raise PreventUpdate from e

    @app.callback(
        Output("query-profile-status", "children"),
        [
            Input("jira-query-profile-selector", "value"),
            Input("jira-query-profile-selector-mobile", "value"),
        ],
        prevent_initial_call=True,
    )
    def update_query_status_message(desktop_value: str, mobile_value: str) -> str:

        selected_profile_id = desktop_value or mobile_value

        if not selected_profile_id:
            return ""

        try:
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
        edit_clicks: int | None,
        query_name: str,
        description: str,
        jql_value: str,
        current_profile_id: str,
    ) -> tuple:

        if not edit_clicks or not current_profile_id or current_profile_id == "custom":
            raise PreventUpdate

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
            updated_profile = _save_jira_query_profile(
                name=query_name.strip(),
                jql=jql_value.strip(),
                description=description.strip() if description else "",
                profile_id=current_profile_id,
            )

            if updated_profile:
                logger.info(f"Updated query profile: {updated_profile['name']}")

                updated_options = _build_profile_options()

                return (
                    updated_options,
                    updated_options,
                    jql_value.strip(),
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
            Output("jira-jql-query", "value", allow_duplicate=True),
        ],
        [Input("load-default-jql-query-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def load_default_query(load_default_clicks: int | None) -> tuple[str, str]:

        if not load_default_clicks:
            raise PreventUpdate

        try:
            default_query = get_default_query()
            if default_query:
                logger.info(f"Loading default query: {default_query['name']}")
                return default_query["id"], default_query["jql"]
            else:
                logger.warning("No default query found")
                raise PreventUpdate

        except Exception as e:
            logger.error(f"Error loading default query: {e}")
            raise PreventUpdate from e

    app.clientside_callback(
        """
        function(jql_value) {
            if (!jql_value) {
                jql_value = '';
            }
            const count = jql_value.length;
            const WARNING_THRESHOLD = 1800;
            const MAX_REFERENCE = 2000;
            const warning = count >= WARNING_THRESHOLD;
            
            const countStr = count.toLocaleString();
            const limitStr = MAX_REFERENCE.toLocaleString();
            
            const cssClasses = warning ? 
                'character-count-display character-count-warning' : 
                'character-count-display';
            
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


def _build_profile_options() -> list[dict[str, str]]:

    options = []
    profiles = load_query_profiles()
    for profile in profiles:
        label = profile["name"]
        if profile.get("is_default", False):
            label += " [Default]"
        options.append({"label": label, "value": profile["id"]})
    return options


def _persist_profile_selection(selected_profile_id: str) -> None:

    try:
        app_settings = load_app_settings()
        current_profile_id = app_settings.get("active_jql_profile_id", "")

        if selected_profile_id != current_profile_id:
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
                jql_query=jql_to_save,
                last_used_data_source=app_settings.get("last_used_data_source"),
                active_jql_profile_id=selected_profile_id or "",
            )
            logger.info(
                f"Persisted profile ID: {selected_profile_id} "
                f"with JQL: {jql_to_save[:50]}..."
            )
    except Exception as e:
        logger.error(f"[Settings] Error persisting profile selection: {e}")
