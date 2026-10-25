from typing import Any

import pandas as pd

from data.budget_calculator_core import get_budget_at_week
from data.bug_processing import calculate_bug_metrics_summary, calculate_bug_statistics
from data.demo.config import AS_OF, START
from data.demo.contracts import CalculationContract
from data.dora_metrics import (
    calculate_change_failure_rate,
    calculate_lead_time_for_changes,
    calculate_mean_time_to_recovery,
    is_production_environment,
)
from data.fixversion_matcher import build_fixversion_release_map
from data.flow_metrics import (
    calculate_flow_distribution,
    calculate_flow_efficiency,
    calculate_flow_load,
    calculate_flow_time,
    calculate_flow_velocity,
)
from data.metrics._weekly_dora_calc import _calculate_deployment_frequency
from data.metrics._weekly_issue_prep import load_and_merge_changelog
from data.metrics_snapshots import clear_snapshots_cache
from data.persistence import PersistenceBackend
from data.processing_averages import calculate_weekly_averages
from data.processing_rates import calculate_rates
from ui.dashboard_enhanced.stats import _calculate_velocity_statistics

LEAD_SAMPLE = (1, 2, 3, 4, 7, 8, 9, 10, 13, 14, 15, 16, 19, 20, 21, 22, 25, 26, 27, 28)


class CalculationSources:
    def __init__(self, backend: PersistenceBackend) -> None:
        self.backend = backend
        self.cache: dict[tuple[str, str], dict] = {}

    def read(self, contract: CalculationContract) -> Any:
        key = (contract.scenario, contract.source)
        if key not in self.cache:
            profile_id = f"demo-{contract.scenario}"
            self.backend.set_app_state("active_profile_id", profile_id)
            self.backend.set_app_state("active_query_id", "main")
            clear_snapshots_cache()
            self.cache[key] = self._calculate(profile_id, contract.source)
        value: Any = self.cache[key]
        for part in contract.field.split("."):
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value

    def _issues(self, profile_id: str) -> list[dict]:
        issues = self.backend.get_issues(profile_id, "main")
        return load_and_merge_changelog(self.backend, issues, profile_id, "main")[0]

    def _statistics(self, profile_id: str, source: str) -> dict:
        statistics = self.backend.get_statistics(profile_id, "main")
        if source == "advanced-statistics":
            return _calculate_velocity_statistics(pd.DataFrame(statistics))
        if source == "averages":
            values = calculate_weekly_averages(statistics, data_points_count=8)
            return dict(
                zip(
                    ("items", "points", "median_items", "median_points"),
                    values,
                    strict=True,
                )
            )
        if source == "rates":
            scope = self.backend.get_scope(profile_id, "main") or {}
            values = calculate_rates(
                pd.DataFrame(statistics),
                scope.get("remaining_items", 0),
                scope.get("remaining_points", 0),
                3,
            )
            names = (
                "days_items",
                "optimistic_items",
                "pessimistic_items",
                "days_points",
                "optimistic_points",
                "pessimistic_points",
            )
            return dict(zip(names, values, strict=True))
        raise ValueError(f"Unknown statistical diagnostic source: {source}")

    def _calculate(self, profile_id: str, source: str) -> dict:
        if source in {"advanced-statistics", "averages", "rates"}:
            return self._statistics(profile_id, source)
        if source.startswith("budget-at-"):
            return (
                get_budget_at_week(
                    profile_id, "main", source.removeprefix("budget-at-")
                )
                or {}
            )
        issues = self._issues(profile_id)
        development = [
            i
            for i in issues
            if i["project_key"] == "DEMO" and i["issue_type"] != "Epic"
        ]
        if source.startswith("flow-"):
            return _flow(source, development)
        if source.startswith("dora-"):
            return _dora(source, issues, development)
        if source == "bugs":
            bugs = [issue for issue in development if issue["issue_type"] == "Bug"]
            weekly = calculate_bug_statistics(bugs, START, AS_OF)
            return calculate_bug_metrics_summary(
                bugs, bugs, weekly, all_project_issues=development
            )
        raise ValueError(f"Unknown calculation diagnostic source: {source}")


def _flow(source: str, issues: list[dict]) -> dict:
    producers = {
        "flow-velocity": calculate_flow_velocity,
        "flow-load": calculate_flow_load,
        "flow-distribution": calculate_flow_distribution,
        "flow-time": calculate_flow_time,
        "flow-efficiency": calculate_flow_efficiency,
    }
    if source in {"flow-time", "flow-efficiency"}:
        selected = {f"DEMO-{number}" for number in LEAD_SAMPLE}
        issues = [issue for issue in issues if issue["issue_key"] in selected]
    return producers[source](issues, time_period_days=56)


def _dora(source: str, issues: list[dict], development: list[dict]) -> dict:
    deployments = [
        issue
        for issue in issues
        if issue["project_key"] == "OPS"
        and is_production_environment(issue, "customfield_10003=PROD")
    ]
    incidents = [
        issue
        for issue in development
        if issue["issue_type"] == "Bug"
        and is_production_environment(issue, "customfield_10003=PROD")
    ]
    if source == "dora-deployments":
        return _calculate_deployment_frequency(
            deployments,
            ["Done"],
            "eight-week-selection",
            START.replace(tzinfo=None),
            AS_OF.replace(tzinfo=None),
            set(),
            build_fixversion_release_map(deployments),
        )
    if source == "dora-failures":
        return calculate_change_failure_rate(
            deployments, incidents, time_period_days=56
        )
    if source == "dora-recovery":
        return calculate_mean_time_to_recovery(incidents, time_period_days=56)
    if source == "dora-lead":
        selected = {f"DEMO-{number}" for number in LEAD_SAMPLE}
        return calculate_lead_time_for_changes(
            [issue for issue in development if issue["issue_key"] in selected],
            time_period_days=56,
            fixversion_release_map=build_fixversion_release_map(deployments),
        )
    raise ValueError(f"Unknown DORA source: {source}")
