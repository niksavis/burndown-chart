from data.demo.contract_types import make_contracts

TIMELINE_CONTRACTS = make_contracts(
    "budget-comparison",
    "data.budget_calculator_comparison.get_budget_baseline_vs_actual",
    "tab-dashboard",
    (
        ("budget-start-date", "baseline.start_date", "2025-12-08"),
        ("budget-end-date", "baseline.allocated_end_date", "2026-02-16"),
        ("budget-allocated-duration", "baseline.time_allocated_weeks", 10),
        ("budget-calendar-elapsed", "actual.elapsed_weeks", 52 / 7),
        ("budget-calendar-elapsed-pct", "actual.elapsed_pct", 520 / 7),
        ("budget-timeline-consumed", "actual.consumed_eur", 8700),
        ("budget-timeline-utilization", "actual.consumed_pct", 290 / 3),
        ("budget-runway-end", "actual.runway_end_date", "2026-01-31"),
        ("budget-burn-variance", "variance.burn_rate_variance_eur", 10),
        ("budget-burn-variance-pct", "variance.burn_rate_variance_pct", 10 / 11),
        ("budget-utilization-pace", "variance.utilization_vs_pace_pct", 470 / 21),
    ),
    backlog="burndownchart-imp012",
    selection="Calendar-day timeline and historical allocation, not a cash-spend measurement",
    derivation=(
        "Dec8+10weeks=Feb16;52whole elapsed days;8700/9000=96.667%; "
        "300/1110runway;1110-1100=10"
    ),
)

BUDGET_CONTRACTS = TIMELINE_CONTRACTS
for week, consumed, total in (
    ("2025-W50", 1000, 8000),
    ("2026-W01", 4200, 9500),
    ("2026-W03", 6500, 9000),
    ("2026-W05", 8700, 9000),
):
    BUDGET_CONTRACTS += make_contracts(
        f"budget-consumed-{week}",
        "data.budget_calculator_consumption.calculate_budget_consumed",
        "tab-dashboard",
        (
            (f"historical-spend-{week}", "consumed", consumed),
            (f"historical-allocation-{week}", "total", total),
            (f"historical-utilization-{week}", "percentage", consumed / total * 100),
        ),
        backlog="burndownchart-imp012",
        selection=f"Completed cohorts through {week}; four items per recorded week",
        derivation=(
            "Allocate each completed cohort using its effective weekly cost, divided by4 items. "
            "Three weeks cost 1000, two cost 1200, three cost 1100. "
            "Cumulative allocations are 1000/4200/6500/8700."
        ),
    )
BUDGET_CONTRACTS += make_contracts(
    "budget-runway",
    "data.budget_calculator_consumption.calculate_runway",
    "tab-dashboard",
    (
        ("budget-weighted-burn", "burn", 1110),
        ("budget-remaining-runway", "runway", 10 / 37),
    ),
    backlog="burndownchart-imp012",
    selection="All eight completed cohorts; historical cost allocation",
    derivation=(
        "Last 4 costs:1200/1100/1100/1100, weights:0.1/0.2/0.3/0.4 =>1110. "
        "Remaining 300/1110 =10/37 weeks."
    ),
)
for category in ("Feature", "Defect", "Technical Debt", "Risk"):
    BUDGET_CONTRACTS += make_contracts(
        "budget-types",
        "data.budget_calculator_consumption.calculate_cost_breakdown_by_type",
        "tab-dashboard",
        (
            (f"budget-type-{category}-cost", f"{category}.cost", 2175),
            (f"budget-type-{category}-count", f"{category}.count", 8),
            (f"budget-type-{category}-share", f"{category}.percentage", 25),
        ),
        backlog="burndownchart-imp012",
        derivation="Each of four types completes once perweek;8700historical allocation/4=2175each",
    )
BUDGET_CONTRACTS += make_contracts(
    "budget-comparison",
    "data.budget_calculator_comparison.get_budget_baseline_vs_actual",
    "tab-dashboard",
    (
        ("budget-current-cost-item", "actual.cost_per_item", 275),
        ("budget-current-cost-point", "actual.cost_per_point", 137.5),
        ("budget-item-cost-variance", "variance.cost_per_item_variance_pct", 0),
        ("budget-point-cost-variance", "variance.cost_per_point_variance_pct", 25),
    ),
    derivation="1100/week divided by4items=275, by8points=137.5. Baseline110/point rises25%.",
)
