from dataclasses import replace

from data.demo.contract_types import make_contracts

HEALTH_CONTRACTS = make_contracts(
    "health-empty",
    "data.project_health_calculator.calculate_comprehensive_project_health",
    "tab-dashboard",
    (("empty-health-score", "overall_score", None),),
    scenario="empty",
    backlog="burndownchart-imp016",
    selection="No measured signals in the empty project",
    derivation="No observed contribution exists from which to calculate an overall health score",
)
for dimension in (
    "delivery",
    "predictability",
    "quality",
    "efficiency",
    "sustainability",
    "financial",
):
    HEALTH_CONTRACTS += make_contracts(
        "health-empty",
        "data.project_health_calculator.calculate_comprehensive_project_health",
        "tab-dashboard",
        (
            (f"empty-health-{dimension}", f"dimensions.{dimension}.score", None),
            (f"empty-health-{dimension}-weight", f"dimensions.{dimension}.weight", 0),
        ),
        scenario="empty",
        backlog="burndownchart-imp016",
        derivation="An absent dimension has no measured score and contributes no weight",
    )
HEALTH_CONTRACTS += make_contracts(
    "health-stage",
    "data.project_health_calculator._determine_project_stage",
    "tab-dashboard",
    (
        ("complete-stage", "complete", "mid"),
        ("stalled-stage", "stalled", "early"),
        ("singleton-stage", "singleton", "late"),
    ),
    derivation="Completion32/48,16/48,1/1 falls in the documented25/50/75percent stage bands",
)
HEALTH_CONTRACTS += make_contracts(
    "health-calibration",
    "data.project_health_calculator._calculate_delivery_dimension",
    "tab-dashboard",
    (
        ("delivery-policy-score", "delivery.score", 58.21392340793509),
        ("delivery-policy-weight", "delivery.weight", 25),
    ),
    selection="Source-derived calibration: completion2/3, stabletrend, velocity4",
    derivation="Progress20 + stabletrend25 + throughput35/(1+exp(0.5)) =58.21392340793509",
)
HEALTH_CONTRACTS += make_contracts(
    "health-calibration",
    "data.project_health_calculator._calculate_predictability_dimension",
    "tab-dashboard",
    (
        ("predictability-policy-score", "predictability.score", 83.62232515468625),
        ("predictability-policy-weight", "predictability.weight", 20),
    ),
    selection="Conditional constant-rate calibration: CV0, schedulevariance0, confidence100",
    derivation="Consistency48.62232515468625 + schedule15 + confidence20 =83.62232515468625",
)
HEALTH_CONTRACTS += make_contracts(
    "health-calibration",
    "data.project_health_calculator._calculate_efficiency_dimension",
    "tab-dashboard",
    (("efficiency-policy-score", "efficiency.score", 89.70795453645152),),
    backlog="burndownchart-imp016",
    selection="Efficiency62.7604167%; median-of-weekly-medians0.6875days; leadtime absent",
    derivation="Components40+27.28096590233864 out of75 =>89.70795453645152% normalized",
)
HEALTH_CONTRACTS += make_contracts(
    "health-calibration",
    "data.project_health_calculator._calculate_sustainability_dimension",
    "tab-dashboard",
    (("sustainability-policy-score", "sustainability.score", 58.19230769230769),),
    backlog="burndownchart-imp016",
    selection="Scope percent unavailable at zero baseline; WIP11,velocity4,typecounts8each",
    derivation="WIP700/39 + distribution509/30 out of60 =>58.19230769230769% normalized",
)

HEALTH_CONTRACTS += make_contracts(
    "mounted-health",
    "callbacks.visualization_helpers.dashboard_tab._render_dashboard_tab",
    "tab-dashboard",
    (
        (
            "mounted-health-completion",
            "inputs.dashboard_metrics.completion_percentage",
            200 / 3,
        ),
        (
            "mounted-health-velocity",
            "inputs.dashboard_metrics.current_velocity_items",
            4,
        ),
        ("mounted-health-cv", "inputs.dashboard_metrics.velocity_cv", 0),
        ("mounted-health-trend", "inputs.dashboard_metrics.trend_direction", "stable"),
        ("mounted-health-change", "inputs.dashboard_metrics.recent_velocity_change", 0),
        ("mounted-health-dora", "available.dora_metrics", True),
        ("mounted-health-release-rate", "inputs.dora_metrics.deployment_frequency", 1),
        ("mounted-health-failure-rate", "inputs.dora_metrics.change_failure_rate", 25),
        ("mounted-health-recovery", "inputs.dora_metrics.mttr_hours", 54),
        ("mounted-health-flow", "available.flow_metrics", True),
        ("mounted-health-flow-velocity", "inputs.flow_metrics.velocity", 4),
        ("mounted-health-flow-time", "inputs.flow_metrics.flow_time", 0.6875),
        (
            "mounted-health-flow-efficiency",
            "inputs.flow_metrics.efficiency",
            62.76041666666667,
        ),
        ("mounted-health-flow-wip", "inputs.flow_metrics.wip", 11),
        (
            "mounted-health-flow-count",
            "inputs.flow_metrics.work_distribution.total",
            32,
        ),
        ("mounted-health-bugs", "available.bug_metrics", True),
        ("mounted-health-resolution", "inputs.bug_metrics.resolution_rate", 100),
        (
            "mounted-health-bug-duration",
            "inputs.bug_metrics.avg_resolution_time_days",
            2.25,
        ),
        (
            "mounted-health-bug-capacity",
            "inputs.bug_metrics.capacity_consumed_by_bugs",
            0,
        ),
        ("mounted-health-open-bugs", "inputs.bug_metrics.open_bugs", 0),
        ("mounted-health-bug-age", "inputs.bug_metrics.avg_age_days", 0),
        ("mounted-health-budget", "available.budget_metrics", True),
    ),
    selection="Actual Dashboard preparation through the comprehensive-health boundary",
    derivation=(
        "32/48completed, constant4/week; 8production releases/8weeks;2failures/8=25%; "
        "54h recovery. Weekly Flow medians give0.6875days; efficiency62.7604167%;11WIP. "
        "8bugs allresolved54h; no openbug points so capacity0; configured budget is available."
    ),
)
HEALTH_CONTRACTS += make_contracts(
    "mounted-health",
    "callbacks.visualization_helpers.dashboard_tab._render_dashboard_tab",
    "tab-dashboard",
    (
        (
            "mounted-stalled-bug-capacity",
            "inputs.bug_metrics.capacity_consumed_by_bugs",
            1 / 48,
        ),
    ),
    scenario="stalled",
    backlog="burndownchart-67xisu",
    derivation="Four open bugs of0.5points each divided by96project points =1/48capacity",
)

MOUNTED_BACKLOGS = {
    "mounted-health-failure-rate": "burndownchart-08ew9g",
    "mounted-health-recovery": "burndownchart-qtlipm",
    "mounted-health-bug-duration": "burndownchart-lokdeu",
    "mounted-health-budget": "burndownchart-q4yq9r",
}
HEALTH_CONTRACTS = tuple(
    replace(
        contract, backlog=MOUNTED_BACKLOGS.get(contract.calculation, contract.backlog)
    )
    for contract in HEALTH_CONTRACTS
)
