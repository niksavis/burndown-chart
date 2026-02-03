"""Data persistence adapters - Metrics history and snapshots."""

# Standard library imports
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Third-party library imports

# Application imports
from configuration.settings import logger
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)


def load_metrics_history() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load historical DORA and Flow metrics data from unified project data.

    Returns:
        Dictionary with 'dora_metrics' and 'flow_metrics' keys, each containing
        a list of historical metric snapshots with timestamps.

    Example structure:
        {
            "dora_metrics": [
                {
                    "timestamp": "2025-10-29T10:00:00Z",
                    "time_period_days": 30,
                    "deployment_frequency": {"value": 5.2, "unit": "deployments/month", ...},
                    "lead_time_for_changes": {"value": 2.5, "unit": "days", ...},
                    ...
                }
            ],
            "flow_metrics": [
                {
                    "timestamp": "2025-10-29T10:00:00Z",
                    "time_period_days": 30,
                    "flow_velocity": {"value": 45, "unit": "items/month", ...},
                    ...
                }
            ]
        }
    """
    try:
        unified_data = load_unified_project_data()

        # Return metrics history or empty structure if not found
        return unified_data.get(
            "metrics_history", {"dora_metrics": [], "flow_metrics": []}
        )

    except Exception as e:
        logger.error(f"[Metrics] Error loading metrics history: {e}")
        return {"dora_metrics": [], "flow_metrics": []}


def save_metrics_snapshot(
    metric_type: str, metrics_data: Dict[str, Any], time_period_days: int
) -> bool:
    """
    Save a snapshot of current DORA or Flow metrics to historical data.

    This enables trend analysis by storing metric values over time. Snapshots are
    automatically deduplicated based on timestamp (same day).

    Args:
        metric_type: Either 'dora_metrics' or 'flow_metrics'
        metrics_data: Dictionary containing all calculated metrics for the type
        time_period_days: Time period used for the calculation (e.g., 30, 90)

    Returns:
        True if save successful, False otherwise

    Example:
        >>> dora_data = {
        ...     "deployment_frequency": {"value": 5.2, "unit": "deployments/month"},
        ...     "lead_time_for_changes": {"value": 2.5, "unit": "days"},
        ... }
        >>> save_metrics_snapshot('dora_metrics', dora_data, 30)
        True
    """
    try:
        if metric_type not in ["dora_metrics", "flow_metrics"]:
            logger.error(f"[Metrics] Invalid metric type: {metric_type}")
            return False

        # Load current unified data
        unified_data = load_unified_project_data()

        # Initialize metrics_history if not present
        if "metrics_history" not in unified_data:
            unified_data["metrics_history"] = {
                "dora_metrics": [],
                "flow_metrics": [],
            }

        # Create snapshot with timestamp
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "time_period_days": time_period_days,
            **metrics_data,  # Include all metric calculations
        }

        # Get existing history for this metric type
        history = unified_data["metrics_history"][metric_type]

        # Check if we already have a snapshot from today (deduplicate)
        today_date = datetime.now().date().isoformat()
        existing_today = [
            i
            for i, s in enumerate(history)
            if s.get("timestamp", "")[:10] == today_date
            and s.get("time_period_days") == time_period_days
        ]

        if existing_today:
            # Replace existing snapshot from today with same time period
            history[existing_today[0]] = snapshot
            logger.debug(
                f"[Metrics] Updated {metric_type} snapshot for {time_period_days}d period"
            )
        else:
            # Add new snapshot
            history.append(snapshot)
            logger.debug(
                f"[Metrics] Added {metric_type} snapshot for {time_period_days}d period"
            )

        # Limit history to last 90 days to prevent file bloat
        cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
        history[:] = [s for s in history if s.get("timestamp", "") >= cutoff_date]

        # Sort by timestamp (oldest first)
        history.sort(key=lambda x: x.get("timestamp", ""))

        # Save updated data
        unified_data["metrics_history"][metric_type] = history
        unified_data["metadata"]["last_updated"] = datetime.now().isoformat()
        save_unified_project_data(unified_data)

        logger.info(f"[Metrics] History saved: {len(history)} {metric_type} snapshots")
        return True

    except Exception as e:
        logger.error(f"[Metrics] Error saving snapshot: {e}")
        return False


def get_metric_trend_data(
    metric_type: str, metric_name: str, time_period_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get historical trend data for a specific metric.

    Args:
        metric_type: Either 'dora_metrics' or 'flow_metrics'
        metric_name: Name of the specific metric (e.g., 'deployment_frequency', 'flow_velocity')
        time_period_days: Filter for specific time period (default: 30)

    Returns:
        List of data points with 'date' and 'value' keys for trend visualization

    Example:
        >>> trend = get_metric_trend_data('dora_metrics', 'deployment_frequency', 30)
        >>> print(trend)
        [
            {"date": "2025-10-01", "value": 4.8},
            {"date": "2025-10-08", "value": 5.2},
            {"date": "2025-10-15", "value": 5.5},
        ]
    """
    try:
        history = load_metrics_history()

        if metric_type not in history:
            return []

        metric_history = history[metric_type]

        # Extract trend data for specific metric
        trend_data = []
        for snapshot in metric_history:
            # Filter by time period
            if snapshot.get("time_period_days") != time_period_days:
                continue

            # Extract metric value
            metric_data = snapshot.get(metric_name, {})
            if isinstance(metric_data, dict) and "value" in metric_data:
                trend_data.append(
                    {
                        "date": snapshot.get("timestamp", "")[:10],  # YYYY-MM-DD only
                        "value": metric_data["value"],
                        "unit": metric_data.get("unit", ""),
                    }
                )

        # Sort by date
        trend_data.sort(key=lambda x: x["date"])

        return trend_data

    except Exception as e:
        logger.error(f"[Metrics] Error getting trend data: {e}")
        return []


#######################################################################
# PARAMETER PANEL STATE PERSISTENCE (User Story 1)
#######################################################################
