from typing import cast

import plotly.graph_objs as go
from dash import dcc

from configuration.chart_config import get_scope_metrics_chart_config


def create_scope_growth_chart(weekly_growth_data, show_points=True):

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

    items_min = weekly_growth_data["items_growth"].min()
    items_max = weekly_growth_data["items_growth"].max()
    points_min = weekly_growth_data["points_growth"].min()
    points_max = weekly_growth_data["points_growth"].max()

    items_range = items_max - items_min
    points_range = points_max - points_min
    items_padding = items_range * 0.1 if items_range > 0 else 1
    points_padding = points_range * 0.1 if points_range > 0 else 1

    items_abs_max = max(abs(items_min), abs(items_max)) + items_padding
    points_abs_max = max(abs(points_min), abs(points_max)) + points_padding

    items_range_final = [-items_abs_max, items_abs_max]
    points_range_final = [-points_abs_max, points_abs_max]

    items_colors = [
        "rgba(0, 123, 255, 0.9)" if val < 0 else "rgba(0, 123, 255, 0.4)"
        for val in weekly_growth_data["items_growth"]
    ]

    items_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["items_growth"],
        name="Items (darker=completing faster)",
        marker_color=items_colors,
        width=0.4,
        offset=-0.25,
        yaxis="y",
        hovertemplate=(
            "<b>Items Net Change</b><br>"
            + "Week: %{x}<br>"
            + "Net: %{y}<br>"
            + "<i>Negative = Completing faster (✓)<br>"
            + "Positive = Scope additions</i>"
        ),
    )

    points_colors = [
        "rgba(253, 126, 20, 0.9)" if val < 0 else "rgba(253, 126, 20, 0.4)"
        for val in weekly_growth_data["points_growth"]
    ]

    points_trace = go.Bar(
        x=weekly_growth_data["week_label"],
        y=weekly_growth_data["points_growth"],
        name="Points (darker=completing faster)",
        marker_color=points_colors,
        width=0.4,
        offset=0.25,
        yaxis="y2",
        hovertemplate=(
            "<b>Points Net Change</b><br>"
            + "Week: %{x}<br>"
            + "Net: %{y}<br>"
            + "<i>Negative = Completing faster (✓)<br>"
            + "Positive = Scope additions</i>"
        ),
    )

    data_traces = [items_trace]
    if show_points:
        data_traces.append(points_trace)

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
            "range": items_range_final,
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
            "range": points_range_final,
        }
        if show_points
        else {},
        height=300,
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
        barmode="group",
    )

    figure = go.Figure(data=data_traces, layout=layout)

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

    weekly_data = weekly_growth_data.sort_values("start_date")

    weekly_data["cum_items_growth"] = weekly_data["items_growth"].cumsum()
    weekly_data["cum_points_growth"] = weekly_data["points_growth"].cumsum()

    weekly_data["net_scope_items"] = baseline_items + weekly_data["cum_items_growth"]
    weekly_data["net_scope_points"] = baseline_points + weekly_data["cum_points_growth"]

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

    data_traces = [
        items_baseline_trace,
        items_scope_trace,
    ]
    if show_points:
        data_traces.extend([points_baseline_trace, points_scope_trace])

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
