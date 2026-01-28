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

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Thread lock for file access
_snapshots_lock = threading.Lock()

# Cache for loaded snapshots to avoid repeated database queries
_snapshots_cache: Optional[Dict[str, Dict[str, Any]]] = None
_cache_query_id: Optional[str] = None  # Track which query the cache is for

# Batch mode context - prevents writes until flush
_batch_mode_active = False
_batch_snapshots = None


def _get_snapshots_file_path() -> Path:
    """Get the path to metrics_snapshots.json in the active query workspace."""
    from data.profile_manager import get_data_file_path

    return get_data_file_path("metrics_snapshots.json")


def load_snapshots() -> Dict[str, Dict[str, Any]]:
    """
    Load all metric snapshots from database via repository pattern.

    Uses a module-level cache to avoid repeated database queries.
    Cache is cleared when query changes.

    Returns:
        Dictionary mapping week labels to metric snapshots
        Example: {"2025-W44": {"flow_load": {...}, "custom_metric": {...}}}
    """
    global _snapshots_cache, _cache_query_id

    try:
        from data.persistence.factory import get_backend
        from data.iso_week_bucketing import get_week_label
        from datetime import datetime

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.info("No active profile/query, returning empty snapshots")
            return {}

        # Check cache: return if query hasn't changed
        if _snapshots_cache is not None and _cache_query_id == active_query_id:
            return _snapshots_cache

        # Load from database - get_metrics_snapshots returns list of dicts
        # Each dict is a ROW with: snapshot_date, metric_category, metric_name, metric_value, etc.
        # Need to reconstruct the nested structure: {week_label: {metric_name: {...}}}
        snapshots = {}
        for metric_type in ["dora", "flow", "custom"]:
            snapshot_list = backend.get_metrics_snapshots(
                active_profile_id,
                active_query_id,
                metric_type,
                limit=10000,  # Increased limit for large projects
            )

            # Group by ISO week label and metric_name
            for row in snapshot_list:
                # Convert snapshot_date (YYYY-MM-DD) to ISO week label (YYYY-Wxx)
                snapshot_date_str = row["snapshot_date"]
                snapshot_date = datetime.fromisoformat(snapshot_date_str).date()
                week_label = get_week_label(
                    datetime.combine(snapshot_date, datetime.min.time())
                )

                if week_label not in snapshots:
                    snapshots[week_label] = {}

                metric_name = row["metric_name"]

                # Reconstruct metric data structure
                # Start with empty dict to allow calculation_metadata to be merged
                metric_data = {}

                # Add calculation metadata first if available (merge into top level)
                if row.get("calculation_metadata"):
                    # Merge all fields from calculation_metadata into metric_data
                    metric_data.update(row["calculation_metadata"])

                # Parse metric_value if it's a dict (saved as JSON in database)
                metric_value = row.get("metric_value")
                if isinstance(metric_value, dict):
                    # metric_value is a dict (parsed JSON) - merge all fields
                    metric_data.update(metric_value)
                else:
                    # Simple scalar value
                    metric_data["value"] = metric_value
                    metric_data["unit"] = row.get("metric_unit", "")

                # Standard fields from row (these override if present)
                metric_data["excluded_issue_count"] = row.get("excluded_issue_count", 0)

                # Add forecast data if available
                if row.get("forecast_value") is not None:
                    metric_data["forecast_value"] = row["forecast_value"]
                    metric_data["forecast_confidence_low"] = row.get(
                        "forecast_confidence_low"
                    )
                    metric_data["forecast_confidence_high"] = row.get(
                        "forecast_confidence_high"
                    )

                snapshots[week_label][metric_name] = metric_data

        logger.info(f"Loaded {len(snapshots)} weeks of metric snapshots from database")

        # Update cache
        _snapshots_cache = snapshots
        _cache_query_id = active_query_id

        return snapshots
    except Exception as e:
        logger.error(f"Failed to load snapshots from database: {e}", exc_info=True)
        return {}


def clear_snapshots_cache() -> None:
    """Clear the snapshots cache. Call this after Force Refresh or when data changes."""
    global _snapshots_cache, _cache_query_id
    _snapshots_cache = None
    _cache_query_id = None
    logger.info("Cleared snapshots cache")


