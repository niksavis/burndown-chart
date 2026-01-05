"""
Callbacks for budget configuration UI.

Handles budget settings load/save/update operations with
revision tracking and modal interactions.
"""

import logging
from datetime import datetime, timezone
from dash import callback, Output, Input, State, no_update, ctx, html

from data.database import get_db_connection
from data.iso_week_bucketing import get_week_label
from ui.budget_settings_card import _create_current_budget_card_content

logger = logging.getLogger(__name__)


# ============================================================================
# Budget Settings Load
# ============================================================================


@callback(
    [
        Output("budget-settings-store", "data"),
        Output("budget-current-card", "children"),
        Output("budget-time-allocated-input", "value"),
        Output("budget-total-manual-input", "value"),
        Output("budget-currency-symbol-input", "value"),
        Output("budget-team-cost-input", "value"),
        Output("budget-cost-rate-type", "value"),
        Output("budget-effective-date-picker", "date"),
        Output("budget-revision-history", "children"),
        Output("budget-total-mode", "value"),
        Output("budget-time-current-value", "children"),
        Output("budget-cost-current-value", "children"),
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
                           budget_total_eur, currency_symbol, cost_rate_type
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
                        "cost_rate_type": result[4] or "weekly",
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
        )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Query budget settings
            cursor.execute(
                """
                SELECT time_allocated_weeks, budget_total_eur, currency_symbol,
                       team_cost_per_week_eur, cost_rate_type, updated_at
                FROM budget_settings
                WHERE profile_id = ?
            """,
                (profile_id,),
            )

            result = cursor.fetchone()

            if not result:
                # No budget configured - return placeholder content
                current_card_content = _create_current_budget_card_content(
                    budget_data=None, show_placeholder=True
                )

                empty_history = [
                    html.P(
                        "No budget configured yet.",
                        className="text-muted small",
                    )
                ]
                return (
                    {},
                    current_card_content,
                    None,
                    None,
                    "€",
                    None,
                    "weekly",
                    None,
                    empty_history,
                    "auto",  # Default to auto mode
                    "Current: Not set",
                    "Current: Not set",
                )

            # Budget exists
            time_allocated = result[0]
            budget_total = result[1]
            currency_symbol = result[2] or "€"
            team_cost = result[3]
            cost_rate_type = result[4] or "weekly"
            updated_at = result[5]

            # Store data for later use
            store_data = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost,
                "cost_rate_type": cost_rate_type,
                "updated_at": updated_at,
            }

            # Get week label for updated_at
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                week_label = get_week_label(dt)
            except Exception:
                week_label = ""

            # Prepare budget data for current card
            budget_card_data = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "team_cost_per_week_eur": team_cost,
                "currency_symbol": currency_symbol,
                "updated_at": updated_at,
                "week_label": week_label,
            }

            # Create current budget card content
            current_card_content = _create_current_budget_card_content(
                budget_data=budget_card_data, live_metrics=None, show_placeholder=False
            )

            # Determine budget total mode
            # If budget_total equals time * team_cost, it's auto mode, otherwise manual
            auto_calculated = time_allocated * team_cost
            if budget_total and abs(budget_total - auto_calculated) > 0.01:
                budget_mode = "manual"
            else:
                budget_mode = "auto"

            # Load budget revisions for history display
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ?
                ORDER BY revision_date DESC
                LIMIT 10
            """,
                (profile_id,),
            )

            revisions = cursor.fetchall()
            if revisions:
                revision_items = []
                for rev in revisions:
                    (
                        rev_date,
                        week_label_rev,
                        time_delta,
                        cost_delta,
                        total_delta,
                        reason,
                    ) = rev

                    # Format changes
                    changes = []
                    if time_delta != 0:
                        sign = "+" if time_delta > 0 else ""
                        changes.append(f"{sign}{time_delta} weeks")
                    if cost_delta != 0:
                        sign = "+" if cost_delta > 0 else ""
                        changes.append(f"{sign}{currency_symbol}{cost_delta:.0f}/week")
                    if total_delta != 0:
                        sign = "+" if total_delta > 0 else ""
                        changes.append(
                            f"{sign}{currency_symbol}{total_delta:,.0f} total"
                        )

                    change_text = ", ".join(changes) if changes else "No changes"

                    revision_items.append(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Strong(
                                            f"Week {week_label_rev}",
                                            className="text-primary",
                                        ),
                                        html.Small(
                                            f" ({rev_date[:10]})",
                                            className="text-muted ms-2",
                                        ),
                                    ],
                                    className="mb-1",
                                ),
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-arrow-right text-muted me-2"
                                        ),
                                        html.Span(change_text, className="fw-medium"),
                                    ],
                                    className="mb-1",
                                ),
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-comment-dots text-muted me-2"
                                        ),
                                        html.Span(
                                            reason or "No reason provided",
                                            className="text-muted small fst-italic",
                                        ),
                                    ]
                                )
                                if reason
                                else None,
                            ],
                            className="border-start border-3 border-primary ps-3 mb-3",
                        )
                    )

                revision_history = revision_items
            else:
                revision_history = [
                    html.P(
                        "No revisions yet. Budget changes will appear here after you update the budget.",
                        className="text-muted small",
                    )
                ]

            return (
                store_data,
                current_card_content,
                time_allocated,
                budget_total if budget_mode == "manual" else None,
                currency_symbol,
                team_cost,
                cost_rate_type,
                None,  # Reset effective date picker
                revision_history,
                budget_mode,
                f"Current: {time_allocated} weeks",
                f"Current: {currency_symbol}{team_cost:,.2f}/week",
            )

    except Exception as e:
        logger.error(f"Failed to load budget settings: {e}")

        current_card_content = _create_current_budget_card_content(
            budget_data=None, show_placeholder=True
        )

        error_history = [
            html.P(
                f"Error loading revision history: {str(e)}",
                className="text-danger small",
            )
        ]
        return (
            {},
            current_card_content,
            None,
            None,
            "€",
            None,
            "weekly",
            None,
            error_history,
            "auto",
            f"Error: {str(e)}",
            f"Error: {str(e)}",
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
# Cost Rate Type Conversion Helper
# ============================================================================


@callback(
    [
        Output("budget-cost-rate-unit", "children"),
        Output("budget-cost-conversion-helper", "children"),
    ],
    Input("budget-cost-rate-type", "value"),
    State("budget-currency-symbol-input", "value"),
    prevent_initial_call=True,
)
def update_cost_rate_helper(rate_type, currency_symbol):
    """
    Update cost rate unit label and conversion helper text.

    Args:
        rate_type: "weekly", "daily", or "hourly"
        currency_symbol: Currency symbol for display

    Returns:
        Tuple of (unit_label, helper_text)
    """
    currency = currency_symbol or "€"

    if rate_type == "daily":
        unit = f"{currency}/day"
        helper = "Will be converted to weekly (×5 days)"
    elif rate_type == "hourly":
        unit = f"{currency}/hour"
        helper = "Will be converted to weekly (×40 hours)"
    else:  # weekly
        unit = f"{currency}/week"
        helper = "Enter weekly team cost"

    return unit, helper


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
        State("budget-cost-rate-type", "value"),
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
    cost_rate_type,
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
        team_cost: Team cost per period
        cost_rate_type: "weekly", "daily", or "hourly"
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
        # Convert team cost to weekly rate
        if cost_rate_type == "daily":
            team_cost_weekly = team_cost * 5
        elif cost_rate_type == "hourly":
            team_cost_weekly = team_cost * 40
        else:
            team_cost_weekly = team_cost

        # Calculate or use budget_total based on mode
        if budget_mode == "auto":
            budget_total = team_cost_weekly * time_allocated
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
                cost_delta = team_cost_weekly - old_cost
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
                        cost_rate_type = ?,
                        updated_at = ?
                    WHERE profile_id = ?
                """,
                    (
                        time_allocated,
                        team_cost_weekly,
                        budget_total,
                        currency_symbol,
                        cost_rate_type,
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
                        budget_total_eur, currency_symbol, cost_rate_type,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        profile_id,
                        time_allocated,
                        team_cost_weekly,
                        budget_total,
                        currency_symbol,
                        cost_rate_type,
                        now_iso,
                        now_iso,
                    ),
                )

                success_msg = "Budget configured successfully"

            conn.commit()

            # Update store
            new_store = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost_weekly,
                "cost_rate_type": cost_rate_type,
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
# Refresh Budget Revision History After Save
# ============================================================================


