"""
Metrics Snapshot Storage

Stores historical weekly snapshots of metrics that can't be reconstructed from JIRA data alone.
Primarily used for Flow Load (WIP) which is a point-in-time measurement.

Storage Format: JSON file with weekly snapshots
{
    "2025-44": {
        "flow_load": {
            "wip_count": 12,
            "by_status": {"In Progress": 10, "In Review": 2},
            "by_issue_type": {"Bug": 5, "Task": 6, "Story": 1},
            "timestamp": "2025-10-31T17:00:00Z"
        },
        "custom_metric": {
            "value": 42,
            "timestamp": "2025-10-31T17:00:00Z"
        }
    }
}

Created: October 31, 2025
"""

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Storage file path
SNAPSHOTS_FILE = "metrics_snapshots.json"

# Thread lock for file access
_snapshots_lock = threading.Lock()


def load_snapshots() -> Dict[str, Dict[str, Any]]:
    """
    Load all metric snapshots from storage.

    Returns:
        Dictionary mapping week labels to metric snapshots
        Example: {"2025-44": {"flow_load": {...}, "custom_metric": {...}}}
    """
    snapshot_path = Path(SNAPSHOTS_FILE)

    if not snapshot_path.exists():
        logger.info(f"No snapshot file found at {SNAPSHOTS_FILE}, starting fresh")
        return {}

    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshots = json.load(f)
        logger.info(
            f"Loaded {len(snapshots)} weeks of metric snapshots from {SNAPSHOTS_FILE}"
        )
        return snapshots
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse {SNAPSHOTS_FILE}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Failed to load snapshots from {SNAPSHOTS_FILE}: {e}")
        return {}


def save_snapshots(snapshots: Dict[str, Dict[str, Any]]) -> bool:
    """
    Save all metric snapshots to storage using atomic write.

    Uses temporary file + rename to prevent corruption from partial writes.

    Args:
        snapshots: Dictionary mapping week labels to metric snapshots

    Returns:
        True if successful, False otherwise
    """
    import tempfile
    import os

    snapshot_path = Path(SNAPSHOTS_FILE)

    try:
        # Write to temporary file first (atomic operation)
        temp_fd, temp_path = tempfile.mkstemp(
            suffix=".json",
            prefix="metrics_snapshots_",
            dir=snapshot_path.parent,
            text=True,
        )

        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(snapshots, f, indent=2, ensure_ascii=False)

            # Atomic rename (replaces existing file)
            # On Windows, need to remove target first
            if snapshot_path.exists():
                snapshot_path.unlink()
            os.rename(temp_path, snapshot_path)

            logger.info(
                f"Saved {len(snapshots)} weeks of metric snapshots to {SNAPSHOTS_FILE}"
            )
            return True
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    except Exception as e:
        logger.error(f"Failed to save snapshots to {SNAPSHOTS_FILE}: {e}")
        return False


