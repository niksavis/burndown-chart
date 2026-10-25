from data.demo.contract_types import make_contracts

RECOMMENDATION_CONTRACTS = ()
for scenario, total_done, ratio, recent_done, excess in (
    ("complete", 32, 1.5, 16, 50),
    ("stalled", 16, 3, 8, 200),
):
    RECOMMENDATION_CONTRACTS += make_contracts(
        "recommendations",
        "data.recommendations.scope_signals.build_scope_signals",
        "tab-dashboard",
        (
            ("scope-signal-created", "scope_growth_ratio.metrics.total_created", 48),
            (
                "scope-signal-done",
                "scope_growth_ratio.metrics.total_completed",
                total_done,
            ),
            ("scope-signal-ratio", "scope_growth_ratio.metrics.ratio", ratio),
            (
                "scope-signal-recent-created",
                "scope_creep_acceleration.metrics.recent_created",
                24,
            ),
            (
                "scope-signal-recent-done",
                "scope_creep_acceleration.metrics.recent_completed",
                recent_done,
            ),
            (
                "scope-signal-excess",
                "scope_creep_acceleration.metrics.excess_pct",
                excess,
            ),
            (
                "scope-signal-weeks-over",
                "scope_creep_acceleration.metrics.weeks_over",
                4,
            ),
        ),
        scenario=scenario,
        derivation="Six new items each week; complete4done or stalled4/0; last4weeks24created",
    )
RECOMMENDATION_CONTRACTS += make_contracts(
    "recommendations",
    "data.recommendations.velocity_signals.build_velocity_consistency_signals",
    "tab-dashboard",
    (("consistent-cv", "velocity_consistent.metrics.velocity_cv", 0),),
    derivation="Eight equal observed velocities4 imply SD0 and coefficient of variation0",
)
RECOMMENDATION_CONTRACTS += make_contracts(
    "recommendations",
    "data.recommendations.velocity_signals.build_velocity_consistency_signals",
    "tab-dashboard",
    (
        (
            "inconsistent-cv",
            "velocity_inconsistent.metrics.velocity_cv",
            100 * (32 / 7) ** 0.5 / 2,
        ),
    ),
    scenario="stalled",
    derivation="Four zeros and four fours:mean2, squared deviation sum32, samplevariance32/7",
)
for scenario, signal, recent, previous, change in (
    ("accelerating", "velocity_acceleration", 4.5, 2, 125),
    ("declining", "velocity_decline", 2, 4.5, 500 / 9),
):
    RECOMMENDATION_CONTRACTS += make_contracts(
        "recommendations",
        "data.recommendations.velocity_signals.build_velocity_trend_signals",
        "tab-dashboard",
        (
            ("trend-signal-recent", f"{signal}.metrics.recent_velocity", recent),
            (
                "trend-signal-historical",
                f"{signal}.metrics.historical_velocity",
                previous,
            ),
            ("trend-signal-change", f"{signal}.metrics.pct_change", change),
        ),
        scenario=scenario,
        derivation="Halves8 and18deliveries:means2 and4.5;125percent rise or55.56percent fall",
    )
RECOMMENDATION_CONTRACTS += make_contracts(
    "recommendations",
    "data.recommendations.velocity_signals.build_throughput_signals",
    "tab-dashboard",
    (("throughput-increase", "throughput_increase.metrics.pct_increase", 125),),
    scenario="accelerating",
    derivation="Recent18 versus previous8 =>125percent increase",
)
