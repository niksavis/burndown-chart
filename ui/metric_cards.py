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

from ui.tooltip_utils import create_info_tooltip


def _create_mini_bar_sparkline(
    data: List[float], color: str, height: int = 40
) -> html.Div:
    """Create a mini CSS-based bar sparkline for inline trend display.

    Args:
        data: List of numeric values to display
        color: CSS color for bars
        height: Maximum height of bars in pixels

    Returns:
        Div containing mini bar chart
    """
    if not data or len(data) < 2:
        return html.Div()

    max_val = max(data) if max(data) > 0 else 1
    normalized = [v / max_val for v in data]

    bars = []
    for i, val in enumerate(normalized):
        bar_height = max(val * height, 2)
        opacity = 0.5 + (i / len(normalized)) * 0.5  # Fade from 0.5 to 1.0

        bars.append(
            html.Div(
                style={
                    "width": "4px",
                    "height": f"{bar_height}px",
                    "backgroundColor": color,
                    "opacity": opacity,
                    "borderRadius": "2px",
                    "margin": "0 1px",
                }
            )
        )

    return html.Div(
        bars,
        className="d-flex align-items-end justify-content-center",
        style={"height": f"{height}px", "gap": "1px"},
    )


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

    Now includes inline trend sparkline (always visible) below the metric value.
    Trend data should be provided in metric_data as:
    - weekly_labels: List of week labels (e.g., ["2025-W40", "2025-W41", ...])
    - weekly_values: List of metric values for each week
    """
    from visualization.metric_trends import create_metric_trend_sparkline

    # Map performance tier colors to Bootstrap colors
    tier_color_map = {
        "green": "success",
        "yellow": "warning",
        "orange": "warning",
        "red": "danger",
    }

    tier_color = metric_data.get("performance_tier_color", "secondary")
    bootstrap_color = tier_color_map.get(tier_color, "secondary")

    # Format metric name for display - use alternative_name if provided
    metric_name = metric_data.get("metric_name", "Unknown Metric")
    alternative_name = metric_data.get("alternative_name")
    metric_tooltip = metric_data.get("tooltip")  # Optional tooltip text

    if alternative_name:
        display_name = alternative_name
        tooltip_text = f"Interpreted as: {alternative_name} (Standard field: {metric_name.replace('_', ' ').title()})"
    else:
        display_name = metric_name.replace("_", " ").title()
        tooltip_text = None

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

    # Build card header children with optional tooltip for alternative names
    if alternative_name:
        header_children: List[Any] = [
            html.Span(
                [
                    html.I(
                        className="fas fa-info-circle me-2 text-info",
                        title=tooltip_text,
                    ),
                    display_name,
                ],
                className="metric-card-title",
            )
        ]
    else:
        # Start with just the display name
        title_content = [display_name]

        # Add info tooltip if provided
        if metric_tooltip:
            title_content.extend(
                [
                    " ",
                    create_info_tooltip(
                        help_text=metric_tooltip,
                        id_suffix=f"metric-{metric_name}",
                        placement="top",
                        variant="dark",
                    ),
                ]
            )

        header_children: List[Any] = [
            html.Span(title_content, className="metric-card-title")
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

    # Build card body with inline trend sparkline
    card_body_children = [
        # Metric value (large, centered)
        html.H2(formatted_value, className="text-center metric-value mb-2"),
        # Unit (smaller, centered)
        html.P(
            metric_data.get("unit", ""),
            className="text-muted text-center metric-unit mb-1",
        ),
    ]

    # Add inline trend sparkline if weekly data is provided
    weekly_labels = metric_data.get("weekly_labels", [])
    weekly_values = metric_data.get("weekly_values", [])

    if weekly_labels and weekly_values and len(weekly_labels) > 1:
        # Determine color based on performance tier
        sparkline_color = {
            "green": "#28a745",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
            "red": "#dc3545",
        }.get(tier_color, "#1f77b4")

        # Create inline mini sparkline (CSS-based, compact)
        mini_sparkline = _create_mini_bar_sparkline(
            weekly_values, sparkline_color, height=40
        )

        # Generate unique collapse ID for this card
        collapse_id = f"{metric_name}-details-collapse"

        card_body_children.append(
            html.Div(
                [
                    html.Hr(className="my-2"),
                    html.Div(
                        [
                            html.Small(
                                f"Trend (last {len(weekly_values)} weeks):",
                                className="text-muted d-block mb-1",
                            ),
                            mini_sparkline,
                            dbc.Button(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Show Details",
                                ],
                                id=f"{metric_name}-details-btn",
                                color="link",
                                size="sm",
                                className="mt-2 p-0",
                                style={"fontSize": "0.85rem"},
                            ),
                        ],
                        className="text-center",
                    ),
                    # Expandable detailed chart section
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                html.H6(
                                    f"Weekly {display_name} Trend",
                                    className="mb-3 text-center",
                                ),
                                create_metric_trend_sparkline(
                                    week_labels=weekly_labels,
                                    values=weekly_values,
                                    metric_name=display_name,
                                    unit=metric_data.get("unit", ""),
                                    height=200,
                                    show_axes=True,
                                    color=sparkline_color,
                                ),
                                html.Div(
                                    [
                                        html.Small(
                                            "Click chart to interact • Hover for values • Double-click to reset zoom",
                                            className="text-muted",
                                        )
                                    ],
                                    className="text-center mt-2",
                                ),
                            ],
                            className="bg-light",
                        ),
                        id=collapse_id,
                        is_open=False,
                    ),
                ],
                className="metric-trend-section",
            )
        )

    # Additional info at bottom
    card_body_children.extend(
        [
            html.Hr(className="my-2"),
            html.Small(
                _format_additional_info(metric_data),
                className="text-muted d-block text-center",
            ),
        ]
    )

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
            "action_text": "Open Settings",
            "action_id": {
                "type": "open-field-mapping",
                "index": metric_name,
            },  # Pattern-matching ID
            "message_override": "Configure JIRA field mappings in Settings to enable this metric.",
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

    # Determine badge text based on error state
    badge_text_map = {
        "no_data": "No Data",
        "missing_mapping": "Setup Required",
        "calculation_error": "Error",
    }
    badge_text = badge_text_map.get(error_state, "Error")

    card_header = dbc.CardHeader(
        [
            html.Span(display_name, className="metric-card-title"),
            dbc.Badge(badge_text, color=config["color"], className="float-end"),
        ]
    )

    card_body = dbc.CardBody(
        [
            html.I(className=f"{config['icon']} fa-3x text-{config['color']} mb-3"),
            html.H5(config["title"], className="mb-3"),
            html.P(
                config.get("message_override", error_message),
                className="text-muted mb-3",
            ),
            dbc.Button(
                config["action_text"],
                id=config["action_id"],
                color=config["color"],
                outline=True,
                className="metric-card-action-button",
            ),
            # Hidden trend collapse placeholder to satisfy pattern-matching callbacks
            # Error cards don't show trends, but callbacks expect these IDs to exist
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.Div(
                                id={
                                    "type": "metric-trend-chart",
                                    "metric": metric_name,
                                },
                                children=[
                                    html.P(
                                        "Trend not available for error state",
                                        className="text-muted text-center my-3",
                                    )
                                ],
                            )
                        ]
                    ),
                    className="mt-2",
                ),
                id={"type": "metric-trend-collapse", "metric": metric_name},
                is_open=False,
                style={"display": "none"},
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


def create_metric_cards_grid(
    metrics_data: Dict[str, dict], tooltips: Optional[Dict[str, str]] = None
) -> dbc.Row:
    """Create a responsive grid of metric cards.

    Args:
        metrics_data: Dictionary mapping metric names to metric data
            Example:
            {
                "deployment_frequency": {...},
                "lead_time_for_changes": {...}
            }
        tooltips: Optional dictionary mapping metric names to tooltip text
            Example:
            {
                "flow_velocity": "Number of work items completed per week...",
                "flow_time": "Median time from work start to completion..."
            }

    Returns:
        Dash Bootstrap Row with responsive columns
    """
    cards = []
    for metric_name, metric_info in metrics_data.items():
        # Add tooltip to metric_info if provided
        if tooltips and metric_name in tooltips:
            metric_info = {**metric_info, "tooltip": tooltips[metric_name]}

        card = create_metric_card(metric_info, card_id=f"{metric_name}-card")
        # Responsive column: full width on mobile, half on tablet, quarter on desktop
        col = dbc.Col(card, width=12, md=6, lg=3)
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid")
