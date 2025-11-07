"""DORA metrics visualization charts.

Provides chart generation functions for DORA metrics visualization.
"""

from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
from datetime import datetime, timedelta


def create_deployment_frequency_chart(
    metric_data: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """Create deployment frequency visualization chart.

    Args:
        metric_data: Current metric data with value and performance tier
        historical_data: Optional historical data for trend line

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    # If historical data provided, show trend
    if historical_data:
        dates = [datetime.fromisoformat(d["date"]) for d in historical_data]
        values = [d["value"] for d in historical_data]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                name="Deployment Frequency",
                line=dict(color="#0d6efd", width=2),
                marker=dict(size=8),
            )
        )
    else:
        # Show current value as single point
        current_value = metric_data.get("value", 0)
        fig.add_trace(
            go.Bar(
                x=["Current"],
                y=[current_value],
                marker_color="#0d6efd",
                name="Deployments/Month",
            )
        )

    # Add performance tier benchmark lines
    tier_color = metric_data.get("performance_tier_color", "grey")
    tier_name = metric_data.get("performance_tier", "Unknown")

    fig.update_layout(
        title=f"Deployment Frequency - {tier_name} Performance",
        xaxis_title="Time Period",
        yaxis_title="Deployments per Month",
        hovermode="x unified",
        template="plotly_white",
        height=300,
    )

    return fig


def create_lead_time_chart(
    metric_data: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """Create lead time for changes visualization chart.

    Args:
        metric_data: Current metric data with value and performance tier
        historical_data: Optional historical data for trend line

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    if historical_data:
        dates = [datetime.fromisoformat(d["date"]) for d in historical_data]
        values = [d["value"] for d in historical_data]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                name="Lead Time",
                line=dict(color="#198754", width=2),
                marker=dict(size=8),
            )
        )
    else:
        current_value = metric_data.get("value", 0)
        fig.add_trace(
            go.Bar(
                x=["Current"],
                y=[current_value],
                marker_color="#198754",
                name="Days",
            )
        )

    tier_name = metric_data.get("performance_tier", "Unknown")

    fig.update_layout(
        title=f"Lead Time for Changes - {tier_name} Performance",
        xaxis_title="Time Period",
        yaxis_title="Days",
        hovermode="x unified",
        template="plotly_white",
        height=300,
    )

    return fig


