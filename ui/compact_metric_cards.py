"""Compact metric overview cards for DORA and Flow dashboards.

Provides small, information-dense cards showing current metric values
at the top of dashboards for quick overview without scrolling.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html


def create_compact_overview_card(
    metric_name: str,
    value: Any,
    unit: str,
    performance_color: str = "primary",
    icon: str = "chart-line",
) -> dbc.Card:
    """Create a small, compact metric overview card.

    Args:
        metric_name: Display name of the metric
        value: Current metric value
        unit: Unit of measurement
        performance_color: Bootstrap color class (success, info, warning, danger)
        icon: Font Awesome icon name

    Returns:
        Compact card component
    """
    # Map performance colors to Bootstrap/custom colors (semaphore style)
    color_map = {
        "green": "success",  # Elite/Excellent
        "blue": "tier-high",  # High/Good - custom cyan
        "yellow": "tier-medium",  # Medium/Fair - custom yellow
        "orange": "tier-orange",  # Low/Slow - custom orange
        "red": "danger",  # Critical/Worst
        # Legacy fallbacks
        "primary": "primary",
        "success": "success",
        "info": "tier-high",  # Map old info to tier-high
        "warning": "tier-medium",  # Map old warning to tier-medium
        "danger": "danger",
    }

    bootstrap_color = color_map.get(performance_color, "primary")

    # Map Bootstrap color to CSS variable for border
    border_color_map = {
        "success": "#198754",  # var(--tier-elite)
        "tier-high": "#0dcaf0",  # var(--tier-high)
        "tier-medium": "#ffc107",  # var(--tier-medium)
        "tier-orange": "#fd7e14",  # var(--tier-low-orange)
        "danger": "#dc3545",  # var(--tier-critical)
        "primary": "#0d6efd",  # Default
    }

    border_color = border_color_map.get(bootstrap_color, "#0d6efd")

    # Format value display
    if isinstance(value, float):
        value_display = f"{value:.1f}"
    else:
        value_display = str(value) if value is not None else "—"

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(className=f"fas fa-{icon} me-2 text-{bootstrap_color}"),
                        html.Span(metric_name, className="text-muted small"),
                    ],
                    className="d-flex align-items-center mb-1",
                ),
                html.Div(
                    [
                        html.Span(
                            value_display,
                            className=f"h4 mb-0 text-{bootstrap_color} fw-bold",
                        ),
                        html.Small(f" {unit}", className="text-muted ms-1"),
                    ],
                ),
            ],
            className="p-2",
        ),
        className="compact-metric-card shadow-sm",
        style={"minHeight": "80px", "borderLeftColor": border_color},
    )


def create_dora_metrics_overview(metrics_data: Dict[str, Any]) -> html.Div:
    """Create compact overview cards for DORA metrics.

    Args:
        metrics_data: Dictionary of DORA metrics with values and metadata

    Returns:
        Row of compact metric cards
    """
    cards = []

    # Deployment Frequency
    if "deployment_frequency" in metrics_data:
        df_metric = metrics_data["deployment_frequency"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Deploy Frequency",
                    value=df_metric.get("value"),
                    unit=df_metric.get("unit", "deploys/week"),
                    performance_color=df_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="rocket",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Lead Time for Changes
    if "lead_time_for_changes" in metrics_data:
        lt_metric = metrics_data["lead_time_for_changes"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Lead Time",
                    value=lt_metric.get("value"),
                    unit=lt_metric.get("unit", "days"),
                    performance_color=lt_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="clock",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Change Failure Rate
    if "change_failure_rate" in metrics_data:
        cfr_metric = metrics_data["change_failure_rate"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Failure Rate",
                    value=cfr_metric.get("value"),
                    unit=cfr_metric.get("unit", "%"),
                    performance_color=cfr_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="exclamation-triangle",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Mean Time to Recovery
    if "mean_time_to_recovery" in metrics_data:
        mttr_metric = metrics_data["mean_time_to_recovery"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="MTTR",
                    value=mttr_metric.get("value"),
                    unit=mttr_metric.get("unit", "hours"),
                    performance_color=mttr_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="medkit",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    if not cards:
        return html.Div()

    return html.Div(
        [
            dbc.Row(cards, className="g-2"),  # Removed mb-3 for tighter bottom spacing
        ]
    )


def create_flow_metrics_overview(metrics_data: Dict[str, Any]) -> html.Div:
    """Create compact overview cards for Flow metrics.

    Args:
        metrics_data: Dictionary of Flow metrics with values and metadata

    Returns:
        Row of compact metric cards
    """
    cards = []

    # Flow Velocity
    if "flow_velocity" in metrics_data:
        velocity_metric = metrics_data["flow_velocity"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Velocity",
                    value=velocity_metric.get("value"),
                    unit=velocity_metric.get("unit", "items/week"),
                    performance_color=velocity_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="tachometer-alt",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Flow Time
    if "flow_time" in metrics_data:
        time_metric = metrics_data["flow_time"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Flow Time",
                    value=time_metric.get("value"),
                    unit=time_metric.get("unit", "days"),
                    performance_color=time_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="hourglass-half",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Flow Efficiency
    if "flow_efficiency" in metrics_data:
        efficiency_metric = metrics_data["flow_efficiency"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="Efficiency",
                    value=efficiency_metric.get("value"),
                    unit=efficiency_metric.get("unit", "%"),
                    performance_color=efficiency_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="percentage",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    # Flow Load (WIP)
    if "flow_load" in metrics_data:
        load_metric = metrics_data["flow_load"]
        cards.append(
            dbc.Col(
                create_compact_overview_card(
                    metric_name="WIP",
                    value=load_metric.get("value"),
                    unit=load_metric.get("unit", "items"),
                    performance_color=load_metric.get(
                        "performance_tier_color", "primary"
                    ),
                    icon="layer-group",
                ),
                width=12,
                md=6,
                lg=3,
                className="mb-0",
            )
        )

    if not cards:
        return html.Div()

    return html.Div(
        [
            dbc.Row(cards, className="g-2"),  # Removed mb-3 for tighter bottom spacing
        ]
    )
