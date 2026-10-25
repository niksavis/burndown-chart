from data.demo.contract_types import make_contracts

FRACTIONAL_CONTRACTS = make_contracts(
    "scope",
    "data.jira.scope_calculator.calculate_jira_project_scope",
    "tab-dashboard",
    (
        ("fractional-completed-points", "completed_points", 6.5),
        ("fractional-remaining-points", "remaining_points", 0.0),
        ("fractional-completed-items", "completed_items", 3),
    ),
    scenario="fractional-points",
    backlog="burndownchart-imp021",
    selection="Three completed issues in the first recorded week",
    derivation="Enumerated 2.5+3.5+0.5=6.5 points; all three issues are completed.",
)
FRACTIONAL_CONTRACTS += make_contracts(
    "statistics",
    "data.jira.data_transformer.jira_to_csv_format",
    "tab-statistics-data",
    (
        ("fractional-statistics-completed", "completed_points", 6.5),
        ("fractional-statistics-created", "created_points", 6.5),
    ),
    scenario="fractional-points",
    backlog="burndownchart-imp021",
    selection="First recorded week, containing all three fractional issues",
    derivation="Each issue is created and completed in the same week; 2.5+3.5+0.5=6.5.",
)
FRACTIONAL_CONTRACTS += make_contracts(
    "weekly-forecast",
    "data.processing_weekly_forecast.generate_weekly_forecast",
    "tab-burndown",
    (("fractional-next-week-points", "points.most_likely_value", 6.5),),
    scenario="fractional-points",
    backlog="burndownchart-imp021",
    selection="One recorded week containing three completed issues",
    derivation="The sole recorded weekly delivery is 2.5+3.5+0.5=6.5 points.",
)
FRACTIONAL_CONTRACTS += make_contracts(
    "report",
    "data.report.generator_metrics.calculate_all_metrics",
    "exported-html",
    (
        ("fractional-report-completed", "dashboard.completed_points", 6.5),
        ("fractional-report-total", "dashboard.total_points", 6.5),
        ("fractional-report-remaining", "dashboard.remaining_points", 0.0),
    ),
    scenario="fractional-points",
    backlog="burndownchart-imp021",
    selection="All three fractional issues and their single recorded delivery week",
    derivation="2.5+3.5+0.5=6.5 total and completed points; no unfinished issues.",
)
