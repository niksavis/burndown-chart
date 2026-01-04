"""
Callbacks for budget configuration UI.

Handles budget settings load/save/update/reconfigure operations with
revision tracking and modal interactions.
"""

import logging
from datetime import datetime, timezone
from dash import callback, Output, Input, State, no_update, ctx
import dash_bootstrap_components as dbc

from data.database import get_db_connection
from data.iso_week_bucketing import get_week_label

logger = logging.getLogger(__name__)


# ============================================================================
# Budget Settings Load
# ============================================================================


@callback(
    [
        Output("budget-settings-store", "data"),
        Output("budget-config-status-indicator", "children"),
        Output("budget-time-allocated-input", "value"),
        Output("budget-total-input", "value"),
        Output("budget-currency-symbol-input", "value"),
        Output("budget-team-cost-input", "value"),
        Output("budget-cost-rate-type", "value"),
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
    if not profile_id or active_tab != "budget-tab":
        return (
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
                # No budget configured
                status = [
                    dbc.Badge("Not Configured", color="secondary", className="me-2"),
                    "Configure budget to enable tracking",
                ]
                return {}, status, None, None, "€", None, "weekly"

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

            status = [
                dbc.Badge("Configured", color="success", className="me-2"),
                f"Last updated: {updated_at[:10] if updated_at else 'Unknown'}",
            ]

            return (
                store_data,
                status,
                time_allocated,
                budget_total,
                currency_symbol,
                team_cost,
                cost_rate_type,
            )

    except Exception as e:
        logger.error(f"Failed to load budget settings: {e}")
        error_status = [
            dbc.Badge("Error", color="danger", className="me-2"),
            f"Failed to load settings: {str(e)}",
        ]
        return {}, error_status, None, None, "€", None, "weekly"


# ============================================================================
# Budget Mode Toggle
# ============================================================================


@callback(
    [
        Output("budget-reconfigure-warning", "is_open"),
        Output("budget-revision-reason-container", "style"),
    ],
    Input("budget-mode-selector", "value"),
    prevent_initial_call=True,
)
def toggle_budget_mode(mode):
    """
    Show/hide warnings and inputs based on selected mode.

    Args:
        mode: "update" or "reconfigure"

    Returns:
        Tuple of (warning_is_open, revision_container_style)
    """
    if mode == "reconfigure":
        return True, {"display": "none"}
    else:
        return False, {"display": "block"}


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
        Output("budget-reconfigure-modal", "is_open"),
    ],
    Input("save-budget-button", "n_clicks"),
    [
        State("profile-selector", "value"),
        State("budget-mode-selector", "value"),
        State("budget-time-allocated-input", "value"),
        State("budget-total-input", "value"),
        State("budget-currency-symbol-input", "value"),
        State("budget-team-cost-input", "value"),
        State("budget-cost-rate-type", "value"),
        State("budget-revision-reason-input", "value"),
        State("budget-settings-store", "data"),
    ],
    prevent_initial_call=True,
)
def save_budget_settings(
    n_clicks,
    profile_id,
    mode,
    time_allocated,
    budget_total,
    currency_symbol,
    team_cost,
    cost_rate_type,
    revision_reason,
    current_settings,
):
    """
    Save or update budget settings with revision tracking.

    Args:
        n_clicks: Button click count
        profile_id: Active profile identifier
        mode: "update" or "reconfigure"
        time_allocated: Time allocated in weeks
        budget_total: Total budget amount (optional)
        currency_symbol: Currency symbol
        team_cost: Team cost per period
        cost_rate_type: "weekly", "daily", or "hourly"
        revision_reason: Reason for budget change
        current_settings: Current budget settings from store

    Returns:
        Tuple of (status_message, updated_store_data, modal_is_open)
    """
    if not n_clicks or not profile_id:
        return no_update, no_update, no_update

    from ui.toast_notifications import create_toast

    # Validate inputs
    if not time_allocated or time_allocated < 1:
        error = create_toast(
            "Time allocated must be at least 1 week",
            toast_type="danger",
            header="Validation Error",
            duration=4000,
        )
        return error, no_update, no_update

    if not team_cost or team_cost <= 0:
        error = create_toast(
            "Team cost must be greater than 0",
            toast_type="danger",
            header="Validation Error",
            duration=4000,
        )
        return error, no_update, no_update

    # Check if reconfigure mode - show modal for confirmation
    if mode == "reconfigure" and current_settings:
        return no_update, no_update, True

    try:
        # Convert team cost to weekly rate
        if cost_rate_type == "daily":
            team_cost_weekly = team_cost * 5
        elif cost_rate_type == "hourly":
            team_cost_weekly = team_cost * 40
        else:
            team_cost_weekly = team_cost

        # Calculate budget_total if not provided
        if not budget_total:
            budget_total = team_cost_weekly * time_allocated

        now_iso = datetime.now(timezone.utc).isoformat()
        current_week = get_week_label(datetime.now())

        with get_db_connection() as conn:
            cursor = conn.cursor()

            if mode == "update" and current_settings:
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
                # Create new budget settings (or reconfigure handled by modal)
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
            return success, new_store, False

    except Exception as e:
        logger.error(f"Failed to save budget settings: {e}")
        error = create_toast(
            f"Failed to save: {str(e)}",
            toast_type="danger",
            header="Save Failed",
            duration=4000,
        )
        return error, no_update, False


# ============================================================================
# Reconfigure Confirmation Modal
# ============================================================================


@callback(
    Output("budget-reconfigure-confirm-button", "disabled"),
    Input("budget-reconfigure-confirm-checkbox", "value"),
    prevent_initial_call=True,
)
def enable_reconfigure_button(checkbox_value):
    """
    Enable confirm button only when checkbox is checked.

    Args:
        checkbox_value: List of checked values

    Returns:
        bool: Button disabled state
    """
    return "confirmed" not in (checkbox_value or [])


@callback(
    [
        Output("budget-reconfigure-modal", "is_open", allow_duplicate=True),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-settings-store", "data", allow_duplicate=True),
        Output("budget-reconfigure-confirm-checkbox", "value"),
    ],
    [
        Input("budget-reconfigure-cancel-button", "n_clicks"),
        Input("budget-reconfigure-confirm-button", "n_clicks"),
    ],
    [
        State("profile-selector", "value"),
        State("budget-time-allocated-input", "value"),
        State("budget-total-input", "value"),
        State("budget-currency-symbol-input", "value"),
        State("budget-team-cost-input", "value"),
        State("budget-cost-rate-type", "value"),
    ],
    prevent_initial_call=True,
)
def handle_reconfigure_modal(
    cancel_clicks,
    confirm_clicks,
    profile_id,
    time_allocated,
    budget_total,
    currency_symbol,
    team_cost,
    cost_rate_type,
):
    """
    Handle reconfigure confirmation modal interactions.

    Args:
        cancel_clicks: Cancel button clicks
        confirm_clicks: Confirm button clicks
        profile_id: Active profile identifier
        time_allocated: Time allocated in weeks
        budget_total: Total budget amount
        currency_symbol: Currency symbol
        team_cost: Team cost per period
        cost_rate_type: Cost rate type

    Returns:
        Tuple of (modal_is_open, status_message, store_data, checkbox_value)
    """
    trigger = ctx.triggered_id

    if trigger == "budget-reconfigure-cancel-button":
        # Close modal without action
        return False, no_update, no_update, []

    elif trigger == "budget-reconfigure-confirm-button":
        # Reconfigure budget (delete revisions and reset baseline)
        from ui.toast_notifications import create_toast

        try:
            # Convert team cost to weekly rate
            if cost_rate_type == "daily":
                team_cost_weekly = team_cost * 5
            elif cost_rate_type == "hourly":
                team_cost_weekly = team_cost * 40
            else:
                team_cost_weekly = team_cost

            if not budget_total:
                budget_total = team_cost_weekly * time_allocated

            now_iso = datetime.now(timezone.utc).isoformat()

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Delete all revisions for this profile
                cursor.execute(
                    """
                    DELETE FROM budget_revisions WHERE profile_id = ?
                """,
                    (profile_id,),
                )

                # Reset budget_settings as fresh baseline
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

                conn.commit()

            new_store = {
                "time_allocated_weeks": time_allocated,
                "budget_total_eur": budget_total,
                "currency_symbol": currency_symbol,
                "team_cost_per_week_eur": team_cost_weekly,
                "cost_rate_type": cost_rate_type,
                "updated_at": now_iso,
            }

            success = create_toast(
                "Budget reconfigured successfully. All revision history deleted.",
                toast_type="success",
                header="Budget Reconfigured",
                duration=4000,
            )

            return False, success, new_store, []

        except Exception as e:
            logger.error(f"Failed to reconfigure budget: {e}")
            error = create_toast(
                f"Failed to reconfigure: {str(e)}",
                toast_type="danger",
                header="Reconfigure Failed",
                duration=4000,
            )
            return False, error, no_update, []

    return no_update, no_update, no_update, no_update


# ============================================================================
# Cancel Button
# ============================================================================


@callback(
    [
        Output("budget-time-allocated-input", "value", allow_duplicate=True),
        Output("budget-total-input", "value", allow_duplicate=True),
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
        Tuple of (time_input, total_input, cost_input, reason_input)
    """
    if not n_clicks or not current_settings:
        return no_update, no_update, no_update, no_update

    return (
        current_settings.get("time_allocated_weeks"),
        current_settings.get("budget_total_eur"),
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
