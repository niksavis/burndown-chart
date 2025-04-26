"""
UI components for displaying scope creep metrics.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from ui.components import TREND_ICONS, TREND_COLORS


def create_scope_creep_indicator(title, value, threshold=15, tooltip=None):
    """
    Create a scope creep indicator that matches the styling of trend indicators.

    Args:
        title: Title of the scope creep metric
        value: Percentage value of scope creep
        threshold: Threshold percentage for determining status color
        tooltip: Optional tooltip text

    Returns:
        html.Div: A scope creep indicator component
    """
    # Generate a unique ID for the indicator based on the title (for tooltip target)
    indicator_id = f"scope-indicator-{title.lower().replace(' ', '-')}"

    # Determine status direction, color, and icon based on threshold
    if value is None or pd.isna(value):
        direction = "stable"
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
        value_text = "N/A"
    else:
        if value > threshold:
            direction = "up"  # High scope creep is represented as "up" (negative)
            icon_class = TREND_ICONS["up"]
            text_color = TREND_COLORS[
                "down"
            ]  # Use "down" color (red) to indicate problem
            bg_color = "rgba(220, 53, 69, 0.1)"  # Light red background
            border_color = "rgba(220, 53, 69, 0.2)"
            value_text = f"{value}%"
        elif value > threshold * 0.8:  # Within 80% of threshold
            direction = "up"  # Medium scope creep still "up"
            icon_class = TREND_ICONS["up"]
            text_color = "#fd7e14"  # Orange color for warning
            bg_color = "rgba(253, 126, 20, 0.1)"  # Light orange background
            border_color = "rgba(253, 126, 20, 0.2)"
            value_text = f"{value}%"
        else:
            direction = "down"  # Low scope creep is represented as "down" (positive)
            icon_class = TREND_ICONS["down"]
            text_color = TREND_COLORS["up"]  # Use "up" color (green) to indicate good
            bg_color = "rgba(40, 167, 69, 0.1)"  # Light green background
            border_color = "rgba(40, 167, 69, 0.2)"
            value_text = f"{value}%"

    # Extract metric name (Items or Points) from title
    metric_name = "Items" if "Items" in title else "Points"

    # Create the compact trend-style indicator
    indicator = html.Div(
        className="compact-trend-indicator d-flex align-items-center p-2 rounded mb-3",
        style={
            "backgroundColor": bg_color,
            "border": f"1px solid {border_color}",
            "maxWidth": "100%",
        },
        id=indicator_id,
        children=[
            # Icon with circle background
            html.Div(
                className="trend-icon me-3 d-flex align-items-center justify-content-center rounded-circle",
                style={
                    "width": "36px",
                    "height": "36px",
                    "backgroundColor": "white",
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                    "flexShrink": 0,
                },
                children=html.I(
                    className=f"{icon_class}",
                    style={"color": text_color, "fontSize": "1rem"},
                ),
            ),
            # Scope Creep information
            html.Div(
                className="trend-info",
                style={"flexGrow": 1, "minWidth": 0},
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Span(
                                f"{metric_name} Scope Creep",
                                className="fw-medium",
                                style={"fontSize": "0.9rem"},
                            ),
                            html.Span(
                                value_text,
                                style={
                                    "color": text_color,
                                    "fontWeight": "500",
                                    "fontSize": "0.9rem",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline mt-1",
                        style={"fontSize": "0.8rem", "color": "#6c757d"},
                        children=[
                            html.Span(
                                f"Threshold: {threshold}%",
                            ),
                            html.Span(
                                f"Status: {'High Risk' if value > threshold else 'Warning' if value > threshold * 0.8 else 'Healthy'}"
                                if value is not None and not pd.isna(value)
                                else "Unknown",
                                style={"color": text_color},
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    # Create components list to return - starting with the indicator
    components = [indicator]

    # Add tooltip if provided
    if tooltip:
        components.append(
            dbc.Tooltip(
                tooltip,
                target=indicator_id,
                className="tooltip-custom",
            )
        )

    # Return all components wrapped in a div
    return html.Div(components, className="mb-3")


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

    # Create traces with improved colors matching the trend visuals
    items_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["items_growth"],
        name="Items Growth",
        marker_color="rgba(32, 201, 151, 0.7)",  # Green color matching items trend
        # Add hover text to clarify meaning of values
        hovertemplate=(
            "<b>Items</b><br>"
            + "Week: %{x}<br>"
            + "Growth: %{y}<br>"
            + "<i>Positive = Scope Increase<br>"
            + "Negative = Backlog Reduction</i>"
        ),
    )

    points_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["points_growth"],
        name="Points Growth",
        marker_color="rgba(253, 126, 20, 0.7)",  # Orange color matching points trend
        # Add hover text to clarify meaning of values
        hovertemplate=(
            "<b>Points</b><br>"
            + "Week: %{x}<br>"
            + "Growth: %{y}<br>"
            + "<i>Positive = Scope Increase<br>"
            + "Negative = Backlog Reduction</i>"
        ),
    )

    # Create layout with improved styling
    layout = go.Layout(
        title="Weekly Scope Growth (+ Increase, - Reduction)",  # Updated title to clarify meaning
        xaxis={
            "title": "Week",
            "tickangle": -45,
            "gridcolor": "rgba(200, 200, 200, 0.2)",
        },
        yaxis={
            "title": "Growth (Created - Completed)",
            "gridcolor": "rgba(200, 200, 200, 0.2)",
            "zeroline": True,
            "zerolinecolor": "rgba(0, 0, 0, 0.2)",
        },
        height=300,
        margin={"l": 60, "r": 20, "t": 50, "b": 80},
        legend={"orientation": "h", "y": -0.2, "xanchor": "center", "x": 0.5},
        hovermode="x unified",
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

    # Add annotation explaining the chart
    figure.add_annotation(
        x=0.5,
        y=-0.25,
        xref="paper",
        yref="paper",
        text=(
            "<b>Growth Interpretation:</b> "
            "Positive values indicate added scope, "
            "negative values indicate backlog reduction."
        ),
        showarrow=False,
        font=dict(size=12),
        align="center",
        bordercolor="rgba(200, 200, 200, 0.5)",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(250, 250, 250, 0.8)",
    )

    # Return the graph component
    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
    )


def create_enhanced_stability_gauge(
    stability_value, title="Scope Stability Index", height=280
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

    # Create gauge with improved layout - gauge in top section, text below
    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",  # Only gauge and number
            value=stability_value,
            domain={"x": [0, 1], "y": [0.15, 0.85]},  # Adjusted to center the gauge
            title={
                "text": f"<b>{title}</b>",
                "font": {"size": 18},
                "align": "center",
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
                "font": {"size": 24, "color": color},
                "valueformat": ".2f",
                "suffix": "",  # No suffix to avoid overlap
            },
        )
    )

    # Add status text annotation BELOW the gauge (not overlapping)
    figure.add_annotation(
        text=f"<b>Status: {status_text}</b>",
        x=0.5,
        y=0.02,  # Position at the bottom
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=15, color=color),
        align="center",
    )

    # Add reference line annotation (adjusted position)
    figure.add_annotation(
        text="Reference: 0.7",
        x=0.85,
        y=0.1,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=10, color="gray"),
        align="right",
    )

    # Add reference line
    figure.add_shape(
        type="line",
        x0=0.7,
        x1=0.7,
        y0=0.15,
        y1=0.85,
        xref="x",
        yref="paper",
        line=dict(color="gray", width=1, dash="dot"),
    )

    # Update layout with more appropriate margins
    figure.update_layout(
        height=height,  # Increased height to accommodate the status text below
        margin={"l": 30, "r": 30, "t": 40, "b": 60},  # Increased bottom margin
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
            # Scope Creep Rate Indicators in cards with matching style
            html.Div(
                [
                    # Items trend box - with similar styling to Weekly Items Trend
                    html.Div(
                        [
                            create_scope_creep_indicator(
                                "Items Scope Creep Rate",
                                scope_creep_rate["items_rate"],
                                threshold,
                                "Percentage of new items created compared to original baseline",
                            )
                        ],
                        className="col-md-6 col-12 mb-3 pe-md-2",
                    ),
                    # Points trend box - with similar styling to Weekly Points Trend
                    html.Div(
                        [
                            create_scope_creep_indicator(
                                "Points Scope Creep Rate",
                                scope_creep_rate["points_rate"],
                                threshold,
                                "Percentage of new points created compared to original baseline",
                            )
                        ],
                        className="col-md-6 col-12 mb-3 ps-md-2",
                    ),
                ],
                className="row g-0 mb-2",  # g-0 removes gutters
            ),
            html.Div(
                html.P(
                    "This analysis tracks how project scope changes over time. Scope creep measures growth beyond the initial baseline. Negative values indicate scope reduction.",
                    className="text-muted mb-4",
                ),
            ),
            # Alert for threshold breach
            create_scope_creep_alert(alert_data),
            # Section header for Growth Analysis
            html.H5(
                [
                    html.I(
                        className="fas fa-chart-bar me-2", style={"color": "#20c997"}
                    ),
                    "Weekly Scope Growth Analysis",
                ],
                className="mt-4 mb-3 border-bottom pb-2 d-flex align-items-center",
            ),
            # Weekly Scope Growth Chart in a card to match other components
            html.Div(
                [
                    html.Div(
                        create_scope_growth_chart(weekly_growth_data),
                        className="p-2",
                    ),
                ],
                className="border rounded mb-4 chart-container",
                style={"boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px"},
            ),
            # Section header for Stability Metrics
            html.H5(
                [
                    html.I(
                        className="fas fa-tachometer-alt me-2",
                        style={"color": "#fd7e14"},
                    ),
                    "Scope Stability Metrics",
                ],
                className="mt-4 mb-3 border-bottom pb-2 d-flex align-items-center",
            ),
            # Brief description of stability index
            html.Div(
                html.P(
                    [
                        "The Stability Index measures how consistent scope has remained over time. ",
                        html.Strong("Higher values (closer to 1.0)"),
                        " indicate more stable scope with fewer changes.",
                    ],
                    className="text-muted mb-3",
                ),
            ),
            # Stability Gauges in cards to match other components
            dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            create_enhanced_stability_gauge(
                                stability_index["items_stability"],
                                "Items Stability Index",
                            ),
                            className="border rounded p-2",
                            style={"boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px"},
                        ),
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                    dbc.Col(
                        html.Div(
                            create_enhanced_stability_gauge(
                                stability_index["points_stability"],
                                "Points Stability Index",
                            ),
                            className="border rounded p-2",
                            style={"boxShadow": "rgba(0, 0, 0, 0.05) 0px 1px 2px 0px"},
                        ),
                        width=12,
                        md=6,
                        className="mb-3",
                    ),
                ],
                className="g-3",  # Small gutters between columns
            ),
        ],
        className="scope-metrics-dashboard",
    )