def create_change_failure_rate_chart(
    metric_data: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """Create change failure rate visualization chart.

    Args:
        metric_data: Current metric data with value and performance tier
        historical_data: Optional historical data for trend line

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    if historical_data:
        dates = [datetime.fromisoformat(d["date"]) for d in historical_data]
        values = [d["value"] for d in historical_data]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                name="Failure Rate",
                line=dict(color="#dc3545", width=2),
                marker=dict(size=8),
            )
        )
    else:
        current_value = metric_data.get("value", 0)
        fig.add_trace(
            go.Bar(
                x=["Current"],
                y=[current_value],
                marker_color="#dc3545",
                name="Percentage",
            )
        )

    tier_name = metric_data.get("performance_tier", "Unknown")

    fig.update_layout(
        title=f"Change Failure Rate - {tier_name} Performance",
        xaxis_title="Time Period",
        yaxis_title="Failure Rate (%)",
        hovermode="x unified",
        template="plotly_white",
        height=300,
    )

    return fig


def create_mttr_chart(
    metric_data: Dict[str, Any], historical_data: Optional[List[Dict[str, Any]]] = None
) -> go.Figure:
    """Create mean time to recovery visualization chart.

    Args:
        metric_data: Current metric data with value and performance tier
        historical_data: Optional historical data for trend line

    Returns:
        Plotly figure object
    """
    fig = go.Figure()

    if historical_data:
        dates = [datetime.fromisoformat(d["date"]) for d in historical_data]
        values = [d["value"] for d in historical_data]

        fig.add_trace(
            go.Scatter(
                x=dates,
                y=values,
                mode="lines+markers",
                name="MTTR",
                line=dict(color="#ffc107", width=2),
                marker=dict(size=8),
            )
        )
    else:
        current_value = metric_data.get("value", 0)
        fig.add_trace(
            go.Bar(
                x=["Current"],
                y=[current_value],
                marker_color="#ffc107",
                name="Hours",
            )
        )

    tier_name = metric_data.get("performance_tier", "Unknown")

    fig.update_layout(
        title=f"Mean Time to Recovery - {tier_name} Performance",
        xaxis_title="Time Period",
        yaxis_title="Hours",
        hovermode="x unified",
        template="plotly_white",
        height=300,
    )

    return fig


def create_dora_summary_chart(metrics_data: Dict[str, Dict[str, Any]]) -> go.Figure:
    """Create a summary radar chart showing all four DORA metrics.

    Args:
        metrics_data: Dictionary containing all four DORA metrics

    Returns:
        Plotly figure object with radar chart
    """
    # Extract performance tier scores (Elite=4, High=3, Medium=2, Low=1)
    tier_scores = {
        "Elite": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1,
    }

    metrics = [
        "Deployment<br>Frequency",
        "Lead Time for<br>Changes",
        "Change Failure<br>Rate",
        "Mean Time to<br>Recovery",
    ]

    scores = []
    for metric_key in [
        "deployment_frequency",
        "lead_time_for_changes",
        "change_failure_rate",
        "mean_time_to_recovery",
    ]:
        metric = metrics_data.get(metric_key, {})
        tier = metric.get("performance_tier", "Low")
        scores.append(tier_scores.get(tier, 1))

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=scores,
            theta=metrics,
            fill="toself",
            name="Current Performance",
            marker=dict(color="#0d6efd"),
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 4],
                tickvals=[1, 2, 3, 4],
                ticktext=["Low", "Medium", "High", "Elite"],
            )
        ),
        showlegend=False,
        title="DORA Metrics Performance Overview",
        height=400,
    )

    return fig


# ============================================================================
# Trend Chart Functions (Phase 7 - User Story 5)
# ============================================================================


def create_deployment_frequency_trend(
    trend_data: List[Dict[str, Any]], metric_data: Dict[str, Any]
) -> go.Figure:
    """Create deployment frequency trend chart over time with separate deployment and release lines.

    T054: Trend visualization for Deployment Frequency metric.

    Args:
        trend_data: List of historical data points with date, value (deployments), and release_value (releases)
            [{"date": "2025-01-01", "value": 30.5, "release_value": 15.2}, ...]
        metric_data: Current metric metadata (tier, benchmarks)

    Returns:
        Plotly figure with dual trend lines (deployments and releases) and benchmark zones
    """
    if not trend_data or len(trend_data) == 0:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No historical data available for trend analysis",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14),
        )
        fig.update_layout(
            title="Deployment Frequency Trend",
            height=300,
            template="plotly_white",
        )
        return fig

    # Parse dates, deployment values, and release values
    dates = [datetime.fromisoformat(d["date"]) for d in trend_data]
    deployment_values = [d["value"] for d in trend_data]
    release_values = [d.get("release_value", 0) for d in trend_data]

    fig = go.Figure()

    # Add deployment trend line (primary - operational tasks)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=deployment_values,
            mode="lines+markers",
            name="Deployments (Operational Tasks)",
            line=dict(color="#0d6efd", width=3),
            marker=dict(size=8, color="#0d6efd"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>"
            + "Deployments: %{y:.1f}/month<br>"
            + "<extra></extra>",
        )
    )

    # Add release trend line (secondary - unique fixVersions)
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=release_values,
            mode="lines+markers",
            name="Releases (Unique fixVersions)",
            line=dict(color="#28a745", width=2, dash="dot"),
            marker=dict(size=6, color="#28a745", symbol="diamond"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>"
            + "Releases: %{y:.1f}/month<br>"
            + "<extra></extra>",
        )
    )

    # Add benchmark zones as horizontal lines (based on deployments)
    # Elite: > 30/month, High: 4-30/month, Medium: 1-4/month, Low: < 1/month
    benchmark_lines = [
        {"value": 30, "name": "Elite", "color": "rgba(40, 167, 69, 0.2)"},
        {"value": 4, "name": "High", "color": "rgba(255, 193, 7, 0.2)"},
        {"value": 1, "name": "Medium", "color": "rgba(255, 152, 0, 0.2)"},
    ]

    for benchmark in benchmark_lines:
        fig.add_hline(
            y=benchmark["value"],
            line_dash="dash",
            line_color=benchmark["color"].replace("0.2", "0.8"),
            annotation_text=benchmark["name"],
            annotation_position="right",
        )

    fig.update_layout(
        title="Deployment Frequency Trend: Deployments vs Releases",
        xaxis_title="Date",
        yaxis_title="Frequency per Month",
        hovermode="x unified",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
        ),
    )

    return fig


def create_lead_time_trend(
    trend_data: List[Dict[str, Any]], metric_data: Dict[str, Any]
) -> go.Figure:
    """Create lead time for changes trend chart over time.

    T054: Trend visualization for Lead Time metric.

    Args:
        trend_data: List of historical data points with date and value
        metric_data: Current metric metadata (tier, benchmarks)

    Returns:
        Plotly figure with trend line and benchmark zones
    """
    if not trend_data or len(trend_data) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical data available for trend analysis",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14),
        )
        fig.update_layout(
            title="Lead Time for Changes Trend",
            height=300,
            template="plotly_white",
        )
        return fig

    dates = [datetime.fromisoformat(d["date"]) for d in trend_data]
    values = [d["value"] for d in trend_data]

    fig = go.Figure()

    # Add trend line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name="Lead Time",
            line=dict(color="#6610f2", width=3),
            marker=dict(size=8, color="#6610f2"),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>"
            + "Lead Time: %{y:.1f} days<br>"
            + "<extra></extra>",
        )
    )

    # Add benchmark zones
    # Elite: < 1 day, High: 1-7 days, Medium: 7-30 days, Low: > 30 days
    benchmark_lines = [
        {"value": 1, "name": "Elite", "color": "rgba(40, 167, 69, 0.2)"},
        {"value": 7, "name": "High", "color": "rgba(255, 193, 7, 0.2)"},
        {"value": 30, "name": "Medium", "color": "rgba(255, 152, 0, 0.2)"},
    ]

    for benchmark in benchmark_lines:
        fig.add_hline(
            y=benchmark["value"],
            line_dash="dash",
            line_color=benchmark["color"].replace("0.2", "0.8"),
            annotation_text=benchmark["name"],
            annotation_position="right",
        )

    fig.update_layout(
        title="Lead Time for Changes Trend",
        xaxis_title="Date",
        yaxis_title="Days",
        hovermode="x unified",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=50, t=50, b=50),
    )

    return fig
