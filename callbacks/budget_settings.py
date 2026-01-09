"""
Callbacks for budget configuration UI.

Handles budget settings load/save/update operations with
revision tracking and modal interactions.
"""

import logging
import math
from datetime import datetime, timezone
from dash import callback, Output, Input, State, no_update, ctx, html

from data.database import get_db_connection
from data.iso_week_bucketing import get_week_label
from ui.budget_settings_card import _create_current_budget_card_content

logger = logging.getLogger(__name__)

# Pagination settings
REVISIONS_PER_PAGE = 2


def _create_revision_history_table(
    revisions, currency_symbol, page=1, per_page=REVISIONS_PER_PAGE
):
    """
    Create paginated revision history table with navigation controls.

    Args:
        revisions: List of revision tuples from database
        currency_symbol: Currency symbol for display
        page: Current page number (1-indexed)
        per_page: Number of revisions per page

    Returns:
        Tuple of (table_element, page_info, prev_disabled, next_disabled, total_pages)
    """
    if not revisions:
        return (
            html.P(
                "No revisions yet. Budget changes will appear here.",
                className="text-muted small text-center",
                style={"padding": "1rem 0"},
            ),
            "Page 1 of 1",
            True,
            True,
            1,
        )

    total_revisions = len(revisions)
    total_pages = math.ceil(total_revisions / per_page)

    # Ensure page is within bounds
    page = max(1, min(page, total_pages))

    # Calculate slice indices
    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_revisions)

    paginated_revisions = revisions[start_idx:end_idx]

    # Create table rows
    table_rows = []
    for rev in paginated_revisions:
        (
            rev_date,
            week_label,
            time_delta,
            cost_delta,
            total_delta,
            reason,
        ) = rev

        # Format effective date as "YYYY-Wxx (YYYY-MM-DD)"
        effective_date_str = rev_date[:10]  # YYYY-MM-DD
        effective_display = f"{week_label} ({effective_date_str})"

        # Format changes compactly
        changes = []
        if time_delta != 0:
            sign = "+" if time_delta > 0 else ""
            changes.append(
                html.Span(
                    f"{sign}{time_delta}w",
                    className="badge bg-primary me-1",
                    style={"fontSize": "0.7rem"},
                )
            )
        if cost_delta != 0:
            sign = "+" if cost_delta > 0 else ""
            changes.append(
                html.Span(
                    f"{sign}{currency_symbol}{cost_delta:.0f}/wk",
                    className="badge bg-info me-1",
                    style={"fontSize": "0.7rem"},
                )
            )
        if total_delta != 0:
            sign = "+" if total_delta > 0 else ""
            badge_class = "bg-success" if total_delta > 0 else "bg-danger"
            changes.append(
                html.Span(
                    f"{sign}{currency_symbol}{total_delta:,.0f}",
                    className=f"badge {badge_class}",
                    style={"fontSize": "0.7rem"},
                )
            )

        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong(
                            effective_display,
                            style={"fontSize": "0.7rem"},
                        ),
                        style={
                            "verticalAlign": "top",
                            "width": "180px",
                            "padding": "0.4rem",
                            "whiteSpace": "nowrap",
                        },
                    ),
                    html.Td(
                        html.Small(
                            rev_date[:10],
                            className="text-muted",
                            style={"fontSize": "0.7rem"},
                        ),
                        style={
                            "verticalAlign": "top",
                            "width": "90px",
                            "padding": "0.4rem",
                        },
                    ),
                    html.Td(
                        changes
                        if changes
                        else html.Span("No changes", className="text-muted small"),
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    ),
                    html.Td(
                        html.Small(
                            reason or "—",
                            className="text-muted fst-italic",
                            style={"fontSize": "0.7rem"},
                        ),
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    )
                    if reason
                    else html.Td(
                        "—",
                        className="text-muted",
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    ),
                ],
                style={"borderBottom": "1px solid #e9ecef"},
            )
        )

    table = html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Effective",
                            style={
                                "fontSize": "0.75rem",
                                "width": "180px",
                                "padding": "0.4rem",
                            },
                        ),
                        html.Th(
                            "Modified",
                            style={
                                "fontSize": "0.75rem",
                                "width": "90px",
                                "padding": "0.4rem",
                            },
                        ),
                        html.Th(
                            "Changes",
                            style={"fontSize": "0.75rem", "padding": "0.4rem"},
                        ),
                        html.Th(
                            "Reason", style={"fontSize": "0.75rem", "padding": "0.4rem"}
                        ),
                    ],
                    style={"borderBottom": "2px solid #dee2e6"},
                )
            ),
            html.Tbody(table_rows),
        ],
        className="table table-sm table-hover",
        style={"fontSize": "0.8rem", "marginBottom": "0"},
    )

    page_info = f"Page {page} of {total_pages}"
    prev_disabled = page <= 1
    next_disabled = page >= total_pages

    return table, page_info, prev_disabled, next_disabled, total_pages


