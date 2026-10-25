from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CalculationContract:
    calculation: str
    scenario: str
    source: str
    field: str
    expected: Any
    producer: str
    surface: str
    backlog: str = ""
    selection: str = "All eight recorded weeks"
    derivation: str = "Synthetic source enumeration"


CONTRACTS = (
    CalculationContract(
        "scope-items",
        "complete",
        "scope",
        "total_items",
        48,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-scope-tracking",
    ),
    CalculationContract(
        "scope-points",
        "complete",
        "scope",
        "total_points",
        96.0,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-scope-tracking",
        "burndownchart-imp021",
    ),
    CalculationContract(
        "completed-items",
        "complete",
        "scope",
        "completed_items",
        32,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-dashboard",
    ),
    CalculationContract(
        "completed-points",
        "complete",
        "scope",
        "completed_points",
        64.0,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-dashboard",
        "burndownchart-imp021",
    ),
    CalculationContract(
        "remaining-items",
        "complete",
        "scope",
        "remaining_items",
        16,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-burndown",
    ),
    CalculationContract(
        "remaining-points",
        "complete",
        "scope",
        "remaining_points",
        32.0,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-burndown",
        "burndownchart-imp021",
    ),
    CalculationContract(
        "fractional-points",
        "fractional-points",
        "scope",
        "total_points",
        6.5,
        "data.jira.scope_calculator.calculate_jira_project_scope",
        "tab-scope-tracking",
        "burndownchart-imp021",
    ),
    CalculationContract(
        "weekly-completed-items",
        "complete",
        "statistics",
        "completed_items",
        32,
        "data.jira.data_transformer.jira_to_csv_format",
        "tab-statistics-data",
    ),
    CalculationContract(
        "weekly-completed-points",
        "complete",
        "statistics",
        "completed_points",
        64.0,
        "data.jira.data_transformer.jira_to_csv_format",
        "tab-statistics-data",
    ),
    CalculationContract(
        "observed-zero-delivery",
        "zero-delivery",
        "statistics",
        "completed_items",
        0,
        "data.jira.data_transformer.jira_to_csv_format",
        "tab-statistics-data",
    ),
    CalculationContract(
        "stalled-delivery",
        "stalled",
        "statistics",
        "completed_items",
        16,
        "data.jira.data_transformer.jira_to_csv_format",
        "tab-statistics-data",
        "burndownchart-imp015",
    ),
    CalculationContract(
        "missing-budget",
        "missing-signals",
        "budget",
        "configured",
        None,
        "data.persistence.sqlite.budget.BudgetMixin.get_budget_settings",
        "tab-dashboard",
        "burndownchart-imp016",
    ),
)


def _contracts(
    source: str,
    producer: str,
    surface: str,
    cases: tuple[tuple[str, str, Any], ...],
    *,
    scenario: str = "complete",
    backlog: str = "",
    selection: str = "All eight recorded weeks",
    derivation: str,
) -> tuple[CalculationContract, ...]:
    return tuple(
        CalculationContract(
            name,
            scenario,
            source,
            field,
            expected,
            producer,
            surface,
            backlog,
            selection,
            derivation,
        )
        for name, field, expected in cases
    )


