"""Reusable metric card components for DORA and Flow metrics.

This module provides functions to create metric display cards with support for:
- Success state with performance tier indicators
- Error states with actionable guidance
- Loading states
- Responsive design (mobile-first)
"""

from typing import Any, Dict, List, Optional

import dash_bootstrap_components as dbc
from dash import html


def create_metric_card(metric_data: dict, card_id: Optional[str] = None) -> dbc.Card:
    """Create a metric display card.

    Args:
        metric_data: Dictionary with metric information:
            {
                "metric_name": str,
                "value": float | None,
                "unit": str,
                "performance_tier": str | None,  # Elite/High/Medium/Low
                "performance_tier_color": str,   # green/yellow/orange/red
                "error_state": str,              # success/missing_mapping/no_data/calculation_error
                "error_message": str | None,
                "excluded_issue_count": int,
                "total_issue_count": int,
                "details": dict
            }
        card_id: Optional HTML ID for the card

    Returns:
        Dash Bootstrap Card component

    Example:
        >>> metric_data = {
        ...     "metric_name": "deployment_frequency",
        ...     "value": 45.2,
        ...     "unit": "deployments/month",
        ...     "performance_tier": "High",
        ...     "performance_tier_color": "yellow",
        ...     "error_state": "success",
        ...     "total_issue_count": 50
        ... }
        >>> card = create_metric_card(metric_data)
    """
    # Determine if error state
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        return _create_error_card(metric_data, card_id)

    return _create_success_card(metric_data, card_id)


