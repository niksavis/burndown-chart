import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from configuration.metrics_config import (
    FLOW_LOAD_RANGE_PERCENT,
    HIGHER_BETTER_METRICS,
    LOWER_BETTER_METRICS,
)
from data.iso_week_bucketing import get_week_label
from data.persistence.factory import get_backend
from data.profile_manager import get_data_file_path
from data.time_period_calculator import get_week_start_date, parse_year_week_label

logger = logging.getLogger(__name__)


def calculate_forecast(*args, **kwargs):  # noqa: PLC0415
    from data.metrics_calculator import calculate_forecast as _fn  # noqa: PLC0415

    return _fn(*args, **kwargs)


def calculate_trend_vs_forecast(*args, **kwargs):  # noqa: PLC0415
    from data.metrics_calculator import (  # noqa: PLC0415
        calculate_trend_vs_forecast as _fn,  # noqa: PLC0415
    )

    return _fn(*args, **kwargs)


def calculate_flow_load_range(*args, **kwargs):  # noqa: PLC0415
    from data.metrics_calculator import (  # noqa: PLC0415
        calculate_flow_load_range as _fn,  # noqa: PLC0415
    )

    return _fn(*args, **kwargs)


_snapshots_lock = threading.Lock()

_snapshots_cache: dict[str, dict[str, Any]] | None = None
_cache_query_id: str | None = None

_batch_mode_active = False
_batch_snapshots = None


def _get_snapshots_file_path() -> Path:

    return get_data_file_path("metrics_snapshots.json")


def load_snapshots() -> dict[str, dict[str, Any]]:

    global _snapshots_cache, _cache_query_id

    try:
        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.info("No active profile/query, returning empty snapshots")
            return {}

        if _snapshots_cache is not None and _cache_query_id == active_query_id:
            return _snapshots_cache

        snapshots = {}
        for metric_type in ["dora", "flow", "custom"]:
            snapshot_list = backend.get_metrics_snapshots(
                active_profile_id,
                active_query_id,
                metric_type,
                limit=10000,
            )

            for row in snapshot_list:
                snapshot_date_str = row["snapshot_date"]
                snapshot_date = datetime.fromisoformat(snapshot_date_str).date()
                week_label = get_week_label(
                    datetime.combine(snapshot_date, datetime.min.time())
                )

                if week_label not in snapshots:
                    snapshots[week_label] = {}

                metric_name = row["metric_name"]

                metric_data = {}

                if row.get("calculation_metadata"):
                    metric_data.update(row["calculation_metadata"])

                metric_value = row.get("metric_value")
                if isinstance(metric_value, dict):
                    metric_data.update(metric_value)
                else:
                    metric_data["value"] = metric_value
                    metric_data["unit"] = row.get("metric_unit", "")

                metric_data["excluded_issue_count"] = row.get("excluded_issue_count", 0)

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

        _snapshots_cache = snapshots
        _cache_query_id = active_query_id

        return snapshots
    except Exception as e:
        logger.error(f"Failed to load snapshots from database: {e}", exc_info=True)
        return {}


def clear_snapshots_cache() -> None:
    global _snapshots_cache, _cache_query_id
    _snapshots_cache = None
    _cache_query_id = None
    logger.info("Cleared snapshots cache")