# ============================================================================
# Budget Settings Load
# ============================================================================


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
    ],
    prevent_initial_call=False,
)
def load_budget_settings(profile_id, query_id, active_tab):
    """
    Load budget settings when profile/query changes or Budget tab is opened.

    Args:
        profile_id: Active profile identifier
        query_id: Active query identifier
        active_tab: Currently active settings tab

    Returns:
        Tuple of (store_data, time_input, currency_input, cost_input,
                  effective_date, revision_history, time_current, cost_current,
                  page_info, prev_disabled, next_disabled)
    """
    logger.info(
        f"[BUDGET LOAD] Called with profile_id={profile_id}, query_id={query_id}, active_tab={active_tab}"
    )

    # Only skip if we don't have both profile_id and query_id
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
    # but skip updating the UI inputs
    if active_tab != "budget-tab":
        try:
            from data.budget_calculator import get_budget_at_week
            from data.iso_week_bucketing import get_week_label
            from datetime import datetime

            # Get current week to apply revisions up to now
            current_week = get_week_label(datetime.now())

            # Get budget with revisions applied (not just base settings)
            budget_with_revisions = get_budget_at_week(
                profile_id, query_id, current_week
            )

            if budget_with_revisions:
                # Also get created_at and updated_at from budget_settings
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT created_at, updated_at FROM budget_settings WHERE profile_id = ? AND query_id = ?",
                        (profile_id, query_id),
                    )
                    timestamps = cursor.fetchone()

                store_data = {
                    "time_allocated_weeks": budget_with_revisions[
                        "time_allocated_weeks"
                    ],
                    "budget_total_eur": budget_with_revisions["budget_total_eur"],
                    "currency_symbol": budget_with_revisions.get(
                        "currency_symbol", "€"
                    ),
                    "team_cost_per_week_eur": budget_with_revisions[
                        "team_cost_per_week_eur"
                    ],
                    "created_at": timestamps[0] if timestamps else "",
                    "updated_at": timestamps[1] if timestamps else "",
                }
                logger.info(
                    f"[BUDGET LOAD] Not on budget-tab, populating store only: time={store_data['time_allocated_weeks']}, cost={store_data['team_cost_per_week_eur']}"
                )
            else:
                # No budget for this query - clear store
                store_data = {}
                logger.warning(
                    "[BUDGET LOAD] No budget found, clearing store and returning no_update"
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

            # Query budget settings
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
                # No budget configured - return empty store
                empty_history = [
                    html.P(
                        "No budget configured yet.",
                        className="text-muted small",
                    )
                ]
                return (
                    {},
                    None,
                    "€",
                    None,
                    None,
                    empty_history,
                    "Current: Not set",
                    "Current: Not set",
                    "Page 1 of 1",
                    True,
                    True,
                )

            # Budget exists
            time_allocated = result[0]
            budget_total = result[1]
            currency_symbol = result[2] or "€"
            team_cost = result[3]
            created_at = result[4]
            updated_at = result[5]

            # Store data for later use
            store_data = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost,
                "created_at": created_at,
                "updated_at": updated_at,
            }

            # Load budget revisions for history display (paginate with helper)
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id, query_id),
            )

            revisions = cursor.fetchall()

            # Use helper to create paginated table
            table, page_info, prev_disabled, next_disabled, _ = (
                _create_revision_history_table(revisions, currency_symbol, page=1)
            )

            if revisions:
                revision_history = [table]
            else:
                revision_history = [table]  # Helper returns placeholder for empty

            return (
                store_data,
                time_allocated,
                currency_symbol,
                team_cost,
                None,  # Reset effective date picker
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
            "€",
            None,
            None,
            error_history,
            f"Error: {str(e)}",
            f"Error: {str(e)}",
            "Page 1 of 1",
            True,
            True,
        )


# ============================================================================
# Budget Total Display Update
# ============================================================================


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
    currency = currency_symbol or "€"

    if time_allocated and team_cost and time_allocated > 0 and team_cost > 0:
        total = time_allocated * team_cost
        return f"{currency}{total:,.2f}"
    else:
        return f"{currency}0.00"


