"""
Statistics Callbacks Module

This module handles callbacks related to statistics data management.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc

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
