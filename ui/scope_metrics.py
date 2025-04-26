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
                                style={
                                    "color": text_color
                                    if value is not None and not pd.isna(value)
                                    else "inherit"
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    # Add tooltip if provided
    if tooltip:
        return html.Div(
            [
                indicator,
                dbc.Tooltip(
                    tooltip,
                    target=indicator_id,
                    className="tooltip-custom",
                ),
            ]
        )

    return indicator


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
        marker_color="rgba(0, 123, 255, 0.7)",  # Changed from green to blue
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
        marker_color="rgba(253, 126, 20, 0.7)",  # Keep orange color for points
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
        margin={"l": 60, "r": 20, "t": 70, "b": 60},  # Increased top margin for legend
        legend={
            "orientation": "h",
            "y": 1.25,
            "xanchor": "center",
            "x": 0.95,
        },  # Moved legend to top
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

    # Return the graph component - note that we removed the explanatory annotation
    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
    )


def create_enhanced_stability_gauge(
    stability_value,
    title="Scope Stability Index",
    height=300,  # Increased height from 280 to 300
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
            domain={
                "x": [0, 1],
                "y": [0.25, 0.85],
            },  # Adjusted to move the gauge up slightly
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
                    "visible": False,  # Hide the axis and ticks
                },
                "bar": {"color": color, "thickness": 0.7},
                "bgcolor": "white",
                "borderwidth": 0,  # Remove border to eliminate coordinate system appearance
                "steps": [
                    {"range": [0, 0.2], "color": "rgba(220, 0, 0, 0.2)"},
                    {"range": [0.2, 0.4], "color": "rgba(230, 120, 0, 0.2)"},
                    {"range": [0.4, 0.6], "color": "rgba(240, 180, 0, 0.2)"},
                    {"range": [0.6, 0.8], "color": "rgba(150, 200, 50, 0.2)"},
                    {"range": [0.8, 1], "color": "rgba(0, 180, 0, 0.2)"},
                ],
                "threshold": {
                    "line": {"color": "black", "width": 2},
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

    # Add status text annotation BELOW the gauge (moved lower)
    figure.add_annotation(
        text=f"<b>Status: {status_text}</b>",
        x=0.5,
        y=0,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=15, color=color),
        align="center",
    )

    # Add reference line annotation (adjusted position)
    figure.add_annotation(
        text="Target: 0.7+",
        x=0.5,
        y=0.15,  # Moved down slightly (was 0.1)
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
        y0=0.25,  # Adjusted to match new domain y0
        y1=0.85,  # Adjusted to match new domain y1
        xref="x",
        yref="paper",
        line=dict(color="gray", width=1, dash="dot"),
    )

    # Update layout with more appropriate margins and hide axes
    figure.update_layout(
        height=height,
        margin={
            "l": 30,
            "r": 30,
            "t": 40,
            "b": 75,
        },  # Increased bottom margin from 60 to 75
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False, "showgrid": False, "zeroline": False},
        yaxis={"visible": False, "showgrid": False, "zeroline": False},
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


def create_forecast_pill(label, value, color):
    """
    Create a forecast pill component.

    Args:
        label: The label for the pill
        value: The value to display
        color: The color for the pill indicator

    Returns:
        html.Div: A forecast pill component
    """
    return html.Div(
        className="forecast-pill",
        style={
            "borderLeft": f"3px solid {color}",
            "paddingLeft": "0.5rem",
            "marginRight": "0.75rem",
        },
        children=[
            html.I(className="fas fa-chart-line me-1", style={"color": color}),
            html.Small([f"{label}: ", html.Strong(f"{value}", style={"color": color})]),
        ],
    )


def create_scope_metrics_header(title, icon, color):
    """
    Create a header for scope metrics similar to trend headers.

    Args:
        title: The title to display
        icon: The icon class
        color: The color for the icon

    Returns:
        html.Div: A header component
    """
    return html.Div(
        className="d-flex align-items-center mb-2",
        children=[
            html.I(className=f"{icon} me-2", style={"color": color}),
            html.Span(title, className="fw-medium"),
        ],
    )


