import argparse
from datetime import timedelta

from data.demo.config import AS_OF, SCENARIOS, SEED_VERSION, START, profile_config
from data.demo.issues import scenario_issues
from data.iso_week_bucketing import get_last_n_weeks
from data.jira.data_transformer import jira_to_csv_format
from data.jira.scope_calculator import calculate_jira_project_scope
from data.metrics.historical_calculator import calculate_metrics_for_last_n_weeks
from data.metrics_snapshots import clear_snapshots_cache
from data.migration.schema_manager import initialize_schema
from data.persistence.factory import get_backend
from utils.offline import install_offline_policy
from utils.runtime import demo_workspace


def _save_budget(profile_id: str, scenario: str) -> None:
    if scenario in {"empty", "missing-signals"}:
        return
    backend = get_backend()
    backend.save_budget_settings(
        profile_id,
        "main",
        {
            "time_allocated_weeks": 10,
            "budget_total_eur": 9000,
            "team_cost_per_week_eur": 1100,
            "currency_symbol": "EUR",
            "cost_rate_type": "weekly",
            "baseline_velocity_items": 4,
            "baseline_velocity_points": 10,
            "created_at": START.isoformat(),
            "updated_at": AS_OF.isoformat(),
        },
    )
    revisions = []
    for week, cost, budget in [(3, 200, 1500), (5, -100, -500)]:
        date = START + timedelta(weeks=week)
        revisions.append(
            {
                "revision_date": date.date().isoformat(),
                "week_label": date.strftime("%G-W%V"),
                "time_allocated_weeks_delta": 1,
                "team_cost_delta": cost,
                "budget_total_delta": budget,
                "revision_reason": "Synthetic team change",
                "created_at": date.isoformat(),
            }
        )
    backend.save_budget_revisions(profile_id, "main", revisions)


def _save_delivery_data(issues: list[dict], profile_id: str, scenario: str) -> None:
    backend = get_backend()
    backend.save_jira_cache(
        profile_id,
        "main",
        "synthetic-demo",
        {"issues": issues},
        AS_OF + timedelta(days=3650),
    )
    development = [
        issue
        for issue in issues
        if issue["fields"]["project"]["key"] == "DEMO"
        and issue["fields"]["issuetype"]["name"] != "Epic"
    ]
    points = "" if scenario in {"no-points", "unmapped-fields"} else "customfield_10001"
    scope = calculate_jira_project_scope(development, points)
    backend.save_scope(profile_id, "main", scope)
    statistics = jira_to_csv_format(development, {"story_points_field": points})
    if scenario in {"singleton", "fractional-points"}:
        statistics = statistics[:1]
    if scenario == "sparse":
        statistics = [row for index, row in enumerate(statistics) if index in {0, 3, 7}]
    backend.save_statistics_batch(profile_id, "main", statistics)
    weeks = get_last_n_weeks(8, AS_OF)
    if scenario in {"singleton", "fractional-points"}:
        weeks = weeks[:1]
    elif scenario == "sparse":
        weeks = [weeks[index] for index in (0, 3, 7)]
    if scenario != "unmapped-fields":
        success, message = calculate_metrics_for_last_n_weeks(custom_weeks=weeks)
        if not success:
            raise RuntimeError(
                f"Synthetic metric calculation failed for {scenario}: {message}"
            )


def seed_scenario(scenario: str) -> None:
    backend = get_backend()
    profile = profile_config(scenario)
    profile_id = profile["id"]
    backend.save_profile(profile)
    backend.save_query(
        profile_id,
        {
            "id": "main",
            "name": scenario,
            "jql": "project in (DEMO, OPS)",
            "created_at": START.isoformat(),
            "last_used": AS_OF.isoformat(),
        },
    )
    backend.set_app_state("active_profile_id", profile_id)
    backend.set_app_state("active_query_id", "main")
    clear_snapshots_cache()
    issues = scenario_issues(scenario)
    if issues:
        _save_delivery_data(issues, profile_id, scenario)
    _save_budget(profile_id, scenario)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--empty", action="store_true")
    arguments = parser.parse_args()
    install_offline_policy()
    workspace = demo_workspace()
    if workspace is None:
        raise ValueError("Seed requires the isolated demo launcher")
    initialize_schema(workspace / "burndown.db")
    if not arguments.empty:
        for scenario in SCENARIOS:
            seed_scenario(scenario)
        get_backend().set_app_state("active_profile_id", "demo-complete")
        get_backend().set_app_state("active_query_id", "main")
    get_backend().set_app_state("demo_seed_version", SEED_VERSION)
    summary = "empty workspace" if arguments.empty else f"{len(SCENARIOS)} scenarios"
    print(f"Synthetic seed complete: {summary}")


if __name__ == "__main__":
    main()
