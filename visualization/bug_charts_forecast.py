"""
Bug Charts Forecast Module

Bug resolution forecast chart with confidence intervals showing
optimistic, most-likely, and pessimistic completion scenarios.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from typing import Any

# Third-party library imports
import plotly.graph_objects as go

#######################################################################
# BUG FORECAST CHART
#######################################################################


def create_bug_forecast_chart(
    forecast: dict[str, Any], viewport_size: str = "mobile"
) -> go.Figure:
    """
    Create bug resolution forecast chart with confidence intervals.

    Implements T098: Mobile-optimized forecast visualization showing
    optimistic/most_likely/pessimistic completion estimates.

    Args:
        forecast: Bug forecast dictionary from forecast_bug_resolution()
        viewport_size: "mobile", "tablet", or "desktop"

    Returns:
        Plotly figure with forecast timeline and confidence intervals
    """
    fig = go.Figure()

    # Check if forecast is valid
    if forecast.get("insufficient_data") or forecast.get("most_likely_weeks") is None:
        # Show empty state with message
        fig.add_annotation(
            text=(
                "Insufficient data to generate forecast<br>"
                "Need at least 4 weeks of history with bug resolutions"
            ),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14 if viewport_size == "mobile" else 16, color="#666"),
            align="center",
        )

        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=300 if viewport_size == "mobile" else 400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        return fig

    # Extract forecast data
    optimistic_weeks = forecast["optimistic_weeks"]
    most_likely_weeks = forecast["most_likely_weeks"]
    pessimistic_weeks = forecast["pessimistic_weeks"]

    optimistic_date = forecast.get("optimistic_date")
    most_likely_date = forecast.get("most_likely_date")
    pessimistic_date = forecast.get("pessimistic_date")

    # Create timeline data
    scenarios = ["Optimistic", "Most Likely", "Pessimistic"]
    weeks = [optimistic_weeks, most_likely_weeks, pessimistic_weeks]
    dates = [optimistic_date, most_likely_date, pessimistic_date]
    colors = ["#28a745", "#007bff", "#ffc107"]

    # Add bar chart for weeks
    fig.add_trace(
        go.Bar(
            x=scenarios,
            y=weeks,
            text=[f"{w} weeks" for w in weeks],
            textposition="outside",
            marker=dict(color=colors, opacity=0.8),
            hovertemplate="<b>%{x}</b><br>"
            + "Completion: %{customdata}<br>"
            + "Weeks: %{y}<br>"
            + "<extra></extra>",
            customdata=dates,
            name="Forecast",
        )
    )

    # Add confidence interval shading
    if pessimistic_weeks and optimistic_weeks:
        fig.add_shape(
            type="rect",
            x0=-0.5,
            x1=2.5,
            y0=optimistic_weeks,
            y1=pessimistic_weeks,
            fillcolor="rgba(0,123,255,0.1)",
            line=dict(width=0),
            layer="below",
        )

    # Configure layout
    height = 350 if viewport_size == "mobile" else 450
    font_size = 11 if viewport_size == "mobile" else 13

    fig.update_layout(
        title=dict(
            text=(
                "Bug Resolution Forecast<br><sub>Based on "
                f"{forecast.get('open_bugs', 0)} open bugs</sub>"
            ),
            font=dict(size=14 if viewport_size == "mobile" else 18),
            x=0.5,
            xanchor="center",
        ),
        xaxis=dict(
            title="Scenario",
            titlefont=dict(size=font_size),
            tickfont=dict(size=font_size),
            showgrid=False,
        ),
        yaxis=dict(
            title="Weeks to Completion",
            titlefont=dict(size=font_size),
            tickfont=dict(size=font_size),
            gridcolor="rgba(0,0,0,0.1)",
            gridwidth=1,
            zeroline=True,
        ),
        height=height,
        margin=dict(
            l=50 if viewport_size == "mobile" else 70,
            r=20,
            t=80 if viewport_size == "mobile" else 100,
            b=50 if viewport_size == "mobile" else 70,
        ),
        showlegend=False,
        hovermode="x unified",
    )

    # Add annotation for insufficient data warning if < 4 weeks
    if forecast.get("insufficient_data"):
        fig.add_annotation(
            text="[!] Limited data - forecast may be less accurate",
            xref="paper",
            yref="paper",
            x=0.5,
            y=1.08 if viewport_size == "mobile" else 1.05,
            showarrow=False,
            font=dict(size=10 if viewport_size == "mobile" else 11, color="#ff6b6b"),
            align="center",
        )

    return fig
