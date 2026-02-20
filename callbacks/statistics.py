"""
Statistics Callbacks Module

This module handles callbacks related to statistics data management.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _create_capacity_metrics_content(capacity_metrics, total_capacity):
    """
    Create the content for the capacity metrics section.

    Args:
        capacity_metrics: Dictionary with capacity metrics data
        total_capacity: Total weekly capacity in hours

    Returns:
        A Dash component with capacity metrics
    """
    if capacity_metrics is None:
        return html.Div(
            [
                html.P(
                    "No capacity metrics available. Please load project data to see metrics."
                ),
            ],
            className="text-muted",
        )

    # Extract metrics using correct keys from calculate_capacity_from_stats return value
    avg_hours_per_item = capacity_metrics.get("avg_hours_per_item", 0)
    avg_hours_per_point = capacity_metrics.get("avg_hours_per_point", 0)
    utilization_percentage = capacity_metrics.get("utilization_percentage", 0)

    # Determine utilization status and color
    if utilization_percentage > 100:
        status = "Over Capacity"
        color = "danger"
    elif utilization_percentage > 85:
        status = "Near Capacity"
        color = "warning"
    else:
        status = "Under Capacity"
        color = "success"

    # Calculate utilized capacity for display
    utilized_capacity = (
        (utilization_percentage / 100) * total_capacity if total_capacity > 0 else 0
    )

    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H6("Average Time"),
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                "Per Item: ", className="text-muted"
                                            ),
                                            html.Span(f"{avg_hours_per_item:.2f} hrs"),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Span(
                                                "Per Point: ", className="text-muted"
                                            ),
                                            html.Span(f"{avg_hours_per_point:.2f} hrs"),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.H6("Capacity Utilization"),
                            html.Div(
                                [
                                    dbc.Progress(
                                        value=min(utilization_percentage, 100),
                                        color=color,
                                        className="mb-2",
                                        style={"height": "20px"},
                                    ),
                                    html.Div(
                                        [
                                            html.Span(
                                                f"{utilization_percentage:.1f}% ",
                                                className=f"text-{color} font-weight-bold",
                                            ),
                                            html.Span(f"({status})"),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Span("Used: ", className="text-muted"),
                                            html.Span(
                                                f"{utilized_capacity:.1f} hrs of {total_capacity} hrs"
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            # Add trend display if available
            html.Div(
                [
                    html.H6("Recent Trend", className="mt-3"),
                    html.Div(
                        [
                            html.Span("Trend: ", className="text-muted"),
                            html.Span(
                                f"{capacity_metrics.get('recent_trend_percentage', 0):.1f}% ",
                                className=f"{'text-success' if capacity_metrics.get('recent_trend_percentage', 0) <= 0 else 'text-danger'}",
                            ),
                            html.Span(
                                f"({'decreasing' if capacity_metrics.get('recent_trend_percentage', 0) <= 0 else 'increasing'})",
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="mt-2",
                # Only show if trend data is available
                style={
                    "display": "block"
                    if "recent_trend_percentage" in capacity_metrics
                    else "none"
                },
            ),
        ]
    )


#######################################################################
# CALLBACKS
#######################################################################


def register(app):
    """
    Register all statistics-related callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        Output("current-statistics", "data"),
        Input("current-statistics", "modified_timestamp"),
        prevent_initial_call=True,
    )
    def reload_statistics_from_database(timestamp):
        """
        Reload statistics from database when modified_timestamp changes.

        This ensures UI reflects database state after external updates like:
        - Update Data (JIRA sync overwrites manual edits)
        - Force Refresh (complete data wipe and reload)
        - Query switching

        Args:
            timestamp: Timestamp from modified_timestamp trigger

        Returns:
            List of statistics dictionaries loaded from database
        """
        from dash.exceptions import PreventUpdate

        from configuration import logger
        from data.persistence import load_unified_project_data
        from data.profile_manager import get_active_profile

        logger.info(
            f"[Statistics] reload_statistics_from_database triggered by timestamp={timestamp}"
        )

        try:
            # Check if we have an active profile - prevent crash when last profile is deleted
            active_profile = get_active_profile()
            if not active_profile:
                logger.info(
                    "[Statistics] No active profile, skipping statistics reload"
                )
                raise PreventUpdate

            # Load fresh data from database
            unified_data = load_unified_project_data()
            statistics = unified_data.get("statistics", [])

            logger.info(f"[Statistics] Reloaded {len(statistics)} rows from database")
            if statistics:
                logger.info(
                    f"[Statistics] First row: {statistics[0].get('date', 'NO_DATE')}, "
                    f"Last row: {statistics[-1].get('date', 'NO_DATE')}"
                )

            return statistics

        except Exception as e:
            logger.error(
                f"[Statistics] Failed to reload from database: {e}", exc_info=True
            )
            raise PreventUpdate from e

    @app.callback(
        [
            Output("current-statistics", "data", allow_duplicate=True),
            Output("current-statistics", "modified_timestamp", allow_duplicate=True),
            Output(
                "chart-cache", "data", allow_duplicate=True
            ),  # Clear cache to force refresh
        ],
        [Input("statistics-table", "data")],
        [
            State("app-init-complete", "data"),
            State("current-statistics", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_statistics_on_edit(table_data, init_complete, current_statistics):
        """
        Save statistics to database when user edits the table.

        This callback watches for changes to the statistics-table data property
        (triggered when user edits cells in the Weekly Data tab) and saves the
        updated data to disk. Then clears chart cache to force visualization refresh.

        CRITICAL: This callback can be triggered by:
        1. User manually editing a cell (SHOULD save)
        2. Tab re-rendering with fresh data from database (SHOULD NOT save - would create loop)

        To distinguish: Compare table_data with current_statistics. If they match,
        this is a re-render, not a user edit.
        """
        from datetime import datetime

        from configuration import logger
        from data.persistence import save_statistics

        logger.info(
            f"[Statistics] save_statistics_on_edit triggered: "
            f"table_data={'None' if table_data is None else f'{len(table_data)} rows'}, "
            f"init_complete={init_complete}"
        )

        # Validate table_data before saving
        if not table_data:
            logger.warning("[Statistics] PREVENTING save - table_data is empty")
            raise PreventUpdate

        # CRITICAL FIX: Prevent save loop when tab re-renders with database data
        # If table_data matches current_statistics, this is NOT a user edit
        if current_statistics and len(table_data) == len(current_statistics):
            # Quick check: compare a few key values to see if data is identical
            # (full deep comparison would be expensive)
            if len(table_data) > 0:
                first_table = table_data[0]
                first_current = current_statistics[0]
                last_table = table_data[-1]
                last_current = current_statistics[-1]

                # Compare key fields to detect if this is the same data
                if (
                    first_table.get("date") == first_current.get("date")
                    and first_table.get("remaining_items")
                    == first_current.get("remaining_items")
                    and first_table.get("completed_items")
                    == first_current.get("completed_items")
                    and last_table.get("date") == last_current.get("date")
                    and last_table.get("remaining_items")
                    == last_current.get("remaining_items")
                    and last_table.get("completed_items")
                    == last_current.get("completed_items")
                ):
                    logger.info(
                        "[Statistics] PREVENTING save - table_data matches current_statistics "
                        "(tab re-render, not user edit)"
                    )
                    raise PreventUpdate

        # Validate table_data before saving
        if not table_data:
            logger.warning("[Statistics] PREVENTING save - table_data is empty")
            raise PreventUpdate

        # Log first and last row for debugging
        if len(table_data) > 0:
            logger.info(
                f"[Statistics] Saving {len(table_data)} rows. "
                f"First: {table_data[0].get('date', 'NO_DATE')}, "
                f"Last: {table_data[-1].get('date', 'NO_DATE')}"
            )

        # Save to database
        try:
            save_statistics(table_data)
            logger.info(
                f"[Statistics] ✓ Table edited and saved SUCCESSFULLY to DB: {len(table_data)} rows"
            )
        except Exception as e:
            logger.error(
                f"[Statistics] ✗ FAILED to save statistics to DB: {e}",
                exc_info=True,
            )
            # Still return the data to update the browser store
            # But the DB save failed

        # Return updated data, timestamp, and clear chart cache to force refresh
        timestamp = int(datetime.now().timestamp() * 1000)
        logger.info(f"[Statistics] Returning updated data with timestamp {timestamp}")
        return table_data, timestamp, {}

    @app.callback(
        Output("statistics-table", "data", allow_duplicate=True),
        [Input("add-row-button", "n_clicks")],
        [State("statistics-table", "data")],
        prevent_initial_call=True,
    )
    def add_table_row(n_clicks, current_data):
        """
        Add a new row to the statistics table.

        Calculates the next Monday date (7 days after most recent entry)
        and inserts a new row at the beginning of the table.
        """
        from datetime import datetime, timedelta

        from configuration import logger
        from data.iso_week_bucketing import get_week_label

        if not n_clicks or not current_data:
            raise PreventUpdate

        # Find the most recent date
        try:
            date_objects = [
                datetime.strptime(row["date"], "%Y-%m-%d")
                for row in current_data
                if row.get("date") and len(row.get("date", "")) == 10
            ]
            if date_objects:
                most_recent_date = max(date_objects)
                # Set new date to 7 days after the most recent
                new_date = (most_recent_date + timedelta(days=7)).strftime("%Y-%m-%d")

                # CRITICAL: Prevent future dates beyond today
                # Statistics for future weeks make no sense (no completed/created items yet)
                today = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                proposed_date = datetime.strptime(new_date, "%Y-%m-%d")
                if proposed_date > today:
                    logger.warning(
                        f"Cannot add row for future date {new_date} (beyond today {today.strftime('%Y-%m-%d')}). "
                        "Statistics are historical data only."
                    )
                    raise PreventUpdate
            else:
                new_date = datetime.now().strftime("%Y-%m-%d")
        except (ValueError, KeyError):
            # Handle any date parsing errors
            new_date = datetime.now().strftime("%Y-%m-%d")

        # Calculate week_label for the new row
        try:
            date_obj = datetime.strptime(new_date, "%Y-%m-%d")
            week_label = get_week_label(date_obj)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate week_label for {new_date}: {e}")
            week_label = ""

        # Insert at beginning (will be at top with desc sorting)
        new_row = {
            "date": new_date,
            "week_label": week_label,
            "completed_items": 0,
            "completed_points": 0,
            "created_items": 0,
            "created_points": 0,
        }

        updated_data = [new_row] + current_data
        logger.info(f"Added new row to statistics table: {new_date} ({week_label})")

        return updated_data

    # REMOVED: update_and_save_statistics and update_table callbacks
    # These callbacks referenced statistics-table which only exists in the Weekly Data tab,
    # causing ReferenceError at app registration (Dash validates all I/O at startup).
    #
    # Statistics are now:
    # - Loaded from database when tab is rendered (callbacks/visualization.py)
    # - Saved when Update Data runs (callbacks/settings.py)
    # - Editable in the table (but changes not persisted until Update Data)
    #
    # File upload functionality (CSV/JSON/ZIP) needs to be moved to a different callback
    # that doesn't depend on statistics-table existing in main layout.

    # REMOVED: toggle_sample_data_alert callback
    # Sample data alert now uses Bootstrap's built-in dismissable=True behavior.
    # No callback needed - the alert automatically closes when user clicks the × button.
    # Alert visibility is controlled by is_open=is_sample_data in ui/layout.py

    # REMOVED: Obsolete callback for jira-data-reload-trigger (store doesn't exist)
    # This callback was part of old data source selection UI that has been removed
    # JIRA data refresh now happens directly through the Update Data button
    # and statistics are reloaded via the existing callbacks

    # REMOVED: Obsolete callback for updating project scope from jira-data-reload-trigger
    # Project scope is now updated directly when JIRA data is fetched
    # via the Calculate Scope button in the settings panel

    # Callback for column explanations toggle
    @app.callback(
        Output("column-explanations-collapse", "is_open"),
        [Input("column-explanations-toggle", "n_clicks")],
        [State("column-explanations-collapse", "is_open")],
    )
    def toggle_column_explanations(n_clicks, is_open):
        """Toggle the column explanations collapse section."""
        if n_clicks:
            return not is_open
        return is_open
