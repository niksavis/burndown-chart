from data.active_work_completed import get_completed_items_by_week
from data.active_work_manager import get_active_work_data
from data.demo.config import AS_OF
from data.persistence import PersistenceBackend, load_app_settings
from data.project_filter import filter_development_issues
from data.sprint_manager import calculate_sprint_progress, get_sprint_dates
from data.sprint_snapshot_calculator import calculate_daily_sprint_snapshots
from data.sprint_tracker_data import load_sprint_tracker_dataset


def active_work(
    backend: PersistenceBackend, profile_id: str, *, completed: bool
) -> dict:
    settings = load_app_settings()
    issues = filter_development_issues(
        backend.get_issues(profile_id, "main"),
        settings["development_projects"],
        settings["devops_projects"],
    )
    general = settings["field_mappings"]["general"]
    workflow = settings["field_mappings"]["workflow"]
    if completed:
        return get_completed_items_by_week(
            issues,
            n_weeks=2,
            flow_end_statuses=workflow["flow_end_statuses"],
            parent_field=general["parent_field"],
        )
    result = get_active_work_data(
        issues,
        backend=backend,
        profile_id=profile_id,
        query_id="main",
        data_points_count=8,
        parent_field=general["parent_field"],
        flow_end_statuses=workflow["flow_end_statuses"],
        flow_wip_statuses=workflow["flow_wip_statuses"],
        parent_issue_types=general["parent_issue_types"],
    )
    return {entry["epic_key"]: entry for entry in result["timeline"]}


def sprint_work(profile_id: str, *, daily: bool) -> dict:
    dataset = load_sprint_tracker_dataset(profile_id, "main", force_refresh=True)
    settings = dataset["settings"]
    if not daily:
        return {
            name: calculate_sprint_progress(
                sprint, settings["flow_end_statuses"], settings["wip_statuses"]
            )
            for name, sprint in dataset["sprint_snapshots"].items()
        }
    result = {}
    for name, sprint in dataset["sprint_snapshots"].items():
        dates = get_sprint_dates(
            name, dataset["tracked_issues"], dataset["sprint_field"]
        )
        if dates is None:
            raise ValueError(f"Synthetic sprint has no metadata: {name}")
        snapshots = calculate_daily_sprint_snapshots(
            sprint,
            dataset["tracked_issues"],
            dataset["status_changelog"],
            dates["start_date"],
            dates["end_date"],
            settings["flow_end_statuses"],
        )
        result[name] = {
            "dates": {row["date"]: row for row in snapshots},
            "future_observations": sum(
                row["date"] > AS_OF.date().isoformat() for row in snapshots
            ),
        }
    return result
