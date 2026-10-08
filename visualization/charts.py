from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from plotly.subplots import make_subplots

from configuration import COLOR_PALETTE
from utils.chart_tooltip_utils import create_hoverlabel_config, format_hover_template
from utils.loading_overlay_utils import create_loading_overlay


def create_capacity_chart(capacity_data, forecast_data, settings):

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    dates = [
        pd.to_datetime(date, format="mixed", errors="coerce")
        for date in forecast_data.get("dates", [])
    ]

    if not dates:
        fig.add_annotation(
            text="No forecast data available.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        return fig

    team_capacity = capacity_data.get("weekly_capacity", 0)
    capacity_line = [team_capacity] * len(dates)

    forecasted_items = forecast_data.get("forecasted_items", [])
    forecasted_points = forecast_data.get("forecasted_points", [])

    hours_per_item = capacity_data.get("avg_hours_per_item", 0)
    hours_per_point = capacity_data.get("avg_hours_per_point", 0)

    items_hours = [items * hours_per_item for items in forecasted_items]
    points_hours = [points * hours_per_point for points in forecasted_points]

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=capacity_line,
            mode="lines",
            name="Team Capacity",
            line=dict(color="rgba(0, 200, 0, 0.8)", width=2, dash="dash"),
            hovertemplate=format_hover_template(
                title="Team Capacity",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_hours,
            mode="lines",
            name="Required (Items)",
            line=dict(color=COLOR_PALETTE["items"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Items Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_hours,
            mode="lines",
            name="Required (Points)",
            line=dict(color=COLOR_PALETTE["points"], width=2),
            fill="tozeroy",
            hovertemplate=format_hover_template(
                title="Points Work Hours",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Hours": "%{y:.1f}",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=False,
    )

    max_utilization = (
        max(
            max(items_hours + [0.1]) / team_capacity if team_capacity else 1,
            max(points_hours + [0.1]) / team_capacity if team_capacity else 1,
            1,
        )
        * 100
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[100] * len(dates),
            mode="lines",
            name="100% Utilization",
            line=dict(color="rgba(255, 165, 0, 0.8)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Threshold",
                fields={
                    "Threshold": "100%",
                },
            ),
            hoverlabel=create_hoverlabel_config("warning"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=[85] * len(dates),
            mode="lines",
            name="85% Target Utilization",
            line=dict(color="rgba(0, 128, 0, 0.6)", width=1.5, dash="dot"),
            hovertemplate=format_hover_template(
                title="Utilization Target",
                fields={
                    "Target": "85%",
                },
            ),
            hoverlabel=create_hoverlabel_config("success"),
        ),
        secondary_y=True,
    )

    items_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in items_hours
    ]
    points_utilization = [
        (hours / team_capacity * 100) if team_capacity else 0 for hours in points_hours
    ]

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=items_utilization,
            mode="lines",
            name="Items Utilization %",
            line=dict(color=COLOR_PALETTE["items"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Items Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=dates,
            y=points_utilization,
            mode="lines",
            name="Points Utilization %",
            line=dict(color=COLOR_PALETTE["points"], width=1.5),
            visible=True,
            hovertemplate=format_hover_template(
                title="Points Utilization",
                fields={
                    "Date": "%{x|%Y-%m-%d}",
                    "Utilization": "%{y:.1f}%",
                },
            ),
            hoverlabel=create_hoverlabel_config("info"),
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="Team Capacity vs. Forecasted Work",
        xaxis_title="Date",
        yaxis_title="Hours per Week",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        hovermode="x unified",
        margin=dict(l=60, r=60, t=50, b=50),
        hoverlabel=dict(font_size=14),
    )

    fig.update_yaxes(title_text="Hours per Week", secondary_y=False)

    fig.update_yaxes(
        title_text="Utilization (%)",
        secondary_y=True,
        range=[
            0,
            max(max_utilization * 1.1, 110),
        ],
    )

    return fig


def create_chart_with_loading(
    id, figure=None, loading_state=None, type="default", height=None
):

    is_loading = loading_state is not None and loading_state.get("is_loading", False)

    loading_messages = {
        "default": "Loading chart...",
        "bar": "Generating bar chart...",
        "line": "Preparing line chart...",
        "scatter": "Creating scatter plot...",
        "pie": "Building pie chart...",
        "area": "Creating area chart...",
    }
    message = loading_messages.get(type, "Loading chart...")

    chart = dcc.Graph(
        id=id,
        figure=figure or {},
        config={
            "displayModeBar": True,
            "responsive": True,
            "toImageButtonOptions": {
                "format": "png",
                "filename": (
                    f"{id.replace('-', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ),
                "scale": 2,
            },
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        },
        style={"height": height or "100%", "width": "100%"},
    )

    return create_loading_overlay(
        children=chart,
        style_key="primary",
        size_key="lg",
        text=message,
        is_loading=is_loading,
        opacity=0.7,
        className=f"{id}-loading-wrapper",
    )


def format_hover_template_fix(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):

    template = []

    if title:
        template.append(f"<b>{title}</b><br>")

    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    hover_text = "".join(template)

    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


def _create_forecast_axes_titles(fig, forecast_data):

    fig.update_xaxes(
        title={"text": "Date", "font": {"size": 16}},
    )

    fig.update_yaxes(
        title={"text": "Remaining Items", "font": {"size": 16}},
        secondary_y=False,
    )

    fig.update_yaxes(
        title={"text": "Remaining Points", "font": {"size": 16}},
        secondary_y=True,
    )

    return fig


def _calculate_forecast_completion_dates(pert_time_items, pert_time_points):

    import math  # noqa: PLC0415

    if pert_time_items is None or (
        isinstance(pert_time_items, float) and math.isnan(pert_time_items)
    ):
        items_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        items_completion_date = current_date + timedelta(days=pert_time_items)
        items_completion_str = items_completion_date.strftime("%Y-%m-%d")
        items_completion_enhanced = (
            f"{items_completion_str} ({pert_time_items:.1f} days, "
            f"{pert_time_items / 7:.1f} weeks)"
        )

    if pert_time_points is None or (
        isinstance(pert_time_points, float) and math.isnan(pert_time_points)
    ):
        points_completion_enhanced = "N/A (insufficient data)"
    else:
        current_date = datetime.now()
        points_completion_date = current_date + timedelta(days=pert_time_points)
        points_completion_str = points_completion_date.strftime("%Y-%m-%d")
        points_completion_enhanced = (
            f"{points_completion_str} ({pert_time_points:.1f} days, "
            f"{pert_time_points / 7:.1f} weeks)"
        )

    return items_completion_enhanced, points_completion_enhanced


def _prepare_metrics_data(
    total_items,
    total_points,
    deadline,
    pert_time_items,
    pert_time_points,
    data_points_count,
    df,
    items_completion_enhanced,
    points_completion_enhanced,
    avg_weekly_items=0.0,
    avg_weekly_points=0.0,
    med_weekly_items=0.0,
    med_weekly_points=0.0,
):

    current_date = datetime.now()

    if pd.isna(deadline):
        days_to_deadline = 0
        deadline_str = "No deadline set"
    else:
        days_to_deadline = max(0, (deadline - pd.Timestamp(current_date)).days)
        deadline_str = deadline.strftime("%Y-%m-%d")

    completed_items = 0
    completed_points = 0

    if (
        not df.empty
        and "completed_items" in df.columns
        and "completed_points" in df.columns
    ):
        completed_items = (
            df["completed_items"].sum() if "completed_items" in df.columns else 0
        )
        completed_points = (
            df["completed_points"].sum() if "completed_points" in df.columns else 0
        )

    total_scope_items = completed_items + total_items
    total_scope_points = completed_points + total_points

    items_percent_complete = 0
    points_percent_complete = 0

    if total_scope_items > 0:
        items_percent_complete = (completed_items / total_scope_items) * 100

    if total_scope_points > 0:
        points_percent_complete = (completed_points / total_scope_points) * 100

    return {
        "total_items": total_items,
        "total_points": total_points,
        "total_scope_items": total_scope_items,
        "total_scope_points": total_scope_points,
        "completed_items": completed_items,
        "completed_points": completed_points,
        "items_percent_complete": items_percent_complete,
        "points_percent_complete": points_percent_complete,
        "deadline": deadline_str,
        "days_to_deadline": days_to_deadline,
        "pert_time_items": pert_time_items,
        "pert_time_points": pert_time_points,
        "avg_weekly_items": round(float(avg_weekly_items), 2),
        "avg_weekly_points": round(float(avg_weekly_points), 2),
        "med_weekly_items": round(float(med_weekly_items), 2),
        "med_weekly_points": round(float(med_weekly_points), 2),
        "avg_weekly_items_str": f"{float(avg_weekly_items):.2f}",
        "avg_weekly_points_str": f"{float(avg_weekly_points):.2f}",
        "med_weekly_items_str": f"{float(med_weekly_items):.2f}",
        "med_weekly_points_str": f"{float(med_weekly_points):.2f}",
        "data_points_used": int(data_points_count)
        if data_points_count is not None and isinstance(data_points_count, (int, float))
        else (len(df) if hasattr(df, "__len__") else 0),
        "data_points_available": len(df) if hasattr(df, "__len__") else 0,
        "items_completion_enhanced": items_completion_enhanced,
        "points_completion_enhanced": points_completion_enhanced,
    }


def create_pert_timeline_chart(pert_data: dict) -> go.Figure:

    try:
        optimistic = (
            datetime.strptime(pert_data["optimistic_date"], "%Y-%m-%d")
            if pert_data.get("optimistic_date")
            else None
        )
        most_likely = (
            datetime.strptime(pert_data["most_likely_date"], "%Y-%m-%d")
            if pert_data.get("most_likely_date")
            else None
        )
        pessimistic = (
            datetime.strptime(pert_data["pessimistic_date"], "%Y-%m-%d")
            if pert_data.get("pessimistic_date")
            else None
        )
        pert_estimate = (
            datetime.strptime(pert_data["pert_estimate_date"], "%Y-%m-%d")
            if pert_data.get("pert_estimate_date")
            else None
        )
    except ValueError, TypeError:
        fig = go.Figure()
        fig.add_annotation(
            text="No forecast data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    if not all([optimistic, most_likely, pessimistic, pert_estimate]):
        fig = go.Figure()
        fig.add_annotation(
            text="Insufficient data for timeline forecast",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="gray"),
        )
        return fig

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[optimistic, pessimistic],
            y=[0, 0],
            mode="lines",
            line=dict(color="rgba(13, 110, 253, 0.2)", width=20),
            name="Confidence Range",
            showlegend=True,
            hovertemplate="Range: %{x}<extra></extra>",
        )
    )

    scenarios = [
        (optimistic, "Optimistic", "green", "circle"),
        (most_likely, "Most Likely", "blue", "diamond"),
        (pert_estimate, "PERT Estimate", "purple", "star"),
        (pessimistic, "Pessimistic", "orange", "circle"),
    ]

    for date, label, color, symbol in scenarios:
        fig.add_trace(
            go.Scatter(
                x=[date],
                y=[0],
                mode="markers+text",
                marker=dict(
                    size=15,
                    color=color,
                    symbol=symbol,
                    line=dict(width=2, color="white"),
                ),
                text=[label],
                textposition="top center",
                name=label,
                showlegend=True,
                hovertemplate=(
                    f"<b>{label}</b><br>Date: %{{x|%Y-%m-%d}}<br>Days: "
                    f"{pert_data.get(label.lower().replace(' ', '_') + '_days', 'N/A')}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="PERT Timeline Forecast",
        xaxis=dict(
            title="Completion Date",
            type="date",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.1)",
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-0.5, 0.5],
        ),
        height=300,
        hovermode="closest",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=60, b=60),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


def get_mobile_chart_config(is_mobile=False, is_tablet=False):

    if is_mobile:
        return {
            "displayModeBar": True,
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "showTips": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        }
    elif is_tablet:
        return {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }
    else:
        return {
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
            "responsive": True,
            "scrollZoom": True,
            "doubleClick": "reset+autosize",
            "displaylogo": False,
        }


def get_mobile_chart_layout(
    is_mobile=False, is_tablet=False, show_legend=True, title=None
):

    if is_mobile:
        return {
            "margin": dict(l=40, r=10, t=30 if title else 10, b=40),
            "showlegend": False,
            "font": dict(size=10),
            "title": dict(
                text=title if title else None,
                font=dict(size=14),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "height": 300,
            "hovermode": "closest",
        }
    elif is_tablet:
        return {
            "margin": dict(
                l=50, r=20, t=50 if title else 20, b=80 if show_legend else 50
            ),
            "showlegend": show_legend,
            "font": dict(size=12),
            "title": dict(
                text=title if title else None,
                font=dict(size=16),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            )
            if show_legend
            else None,
            "height": 400,
            "hovermode": "x unified",
        }
    else:
        return {
            "margin": dict(
                l=60, r=30, t=80 if title else 30, b=100 if show_legend else 60
            ),
            "showlegend": show_legend,
            "font": dict(size=13),
            "title": dict(
                text=title if title else None,
                font=dict(size=18),
                x=0.5,
                xanchor="center",
            )
            if title
            else None,
            "legend": dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="right",
                x=1.15,
            )
            if show_legend
            else None,
            "height": 500,
            "hovermode": "x unified",
        }


def apply_mobile_optimization(fig, is_mobile=False, is_tablet=False, title=None):

    layout_updates = get_mobile_chart_layout(
        is_mobile=is_mobile, is_tablet=is_tablet, show_legend=not is_mobile, title=title
    )

    fig.update_layout(**layout_updates)

    config = get_mobile_chart_config(is_mobile=is_mobile, is_tablet=is_tablet)

    return fig, config
