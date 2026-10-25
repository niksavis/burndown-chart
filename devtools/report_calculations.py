from data.report.data_loader import load_report_data
from data.report.generator_metrics import calculate_all_metrics


def report_calculations(profile_id: str) -> dict:
    data = load_report_data(profile_id, 8)
    data["profile_id"] = profile_id
    result = calculate_all_metrics(data, ["burndown", "flow", "dora", "budget"], 8)
    result["window"] = {
        "snapshot_weeks": sorted(data["snapshots"]),
        "recorded_weeks": [row["week_label"] for row in data["statistics"]],
    }
    return result
