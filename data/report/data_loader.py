import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from data.metrics_snapshots import load_snapshots
from data.persistence import load_app_settings, load_unified_project_data
from data.persistence.factory import get_backend
from data.query_manager import get_active_query_id
from data.time_period_calculator import format_year_week, get_iso_week

logger = logging.getLogger(__name__)


def load_report_data(profile_id: str, weeks: int) -> dict[str, Any]:

    project_data = load_unified_project_data()
    all_snapshots = load_snapshots()
    settings = load_app_settings()

    jira_issues = []
    try:
        backend = get_backend()
        query_id = get_active_query_id()
        if query_id and profile_id:
            jira_issues = backend.get_issues(profile_id, query_id)
            logger.info(
                f"[REPORT JIRA] Loaded {len(jira_issues)} JIRA issues from database "
                f"(profile={profile_id}, query={query_id})"
            )
        else:
            logger.warning(
                f"[REPORT JIRA] Missing profile_id={profile_id} or query_id={query_id}"
            )
    except Exception as e:
        logger.warning(
            f"[REPORT JIRA] Could not load JIRA issues from database: {e}",
            exc_info=True,
        )

    all_stats = project_data.get("statistics", [])

    if not all_stats:
        logger.warning("No statistics data available")
        return {
            "project_scope": project_data.get("project_scope", {}),
            "statistics": [],
            "all_statistics": [],
            "snapshots": {},
            "settings": settings,
            "jira_issues": [],
            "weeks_count": 0,
        }

    df_all = pd.DataFrame(all_stats)
    df_all["date"] = pd.to_datetime(df_all["date"], format="mixed", errors="coerce")
    df_all = df_all.dropna(subset=["date"]).sort_values("date", ascending=True)

    reference_date = df_all["date"].max()
    current_week = reference_date.strftime("%G-W%V")

    week_labels_list = []
    current_date = reference_date
    for _i in range(weeks):
        year, week = get_iso_week(current_date)
        week_label = format_year_week(year, week)
        week_labels_list.append(week_label)
        current_date = current_date - timedelta(days=7)

    week_labels = set(reversed(week_labels_list))

    logger.info(
        f"[REPORT FILTER] Filtering to last {weeks} weeks from "
        f"{reference_date.strftime('%Y-%m-%d')}: {sorted(week_labels)}"
    )

    if "week_label" in df_all.columns:
        df_filtered = df_all[df_all["week_label"].isin(week_labels)]
        logger.info(
            f"[REPORT FILTER] Filtered to {len(df_filtered)} rows using "
            f"week_label matching (requested {weeks} weeks)"
        )
    else:
        logger.error(
            "[REPORT FILTER] CRITICAL: week_label column missing from statistics! "
            "Using date range filtering as fallback (less accurate)."
        )
        cutoff_date = reference_date - timedelta(weeks=weeks)
        df_filtered = df_all[df_all["date"] >= cutoff_date]
        logger.warning(
            f"[REPORT FILTER] Fallback date range filtering: {len(df_filtered)} rows"
        )

    filtered_stats = df_filtered.to_dict("records")

    filtered_snapshots = {}
    if all_snapshots:
        for week_label_key, snapshot_data in all_snapshots.items():
            if week_label_key in week_labels and week_label_key != current_week:
                filtered_snapshots[week_label_key] = snapshot_data
        logger.info(
            f"[REPORT FILTER] Filtered snapshots: {len(filtered_snapshots)} "
            f"weeks (excluded current week {current_week})"
        )

    weeks_count = weeks
    reference_date_display = (
        reference_date.strftime("%Y-%m-%d")
        if isinstance(reference_date, datetime)
        else str(reference_date)
    )

    logger.info(
        f"[REPORT DATA] Loaded data summary:\n"
        f"  - Total statistics: {len(all_stats)}\n"
        f"  - Filtered statistics: {len(filtered_stats)} "
        f"(requested {weeks_count} weeks)\n"
        f"  - Snapshot weeks: {len(filtered_snapshots)}\n"
        "  - Reference date: "
        f"{reference_date_display}"
        "\n"
        f"  - Week labels included: {sorted(week_labels)}"
    )

    if filtered_stats:
        completed_items_sum = sum(s.get("completed_items", 0) for s in filtered_stats)
        completed_points_sum = sum(s.get("completed_points", 0) for s in filtered_stats)
        logger.info(
            f"[REPORT DATA] Filtered data summary: {completed_items_sum} items, "
            f"{completed_points_sum:.1f} points completed"
        )

    return {
        "project_scope": project_data.get("project_scope", {}),
        "statistics": filtered_stats,
        "all_statistics": all_stats,
        "snapshots": filtered_snapshots,
        "settings": settings,
        "jira_issues": jira_issues,
        "weeks_count": weeks_count,
        "week_labels": sorted(week_labels),
    }
