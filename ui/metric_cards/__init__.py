"""Reusable metric card components for DORA and Flow metrics.

This package provides functions to create metric display cards with support for:
- Success state with performance tier indicators
- Error states with actionable guidance
- Loading states
- Responsive design (mobile-first)

Public API:
    create_metric_card        -- Build a single metric card (success or error)
    create_metric_cards_grid  -- Build a responsive grid of metric cards
    create_forecast_section   -- Build the forecast display section (Feature 009)
    create_loading_card       -- Build a loading placeholder card
"""

from typing import Any

import dash_bootstrap_components as dbc

# Re-export symbols used by external callers
from ui.metric_cards._card_states import _create_error_card, create_loading_card
from ui.metric_cards._charts import (
    _create_deployment_details_table,
    _create_detailed_chart,
)
from ui.metric_cards._forecast import create_forecast_section
from ui.metric_cards._helpers import _get_flow_performance_tier_color_hex
from ui.metric_cards._success_card import _create_success_card

__all__ = [
    # Primary public API
    "create_metric_card",
    "create_metric_cards_grid",
    "create_forecast_section",
    "create_loading_card",
    # Semi-private symbols referenced by callbacks and tests
    "_create_detailed_chart",
    "_create_deployment_details_table",
    "_get_flow_performance_tier_color_hex",
    "_create_error_card",
    "_create_success_card",
]


def create_metric_card(
    metric_data: dict,
    card_id: str | None = None,
    forecast_data: dict[str, Any] | None = None,
    trend_vs_forecast: dict[str, Any] | None = None,
    show_details_button: bool = True,
    text_details: list[Any] | None = None,
) -> dbc.Card:
    """Create a metric display card.

    Args:
        metric_data: Dictionary with metric information:
            {
                "metric_name": str,
                "value": float | None,
                "unit": str,
                "performance_tier": str | None,  # Elite/High/Medium/Low
                "performance_tier_color": str,   # green/yellow/orange/red
                "error_state": str,  # success/missing_mapping/no_data/
                # calculation_error
                "error_message": str | None,
                "excluded_issue_count": int,
                "total_issue_count": int,
                "details": dict
            }
        card_id: Optional HTML ID for the card
        forecast_data: Optional forecast calculation results (Feature 009)
        trend_vs_forecast: Optional trend vs forecast analysis (Feature 009)
        show_details_button: If True, show "Show Details" button
            for expandable chart (default: True)
        text_details: Optional list of html.Div components
            with rich text content to display inline

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
    error_state = metric_data.get("error_state", "success")

    if error_state != "success":
        return _create_error_card(metric_data, card_id)

    return _create_success_card(
        metric_data,
        card_id,
        forecast_data,
        trend_vs_forecast,
        show_details_button,
        text_details,
    )


def create_metric_cards_grid(
    metrics_data: dict[str, dict],
    tooltips: dict[str, str] | None = None,
) -> dbc.Row:
    """Create a responsive grid of metric cards.

    Args:
        metrics_data: Dictionary mapping metric names to metric data.
            Example::

                {
                    "deployment_frequency": {...},
                    "lead_time_for_changes": {...}
                }

        tooltips: Optional dictionary mapping metric names to tooltip text.
            Example::

                {
                    "flow_velocity": "Number of work items completed per week...",
                    "flow_time": "Median time from work start to completion..."
                }

    Returns:
        Dash Bootstrap Row with responsive columns
    """
    cards = []
    for metric_name, metric_info in metrics_data.items():
        if tooltips and metric_name in tooltips:
            metric_info = {**metric_info, "tooltip": tooltips[metric_name]}

        forecast_data = metric_info.get("forecast_data")
        trend_vs_forecast = metric_info.get("trend_vs_forecast")

        card = create_metric_card(
            metric_info,
            card_id=f"{metric_name}-card",
            forecast_data=forecast_data,
            trend_vs_forecast=trend_vs_forecast,
        )
        col = dbc.Col(card, xs=12, lg=6, className="mb-3")
        cards.append(col)

    return dbc.Row(cards, className="metric-cards-grid")