# ============================================================================
# Budget Save/Update
# ============================================================================


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
    ],
    Input("save-budget-button", "n_clicks"),
    [
        State("profile-selector", "value"),
        State("query-selector", "value"),
        State("budget-time-allocated-input", "value"),
        State("budget-currency-symbol-input", "value"),
        State("budget-team-cost-input", "value"),
        State("budget-revision-reason-input", "value"),
        State("budget-settings-store", "data"),
        State("budget-effective-date-picker", "date"),
    ],
    prevent_initial_call=True,
)
def save_budget_settings(
    n_clicks,
    profile_id,
    query_id,
    time_allocated,
    currency_symbol,
    team_cost,
    revision_reason,
    current_settings,
    effective_date,
):
    """
    Save or update budget settings with revision tracking.

    Args:
        n_clicks: Button click count
        profile_id: Active profile identifier
        query_id: Active query identifier
        time_allocated: Time allocated in weeks
        currency_symbol: Currency symbol
        team_cost: Team cost per week (weekly rate)
        revision_reason: Reason for budget change
        current_settings: Current budget settings from store
        effective_date: Effective date for retroactive budget entry

    Returns:
        Tuple of (status_message, updated_store_data)
    """
    if not n_clicks or not profile_id or not query_id:
        return no_update, no_update

    from ui.toast_notifications import create_toast

    # Validate inputs - always require time and cost
    if not time_allocated or time_allocated < 1:
        error = create_toast(
            "Time allocated must be at least 1 week",
            toast_type="danger",
            header="Validation Error",
            duration=4000,
        )
        return error, no_update

    if not team_cost or team_cost <= 0:
        error = create_toast(
            "Team cost must be greater than 0",
            toast_type="danger",
            header="Validation Error",
            duration=4000,
        )
        return error, no_update

    # Calculate budget total from time × cost
    budget_total = team_cost * time_allocated

    try:
        now_iso = datetime.now(timezone.utc).isoformat()

        # Use effective_date if provided, otherwise use current date
        if effective_date:
            # Parse the date string from DatePickerSingle (format: YYYY-MM-DD)
            effective_dt = datetime.fromisoformat(effective_date)
            current_week = get_week_label(effective_dt)
            # Use effective date as ISO timestamp for created_at
            effective_dt_iso = effective_dt.replace(tzinfo=timezone.utc).isoformat()
            logger.info(
                f"Using effective date {effective_date} for budget revision (week: {current_week})"
            )
        else:
            effective_dt_iso = now_iso
            current_week = get_week_label(datetime.now())
            logger.info(
                f"Using current date for budget revision (week: {current_week})"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            if current_settings:
                # Update mode: Calculate deltas and insert revision
                old_time = current_settings.get("time_allocated_weeks", 0)
                old_cost = current_settings.get("team_cost_per_week_eur", 0)
                old_total = current_settings.get("budget_total_eur", 0)

                time_delta = time_allocated - old_time
                cost_delta = team_cost - old_cost
                total_delta = budget_total - old_total

                # Only insert revision if there are changes
                if time_delta != 0 or cost_delta != 0 or total_delta != 0:
                    cursor.execute(
                        """
                        INSERT INTO budget_revisions (
                            profile_id, query_id, revision_date, week_label,
                            time_allocated_weeks_delta, team_cost_delta, budget_total_delta,
                            revision_reason, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            profile_id,
                            query_id,
                            now_iso,
                            current_week,
                            time_delta,
                            cost_delta,
                            total_delta,
                            revision_reason,
                            now_iso,
                        ),
                    )

                # Update budget_settings
                # If effective_date provided, also update created_at to reflect new effective date
                cursor.execute(
                    """
                    UPDATE budget_settings
                    SET time_allocated_weeks = ?,
                        team_cost_per_week_eur = ?,
                        budget_total_eur = ?,
                        currency_symbol = ?,
                        created_at = ?,
                        updated_at = ?
                    WHERE profile_id = ? AND query_id = ?
                """,
                    (
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        effective_dt_iso,
                        now_iso,
                        profile_id,
                        query_id,
                    ),
                )

                success_msg = "Budget updated successfully"

            else:
                # Create new budget settings
                # Use effective_dt_iso for created_at to respect user's effective date
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO budget_settings (
                        profile_id, query_id, time_allocated_weeks, team_cost_per_week_eur,
                        budget_total_eur, currency_symbol,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        profile_id,
                        query_id,
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        effective_dt_iso,
                        now_iso,
                    ),
                )

                success_msg = "Budget configured successfully"

            conn.commit()

            # Get created_at from database to reflect any updates made
            # (important when effective date is changed during update)
            cursor.execute(
                "SELECT created_at FROM budget_settings WHERE profile_id = ? AND query_id = ?",
                (profile_id, query_id),
            )
            result = cursor.fetchone()
            created_at = result[0] if result else effective_dt_iso

            # Update store
            new_store = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost,
                "created_at": created_at,
                "updated_at": now_iso,
            }

            success = create_toast(
                success_msg,
                toast_type="success",
                header="Budget Saved",
                duration=4000,
            )
            return success, new_store

    except Exception as e:
        logger.error(f"Failed to save budget settings: {e}")
        error = create_toast(
            f"Failed to save: {str(e)}",
            toast_type="danger",
            header="Save Failed",
            duration=4000,
        )
        return error, no_update


# ============================================================================
# Refresh Current Budget Card After Save
# ============================================================================


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
    Refresh current budget card when store updates or when Budget tab becomes active.

    Args:
        store_data: Budget settings store
        active_tab: Currently active settings tab

    Returns:
        store_data: Updated budget settings store

    Returns:
        Updated card children
    """
    # Check if store is empty (budget deleted) or has no data
    if not store_data or not store_data.get("time_allocated_weeks"):
        # Show placeholder for no budget
        return _create_current_budget_card_content(
            budget_data=None, show_placeholder=True
        )

    # Get week label from created_at (budget start date)
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
        "currency_symbol": store_data.get("currency_symbol", "€"),
        "created_at": store_data.get("created_at", ""),
        "updated_at": store_data.get("updated_at", ""),
        "week_label": week_label,
    }

    return _create_current_budget_card_content(
        budget_data, live_metrics=None, show_placeholder=False
    )


# ============================================================================
# Load Budget Input Fields When Tab Becomes Active
# ============================================================================


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

    This handles the case where the app starts on a different tab,
    so inputs weren't populated by load_budget_settings.

    Args:
        active_tab: Currently active settings tab
        store_data: Budget settings from store

    Returns:
        Tuple of (time_input, currency_input, cost_input, effective_date)
    """
    logger.info(
        f"[POPULATE INPUTS] Called with active_tab={active_tab}, store_data={'present' if store_data else 'None'}"
    )

    # Only populate when switching TO budget tab
    if active_tab != "budget-tab":
        logger.info("[POPULATE INPUTS] Not on budget-tab, returning no_update")
        return no_update, no_update, no_update, no_update

    # If no budget data, clear inputs
    if not store_data or not store_data.get("time_allocated_weeks"):
        logger.warning(
            "[POPULATE INPUTS] No budget data in store, returning empty inputs"
        )
        return None, "€", None, None

    logger.info(
        f"[POPULATE INPUTS] Populating inputs: time={store_data.get('time_allocated_weeks')}, cost={store_data.get('team_cost_per_week_eur')}"
    )

    # Get effective date from created_at
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
        store_data.get("currency_symbol", "€"),
        store_data.get("team_cost_per_week_eur"),
        effective_date,
    )


# ============================================================================
# Refresh Budget Revision History After Save
# ============================================================================


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
    """
    Refresh budget revision history when store updates or when Budget tab becomes active.

    Args:
        store_data: Updated budget settings store
        profile_id: Active profile identifier
        query_id: Active query identifier
        current_page: Current pagination page
        active_tab: Currently active settings tab

    Returns:
        List of revision history UI elements
    """
    if not profile_id or not query_id or not store_data:
        return no_update

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get currency symbol from store
            currency_symbol = store_data.get("currency_symbol", "€")

            # Load ALL budget revisions (no LIMIT for pagination)
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id, query_id),
            )

            revisions = cursor.fetchall()

            # Use helper function to create paginated table
            page = current_page if current_page else 1
            table, _, _, _, _ = _create_revision_history_table(
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


# ============================================================================
# Cancel Button
# ============================================================================

# ============================================================================
# Budget Alert Toggle
# ============================================================================


@callback(
    Output("budget-alert-detail-collapse", "is_open"),
    Input("budget-alert-detail-toggle", "n_clicks"),
    State("budget-alert-detail-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_budget_alert_details(n_clicks, is_open):
    """
    Toggle budget alert detail collapse.

    Args:
        n_clicks: Button click count
        is_open: Current collapse state

    Returns:
        bool: New collapse state
    """
    if n_clicks:
        return not is_open
    return is_open


# ============================================================================
# Danger Zone Toggle & Revision History Pagination
# ============================================================================


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
    """
    Toggle danger zone collapse.

    Args:
        n_clicks: Button click count
        is_open: Current collapse state

    Returns:
        Tuple of (is_open, chevron_class)
    """
    if n_clicks:
        new_state = not is_open
        chevron_class = (
            "fas fa-chevron-up ms-auto" if new_state else "fas fa-chevron-down ms-auto"
        )
        return new_state, chevron_class
    return is_open, "fas fa-chevron-down ms-auto"


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
    """
    Handle revision history pagination button clicks.

    Args:
        prev_clicks: Previous button click count
        next_clicks: Next button click count
        current_page: Current page number (1-indexed)

    Returns:
        int: New page number
    """
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
    """
    Update revision history table when page changes.

    Args:
        page: Current page number
        store_data: Budget settings store
        profile_id: Active profile identifier
        query_id: Active query identifier

    Returns:
        Tuple of (table, page_info, prev_disabled, next_disabled)
    """
    if not profile_id or not query_id or not store_data:
        return no_update, no_update, no_update, no_update

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get currency symbol
            currency_symbol = store_data.get("currency_symbol", "€")

            # Load all revisions
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id, query_id),
            )

            revisions = cursor.fetchall()

            # Use helper to create paginated table
            table, page_info, prev_disabled, next_disabled, _ = (
                _create_revision_history_table(
                    revisions, currency_symbol, page=page or 1
                )
            )

            return [table], page_info, prev_disabled, next_disabled

    except Exception as e:
        logger.error(f"Failed to update revision history page: {e}")
        return no_update, no_update, no_update, no_update


# ============================================================================
# Budget Total Auto Preview
# ============================================================================


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
        return f"{currency or '€'}0.00"

    total = time_allocated * team_cost
    return f"{currency or '€'}{total:,.2f}"


# ============================================================================
# Delete History Modal Control
# ============================================================================


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
    """
    Toggle delete history modal.

    Args:
        delete_clicks: Delete button clicks
        cancel_clicks: Cancel button clicks
        confirm_clicks: Confirm button clicks
        is_open: Current modal state

    Returns:
        bool: New modal state
    """
    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "budget-delete-history-button":
        return True
    else:  # cancel or confirm
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
    """
    Delete all budget revision history (danger zone action).

    Args:
        n_clicks: Confirm button clicks
        profile_id: Active profile identifier
        query_id: Active query identifier

    Returns:
        Tuple of (notification, updated_store, modal_state, revision_history)
    """
    if not n_clicks or not profile_id or not query_id:
        return no_update, no_update, no_update, no_update

    from ui.toast_notifications import create_toast

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
            "Budget revision history deleted successfully. Budget baseline has been reset.",
            toast_type="success",
            header="History Deleted",
            duration=4000,
        )

        # Return empty history
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


# ============================================================================
# Delete Complete Budget Modal Control
# ============================================================================


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
    """
    Toggle delete complete budget modal.

    Args:
        delete_clicks: Delete button clicks
        cancel_clicks: Cancel button clicks
        confirm_clicks: Confirm button clicks
        is_open: Current modal state

    Returns:
        bool: New modal state
    """
    if not ctx.triggered:
        return is_open

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "budget-delete-complete-button":
        return True
    else:  # cancel or confirm
        return False


@callback(
    Output("budget-delete-complete-confirm-button", "disabled"),
    Input("budget-delete-confirmation-input", "value"),
    prevent_initial_call=True,
)
def enable_delete_complete_button(confirmation_text):
    """
    Enable confirm button only when user types "DELETE".

    Args:
        confirmation_text: Text entered by user

    Returns:
        bool: Button disabled state
    """
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
    """
    Delete complete budget configuration including all history (danger zone action).

    Args:
        n_clicks: Confirm button clicks
        profile_id: Active profile identifier
        query_id: Active query identifier

    Returns:
        Tuple of (notification, updated_store, modal_state, history, time_input, cost_input)
    """
    if not n_clicks or not profile_id or not query_id:
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    from ui.toast_notifications import create_toast

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete revisions first (foreign key constraint)
            cursor.execute(
                """
                DELETE FROM budget_revisions
                WHERE profile_id = ? AND query_id = ?
                """,
                (profile_id, query_id),
            )

            # Delete budget settings
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

        # Return empty/placeholder state
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
