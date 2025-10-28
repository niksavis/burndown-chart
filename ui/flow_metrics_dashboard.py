"""Flow Metrics Dashboard UI Components.

Provides the user interface for viewing Flow metrics including Velocity, Time,
Efficiency, Load, and Distribution with work type breakdown.
"""

from typing import Dict, Any
import dash_bootstrap_components as dbc
from dash import html, dcc

from ui.metric_cards import create_loading_card


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
                                className="text-muted mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            # Time period selector
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Time Period:", className="fw-bold mb-2"),
                            dbc.Select(
                                id="flow-time-period-select",
                                options=[
                                    {"label": "Last 7 Days", "value": "7"},
                                    {"label": "Last 30 Days", "value": "30"},
                                    {"label": "Last 90 Days", "value": "90"},
                                    {"label": "Custom Range", "value": "custom"},
                                ],
                                value="30",
                                className="mb-3",
                            ),
                        ],
                        width=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.Label(
                                        "Custom Date Range:", className="fw-bold mb-2"
                                    ),
                                    dcc.DatePickerRange(
                                        id="flow-date-range-picker",
                                        display_format="YYYY-MM-DD",
                                        className="d-block",
                                        style={"display": "none"},  # Hidden by default
                                    ),
                                ],
                                id="flow-custom-date-range-container",
                                style={"display": "none"},
                            ),
                        ],
                        width=12,
                        md=6,
                        lg=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                [
                                    html.I(className="fas fa-sync-alt me-2"),
                                    "Refresh Metrics",
                                ],
                                id="flow-refresh-button",
                                color="primary",
                                className="float-end",
                            ),
                        ],
                        width=12,
                        lg=4,
                        className="d-flex align-items-end justify-content-end",
                    ),
                ],
                className="mb-4",
            ),
            # Loading state indicator
            html.Div(id="flow-loading-state"),
            # Metrics cards grid
            html.Div(
                id="flow-metrics-cards-container",
                children=create_flow_loading_cards_grid(),
            ),
            # Distribution chart section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5(
                                            "Work Distribution Breakdown",
                                            className="mb-0",
                                        ),
                                        className="bg-light",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "Distribution of completed work across the four Flow item types. "
                                                "Recommended ranges are based on the Flow Framework.",
                                                className="text-muted mb-3",
                                            ),
                                            dcc.Loading(
                                                id="flow-distribution-loading",
                                                type="default",
                                                children=html.Div(
                                                    id="flow-distribution-chart-container"
                                                ),
                                            ),
                                        ]
                                    ),
                                ],
                                className="mb-4",
                            ),
                        ],
                        width=12,
                    ),
                ],
            ),
        ],
        fluid=True,
        className="py-4",
    )


def create_flow_loading_cards_grid() -> dbc.Row:
    """Create a grid of loading cards for Flow metrics.

    Returns:
        dbc.Row with loading card placeholders
    """
    metric_names = [
        "Flow Velocity",
        "Flow Time",
        "Flow Efficiency",
        "Flow Load",
        "Flow Distribution",
    ]

    loading_cards = [create_loading_card(name) for name in metric_names]

    return dbc.Row(
        [dbc.Col(card, width=12, md=6, lg=4, xl=2.4) for card in loading_cards],
        className="mb-4 g-3",
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

    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6(metric_name, className="text-muted mb-2"),
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
