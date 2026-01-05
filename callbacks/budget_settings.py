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
                            week_label,
                            style={"fontSize": "0.7rem"},
                        ),
                        style={
                            "verticalAlign": "top",
                            "width": "95px",
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
                            "Week",
                            style={
                                "fontSize": "0.75rem",
                                "width": "95px",
                                "padding": "0.4rem",
                            },
                        ),
                        html.Th(
                            "Date",
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
        Output("budget-total-manual-input", "value"),
        Output("budget-currency-symbol-input", "value"),
        Output("budget-team-cost-input", "value"),
        Output("budget-effective-date-picker", "date"),
        Output("budget-revision-history", "children"),
        Output("budget-total-mode", "value"),
        Output("budget-time-current-value", "children"),
        Output("budget-cost-current-value", "children"),
        Output("budget-revision-history-page-info", "children"),
        Output("budget-revision-history-prev", "disabled"),
        Output("budget-revision-history-next", "disabled"),
    ],
    [
        Input("profile-selector", "value"),
        Input("settings-tabs", "active_tab"),
    ],
    prevent_initial_call=False,
)
def load_budget_settings(profile_id, active_tab):
    """
    Load budget settings when profile changes or Budget tab is opened.

    Args:
        profile_id: Active profile identifier
        active_tab: Currently active settings tab

    Returns:
        Tuple of (store_data, status_indicator, time_input, total_input,
                  currency_input, cost_input, rate_type)
    """
    # Only skip if we don't have a profile_id
    if not profile_id:
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
            no_update,
            no_update,
        )

    # If not on budget tab, only update the store (for other components to use)
    # but skip updating the UI inputs
    if active_tab != "budget-tab":
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT time_allocated_weeks, team_cost_per_week_eur,
                           budget_total_eur, currency_symbol, created_at, updated_at
                    FROM budget_settings
                    WHERE profile_id = ?
                """,
                    (profile_id,),
                )
                result = cursor.fetchone()
                if result:
                    store_data = {
                        "time_allocated_weeks": result[0],
                        "budget_total_eur": result[2],
                        "currency_symbol": result[3] or "€",
                        "team_cost_per_week_eur": result[1],
                        "created_at": result[4],
                        "updated_at": result[5],
                    }
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
                WHERE profile_id = ?
            """,
                (profile_id,),
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
                    None,
                    "€",
                    None,
                    None,
                    empty_history,
                    "auto",  # Default to auto mode
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

            # Determine budget total mode
            # If budget_total equals time * team_cost, it's auto mode, otherwise manual
            auto_calculated = time_allocated * team_cost
            if budget_total and abs(budget_total - auto_calculated) > 0.01:
                budget_mode = "manual"
            else:
                budget_mode = "auto"

            # Load budget revisions for history display (paginate with helper)
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id,),
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
                budget_total if budget_mode == "manual" else None,
                currency_symbol,
                team_cost,
                None,  # Reset effective date picker
                revision_history,
                budget_mode,
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
            None,
            "€",
            None,
            None,
            error_history,
            "auto",
            f"Error: {str(e)}",
            f"Error: {str(e)}",
            "Page 1 of 1",
            True,
            True,
        )


# ============================================================================
# Budget Total Mode Toggle
# ============================================================================


@callback(
    [
        Output("budget-total-auto-container", "style"),
        Output("budget-total-manual-container", "style"),
    ],
    Input("budget-total-mode", "value"),
    prevent_initial_call=True,
)
def toggle_budget_total_mode(mode):
    """
    Show/hide budget total input containers based on selected mode.

    Args:
        mode: "auto" or "manual"

    Returns:
        Tuple of (auto_container_style, manual_container_style)
    """
    if mode == "auto":
        return {"display": "block"}, {"display": "none"}
    else:
        return {"display": "none"}, {"display": "block"}


# ============================================================================
# Currency Symbol Update
# ============================================================================


