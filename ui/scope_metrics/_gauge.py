"""Scope Stability Gauge Component

Provides the enhanced stability gauge visualization for adaptability metrics.
"""

from typing import cast

import plotly.graph_objs as go
from dash import dcc

from configuration.chart_config import get_scope_metrics_chart_config


def create_enhanced_stability_gauge(
    stability_value, title="Scope Stability Index", height=300, show_toolbar=True
):
    """
    Create an enhanced gauge visualization for the scope stability index
    with better visual indicators.

    Args:
        stability_value (float): A value between 0 and 1 representing stability
        title (str): Title displayed above the gauge
        height (int): Height of the gauge in pixels
        show_toolbar (bool): Whether to show Plotly toolbar (default: True)

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

    # Configure chart options based on toolbar preference
    if show_toolbar:
        chart_config = get_scope_metrics_chart_config()  # type: ignore[arg-type]
    else:
        # Hide toolbar for cleaner UI on gauge charts
        chart_config = {"displayModeBar": False, "responsive": True}  # type: ignore[arg-type]

    chart_height = cast(int, getattr(figure.layout, "height", None) or height)
    return dcc.Graph(
        figure=figure,
        config=chart_config,  # type: ignore[arg-type]
        style={"height": f"{chart_height}px"},
    )
