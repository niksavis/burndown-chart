"""
Statistics Callbacks Module

This module handles callbacks related to statistics data management.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import io
import json
import base64
from datetime import datetime, timedelta

# Third-party library imports
import dash
from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import pandas as pd
import dash_bootstrap_components as dbc

# Application imports
from configuration import logger
from data import save_statistics, save_statistics_from_csv_import, read_and_clean_data

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
        [
            Output("current-statistics", "data"),
            Output("current-statistics", "modified_timestamp"),
        ],
        [Input("statistics-table", "data")],
        [State("app-init-complete", "data")],
    )
    def update_and_save_statistics(data, init_complete):
        """
        Update current statistics and save to disk when changed.
        """
        ctx = dash.callback_context

        # Skip if not initialized or no data
        if not init_complete or not ctx.triggered or not data:
            raise PreventUpdate

        # Save to disk
        save_statistics(data)
        logger.info("Statistics updated and saved")
        return data, int(datetime.now().timestamp() * 1000)

    @app.callback(
        [
            Output("statistics-table", "data"),
            Output("is-sample-data", "data"),
            Output("upload-data", "contents", allow_duplicate=True),
        ],
        [
            Input("add-row-button", "n_clicks"),
            Input("upload-data", "contents"),
            Input("statistics-table", "data_timestamp"),
        ],
        [
            State("statistics-table", "data"),
            State("upload-data", "filename"),
            State("is-sample-data", "data"),
        ],
        prevent_initial_call=True,
    )
    def update_table(
        n_clicks,
        contents,
        data_timestamp,
        rows,
        filename,
        is_sample_data,
    ):
        """
        Update the statistics table data when:
        - A row is added
        - Data is uploaded
        - Cell values are edited (and need empty values converted to zeros)
        Also update the sample data flag when real data is uploaded.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            # No triggers, return unchanged
            return rows, is_sample_data, no_update

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        trigger_prop = (
            ctx.triggered[0]["prop_id"].split(".")[1]
            if "." in ctx.triggered[0]["prop_id"]
            else None
        )

        try:
            # Always clean numeric values first to prevent errors
            if rows:
                for row in rows:
                    numeric_columns = [
                        "completed_items",
                        "completed_points",
                        "created_items",
                        "created_points",
                    ]
                    for col in numeric_columns:
                        if col in row:
                            if row[col] == "" or row[col] is None:
                                row[col] = 0
                            else:
                                try:
                                    row[col] = int(float(row[col]))
                                except (ValueError, TypeError):
                                    row[col] = 0

            # Add a new row with a smart date calculation
            if trigger_id == "add-row-button":
                if not rows:
                    # If no existing rows, use today's date
                    new_date = datetime.now().strftime("%Y-%m-%d")
                else:
                    # Find the most recent date
                    try:
                        date_objects = [
                            datetime.strptime(row["date"], "%Y-%m-%d")
                            for row in rows
                            if row["date"] and len(row["date"]) == 10
                        ]
                        if date_objects:
                            most_recent_date = max(date_objects)
                            # Set new date to 7 days after the most recent
                            new_date = (most_recent_date + timedelta(days=7)).strftime(
                                "%Y-%m-%d"
                            )
                        else:
                            new_date = datetime.now().strftime("%Y-%m-%d")
                    except ValueError:
                        # Handle any date parsing errors
                        new_date = datetime.now().strftime("%Y-%m-%d")

                # Insert at beginning (will be at top with desc sorting)
                rows.insert(
                    0,
                    {
                        "date": new_date,
                        "completed_items": 0,
                        "completed_points": 0,
                        "created_items": 0,
                        "created_points": 0,
                    },
                )

                # If user adds a row, we're no longer using sample data
                if is_sample_data:
                    return rows, False, no_update
                else:
                    return rows, is_sample_data, no_update

            elif trigger_id == "upload-data" and contents:
                # Parse uploaded file
                content_type, content_string = contents.split(",")
                decoded = base64.b64decode(content_string)
                if "csv" in filename.lower():
                    try:
                        # Try semicolon separator first
                        df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), sep=";")
                        if (
                            "date" not in df.columns
                            or "completed_items" not in df.columns
                            or "completed_points" not in df.columns
                        ):
                            # Try with comma separator
                            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

                        # Clean data and ensure date is in YYYY-MM-DD format
                        df = read_and_clean_data(df)

                        # Ensure created_items and created_points columns exist
                        if "created_items" not in df.columns:
                            df["created_items"] = 0
                        if "created_points" not in df.columns:
                            df["created_points"] = 0

                        # Convert empty strings to zeros for all numeric columns
                        numeric_columns = [
                            "completed_items",
                            "completed_points",
                            "created_items",
                            "created_points",
                        ]
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = (
                                    pd.to_numeric(df[col], errors="coerce")
                                    .fillna(0)
                                    .astype(int)
                                )

                        # Save CSV data directly with correct metadata
                        save_statistics_from_csv_import(df.to_dict("records"))

                        # When uploading data, we're no longer using sample data
                        # Clear the upload contents to allow consecutive uploads of the same file
                        return df.to_dict("records"), False, None
                    except Exception as e:
                        logger.error(f"Error loading CSV file: {e}")
                        # Return unchanged data if there's an error
                        return rows, is_sample_data, no_update

                elif "json" in filename.lower():
                    try:
                        # Parse JSON file
                        json_data = json.loads(decoded.decode("utf-8"))

                        # Check if this is a full project data structure (exported JSON)
                        if isinstance(json_data, dict) and "statistics" in json_data:
                            # This is a full project data export - handle it specially
                            from data.persistence import save_unified_project_data

                            # Save the full project data
                            save_unified_project_data(json_data)
                            logger.info(f"Imported full project data from {filename}")

                            # Extract statistics for the table
                            statistics_data = json_data.get("statistics", [])
                            df = pd.DataFrame(statistics_data)
                        else:
                            # This is just statistics data (legacy format)
                            df = pd.DataFrame(json_data)

                        # Validate required columns for statistics
                        required_columns = [
                            "date",
                            "completed_items",
                            "completed_points",
                        ]

                        if df.empty:
                            logger.error("JSON file contains no statistics data")
                            return rows, is_sample_data, no_update

                        missing_columns = [
                            col for col in required_columns if col not in df.columns
                        ]

                        if missing_columns:
                            logger.error(
                                f"JSON file missing required columns: {missing_columns}"
                            )
                            return rows, is_sample_data, no_update

                        # Clean data and ensure date is in YYYY-MM-DD format
                        df = read_and_clean_data(df)

                        # Ensure created_items and created_points columns exist
                        if "created_items" not in df.columns:
                            df["created_items"] = 0
                        if "created_points" not in df.columns:
                            df["created_points"] = 0

                        # Convert empty strings to zeros for all numeric columns
                        numeric_columns = [
                            "completed_items",
                            "completed_points",
                            "created_items",
                            "created_points",
                        ]
                        for col in numeric_columns:
                            if col in df.columns:
                                df[col] = (
                                    pd.to_numeric(df[col], errors="coerce")
                                    .fillna(0)
                                    .astype(int)
                                )

                        # Check if this was a full project data import to trigger reload
                        full_project_imported = (
                            isinstance(json_data, dict) and "statistics" in json_data
                        )

                        # When uploading JSON data, we're no longer using sample data
                        # Note: Full project data import now handled by saving directly to disk
                        # No need for reload trigger - page refresh will pick up changes

                        # Log success message for full project import
                        if full_project_imported:
                            logger.info(
                                "Full project data imported successfully. Statistics table updated. Page refresh recommended to update all charts and project scope metrics."
                            )

                        # Clear the upload contents to allow consecutive uploads of the same file
                        return df.to_dict("records"), False, None
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON file: {e}")
                        return rows, is_sample_data, no_update
                    except Exception as e:
                        logger.error(f"Error loading JSON file: {e}")
                        return rows, is_sample_data, no_update

                else:
                    logger.error(
                        f"Unsupported file type: {filename}. Please upload a CSV or JSON file."
                    )
                    return rows, is_sample_data, no_update

            elif trigger_id == "statistics-table" and trigger_prop == "data_timestamp":
                # This is triggered when a cell is edited and loses focus
                # We've already cleaned the data at the start of this callback
                return rows, is_sample_data, no_update

        except Exception as e:
            logger.error(f"Error in update_table callback: {e}")

        return rows, is_sample_data, no_update

    @app.callback(
        Output("statistics-table", "filter_query"),
        [Input("clear-filters-button", "n_clicks")],
        prevent_initial_call=True,
    )
    def clear_table_filters(n_clicks):
        """
        Clear all filters from the statistics table when the clear filters button is clicked.

        Args:
            n_clicks: Number of times the clear-filters button has been clicked

        Returns:
            Empty string to clear all filters
        """
        if n_clicks:
            # Return empty string to clear all filters from the table
            return ""

        # This should not be reached due to prevent_initial_call=True
        raise PreventUpdate

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
