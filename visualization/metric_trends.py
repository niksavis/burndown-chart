from typing import Any

import plotly.graph_objects as go
from dash import dcc

from configuration.dora_config import DORA_BENCHMARKS


def _add_performance_tier_zones(
    figure: go.Figure,
    metric_name: str,
    y_max: float,
    x_range: list[str],
) -> None:

    if metric_name not in DORA_BENCHMARKS:
        return

    benchmarks = DORA_BENCHMARKS[metric_name]

    if metric_name == "deployment_frequency":
        elite_threshold = benchmarks["elite"]["threshold"] * 30
        high_threshold = benchmarks["high"]["threshold"] * 4
        medium_threshold = benchmarks["medium"]["threshold"]

        zones = [
            {
                "y0": elite_threshold,
                "y1": y_max * 1.1,
                "color": "rgba(25, 135, 84, 0.02)",
                "name": "Elite",
            },
            {
                "y0": high_threshold,
                "y1": elite_threshold,
                "color": "rgba(255, 193, 7, 0.02)",
                "name": "High",
            },
            {
                "y0": medium_threshold,
                "y1": high_threshold,
                "color": "rgba(253, 126, 20, 0.02)",
                "name": "Medium",
            },
            {
                "y0": 0,
                "y1": medium_threshold,
                "color": "rgba(220, 53, 69, 0.02)",
                "name": "Low",
            },
        ]

    elif metric_name in ["lead_time_for_changes", "mean_time_to_recovery"]:
        elite_threshold = benchmarks["elite"]["threshold"]
        high_threshold = benchmarks["high"]["threshold"]
        medium_threshold = benchmarks["medium"]["threshold"]

        if metric_name == "mean_time_to_recovery":
            elite_threshold = elite_threshold / 24
            high_threshold = high_threshold * 1
            medium_threshold = medium_threshold * 1

        zones = [
            {
                "y0": 0,
                "y1": elite_threshold,
                "color": "rgba(25, 135, 84, 0.02)",
                "name": "Elite",
            },
            {
                "y0": elite_threshold,
                "y1": high_threshold,
                "color": "rgba(255, 193, 7, 0.02)",
                "name": "High",
            },
            {
                "y0": high_threshold,
                "y1": medium_threshold,
                "color": "rgba(253, 126, 20, 0.02)",
                "name": "Medium",
            },
            {
                "y0": medium_threshold,
                "y1": y_max * 1.1,
                "color": "rgba(220, 53, 69, 0.02)",
                "name": "Low",
            },
        ]

    elif metric_name == "change_failure_rate":
        elite_threshold = benchmarks["elite"]["threshold"]
        high_threshold = benchmarks["high"]["threshold"]
        medium_threshold = benchmarks["medium"]["threshold"]

        zones = [
            {
                "y0": 0,
                "y1": elite_threshold,
                "color": "rgba(25, 135, 84, 0.02)",
                "name": "Elite",
            },
            {
                "y0": elite_threshold,
                "y1": high_threshold,
                "color": "rgba(255, 193, 7, 0.02)",
                "name": "High",
            },
            {
                "y0": high_threshold,
                "y1": medium_threshold,
                "color": "rgba(253, 126, 20, 0.02)",
                "name": "Medium",
            },
            {
                "y0": medium_threshold,
                "y1": 100,
                "color": "rgba(220, 53, 69, 0.02)",
                "name": "Low",
            },
        ]
    else:
        return

    for zone in zones:
        figure.add_shape(
            type="rect",
            xref="paper",
            yref="y",
            x0=0,
            y0=zone["y0"],
            x1=1,
            y1=zone["y1"],
            fillcolor=zone["color"],
            line={"width": 0},
            layer="below",
        )


