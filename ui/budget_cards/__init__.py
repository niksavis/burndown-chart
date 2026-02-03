"""
Budget Cards Package

Modular budget visualization components extracted from monolithic budget_cards.py.
Provides backward compatibility for existing imports.

Modules:
- core_metrics: Budget utilization, weekly burn rate, budget runway
- cost_metrics: Cost per item/point, budget forecast
- breakdown_cards: Cost breakdown by work type, sparkline visualizations
- timeline_cards: Forecast vs budget alignment, budget timeline

Architecture:
Split from single 3,047-line file into focused modules following 500-line guideline.
Maintains Single Responsibility Principle with each module handling specific card types.

Created: January 30, 2026
"""

# Core budget tracking metrics
from ui.budget_cards.core_metrics import (
    create_budget_utilization_card,
    create_weekly_burn_rate_card,
    create_budget_runway_card,
)

# Cost efficiency metrics
from ui.budget_cards.cost_metrics import (
    create_cost_per_item_card,
    create_cost_per_point_card,
    create_budget_forecast_card,
)

# Cost breakdown and visualizations
from ui.budget_cards.breakdown_cards import (
    create_cost_breakdown_card,
)

# Timeline and forecast alignment
from ui.budget_cards.timeline_cards import (
    create_forecast_alignment_card,
    create_budget_timeline_card,
)

# Public API
__all__ = [
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