@callback(
    Output("budget-total-manual-currency", "children"),
    Input("budget-currency-symbol-input", "value"),
    prevent_initial_call=False,
)
def update_currency_displays(currency_symbol):
    """
    Update manual budget currency display when currency symbol changes.

    Args:
        currency_symbol: Currency symbol

    Returns:
        str: Currency symbol for manual budget input
    """
    return currency_symbol or "€"


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
        State("budget-total-mode", "value"),
        State("budget-time-allocated-input", "value"),
        State("budget-total-manual-input", "value"),
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
    budget_mode,
    time_allocated,
    budget_total_manual,
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
        budget_mode: "auto" or "manual" (for budget total calculation)
        time_allocated: Time allocated in weeks
        budget_total_manual: Manual budget total (only used if budget_mode is "manual")
        currency_symbol: Currency symbol
        team_cost: Team cost per week (weekly rate)
        revision_reason: Reason for budget change
        current_settings: Current budget settings from store
        effective_date: Effective date for retroactive budget entry

    Returns:
        Tuple of (status_message, updated_store_data)
    """
    if not n_clicks or not profile_id:
        return no_update, no_update

    from ui.toast_notifications import create_toast

    # Validate inputs
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

    try:
        # Calculate or use budget_total based on mode
        if budget_mode == "auto":
            budget_total = team_cost * time_allocated
        else:  # manual mode
            if not budget_total_manual or budget_total_manual <= 0:
                error = create_toast(
                    "Manual budget total must be greater than 0",
                    toast_type="danger",
                    header="Validation Error",
                    duration=4000,
                )
                return error, no_update
            budget_total = budget_total_manual

        now_iso = datetime.now(timezone.utc).isoformat()

        # Use effective_date if provided, otherwise use current date
        if effective_date:
            # Parse the date string from DatePickerSingle (format: YYYY-MM-DD)
            effective_dt = datetime.fromisoformat(effective_date)
            current_week = get_week_label(effective_dt)
            logger.info(
                f"Using effective date {effective_date} for budget revision (week: {current_week})"
            )
        else:
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
                            profile_id, revision_date, week_label,
                            time_allocated_weeks_delta, team_cost_delta, budget_total_delta,
                            revision_reason, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            profile_id,
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
                cursor.execute(
                    """
                    UPDATE budget_settings
                    SET time_allocated_weeks = ?,
                        team_cost_per_week_eur = ?,
                        budget_total_eur = ?,
                        currency_symbol = ?,
                        updated_at = ?
                    WHERE profile_id = ?
                """,
                    (
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        now_iso,
                        profile_id,
                    ),
                )

                success_msg = "Budget updated successfully"

            else:
                # Create new budget settings
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO budget_settings (
                        profile_id, time_allocated_weeks, team_cost_per_week_eur,
                        budget_total_eur, currency_symbol,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        profile_id,
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        now_iso,
                        now_iso,
                    ),
                )

                success_msg = "Budget configured successfully"

            conn.commit()

            # Get created_at for store (it might be from current_settings or just created)
            if current_settings and "created_at" in current_settings:
                created_at = current_settings["created_at"]
            else:
                # Query from database if not in store
                cursor.execute(
                    "SELECT created_at FROM budget_settings WHERE profile_id = ?",
                    (profile_id,),
                )
                result = cursor.fetchone()
                created_at = result[0] if result else now_iso

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
    Input("budget-settings-store", "data"),
    prevent_initial_call="initial_duplicate",
)
def refresh_current_budget_card(store_data):
    """
    Refresh current budget card when store updates (after save).

    Args:
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
# Refresh Budget Revision History After Save
# ============================================================================


@callback(
    Output("budget-revision-history", "children", allow_duplicate=True),
    [
        Input("budget-settings-store", "data"),
        Input("profile-selector", "value"),
        Input("budget-revision-history-page", "data"),
    ],
    prevent_initial_call=True,
)
def refresh_budget_revision_history(store_data, profile_id, current_page):
    """
    Refresh budget revision history when store updates (after save).

    Args:
        store_data: Updated budget settings store
        profile_id: Active profile identifier
        current_page: Current pagination page

    Returns:
        List of revision history UI elements
    """
    if not profile_id or not store_data:
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
                WHERE profile_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id,),
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


