import logging

from dash import Input, Output, State, callback, ctx, html, no_update

from data.database import get_db_connection
from ui.budget_revision_history import create_revision_history_table

logger = logging.getLogger(__name__)


@callback(
    Output("budget-revision-history", "children", allow_duplicate=True),
    [
        Input("budget-settings-store", "data"),
        Input("profile-selector", "value"),
        Input("query-selector", "value"),
        Input("budget-revision-history-page", "data"),
        Input("parameter-tabs", "active_tab"),
    ],
    prevent_initial_call=True,
)
def refresh_budget_revision_history(
    store_data, profile_id, query_id, current_page, active_tab
):

    if not profile_id or not query_id or not store_data:
        return no_update

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            currency_symbol = store_data.get("currency_symbol", "\u20ac")

            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason, created_at
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id, query_id),
            )

            revisions = cursor.fetchall()

            page = current_page if current_page else 1
            table, _, _, _, _ = create_revision_history_table(
                revisions, currency_symbol, page=page
            )

            return [table]

    except Exception as e:
        logger.error(f"Failed to refresh budget revision history: {e}")
        return [
            html.P(
                f"Error loading revision history: {str(e)}",
                className="text-danger small",
            )
        ]


@callback(
    Output("budget-revision-history-page", "data"),
    [
        Input("budget-revision-history-prev", "n_clicks"),
        Input("budget-revision-history-next", "n_clicks"),
    ],
    State("budget-revision-history-page", "data"),
    prevent_initial_call=True,
)
def handle_revision_pagination(prev_clicks, next_clicks, current_page):

    if not ctx.triggered:
        return current_page or 1

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    page = current_page or 1

    if button_id == "budget-revision-history-prev" and page > 1:
        return page - 1
    elif button_id == "budget-revision-history-next":
        return page + 1

    return page


@callback(
    [
        Output("budget-revision-history", "children", allow_duplicate=True),
        Output("budget-revision-history-page-info", "children", allow_duplicate=True),
        Output("budget-revision-history-prev", "disabled", allow_duplicate=True),
        Output("budget-revision-history-next", "disabled", allow_duplicate=True),
    ],
    [
        Input("budget-revision-history-page", "data"),
        Input("budget-settings-store", "data"),
    ],
    [
        State("profile-selector", "value"),
        State("query-selector", "value"),
    ],
    prevent_initial_call=True,
)
def update_revision_history_page(page, store_data, profile_id, query_id):

    if not profile_id or not query_id or not store_data:
        return no_update, no_update, no_update, no_update

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            currency_symbol = store_data.get("currency_symbol", "\u20ac")

            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason, created_at
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id, query_id),
            )

            revisions = cursor.fetchall()

            table, page_info, prev_disabled, next_disabled, _ = (
                create_revision_history_table(
                    revisions, currency_symbol, page=page or 1
                )
            )

            return [table], page_info, prev_disabled, next_disabled

    except Exception as e:
        logger.error(f"Failed to update revision history page: {e}")
        return no_update, no_update, no_update, no_update
