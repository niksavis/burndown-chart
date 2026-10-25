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
