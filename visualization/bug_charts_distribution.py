import plotly.graph_objects as go

from data.bug_processing import generate_bug_weekly_forecast
from visualization.bug_charts_trend import get_mobile_chart_layout


def create_bug_investment_chart(
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
            title="Bug Investment: Items vs Points",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig

    weeks = [stat["week"] for stat in weekly_stats]
    bugs_created = [stat["bugs_created"] for stat in weekly_stats]
    bugs_resolved = [stat["bugs_resolved"] for stat in weekly_stats]
    points_created = [stat["bugs_points_created"] for stat in weekly_stats]
    points_resolved = [stat["bugs_points_resolved"] for stat in weekly_stats]

    fig = go.Figure()

    bugs_resolved_negative = [-x for x in bugs_resolved]
    points_resolved_negative = [-x for x in points_resolved]

    bugs_max = max(
        max(bugs_created) if bugs_created else 1,
        max(bugs_resolved) if bugs_resolved else 1,
    )
    points_max = max(
        max(points_created) if points_created else 1,
        max(points_resolved) if points_resolved else 1,
    )
    scale_factor = bugs_max / points_max if points_max > 0 else 1

    points_created_scaled = [p * scale_factor for p in points_created]
    points_resolved_negative_scaled = [
        p * scale_factor for p in points_resolved_negative
    ]

    fig.add_trace(
        go.Bar(
            x=weeks,
            y=bugs_created,
            name="Bugs Created",
            marker=dict(color="rgb(100, 149, 237)", opacity=0.7),
            hovertemplate="<b>%{x}</b><br>Bugs Created: %{y}<extra></extra>",
            width=0.35,
            offset=-0.2,
        ),
    )

    fig.add_trace(
        go.Bar(
            x=weeks,
            y=bugs_resolved_negative,
            name="Bugs Resolved",
            marker=dict(color="rgb(0, 99, 178)", opacity=0.9),
            hovertemplate="<b>%{x}</b><br>Bugs Resolved: %{customdata}<extra></extra>",
            customdata=bugs_resolved,
            width=0.35,
            offset=-0.2,
        ),
    )

    fig.add_trace(
        go.Bar(
            x=weeks,
            y=points_created_scaled,
            name="Points Created",
            marker=dict(color="rgb(255, 179, 102)", opacity=0.7),
            hovertemplate="<b>%{x}</b><br>Points Created: %{customdata}<extra></extra>",
            customdata=points_created,
            width=0.35,
            offset=0.2,
        ),
    )

    fig.add_trace(
        go.Bar(
            x=weeks,
            y=points_resolved_negative_scaled,
            name="Points Resolved",
            marker=dict(color="rgb(255, 127, 14)", opacity=0.9),
            hovertemplate=(
                "<b>%{x}</b><br>Points Resolved: %{customdata}<extra></extra>"
            ),
            customdata=points_resolved,
            width=0.35,
            offset=0.2,
        ),
    )

    if include_forecast and len(weekly_stats) >= 2:
        forecast = generate_bug_weekly_forecast(weekly_stats)

        if not forecast.get("insufficient_data", False):
            next_week = forecast["created"]["next_week"]

            created_ml = forecast["created"]["most_likely"]
            resolved_ml = forecast["resolved"]["most_likely"]
            resolved_ml_negative = -resolved_ml

            fig.add_trace(
                go.Bar(
                    x=[next_week],
                    y=[created_ml],
                    name="Bugs Forecast (Created)",
                    marker=dict(
                        color="rgb(100, 149, 237)",
                        opacity=0.4,
                        pattern_shape="x",
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>Forecast Bugs Created: %{y:.1f}<extra></extra>"
                    ),
                    width=0.35,
                    offset=-0.2,
                ),
            )

            fig.add_trace(
                go.Bar(
                    x=[next_week],
                    y=[resolved_ml_negative],
                    name="Bugs Forecast (Resolved)",
                    marker=dict(
                        color="rgb(0, 99, 178)",
                        opacity=0.4,
                        pattern_shape="x",
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>Forecast Bugs Resolved: "
                        "%{customdata:.1f}<extra></extra>"
                    ),
                    customdata=[resolved_ml],
                    width=0.35,
                    offset=-0.2,
                ),
            )

            if "created_points" in forecast:
                created_points_ml = forecast["created_points"]["most_likely"]
                resolved_points_ml = forecast["resolved_points"]["most_likely"]
                resolved_points_ml_negative = -resolved_points_ml

                created_points_ml_scaled = created_points_ml * scale_factor
                resolved_points_ml_negative_scaled = (
                    resolved_points_ml_negative * scale_factor
                )

                fig.add_trace(
                    go.Bar(
                        x=[next_week],
                        y=[created_points_ml_scaled],
                        name="Points Forecast (Created)",
                        marker=dict(
                            color="rgb(255, 179, 102)",
                            opacity=0.4,
                            pattern_shape="x",
                        ),
                        hovertemplate=(
                            "<b>%{x}</b><br>Forecast Points Created: "
                            "%{customdata:.1f}<extra></extra>"
                        ),
                        customdata=[created_points_ml],
                        width=0.35,
                        offset=0.2,
                    ),
                )

                fig.add_trace(
                    go.Bar(
                        x=[next_week],
                        y=[resolved_points_ml_negative_scaled],
                        name="Points Forecast (Resolved)",
                        marker=dict(
                            color="rgb(255, 127, 14)",
                            opacity=0.4,
                            pattern_shape="x",
                        ),
                        hovertemplate=(
                            "<b>%{x}</b><br>Forecast Points Resolved: "
                            "%{customdata:.1f}<extra></extra>"
                        ),
                        customdata=[resolved_points_ml],
                        width=0.35,
                        offset=0.2,
                    ),
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
                text="<b>Forecast \u2192</b>",
                showarrow=False,
                font=dict(size=10, color="rgba(0, 0, 0, 0.65)"),
                xanchor="center",
                yanchor="middle",
                bgcolor="rgba(255, 255, 255, 0.85)",
                bordercolor="rgba(0, 0, 0, 0.15)",
                borderwidth=1,
                borderpad=4,
            )

    layout_config = get_mobile_chart_layout(viewport_size)

    layout_config_clean = {
        k: v for k, v in layout_config.items() if k not in ["xaxis", "yaxis", "yaxis2"]
    }

    if "margin" in layout_config_clean:
        layout_config_clean["margin"]["t"] = max(
            layout_config_clean["margin"].get("t", 50), 50
        )

    all_values = (
        bugs_created
        + [abs(x) for x in bugs_resolved_negative]
        + points_created_scaled
        + [abs(x) for x in points_resolved_negative_scaled]
    )
    max_value = max(all_values) if all_values else 1
    max_padded = max_value * 1.15

    fig.update_yaxes(
        title_text=f"Bug Count (Points scaled {scale_factor:.1f}x)",
        tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        range=[-max_padded, max_padded],
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor="rgba(0,0,0,0.3)",
    )

    if "margin" in layout_config_clean:
        layout_config_clean["margin"]["b"] = 130

    fig.update_layout(
        title="Bug Investment: Count vs Points (+ Created, - Resolved)",
        xaxis=dict(
            title="Week",
            tickangle=45 if viewport_size == "mobile" else 0,
            tickfont=dict(size=10 if viewport_size == "mobile" else 12),
        ),
        hovermode="x unified",
        template="plotly_white",
        **layout_config_clean,
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.35,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="rgba(0,0,0,0.1)",
            borderwidth=1,
        ),
    )

    return fig
