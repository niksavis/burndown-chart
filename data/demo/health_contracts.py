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
