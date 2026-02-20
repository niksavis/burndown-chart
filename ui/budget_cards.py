"""
Budget Cards - UI Components for Lean Budgeting

DEPRECATED: This module has been refactored into focused submodules for maintainability.
All functionality has been preserved through package re-exports.

New structure:
- ui/budget_cards/core_metrics.py: Budget utilization, weekly burn rate, budget runway
- ui/budget_cards/cost_metrics.py: Cost per item/point, budget forecast
- ui/budget_cards/breakdown_cards.py: Cost breakdown by work type
- ui/budget_cards/timeline_cards.py: Forecast alignment, budget timeline

This file maintains backward compatibility by re-exporting all functions.
Direct imports from submodules are recommended for new code.

Refactored: January 30, 2026 (original: January 4, 2026)
"""

import logging

# Re-export all functions from package for backward compatibility
from ui.budget_cards import (
    create_budget_forecast_card,
    create_budget_runway_card,
    create_budget_timeline_card,
    # Core metrics
    create_budget_utilization_card,
    # Breakdown cards
    create_cost_breakdown_card,
    # Cost metrics
    create_cost_per_item_card,
    create_cost_per_point_card,
    # Timeline cards
    create_forecast_alignment_card,
    create_weekly_burn_rate_card,
)

logger = logging.getLogger(__name__)

# Currency symbol to FontAwesome icon mapping (preserved for compatibility)
CURRENCY_ICON_MAP = {
    "$": "fa-dollar-sign",
    "€": "fa-euro-sign",
    "£": "fa-pound-sign",
    "¥": "fa-yen-sign",
}

__all__ = [
    # Currency mapping
    "CURRENCY_ICON_MAP",
    # Core metrics
    "create_budget_utilization_card",
    "create_weekly_burn_rate_card",
    "create_budget_runway_card",
    # Cost metrics
    "create_cost_per_item_card",
    "create_cost_per_point_card",
    "create_budget_forecast_card",
    # Breakdown cards
    "create_cost_breakdown_card",
    # Timeline cards
    "create_forecast_alignment_card",
    "create_budget_timeline_card",
]
