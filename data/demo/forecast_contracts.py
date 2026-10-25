from data.demo.contract_types import make_contracts

FORECAST_CONTRACTS = make_contracts(
    "weekly-forecast",
    "data.processing_weekly_forecast.generate_weekly_forecast",
    "tab-burndown",
    (
        ("next-week-items", "items.most_likely_value", 4),
        ("next-week-items-best", "items.optimistic_value", 4),
        ("next-week-items-worst", "items.pessimistic_value", 4),
        ("next-week-points", "points.most_likely_value", 8),
        ("next-week-points-best", "points.optimistic_value", 8),
        ("next-week-points-worst", "points.pessimistic_value", 8),
        ("next-week-iso-label", "items.dates", ["2026-W06"]),
    ),
    derivation="Eight equal 4-item/8-point weeks imply equal bounds. February 2 is ISO week 6.",
)
FORECAST_CONTRACTS += make_contracts(
    "daily-forecast",
    "data.processing_daily_forecast.daily_forecast",
    "tab-burndown",
    (
        ("daily-remaining-start", "down.first", 16),
        ("daily-remaining-finish", "down.last", 0),
        ("daily-completion-date", "down.end", "2026-02-26T12:00:00"),
        ("daily-unique-observations", "down.count", 29),
    ),
    backlog="burndownchart-imp064",
    selection="Evaluation noonJan29;16remaining at4perweek",
    derivation="16/(4/7)=28days;29 daily observations including initial value and completion",
)
FORECAST_CONTRACTS += make_contracts(
    "daily-forecast",
    "data.processing_daily_forecast.daily_forecast_burnup",
    "tab-burndown",
    (
        ("daily-burnup-start", "up.first", 32),
        ("daily-burnup-finish", "up.last", 48),
        ("daily-burnup-date", "up.end", "2026-02-26T12:00:00"),
    ),
    backlog="burndownchart-imp064",
    derivation="32done of48, progressing4perweek reaches48 after28days fromJan29noon",
)
FORECAST_CONTRACTS += make_contracts(
    "confidence-probability",
    "ui.dashboard_enhanced.stats._calculate_confidence_intervals",
    "tab-dashboard",
    (
        ("constant-ci50", "intervals.ci_50", 28),
        ("constant-ci80", "intervals.ci_80", 28),
        ("constant-ci95", "intervals.ci_95", 28),
    ),
    selection="Conditional constant-rate model;8observations, mean4 and SD0, forecast28days",
    derivation="A point-mass model has all completion quantiles at28days; no arbitrary margin",
)
FORECAST_CONTRACTS += make_contracts(
    "confidence-probability",
    "ui.dashboard_enhanced.stats._calculate_deadline_probability",
    "tab-dashboard",
    (
        ("constant-probability-equal", "equal", 100),
        ("constant-probability-before", "before", 0),
    ),
    selection="Same conditional point-mass model; deadlines28days and27days",
    derivation="Constant28day completion is on time at28days and late at27days",
)
FORECAST_CONTRACTS += make_contracts(
    "confidence-probability",
    "ui.dashboard_enhanced.stats._calculate_deadline_probability",
    "tab-dashboard",
    (("variable-probability-equal", "equal", 50),),
    scenario="stalled",
    selection="Positive measured variance; deadline equals modeled center28days",
    derivation="Normal-model symmetry puts half of its probability on either side of the mean",
)
FORECAST_CONTRACTS += make_contracts(
    "confidence-probability",
    "ui.dashboard_enhanced.stats._calculate_deadline_probability",
    "tab-dashboard",
    (("zero-velocity-probability", "equal", None),),
    scenario="zero-delivery",
    backlog="burndownchart-imp017",
    derivation="Eight zero-delivery weeks provide no finite forecast or probability.",
)
FORECAST_CONTRACTS += make_contracts(
    "pace",
    "data.velocity_projections.calculate_required_velocity",
    "tab-dashboard",
    (
        ("required-items", "items.required", 4),
        ("required-points", "points.required", 8),
    ),
    backlog="burndownchart-imp021",
    selection="Calendar midnightJan29 to midnightFeb26,28days",
    derivation="16items/32points remaining divided by4calendarweeks =>4/8perweek",
)
FORECAST_CONTRACTS += make_contracts(
    "pace",
    "data.velocity_projections.calculate_velocity_gap",
    "tab-dashboard",
    (
        ("pace-gap", "items.gap.gap", 0),
        ("pace-gap-percent", "items.gap.percent", 0),
        ("pace-ratio", "items.gap.ratio", 1),
    ),
    selection="Calendar28day deadline; current4/week and required4/week",
    derivation="Equal required and measured item rates have no gap and ratio1",
)
FORECAST_CONTRACTS += make_contracts(
    "pace",
    "data.velocity_projections.assess_pace_health",
    "tab-dashboard",
    (("pace-status", "items.health.status", "on_pace"),),
    derivation="On the explicit28calendar-day basis, required4 equals observed4",
)
for scenario, current, change in (
    ("accelerating", 4.5, 125),
    ("declining", 2, -500 / 9),
):
    FORECAST_CONTRACTS += make_contracts(
        "advanced-statistics",
        "ui.dashboard_enhanced.stats._calculate_velocity_statistics",
        "tab-dashboard",
        (
            ("trend-recent-average", "recent_avg", current),
            ("trend-percent-change", "recent_change", change),
        ),
        scenario=scenario,
        derivation="The four-week halves total 8 and 18 items. Their means are 2 and 4.5.",
    )
FORECAST_CONTRACTS += make_contracts(
    "advanced-points",
    "ui.dashboard_enhanced.stats._calculate_velocity_statistics",
    "tab-dashboard",
    (("variable-points-mean", "mean", 18), ("variable-points-sd", "std_dev", 96**0.5)),
    scenario="variable-points",
    selection="Items stay4/week; points4,8,12,16,20,24,28,32",
    derivation="Sum144/8=18; centered squared deviations672, samplevariance672/7=96",
)

FORECAST_CONTRACTS += make_contracts(
    "mounted-confidence",
    "ui.dashboard.create_comprehensive_dashboard",
    "tab-dashboard",
    (
        ("mounted-constant-probability", "deadline_probability_items", 100),
        ("mounted-constant-point-probability", "deadline_probability_points", 100),
        ("mounted-constant-ci95", "ci_95", 28),
    ),
    backlog="burndownchart-imp017",
    selection="Real render boundary;8constant weeks; conditional28day forecast/deadline",
    derivation="The conditional constant model has28day quantiles and100% on-time at28days",
)
FORECAST_CONTRACTS += make_contracts(
    "mounted-confidence",
    "ui.dashboard.create_comprehensive_dashboard",
    "tab-dashboard",
    (("mounted-variable-point-probability", "deadline_probability_points", 50),),
    scenario="variable-points",
    backlog="burndownchart-imp017",
    selection="Constant item rates, variable point rates; forecast equals28day deadline",
    derivation="Point variance is positive. A symmetric model has50% at its center.",
)
for scenario in ("no-deadline", "zero-delivery"):
    FORECAST_CONTRACTS += make_contracts(
        "mounted-confidence",
        "ui.dashboard.create_comprehensive_dashboard",
        "tab-dashboard",
        (("mounted-unavailable-probability", "deadline_probability_items", None),),
        scenario=scenario,
        backlog="burndownchart-imp017",
        derivation="Missing deadline or no delivery rate cannot establish an on-time probability",
    )
