"""
Visualization Callbacks Module

This module handles callbacks related to visualization updates and interactions.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Import from application modules
from configuration import logger
from data import compute_cumulative_values, calculate_weekly_averages
from visualization import create_forecast_plot
from ui import create_pert_info_table

#######################################################################
# CALLBACKS
#######################################################################


def register(app):
    """
    Register all visualization-related callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        Output("app-init-complete", "data"), [Input("forecast-graph", "figure")]
    )
    def mark_initialization_complete(figure):
        """
        Mark the application as fully initialized after the graph is rendered.
        This prevents saving during initial load and avoids triggering callbacks prematurely.
        """
        return True

    @app.callback(
        [Output("forecast-graph", "figure"), Output("pert-info-container", "children")],
        [
            Input("current-settings", "modified_timestamp"),
            Input("current-statistics", "modified_timestamp"),
            Input("calculation-results", "data"),
        ],
        [State("current-settings", "data"), State("current-statistics", "data")],
    )
    def update_graph_and_pert_info(
        settings_ts, statistics_ts, calc_results, settings, statistics
    ):
        """
        Update the forecast graph and PERT analysis when settings or statistics change.
        """
        if not settings or not statistics:
            raise PreventUpdate

        try:
            # Create dataframe from statistics data
            df = pd.DataFrame(statistics)

            # Get values from settings
            pert_factor = settings["pert_factor"]
            total_items = settings["total_items"]
            # Use calculated total points from calc_results if available
            total_points = calc_results.get("total_points", settings["total_points"])
            deadline = settings["deadline"]

            # Process data for calculations
            if not df.empty:
                df = compute_cumulative_values(df, total_items, total_points)

            # Create forecast plot and get PERT values
            fig, pert_time_items, pert_time_points = create_forecast_plot(
                df=df,
                total_items=total_items,
                total_points=total_points,
                pert_factor=pert_factor,
                deadline_str=deadline,
            )

            # Calculate days to deadline
            deadline_date = pd.to_datetime(deadline)
            current_date = datetime.now()
            days_to_deadline = max(0, (deadline_date - current_date).days)

            # Calculate average and median weekly metrics
            avg_weekly_items, avg_weekly_points, med_weekly_items, med_weekly_points = (
                calculate_weekly_averages(statistics)
            )

            # Create PERT info component
            pert_info = create_pert_info_table(
                pert_time_items,
                pert_time_points,
                days_to_deadline,
                avg_weekly_items,
                avg_weekly_points,
                med_weekly_items,
                med_weekly_points,
                pert_factor,
            )

            return fig, pert_info
        except Exception as e:
            logger.error(f"Error in update_graph_and_pert_info callback: {e}")
            # Return empty figure and error message on failure
            fig = go.Figure()
            fig.add_annotation(
                text=f"Error generating forecast: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=16, color="red"),
            )
            error_info = html.Div(
                [html.P("Error calculating PERT values", style={"color": "red"})]
            )
            return fig, error_info

    @app.callback(
        Output("help-modal", "is_open"),
        [Input("help-button", "n_clicks"), Input("close-help", "n_clicks")],
        [State("help-modal", "is_open")],
    )
    def toggle_help_modal(n1, n2, is_open):
        """
        Toggle the help modal visibility.
        """
        if n1 or n2:
            return not is_open
        return is_open
