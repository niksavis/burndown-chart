"""Flow Metrics Dashboard UI Components.

Provides the user interface for viewing Flow metrics including Velocity, Time,
Efficiency, Load, and Distribution with work type breakdown.

Uses Data Points slider from settings panel to control historical data display.
Metrics calculated per ISO week (Monday-Sunday), showing current week + N-1 historical weeks.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html, dcc

from configuration.help_content import FLOW_METRICS_TOOLTIPS
from ui.tooltip_utils import create_info_tooltip


def create_flow_dashboard() -> dbc.Container:
    """Create the complete Flow metrics dashboard layout.

    Returns:
        dbc.Container with Flow metrics dashboard components
    """
    return dbc.Container(
        [
            # Header section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H2(
                                "Flow Metrics Dashboard",
                                className="mb-2",
                            ),
                            html.P(
                                "Flow Framework metrics for measuring value stream efficiency "
                                "and work distribution across Feature, Defect, Risk, and Technical Debt.",
                                className="text-muted",
                            ),
                            html.P(
                                [
                                    html.I(className="fas fa-calculator me-2"),
                                    "Use ",
                                    html.Strong("Calculate Metrics"),
                                    " button in Settings panel to refresh metrics. ",
                                    "Use ",
                                    html.Strong("Data Points slider"),
                                    " to control number of weeks displayed.",
                                ],
                                className="text-muted small mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Metrics cards grid
            html.Div(
                id="flow-metrics-cards-container",
                children=[],  # Will be populated by callback
            ),
            # Distribution chart section (rendered by callback)
            html.Div(
                id="flow-distribution-chart-container",
                children=[],  # Will be populated by callback
            ),
            # Store for metrics data
            dcc.Store(id="flow-metrics-store", data={}),
            # Store to trigger metrics refresh (timestamp of last refresh)
            dcc.Store(id="metrics-refresh-trigger", data=None),
        ],
        fluid=True,
        className="py-4",
    )


def create_flow_metric_card(
    metric_data: Dict[str, Any],
    metric_name: str,
) -> dbc.Card:
    """Create a metric card for a single Flow metric.

    Args:
        metric_data: Metric calculation result
        metric_name: Display name for the metric

    Returns:
        dbc.Card with metric display
    """
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        # Error card
        return _create_flow_error_card(metric_data, metric_name)

    value = metric_data.get("value")
    unit = metric_data.get("unit", "")

    # Format value display
    if isinstance(value, float):
        value_display = f"{value:.1f}"
    else:
        value_display = str(value)

    # Get status color based on metric type (default to primary if value is None)
    status_color = _get_flow_metric_color(metric_data["metric_name"], value or 0.0)

    # Get tooltip for this metric
    metric_key = metric_data["metric_name"]
    tooltip_text = FLOW_METRICS_TOOLTIPS.get(metric_key, "")

    # Create metric title with info icon
    if tooltip_text:
        title_element = html.H6(
            [
                metric_name,
                " ",
                create_info_tooltip(
                    help_text=tooltip_text,
                    id_suffix=f"flow-{metric_key}",
                    placement="top",
                    variant="dark",
                ),
            ],
            className="text-muted mb-2",
        )
    else:
        title_element = html.H6(metric_name, className="text-muted mb-2")

    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    title_element,
                    html.H2(
                        [
                            html.Span(value_display, className=f"text-{status_color}"),
                            html.Small(f" {unit}", className="text-muted ms-2"),
                        ],
                        className="mb-3",
                    ),
                    # Type breakdown if available
                    _create_type_breakdown(metric_data.get("details", {})),
                    # Trend indicator if available
                    _create_trend_indicator(metric_data.get("details", {})),
                ]
            ),
        ],
        className="h-100 shadow-sm",
    )

    return card


def _create_flow_error_card(metric_data: Dict[str, Any], metric_name: str) -> dbc.Card:
    """Create an error card for Flow metric.

    Args:
        metric_data: Metric data with error state
        metric_name: Display name

    Returns:
        dbc.Card with error display
    """
    error_message = metric_data.get("error_message", "Unknown error")

    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6(metric_name, className="text-muted mb-2"),
                    html.Div(
                        [
                            html.I(
                                className="fas fa-exclamation-triangle text-warning me-2"
                            ),
                            html.Span("Error", className="text-warning"),
                        ],
                        className="mb-2",
                    ),
                    html.P(
                        error_message,
                        className="small text-muted mb-0",
                    ),
                ]
            ),
        ],
        className="h-100 shadow-sm border-warning",
    )


def _create_type_breakdown(details: Dict[str, Any]) -> html.Div:
    """Create work type breakdown display.

    Args:
        details: Metric details with by_type breakdown

    Returns:
        html.Div with type breakdown or empty div
    """
    by_type = details.get("by_type", {})

    if not by_type or all(v == 0 for v in by_type.values()):
        return html.Div()

    # Create mini badges for each type
    type_badges = []
    type_colors = {
        "Feature": "primary",
        "Defect": "danger",
        "Risk": "warning",
        "Technical_Debt": "info",
    }

    for work_type, count in by_type.items():
        if count > 0:
            color = type_colors.get(work_type, "secondary")
            label = work_type.replace("_", " ")
            type_badges.append(
                dbc.Badge(
                    f"{label}: {count}",
                    color=color,
                    className="me-1 mb-1",
                    pill=True,
                )
            )

    if not type_badges:
        return html.Div()

    return html.Div(
        type_badges,
        className="mt-2",
    )


def _create_trend_indicator(details: Dict[str, Any]) -> html.Div:
    """Create trend indicator display.

    Args:
        details: Metric details with trend information

    Returns:
        html.Div with trend display or empty div
    """
    trend_direction = details.get("trend_direction", "unknown")
    trend_percentage = details.get("trend_percentage", 0)

    if trend_direction == "unknown" or trend_percentage == 0:
        return html.Div()

    # Determine icon and color
    if trend_direction == "up":
        icon = "fa-arrow-up"
        color = "success"
    elif trend_direction == "down":
        icon = "fa-arrow-down"
        color = "danger"
    else:  # stable
        icon = "fa-minus"
        color = "secondary"

    return html.Div(
        [
            html.I(className=f"fas {icon} text-{color} me-1"),
            html.Span(
                f"{abs(trend_percentage):.1f}%",
                className=f"text-{color} small",
            ),
            html.Span(" vs last period", className="text-muted small ms-1"),
        ],
        className="mt-2",
    )


def _get_flow_metric_color(metric_name: str, value: float) -> str:
    """Get color for metric based on value and thresholds.

    Args:
        metric_name: Name of the metric
        value: Metric value

    Returns:
        Bootstrap color class name
    """
    # Flow Efficiency thresholds
    if metric_name == "flow_efficiency":
        if 25 <= value <= 40:
            return "success"  # Healthy range
        elif value < 15:
            return "danger"  # Critical
        else:
            return "warning"  # Outside ideal range

    # Flow Load (WIP) - lower is generally better
    if metric_name == "flow_load":
        if value < 10:
            return "success"
        elif value < 20:
            return "info"
        else:
            return "warning"

    # Default colors
    return "primary"


def create_flow_metrics_cards_grid(metrics_data: dict):
    """Create a grid of Flow metric cards with info tooltips.

    This is the Flow-specific version that uses create_flow_metric_card()
    which includes info icon tooltips for each metric.

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "flow_velocity": {
                    "metric_name": "flow_velocity",
                    "value": 5.2,
                    "unit": "items/week",
                    ...
                },
                "flow_time": {...}
            }

    Returns:
        dbc.Row containing the grid of Flow metric cards
    """
    if not metrics_data:
        return html.Div(
            "No Flow metrics available. Please ensure data is loaded.",
            className="text-muted p-3",
        )

    # Create cards using Flow-specific function with tooltips
    cards = []
    for metric_name, metric_info in metrics_data.items():
        card_id = f"flow-metric-{metric_name}"
        card = create_flow_metric_card(metric_info, card_id)
        # Responsive column: full width on mobile, half on tablet, quarter on desktop
        cards.append(dbc.Col(card, width=12, md=6, lg=3))

    return dbc.Row(cards, className="metric-cards-grid")
