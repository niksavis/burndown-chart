"""Scope Metrics Chart Components

Provides bar and line chart components for scope growth visualization.
"""

from typing import cast

import plotly.graph_objs as go
from dash import dcc

from configuration.chart_config import get_scope_metrics_chart_config


def create_scope_growth_chart(weekly_growth_data, show_points=True):
    """Create a bar chart showing weekly scope growth.

    Uses side-by-side bars and separate y-axes for items and points.
    """
    if weekly_growth_data.empty:
        empty_layout = go.Layout(
            title="Weekly Scope Growth",
            xaxis={"title": "Week"},
            yaxis={"title": "Growth"},
            height=300,
        )
        empty_figure = go.Figure(data=[], layout=empty_layout)
        chart_height = cast(int, getattr(empty_layout, "height", None) or 300)
        return dcc.Graph(
            figure=empty_figure,
            config=get_scope_metrics_chart_config(
                filename_prefix="weekly_scope_growth"
            ),  # type: ignore[arg-type]
            style={"height": f"{chart_height}px"},
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

    # Create trace for items - keep blue color, vary intensity for positive/negative
    items_colors = [
        "rgba(0, 123, 255, 0.9)" if val < 0 else "rgba(0, 123, 255, 0.4)"
        for val in weekly_growth_data["items_growth"]
    ]

    items_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["items_growth"],
        name="Items (darker=completing faster)",
        marker_color=items_colors,
        # Darker blue = net reduction (good), lighter = additions
        width=0.4,  # Make bars narrower to fit side by side
        offset=-0.25,  # Shift to the left for side by side
        yaxis="y",  # Use primary y-axis
        # Add hover text to clarify meaning of values
        hovertemplate=(
            "<b>Items Net Change</b><br>"
            + "Week: %{x}<br>"
            + "Net: %{y}<br>"
            + "<i>Negative = Completing faster (✓)<br>"
            + "Positive = Scope additions</i>"
        ),
    )

    # Create points trace - keep orange color, vary intensity for positive/negative
    points_colors = [
        "rgba(253, 126, 20, 0.9)" if val < 0 else "rgba(253, 126, 20, 0.4)"
        for val in weekly_growth_data["points_growth"]
    ]

    points_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["points_growth"],
        name="Points (darker=completing faster)",
        marker_color=points_colors,
        # Darker orange = net reduction (good), lighter = additions
        width=0.4,  # Make bars narrower to fit side by side
        offset=0.25,  # Shift to the right for side by side
        yaxis="y2",  # Use secondary y-axis
        # Add hover text to clarify meaning of values
        hovertemplate=(
            "<b>Points Net Change</b><br>"
            + "Week: %{x}<br>"
            + "Net: %{y}<br>"
            + "<i>Negative = Completing faster (✓)<br>"
            + "Positive = Scope additions</i>"
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

    chart_height = cast(int, getattr(figure.layout, "height", None) or 300)
    return dcc.Graph(
        figure=figure,
        config=get_scope_metrics_chart_config(filename_prefix="weekly_scope_growth"),  # type: ignore[arg-type]
        style={"height": f"{chart_height}px"},
    )


def create_cumulative_scope_chart(
    weekly_growth_data, baseline_items, baseline_points, show_points=True
):
    """
    Create a line chart showing backlog evolution over time
    with separate y-axes for items and points.

    Args:
        weekly_growth_data (DataFrame): DataFrame with weekly growth data
        baseline_items (int): Initial baseline for items
            (backlog at period start = current + completed - created)
        baseline_points (int): Initial baseline for points
            (backlog at period start = current + completed - created)
        show_points (bool): Whether to show points traces

    Returns:
        dcc.Graph: A graph component with backlog size evolution
    """
    if weekly_growth_data.empty:
        empty_layout = go.Layout(
            title="Backlog Size Over Time",
            xaxis={"title": "Week"},
            yaxis={"title": "Items Remaining"},
            height=350,
        )
        empty_figure = go.Figure(data=[], layout=empty_layout)
        chart_height = cast(int, getattr(empty_layout, "height", None) or 350)
        return dcc.Graph(
            figure=empty_figure,
            config=get_scope_metrics_chart_config(
                filename_prefix="backlog_size_over_time"
            ),  # type: ignore[arg-type]
            style={"height": f"{chart_height}px"},
        )

    # Sort data by week to ensure proper accumulation
    weekly_data = weekly_growth_data.sort_values("start_date")

    # Create cumulative series for items and points (NET change from baseline)
    weekly_data["cum_items_growth"] = weekly_data["items_growth"].cumsum()
    weekly_data["cum_points_growth"] = weekly_data["points_growth"].cumsum()

    # Calculate actual remaining work over time
    # by starting from baseline and applying cumulative changes
    # This represents the actual backlog size at each week (baseline + net_change)
    # Cannot go negative as long as baseline is positive
    weekly_data["net_scope_items"] = baseline_items + weekly_data["cum_items_growth"]
    weekly_data["net_scope_points"] = baseline_points + weekly_data["cum_points_growth"]

    # Create traces for items (yaxis1) - showing actual remaining work from baseline
    items_baseline_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=[baseline_items] * len(weekly_data),
        mode="lines",
        name="Items Baseline",
        line=dict(color="rgba(128, 128, 128, 0.5)", width=2, dash="dash"),
        hovertemplate=(
            "<b>Items Baseline</b><br>"
            f"Week: %{{x}}<br>Items: {baseline_items}<extra></extra>"
        ),
        yaxis="y",
        showlegend=True,
    )

    items_scope_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=weekly_data["net_scope_items"],
        mode="lines+markers",
        name="Items Remaining",
        line=dict(color="rgba(0, 123, 255, 1)", width=3),
        marker=dict(size=7),
        fill="tonexty",
        fillcolor="rgba(0, 123, 255, 0.1)",
        hovertemplate=(
            "<b>Items Remaining</b><br>Week: %{x}<br>Remaining: %{y}<extra></extra>"
        ),
        yaxis="y",
    )

    # Create traces for points with different color (yaxis2)
    points_baseline_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=[baseline_points] * len(weekly_data),
        mode="lines",
        name="Points Baseline",
        line=dict(color="rgba(253, 126, 20, 0.3)", width=2, dash="dash"),
        hovertemplate=(
            "<b>Points Baseline</b><br>"
            f"Week: %{{x}}<br>Points: {baseline_points:.1f}<extra></extra>"
        ),
        yaxis="y2",
        showlegend=False,
    )

    points_scope_trace = go.Scatter(
        x=weekly_data["week_label"],
        y=weekly_data["net_scope_points"],
        mode="lines+markers",
        name="Points Remaining",
        line=dict(color="rgba(253, 126, 20, 1)", width=3),
        marker=dict(size=7),
        fill="tonexty",
        fillcolor="rgba(253, 126, 20, 0.1)",
        hovertemplate=(
            "<b>Points Remaining</b><br>"
            "Week: %{x}<br>Remaining: %{y:.1f}<extra></extra>"
        ),
        yaxis="y2",
    )

    # Create data list - include points traces only if points tracking is enabled
    # Baseline traces show initial scope at start of period
    data_traces = [
        items_baseline_trace,
        items_scope_trace,
    ]
    if show_points:
        data_traces.extend([points_baseline_trace, points_scope_trace])

    # Create layout with dual y-axes
    layout = go.Layout(
        title="Backlog Size Over Time (Remaining Work)",
        xaxis={
            "title": "Week",
            "tickangle": -45,
            "gridcolor": "rgba(200, 200, 200, 0.2)",
        },
        yaxis={
            "title": {
                "text": "Items Remaining",
                "font": {"color": "rgba(0, 123, 255, 1)"},
            },
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
            "t": 90,
            "b": 60,
        },
        legend={
            "orientation": "h",
            "y": 1.15,
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

    chart_height = cast(int, getattr(figure.layout, "height", None) or 350)
    return dcc.Graph(
        figure=figure,
        config=get_scope_metrics_chart_config(filename_prefix="backlog_size_over_time"),  # type: ignore[arg-type]
        style={"height": f"{chart_height}px"},
    )
