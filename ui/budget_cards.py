import logging

from ui.budget_cards import (
    create_budget_forecast_card,
    create_budget_runway_card,
    create_budget_timeline_card,
    create_budget_utilization_card,
    create_cost_breakdown_card,
    create_cost_per_item_card,
    create_cost_per_point_card,
    create_forecast_alignment_card,
    create_weekly_burn_rate_card,
)

logger = logging.getLogger(__name__)

CURRENCY_ICON_MAP = {
    "$": "fa-dollar-sign",
    "€": "fa-euro-sign",
    "£": "fa-pound-sign",
    "¥": "fa-yen-sign",
}

__all__ = [
    "CURRENCY_ICON_MAP",
    "create_budget_utilization_card",
    "create_weekly_burn_rate_card",
    "create_budget_runway_card",
    "create_cost_per_item_card",
    "create_cost_per_point_card",
    "create_budget_forecast_card",
    "create_cost_breakdown_card",
    "create_forecast_alignment_card",
    "create_budget_timeline_card",
]
