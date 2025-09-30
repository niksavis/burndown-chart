"""
UI components for displaying scope change metrics.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objs as go
import pandas as pd
from ui.components import TREND_ICONS, TREND_COLORS
from ui.tooltip_utils import create_info_tooltip
from configuration import SCOPE_HELP_TEXTS
from data.schema import DEFAULT_SETTINGS  # Import the DEFAULT_SETTINGS


def create_scope_change_indicator(
    title, value, threshold=None, tooltip=None, throughput_ratio=None
):
    """
    Create a scope change indicator that shows scope change rate with throughput ratio comparison.

    Args:
        title: Title of the scope change metric
        value: Percentage value of scope change
        threshold: Threshold percentage for determining status color
        tooltip: Optional tooltip text
        throughput_ratio: Optional ratio of created vs completed items/points

    Returns:
        html.Div: A scope change indicator component
    """
    # Use the threshold from DEFAULT_SETTINGS if not provided
    if threshold is None:
        threshold = DEFAULT_SETTINGS["scope_change_threshold"]

    # Generate a unique ID for the indicator based on the title (for tooltip target)
    indicator_id = f"scope-indicator-{title.lower().replace(' ', '-')}"

    # Extract metric name (Items or Points) from title
    metric_name = "Items" if "Items" in title else "Points"

    # Determine status based on value and throughput ratio
    high_throughput_ratio = throughput_ratio and throughput_ratio > 1

    # By default, scope changes are not considered negative
    # Only if changes are significant AND outpacing throughput, we show warning indicators
    if value is None or pd.isna(value):
        icon_class = TREND_ICONS["stable"]
        text_color = TREND_COLORS["stable"]
        bg_color = "rgba(108, 117, 125, 0.1)"
        border_color = "rgba(108, 117, 125, 0.2)"
        value_text = "N/A"
        status_text = "Unknown"
    elif value > threshold and high_throughput_ratio:
        # Only show warning if both threshold exceeded and throughput ratio > 1
        icon_class = TREND_ICONS["up"]
        text_color = TREND_COLORS["down"]  # Red to indicate potential concern
        bg_color = "rgba(220, 53, 69, 0.1)"  # Light red background
        border_color = "rgba(220, 53, 69, 0.2)"
        value_text = f"{value}%"
        status_text = "High Change"
    elif value > threshold * 0.8 and high_throughput_ratio:
        # Warning level - approaching threshold and throughput ratio > 1
        icon_class = TREND_ICONS["up"]
        text_color = "#fd7e14"  # Orange color for notice
        bg_color = "rgba(253, 126, 20, 0.1)"  # Light orange background
        border_color = "rgba(253, 126, 20, 0.2)"
        value_text = f"{value}%"
        status_text = "Moderate Change"
    else:
        # Normal - either below threshold or not outpacing throughput
        icon_class = TREND_ICONS["up" if value > 0 else "stable"]
        text_color = "#20c997"  # Teal color for neutral/information
        bg_color = "rgba(32, 201, 151, 0.1)"  # Light teal background
        border_color = "rgba(32, 201, 151, 0.2)"
        value_text = f"{value}%"
        status_text = "Normal Change"

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
            # Scope Change information
            html.Div(
                className="trend-info",
                style={"flexGrow": 1, "minWidth": 0},
                children=[
                    html.Div(
                        className="d-flex justify-content-between align-items-baseline",
                        children=[
                            html.Span(
                                f"{metric_name} Scope Change",
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
                                [
                                    "Threshold: ",
                                    html.Span(f"{threshold}%"),
                                    throughput_ratio is not None
                                    and html.Span(
                                        [
                                            " | Throughput Ratio: ",
                                            html.Span(
                                                f"{throughput_ratio:.2f}x",
                                                style={
                                                    "color": "#dc3545"
                                                    if high_throughput_ratio
                                                    else "#20c997"
                                                },
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            html.Span(
                                status_text,
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


# For backwards compatibility
create_scope_creep_indicator = create_scope_change_indicator


def create_scope_growth_chart(weekly_growth_data, show_points=True):
    """Create a bar chart showing weekly scope growth with side-by-side bars and separate y-axes for items and points."""
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

    # Calculate the data ranges to align zero lines
    items_min = weekly_growth_data["items_growth"].min()
    items_max = weekly_growth_data["items_growth"].max()
    points_min = weekly_growth_data["points_growth"].min()
    points_max = weekly_growth_data["points_growth"].max()

    # Add some padding (10% of range) to both axes
    items_range = items_max - items_min
    points_range = points_max - points_min
    items_padding = items_range * 0.1 if items_range > 0 else 1
    points_padding = points_range * 0.1 if points_range > 0 else 1

    # Calculate ranges that align zero lines
    # Get the larger absolute value for each axis to make them symmetric around zero
    items_abs_max = max(abs(items_min), abs(items_max)) + items_padding
    points_abs_max = max(abs(points_min), abs(points_max)) + points_padding

    # Set symmetric ranges around zero to ensure proper alignment
    items_range_final = [-items_abs_max, items_abs_max]
    points_range_final = [-points_abs_max, points_abs_max]

    # Create trace for items - side by side bars with primary y-axis
    items_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["items_growth"],
        name="Items Growth",
        marker_color="rgba(0, 123, 255, 0.7)",  # Blue for items
        width=0.4,  # Make bars narrower to fit side by side
        offset=-0.25,  # Shift to the left for side by side
        yaxis="y",  # Use primary y-axis
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
        marker_color="rgba(253, 126, 20, 0.7)",  # Orange for points
        width=0.4,  # Make bars narrower to fit side by side
        offset=0.25,  # Shift to the right for side by side
        yaxis="y2",  # Use secondary y-axis
        # Add hover text to clarify meaning of values
        hovertemplate=(
            "<b>Points</b><br>"
            + "Week: %{x}<br>"
            + "Growth: %{y}<br>"
            + "<i>Positive = Scope Increase<br>"
            + "Negative = Backlog Reduction</i>"
        ),
    )

    # Create data list - include points trace only if points tracking is enabled
    data_traces = [items_trace]
    if show_points:
        data_traces.append(points_trace)

    # Create layout with dual y-axes but still using side-by-side bars
    layout = go.Layout(
        title="Weekly Scope Growth (+ Increase, - Reduction)",
        xaxis={
            "title": "Week",
            "tickangle": -45,
            "gridcolor": "rgba(200, 200, 200, 0.2)",
        },
        yaxis={
            "title": {
                "text": "Items Growth",
                "font": {"color": "rgba(0, 123, 255, 1)"},
            },
            "tickfont": {"color": "rgba(0, 123, 255, 1)"},
            "gridcolor": "rgba(0, 123, 255, 0.1)",
            "zeroline": True,
            "zerolinecolor": "rgba(0, 123, 255, 0.2)",
            "side": "left",
            "range": items_range_final,  # Set explicit range to align zero
        },
        yaxis2={
            "title": {
                "text": "Points Growth",
                "font": {"color": "rgba(253, 126, 20, 1)"},
            },
            "tickfont": {"color": "rgba(253, 126, 20, 1)"},
            "gridcolor": "rgba(253, 126, 20, 0.1)",
            "zeroline": True,
            "zerolinecolor": "rgba(253, 126, 20, 0.2)",
            "overlaying": "y",
            "side": "right",
            "range": points_range_final,  # Set explicit range to align zero
        }
        if show_points
        else {},
        height=300,
        margin={
            "l": 60,
            "r": 60,  # Increased right margin back for the second y-axis
            "t": 70,
            "b": 60,
        },
        legend={
            "orientation": "h",
            "y": 1.25,
            "xanchor": "center",
            "x": 0.5,
        },
        hovermode="x unified",
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
        barmode="group",  # Keep the bars grouped side by side
    )

    # Create figure
    figure = go.Figure(data=data_traces, layout=layout)

    # Add a reference line at y=0 for both axes
    figure.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=0,
        y1=0,
        yref="y",
        line=dict(color="rgba(0, 123, 255, 0.5)", width=1, dash="dot"),
    )

    if show_points:
        figure.add_shape(
            type="line",
            x0=0,
            x1=1,
            xref="paper",
            y0=0,
            y1=0,
            yref="y2",
            line=dict(color="rgba(253, 126, 20, 0.5)", width=1, dash="dot"),
        )

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
    )


def create_enhanced_stability_gauge(
    stability_value, title="Scope Stability Index", height=300
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
                    "visible": True,
                },
                "bar": {
                    "color": color,
                    "thickness": 0.6,
                },
                "bgcolor": "white",
                "borderwidth": 0.4,
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
                "font": {"size": 24, "color": color},  # Removed 'weight' property
                "valueformat": ".2f",
                "suffix": "",  # No suffix to avoid overlap
            },
        )
    )

    # Add status text annotation BELOW the gauge (moved lower)
    figure.add_annotation(
        text=f"<b>Status: {status_text}</b>",
        x=0.5,
        y=-0.01,  # Position further down (was 0.02)
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=16, color=color),
        align="center",
    )

    # Add reference line annotation (adjusted position)
    figure.add_annotation(
        text="Target: 0.7+",
        x=0.5,
        y=0.13,  # Moved down slightly (was 0.1)
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


def create_scope_change_alert(alert_data):
    """Create an alert component for significant scope changes."""
    if alert_data["status"] == "ok":
        return html.Div()  # Return empty div if no alert

    # Use different colors based on status
    if alert_data["status"] == "warning":
        color = "warning"
        icon = "fas fa-exclamation-triangle"
    else:  # info status
        color = "info"
        icon = "fas fa-info-circle"

    return dbc.Alert(
        [html.I(className=f"{icon} me-2"), alert_data["message"]],
        color=color,
        className="mt-3",
        is_open=True,
    )


# For backwards compatibility
create_scope_creep_alert = create_scope_change_alert


def create_cumulative_scope_chart(
    weekly_growth_data, baseline_items, baseline_points, show_points=True
):
    """
    Create a line chart showing cumulative scope growth over time with separate y-axes for items and points.

    Args:
        weekly_growth_data (DataFrame): DataFrame with weekly growth data
        baseline_items (int): Initial baseline for items
        baseline_points (int): Initial baseline for points
        show_points (bool): Whether to show points traces

    Returns:
        dcc.Graph: A graph component with cumulative scope growth
    """
    if weekly_growth_data.empty:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": go.Layout(
                    title="Cumulative Scope Growth",
                    xaxis={"title": "Week"},
                    yaxis={"title": "Items"},
                    height=350,
                ),
            },
            config={"displayModeBar": False, "responsive": True},
        )

    # Sort data by week to ensure proper accumulation
    weekly_data = weekly_growth_data.sort_values("start_date")

    # Create cumulative series for items and points
    weekly_data["cum_items_growth"] = weekly_data["items_growth"].cumsum()
    weekly_data["cum_points_growth"] = weekly_data["points_growth"].cumsum()

    # Calculate total scope at each point (baseline + cumulative growth)
    weekly_data["total_items_scope"] = baseline_items + weekly_data["cum_items_growth"]
    weekly_data["total_points_scope"] = (
        baseline_points + weekly_data["cum_points_growth"]
    )

    # Create traces for items (yaxis1)
    items_baseline_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=[baseline_items] * len(weekly_data),
        mode="lines",
        name="Items Baseline",
        line=dict(color="rgba(0, 123, 255, 0.5)", width=2, dash="dash"),
        hovertemplate="<b>Items Baseline</b><br>Week: %{x}<br>Value: %{y}<extra></extra>",
        yaxis="y",
    )

    items_scope_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=weekly_data["total_items_scope"],
        mode="lines+markers",
        name="Items Total Scope",
        line=dict(color="rgba(0, 123, 255, 1)", width=3),
        marker=dict(size=7),
        hovertemplate="<b>Items Total Scope</b><br>Week: %{x}<br>Value: %{y}<extra></extra>",
        yaxis="y",
    )

    # Create traces for points with different color (yaxis2)
    points_baseline_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=[baseline_points] * len(weekly_data),
        mode="lines",
        name="Points Baseline",
        line=dict(color="rgba(253, 126, 20, 0.5)", width=2, dash="dash"),
        hovertemplate="<b>Points Baseline</b><br>Week: %{x}<br>Value: %{y}<extra></extra>",
        yaxis="y2",
    )

    points_scope_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=weekly_data["total_points_scope"],
        mode="lines+markers",
        name="Points Total Scope",
        line=dict(color="rgba(253, 126, 20, 1)", width=3),
        marker=dict(size=7),
        hovertemplate="<b>Points Total Scope</b><br>Week: %{x}<br>Value: %{y}<extra></extra>",
        yaxis="y2",
    )

    # Create data list - include points traces only if points tracking is enabled
    data_traces = [
        items_baseline_trace,
        items_scope_trace,
    ]
    if show_points:
        data_traces.extend([points_baseline_trace, points_scope_trace])

    # Create layout with dual y-axes
    layout = go.Layout(
        title="Cumulative Scope Growth (Baseline + Change)",
        xaxis={
            "title": "Week",
            "tickangle": -45,
            "gridcolor": "rgba(200, 200, 200, 0.2)",
        },
        yaxis={
            "title": {"text": "Items", "font": {"color": "rgba(0, 123, 255, 1)"}},
            "tickfont": {"color": "rgba(0, 123, 255, 1)"},
            "gridcolor": "rgba(0, 123, 255, 0.1)",
            "zeroline": True,
            "zerolinecolor": "rgba(0, 123, 255, 0.2)",
            "side": "left",
        },
        yaxis2={
            "title": {"text": "Points", "font": {"color": "rgba(253, 126, 20, 1)"}},
            "tickfont": {"color": "rgba(253, 126, 20, 1)"},
            "gridcolor": "rgba(253, 126, 20, 0.1)",
            "zeroline": True,
            "zerolinecolor": "rgba(253, 126, 20, 0.2)",
            "overlaying": "y",
            "side": "right",
        }
        if show_points
        else {},
        height=350,
        margin={
            "l": 60,
            "r": 60,
            "t": 70,
            "b": 60,
        },
        legend={
            "orientation": "h",
            "y": 1.25,
            "xanchor": "center",
            "x": 0.5,
        },
        hovermode="x unified",
        plot_bgcolor="rgba(255, 255, 255, 0.9)",
    )

    # Create figure with conditional traces
    figure = go.Figure(
        data=data_traces,
        layout=layout,
    )

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False, "responsive": True},
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
    scope_change_rate,
    weekly_growth_data,
    stability_index,
    threshold=20,
    total_items_scope=None,
    total_points_scope=None,  # Add parameters for total scope
    show_points=True,  # Add parameter for points tracking
):
    """
    Create a dashboard component displaying all scope metrics.

    Args:
        scope_change_rate (dict): Dictionary containing items_rate, points_rate and throughput_ratio
        weekly_growth_data (DataFrame): DataFrame containing weekly growth data
        stability_index (dict): Dictionary containing items_stability and points_stability values
        threshold (int): Threshold percentage for scope change notifications
        total_items_scope (int, optional): Total items scope (completed + remaining)
        total_points_scope (int, optional): Total points scope (completed + remaining)
        show_points (bool): Whether points tracking is enabled (default: True)

    Returns:
        html.Div: A dashboard component with scope metrics
    """
    # Read remaining items from project data using new persistence functions
    from data.persistence import load_project_data

    try:
        project_data = load_project_data()
        remaining_items = project_data.get("total_items", 34)
        remaining_points = project_data.get("total_points", 154)
    except Exception:
        # If we can't read the file, use defaults
        remaining_items = 34
        remaining_points = 154

    # Get total created and completed items/points from the statistics
    from data.persistence import load_statistics

    try:
        statistics_data, _ = load_statistics()
        if statistics_data:
            df = pd.DataFrame(statistics_data)
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
        else:
            total_completed_items = 0
            total_completed_points = 0
            total_created_items = 0
            total_created_points = 0
    except Exception:
        # If we can't read the data, use defaults
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

    # Extract throughput ratios if available, or calculate them
    items_throughput_ratio = (
        scope_change_rate.get("throughput_ratio", {}).get("items", 0)
        if isinstance(scope_change_rate.get("throughput_ratio", {}), dict)
        else (
            total_created_items / total_completed_items
            if total_completed_items > 0
            else float("inf")
            if total_created_items > 0
            else 0
        )
    )

    points_throughput_ratio = (
        scope_change_rate.get("throughput_ratio", {}).get("points", 0)
        if isinstance(scope_change_rate.get("throughput_ratio", {}), dict)
        else (
            total_created_points / total_completed_points
            if total_completed_points > 0
            else float("inf")
            if total_created_points > 0
            else 0
        )
    )

    # Check if scope change exceeds threshold and create alert
    items_exceeded = scope_change_rate["items_rate"] > threshold
    points_exceeded = scope_change_rate["points_rate"] > threshold
    items_throughput_concern = items_throughput_ratio > 1
    points_throughput_concern = points_throughput_ratio > 1

    alert_data = {
        "status": "warning"
        if (items_exceeded or points_exceeded)
        and (items_throughput_concern or points_throughput_concern)
        else "info"
        if items_exceeded
        or points_exceeded
        or items_throughput_concern
        or points_throughput_concern
        else "ok",
        "message": "",
    }

    if alert_data["status"] != "ok":
        parts = []
        if items_exceeded:
            parts.append(f"Items scope change ({scope_change_rate['items_rate']}%)")
        if points_exceeded:
            parts.append(f"Points scope change ({scope_change_rate['points_rate']}%)")

        if parts:
            if alert_data["status"] == "warning":
                alert_data["message"] = (
                    f"{' and '.join(parts)} exceed threshold ({threshold}%)."
                )
            else:
                alert_data["message"] = (
                    f"{' and '.join(parts)} changing significantly ({threshold}% threshold)."
                )

            # Add throughput insight
            if items_throughput_concern and points_throughput_concern:
                alert_data["message"] += (
                    f" Scope is growing {items_throughput_ratio:.2f}x faster than items completion and {points_throughput_ratio:.2f}x faster than points completion."
                )
            elif items_throughput_concern:
                alert_data["message"] += (
                    f" Scope is growing {items_throughput_ratio:.2f}x faster than items completion."
                )
            elif points_throughput_concern:
                alert_data["message"] += (
                    f" Scope is growing {points_throughput_ratio:.2f}x faster than points completion."
                )

    return html.Div(
        [
            # Scope Change Rate Indicators with improved layout
            html.Div(
                [
                    # Items trend box
                    html.Div(
                        [
                            # Header with icon and tooltip - matching weekly metrics style
                            html.Div(
                                className="d-flex align-items-center mb-2",
                                children=[
                                    html.I(
                                        className="fas fa-tasks me-2",
                                        style={"color": "#20c997"},
                                    ),
                                    html.Span(
                                        "Items Scope Change Metrics",
                                        className="fw-medium",
                                    ),
                                    html.I(
                                        className="fas fa-info-circle text-info ms-2",
                                        id="info-tooltip-items-scope-methodology",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                            ),
                            # Enhanced scope change indicator with tooltips
                            html.Div(
                                [
                                    create_scope_change_indicator(
                                        "Items Scope Change Rate",
                                        scope_change_rate["items_rate"],
                                        threshold,
                                        SCOPE_HELP_TEXTS["scope_change_rate"],
                                        items_throughput_ratio,
                                    ),
                                    # Add scope calculation tooltip icon
                                    html.I(
                                        className="fas fa-calculator text-info ms-2",
                                        id="info-tooltip-items-scope-calculation",
                                        style={"cursor": "pointer"},
                                    ),
                                    # Add throughput ratio tooltip icon
                                    html.I(
                                        className="fas fa-chart-line text-info ms-2",
                                        id="info-tooltip-items-throughput-ratio",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="d-flex align-items-center",
                                style={"gap": "0.25rem"},
                            ),
                            # Enhanced forecast pills with methodology tooltip - matching weekly metrics style
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            create_forecast_pill(
                                                "Created",
                                                f"{int(total_created_items)} items",
                                                "#20c997",
                                            ),
                                            create_forecast_pill(
                                                "Completed",
                                                f"{int(total_completed_items)} items",
                                                "#0d6efd",
                                            ),
                                            create_forecast_pill(
                                                "Threshold",
                                                f"{int(threshold_items)} items",
                                                "#fd7e14",
                                            ),
                                            html.Div(
                                                html.Small(
                                                    f"baseline: {int(baseline_items)} items",
                                                    className="text-muted fst-italic",
                                                ),
                                                style={"paddingTop": "2px"},
                                            ),
                                        ],
                                        className="d-flex flex-wrap align-items-center",
                                        style={"gap": "0.25rem"},
                                    ),
                                    # Add scope breakdown methodology tooltip icon
                                    html.I(
                                        className="fas fa-chart-bar text-info ms-2",
                                        id="info-tooltip-items-scope-breakdown",
                                        style={"cursor": "pointer"},
                                    ),
                                ],
                                className="d-flex align-items-center mt-2",
                                style={"gap": "0.5rem"},
                            ),
                            # Add all tooltip components at the end for proper rendering - matching weekly metrics pattern
                            html.Div(
                                [
                                    create_info_tooltip(
                                        "items-scope-methodology",
                                        SCOPE_HELP_TEXTS["scope_metrics_explanation"],
                                    ),
                                    create_info_tooltip(
                                        "items-scope-calculation",
                                        SCOPE_HELP_TEXTS["scope_change_rate"],
                                    ),
                                    create_info_tooltip(
                                        "items-throughput-ratio",
                                        SCOPE_HELP_TEXTS["throughput_ratio"],
                                    ),
                                    create_info_tooltip(
                                        "items-scope-breakdown",
                                        "Breakdown of scope metrics: Created items show new work added, Completed items show work finished, Threshold shows the alert level, and Baseline shows the original scope when tracking began.",
                                    ),
                                ],
                                style={"display": "none"},
                            ),
                        ],
                        className="col-md-6 col-12 mb-3 pe-md-2",
                    ),
                    # Points trend box - only show if points tracking is enabled
                ]
                + (
                    [
                        html.Div(
                            [
                                # Header with icon and tooltip - matching weekly metrics style
                                html.Div(
                                    className="d-flex align-items-center mb-2",
                                    children=[
                                        html.I(
                                            className="fas fa-chart-bar me-2",
                                            style={"color": "#fd7e14"},
                                        ),
                                        html.Span(
                                            "Points Scope Change Metrics",
                                            className="fw-medium",
                                        ),
                                        html.I(
                                            className="fas fa-info-circle text-info ms-2",
                                            id="info-tooltip-points-scope-methodology",
                                            style={"cursor": "pointer"},
                                        ),
                                    ],
                                ),
                                # Enhanced scope change indicator with tooltips
                                html.Div(
                                    [
                                        create_scope_change_indicator(
                                            "Points Scope Change Rate",
                                            scope_change_rate["points_rate"],
                                            threshold,
                                            SCOPE_HELP_TEXTS["scope_change_rate"]
                                            + " This version measures scope changes based on story points rather than item counts.",
                                            points_throughput_ratio,
                                        ),
                                        # Add scope calculation tooltip icon
                                        html.I(
                                            className="fas fa-calculator text-info ms-2",
                                            id="info-tooltip-points-scope-calculation",
                                            style={"cursor": "pointer"},
                                        ),
                                        # Add throughput ratio tooltip icon
                                        html.I(
                                            className="fas fa-chart-line text-info ms-2",
                                            id="info-tooltip-points-throughput-ratio",
                                            style={"cursor": "pointer"},
                                        ),
                                    ],
                                    className="d-flex align-items-center",
                                    style={"gap": "0.25rem"},
                                ),
                                # Enhanced forecast pills with methodology tooltip - matching weekly metrics style
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                create_forecast_pill(
                                                    "Created",
                                                    f"{int(total_created_points)} points",
                                                    "#fd7e14",
                                                ),
                                                create_forecast_pill(
                                                    "Completed",
                                                    f"{int(total_completed_points)} points",
                                                    "#0d6efd",
                                                ),
                                                create_forecast_pill(
                                                    "Threshold",
                                                    f"{int(threshold_points)} points",
                                                    "#fd7e14",
                                                ),
                                                html.Div(
                                                    html.Small(
                                                        f"baseline: {int(baseline_points)} points",
                                                        className="text-muted fst-italic",
                                                    ),
                                                    style={"paddingTop": "2px"},
                                                ),
                                            ],
                                            className="d-flex flex-wrap align-items-center",
                                            style={"gap": "0.25rem"},
                                        ),
                                        # Add scope breakdown methodology tooltip icon
                                        html.I(
                                            className="fas fa-chart-bar text-info ms-2",
                                            id="info-tooltip-points-scope-breakdown",
                                            style={"cursor": "pointer"},
                                        ),
                                    ],
                                    className="d-flex align-items-center mt-2",
                                    style={"gap": "0.5rem"},
                                ),
                                # Add all tooltip components at the end for proper rendering - matching weekly metrics pattern
                                html.Div(
                                    [
                                        create_info_tooltip(
                                            "points-scope-methodology",
                                            SCOPE_HELP_TEXTS[
                                                "scope_metrics_explanation"
                                            ]
                                            + " This version tracks changes based on story points rather than item counts, giving a weighted view of scope complexity changes.",
                                        ),
                                        create_info_tooltip(
                                            "points-scope-calculation",
                                            SCOPE_HELP_TEXTS["scope_change_rate"]
                                            + " This version measures scope changes based on story points rather than item counts.",
                                        ),
                                        create_info_tooltip(
                                            "points-throughput-ratio",
                                            SCOPE_HELP_TEXTS["throughput_ratio"]
                                            + " Points-based throughput shows if scope complexity is growing faster than delivery capability.",
                                        ),
                                        create_info_tooltip(
                                            "points-scope-breakdown",
                                            "Breakdown of scope metrics based on story points: Created points show complexity of new work added, Completed points show effort delivered, Threshold shows the alert level for complexity growth, and Baseline shows the original planned effort.",
                                        ),
                                    ],
                                    style={"display": "none"},
                                ),
                            ],
                            className="col-md-6 col-12 mb-3 ps-md-2",
                        ),
                    ]
                    if show_points
                    else []
                ),
                className="row mb-3",
            ),
            # Alert for threshold breach
            create_scope_change_alert(alert_data),
            # Cumulative Scope Growth Chart with Tooltip
            html.Div(
                [
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className="fas fa-chart-area me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "Cumulative Scope Changes Over Time ",
                                    create_info_tooltip(
                                        "cumulative_scope_chart",
                                        SCOPE_HELP_TEXTS["cumulative_chart"],
                                    ),
                                ],
                                className="mb-3",
                            ),
                            create_cumulative_scope_chart(
                                weekly_growth_data,
                                baseline_items,
                                baseline_points,
                                show_points,
                            ),
                        ]
                    )
                ],
                className="mb-3",
            ),
            # Throughput vs Scope Change summary with tooltip
            html.Div(
                [
                    html.Div(
                        className="d-flex align-items-center mb-2",
                        children=[
                            html.I(
                                className="fas fa-balance-scale me-2",
                                style={"color": "#6610f2"},
                            ),
                            html.Span(
                                "Scope Change vs Team Throughput ",
                                className="fw-medium",
                            ),
                            create_info_tooltip(
                                "throughput_comparison",
                                SCOPE_HELP_TEXTS["throughput_ratio"],
                            ),
                        ],
                    ),
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.P(
                                    [
                                        "Items: ",
                                        html.Span(
                                            f"For every completed item, {items_throughput_ratio:.2f} new items are being created",
                                            className="fw-medium",
                                            style={
                                                "color": "#dc3545"
                                                if items_throughput_ratio > 1
                                                else "#20c997"
                                            },
                                        ),
                                        html.Span(
                                            f" ({total_created_items} created vs {total_completed_items} completed)",
                                            className="text-muted ms-1",
                                            style={"fontSize": "0.9rem"},
                                        ),
                                    ]
                                ),
                            ]
                            + (
                                [
                                    html.P(
                                        [
                                            "Points: ",
                                            html.Span(
                                                f"For every completed point, {points_throughput_ratio:.2f} new points are being created",
                                                className="fw-medium",
                                                style={
                                                    "color": "#dc3545"
                                                    if points_throughput_ratio > 1
                                                    else "#20c997"
                                                },
                                            ),
                                            html.Span(
                                                f" ({total_created_points} created vs {total_completed_points} completed)",
                                                className="text-muted ms-1",
                                                style={"fontSize": "0.9rem"},
                                            ),
                                        ]
                                    ),
                                ]
                                if show_points
                                else []
                            )
                            + [
                                html.P(
                                    "A ratio greater than 1.0 indicates scope is growing faster than the team can deliver. This may affect delivery timelines.",
                                    className="text-muted small mb-0 mt-2 fst-italic",
                                ),
                            ]
                        ),
                        className="mb-3",
                    ),
                ]
            ),
            # Weekly Scope Growth Chart with Tooltip
            html.Div(
                [
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className="fas fa-chart-bar me-2",
                                        style={"color": "#fd7e14"},
                                    ),
                                    "Weekly Scope Growth Patterns ",
                                    create_info_tooltip(
                                        "weekly_growth_chart",
                                        SCOPE_HELP_TEXTS["weekly_growth"],
                                    ),
                                ],
                                className="mb-3",
                            ),
                            create_scope_growth_chart(weekly_growth_data, show_points),
                        ]
                    )
                ],
                className="mb-2",
            ),
            # Enhanced Footnote with Agile Context
            html.Div(
                className="text-muted fst-italic small text-center",
                children=[
                    html.I(
                        className="fas fa-seedling me-1",
                        style={"color": "rgb(108, 117, 125)"},
                    ),
                    "Growth Patterns: Positive spikes show scope additions from new requirements or discoveries. Negative values indicate backlog refinement or completion focus.",
                ],
            ),
            # Agile Context Notice
            dbc.Alert(
                [
                    html.I(className="fas fa-lightbulb me-2"),
                    html.Strong("Agile Project Context: "),
                    "In agile projects, scope changes are normal and healthy. These metrics help you understand patterns, not problems. Lower adaptability values are typical for responsive agile teams.",
                ],
                color="info",
                className="mb-4",
                style={"fontSize": "0.9rem"},
            ),
            # Adaptability Gauges with Tooltips
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H6(
                                                [
                                                    "Items Adaptability Index ",
                                                    create_info_tooltip(
                                                        "adaptability_index",
                                                        SCOPE_HELP_TEXTS[
                                                            "adaptability_index"
                                                        ],
                                                    ),
                                                ],
                                                className="mb-3 text-center",
                                            ),
                                            create_enhanced_stability_gauge(
                                                stability_index["items_stability"],
                                                "",  # Empty title since we have header above
                                                height=280,
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ],
                        width=12,
                        md=6,
                    ),
                ]
                + (
                    [
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.H6(
                                                    [
                                                        "Points Adaptability Index ",
                                                        create_info_tooltip(
                                                            "points_adaptability_index",
                                                            SCOPE_HELP_TEXTS[
                                                                "adaptability_index"
                                                            ]
                                                            + " This version measures adaptability based on story points rather than item counts.",
                                                        ),
                                                    ],
                                                    className="mb-3 text-center",
                                                ),
                                                create_enhanced_stability_gauge(
                                                    stability_index["points_stability"],
                                                    "",  # Empty title since we have header above
                                                    height=280,
                                                ),
                                            ]
                                        )
                                    ]
                                )
                            ],
                            width=12,
                            md=6,
                        ),
                    ]
                    if show_points
                    else []
                )
            ),
            # Enhanced Footer with Agile Context
            html.Div(
                className="text-muted fst-italic small text-center mt-3",
                children=[
                    html.I(
                        className="fas fa-chart-line me-1",
                        style={"color": "rgb(108, 117, 125)"},
                    ),
                    "Adaptability Index: Lower values (0.3-0.6) are normal for responsive agile teams. Higher values (0.7+) indicate more predictable scope.",
                ],
            ),
        ]
    )


# For backwards compatibility
create_scope_creep_dashboard = create_scope_metrics_dashboard
