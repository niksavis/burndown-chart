"""Forecast chart trace builders.

Creates all Plotly scatter traces for the cumulative forecast chart:
historical items/points, forecast lines (avg/EWMA/optimistic/pessimistic).
Part of visualization/forecast_chart.py split.
"""

import plotly.graph_objects as go

from configuration import COLOR_PALETTE
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template


def create_plot_traces(
    forecast_data, show_forecast=True, forecast_visibility=True, show_points=True
):
    """
    Create all the traces for the plot.

    Args:
        forecast_data: Dictionary of forecast data from prepare_forecast_data
        show_forecast: Whether to show forecast lines (default: True)
        forecast_visibility: Visibility mode for forecast traces
            - True, False, or "legendonly" (default: "legendonly")
        show_points: Whether points tracking is enabled (default: True)

    Returns:
        List of traces for Plotly figure
    """
    df_calc = forecast_data["df_calc"]
    items_forecasts = forecast_data["items_forecasts"]
    points_forecasts = forecast_data["points_forecasts"]

    traces = []

    # Historical items trace - enhanced markers
    traces.append(
        {
            "data": go.Scatter(
                x=df_calc["date"],
                y=df_calc["cum_items"],
                mode="lines+markers",
                name="Items History",
                line=dict(color=COLOR_PALETTE["items"], width=3),
                marker=dict(
                    size=10,
                    color=COLOR_PALETTE["items"],
                    symbol="circle",
                    line=dict(width=2, color="white"),
                ),
                hovertemplate=format_hover_template(
                    title="Items History",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y}",
                    },
                    extra_info="Items",
                ),
                hoverlabel=create_hoverlabel_config("default"),
            ),
            "secondary_y": False,
        }
    )

    # Items forecast traces - improved line visibility
    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["avg"][0],
                y=items_forecasts["avg"][1],
                mode="lines+markers",  # Added markers for better visibility
                name="Items Forecast (Most Likely)",
                line=dict(
                    color=COLOR_PALETTE["items"], dash="dash", width=3
                ),  # Increased width
                marker=dict(
                    size=8,
                    symbol="diamond",
                    color=COLOR_PALETTE["items"],
                    line=dict(color="white", width=1),
                ),
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Most Likely",
                    },
                ),
                hoverlabel=create_hoverlabel_config("info"),
                visible=True,
            ),
            "secondary_y": False,
        }
    )

    if items_forecasts.get("ewma", ([], []))[0]:
        traces.append(
            {
                "data": go.Scatter(
                    x=items_forecasts["ewma"][0],
                    y=items_forecasts["ewma"][1],
                    mode="lines+markers",
                    name="Items Forecast (EWMA)",
                    line=dict(color="#6b7c93", dash="dashdot", width=2.0),
                    marker=dict(
                        size=7,
                        symbol="diamond",
                        color="#6b7c93",
                        line=dict(color="white", width=1),
                    ),
                    hovertemplate=format_hover_template(
                        title="Items Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Items": "%{y:.1f}",
                            "Type": "EWMA",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                    visible=True,
                ),
                "secondary_y": False,
            }
        )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["opt"][0],
                y=items_forecasts["opt"][1],
                mode="lines+markers",  # Added markers
                name="Items Forecast (Optimistic)",
                line=dict(color=COLOR_PALETTE["optimistic"], dash="dot", width=2.5),
                marker=dict(
                    size=7,
                    symbol="triangle-up",
                    color=COLOR_PALETTE["optimistic"],
                    line=dict(color="white", width=1),
                ),
                visible=True,
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Optimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("success"),
            ),
            "secondary_y": False,
        }
    )

    traces.append(
        {
            "data": go.Scatter(
                x=items_forecasts["pes"][0],
                y=items_forecasts["pes"][1],
                mode="lines+markers",  # Added markers
                name="Items Forecast (Pessimistic)",
                line=dict(color=COLOR_PALETTE["pessimistic"], dash="dot", width=2.5),
                marker=dict(
                    size=7,
                    symbol="triangle-down",
                    color=COLOR_PALETTE["pessimistic"],
                    line=dict(color="white", width=1),
                ),
                visible=True,
                hovertemplate=format_hover_template(
                    title="Items Forecast",
                    fields={
                        "Date": "%{x|%Y-%m-%d}",
                        "Items": "%{y:.1f}",
                        "Type": "Pessimistic",
                    },
                ),
                hoverlabel=create_hoverlabel_config("warning"),
            ),
            "secondary_y": False,
        }
    )

    # Only add points traces if points tracking is enabled
    if show_points:
        # Historical points trace - enhanced markers
        traces.append(
            {
                "data": go.Scatter(
                    x=df_calc["date"],
                    y=df_calc["cum_points"],
                    mode="lines+markers",
                    name="Points History",
                    line=dict(color=COLOR_PALETTE["points"], width=3),
                    marker=dict(
                        size=10,
                        color=COLOR_PALETTE["points"],
                        symbol="circle",
                        line=dict(width=2, color="white"),
                    ),
                    hovertemplate=format_hover_template(
                        title="Points History",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y}",
                        },
                        extra_info="Points",
                    ),
                    hoverlabel=create_hoverlabel_config("default"),
                ),
                "secondary_y": True,
            }
        )

        # Points forecast traces - improving visibility
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["avg"][0],
                    y=points_forecasts["avg"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Most Likely)",
                    line=dict(
                        color=COLOR_PALETTE["points"], dash="dash", width=3
                    ),  # Increased width
                    marker=dict(
                        size=8,
                        symbol="diamond",
                        color=COLOR_PALETTE["points"],
                        line=dict(color="white", width=1),
                    ),
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Most Likely",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("info"),
                    visible=True,
                ),
                "secondary_y": True,
            }
        )

        if points_forecasts.get("ewma", ([], []))[0]:
            traces.append(
                {
                    "data": go.Scatter(
                        x=points_forecasts["ewma"][0],
                        y=points_forecasts["ewma"][1],
                        mode="lines+markers",
                        name="Points Forecast (EWMA)",
                        line=dict(color="#8a6d3b", dash="dashdot", width=2.0),
                        marker=dict(
                            size=7,
                            symbol="diamond",
                            color="#8a6d3b",
                            line=dict(color="white", width=1),
                        ),
                        hovertemplate=format_hover_template(
                            title="Points Forecast",
                            fields={
                                "Date": "%{x|%Y-%m-%d}",
                                "Points": "%{y:.1f}",
                                "Type": "EWMA",
                            },
                        ),
                        hoverlabel=create_hoverlabel_config("info"),
                        visible=True,
                    ),
                    "secondary_y": True,
                }
            )

        # Use gold color for optimistic points forecast (matching info card description)
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["opt"][0],
                    y=points_forecasts["opt"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Optimistic)",
                    line=dict(
                        color="rgb(184, 134, 11)", dash="dot", width=2.5
                    ),  # Gold color for optimistic points
                    marker=dict(
                        size=7,
                        symbol="triangle-up",
                        color="rgb(184, 134, 11)",  # Gold color for marker
                        line=dict(color="white", width=1),
                    ),
                    visible=True,
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Optimistic",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("success"),
                ),
                "secondary_y": True,
            }
        )

        # Use brown color for pessimistic points forecast
        # (matching info card description)
        traces.append(
            {
                "data": go.Scatter(
                    x=points_forecasts["pes"][0],
                    y=points_forecasts["pes"][1],
                    mode="lines+markers",  # Added markers
                    name="Points Forecast (Pessimistic)",
                    line=dict(
                        color="rgb(165, 42, 42)", dash="dot", width=2.5
                    ),  # Brown color for pessimistic points
                    marker=dict(
                        size=7,
                        symbol="triangle-down",
                        color="rgb(165, 42, 42)",  # Brown color for marker
                        line=dict(color="white", width=1),
                    ),
                    visible=True,
                    hovertemplate=format_hover_template(
                        title="Points Forecast",
                        fields={
                            "Date": "%{x|%Y-%m-%d}",
                            "Points": "%{y:.1f}",
                            "Type": "Pessimistic",
                        },
                    ),
                    hoverlabel=create_hoverlabel_config("warning"),
                ),
                "secondary_y": True,
            }
        )

    return traces
