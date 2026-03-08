"""Forecast Analytics - Chart Generation and Forecast History.

Provides historical forecast data retrieval and trend visualization
chart builders for the forecast analytics dashboard section.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.style_constants import COLOR_PALETTE


def get_forecast_history() -> tuple[list, list, list]:
    """Get historical forecast data for trend visualization.

    Returns:
        Tuple of (dates, items_forecasts, points_forecasts) lists
    """
    try:
        from data.persistence import load_unified_project_data

        unified_data = load_unified_project_data()
        forecast_history = unified_data.get("forecast_history", [])

        # Extract data for plotting (last 10 data points)
        dates = []
        items_forecasts = []
        points_forecasts = []

        for entry in forecast_history[-10:]:
            dates.append(entry.get("date", ""))
            items_forecasts.append(entry.get("items_forecast_date", ""))
            points_forecasts.append(entry.get("points_forecast_date", ""))

        return dates, items_forecasts, points_forecasts
    except Exception:
        return [], [], []


def _build_forecast_trend_chart(
    history_dates: list,
    history_items: list,
    history_points: list,
    show_points: bool,
) -> dbc.Card | None:
    """Build forecast evolution trend chart card.

    Args:
        history_dates: List of calculation date strings
        history_items: List of items-based forecast dates
        history_points: List of points-based forecast dates
        show_points: Whether to render the points track

    Returns:
        dbc.Card containing the chart, or None if insufficient data
    """
    if not history_dates or len(history_dates) < 2:
        return None

    import plotly.graph_objects as go

    fig = go.Figure()

    if history_items:
        fig.add_trace(
            go.Scatter(
                x=history_dates,
                y=history_items,
                mode="lines+markers",
                name="Items-based Forecast",
                line=dict(color=COLOR_PALETTE["items"], width=3),
                marker=dict(size=8, symbol="circle"),
            )
        )

    if history_points and show_points:
        fig.add_trace(
            go.Scatter(
                x=history_dates,
                y=history_points,
                mode="lines+markers",
                name="Points-based Forecast",
                line=dict(color=COLOR_PALETTE["points"], width=3, dash="dot"),
                marker=dict(size=8, symbol="diamond"),
            )
        )

    fig.update_layout(
        title=dict(
            text="Forecast Evolution Over Time",
            font=dict(size=14, color="#495057"),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title="Calculation Date",
            showgrid=True,
            gridcolor="#e9ecef",
        ),
        yaxis=dict(
            title="Predicted Completion Date",
            showgrid=True,
            gridcolor="#e9ecef",
        ),
        hovermode="x unified",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=300,
        margin=dict(l=60, r=40, t=50, b=60),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return dbc.Card(
        dbc.CardBody(
            [
                dcc.Graph(
                    figure=fig,
                    config={"displayModeBar": False},
                    style={"height": "300px"},
                ),
                html.Div(
                    html.Small(
                        "Historical trend showing how forecast dates "
                        "change as the project progresses",
                        className="text-muted",
                    ),
                    className="text-center mt-2",
                ),
            ]
        ),
        className="metric-card mb-3",
    )
