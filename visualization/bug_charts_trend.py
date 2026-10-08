from datetime import datetime
from typing import Any

import plotly.graph_objects as go

from data.bug_processing import generate_bug_weekly_forecast


def get_mobile_chart_config(viewport_size: str = "mobile") -> dict[str, Any]:

    base_config = {
        "displayModeBar": True,
        "responsive": True,
        "scrollZoom": True,
        "doubleClick": "reset+autosize",
        "showTips": True,
        "displaylogo": False,
        "toImageButtonOptions": {
            "format": "png",
            "filename": f"burndown_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "scale": 2,
        },
    }

    if viewport_size == "mobile":
        mobile_config = {
            **base_config,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
            "toImageButtonOptions": {
                "format": "png",
                "filename": (
                    f"burndown_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ),
                "height": 400,
                "width": 600,
                "scale": 2,
            },
        }
        return mobile_config
    elif viewport_size == "tablet":
        tablet_config = {
            **base_config,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "toggleSpikelines",
            ],
        }
        return tablet_config
    else:
        return base_config


def get_mobile_chart_layout(viewport_size: str = "mobile") -> dict[str, Any]:

    if viewport_size == "mobile":
        return {
            "margin": {
                "t": 30,
                "r": 15,
                "b": 130,
                "l": 50,
            },
            "height": 450,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": -0.35,
                "xanchor": "center",
                "x": 0.5,
                "font": {"size": 10},
            },
            "xaxis": {
                "title": {"font": {"size": 10}},
                "tickfont": {"size": 9},
                "tickangle": 45,
            },
            "yaxis": {"title": {"font": {"size": 10}}, "tickfont": {"size": 9}},
            "yaxis2": {"title": {"font": {"size": 10}}, "tickfont": {"size": 9}},
        }
    elif viewport_size == "tablet":
        return {
            "margin": {
                "t": 50,
                "r": 30,
                "b": 70,
                "l": 60,
            },
            "height": 480,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
        }
    else:
        return {
            "margin": {
                "t": 80,
                "r": 60,
                "b": 80,
                "l": 60,
            },
            "height": 550,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5,
            },
        }


def get_mobile_hover_template(chart_type: str = "burndown") -> str:

    templates = {
        "burndown": ("<b>%{x}</b><br>Items: %{y}<br><extra></extra>"),
        "items": ("<b>%{x}</b><br>Completed: %{y}<br><extra></extra>"),
        "points": ("<b>%{x}</b><br>Points: %{y}<br><extra></extra>"),
        "scope": ("<b>%{x}</b><br>Scope: %{y}<br><extra></extra>"),
    }

    return templates.get(chart_type, templates["burndown"])


def apply_mobile_chart_optimizations(
    fig, viewport_size: str = "mobile", chart_type: str = "burndown"
):

    mobile_layout = get_mobile_chart_layout(viewport_size)

    fig.update_layout(**mobile_layout)

    if viewport_size == "mobile":
        fig.update_traces(
            line_width=2,
            marker_size=6,
        )

        mobile_template = get_mobile_hover_template(chart_type)
        fig.update_traces(hovertemplate=mobile_template)

        fig.update_annotations(
            font_size=9,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        )

    return fig


def create_mobile_optimized_chart(
    figure_data: dict, viewport_size: str = "mobile", chart_type: str = "burndown"
):

    if hasattr(figure_data, "update_layout"):
        optimized_fig = apply_mobile_chart_optimizations(
            figure_data, viewport_size, chart_type
        )
        return optimized_fig
    else:
        return figure_data