CONTRACTS += _contracts(
    "advanced-statistics",
    "ui.dashboard_enhanced.stats._calculate_velocity_statistics",
    "tab-dashboard",
    (
        ("velocity-mean", "mean", 4),
        ("velocity-median", "median", 4),
        ("velocity-sd", "std_dev", 0),
        ("velocity-cv", "cv", 0),
        ("recent-velocity", "recent_avg", 4),
        ("velocity-change", "recent_change", 0),
    ),
    derivation="Eight observations all equal four: mean=median=4; SD=CV=change=0",
)
CONTRACTS += _contracts(
    "advanced-statistics",
    "ui.dashboard_enhanced.stats._calculate_velocity_statistics",
    "tab-dashboard",
    (("singleton-sd", "std_dev", None),),
    scenario="singleton",
    backlog="burndownchart-imp018",
    selection="One recorded observation",
    derivation="Sample SD needs at least two observations; one is unavailable",
)
CONTRACTS += _contracts(
    "averages",
    "data.processing_averages.calculate_weekly_averages",
    "tab-dashboard",
    (
        ("observed-items-mean", "items", 4),
        ("observed-points-mean", "points", 8),
        ("observed-items-median", "median_items", 4),
        ("observed-points-median", "median_points", 8),
    ),
    scenario="sparse",
    backlog="burndownchart-imp014",
    selection="Three observed weeks; other five absent",
    derivation="Three measured observations 4items/8points; absence is not zero",
)
CONTRACTS += _contracts(
    "rates",
    "data.processing_rates.calculate_rates",
    "tab-burndown",
    (
        ("pert-items-days", "days_items", 28),
        ("pert-points-days", "days_points", 28),
        ("optimistic-items-rate", "optimistic_items", 4 / 7),
        ("pessimistic-items-rate", "pessimistic_items", 4 / 7),
        ("optimistic-points-rate", "optimistic_points", 8 / 7),
        ("pessimistic-points-rate", "pessimistic_points", 8 / 7),
    ),
    backlog="burndownchart-imp021",
    derivation="Constant velocity4items/8points per7days; 16items/32points remaining =>28days",
)
CONTRACTS += _contracts(
    "rates",
    "data.processing_rates.calculate_rates",
    "tab-burndown",
    (
        ("zero-pessimistic-items", "pessimistic_items", 0),
        ("zero-pessimistic-points", "pessimistic_points", 0),
    ),
    scenario="stalled",
    backlog="burndownchart-imp015",
    derivation="Observed weeks alternate4/0items and8/0points; smallest values are zero",
)
CONTRACTS += _contracts(
    "flow-velocity",
    "data.flow_metrics.calculate_flow_velocity",
    "tab-flow-metrics",
    (
        ("flow-weekly-velocity", "value", 4),
        ("flow-feature-count", "breakdown.Feature", 8),
        ("flow-defect-count", "breakdown.Defect", 8),
        ("flow-risk-count", "breakdown.Risk", 8),
        ("flow-debt-count", "breakdown.Technical Debt", 8),
    ),
    derivation="Four completed types once per week over56days =>32/8=4 and8each",
)
CONTRACTS += _contracts(
    "flow-distribution",
    "data.flow_metrics.calculate_flow_distribution",
    "tab-flow-metrics",
    (
        ("flow-feature-share", "value.Feature", 25),
        ("flow-defect-share", "value.Defect", 25),
        ("flow-risk-share", "value.Risk", 25),
        ("flow-debt-share", "value.Technical Debt", 25),
    ),
    derivation="Eight completed issues in each category, divided by32 completed =>25percent each",
)
CONTRACTS += _contracts(
    "flow-load",
    "data.flow_metrics.calculate_flow_load",
    "tab-flow-metrics",
    (("flow-wip", "value", 11),),
    derivation="Open statuses: InProgress4 +Review4 +Testing3 =11; ToDo3/Blocked2 excluded",
)
CONTRACTS += _contracts(
    "flow-time",
    "data.flow_metrics_time.calculate_flow_time",
    "tab-flow-metrics",
    (("flow-time-median", "value", 0.4375), ("flow-time-mean", "mean_days", 0.4375)),
    selection="Twenty completed keys listed in devtools.calculation_sources.LEAD_SAMPLE",
    derivation="Durations1..20hours =>mean=median10.5h /24=0.4375days",
)
CONTRACTS += _contracts(
    "flow-efficiency",
    "data.flow_metrics.calculate_flow_efficiency",
    "tab-flow-metrics",
    (("flow-efficiency", "value", 200 / 3),),
    selection="Twenty completed keys listed in devtools.calculation_sources.LEAD_SAMPLE",
    derivation="Equal thirds in InProgress/Review/Testing; two active thirds=66.6667percent",
)
CONTRACTS += _contracts(
    "dora-deployments",
    "data.metrics._weekly_dora_calc._calculate_deployment_frequency",
    "tab-dora-metrics",
    (
        ("deployment-count", "deployment_count", 8),
        ("release-count", "release_count", 8),
    ),
    selection="Eight production OPS releases over56days; TEST deployment excluded",
    derivation="Eight unique weekly production deployments /8weeks=1perweek",
)
CONTRACTS += _contracts(
    "dora-failures",
    "data.dora._change_fail_rate.calculate_change_failure_rate",
    "tab-dora-metrics",
    (
        ("failure-rate", "value", 25),
        ("failure-denominator", "total_deployments", 8),
        ("failure-numerator", "failed_deployments", 2),
    ),
    derivation="Two failed production deployments in eight =>25percent",
)
CONTRACTS += _contracts(
    "dora-lead",
    "data.dora._lead_time.calculate_lead_time_for_changes",
    "tab-dora-metrics",
    (
        ("lead-median-hours", "median_hours", 19.5),
        ("lead-mean-hours", "mean_hours", 19.5),
        ("lead-sample-size", "sample_count", 20),
    ),
    selection="Explicit first20 completed development keys, each released next midnight",
    derivation="Start-to-Done1..20hours plus9hours until release =>10..29hours; center19.5; n20",
)
CONTRACTS += _contracts(
    "dora-lead",
    "data.dora._lead_time.calculate_lead_time_for_changes",
    "tab-dora-metrics",
    (("lead-p95-hours", "p95_hours", 28.05),),
    backlog="burndownchart-imp020",
    selection="Same explicit twenty-observation lead-time sample",
    derivation="Linear p95 at index18.05 between28h and29h =>28.05h; IMP-020 convention",
)
CONTRACTS += _contracts(
    "dora-recovery",
    "data.dora._mttr.calculate_mean_time_to_recovery",
    "tab-dora-metrics",
    (("recovery-hours", "mean_hours", 54),),
    selection="Resolved production bugs; TEST incidents excluded",
    backlog="burndownchart-qtlipm",
    derivation="Each incident Monday09:00 through Wednesday15:00 =>54hours",
)
CONTRACTS += _contracts(
    "bugs",
    "data.bug_processing.calculate_bug_metrics_summary",
    "tab-bug-analysis",
    (
        ("bugs-total", "total_bugs", 8),
        ("bugs-open", "open_bugs", 0),
        ("bugs-closed", "closed_bugs", 8),
        ("bugs-resolution-rate", "resolution_rate", 1),
        ("bugs-resolution-days", "avg_resolution_time_days", 2.25),
        ("bugs-points", "total_bug_points", 12),
        ("bugs-recent-created", "bugs_created_last_4_weeks", 4),
        ("bugs-recent-resolved", "bugs_resolved_last_4_weeks", 4),
    ),
    backlog="burndownchart-lokdeu",
    derivation="One1.5point bug perweek; eight allresolved after54hours; trailing4weeks contains4",
)
for _week, _time, _cost, _budget in (
    ("2025-W50", 8, 1000, 8000),
    ("2026-W01", 9, 1200, 9500),
    ("2026-W03", 10, 1100, 9000),
):
    CONTRACTS += _contracts(
        f"budget-at-{_week}",
        "data.budget_calculator_core.get_budget_at_week",
        "tab-dashboard",
        (
            (f"budget-time-{_week}", "time_allocated_weeks", _time),
            (f"budget-cost-{_week}", "team_cost_per_week_eur", _cost),
            (f"budget-total-{_week}", "budget_total_eur", _budget),
        ),
        backlog="burndownchart-imp013",
        selection=f"Effective budget at {_week}",
        derivation=(
            "Baseline8weeks/1000weekly/8000total; week3adds1/200/1500; "
            "week5adds1/-100/-500; settings hold latest"
        ),
    )
