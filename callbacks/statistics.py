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
from configuration.settings import logger
from data.persistence import save_statistics
from data.processing import read_and_clean_data

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
        Output("statistics-table", "data"),
        [Input("add-row-button", "n_clicks"), Input("upload-data", "contents")],
        [State("statistics-table", "data"), State("upload-data", "filename")],
    )
    def update_table(n_clicks, contents, rows, filename):
        """
        Update the statistics table data when a row is added or data is uploaded.
        """
        ctx = dash.callback_context
        if not ctx.triggered:
            # No triggers, return unchanged
            return rows

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
                return rows

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
                        return df.to_dict("records")
                    except Exception as e:
                        logger.error(f"Error loading CSV file: {e}")
                        # Return unchanged data if there's an error
                        return rows
        except Exception as e:
            logger.error(f"Error in update_table callback: {e}")
        return rows
