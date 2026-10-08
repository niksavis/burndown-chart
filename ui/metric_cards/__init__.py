from typing import Any

import dash_bootstrap_components as dbc

from ui.metric_cards._card_states import _create_error_card, create_loading_card
from ui.metric_cards._charts import (
    _create_deployment_details_table,
    _create_detailed_chart,
)
from ui.metric_cards._forecast import create_forecast_section
from ui.metric_cards._helpers import _get_flow_performance_tier_color_hex
from ui.metric_cards._success_card import _create_success_card

__all__ = [
    "create_metric_card",
    "create_metric_cards_grid",
    "create_forecast_section",
    "create_loading_card",
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
