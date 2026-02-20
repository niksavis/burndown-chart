"""Data loading for report generation.

Handles loading and filtering of project data, statistics, and snapshots.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def load_report_data(profile_id: str, weeks: int) -> dict[str, Any]:
    """
    Load all data needed for report generation.

    Loads project scope, statistics, snapshots, settings, and JIRA issues.
    Applies time-based filtering to statistics and snapshots to match the
    requested time period, excluding the current incomplete week.

    Args:
        profile_id: Profile ID to load data for
        weeks: Number of weeks to include in the period

    Returns:
        Dictionary containing:
            - project_scope: Current project scope (remaining items/points)
            - statistics: Filtered statistics for the time period
            - snapshots: Filtered weekly snapshots for the time period
            - settings: App settings (deadline, milestone, bug types)
            - jira_issues: Raw JIRA issues for ad-hoc calculations
            - weeks_count: Actual number of weeks with data
    """
    from data.metrics_snapshots import load_snapshots
    from data.persistence import load_app_settings, load_unified_project_data
    from data.persistence.factory import get_backend
    from data.query_manager import get_active_query_id

    # Load core data
    project_data = load_unified_project_data()
    all_snapshots = load_snapshots()
    settings = load_app_settings()

    # Load JIRA issues from database for the specific profile
    jira_issues = []
    try:
        backend = get_backend()
        query_id = get_active_query_id()
        if query_id and profile_id:
            # Load all issues from database (no filters)
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

    # Calculate time period boundaries using EXACT SAME METHOD as UI dashboard
    # CRITICAL: Use week label matching, not date range filtering
    # This ensures report and UI include exactly the same data points
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

    # Convert to DataFrame for consistent processing (same as UI)
    df_all = pd.DataFrame(all_stats)
    df_all["date"] = pd.to_datetime(df_all["date"], format="mixed", errors="coerce")
    df_all = df_all.dropna(subset=["date"]).sort_values("date", ascending=True)

    # Get reference date (last statistics date, not today)
    reference_date = df_all["date"].max()
    current_week = reference_date.strftime("%G-W%V")

    # Generate week labels to include (SAME AS UI)
    from data.time_period_calculator import format_year_week, get_iso_week

    week_labels_list = []
    current_date = reference_date
    for _i in range(weeks):
        year, week = get_iso_week(current_date)
        week_label = format_year_week(year, week)
        week_labels_list.append(week_label)
        current_date = current_date - timedelta(days=7)

    week_labels = set(reversed(week_labels_list))  # Convert to set for fast lookup

    logger.info(
        f"[REPORT FILTER] Filtering to last {weeks} weeks from {reference_date.strftime('%Y-%m-%d')}: {sorted(week_labels)}"
    )

    # Filter using week labels (SAME AS UI)
    if "week_label" in df_all.columns:
        df_filtered = df_all[df_all["week_label"].isin(week_labels)]
        logger.info(
            f"[REPORT FILTER] Filtered to {len(df_filtered)} rows using week_label matching (requested {weeks} weeks)"
        )
    else:
        # Should not happen - week_label is backfilled by persistence layer
        logger.error(
            "[REPORT FILTER] CRITICAL: week_label column missing from statistics! "
            "Using date range filtering as fallback (less accurate)."
        )
        cutoff_date = reference_date - timedelta(weeks=weeks)
        df_filtered = df_all[df_all["date"] >= cutoff_date]
        logger.warning(
            f"[REPORT FILTER] Fallback date range filtering: {len(df_filtered)} rows"
        )

    # Convert back to list of dicts
    filtered_stats = df_filtered.to_dict("records")

    # Filter snapshots to time period using week labels (exclude current incomplete week)
    filtered_snapshots = {}
    if all_snapshots:
        for week_label_key, snapshot_data in all_snapshots.items():
            # Include if in the requested week labels AND not current week
            if week_label_key in week_labels and week_label_key != current_week:
                filtered_snapshots[week_label_key] = snapshot_data
        logger.info(
            f"[REPORT FILTER] Filtered snapshots: {len(filtered_snapshots)} weeks (excluded current week {current_week})"
        )

    # Use REQUESTED weeks, not snapshot count
    # The velocity calculation groups statistics by ISO week, so it doesn't need to match snapshot count
    # CRITICAL: This must match the user's selected data window in the app (data_points_count)
    weeks_count = weeks

    # Log comprehensive filtering summary
    logger.info(
        f"[REPORT DATA] Loaded data summary:\n"
        f"  - Total statistics: {len(all_stats)}\n"
        f"  - Filtered statistics: {len(filtered_stats)} (requested {weeks_count} weeks)\n"
        f"  - Snapshot weeks: {len(filtered_snapshots)}\n"
        f"  - Reference date: {reference_date.strftime('%Y-%m-%d') if isinstance(reference_date, datetime) else reference_date}\n"
        f"  - Week labels included: {sorted(week_labels)}"
    )

    # Log the actual data for debugging
    if filtered_stats:
        completed_items_sum = sum(s.get("completed_items", 0) for s in filtered_stats)
        completed_points_sum = sum(s.get("completed_points", 0) for s in filtered_stats)
        logger.info(
            f"[REPORT DATA] Filtered data summary: {completed_items_sum} items, {completed_points_sum:.1f} points completed"
        )

    return {
        "project_scope": project_data.get("project_scope", {}),
        "statistics": filtered_stats,
        "all_statistics": all_stats,  # Full history for lifetime metrics
        "snapshots": filtered_snapshots,
        "settings": settings,
        "jira_issues": jira_issues,
        "weeks_count": weeks_count,
        "week_labels": sorted(
            week_labels
        ),  # Pass week labels to ensure consistent filtering
    }
