"""Metrics operations mixin for SQLiteBackend."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from data.database import get_db_connection

logger = logging.getLogger(__name__)


class MetricsMixin:
    """Mixin for metrics data operations."""

    db_path: Path  # Set by composition class (SQLiteBackend)

    def get_metric_values(
        self,
        profile_id: str,
        query_id: str,
        metric_name: str | None = None,
        metric_category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Query normalized metric data points."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                query = "SELECT * FROM metrics_data_points WHERE profile_id = ? AND query_id = ?"
                params: list[Any] = [profile_id, query_id]

                if metric_name:
                    query += " AND metric_name = ?"
                    params.append(metric_name)
                if metric_category:
                    query += " AND metric_category = ?"
                    params.append(metric_category)
                if start_date:
                    query += " AND snapshot_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND snapshot_date <= ?"
                    params.append(end_date)

                query += " ORDER BY snapshot_date DESC"

                if limit:
                    query += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query, params)
                results = cursor.fetchall()

                metrics = []
                for row in results:
                    metric = dict(row)
                    metric_value = metric.get("metric_value")
                    if isinstance(metric_value, str) and (
                        metric_value.startswith("{") or metric_value.startswith("[")
                    ):
                        try:
                            metric["metric_value"] = json.loads(metric_value)
                        except (json.JSONDecodeError, TypeError):
                            pass
                    if metric.get("calculation_metadata"):
                        metric["calculation_metadata"] = json.loads(
                            metric["calculation_metadata"]
                        )
                    metrics.append(metric)

                return metrics

        except Exception as e:
            logger.error(
                f"Failed to get metric values for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def delete_metrics(
        self,
        profile_id: str,
        query_id: str,
    ) -> int:
        """Delete all metrics for a specific profile/query combination."""
        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM metrics_data_points WHERE profile_id = ? AND query_id = ?",
                    (profile_id, query_id),
                )
                deleted_count = cursor.rowcount
                conn.commit()
                logger.info(
                    f"Deleted {deleted_count} metrics for {profile_id}/{query_id}"
                )
                return deleted_count

        except Exception as e:
            logger.error(
                f"Failed to delete metrics for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def save_metrics_batch(
        self,
        profile_id: str,
        query_id: str,
        metrics: list[dict],
    ) -> None:
        """Batch UPSERT metric data points."""
        if not metrics:
            return

        try:
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()

                for metric in metrics:
                    metric_value = metric.get("metric_value")
                    if isinstance(metric_value, (dict, list)):
                        metric_value = json.dumps(metric_value)

                    cursor.execute(
                        """
                        INSERT INTO metrics_data_points (
                            profile_id, query_id, snapshot_date, metric_category, metric_name,
                            metric_value, metric_unit, excluded_issue_count, calculation_metadata,
                            forecast_value, forecast_confidence_low, forecast_confidence_high, calculated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(profile_id, query_id, snapshot_date, metric_category, metric_name) DO UPDATE SET
                            metric_value = excluded.metric_value,
                            metric_unit = excluded.metric_unit,
                            excluded_issue_count = excluded.excluded_issue_count,
                            calculation_metadata = excluded.calculation_metadata,
                            forecast_value = excluded.forecast_value,
                            forecast_confidence_low = excluded.forecast_confidence_low,
                            forecast_confidence_high = excluded.forecast_confidence_high,
                            calculated_at = excluded.calculated_at
                    """,
                        (
                            profile_id,
                            query_id,
                            metric.get("snapshot_date"),
                            metric.get("metric_category"),
                            metric.get("metric_name"),
                            metric_value,
                            metric.get("metric_unit"),
                            metric.get("excluded_issue_count", 0),
                            json.dumps(metric.get("calculation_metadata"))
                            if metric.get("calculation_metadata")
                            else None,
                            metric.get("forecast_value"),
                            metric.get("forecast_confidence_low"),
                            metric.get("forecast_confidence_high"),
                            datetime.now().isoformat(),
                        ),
                    )

                conn.commit()
                logger.info(f"Saved {len(metrics)} metrics for {profile_id}/{query_id}")

        except Exception as e:
            logger.error(
                f"Failed to save metrics batch for {profile_id}/{query_id}: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise

    def get_metrics_snapshots(
        self, profile_id: str, query_id: str, metric_type: str, limit: int = 52
    ) -> list[dict]:
        """LEGACY: Get metrics snapshots - returns normalized metrics."""
        return self.get_metric_values(
            profile_id, query_id, metric_category=metric_type, limit=limit
        )

    def save_metrics_snapshot(
        self,
        profile_id: str,
        query_id: str,
        snapshot_date: str,
        metric_type: str,
        metrics: dict,
        forecast: dict | None = None,
    ) -> None:
        """LEGACY: Save metrics snapshot - converts to normalized metrics."""
        metric_list = []
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (dict, list)):
                metric_value = json.dumps(metric_value)

            metric_list.append(
                {
                    "snapshot_date": snapshot_date,
                    "metric_category": metric_type,
                    "metric_name": metric_name,
                    "metric_value": metric_value,
                    "metric_unit": "",
                }
            )
        self.save_metrics_batch(profile_id, query_id, metric_list)