def save_snapshots(snapshots: Dict[str, Dict[str, Any]]) -> bool:
    """
    Save all metric snapshots to database via repository pattern.

    Args:
        snapshots: Dictionary mapping week labels to metric snapshots

    Returns:
        True if successful, False otherwise
    """
    try:
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.error("No active profile/query to save snapshots to")
            return False

        # Save each week's snapshots
        for week, metrics in snapshots.items():
            # Determine metric type based on metric names (simple heuristic)
            # For now, save as "metrics" category - can be refined later
            metric_type = (
                "dora" if any(k.startswith("dora_") for k in metrics.keys()) else "flow"
            )
            backend.save_metrics_snapshot(
                active_profile_id,
                active_query_id,
                week,
                metric_type,
                metrics,
            )

        logger.info(f"Saved {len(snapshots)} weeks of metric snapshots to database")

        # Clear cache after saving so next load gets fresh data
        clear_snapshots_cache()

        return True
    except Exception as e:
        logger.error(f"Failed to save snapshots to database: {e}")
        return False


def save_metric_snapshot(
    week_label: str, metric_name: str, metric_data: Dict[str, Any]
) -> bool:
    """
    Save a snapshot of a specific metric for a specific week.

    Thread-safe operation using file lock.

    In batch mode, accumulates changes in memory without writing to disk.
    Use batch_write_mode() context manager to batch multiple saves into one write.

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
    global _batch_mode_active, _batch_snapshots

    with _snapshots_lock:  # Prevent concurrent access
        # In batch mode, use in-memory snapshot cache
        if _batch_mode_active:
            if _batch_snapshots is None:
                raise RuntimeError("Batch mode active but _batch_snapshots is None")

            # Initialize week if not exists
            if week_label not in _batch_snapshots:
                _batch_snapshots[week_label] = {}

            # Add timestamp to metric data
            metric_data_with_timestamp = {
                **metric_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Store metric snapshot in memory
            _batch_snapshots[week_label][metric_name] = metric_data_with_timestamp
            logger.debug(
                f"[Batch] Queued snapshot for {metric_name} in week {week_label}"
            )
            return True

        # Normal mode: load, modify, save immediately
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


class batch_write_mode:
    """
    Context manager for batch writing multiple metrics snapshots.

    Accumulates all save_metric_snapshot() calls in memory and writes once on exit.
    Dramatically improves performance when saving many metrics (e.g., 52 weeks × 8 metrics).

    Example:
        >>> with batch_write_mode():
        ...     for week in weeks:
        ...         save_metric_snapshot(week, "flow_velocity", data)
        ...         save_metric_snapshot(week, "flow_load", data)
        ...     # Writes once here on exit
    """

    def __enter__(self):
        global _batch_mode_active, _batch_snapshots

        with _snapshots_lock:
            if _batch_mode_active:
                raise RuntimeError("Cannot nest batch_write_mode contexts")

            _batch_mode_active = True
            # Load existing snapshots into memory
            _batch_snapshots = load_snapshots()
            logger.info(
                "[Batch] Started batch write mode - accumulating changes in memory"
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _batch_mode_active, _batch_snapshots

        with _snapshots_lock:
            if not _batch_mode_active:
                return False

            try:
                if exc_type is None and _batch_snapshots is not None:
                    # No exception - flush to disk
                    num_weeks = len(_batch_snapshots)
                    logger.info(f"[Batch] Flushing {num_weeks} weeks to disk...")
                    save_snapshots(_batch_snapshots)
                    logger.info(
                        f"[Batch] Batch write complete: {num_weeks} weeks saved in single write"
                    )
                else:
                    # Exception occurred - discard changes
                    logger.warning(
                        f"[Batch] Exception occurred, discarding batched changes: {exc_val}"
                    )
            finally:
                # Always reset batch mode
                _batch_mode_active = False
                _batch_snapshots = None

        return False  # Don't suppress exceptions


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


def get_last_n_weeks_values(
    metric_key: str,
    value_key: str,
    n_weeks: int = 4,
    current_week: Optional[str] = None,
) -> List[float]:
    """
    Get last N weeks of values for a specific metric (for forecast calculation).

    Retrieves historical values in chronological order (oldest to newest) for use
    with calculate_forecast() function.

    Args:
        metric_key: Metric name (e.g., "flow_velocity", "flow_load", "dora_lead_time")
        value_key: Key to extract from metric data (e.g., "completed_count", "wip_count", "median_hours")
        n_weeks: Number of weeks to retrieve (default: 4)
        current_week: Optional current week to exclude (if calculating forecast for current week)

    Returns:
        List of values in chronological order (oldest to newest), excluding weeks with no data
        Empty list if insufficient historical data

    Example:
        >>> # Get last 4 weeks of Flow Velocity for forecast
        >>> values = get_last_n_weeks_values("flow_velocity", "completed_count", n_weeks=4)
        >>> [10, 12, 15, 18]  # Oldest to newest

        >>> # Get last 4 weeks of Flow Load (excluding current week)
        >>> values = get_last_n_weeks_values("flow_load", "wip_count", n_weeks=4, current_week="2025-44")
        >>> [12, 15, 14, 13]  # W-4, W-3, W-2, W-1 (excludes W-0)
    """
    snapshots = load_snapshots()

    # Get all available weeks, sorted newest first
    all_weeks = sorted(snapshots.keys(), reverse=True)

    values = []

    # Iterate through weeks from newest to oldest
    for week_label in all_weeks:
        # Skip current week if specified
        if current_week and week_label == current_week:
            continue

        # Get metric snapshot for this week
        metric_snapshot = snapshots.get(week_label, {}).get(metric_key)

        if metric_snapshot and value_key in metric_snapshot:
            value = metric_snapshot[value_key]
            # Only include valid numeric values
            if isinstance(value, (int, float)) and value >= 0:
                values.append(float(value))

        # Stop if we have enough values
        if len(values) >= n_weeks:
            break

    # Reverse to get chronological order (oldest to newest)
    return list(reversed(values))


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
    snapshot_path = _get_snapshots_file_path()

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


# ============================================================================
# FORECAST ENHANCEMENT FUNCTIONS (Feature 009)
# ============================================================================


def save_metric_snapshot_with_forecast(
    week_label: str,
    metric_name: str,
    metric_data: Dict[str, Any],
    metric_type: Optional[str] = None,
) -> bool:
    """
    Save metric snapshot WITH forecast calculation (Feature 009).

    This is an enhanced version of save_metric_snapshot() that automatically:
    1. Saves the current metric data
    2. Retrieves last N weeks of historical data
    3. Calculates forecast using calculate_forecast()
    4. Calculates trend vs forecast using calculate_trend_vs_forecast()
    5. Stores forecast data in the snapshot

    Args:
        week_label: ISO week label (e.g., "2025-44")
        metric_name: Name of the metric (e.g., "flow_velocity", "dora_lead_time")
        metric_data: Current metric data to store
        metric_type: Optional "higher_better" or "lower_better" for trend calculation

    Returns:
        True if successful, False otherwise

    Example:
        >>> save_metric_snapshot_with_forecast(
        ...     "2025-44",
        ...     "flow_velocity",
        ...     {"completed_count": 15, "distribution": {...}},
        ...     metric_type="higher_better"
        ... )
    """
    from data.metrics_calculator import (
        calculate_forecast,
        calculate_trend_vs_forecast,
        calculate_flow_load_range,
    )
    from configuration.metrics_config import (
        HIGHER_BETTER_METRICS,
        LOWER_BETTER_METRICS,
        FLOW_LOAD_RANGE_PERCENT,
    )

    # First, save the base metric data (without forecast)
    success = save_metric_snapshot(week_label, metric_name, metric_data)
    if not success:
        return False

    # Determine value key based on metric name
    value_key_map = {
        "flow_velocity": "completed_count",
        "flow_load": "wip_count",
        "flow_time": "median_days",
        "flow_efficiency": "overall_pct",
        "dora_deployment_frequency": "deployment_count",
        "dora_lead_time": "median_hours",
        "dora_change_failure_rate": "change_failure_rate_percent",
        "dora_mttr": "median_hours",
    }

    value_key = value_key_map.get(metric_name)
    if not value_key:
        logger.warning(
            f"No value key mapping for metric {metric_name}, skipping forecast"
        )
        return True  # Metric saved, just no forecast

    # Get last 4 weeks of historical values (excluding current week for historical weeks)
    historical_values = get_last_n_weeks_values(
        metric_key=metric_name,
        value_key=value_key,
        n_weeks=4,
        current_week=week_label,  # Exclude current week from history
    )

    # Calculate forecast if we have enough historical data
    forecast_data = calculate_forecast(historical_values) if historical_values else None

    if forecast_data:
        # Determine metric type if not provided
        if not metric_type:
            if metric_name in HIGHER_BETTER_METRICS:
                metric_type = "higher_better"
            elif metric_name in LOWER_BETTER_METRICS:
                metric_type = "lower_better"

        # Get current value from metric_data
        current_value = metric_data.get(value_key, 0)

        # Calculate trend vs forecast (if we know the metric type)
        trend_data = None
        if metric_type and current_value is not None:
            try:
                trend_data = calculate_trend_vs_forecast(
                    current_value=float(current_value),
                    forecast_value=forecast_data["forecast_value"],
                    metric_type=metric_type,
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate trend for {metric_name}: {e}")

        # Special handling for Flow Load range
        if metric_name == "flow_load" and forecast_data:
            try:
                range_data = calculate_flow_load_range(
                    forecast_value=forecast_data["forecast_value"],
                    range_percent=FLOW_LOAD_RANGE_PERCENT,
                )
                forecast_data["forecast_range"] = range_data
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate Flow Load range: {e}")

        # Update the snapshot with forecast data
        snapshots = load_snapshots()
        if week_label in snapshots and metric_name in snapshots[week_label]:
            snapshots[week_label][metric_name]["forecast"] = forecast_data
            if trend_data:
                snapshots[week_label][metric_name]["trend_vs_forecast"] = trend_data

            save_snapshots(snapshots)
            logger.info(
                f"Added forecast data to {metric_name} snapshot for week {week_label}"
            )

    return True


def add_forecasts_to_week(week_label: str) -> bool:
    """
    Add forecast data to all metrics for a specific week (Feature 009).

    Call this AFTER all metrics have been saved for a week to calculate
    and add forecast data based on historical weeks.

    Args:
        week_label: ISO week label (e.g., "2025-44")

    Returns:
        True if successful, False otherwise

    Example:
        >>> # After calculating all metrics for week 2025-44
        >>> add_forecasts_to_week("2025-44")
        True
    """
    from data.metrics_calculator import (
        calculate_forecast,
        calculate_trend_vs_forecast,
        calculate_flow_load_range,
    )
    from configuration.metrics_config import FLOW_LOAD_RANGE_PERCENT

    logger.info(f"Adding forecast data to all metrics for week {week_label}")

    # Metric name → value key mapping
    metric_configs = {
        "flow_velocity": {
            "value_key": "completed_count",
            "metric_type": "higher_better",
        },
        "flow_load": {"value_key": "wip_count", "metric_type": None},  # Bidirectional
        "flow_time": {"value_key": "median_days", "metric_type": "lower_better"},
        "flow_efficiency": {"value_key": "overall_pct", "metric_type": "higher_better"},
        "dora_deployment_frequency": {
            "value_key": "deployment_count",
            "metric_type": "higher_better",
        },
        "dora_lead_time": {"value_key": "median_hours", "metric_type": "lower_better"},
        "dora_change_failure_rate": {
            "value_key": "change_failure_rate_percent",
            "metric_type": "lower_better",
        },
        "dora_mttr": {"value_key": "median_hours", "metric_type": "lower_better"},
    }

    snapshots = load_snapshots()
    modified = False

    for metric_name, config in metric_configs.items():
        value_key = config["value_key"]
        metric_type = config["metric_type"]

        # Get historical values (excluding current week)
        historical_values = get_last_n_weeks_values(
            metric_key=metric_name,
            value_key=value_key,
            n_weeks=4,
            current_week=week_label,
        )

        # Calculate forecast
        forecast_data = (
            calculate_forecast(historical_values) if historical_values else None
        )

        if not forecast_data:
            logger.debug(f"No forecast for {metric_name} (insufficient history)")
            continue

        # Get current value from snapshot
        metric_snapshot = snapshots.get(week_label, {}).get(metric_name)
        if not metric_snapshot:
            logger.debug(f"No snapshot found for {metric_name} in week {week_label}")
            continue

        current_value = metric_snapshot.get(value_key)

        # Calculate trend vs forecast
        trend_data = None
        if metric_type and current_value is not None:
            try:
                trend_data = calculate_trend_vs_forecast(
                    current_value=float(current_value),
                    forecast_value=forecast_data["forecast_value"],
                    metric_type=metric_type,
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate trend for {metric_name}: {e}")

        # Special handling for Flow Load range
        if metric_name == "flow_load":
            try:
                range_data = calculate_flow_load_range(
                    forecast_value=forecast_data["forecast_value"],
                    range_percent=FLOW_LOAD_RANGE_PERCENT,
                )
                forecast_data["forecast_range"] = range_data
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate Flow Load range: {e}")

        # Update snapshot
        snapshots[week_label][metric_name]["forecast"] = forecast_data
        if trend_data:
            snapshots[week_label][metric_name]["trend_vs_forecast"] = trend_data

        modified = True
        logger.info(f"Added forecast to {metric_name} for week {week_label}")

    if modified:
        save_snapshots(snapshots)
        logger.info(f"Saved forecast data for week {week_label}")
        return True

    return False
