from data.budget_calculator_comparison import get_budget_baseline_vs_actual
from data.budget_calculator_consumption import (
    calculate_budget_consumed,
    calculate_cost_breakdown_by_type,
    calculate_runway,
)


def budget_calculations(profile_id: str, source: str) -> dict:
    if source.startswith("budget-consumed-"):
        week = source.removeprefix("budget-consumed-")
        consumed, total, percentage = calculate_budget_consumed(
            profile_id, "main", week
        )
        return {"consumed": consumed, "total": total, "percentage": percentage}
    if source == "budget-runway":
        runway, burn = calculate_runway(profile_id, "main", "2026-W05", 8)
        return {"runway": runway, "burn": burn}
    if source == "budget-types":
        return calculate_cost_breakdown_by_type(profile_id, "main", "2026-W05")
    if source == "budget-comparison":
        return get_budget_baseline_vs_actual(profile_id, "main", "2026-W05", 8)
    raise ValueError(f"Unknown budget diagnostic source: {source}")
