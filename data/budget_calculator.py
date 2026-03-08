"""
Budget Calculator - Re-export shim for backward compatibility.

All logic has been split into focused modules:
- data.budget_calculator_core: Budget config reading and velocity helpers
- data.budget_calculator_consumption: Consumption, breakdown, and runway calculations
- data.budget_calculator_comparison: Baseline vs actual comparison and health tiers

Migration status: Callers may continue importing from this module.
New code should import from the canonical modules directly.
"""

from data.budget_calculator_comparison import (  # noqa: F401
    _calculate_health_tier,
    _empty_baseline_comparison,
    get_budget_baseline_vs_actual,
)
from data.budget_calculator_consumption import (  # noqa: F401
    _empty_breakdown,
    calculate_budget_consumed,
    calculate_cost_breakdown_by_type,
    calculate_runway,
    calculate_weekly_cost_breakdowns,
)
from data.budget_calculator_core import (  # noqa: F401
    _get_current_budget,
    _get_velocity,
    _get_velocity_points,
    get_budget_at_week,
)
