from data.demo.contract_types import make_contracts

POLICY_CONTRACTS = make_contracts(
    "recommendation-policies",
    "data.recommendations.budget_signals.build_budget_health_signals",
    "tab-dashboard",
    (
        (
            "budget-signal-utilization",
            "budget.signals.budget_critical.metrics.utilization_pct",
            290 / 3,
        ),
        (
            "budget-signal-runway",
            "budget.signals.budget_critical.metrics.runway_weeks",
            10 / 37,
        ),
        (
            "budget-signal-burn",
            "budget.signals.budget_critical.metrics.burn_rate",
            1110,
        ),
        ("budget-absent-signal", "budget_missing.count", 0),
        ("budget-absent-forecast", "forecast_missing.count", 0),
    ),
    selection="Independent corrected budget allocation inputs; explicit policy calibration",
    derivation="8700/9000=290/3percent;300/1110=10/37weeks; missing inputs give no signal",
)
for wrapper in ("forecast_pert", "forecast_dashboard"):
    POLICY_CONTRACTS += make_contracts(
        "recommendation-policies",
        "data.recommendations.budget_signals.build_budget_forecast_signals",
        "tab-dashboard",
        (
            (
                f"{wrapper}-shortfall",
                f"{wrapper}.signals.budget_exhaustion_before_completion.metrics.shortfall_weeks",
                138 / 37,
            ),
            (
                f"{wrapper}-shortfall-pct",
                f"{wrapper}.signals.budget_exhaustion_before_completion.metrics.shortfall_pct",
                3450 / 37,
            ),
        ),
        derivation=(
            "4week forecast minus10/37runway=138/37; "
            "divide by4 and multiply100=3450/37percent"
        ),
    )
for scenario, signal, required, current, ratio in (
    ("complete", "pace_on_track", 4, 4, 1),
    ("stalled", "pace_critically_behind", 8, 2, 0.25),
):
    POLICY_CONTRACTS += make_contracts(
        "recommendation-policies",
        "data.recommendations.pace_signals.build_required_pace_signals",
        "tab-dashboard",
        (
            (
                "pace-signal-required",
                f"pace.signals.{signal}.metrics.required_velocity_items",
                required,
            ),
            (
                "pace-signal-current",
                f"pace.signals.{signal}.metrics.current_velocity_items",
                current,
            ),
            ("pace-signal-ratio", f"pace.signals.{signal}.metrics.ratio", ratio),
        ),
        scenario=scenario,
        derivation="28calendar days=4weeks; remaining16or32; mean4or2",
    )
for scenario in ("empty", "no-deadline"):
    POLICY_CONTRACTS += make_contracts(
        "recommendation-policies",
        "data.recommendations.pace_signals.build_required_pace_signals",
        "tab-dashboard",
        (("pace-unavailable", "pace.count", 0),),
        scenario=scenario,
        derivation="No observations or no deadline means no pace assertion",
    )
for scenario, case, signal, expected in (
    ("stalled", "unstable", "unstable_delivery_scope_creep", True),
    ("complete", "unstable", "unstable_delivery_scope_creep", False),
    ("complete", "uncertain", "budget_forecast_uncertainty", True),
    ("accelerating", "surplus", "performance_surplus", True),
    ("complete", "wip", "high_wip_long_lead_time", True),
    ("complete", "wip_boundary", "high_wip_long_lead_time", False),
    ("declining", "bugs", "bug_velocity_drain", True),
    ("complete", "bugs", "bug_velocity_drain", False),
    ("stalled", "quality", "quality_scope_pressure", True),
    ("stalled", "quality_boundary", "quality_scope_pressure", False),
    ("accelerating", "dora", "dora_velocity_divergence", True),
    ("accelerating", "dora_high", "dora_velocity_divergence", False),
):
    POLICY_CONTRACTS += make_contracts(
        "recommendation-policies",
        "data.recommendations.correlation_signals.build_correlation_signals",
        "tab-dashboard",
        (
            (
                f"correlation-{case}-{signal}",
                f"correlations.{case}.present.{signal}",
                expected,
            ),
        ),
        scenario=scenario,
        selection="Actual seeded velocity frame with named auxiliary threshold calibrations",
        derivation=(
            "StalledCV106.9%; acceleration125%; decline55.56%; "
            "explicit WIP20/time8, resolution49, medium tier"
        ),
    )
POLICY_CONTRACTS += make_contracts(
    "recommendation-policies",
    "data.recommendations.correlation_signals.build_correlation_signals",
    "tab-dashboard",
    (
        (
            "zero-resolution-quality-pressure",
            "correlations.quality_zero.present.quality_scope_pressure",
            True,
        ),
    ),
    scenario="stalled",
    backlog="burndownchart-ftzd2n",
    selection="Explicit zero-resolution calibration with growing observed scope",
    derivation="Measured0percent resolution is below50;48created exceeds16completed",
)
POLICY_CONTRACTS += make_contracts(
    "recommendation-policies",
    "data.recommendations.pace_signals.build_required_pace_signals",
    "tab-dashboard",
    (
        (
            "zero-velocity-shortfall",
            "pace.signals.pace_critically_behind.metrics.gap_pct",
            100,
        ),
    ),
    scenario="zero-delivery",
    backlog="burndownchart-ftzd2n",
    derivation="Required48/4=12items/week versus measured0 is100percent shortfall",
)