def create_scope_metrics_dashboard(
    scope_creep_rate,
    weekly_growth_data,
    stability_index,
    threshold=15,
    total_items_scope=None,
    total_points_scope=None,  # Add parameters for total scope
):
    """
    Create a dashboard component displaying all scope metrics.

    Args:
        scope_creep_rate (dict): Dictionary containing items_rate and points_rate percentages
        weekly_growth_data (DataFrame): DataFrame containing weekly growth data
        stability_index (dict): Dictionary containing items_stability and points_stability values
        threshold (int): Threshold percentage for scope creep warnings
        total_items_scope (int, optional): Total items scope (completed + remaining)
        total_points_scope (int, optional): Total points scope (completed + remaining)

    Returns:
        html.Div: A dashboard component with scope metrics
    """
    # Read remaining items directly from forecast settings
    import json

    try:
        with open("forecast_settings.json", "r") as f:
            settings = json.load(f)
            remaining_items = settings.get(
                "total_items", 34
            )  # Default to 34 if not found
            remaining_points = settings.get(
                "total_points", 154
            )  # Default to 154 if not found
    except:
        # If we can't read the file, use defaults
        remaining_items = 34
        remaining_points = 154

    # Get total created and completed items/points from the full dataset
    import pandas as pd

    try:
        df = pd.read_csv("forecast_statistics.csv")
        total_completed_items = (
            df["completed_items"].sum() if "completed_items" in df.columns else 0
        )
        total_completed_points = (
            df["completed_points"].sum() if "completed_points" in df.columns else 0
        )
        total_created_items = (
            df["created_items"].sum() if "created_items" in df.columns else 0
        )
        total_created_points = (
            df["created_points"].sum() if "created_points" in df.columns else 0
        )
    except:
        # If we can't read the file, use the data from weekly_growth_data
        total_completed_items = 0
        total_completed_points = 0
        total_created_items = 0
        total_created_points = 0

        if not weekly_growth_data.empty:
            # Try to get sums from weekly_growth_data
            if "completed_items" in weekly_growth_data.columns:
                total_completed_items = weekly_growth_data["completed_items"].sum()
                total_completed_points = (
                    weekly_growth_data["completed_points"].sum()
                    if "completed_points" in weekly_growth_data.columns
                    else 0
                )

            if "created_items" in weekly_growth_data.columns:
                total_created_items = weekly_growth_data["created_items"].sum()
                total_created_points = (
                    weekly_growth_data["created_points"].sum()
                    if "created_points" in weekly_growth_data.columns
                    else 0
                )

    # Calculate baselines using the provided total scope if available
    if total_items_scope is not None:
        baseline_items = total_items_scope  # Use the provided total scope
    else:
        # Fall back to the old calculation (remaining + completed = baseline)
        baseline_items = remaining_items + total_completed_items

    if total_points_scope is not None:
        baseline_points = total_points_scope  # Use the provided total scope
    else:
        # Fall back to the old calculation (remaining + completed = baseline)
        baseline_points = remaining_points + total_completed_points

    # Calculate threshold in absolute values - how many items/points can be added
    # before exceeding the threshold percentage
    threshold_items = round(baseline_items * threshold / 100)
    threshold_points = round(baseline_points * threshold / 100)

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
            # Scope Creep Rate Indicators with improved layout
            html.Div(
                [
                    # Items trend box - with similar styling to Weekly Items Trend
                    html.Div(
                        [
                            # Header with icon
                            create_scope_metrics_header(
                                "Items Scope Creep Metrics", "fas fa-tasks", "#20c997"
                            ),
                            # Scope creep indicator
                            create_scope_creep_indicator(
                                "Items Scope Creep Rate",
                                scope_creep_rate["items_rate"],
                                threshold,
                                "Percentage of new items created compared to original baseline",
                            ),
                            # Forecast pills for items scope creep - showing absolute values
                            html.Div(
                                [
                                    create_forecast_pill(
                                        "Current",
                                        f"{int(total_created_items)} items",
                                        "#20c997",
                                    ),
                                    create_forecast_pill(
                                        "Threshold",
                                        f"{int(threshold_items)} items",
                                        "#dc3545",
                                    ),
                                    html.Div(
                                        html.Small(
                                            f"baseline: {int(baseline_items)} items",
                                            className="text-muted fst-italic",
                                        ),
                                        style={"paddingTop": "2px"},
                                    ),
                                ],
                                className="d-flex flex-wrap mt-2 align-items-center",
                                style={"gap": "0.25rem"},
                            ),
                        ],
                        className="col-md-6 col-12 mb-3 pe-md-2",
                    ),
                    # Points trend box - with similar styling to Weekly Points Trend
                    html.Div(
                        [
                            # Header with icon
                            create_scope_metrics_header(
                                "Points Scope Creep Metrics",
                                "fas fa-chart-bar",
                                "#fd7e14",
                            ),
                            # Scope creep indicator
                            create_scope_creep_indicator(
                                "Points Scope Creep Rate",
                                scope_creep_rate["points_rate"],
                                threshold,
                                "Percentage of new points created compared to original baseline",
                            ),
                            # Forecast pills for points scope creep - showing absolute values
                            html.Div(
                                [
                                    create_forecast_pill(
                                        "Current",
                                        f"{int(total_created_points)} points",
                                        "#fd7e14",
                                    ),
                                    create_forecast_pill(
                                        "Threshold",
                                        f"{int(threshold_points)} points",
                                        "#dc3545",
                                    ),
                                    html.Div(
                                        html.Small(
                                            f"baseline: {int(baseline_points)} points",
                                            className="text-muted fst-italic",
                                        ),
                                        style={"paddingTop": "2px"},
                                    ),
                                ],
                                className="d-flex flex-wrap mt-2 align-items-center",
                                style={"gap": "0.25rem"},
                            ),
                        ],
                        className="col-md-6 col-12 mb-3 ps-md-2",
                    ),
                ],
                className="row mb-3",
            ),
            # Alert for threshold breach
            create_scope_creep_alert(alert_data),
            # Weekly Scope Growth Chart
            html.Div([create_scope_growth_chart(weekly_growth_data)], className="mb-2"),
            # Footnote explaining growth interpretation with consistent styling and icon
            html.Div(
                className="text-muted fst-italic small text-center",
                children=[
                    html.I(
                        className="fas fa-info-circle me-1",
                        style={"color": "rgb(108, 117, 125)"},
                    ),
                    "Growth Interpretation: Positive values indicate added scope, negative values indicate backlog reduction.",
                ],
            ),
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
            # Footnote explaining stability index with consistent styling and icon
            html.Div(
                className="text-muted fst-italic small text-center",
                children=[
                    html.I(
                        className="fas fa-info-circle me-1",
                        style={"color": "rgb(108, 117, 125)"},
                    ),
                    "Stability Index: Higher values indicate more stable scope (fewer changes relative to total scope).",
                ],
            ),
        ]
    )
