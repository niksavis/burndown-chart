"""
UI components for displaying scope creep metrics.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np


def create_scope_creep_indicator(title, value, threshold=15, tooltip=None):
    """Create an indicator for scope creep metrics."""
    # Generate a unique ID for the indicator based on the title (for tooltip target)
    indicator_id = f"scope-indicator-{title.lower().replace(' ', '-')}"

    # Determine status color based on threshold
    if value is None or pd.isna(value):
        color = "secondary"
        value_text = "N/A"
    else:
        if value > threshold:
            color = "danger"
        elif value > threshold * 0.8:  # Within 80% of threshold
            color = "warning"
        else:
            color = "success"
        value_text = f"{value}%"

    # Create the indicator component with the unique ID
    indicator = html.Div(
        [
            html.H6(title, className="mb-0 text-muted"),
            html.Div(
                [
                    html.Span(value_text, className=f"fw-bold text-{color}"),
                ],
                className="d-flex align-items-center",
            ),
        ],
        className="mb-3",
        id=indicator_id,  # Add a unique ID to the div
    )

    # Create components list to return - starting with the indicator
    components = [indicator]

    # Add tooltip if provided
    if tooltip:
        components.append(
            dbc.Tooltip(
                tooltip,
                target=indicator_id,  # Reference the ID of the indicator
                className="tooltip-custom",
            )
        )

    # Return all components wrapped in a fragment-style div
    return html.Div(components, style={"display": "contents"})


def create_scope_growth_chart(weekly_growth_data):
    """Create a bar chart showing weekly scope growth."""
    if weekly_growth_data.empty:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": go.Layout(
                    title="Weekly Scope Growth",
                    xaxis={"title": "Week"},
                    yaxis={"title": "Growth"},
                    height=300,
                ),
            },
            config={"displayModeBar": False, "responsive": True},
        )

    # Create traces
    items_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["items_growth"],
        name="Items Growth",
        marker_color="rgba(50, 171, 96, 0.7)",
    )

    points_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["points_growth"],
        name="Points Growth",
        marker_color="rgba(219, 64, 82, 0.7)",
    )

    # Create layout
    layout = go.Layout(
        title="Weekly Scope Growth",
        xaxis={"title": "Week", "tickangle": -45},
        yaxis={"title": "Growth (Created - Completed)"},
        height=300,
        margin={"l": 60, "r": 20, "t": 50, "b": 80},
        legend={"orientation": "h", "y": -0.2},
        hovermode="x",
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
    )

    # Create figure
    figure = go.Figure(data=[items_trace, points_trace], layout=layout)

    # Add a reference line at y=0
    figure.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=0,
        y1=0,
        line=dict(color="black", width=1, dash="dot"),
    )

    # Return the graph component
    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
    )


def create_enhanced_stability_gauge(
    stability_value, title="Scope Stability Index", height=250
):
    """
    Create an enhanced gauge visualization for the scope stability index with better visual indicators.

    Args:
        stability_value (float): A value between 0 and 1 representing stability
        title (str): Title displayed above the gauge
        height (int): Height of the gauge in pixels

    Returns:
        dcc.Graph: A Dash graph component with the gauge
    """
    # Define color scale based on stability value
    if stability_value > 0.8:
        color = "rgb(0, 180, 0)"  # Darker green for better visibility
        status_text = "Stable"
    elif stability_value > 0.6:
        color = "rgb(150, 200, 50)"  # Lime green
        status_text = "Moderately Stable"
    elif stability_value > 0.4:
        color = "rgb(240, 180, 0)"  # Amber/Orange
        status_text = "Moderately Unstable"
    elif stability_value > 0.2:
        color = "rgb(230, 120, 0)"  # Orange/Red
        status_text = "Unstable"
    else:
        color = "rgb(220, 0, 0)"  # Bright Red
        status_text = "Highly Unstable"

    # Create gauge
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=stability_value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": f"<b>{title}</b>", "font": {"size": 18}, "align": "center"},
            delta={
                "reference": 0.7,  # Reference value (good stability threshold)
                "increasing": {"color": "green"},
                "decreasing": {"color": "red"},
            },
            gauge={
                "axis": {
                    "range": [0, 1],
                    "tickwidth": 1,
                    "tickcolor": "darkgrey",
                    "tickmode": "array",
                    "tickvals": [0, 0.2, 0.4, 0.6, 0.8, 1],
                    "ticktext": ["0", "0.2", "0.4", "0.6", "0.8", "1"],
                },
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 0.2], "color": "rgba(220, 0, 0, 0.2)"},
                    {"range": [0.2, 0.4], "color": "rgba(230, 120, 0, 0.2)"},
                    {"range": [0.4, 0.6], "color": "rgba(240, 180, 0, 0.2)"},
                    {"range": [0.6, 0.8], "color": "rgba(150, 200, 50, 0.2)"},
                    {"range": [0.8, 1], "color": "rgba(0, 180, 0, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": stability_value,
                },
            },
            number={
                "font": {"size": 28, "color": color},
                "suffix": "",
                "valueformat": ".2f",
            },
        )
    )

    # Add status text annotation
    figure.add_annotation(
        text=f"<b>{status_text}</b>",
        x=0.5,
        y=0.18,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16, color=color),
    )

    # Update layout
    figure.update_layout(
        height=height,
        margin={"l": 30, "r": 30, "t": 50, "b": 30},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
    )


def create_scope_creep_alert(alert_data):
    """Create an alert component for scope creep warnings."""
    if alert_data["status"] == "ok":
        return html.Div()  # Return empty div if no alert

    return dbc.Alert(
        [html.I(className="fas fa-exclamation-triangle me-2"), alert_data["message"]],
        color="warning",
        className="mt-3",
        is_open=True,
    )


def create_scope_metrics_dashboard(
    scope_creep_rate, weekly_growth_data, stability_index, threshold=15
):
    """Create a dashboard component displaying all scope metrics."""
    # Check if scope creep exceeds threshold and create alert
    alert_data = {
        "status": "warning"
        if (
            scope_creep_rate["items_rate"] > threshold
            or scope_creep_rate["points_rate"] > threshold
        )
        else "ok",
        "message": "",
    }

    if alert_data["status"] == "warning":
        parts = []
        if scope_creep_rate["items_rate"] > threshold:
            parts.append(f"Items scope creep ({scope_creep_rate['items_rate']}%)")
        if scope_creep_rate["points_rate"] > threshold:
            parts.append(f"Points scope creep ({scope_creep_rate['points_rate']}%)")

        if parts:
            alert_data["message"] = (
                f"{' and '.join(parts)} exceed threshold ({threshold}%)."
            )

    return html.Div(
        [
            html.H5("Scope Creep Metrics", className="mb-4"),
            # Scope Creep Rate Indicators
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_scope_creep_indicator(
                                "Items Scope Creep Rate",
                                scope_creep_rate["items_rate"],
                                threshold,
                                "Percentage of new items created compared to original baseline",
                            )
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            create_scope_creep_indicator(
                                "Points Scope Creep Rate",
                                scope_creep_rate["points_rate"],
                                threshold,
                                "Percentage of new points created compared to original baseline",
                            )
                        ],
                        width=6,
                    ),
                ],
                className="mb-4",
            ),
            # Alert for threshold breach
            create_scope_creep_alert(alert_data),
            # Weekly Scope Growth Chart
            html.Div([create_scope_growth_chart(weekly_growth_data)], className="mb-4"),
            # Stability Gauges
            dbc.Row(
                [
                    dbc.Col(
                        [
                            create_enhanced_stability_gauge(
                                stability_index["items_stability"],
                                "Items Stability Index",
                            )
                        ],
                        width=12,
                        md=6,
                    ),
                    dbc.Col(
                        [
                            create_enhanced_stability_gauge(
                                stability_index["points_stability"],
                                "Points Stability Index",
                            )
                        ],
                        width=12,
                        md=6,
                    ),
                ]
            ),
            # Footnote explaining stability index
            html.Small(
                "Stability Index: Higher values indicate more stable scope (fewer changes relative to total scope).",
                className="text-muted mt-2",
            ),
        ]
    )
