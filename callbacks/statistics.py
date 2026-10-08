from datetime import datetime, timedelta

import dash_bootstrap_components as dbc
from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from configuration import logger
from data.iso_week_bucketing import get_week_label
from data.persistence import load_unified_project_data, save_statistics
from data.profile_manager import get_active_profile


def _create_capacity_metrics_content(capacity_metrics, total_capacity):

    if capacity_metrics is None:
        return html.Div(
            [
                html.P(
                    "No capacity metrics available. Please load project "
                    "data to see metrics."
                ),
            ],
            className="text-muted",
        )

    avg_hours_per_item = capacity_metrics.get("avg_hours_per_item", 0)
    avg_hours_per_point = capacity_metrics.get("avg_hours_per_point", 0)
    utilization_percentage = capacity_metrics.get("utilization_percentage", 0)
    recent_trend_percentage = capacity_metrics.get("recent_trend_percentage", 0)

    if utilization_percentage > 100:
        status = "Over Capacity"
        color = "danger"
    elif utilization_percentage > 85:
        status = "Near Capacity"
        color = "warning"
    else:
        status = "Under Capacity"
        color = "success"

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
                                                className=(
                                                    f"text-{color} font-weight-bold"
                                                ),
                                            ),
                                            html.Span(f"({status})"),
                                        ]
                                    ),
                                    html.Div(
                                        [
                                            html.Span("Used: ", className="text-muted"),
                                            html.Span(
                                                f"{utilized_capacity:.1f} "
                                                f"hrs of {total_capacity} hrs"
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
            html.Div(
                [
                    html.H6("Recent Trend", className="mt-3"),
                    html.Div(
                        [
                            html.Span("Trend: ", className="text-muted"),
                            html.Span(
                                f"{recent_trend_percentage:.1f}% ",
                                className=(
                                    "text-success"
                                    if recent_trend_percentage <= 0
                                    else "text-danger"
                                ),
                            ),
                            html.Span(
                                (
                                    "(decreasing)"
                                    if recent_trend_percentage <= 0
                                    else "(increasing)"
                                ),
                                className="text-muted",
                            ),
                        ]
                    ),
                ],
                className="mt-2",
                style={
                    "display": "block"
                    if "recent_trend_percentage" in capacity_metrics
                    else "none"
                },
            ),
        ]
    )


def register(app):

    @app.callback(
        Output("current-statistics", "data"),
        Input("current-statistics", "modified_timestamp"),
        prevent_initial_call=True,
    )
    def reload_statistics_from_database(timestamp):

        logger.info(
            "[Statistics] reload_statistics_from_database "
            f"triggered by timestamp={timestamp}"
        )

        try:
            active_profile = get_active_profile()
            if not active_profile:
                logger.info(
                    "[Statistics] No active profile, skipping statistics reload"
                )
                raise PreventUpdate

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
            Output("chart-cache", "data", allow_duplicate=True),
        ],
        [Input("statistics-table", "data")],
        [
            State("app-init-complete", "data"),
            State("current-statistics", "data"),
        ],
        prevent_initial_call=True,
    )
    def save_statistics_on_edit(table_data, init_complete, current_statistics):

        logger.info(
            f"[Statistics] save_statistics_on_edit triggered: "
            "table_data="
            f"{'None' if table_data is None else f'{len(table_data)} rows'}, "
            f"init_complete={init_complete}"
        )

        if not table_data:
            logger.warning("[Statistics] PREVENTING save - table_data is empty")
            raise PreventUpdate

        if current_statistics and len(table_data) == len(current_statistics):
            if len(table_data) > 0:
                first_table = table_data[0]
                first_current = current_statistics[0]
                last_table = table_data[-1]
                last_current = current_statistics[-1]

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
                        "[Statistics] PREVENTING save - table_data "
                        "matches current_statistics "
                        "(tab re-render, not user edit)"
                    )
                    raise PreventUpdate

        if not table_data:
            logger.warning("[Statistics] PREVENTING save - table_data is empty")
            raise PreventUpdate

        if len(table_data) > 0:
            logger.info(
                f"[Statistics] Saving {len(table_data)} rows. "
                f"First: {table_data[0].get('date', 'NO_DATE')}, "
                f"Last: {table_data[-1].get('date', 'NO_DATE')}"
            )

        try:
            save_statistics(table_data)
            logger.info(
                "[Statistics] Table edited and saved "
                f"SUCCESSFULLY to DB: {len(table_data)} rows"
            )
        except Exception as e:
            logger.error(
                f"[Statistics] FAILED to save statistics to DB: {e}",
                exc_info=True,
            )

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

        if not n_clicks or not current_data:
            raise PreventUpdate

        try:
            date_objects = [
                datetime.strptime(row["date"], "%Y-%m-%d")
                for row in current_data
                if row.get("date") and len(row.get("date", "")) == 10
            ]
            if date_objects:
                most_recent_date = max(date_objects)
                new_date = (most_recent_date + timedelta(days=7)).strftime("%Y-%m-%d")

                today = datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                proposed_date = datetime.strptime(new_date, "%Y-%m-%d")
                if proposed_date > today:
                    logger.warning(
                        "Cannot add row for future date "
                        f"{new_date} (beyond today "
                        f"{today.strftime('%Y-%m-%d')}). "
                        "Statistics are historical data only."
                    )
                    raise PreventUpdate
            else:
                new_date = datetime.now().strftime("%Y-%m-%d")
        except ValueError, KeyError:
            new_date = datetime.now().strftime("%Y-%m-%d")

        try:
            date_obj = datetime.strptime(new_date, "%Y-%m-%d")
            week_label = get_week_label(date_obj)
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not calculate week_label for {new_date}: {e}")
            week_label = ""

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

    @app.callback(
        Output("column-explanations-collapse", "is_open"),
        [Input("column-explanations-toggle", "n_clicks")],
        [State("column-explanations-collapse", "is_open")],
    )
    def toggle_column_explanations(n_clicks, is_open):
        if n_clicks:
            return not is_open
        return is_open
