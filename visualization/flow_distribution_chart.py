"""Flow Work Distribution chart visualization.

Creates stacked bar chart showing distribution of work across Flow item types over time.
"""

import plotly.graph_objects as go
from typing import List, Dict, Any


def create_work_distribution_chart(
    distribution_history: List[Dict[str, Any]],
) -> go.Figure:
    """Create stacked bar chart showing work distribution over time.

    Args:
        distribution_history: List of weekly distribution data
            [{"week": "2025-W34", "feature": 5, "defect": 3, "tech_debt": 2, "risk": 0, "total": 10}, ...]

    Returns:
        Plotly Figure with stacked bar chart
    """
    fig = go.Figure()

    # Colors: slightly more vibrant and brighter for better visibility
    # Using brighter RGB values with 0.65 opacity for good balance
    trace_configs = [
        (
            "Feature",
            "feature",
            "rgba(24, 128, 80, 0.65)",
            "40-60%",
        ),  # Brighter green
        (
            "Defect",
            "defect",
            "rgba(210, 50, 65, 0.65)",
            "20-40%",
        ),  # Brighter red
        (
            "Tech Debt",
            "tech_debt",
            "rgba(245, 120, 19, 0.65)",
            "10-20%",
        ),  # Brighter orange
        (
            "Risk",
            "risk",
            "rgba(245, 185, 7, 0.65)",
            "0-10%",
        ),  # Brighter yellow
    ]

    for trace_name, field_key, color, target_range in trace_configs:
        # Calculate percentages for hover
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
                hovertemplate=f"<b>{trace_name}</b><br>%{{y:.1f}}% (%{{customdata}} items)<br><i>Target: {target_range}</i><extra></extra>",
            )
        )

    fig.update_layout(
        # No title - removed for cleaner look
        barmode="stack",
        bargap=0.05,  # Minimal gap to make bars wider with less white space
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
            tickangle=-45,
            tickfont=dict(size=9),
            title=None,  # No x-axis label
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,0,0,0.05)",
            range=[0, 100],
            title=None,  # No y-axis label
        ),
    )

    return fig