def save_metric_snapshot(
    week_label: str, metric_name: str, metric_data: Dict[str, Any]
) -> bool:
    """
    Save a snapshot of a specific metric for a specific week.

    Thread-safe operation using file lock.

    Args:
        week_label: ISO week label (e.g., "2025-44")
        metric_name: Name of the metric (e.g., "flow_load", "deployment_frequency")
        metric_data: Metric data to store (should NOT include timestamp - added automatically)

    Returns:
        True if successful, False otherwise

    Example:
        >>> save_metric_snapshot("2025-44", "flow_load", {
        ...     "wip_count": 12,
        ...     "by_status": {"In Progress": 10, "In Review": 2}
        ... })
    """
    with _snapshots_lock:  # Prevent concurrent access
        snapshots = load_snapshots()

        # Initialize week if not exists
        if week_label not in snapshots:
            snapshots[week_label] = {}

        # Add timestamp to metric data
        metric_data_with_timestamp = {
            **metric_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Store metric snapshot
        snapshots[week_label][metric_name] = metric_data_with_timestamp

        logger.info(f"Saving snapshot for {metric_name} in week {week_label}")
        return save_snapshots(snapshots)


def get_metric_snapshot(week_label: str, metric_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific metric snapshot for a specific week.

    Args:
        week_label: ISO week label (e.g., "2025-44")
        metric_name: Name of the metric (e.g., "flow_load")

    Returns:
        Metric data dict if found, None otherwise
    """
    snapshots = load_snapshots()
    return snapshots.get(week_label, {}).get(metric_name)


def get_metric_weekly_values(
    week_labels: List[str], metric_name: str, value_key: str
) -> List[float]:
    """
    Extract weekly values for a specific metric across multiple weeks.

    Args:
        week_labels: List of ISO week labels (e.g., ["2025-43", "2025-44"])
        metric_name: Name of the metric (e.g., "flow_load")
        value_key: Key to extract from metric data (e.g., "wip_count")

    Returns:
        List of values, 0 for weeks with no data

    Example:
        >>> get_metric_weekly_values(["2025-43", "2025-44"], "flow_load", "wip_count")
        [15, 12]  # WIP was 15 in week 43, 12 in week 44
    """
    snapshots = load_snapshots()
    values = []

    for week_label in week_labels:
        metric_data = snapshots.get(week_label, {}).get(metric_name)
        if metric_data and value_key in metric_data:
            values.append(metric_data[value_key])
        else:
            values.append(0)  # No data for this week

    return values


def cleanup_old_snapshots(weeks_to_keep: int = 52) -> int:
    """
    Remove snapshots older than specified number of weeks.

    Args:
        weeks_to_keep: Number of recent weeks to retain (default: 52 = 1 year)

    Returns:
        Number of weeks removed
    """
    snapshots = load_snapshots()

    # Calculate cutoff week (simplified - just compare as strings for now)
    # More sophisticated logic could parse year-week format
    weeks = sorted(snapshots.keys(), reverse=True)
    if len(weeks) <= weeks_to_keep:
        logger.info(f"No cleanup needed: {len(weeks)} weeks <= {weeks_to_keep} limit")
        return 0

    # Remove oldest weeks beyond retention period
    weeks_to_remove = weeks[weeks_to_keep:]
    removed_count = 0

    for week in weeks_to_remove:
        del snapshots[week]
        removed_count += 1

    if removed_count > 0:
        save_snapshots(snapshots)
        logger.info(
            f"Cleaned up {removed_count} old snapshot weeks (keeping {weeks_to_keep})"
        )

    return removed_count


def get_snapshot_stats() -> Dict[str, Any]:
    """
    Get statistics about stored snapshots.

    Returns:
        Dictionary with snapshot statistics:
        {
            "total_weeks": 16,
            "metrics": ["flow_load", "custom_metric"],
            "oldest_week": "2025-29",
            "newest_week": "2025-44",
            "file_size_kb": 12.5
        }
    """
    snapshots = load_snapshots()
    snapshot_path = Path(SNAPSHOTS_FILE)

    # Collect all unique metric names
    all_metrics = set()
    for week_data in snapshots.values():
        all_metrics.update(week_data.keys())

    stats = {
        "total_weeks": len(snapshots),
        "metrics": sorted(list(all_metrics)),
        "oldest_week": min(snapshots.keys()) if snapshots else None,
        "newest_week": max(snapshots.keys()) if snapshots else None,
        "file_size_kb": (
            round(snapshot_path.stat().st_size / 1024, 2)
            if snapshot_path.exists()
            else 0
        ),
    }

    return stats


def get_weekly_metrics(week_label: str) -> Dict[str, Any]:
    """
    Get all metrics for a specific week.

    Args:
        week_label: ISO week label (e.g., "2025-44")

    Returns:
        Dictionary containing all metrics for the week:
        {
            "flow_time": {...},
            "flow_efficiency": {...},
            "dora_deployment_frequency": {...},
            "dora_lead_time": {...},
            "trends": {...}
        }
        Returns empty dict if week has no data.

    Example:
        >>> metrics = get_weekly_metrics("2025-44")
        >>> if metrics.get("flow_time"):
        ...     print(f"Avg flow time: {metrics['flow_time']['avg_days']} days")
    """
    snapshots = load_snapshots()
    return snapshots.get(week_label, {})


def save_flow_time_snapshot(week_label: str, data: Dict[str, Any]) -> bool:
    """
    Save Flow Time metric snapshot.

    Args:
        week_label: ISO week label (e.g., "2025-44")
        data: Flow Time data containing avg_days, median_days, p85_days, completed_count

    Returns:
        True if successful, False otherwise
    """
    return save_metric_snapshot(week_label, "flow_time", data)


def save_flow_efficiency_snapshot(week_label: str, data: Dict[str, Any]) -> bool:
    """
    Save Flow Efficiency metric snapshot.

    Args:
        week_label: ISO week label (e.g., "2025-44")
        data: Flow Efficiency data containing overall_pct, avg_active_days, avg_waiting_days

    Returns:
        True if successful, False otherwise
    """
    return save_metric_snapshot(week_label, "flow_efficiency", data)


def save_dora_metrics_snapshot(
    week_label: str, deployment_data: Dict[str, Any], lead_time_data: Dict[str, Any]
) -> bool:
    """
    Save DORA metrics snapshots (both deployment frequency and lead time).

    Args:
        week_label: ISO week label (e.g., "2025-44")
        deployment_data: Deployment frequency data
        lead_time_data: Lead time for changes data

    Returns:
        True if both saved successfully, False otherwise
    """
    deployment_success = save_metric_snapshot(
        week_label, "dora_deployment_frequency", deployment_data
    )
    lead_time_success = save_metric_snapshot(
        week_label, "dora_lead_time", lead_time_data
    )

    return deployment_success and lead_time_success


def has_metric_snapshot(week_label: str, metric_name: str) -> bool:
    """
    Check if a metric snapshot exists for a specific week.

    Args:
        week_label: ISO week label (e.g., "2025-44")
        metric_name: Name of the metric (e.g., "flow_time")

    Returns:
        True if snapshot exists, False otherwise

    Example:
        >>> if not has_metric_snapshot("2025-44", "flow_time"):
        ...     print("No Flow Time data for this week. Click 'Refresh Metrics' to calculate.")
    """
    return get_metric_snapshot(week_label, metric_name) is not None


def get_available_weeks() -> List[str]:
    """
    Get list of all weeks that have snapshots.

    Returns:
        List of ISO week labels, sorted newest first

    Example:
        >>> weeks = get_available_weeks()
        >>> print(f"Metrics available for {len(weeks)} weeks: {weeks[0]} to {weeks[-1]}")
    """
    snapshots = load_snapshots()
    return sorted(snapshots.keys(), reverse=True)
