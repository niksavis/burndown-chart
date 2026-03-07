"""
Dashboard Enhanced Package - Compact project analytics widgets.

This package splits the original dashboard_enhanced.py into focused submodules:
- stats: Statistical calculations (velocity, confidence intervals, health)
- components: Visual primitives (sparklines, progress bars)
- metric_cards: Forecast and velocity card builders
- capacity_card: Capacity gap analysis card
- overview_bar: Overview bar widget
- layout: Main dashboard assembly
"""

from ui.dashboard_enhanced.capacity_card import _create_capacity_card
from ui.dashboard_enhanced.components import (
    _create_progress_bar,
    _create_sparkline_bars,
)
from ui.dashboard_enhanced.layout import create_enhanced_dashboard
from ui.dashboard_enhanced.metric_cards import (
    _create_forecast_card,
    _create_velocity_card,
)
from ui.dashboard_enhanced.stats import (
    _assess_project_health,
    _calculate_confidence_intervals,
    _calculate_deadline_probability,
    _calculate_velocity_statistics,
)

__all__ = [
    # Public API
    "create_enhanced_dashboard",
    # Statistical helpers (exposed for tests and direct use)
    "_calculate_velocity_statistics",
    "_calculate_confidence_intervals",
    "_calculate_deadline_probability",
    "_assess_project_health",
    # Visual primitives
    "_create_sparkline_bars",
    "_create_progress_bar",
    # Card builders
    "_create_forecast_card",
    "_create_velocity_card",
    "_create_capacity_card",
]
