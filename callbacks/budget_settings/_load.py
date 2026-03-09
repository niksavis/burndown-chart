"""
Budget settings - load, display, and populate callbacks.

Handles loading budget settings when profile/query changes, refreshing
the current budget card, populating inputs when the Budget tab opens,
and displaying the budget total and baseline velocity.
"""

import logging
from datetime import datetime

from dash import Input, Output, callback, html, no_update

from data.budget_calculator import get_budget_at_week
from data.database import get_db_connection
from data.iso_week_bucketing import get_week_label
from data.persistence import load_unified_project_data
from ui.budget_revision_history import create_revision_history_table
from ui.budget_settings_card import _create_current_budget_card_content

logger = logging.getLogger(__name__)


@callback(
    [
        Output("budget-settings-store", "data"),
        Output("budget-time-allocated-input", "value"),
        Output("budget-currency-symbol-input", "value"),
        Output("budget-team-cost-input", "value"),
        Output("budget-effective-date-picker", "date"),
        Output("budget-revision-history", "children"),
        Output("budget-time-current-value", "children"),
        Output("budget-cost-current-value", "children"),
        Output("budget-revision-history-page-info", "children"),
        Output("budget-revision-history-prev", "disabled"),
        Output("budget-revision-history-next", "disabled"),
    ],
    [
        Input("profile-selector", "value"),
        Input("query-selector", "value"),
        Input("parameter-tabs", "active_tab"),
        Input("profile-switch-trigger", "data"),
        Input("metrics-refresh-trigger", "data"),
    ],
    prevent_initial_call=False,
)
def load_budget_settings(
    profile_id, query_id, active_tab, profile_switch, metrics_refresh
):
    """
    Load budget settings when profile/query changes or Budget tab is opened.

    Args:
        profile_id: Active profile identifier
        query_id: Active query identifier
        active_tab: Currently active settings tab
        profile_switch: Trigger for profile switch
        metrics_refresh: Trigger for metrics refresh

    Returns:
        Tuple of (store_data, time_input, currency_input, cost_input,
                  effective_date, revision_history, time_current, cost_current,
                  page_info, prev_disabled, next_disabled)
    """
    logger.info(
        "[BUDGET LOAD] Called with "
        f"profile_id={profile_id}, query_id={query_id}, "
        f"active_tab={active_tab}"
    )

    if not profile_id or not query_id:
        logger.warning(
            "[BUDGET LOAD] Missing profile_id or query_id, returning no_update"
        )
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    # If not on budget tab, only update the store (for other components to use)
    if active_tab != "budget-tab":
        try:
            current_week = get_week_label(datetime.now())
            budget_with_revisions = get_budget_at_week(
                profile_id, query_id, current_week
            )

            if budget_with_revisions:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT created_at, updated_at "
                        "FROM budget_settings WHERE profile_id = ? AND query_id = ?",
                        (profile_id, query_id),
                    )
                    timestamps = cursor.fetchone()

                store_data = {
                    "time_allocated_weeks": budget_with_revisions[
                        "time_allocated_weeks"
                    ],
                    "budget_total_eur": budget_with_revisions["budget_total_eur"],
                    "currency_symbol": budget_with_revisions.get(
                        "currency_symbol", "\u20ac"
                    ),
                    "team_cost_per_week_eur": budget_with_revisions[
                        "team_cost_per_week_eur"
                    ],
                    "created_at": timestamps[0] if timestamps else "",
                    "updated_at": timestamps[1] if timestamps else "",
                }
                logger.info(
                    "[BUDGET LOAD] Not on budget-tab, populating store only: "
                    f"time={store_data['time_allocated_weeks']}, "
                    f"cost={store_data['team_cost_per_week_eur']}"
                )
            else:
                store_data = {}
                logger.warning(
                    "[BUDGET LOAD] No budget found, "
                    "clearing store and returning no_update"
                )
                return (
                    store_data,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                )
        except Exception:
            pass
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
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
                SELECT time_allocated_weeks, budget_total_eur, currency_symbol,
                       team_cost_per_week_eur, created_at, updated_at
                FROM budget_settings
                WHERE profile_id = ? AND query_id = ?
            """,
                (profile_id, query_id),
            )

            result = cursor.fetchone()

            if not result:
                empty_history = [
                    html.P(
                        "No budget configured yet.",
                        className="text-muted small",
                    )
                ]
                return (
                    {},
                    None,
                    "\u20ac",
                    None,
                    None,
                    empty_history,
                    "Current: Not set",
                    "Current: Not set",
                    "Page 1 of 1",
                    True,
                    True,
                )

            time_allocated = result[0]
            budget_total = result[1]
            currency_symbol = result[2] or "\u20ac"
            team_cost = result[3]
            created_at = result[4]
            updated_at = result[5]

            store_data = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost,
                "created_at": created_at,
                "updated_at": updated_at,
            }

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
                create_revision_history_table(revisions, currency_symbol, page=1)
            )
            revision_history = [table]

            return (
                store_data,
                time_allocated,
                currency_symbol,
                team_cost,
                None,
                revision_history,
                f"Current: {time_allocated} weeks",
                f"Current: {currency_symbol}{team_cost:,.2f}/week",
                page_info,
                prev_disabled,
                next_disabled,
            )

    except Exception as e:
        logger.error(f"Failed to load budget settings: {e}")
        error_history = [
            html.P(
                f"Error loading revision history: {str(e)}",
                className="text-danger small",
            )
        ]
        return (
            {},
            None,
            "\u20ac",
            None,
            None,
            error_history,
            f"Error: {str(e)}",
            f"Error: {str(e)}",
            "Page 1 of 1",
            True,
            True,
        )


@callback(
    Output("budget-total-display-value", "children"),
    [
        Input("budget-time-allocated-input", "value"),
        Input("budget-team-cost-input", "value"),
        Input("budget-currency-symbol-input", "value"),
    ],
    prevent_initial_call=False,
)
def update_budget_total_display(time_allocated, team_cost, currency_symbol):
    """
    Update budget total display when time or cost inputs change.

    Args:
        time_allocated: Time allocated in weeks
        team_cost: Team cost per week
        currency_symbol: Currency symbol for display

    Returns:
        str: Formatted budget total string
    """
    currency = currency_symbol or "\u20ac"
    if time_allocated and team_cost and time_allocated > 0 and team_cost > 0:
        total = time_allocated * team_cost
        return f"{currency}{total:,.2f}"
    return f"{currency}0.00"


@callback(
    Output("budget-total-auto-preview", "children"),
    [
        Input("budget-time-allocated-input", "value"),
        Input("budget-team-cost-input", "value"),
        Input("budget-currency-symbol-input", "value"),
    ],
    prevent_initial_call=False,
)
def update_budget_total_preview(time_allocated, team_cost, currency):
    """
    Update auto-calculated budget total preview.

    Args:
        time_allocated: Time allocated in weeks
        team_cost: Team cost per week (weekly rate)
        currency: Currency symbol

    Returns:
        str: Formatted budget total preview
    """
    if not time_allocated or not team_cost:
        return f"{currency or '\u20ac'}0.00"
    total = time_allocated * team_cost
    return f"{currency or '\u20ac'}{total:,.2f}"


@callback(
    Output("budget-baseline-velocity-display", "children"),
    [
        Input("profile-selector", "value"),
        Input("query-selector", "value"),
    ],
    prevent_initial_call=False,
)
def update_baseline_velocity_display(profile_id, query_id):
    """
    Display current velocity that will be captured as baseline when budget is saved.

    Args:
        profile_id: Active profile identifier
        query_id: Active query identifier

    Returns:
        str or html.Span: Velocity display text
    """
    if not profile_id or not query_id:
        return "Will be captured from Recent Completions (Last 4 Weeks) when you save"

    try:
        import pandas as pd  # noqa: PLC0415

        unified_data = load_unified_project_data()
        statistics_list = unified_data.get("statistics", [])

        if statistics_list:
            statistics_df = pd.DataFrame(statistics_list)
            recent_window = min(4, len(statistics_df))
            recent_data = statistics_df.tail(recent_window)

            velocity_items = (
                recent_data["completed_items"].mean() if not recent_data.empty else 0.0
            )
            velocity_points = (
                recent_data["completed_points"].mean()
                if not recent_data.empty and "completed_points" in recent_data.columns
                else 0.0
            )
        else:
            velocity_items = 0.0
            velocity_points = 0.0

        if velocity_items > 0 or velocity_points > 0:
            return html.Span(
                [
                    f"{velocity_items:.2f} items/wk",
                    html.Span(" \u2022 ", className="text-muted mx-1"),
                    f"{velocity_points:.2f} points/wk",
                    html.Span(
                        " (from Recent Completions)",
                        className="text-muted",
                        style={"fontSize": "0.75rem"},
                    ),
                ]
            )
        return "No velocity data available yet - run analysis first"

    except Exception as e:
        logger.error(f"Failed to get velocity for baseline display: {e}")
        return "Unable to calculate velocity"


@callback(
    Output("budget-current-card-body", "children", allow_duplicate=True),
    [
        Input("budget-settings-store", "data"),
        Input("parameter-tabs", "active_tab"),
    ],
    prevent_initial_call="initial_duplicate",
)
def refresh_current_budget_card(store_data, active_tab):
    """
    Refresh current budget card when store updates or Budget tab becomes active.

    Args:
        store_data: Budget settings store
        active_tab: Currently active settings tab

    Returns:
        Updated card children
    """
    if not store_data or not store_data.get("time_allocated_weeks"):
        return _create_current_budget_card_content(
            budget_data=None, show_placeholder=True
        )

    week_label = ""
    if "created_at" in store_data:
        try:
            created_dt = datetime.fromisoformat(
                store_data["created_at"].replace("Z", "+00:00")
            )
            week_label = get_week_label(created_dt)
        except Exception:
            pass

    budget_data = {
        "time_allocated_weeks": store_data.get("time_allocated_weeks", 0),
        "budget_total_eur": store_data.get("budget_total_eur", 0),
        "team_cost_per_week_eur": store_data.get("team_cost_per_week_eur", 0),
        "currency_symbol": store_data.get("currency_symbol", "\u20ac"),
        "created_at": store_data.get("created_at", ""),
        "updated_at": store_data.get("updated_at", ""),
        "week_label": week_label,
    }

    return _create_current_budget_card_content(
        budget_data, live_metrics=None, show_placeholder=False
    )


@callback(
    [
        Output("budget-time-allocated-input", "value", allow_duplicate=True),
        Output("budget-currency-symbol-input", "value", allow_duplicate=True),
        Output("budget-team-cost-input", "value", allow_duplicate=True),
        Output("budget-effective-date-picker", "date", allow_duplicate=True),
    ],
    [
        Input("parameter-tabs", "active_tab"),
        Input("budget-settings-store", "data"),
    ],
    prevent_initial_call=True,
)
def populate_inputs_on_tab_switch(active_tab, store_data):
    """
    Populate budget input fields when Budget tab becomes active.

    Handles the case where the app starts on a different tab and inputs
    were not populated by load_budget_settings.

    Args:
        active_tab: Currently active settings tab
        store_data: Budget settings from store

    Returns:
        Tuple of (time_input, currency_input, cost_input, effective_date)
    """
    logger.info(
        "[POPULATE INPUTS] Called with "
        f"active_tab={active_tab}, "
        f"store_data={'present' if store_data else 'None'}"
    )

    if active_tab != "budget-tab":
        logger.info("[POPULATE INPUTS] Not on budget-tab, returning no_update")
        return no_update, no_update, no_update, no_update

    if not store_data or not store_data.get("time_allocated_weeks"):
        logger.warning(
            "[POPULATE INPUTS] No budget data in store, returning empty inputs"
        )
        return None, "\u20ac", None, None

    logger.info(
        "[POPULATE INPUTS] Populating inputs: "
        f"time={store_data.get('time_allocated_weeks')}, "
        f"cost={store_data.get('team_cost_per_week_eur')}"
    )

    effective_date = None
    if "created_at" in store_data:
        try:
            created_dt = datetime.fromisoformat(
                store_data["created_at"].replace("Z", "+00:00")
            )
            effective_date = created_dt.date().isoformat()
        except Exception:
            pass

    return (
        store_data.get("time_allocated_weeks"),
        store_data.get("currency_symbol", "\u20ac"),
        store_data.get("team_cost_per_week_eur"),
        effective_date,
    )
