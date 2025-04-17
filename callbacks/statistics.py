"""
Statistics Callbacks Module

This module handles callbacks related to statistics data management.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
from datetime import datetime, timedelta
import io
import base64

# Import from application modules
from configuration import logger
from data import save_statistics, read_and_clean_data

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
        [Output("statistics-table", "data"), Output("is-sample-data", "data")],
        [Input("add-row-button", "n_clicks"), Input("upload-data", "contents")],
        [
            State("statistics-table", "data"),
            State("upload-data", "filename"),
            State("is-sample-data", "data"),
        ],
    )
    def update_table(n_clicks, contents, rows, filename, is_sample_data):
        """
        Update the statistics table data when a row is added or data is uploaded.
        Also update the sample data flag when real data is uploaded.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            # No triggers, return unchanged
            return rows, is_sample_data

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        try:
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
                        "no_items": 0,
                        "no_points": 0,
                    },
                )

                # If user adds a row, we're no longer using sample data
                if is_sample_data:
                    return rows, False
                else:
                    return rows, is_sample_data

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
                            or "no_items" not in df.columns
                            or "no_points" not in df.columns
                        ):
                            # Try with comma separator
                            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

                        # Clean data and ensure date is in YYYY-MM-DD format
                        df = read_and_clean_data(df)
                        # When uploading data, we're no longer using sample data
                        return df.to_dict("records"), False
                    except Exception as e:
                        logger.error(f"Error loading CSV file: {e}")
                        # Return unchanged data if there's an error
                        return rows, is_sample_data
        except Exception as e:
            logger.error(f"Error in update_table callback: {e}")
        return rows, is_sample_data

    @app.callback(
        Output("sample-data-alert", "is_open"),
        [
            Input("dismiss-sample-alert", "n_clicks"),
            Input("is-sample-data", "data"),
            Input("upload-data", "contents"),
        ],
        [State("sample-data-alert", "is_open")],
    )
    def toggle_sample_data_alert(n_clicks, is_sample_data, upload_contents, is_open):
        """
        Show or hide the sample data alert banner.
        - Show when sample data is being used
        - Hide when dismissed or when real data is uploaded
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            # Initial load
            return is_sample_data

        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "dismiss-sample-alert" and n_clicks:
            # User dismissed the alert
            return False
        elif trigger_id == "upload-data" and upload_contents:
            # Data was uploaded, hide the alert
            return False
        elif trigger_id == "is-sample-data":
            # Sample data flag changed
            return is_sample_data

        # Default: maintain current state
        return is_open