def save_snapshots(snapshots: dict[str, dict[str, Any]]) -> bool:

    try:
        backend = get_backend()

        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.error("No active profile/query to save snapshots to")
            return False

        for week, metrics in snapshots.items():
            year, week_num = parse_year_week_label(week)
            week_start = get_week_start_date(year, week_num)
            snapshot_date = week_start.strftime("%Y-%m-%d")

            flow_metrics = {k: v for k, v in metrics.items() if k.startswith("flow_")}
            dora_metrics = {k: v for k, v in metrics.items() if k.startswith("dora_")}
            custom_metrics = {
                k: v
                for k, v in metrics.items()
                if not k.startswith("flow_") and not k.startswith("dora_")
            }

            if flow_metrics:
                backend.save_metrics_snapshot(
                    active_profile_id,
                    active_query_id,
                    snapshot_date,
                    "flow",
                    flow_metrics,
                )

            if dora_metrics:
                backend.save_metrics_snapshot(
                    active_profile_id,
                    active_query_id,
                    snapshot_date,
                    "dora",
                    dora_metrics,
                )

            if custom_metrics:
                backend.save_metrics_snapshot(
                    active_profile_id,
                    active_query_id,
                    snapshot_date,
                    "custom",
                    custom_metrics,
                )

        logger.info(f"Saved {len(snapshots)} weeks of metric snapshots to database")

        clear_snapshots_cache()

        return True
    except Exception as e:
        logger.error(f"Failed to save snapshots to database: {e}")
        return False


