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
