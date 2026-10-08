from typing import Any

import plotly.graph_objects as go


def create_work_distribution_chart(
    distribution_history: list[dict[str, Any]],
) -> go.Figure:

    fig = go.Figure()

    trace_configs = [
        (
            "Feature",
            "feature",
            "rgba(24, 128, 80, 0.65)",
            "40-60%",
        ),
        (
            "Defect",
            "defect",
            "rgba(210, 50, 65, 0.65)",
            "20-40%",
        ),
        (
            "Tech Debt",
            "tech_debt",
            "rgba(245, 120, 19, 0.65)",
            "10-20%",
        ),
        (
            "Risk",
            "risk",
            "rgba(245, 185, 7, 0.65)",
            "0-10%",
        ),
    ]

    for trace_name, field_key, color, target_range in trace_configs:
        percentages = []
        counts = []
        for week_data in distribution_history:
            week_total = week_data["total"]
            count = week_data[field_key]
            pct = (count / week_total * 100) if week_total > 0 else 0
            percentages.append(pct)
            counts.append(count)

        fig.add_trace(
            go.Bar(
                x=[d["week"] for d in distribution_history],
                y=percentages,
                name=trace_name,
                marker=dict(
                    color=color,
                    line=dict(color="white", width=0.5),
                ),
                customdata=counts,
                hovertemplate=(
                    f"<b>{trace_name}</b><br>%{{y:.1f}}% "
                    f"(%{{customdata}} items)<br>"
                    f"<i>Target: {target_range}</i><extra></extra>"
                ),
            )
        )

    fig.update_layout(
        barmode="stack",
        bargap=0.05,
        hovermode="x unified",
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=[d["week"] for d in distribution_history],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            tickangle=45,
            tickfont=dict(size=9),
            title=None,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            range=[0, 100],
            title=None,
        ),
    )

    return fig