def save_metric_snapshot(
    week_label: str, metric_name: str, metric_data: dict[str, Any]
) -> bool:

    global _batch_mode_active, _batch_snapshots

    with _snapshots_lock:
        if _batch_mode_active:
            if _batch_snapshots is None:
                raise RuntimeError("Batch mode active but _batch_snapshots is None")

            if week_label not in _batch_snapshots:
                _batch_snapshots[week_label] = {}

            metric_data_with_timestamp = {
                **metric_data,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            _batch_snapshots[week_label][metric_name] = metric_data_with_timestamp
            logger.debug(
                f"[Batch] Queued snapshot for {metric_name} in week {week_label}"
            )
            return True

        snapshots = load_snapshots()

        if week_label not in snapshots:
            snapshots[week_label] = {}

        metric_data_with_timestamp = {
            **metric_data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        snapshots[week_label][metric_name] = metric_data_with_timestamp

        logger.info(f"Saving snapshot for {metric_name} in week {week_label}")
        return save_snapshots(snapshots)


class batch_write_mode:
    def __enter__(self):
        global _batch_mode_active, _batch_snapshots

        with _snapshots_lock:
            if _batch_mode_active:
                raise RuntimeError("Cannot nest batch_write_mode contexts")

            _batch_mode_active = True
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
                    num_weeks = len(_batch_snapshots)
                    logger.info(f"[Batch] Flushing {num_weeks} weeks to disk...")
                    save_snapshots(_batch_snapshots)
                    logger.info(
                        f"[Batch] Batch write complete: {num_weeks} weeks "
                        "saved in single write"
                    )
                else:
                    logger.warning(
                        "[Batch] Exception occurred, discarding batched "
                        f"changes: {exc_val}"
                    )
            finally:
                _batch_mode_active = False
                _batch_snapshots = None

        return False


def get_metric_snapshot(week_label: str, metric_name: str) -> dict[str, Any] | None:

    snapshots = load_snapshots()
    return snapshots.get(week_label, {}).get(metric_name)


def get_metric_weekly_values(
    week_labels: list[str], metric_name: str, value_key: str
) -> list[float]:

    snapshots = load_snapshots()
    values = []

    for week_label in week_labels:
        metric_data = snapshots.get(week_label, {}).get(metric_name)
        if metric_data and value_key in metric_data:
            values.append(metric_data[value_key])
        else:
            values.append(0)

    return values


def get_last_n_weeks_values(
    metric_key: str,
    value_key: str,
    n_weeks: int = 4,
    current_week: str | None = None,
) -> list[float]:

    snapshots = load_snapshots()

    all_weeks = sorted(snapshots.keys(), reverse=True)

    values = []

    for week_label in all_weeks:
        if current_week and week_label == current_week:
            continue

        metric_snapshot = snapshots.get(week_label, {}).get(metric_key)

        if metric_snapshot and value_key in metric_snapshot:
            value = metric_snapshot[value_key]
            if isinstance(value, (int, float)) and value >= 0:
                values.append(float(value))

        if len(values) >= n_weeks:
            break

    return list(reversed(values))


def cleanup_old_snapshots(weeks_to_keep: int = 52) -> int:

    snapshots = load_snapshots()

    weeks = sorted(snapshots.keys(), reverse=True)
    if len(weeks) <= weeks_to_keep:
        logger.info(f"No cleanup needed: {len(weeks)} weeks <= {weeks_to_keep} limit")
        return 0

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


def get_snapshot_stats() -> dict[str, Any]:

    snapshots = load_snapshots()
    snapshot_path = _get_snapshots_file_path()

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


def get_weekly_metrics(week_label: str) -> dict[str, Any]:

    snapshots = load_snapshots()
    return snapshots.get(week_label, {})


def save_flow_time_snapshot(week_label: str, data: dict[str, Any]) -> bool:

    return save_metric_snapshot(week_label, "flow_time", data)


def save_flow_efficiency_snapshot(week_label: str, data: dict[str, Any]) -> bool:

    return save_metric_snapshot(week_label, "flow_efficiency", data)


def save_dora_metrics_snapshot(
    week_label: str, deployment_data: dict[str, Any], lead_time_data: dict[str, Any]
) -> bool:

    deployment_success = save_metric_snapshot(
        week_label, "dora_deployment_frequency", deployment_data
    )
    lead_time_success = save_metric_snapshot(
        week_label, "dora_lead_time", lead_time_data
    )

    return deployment_success and lead_time_success


def has_metric_snapshot(week_label: str, metric_name: str) -> bool:

    return get_metric_snapshot(week_label, metric_name) is not None


def get_available_weeks() -> list[str]:

    snapshots = load_snapshots()
    return sorted(snapshots.keys(), reverse=True)


def save_metric_snapshot_with_forecast(
    week_label: str,
    metric_name: str,
    metric_data: dict[str, Any],
    metric_type: str | None = None,
) -> bool:

    success = save_metric_snapshot(week_label, metric_name, metric_data)
    if not success:
        return False

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
        return True

    historical_values = get_last_n_weeks_values(
        metric_key=metric_name,
        value_key=value_key,
        n_weeks=4,
        current_week=week_label,
    )

    forecast_data = calculate_forecast(historical_values) if historical_values else None

    if forecast_data:
        if not metric_type:
            if metric_name in HIGHER_BETTER_METRICS:
                metric_type = "higher_better"
            elif metric_name in LOWER_BETTER_METRICS:
                metric_type = "lower_better"

        current_value = metric_data.get(value_key, 0)

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

        if metric_name == "flow_load" and forecast_data:
            try:
                range_data = calculate_flow_load_range(
                    forecast_value=forecast_data["forecast_value"],
                    range_percent=FLOW_LOAD_RANGE_PERCENT,
                )
                forecast_data["forecast_range"] = range_data
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate Flow Load range: {e}")

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

    logger.info(f"Adding forecast data to all metrics for week {week_label}")

    metric_configs = {
        "flow_velocity": {
            "value_key": "completed_count",
            "metric_type": "higher_better",
        },
        "flow_load": {"value_key": "wip_count", "metric_type": None},
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

        historical_values = get_last_n_weeks_values(
            metric_key=metric_name,
            value_key=value_key,
            n_weeks=4,
            current_week=week_label,
        )

        forecast_data = (
            calculate_forecast(historical_values) if historical_values else None
        )

        if not forecast_data:
            logger.debug(f"No forecast for {metric_name} (insufficient history)")
            continue

        metric_snapshot = snapshots.get(week_label, {}).get(metric_name)
        if not metric_snapshot:
            logger.debug(f"No snapshot found for {metric_name} in week {week_label}")
            continue

        current_value = metric_snapshot.get(value_key)

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

        if metric_name == "flow_load":
            try:
                range_data = calculate_flow_load_range(
                    forecast_value=forecast_data["forecast_value"],
                    range_percent=FLOW_LOAD_RANGE_PERCENT,
                )
                forecast_data["forecast_range"] = range_data
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to calculate Flow Load range: {e}")

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