def _create_success_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for successful metric calculation.

    T056: Now includes collapsible trend section with "Show Trend" button.
    """
    # Map performance tier colors to Bootstrap colors
    tier_color_map = {
        "green": "success",
        "yellow": "warning",
        "orange": "warning",
        "red": "danger",
    }

    tier_color = metric_data.get("performance_tier_color", "secondary")
    bootstrap_color = tier_color_map.get(tier_color, "secondary")

    # Format metric name for display
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    display_name = metric_name.replace("_", " ").title()

    # Format value
    value = metric_data.get("value")
    if value is not None:
        formatted_value = f"{value:.1f}" if value >= 10 else f"{value:.2f}"
    else:
        formatted_value = "N/A"

    # Build card
    card_props = {"className": "metric-card mb-3"}
    if card_id:
        card_props["id"] = card_id

    # Build card header children
    header_children: List[Any] = [
        html.Span(display_name, className="metric-card-title")
    ]

    # Add performance tier badge if present
    if metric_data.get("performance_tier"):
        header_children.append(
            dbc.Badge(
                metric_data.get("performance_tier", "Unknown"),
                color=bootstrap_color,
                className="float-end",
            )
        )

    card_header = dbc.CardHeader(header_children)

    # Trend button and collapsible section (T056)
    trend_collapse_id = f"{metric_name}-trend-collapse"
    trend_button_id = f"{metric_name}-trend-button"

    card_body_children = [
        # Metric value (large, centered)
        html.H2(formatted_value, className="text-center metric-value mb-2"),
        # Unit (smaller, centered)
        html.P(
            metric_data.get("unit", ""),
            className="text-muted text-center metric-unit mb-3",
        ),
        # Additional info
        html.Small(_format_additional_info(metric_data), className="text-muted"),
        # Show Trend button
        html.Hr(className="my-3"),
        dbc.Button(
            [
                html.I(className="fas fa-chart-line me-2"),
                "Show Trend",
            ],
            id=trend_button_id,
            color="link",
            size="sm",
            className="w-100",
        ),
        # Collapsible trend chart container
        dbc.Collapse(
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            id=f"{metric_name}-trend-chart",
                            children=[
                                html.P(
                                    "Trend chart will be displayed here",
                                    className="text-muted text-center my-3",
                                )
                            ],
                        )
                    ]
                ),
                className="mt-2",
            ),
            id=trend_collapse_id,
            is_open=False,
        ),
    ]

    card_body = dbc.CardBody(card_body_children)

    return dbc.Card([card_header, card_body], **card_props)  # type: ignore[call-arg]


def _create_error_card(metric_data: dict, card_id: Optional[str]) -> dbc.Card:
    """Create card for error state with actionable guidance."""
    error_state = metric_data.get("error_state", "unknown_error")
    error_message = metric_data.get("error_message", "An error occurred")

    # Format metric name for display
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    display_name = metric_name.replace("_", " ").title()

    # Map error states to icons and titles
    error_config = {
        "missing_mapping": {
            "icon": "fas fa-cog",
            "title": "⚙️ Field Mapping Required",
            "color": "warning",
            "action_text": "Configure Mappings",
            "action_id": "open-field-mapping-modal",
        },
        "no_data": {
            "icon": "fas fa-chart-line",
            "title": "📊 No Data Available",
            "color": "info",
            "action_text": "Change Time Period",
            "action_id": "open-time-period-selector",
        },
        "calculation_error": {
            "icon": "fas fa-exclamation-triangle",
            "title": "❌ Calculation Error",
            "color": "danger",
            "action_text": "Retry",
            "action_id": "retry-metric-calculation",
        },
    }

    config = error_config.get(
        error_state,
        {
            "icon": "fas fa-exclamation-circle",
            "title": "⚠️ Error",
            "color": "warning",
            "action_text": "View Details",
            "action_id": "view-error-details",
        },
    )

    # Build card
    card_props = {"className": "metric-card metric-card-error mb-3"}
    if card_id:
        card_props["id"] = card_id

    card_header = dbc.CardHeader(
        [
            html.Span(display_name, className="metric-card-title"),
            dbc.Badge("Error", color=config["color"], className="float-end"),
        ]
    )

    card_body = dbc.CardBody(
        [
            html.I(className=f"{config['icon']} fa-3x text-{config['color']} mb-3"),
            html.H5(config["title"], className="mb-3"),
            html.P(error_message, className="text-muted mb-3"),
            dbc.Button(
                config["action_text"],
                id=config["action_id"],
                color=config["color"],
                outline=True,
                className="metric-card-action-button",
            ),
        ],
        className="text-center",
    )

    return dbc.Card([card_header, card_body], **card_props)  # type: ignore[call-arg]


def _format_additional_info(metric_data: dict) -> str:
    """Format additional information text for metric card."""
    total_issues = metric_data.get("total_issue_count", 0)
    excluded_issues = metric_data.get("excluded_issue_count", 0)

    if excluded_issues > 0:
        return (
            f"Based on {total_issues - excluded_issues} of {total_issues} issues. "
            f"{excluded_issues} excluded due to missing data."
        )
    else:
        return f"Based on {total_issues} issues"


def create_loading_card(metric_name: str) -> dbc.Card:
    """Create a loading placeholder card.

    Args:
        metric_name: Name of the metric being calculated

    Returns:
        Card with loading spinner
    """
    display_name = metric_name.replace("_", " ").title()

    return dbc.Card(
        [
            dbc.CardHeader(display_name),
            dbc.CardBody(
                [
                    dbc.Spinner(size="lg", color="primary"),
                    html.P("Calculating...", className="text-muted text-center mt-3"),
                ],
                className="text-center",
            ),
        ],
        className="metric-card metric-card-loading mb-3",
    )


def create_metric_cards_grid(metrics_data: Dict[str, dict]) -> dbc.Row:
    """Create a responsive grid of metric cards.

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "deployment_frequency": {...},
                "lead_time_for_changes": {...}
            }

    Returns:
        Dash Bootstrap Row with responsive columns
    """
    cards = []
    for metric_name, metric_info in metrics_data.items():
        card = create_metric_card(metric_info, card_id=f"{metric_name}-card")
        # Responsive column: full width on mobile, half on tablet, quarter on desktop
        col = dbc.Col(card, width=12, md=6, lg=3)
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid")
