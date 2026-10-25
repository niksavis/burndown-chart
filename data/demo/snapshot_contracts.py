from data.demo.contract_types import make_contracts

SNAPSHOT_CONTRACTS = ()
WEEKS = (
    "2025-W50",
    "2025-W51",
    "2025-W52",
    "2026-W01",
    "2026-W02",
    "2026-W03",
    "2026-W04",
    "2026-W05",
)
for index, (week, hours) in enumerate(
    zip(WEEKS, (2.5, 6.5, 10.5, 14.5, 18.5, 48, 48, 48), strict=True)
):
    efficiency = 200 / 3 if index < 5 else 56.25
    failures = 1 if index in {0, 5} else 0
    SNAPSHOT_CONTRACTS += make_contracts(
        "persisted-metrics",
        "data.metrics.historical_calculator.calculate_metrics_for_last_n_weeks",
        "tab-flow-metrics",
        (
            (
                f"persisted-flow-count-{week}",
                f"{week}.flow_velocity.completed_count",
                4,
            ),
            (
                f"persisted-flow-median-{week}",
                f"{week}.flow_time.median_days",
                hours / 24,
            ),
            (f"persisted-flow-mean-{week}", f"{week}.flow_time.avg_days", hours / 24),
            (f"persisted-flow-time-n-{week}", f"{week}.flow_time.completed_count", 4),
            (
                f"persisted-flow-efficiency-{week}",
                f"{week}.flow_efficiency.overall_pct",
                efficiency,
            ),
            (
                f"persisted-flow-efficiency-n-{week}",
                f"{week}.flow_efficiency.completed_count",
                4,
            ),
        ),
        selection=f"Persisted weekly Flow snapshot {week}",
        backlog="burndownchart-imp064",
        derivation=(
            "4 done/week. First 20 durations 1..20h, equal active/waiting thirds; "
            "last 12 active 27/48h."
        ),
    )
    SNAPSHOT_CONTRACTS += make_contracts(
        "persisted-metrics",
        "data.metrics.historical_calculator.calculate_metrics_for_last_n_weeks",
        "tab-dora-metrics",
        (
            (
                f"persisted-prod-tasks-{week}",
                f"{week}.dora_deployment_frequency.deployment_count",
                1,
            ),
            (
                f"persisted-prod-releases-{week}",
                f"{week}.dora_deployment_frequency.release_count",
                1,
            ),
            (
                f"persisted-prod-denominator-{week}",
                f"{week}.dora_change_failure_rate.total_deployments",
                1,
            ),
            (
                f"persisted-prod-failed-{week}",
                f"{week}.dora_change_failure_rate.failed_deployments",
                failures,
            ),
            (
                f"persisted-prod-cfr-{week}",
                f"{week}.dora_change_failure_rate.change_failure_rate_percent",
                100 * failures,
            ),
        ),
        backlog="burndownchart-08ew9g",
        selection=f"Completed production operational tasks in {week}; elapsed release date",
        derivation=(
            "One production OPS per week; failures weeks 0/5. "
            "TEST OPS99 is excluded even when release matches."
        ),
    )

SNAPSHOT_CONTRACTS += make_contracts(
    "persisted-metrics",
    "data.metrics.historical_calculator.calculate_metrics_for_last_n_weeks",
    "tab-dora-metrics",
    (
        (
            "unreleased-flag-completed-task",
            "2026-W05.dora_deployment_frequency.deployment_count",
            1,
        ),
        (
            "unreleased-flag-elapsed-release",
            "2026-W05.dora_deployment_frequency.release_count",
            1,
        ),
    ),
    scenario="unreleased-version",
    selection="Completed OPS8 and elapsed January29 release date; version flag is false",
    derivation=(
        "The documented repository deployment filter is completed task plus elapsed release date. "
        "The released flag alone does not exclude this named edge; "
        "no new eligibility rule is assumed."
    ),
)
