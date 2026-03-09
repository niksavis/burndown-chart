"""
Budget settings - save/update callback.

Handles saving new budget settings and updating existing ones,
including revision tracking and baseline velocity capture.
"""

import logging
from datetime import UTC, datetime

from dash import Input, Output, State, callback, no_update

from data.database import get_db_connection
from data.iso_week_bucketing import get_week_label
from data.persistence import load_unified_project_data
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


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

    budget_total = team_cost * time_allocated

    try:
        now_iso = datetime.now(UTC).isoformat()

        if effective_date:
            effective_dt = datetime.fromisoformat(effective_date)
            current_week = get_week_label(effective_dt)
            effective_dt_iso = effective_dt.replace(tzinfo=UTC).isoformat()
            logger.info(
                f"Using effective date {effective_date} "
                f"for budget revision (week: {current_week})"
            )
        else:
            effective_dt_iso = now_iso
            current_week = get_week_label(datetime.now())
            logger.info(
                f"Using current date for budget revision (week: {current_week})"
            )

        if current_settings:
            # Update mode: preserve existing baseline velocities
            baseline_velocity_items = current_settings.get("baseline_velocity_items", 0)
            baseline_velocity_points = current_settings.get(
                "baseline_velocity_points", 0
            )
            logger.info(
                "Budget update: Preserving existing baseline velocity: "
                f"items={baseline_velocity_items:.2f}, "
                f"points={baseline_velocity_points:.2f}"
            )
        else:
            # Create mode: capture baseline from Recent Completions (last 4 weeks)
            import pandas as pd

            unified_data = load_unified_project_data()
            statistics_list = unified_data.get("statistics", [])

            if statistics_list:
                statistics_df = pd.DataFrame(statistics_list)
                recent_window = min(4, len(statistics_df))
                recent_data = statistics_df.tail(recent_window)

                baseline_velocity_items = (
                    recent_data["completed_items"].mean()
                    if not recent_data.empty
                    else 0.0
                )
                baseline_velocity_points = (
                    recent_data["completed_points"].mean()
                    if not recent_data.empty
                    and "completed_points" in recent_data.columns
                    else 0.0
                )
            else:
                baseline_velocity_items = 0.0
                baseline_velocity_points = 0.0

            logger.info(
                "Budget creation: Capturing baseline velocity "
                "from last 4 weeks (Recent Completions): "
                f"items={baseline_velocity_items:.2f}, "
                f"points={baseline_velocity_points:.2f}"
            )

        with get_db_connection() as conn:
            cursor = conn.cursor()

            if current_settings:
                old_time = current_settings.get("time_allocated_weeks", 0)
                old_cost = current_settings.get("team_cost_per_week_eur", 0)
                old_total = current_settings.get("budget_total_eur", 0)

                time_delta = time_allocated - old_time
                cost_delta = team_cost - old_cost
                total_delta = budget_total - old_total

                if time_delta != 0 or cost_delta != 0 or total_delta != 0:
                    cursor.execute(
                        """
                        INSERT INTO budget_revisions (
                            profile_id, query_id, revision_date, week_label,
                            time_allocated_weeks_delta,
                            team_cost_delta,
                            budget_total_delta,
                            revision_reason, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            profile_id,
                            query_id,
                            effective_dt_iso,
                            current_week,
                            time_delta,
                            cost_delta,
                            total_delta,
                            revision_reason,
                            now_iso,
                        ),
                    )

                cursor.execute(
                    """
                    UPDATE budget_settings
                    SET time_allocated_weeks = ?,
                        team_cost_per_week_eur = ?,
                        budget_total_eur = ?,
                        currency_symbol = ?,
                        baseline_velocity_items = ?,
                        baseline_velocity_points = ?,
                        created_at = ?,
                        updated_at = ?
                    WHERE profile_id = ? AND query_id = ?
                """,
                    (
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        baseline_velocity_items,
                        baseline_velocity_points,
                        effective_dt_iso,
                        now_iso,
                        profile_id,
                        query_id,
                    ),
                )

                success_msg = "Budget updated successfully"

            else:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO budget_settings (
                        profile_id, query_id,
                        time_allocated_weeks, team_cost_per_week_eur,
                        budget_total_eur, currency_symbol,
                        baseline_velocity_items, baseline_velocity_points,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        profile_id,
                        query_id,
                        time_allocated,
                        team_cost,
                        budget_total,
                        currency_symbol,
                        baseline_velocity_items,
                        baseline_velocity_points,
                        effective_dt_iso,
                        now_iso,
                    ),
                )

                success_msg = "Budget configured successfully"

            conn.commit()

            cursor.execute(
                "SELECT created_at FROM budget_settings "
                "WHERE profile_id = ? AND query_id = ?",
                (profile_id, query_id),
            )
            result = cursor.fetchone()
            created_at = result[0] if result else effective_dt_iso

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
