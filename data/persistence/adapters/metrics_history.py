import logging
from datetime import datetime, timedelta
from typing import Any

from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)

logger = logging.getLogger(__name__)


def load_metrics_history() -> dict[str, list[dict[str, Any]]]:

    try:
        unified_data = load_unified_project_data()

        return unified_data.get(
            "metrics_history", {"dora_metrics": [], "flow_metrics": []}
        )

    except Exception as e:
        logger.error(f"[Metrics] Error loading metrics history: {e}")
        return {"dora_metrics": [], "flow_metrics": []}


def save_metrics_snapshot(
    metric_type: str, metrics_data: dict[str, Any], time_period_days: int
) -> bool:

    try:
        if metric_type not in ["dora_metrics", "flow_metrics"]:
            logger.error(f"[Metrics] Invalid metric type: {metric_type}")
            return False

        unified_data = load_unified_project_data()

        if "metrics_history" not in unified_data:
            unified_data["metrics_history"] = {
                "dora_metrics": [],
                "flow_metrics": [],
            }

        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "time_period_days": time_period_days,
            **metrics_data,
        }

        history = unified_data["metrics_history"][metric_type]

        today_date = datetime.now().date().isoformat()
        existing_today = [
            i
            for i, s in enumerate(history)
            if s.get("timestamp", "")[:10] == today_date
            and s.get("time_period_days") == time_period_days
        ]

        if existing_today:
            history[existing_today[0]] = snapshot
            logger.debug(
                f"[Metrics] Updated {metric_type} snapshot "
                f"for {time_period_days}d period"
            )
        else:
            history.append(snapshot)
            logger.debug(
                f"[Metrics] Added {metric_type} snapshot for {time_period_days}d period"
            )

        cutoff_date = (datetime.now() - timedelta(days=90)).isoformat()
        history[:] = [s for s in history if s.get("timestamp", "") >= cutoff_date]

        history.sort(key=lambda x: x.get("timestamp", ""))

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
) -> list[dict[str, Any]]:

    try:
        history = load_metrics_history()

        if metric_type not in history:
            return []

        metric_history = history[metric_type]

        trend_data = []
        for snapshot in metric_history:
            if snapshot.get("time_period_days") != time_period_days:
                continue

            metric_data = snapshot.get(metric_name, {})
            if isinstance(metric_data, dict) and "value" in metric_data:
                trend_data.append(
                    {
                        "date": snapshot.get("timestamp", "")[:10],
                        "value": metric_data["value"],
                        "unit": metric_data.get("unit", ""),
                    }
                )

        trend_data.sort(key=lambda x: x["date"])

        return trend_data

    except Exception as e:
        logger.error(f"[Metrics] Error getting trend data: {e}")
        return []
