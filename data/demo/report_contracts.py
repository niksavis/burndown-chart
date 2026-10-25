from dataclasses import replace

from data.demo.contract_types import make_contracts

REPORT_CONTRACTS = make_contracts(
    "report",
    "data.report.generator_metrics.calculate_all_metrics",
    "exported-html",
    (
        ("report-completed-items", "dashboard.completed_items", 32),
        ("report-remaining-items", "dashboard.remaining_items", 16),
        ("report-total-items", "dashboard.total_items", 48),
        ("report-completed-points", "dashboard.completed_points", 64),
        ("report-remaining-points", "dashboard.remaining_points", 32),
        ("report-total-points", "dashboard.total_points", 96),
        ("report-item-completion", "dashboard.items_completion_pct", 200 / 3),
        ("report-point-completion", "dashboard.points_completion_pct", 200 / 3),
        ("report-item-velocity", "dashboard.velocity_items", 4),
        ("report-point-velocity", "dashboard.velocity_points", 8),
        ("report-item-forecast", "dashboard.pert_time_items", 28),
        ("report-point-forecast", "dashboard.pert_time_points", 28),
        ("report-flow-velocity", "flow.velocity", 4),
        ("report-flow-time", "flow.flow_time", 0.7),
        ("report-flow-wip", "flow.wip", 11),
        ("report-release-frequency", "dora.deployment_frequency", 1),
        ("report-task-frequency", "dora.deployment_frequency_tasks", 1),
        ("report-failure-rate", "dora.change_failure_rate", 25),
        ("report-recovery-hours", "dora.mttr_hours", 54),
    ),
    backlog="burndownchart-imp064",
    derivation=(
        "Same48/96scope and32/64done across8weeks;16/32remain;4/8weekly =>28days. "
        "Weekly Flow medians2.5,6.5,10.5,14.5,18.5,48,48,48hours =>16.5h median=0.7d rounded. "
        "11WIP;8production releases/8weeks;2failed;54h incident recovery."
    ),
)
REPORT_CONTRACTS += make_contracts(
    "report",
    "data.report.generator_metrics.calculate_all_metrics",
    "exported-html",
    (
        ("report-initial-scope-items", "scope.initial_items", 0),
        ("report-initial-scope-points", "scope.initial_points", 0),
        ("report-created-items", "scope.created_items", 48),
        ("report-created-points", "scope.created_points", 96),
        ("report-scope-ratio", "scope.items_ratio", 1.5),
    ),
    backlog="burndownchart-imp031",
    derivation="All 48 items/96 points were created in the window. 48 created/32 done = 1.5.",
)
REPORT_CONTRACTS += make_contracts(
    "report",
    "data.report.data_loader.load_report_data",
    "exported-html",
    (
        (
            "report-recorded-window",
            "window.recorded_weeks",
            [
                "2025-W50",
                "2025-W51",
                "2025-W52",
                "2026-W01",
                "2026-W02",
                "2026-W03",
                "2026-W04",
                "2026-W05",
            ],
        ),
        (
            "report-snapshot-window",
            "window.snapshot_weeks",
            [
                "2025-W50",
                "2025-W51",
                "2025-W52",
                "2026-W01",
                "2026-W02",
                "2026-W03",
                "2026-W04",
                "2026-W05",
            ],
        ),
    ),
    backlog="burndownchart-imp032",
    derivation=(
        "The eight weeks from December 8 through January 29 include partial ISO week 5. "
        "Records and snapshots must use the same selected weeks."
    ),
)

REPORT_BACKLOGS = {
    "report-remaining-points": "burndownchart-imp021",
    "report-total-points": "burndownchart-imp021",
    "report-point-completion": "burndownchart-imp021",
    "report-point-forecast": "burndownchart-imp021",
    "report-task-frequency": "burndownchart-08ew9g",
    "report-failure-rate": "burndownchart-08ew9g",
    "report-recovery-hours": "burndownchart-qtlipm",
}
REPORT_CONTRACTS += make_contracts(
    "report",
    "data.report.generator_metrics.calculate_all_metrics",
    "exported-html",
    (
        ("report-budget-consumed", "budget.consumed_amount", 8700),
        ("report-budget-remaining", "budget.remaining_amount", 300),
        ("report-budget-utilization", "budget.consumed_percentage", 290 / 3),
        ("report-budget-burn", "budget.burn_rate", 1110),
        ("report-budget-runway", "budget.runway_weeks", 10 / 37),
    ),
    backlog="burndownchart-imp012",
    derivation="Historical allocation8700, funding9000, burn1110 and runway300/1110",
)
REPORT_CONTRACTS += make_contracts(
    "report",
    "data.report.domain_metrics.calculate_bug_metrics",
    "exported-html",
    (
        ("report-bugs-total", "bug_analysis.total_bugs", 8),
        ("report-bugs-open", "bug_analysis.open_bugs", 0),
        ("report-bugs-resolution", "bug_analysis.resolution_rate", 100),
        ("report-bugs-investment", "bug_analysis.bug_investment_pct", 25),
    ),
    derivation="8resolved bugs/8total=100%;8bugs/32completed items=25%investment",
)
REPORT_CONTRACTS += make_contracts(
    "report-four-weeks",
    "data.report.domain_metrics.calculate_scope_metrics",
    "exported-html",
    (
        ("report-window-initial-items", "scope.initial_items", 8),
        ("report-window-initial-points", "scope.initial_points", 16),
        ("report-window-created-items", "scope.created_items", 24),
        ("report-window-created-points", "scope.created_points", 48),
    ),
    backlog="burndownchart-imp021",
    derivation="Last4weeks create24/48, complete16/32; remaining16/32 implies initial8/16",
)
REPORT_CONTRACTS = tuple(
    replace(
        contract, backlog=REPORT_BACKLOGS.get(contract.calculation, contract.backlog)
    )
    for contract in REPORT_CONTRACTS
)
