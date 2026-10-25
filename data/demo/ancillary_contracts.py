from data.demo.contract_types import make_contracts

ANCILLARY_CONTRACTS = make_contracts(
    "metric-forecast",
    "data.metrics.forecast_calculator.calculate_forecast",
    "tab-flow-metrics",
    (
        ("metric-weighted-forecast", "weighted.forecast_value", 4),
        ("metric-forecast-sample", "weighted.weeks_available", 8),
        ("metric-forecast-confidence", "weighted.confidence", "established"),
    ),
    backlog="burndownchart-imp030",
    derivation="Eight equal observations forecast4. Eight samples must not rank below four.",
)
ANCILLARY_CONTRACTS += make_contracts(
    "metric-forecast",
    "data.metrics.forecast_calculator.calculate_ewma_forecast",
    "tab-flow-metrics",
    (("metric-ewma-forecast", "ewma.forecast_value", 4),),
    derivation="An exponentially weighted average of identical4item observations stays4",
)
ANCILLARY_CONTRACTS += make_contracts(
    "metric-forecast",
    "data.metrics.forecast_calculator.calculate_flow_load_range",
    "tab-flow-metrics",
    (
        ("wip-range-low", "wip_range.lower", 9),
        ("wip-range-high", "wip_range.upper", 13),
    ),
    selection="WIP11 calibration;20percent display range, rounded to whole items",
    derivation="11times0.8=8.8 and11times1.2=13.2, displayed as9 and13",
)
ANCILLARY_CONTRACTS += make_contracts(
    "metric-forecast",
    "data.metrics.blending.get_blend_metadata",
    "tab-dashboard",
    (
        ("current-blended-value", "blend.blended", 4),
        ("current-actual-weight", "blend.actual_percent", 60),
        ("current-forecast-weight", "blend.forecast_percent", 40),
        ("current-blend-day", "blend.day_name", "Thursday"),
    ),
    derivation="January29 isThursday. Configured60/40 blend of identical4item values stays4.",
)
ANCILLARY_CONTRACTS += make_contracts(
    "bugs",
    "data.bug_processing.calculate_bug_metrics_summary",
    "tab-bug-analysis",
    (
        ("stalled-open-bugs", "open_bugs", 4),
        ("stalled-closed-bugs", "closed_bugs", 4),
        ("stalled-bug-resolution", "resolution_rate", 0.5),
        ("stalled-open-bug-age", "avg_age_days", 24),
        ("stalled-open-bug-points", "open_bug_points", 2),
    ),
    scenario="stalled",
    derivation="Odd weeks leave4bugs open at0.5point each. Ages45/31/17/3whole days average24.",
)
ANCILLARY_CONTRACTS += make_contracts(
    "bug-forecast",
    "data.bug_processing.forecast_bug_resolution",
    "tab-bug-analysis",
    (
        ("bug-closure-rate", "avg_closure_rate", 0.5),
        ("bug-likely-weeks", "most_likely_weeks", 8),
        ("bug-optimistic-weeks", "optimistic_weeks", 4),
        ("bug-pessimistic-unavailable", "pessimistic_weeks", None),
        ("bug-forecast-sample", "weeks_analyzed", 8),
        ("bug-forecast-date", "most_likely_date", "2026-03-26"),
    ),
    scenario="stalled",
    backlog="burndownchart-imp015",
    derivation="Four open bugs. Rates1/0.5/0 imply4/8/unbounded weeks; closure SD0.5.",
)