@callback(
    Output("budget-revision-history", "children", allow_duplicate=True),
    [
        Input("budget-settings-store", "data"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=True,
)
def refresh_budget_revision_history(store_data, profile_id):
    """
    Refresh budget revision history when store updates (after save).

    Args:
        store_data: Updated budget settings store
        profile_id: Active profile identifier

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

            # Load budget revisions
            cursor.execute(
                """
                SELECT revision_date, week_label, time_allocated_weeks_delta,
                       team_cost_delta, budget_total_delta, revision_reason
                FROM budget_revisions
                WHERE profile_id = ?
                ORDER BY revision_date DESC
                LIMIT 10
            """,
                (profile_id,),
            )

            revisions = cursor.fetchall()
            if revisions:
                revision_items = []
                for rev in revisions:
                    (
                        rev_date,
                        week_label,
                        time_delta,
                        cost_delta,
                        total_delta,
                        reason,
                    ) = rev

                    # Format changes
                    changes = []
                    if time_delta != 0:
                        sign = "+" if time_delta > 0 else ""
                        changes.append(f"{sign}{time_delta} weeks")
                    if cost_delta != 0:
                        sign = "+" if cost_delta > 0 else ""
                        changes.append(f"{sign}{currency_symbol}{cost_delta:.0f}/week")
                    if total_delta != 0:
                        sign = "+" if total_delta > 0 else ""
                        changes.append(
                            f"{sign}{currency_symbol}{total_delta:,.0f} total"
                        )

                    change_text = ", ".join(changes) if changes else "No changes"

                    revision_items.append(
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Strong(
                                            f"Week {week_label}",
                                            className="text-primary",
                                        ),
                                        html.Small(
                                            f" ({rev_date[:10]})",
                                            className="text-muted ms-2",
                                        ),
                                    ],
                                    className="mb-1",
                                ),
                                html.Div(
                                    [
                                        html.I(
                                            className="fas fa-arrow-right text-muted me-2"
                                        ),
                                        html.Span(change_text, className="fw-medium"),
                                    ],
                                    className="mb-1",
                                ),
                                (
                                    html.Div(
                                        [
                                            html.I(
                                                className="fas fa-comment-dots text-muted me-2"
                                            ),
                                            html.Span(
                                                reason or "No reason provided",
                                                className="text-muted small fst-italic",
                                            ),
                                        ]
                                    )
                                    if reason
                                    else None
                                ),
                            ],
                            className="border-start border-3 border-primary ps-3 mb-3",
                        )
                    )

                return revision_items
            else:
                return [
                    html.P(
                        "No revisions yet. Budget changes will appear here after you update the budget.",
                        className="text-muted small",
                    )
                ]

    except Exception as e:
        logger.error(f"Failed to refresh budget revision history: {e}")
        return [
            html.P(
                f"Error loading revision history: {str(e)}",
                className="text-danger small",
            )
        ]


# ============================================================================
# Revision History Toggle (in Advanced Options)
# ============================================================================


@callback(
    [
        Output("budget-revision-history-collapse", "is_open"),
        Output("budget-revision-history-chevron", "className"),
    ],
    Input("budget-revision-history-toggle", "n_clicks"),
    State("budget-revision-history-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_revision_history_in_advanced(n_clicks, is_open):
    """
    Toggle budget revision history collapse within advanced options.

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
# Advanced Options Toggle
# ============================================================================


@callback(
    [
        Output("advanced-options-collapse", "is_open"),
        Output("advanced-options-chevron", "className"),
    ],
    Input("advanced-options-toggle", "n_clicks"),
    State("advanced-options-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_advanced_options(n_clicks, is_open):
    """
    Toggle advanced options collapse.

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


# ============================================================================
# Budget Total Auto Preview
# ============================================================================


@callback(
    Output("budget-total-auto-preview", "children"),
    [
        Input("budget-time-allocated-input", "value"),
        Input("budget-team-cost-input", "value"),
        Input("budget-cost-rate-type", "value"),
        Input("budget-currency-symbol-input", "value"),
    ],
    prevent_initial_call=False,
)
def update_budget_total_preview(time_allocated, team_cost, cost_rate_type, currency):
    """
    Update auto-calculated budget total preview.

    Args:
        time_allocated: Time allocated in weeks
        team_cost: Team cost input
        cost_rate_type: "weekly", "daily", or "hourly"
        currency: Currency symbol

    Returns:
        str: Formatted budget total preview
    """
    if not time_allocated or not team_cost:
        return f"{currency or '€'}0.00"

    # Convert to weekly
    if cost_rate_type == "daily":
        team_cost_weekly = team_cost * 5
    elif cost_rate_type == "hourly":
        team_cost_weekly = team_cost * 40
    else:
        team_cost_weekly = team_cost

    total = time_allocated * team_cost_weekly
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
        Tuple of (notification, updated_store, modal_state)
    """
    if not n_clicks or not profile_id:
        return no_update, no_update, no_update

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

        return success, no_update, False

    except Exception as e:
        logger.error(f"Failed to delete budget history: {e}")
        error = create_toast(
            f"Failed to delete budget history: {str(e)}",
            toast_type="danger",
            header="Error",
            duration=5000,
        )
        return error, no_update, False