@callback(
    [
        Output("budget-time-allocated-input", "value", allow_duplicate=True),
        Output("budget-total-manual-input", "value", allow_duplicate=True),
        Output("budget-team-cost-input", "value", allow_duplicate=True),
        Output("budget-revision-reason-input", "value"),
    ],
    Input("cancel-budget-button", "n_clicks"),
    State("budget-settings-store", "data"),
    prevent_initial_call=True,
)
def cancel_budget_changes(n_clicks, current_settings):
    """
    Reset form to current settings when cancel is clicked.

    Args:
        n_clicks: Cancel button clicks
        current_settings: Current budget settings from store

    Returns:
        Tuple of (time_input, manual_total_input, cost_input, reason_input)
    """
    if not n_clicks or not current_settings:
        return no_update, no_update, no_update, no_update

    budget_total = current_settings.get("budget_total_eur")
    return (
        current_settings.get("time_allocated_weeks"),
        budget_total,
        current_settings.get("team_cost_per_week_eur"),
        "",
    )


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
    State("profile-selector", "value"),
    prevent_initial_call=True,
)
def update_revision_history_page(page, store_data, profile_id):
    """
    Update revision history table when page changes.

    Args:
        page: Current page number
        store_data: Budget settings store
        profile_id: Active profile identifier

    Returns:
        Tuple of (table, page_info, prev_disabled, next_disabled)
    """
    if not profile_id or not store_data:
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
                WHERE profile_id = ?
                ORDER BY revision_date DESC
            """,
                (profile_id,),
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
    Output("budget-delete-history-confirm-button", "disabled"),
    Input("budget-delete-history-confirm-checkbox", "value"),
    prevent_initial_call=True,
)
def enable_delete_confirm_button(checkbox_values):
    """
    Enable confirm button only when checkbox is checked.

    Args:
        checkbox_values: List of checked values

    Returns:
        bool: Button disabled state
    """
    return "confirmed" not in (checkbox_values or [])


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
        Output("budget-delete-history-modal", "is_open", allow_duplicate=True),
        Output("budget-revision-history", "children", allow_duplicate=True),
    ],
    Input("budget-delete-history-confirm-button", "n_clicks"),
    State("profile-selector", "value"),
    prevent_initial_call=True,
)
def confirm_delete_budget_history(n_clicks, profile_id):
    """
    Delete all budget revision history (danger zone action).

    Args:
        n_clicks: Confirm button clicks
        profile_id: Active profile identifier

    Returns:
        Tuple of (notification, updated_store, modal_state, revision_history)
    """
    if not n_clicks or not profile_id:
        return no_update, no_update, no_update, no_update

    from ui.toast_notifications import create_toast

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM budget_revisions
                WHERE profile_id = ?
                """,
                (profile_id,),
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
    Input("budget-delete-complete-confirm-checkbox", "value"),
    prevent_initial_call=True,
)
def enable_delete_complete_button(checkbox_values):
    """
    Enable confirm button only when checkbox is checked.

    Args:
        checkbox_values: List of checked values

    Returns:
        bool: Button disabled state
    """
    return "confirmed" not in (checkbox_values or [])


@callback(
    [
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
        Output("budget-delete-complete-modal", "is_open", allow_duplicate=True),
        Output("budget-revision-history", "children", allow_duplicate=True),
        Output("budget-time-allocated-input", "value", allow_duplicate=True),
        Output("budget-total-manual-input", "value", allow_duplicate=True),
        Output("budget-team-cost-input", "value", allow_duplicate=True),
    ],
    Input("budget-delete-complete-confirm-button", "n_clicks"),
    State("profile-selector", "value"),
    prevent_initial_call=True,
)
def confirm_delete_complete_budget(n_clicks, profile_id):
    """
    Delete complete budget configuration including all history (danger zone action).

    Args:
        n_clicks: Confirm button clicks
        profile_id: Active profile identifier

    Returns:
        Tuple of (notification, updated_store, modal_state, history, time_input, total_input, cost_input)
    """
    if not n_clicks or not profile_id:
        return (
            no_update,
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
                WHERE profile_id = ?
                """,
                (profile_id,),
            )

            # Delete budget settings
            cursor.execute(
                """
                DELETE FROM budget_settings
                WHERE profile_id = ?
                """,
                (profile_id,),
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

        return success, {}, False, empty_history, None, None, None

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
            no_update,
        )