def create_metric_trend_sparkline(
    week_labels: list[str],
    values: list[float],
    metric_name: str,
    adjusted_values: list[float] | None = None,
    unit: str = "",
    height: int = 80,
    show_axes: bool = False,
    color: str = "#1f77b4",
) -> dcc.Graph:

    if not week_labels or not values:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {
                    "height": height,
                    "margin": {"t": 0, "r": 0, "b": 0, "l": 0},
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                    "annotations": [
                        {
                            "text": "No trend data available",
                            "xref": "paper",
                            "yref": "paper",
                            "x": 0.5,
                            "y": 0.5,
                            "showarrow": False,
                            "font": {"size": 10, "color": "#999"},
                        }
                    ],
                },
            },
            config={"displayModeBar": False},
            style={"height": f"{height}px"},
        )

    trace = go.Scatter(
        x=week_labels,
        y=values,
        mode="lines+markers",
        line={"color": color, "width": 3},
        marker={"size": 6, "color": color},
        hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
        name=metric_name,
    )

    adjusted_trace = None
    if adjusted_values and len(adjusted_values) == len(week_labels):
        adjusted_trace = go.Scatter(
            x=week_labels,
            y=adjusted_values,
            mode="lines+markers",
            line={"color": color, "width": 2, "dash": "dot"},
            marker={"size": 5, "color": color, "symbol": "circle-open"},
            hovertemplate=(
                f"<b>%{{x}}</b><br>Adjusted: %{{y:.2f}} {unit}<extra></extra>"
            ),
            name="Adjusted",
        )

    all_values = values + adjusted_values if adjusted_values else values
    if all_values:
        min_val = min(all_values)
        max_val = max(all_values)
        range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
        y_min = min_val - range_padding
        y_max = max_val + range_padding

        if max_val <= 100 and min_val >= 0:
            y_min = max(0, y_min)

        y_range = [y_min, y_max]
    else:
        y_range = None

    layout = {
        "height": height,
        "margin": {
            "t": 10,
            "r": 20,
            "b": 50 if show_axes else 5,
            "l": 50 if show_axes else 5,
        },
        "xaxis": {
            "type": "category",
            "categoryorder": "array",
            "categoryarray": week_labels,
            "visible": show_axes,
            "showgrid": True if show_axes else False,
            "gridcolor": "rgba(0,0,0,0.1)",
            "gridwidth": 1,
            "zeroline": False,
            "tickangle": 45,
            "tickfont": {"size": 9},
        },
        "yaxis": {
            "visible": show_axes,
            "showgrid": True if show_axes else False,
            "gridcolor": "rgba(0,0,0,0.1)",
            "gridwidth": 1,
            "zeroline": False,
            "range": y_range,
            "tickfont": {"size": 10},
        },
        "showlegend": False,
        "hovermode": "x unified",
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
    }

    chart_traces = [trace]
    if adjusted_trace is not None:
        chart_traces.append(adjusted_trace)

    figure = {"data": chart_traces, "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={
            "displayModeBar": False,
            "responsive": True,
            "scrollZoom": False,
            "doubleClick": False,
            "showTips": False,
        },
        style={"height": f"{height}px"},
        className="metric-sparkline",
    )


def create_metric_trend_full(
    week_labels: list[str],
    values: list[float],
    metric_name: str,
    adjusted_values: list[float] | None = None,
    unit: str = "",
    target_line: float | None = None,
    target_label: str = "Target",
    height: int = 200,
    show_performance_zones: bool = True,
    line_color: str = "#1f77b4",
) -> dcc.Graph:

    if not week_labels or not values:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {
                    "height": height,
                    "title": "No trend data available",
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                },
            },
            config={
                "displayModeBar": False,
                "responsive": True,
                "scrollZoom": False,
                "doubleClick": False,
                "showTips": False,
            },
            style={"height": f"{height}px"},
        )

    all_values = values + adjusted_values if adjusted_values else values
    min_val = min(all_values)
    max_val = max(all_values)
    range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
    y_min = max(0, min_val - range_padding)
    y_max = max_val + range_padding

    traces = [
        go.Scatter(
            x=week_labels,
            y=values,
            mode="lines+markers",
            line={"color": line_color, "width": 3},
            marker={"size": 8, "color": line_color},
            hovertemplate=f"<b>%{{x}}</b><br>%{{y:.2f}} {unit}<extra></extra>",
            name=metric_name,
        )
    ]

    if adjusted_values and len(adjusted_values) == len(week_labels):
        traces.append(
            go.Scatter(
                x=week_labels,
                y=adjusted_values,
                mode="lines+markers",
                line={"color": line_color, "width": 2, "dash": "dot"},
                marker={"size": 6, "color": line_color, "symbol": "circle-open"},
                hovertemplate=(
                    f"<b>%{{x}}</b><br>Adjusted: %{{y:.2f}} {unit}<extra></extra>"
                ),
                name="Adjusted",
            )
        )

    if target_line is not None:
        traces.append(
            go.Scatter(
                x=[week_labels[0], week_labels[-1]],
                y=[target_line, target_line],
                mode="lines",
                line={"color": "red", "width": 2, "dash": "dash"},
                hovertemplate=(
                    f"<b>{target_label}</b><br>%{{y:.2f}} {unit}<extra></extra>"
                ),
                name=target_label,
            )
        )

    layout = {
        "height": height,
        "xaxis": {
            "title": "",
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "tickfont": {"size": 10},
            "tickangle": 45,
        },
        "yaxis": {
            "title": "",
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "range": [y_min, y_max],
            "tickfont": {"size": 10},
        },
        "hovermode": "x unified",
        "showlegend": False,
        "margin": dict(l=50, r=20, t=10, b=50),
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
        "font": {"size": 12},
    }

    figure = go.Figure(data=traces, layout=layout)

    return dcc.Graph(
        figure=figure,
        config={
            "displayModeBar": False,
            "staticPlot": False,
            "responsive": True,
        },
        style={"height": f"{height}px"},
    )


def format_week_label(week_label: str) -> str:

    if not week_label:
        return ""

    if "-W" in week_label:
        week_num = week_label.split("-W")[1]
    elif "-" in week_label:
        week_num = week_label.split("-")[1]
    else:
        return week_label

    return f"W{week_num}"