def create_bug_trend_chart(
    weekly_stats: list[dict],
    viewport_size: str = "mobile",
    include_forecast: bool = True,
) -> go.Figure:

    if not weekly_stats:
        fig = go.Figure()
        fig.add_annotation(
            text="No bug data available for the selected period",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="gray"),
        )
        fig.update_layout(
            title="Bug Trends: Creation vs Resolution",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    weeks = [stat["week"] for stat in weekly_stats]
    bugs_created = [stat["bugs_created"] for stat in weekly_stats]
    bugs_resolved = [stat["bugs_resolved"] for stat in weekly_stats]

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=bugs_created,
            name="Bugs Created",
            mode="lines+markers",
            line=dict(color="#dc3545", width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Created: %{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=bugs_resolved,
            name="Bugs Closed",
            mode="lines+markers",
            line=dict(color="#28a745", width=2),
            marker=dict(size=6),
            hovertemplate="<b>%{x}</b><br>Closed: %{y}<extra></extra>",
        )
    )

    if include_forecast and len(weekly_stats) >= 2:
        forecast = generate_bug_weekly_forecast(weekly_stats)

        if not forecast.get("insufficient_data", False):
            next_week = forecast["created"]["next_week"]

            created_ml = forecast["created"]["most_likely"]
            created_upper = forecast["created"]["optimistic"] - created_ml
            created_lower = created_ml - forecast["created"]["pessimistic"]

            created_range_text = (
                f"{forecast['created']['pessimistic']:.1f}-"
                f"{forecast['created']['optimistic']:.1f}"
            )
            fig.add_trace(
                go.Scatter(
                    x=[next_week],
                    y=[created_ml],
                    name="Created Forecast",
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#dc3545",
                        symbol="x",
                        line=dict(width=2, color="white"),
                    ),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[created_upper],
                        arrayminus=[created_lower],
                        color="rgba(220, 53, 69, 0.4)",
                        thickness=2,
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>Forecast Created: %{y:.1f}<br>"
                        f"Range: {created_range_text}<extra></extra>"
                    ),
                )
            )

            resolved_ml = forecast["resolved"]["most_likely"]
            resolved_upper = forecast["resolved"]["optimistic"] - resolved_ml
            resolved_lower = resolved_ml - forecast["resolved"]["pessimistic"]

            resolved_range_text = (
                f"{forecast['resolved']['pessimistic']:.1f}-"
                f"{forecast['resolved']['optimistic']:.1f}"
            )
            fig.add_trace(
                go.Scatter(
                    x=[next_week],
                    y=[resolved_ml],
                    name="Resolved Forecast",
                    mode="markers",
                    marker=dict(
                        size=10,
                        color="#28a745",
                        symbol="x",
                        line=dict(width=2, color="white"),
                    ),
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=[resolved_upper],
                        arrayminus=[resolved_lower],
                        color="rgba(40, 167, 69, 0.4)",
                        thickness=2,
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>Forecast Resolved: %{y:.1f}<br>"
                        f"Range: {resolved_range_text}<extra></extra>"
                    ),
                )
            )

            fig.add_vline(
                x=len(weeks) - 0.5,
                line_dash="dash",
                line_color="rgba(0, 0, 0, 0.25)",
                line_width=1.5,
            )

            fig.add_annotation(
                x=len(weeks) - 0.5,
                y=0.85,
                xref="x",
                yref="paper",
                text="<b>Forecast -></b>",
                showarrow=False,
                font=dict(size=10, color="rgba(0, 0, 0, 0.65)"),
                xanchor="center",
                yanchor="middle",
                bgcolor="rgba(255, 255, 255, 0.85)",
                bordercolor="rgba(0, 0, 0, 0.15)",
                borderwidth=1,
                borderpad=4,
            )

    warning_shapes = []
    consecutive_negative_weeks = 0
    warning_start_idx = None

    for idx, stat in enumerate(weekly_stats):
        if stat["bugs_created"] > stat["bugs_resolved"]:
            consecutive_negative_weeks += 1
            if consecutive_negative_weeks == 1:
                warning_start_idx = idx
        else:
            if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
                warning_shapes.append(
                    dict(
                        type="rect",
                        xref="x",
                        yref="paper",
                        x0=weeks[warning_start_idx],
                        x1=weeks[idx - 1],
                        y0=0,
                        y1=1,
                        fillcolor="rgba(255, 100, 0, 0.2)",
                        layer="below",
                        line_width=0,
                    )
                )
            consecutive_negative_weeks = 0
            warning_start_idx = None

    if consecutive_negative_weeks >= 3 and warning_start_idx is not None:
        warning_shapes.append(
            dict(
                type="rect",
                xref="x",
                yref="paper",
                x0=weeks[warning_start_idx],
                x1=weeks[-1],
                y0=0,
                y1=1,
                fillcolor="rgba(255, 100, 0, 0.2)",
                layer="below",
                line_width=0,
            )
        )

    layout_config = get_mobile_chart_layout(viewport_size)

    layout_config_clean = {
        k: v for k, v in layout_config.items() if k not in ["xaxis", "yaxis", "yaxis2"]
    }

    if "margin" in layout_config_clean:
        layout_config_clean["margin"]["t"] = max(
            layout_config_clean["margin"].get("t", 50), 50
        )

    fig.update_layout(
        title="Bug Trends: Creation vs Resolution",
        xaxis=dict(
            title="Week",
            tickangle=45 if viewport_size == "mobile" else 0,
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        yaxis=dict(
            title="Bug Count",
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        shapes=warning_shapes,
        hovermode="x unified",
        template="plotly_white",
        **layout_config_clean,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h" if viewport_size == "mobile" else "v",
            yanchor="bottom",
            y=-0.35 if viewport_size == "mobile" else 0.5,
            xanchor="left" if viewport_size == "mobile" else "left",
            x=0 if viewport_size == "mobile" else 1.02,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    return fig
