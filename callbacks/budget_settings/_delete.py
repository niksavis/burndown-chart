import logging

from dash import Input, Output, State, callback, ctx, html, no_update

from data.database import get_db_connection
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("budget-alert-detail-collapse", "is_open"),
    Input("budget-alert-detail-toggle", "n_clicks"),
    State("budget-alert-detail-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_budget_alert_details(n_clicks, is_open):

    if n_clicks:
        return not is_open
    return is_open


@callback(
    [
        Output("budget-danger-zone-collapse", "is_open"),
        Output("budget-danger-zone-chevron", "className"),
    ],
    Input("budget-danger-zone-toggle", "n_clicks"),
    State("budget-danger-zone-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_danger_zone(n_clicks, is_open):

    if n_clicks:
        new_state = not is_open
        chevron_class = (
            "fas fa-chevron-up ms-auto" if new_state else "fas fa-chevron-down ms-auto"
        )
        return new_state, chevron_class
    return is_open, "fas fa-chevron-down ms-auto"


@callback(
    Output("budget-delete-history-modal", "is_open"),
    [
        Input("budget-delete-history-button", "n_clicks"),
        Input("budget-delete-history-cancel-button", "n_clicks"),
        Input("budget-delete-history-confirm-button", "n_clicks"),
    ],
    State("budget-delete-history-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_delete_history_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open):

    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "budget-delete-history-button":
        return True
    return False


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
        Output("budget-delete-history-modal", "is_open", allow_duplicate=True),
        Output("budget-revision-history", "children", allow_duplicate=True),
    ],
    Input("budget-delete-history-confirm-button", "n_clicks"),
    [
        State("profile-selector", "value"),
        State("query-selector", "value"),
    ],
    prevent_initial_call=True,
)
def confirm_delete_budget_history(n_clicks, profile_id, query_id):

    if not n_clicks or not profile_id or not query_id:
        return no_update, no_update, no_update, no_update

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                """,
                (profile_id, query_id),
            )
            conn.commit()

        success = create_toast(
            "Budget revision history deleted successfully. "
            "Budget baseline has been reset.",
            toast_type="success",
            header="History Deleted",
            duration=4000,
        )

        empty_history = [
            html.P(
                "No revisions recorded yet.",
                className="text-muted small",
            )
        ]

        return success, no_update, False, empty_history

    except Exception as e:
        logger.error(f"Failed to delete budget history: {e}")
        error = create_toast(
            f"Failed to delete budget history: {str(e)}",
            toast_type="danger",
            header="Error",
            duration=5000,
        )
        return error, no_update, False, no_update


@callback(
    Output("budget-delete-complete-modal", "is_open"),
    [
        Input("budget-delete-complete-button", "n_clicks"),
        Input("budget-delete-complete-cancel-button", "n_clicks"),
        Input("budget-delete-complete-confirm-button", "n_clicks"),
    ],
    State("budget-delete-complete-modal", "is_open"),
    prevent_initial_call=True,
)
def toggle_delete_complete_modal(delete_clicks, cancel_clicks, confirm_clicks, is_open):

    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "budget-delete-complete-button":
        return True
    return False


@callback(
    Output("budget-delete-complete-confirm-button", "disabled"),
    Input("budget-delete-confirmation-input", "value"),
    prevent_initial_call=True,
)
def enable_delete_complete_button(confirmation_text):

    return (confirmation_text or "").strip().upper() != "DELETE"


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
        Output("budget-delete-complete-modal", "is_open", allow_duplicate=True),
        Output("budget-revision-history", "children", allow_duplicate=True),
        Output("budget-time-allocated-input", "value", allow_duplicate=True),
        Output("budget-team-cost-input", "value", allow_duplicate=True),
    ],
    Input("budget-delete-complete-confirm-button", "n_clicks"),
    [
        State("profile-selector", "value"),
        State("query-selector", "value"),
    ],
    prevent_initial_call=True,
)
def confirm_delete_complete_budget(n_clicks, profile_id, query_id):

    if not n_clicks or not profile_id or not query_id:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                """,
                (profile_id, query_id),
            )

            cursor.execute(
                """
                DELETE FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
                """,
                (profile_id, query_id),
            )
            conn.commit()

        success = create_toast(
            "Budget configuration deleted completely. All data has been removed.",
            toast_type="success",
            header="Budget Deleted",
            duration=4000,
        )

        empty_history = [
            html.P(
                "No budget configured yet.",
                className="text-muted small",
            )
        ]

        return success, {}, False, empty_history, None, None

    except Exception as e:
        logger.error(f"Failed to delete budget: {e}")
        error = create_toast(
            f"Failed to delete budget: {str(e)}",
            toast_type="danger",
            header="Error",
            duration=5000,
        )
        return (
            error,
            no_update,
            False,
            no_update,
            no_update,
            no_update,
        )