def get_trend_indicator(
    current_value: float | None,
    previous_value: float | None,
    higher_is_better: bool = True,
) -> dict[str, Any]:

    if current_value is None or previous_value is None or previous_value == 0:
        return {
            "direction": "stable",
            "percentage_change": 0.0,
            "is_good": True,
            "icon": "fa-minus",
            "color": "secondary",
        }

    percentage_change = ((current_value - previous_value) / previous_value) * 100

    if abs(percentage_change) < 5:
        direction = "stable"
        icon = "fa-minus"
    elif percentage_change > 0:
        direction = "up"
        icon = "fa-arrow-up"
    else:
        direction = "down"
        icon = "fa-arrow-down"

    if direction == "stable":
        is_good = True
        color = "secondary"
    elif direction == "up":
        is_good = higher_is_better
        color = "success" if is_good else "danger"
    else:
        is_good = not higher_is_better
        color = "success" if is_good else "danger"

    return {
        "direction": direction,
        "percentage_change": round(abs(percentage_change), 1),
        "is_good": is_good,
        "icon": icon,
        "color": color,
    }


def create_dual_line_trend(
    week_labels: list[str],
    deployment_values: list[float],
    release_values: list[float],
    adjusted_deployment_values: list[float] | None = None,
    height: int = 250,
    show_axes: bool = True,
    primary_color: str = "#0d6efd",
    secondary_color: str = "#28a745",
    chart_title: str = "Deployment Frequency",
) -> dcc.Graph:

    if not week_labels or not deployment_values:
        return dcc.Graph(
            figure={
                "data": [],
                "layout": {
                    "height": height,
                    "margin": {"t": 0, "r": 0, "b": 0, "l": 0},
                    "xaxis": {"visible": False},
                    "yaxis": {"visible": False},
                    "annotations": [
                        {
                            "text": "No trend data available",
                            "xref": "paper",
                            "yref": "paper",
                            "x": 0.5,
                            "y": 0.5,
                            "showarrow": False,
                            "font": {"size": 10, "color": "#999"},
                        }
                    ],
                },
            },
            config={"displayModeBar": False},
            style={"height": f"{height}px"},
        )

    traces = []

    traces.append(
        go.Scatter(
            x=week_labels,
            y=release_values,
            mode="lines+markers",
            name="Releases",
            line={"color": primary_color, "width": 3},
            marker={"size": 8, "color": primary_color},
            hovertemplate="<b>%{x}</b><br>Releases: %{y}<extra></extra>",
        )
    )

    traces.append(
        go.Scatter(
            x=week_labels,
            y=deployment_values,
            mode="lines+markers",
            name="Deployments",
            line={"color": secondary_color, "width": 2, "dash": "dot"},
            marker={"size": 6, "color": secondary_color, "symbol": "diamond"},
            hovertemplate="<b>%{x}</b><br>Deployments: %{y}<extra></extra>",
        )
    )

    if adjusted_deployment_values and len(adjusted_deployment_values) == len(
        week_labels
    ):
        traces.append(
            go.Scatter(
                x=week_labels,
                y=adjusted_deployment_values,
                mode="lines+markers",
                name="Adjusted Deployments",
                line={"color": secondary_color, "width": 2, "dash": "dash"},
                marker={"size": 5, "color": secondary_color, "symbol": "circle-open"},
                hovertemplate="<b>%{x}</b><br>Adjusted: %{y}<extra></extra>",
            )
        )

    all_values = deployment_values + release_values
    if adjusted_deployment_values:
        all_values += adjusted_deployment_values
    if all_values:
        min_val = min(all_values)
        max_val = max(all_values)
        range_padding = (max_val - min_val) * 0.2 if max_val > min_val else 1
        y_min = max(0, min_val - range_padding)
        y_max = max_val + range_padding
        y_range = [y_min, y_max]
    else:
        y_range = None

    layout = {
        "height": height,
        "margin": {
            "t": 10,
            "r": 10,
            "b": 60 if show_axes else 5,
            "l": 45 if show_axes else 5,
        },
        "xaxis": {
            "type": "category",
            "categoryorder": "array",
            "categoryarray": week_labels,
            "visible": show_axes,
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
            "tickangle": 45,
            "tickfont": {"size": 9},
            "title": "",
        },
        "yaxis": {
            "visible": show_axes,
            "showgrid": True,
            "gridcolor": "rgba(0,0,0,0.1)",
            "zeroline": False,
            "range": y_range,
            "tickfont": {"size": 10},
            "title": "",
        },
        "showlegend": True,
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 10},
        },
        "hovermode": "x unified",
        "plot_bgcolor": "white",
        "paper_bgcolor": "white",
    }

    figure = {"data": traces, "layout": layout}

    return dcc.Graph(
        figure=figure,
        config={"displayModeBar": False},
        style={"height": f"{height}px"},
        className="metric-dual-line-chart",
    )
