"""Shared required pace recommendation signals."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from data.velocity_projections import assess_pace_health, calculate_required_velocity


def build_required_pace_signals(
    statistics_df: pd.DataFrame,
    deadline: str | None,
    time_unit: str = "week",
) -> list[dict[str, Any]]:
    """Build required pace signals from statistics data and deadline.

    Args:
        statistics_df: Project statistics with remaining/completed columns.
        deadline: Deadline date string.
        time_unit: Time unit for velocity calculations.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if statistics_df.empty or not deadline:
        return []

    deadline_date = pd.to_datetime(deadline)
    if pd.isna(deadline_date):
        return []

    current_date = datetime.combine(datetime.now().date(), datetime.min.time())
    days_to_deadline = max(0, (deadline_date - current_date).days)

    if "remaining_items" not in statistics_df.columns:
        return []

    remaining_items = float(statistics_df.iloc[-1]["remaining_items"])
    current_velocity_items = float(statistics_df["completed_items"].mean())

    required_velocity_items = calculate_required_velocity(
        remaining_items, deadline_date, current_date, time_unit=time_unit
    )

    signals: list[dict[str, Any]] = []

    if required_velocity_items == float("inf"):
        signals.append(
            {
                "id": "pace_deadline_exceeded",
                "severity": "danger",
                "metrics": {
                    "remaining_items": remaining_items,
                    "days_to_deadline": days_to_deadline,
                    "current_velocity_items": current_velocity_items,
                    "required_velocity_items": required_velocity_items,
                },
            }
        )
        return signals

    if required_velocity_items <= 0:
        return signals

    pace_health_items = assess_pace_health(
        current_velocity_items, required_velocity_items
    )

    ratio = float(pace_health_items.get("ratio", 0))
    gap_pct = (1 - ratio) * 100 if ratio > 0 else 0
    gap_absolute = required_velocity_items - current_velocity_items
    delay_days = (gap_pct / 100) * days_to_deadline if days_to_deadline > 0 else 0

    if pace_health_items.get("status") in {"behind", "behind_pace"} and ratio < 0.7:
        signals.append(
            {
                "id": "pace_critically_behind",
                "severity": "danger",
                "metrics": {
                    "gap_pct": gap_pct,
                    "gap_absolute": gap_absolute,
                    "delay_days": delay_days,
                    "remaining_items": remaining_items,
                    "days_to_deadline": days_to_deadline,
                    "current_velocity_items": current_velocity_items,
                    "required_velocity_items": required_velocity_items,
                    "ratio": ratio,
                },
            }
        )
    elif pace_health_items.get("status") == "at_risk" and 0.8 <= ratio < 1.0:
        signals.append(
            {
                "id": "pace_at_risk",
                "severity": "warning",
                "metrics": {
                    "gap_pct": gap_pct,
                    "gap_absolute": gap_absolute,
                    "delay_days": delay_days,
                    "remaining_items": remaining_items,
                    "days_to_deadline": days_to_deadline,
                    "current_velocity_items": current_velocity_items,
                    "required_velocity_items": required_velocity_items,
                    "ratio": ratio,
                },
            }
        )
    elif pace_health_items.get("status") == "on_pace" and ratio >= 1.2:
        ahead_pct = (ratio - 1.0) * 100
        days_ahead = (ahead_pct / 100) * days_to_deadline if days_to_deadline > 0 else 0
        extra_capacity_items = (ahead_pct / 100) * remaining_items
        signals.append(
            {
                "id": "pace_significantly_ahead",
                "severity": "success",
                "metrics": {
                    "ahead_pct": ahead_pct,
                    "days_ahead": days_ahead,
                    "extra_capacity_items": extra_capacity_items,
                    "remaining_items": remaining_items,
                    "days_to_deadline": days_to_deadline,
                    "current_velocity_items": current_velocity_items,
                    "required_velocity_items": required_velocity_items,
                    "ratio": ratio,
                },
            }
        )
    elif pace_health_items.get("status") == "on_pace" and 1.0 <= ratio < 1.2:
        ahead_pct = (ratio - 1.0) * 100
        signals.append(
            {
                "id": "pace_on_track",
                "severity": "success",
                "metrics": {
                    "ahead_pct": ahead_pct,
                    "remaining_items": remaining_items,
                    "days_to_deadline": days_to_deadline,
                    "current_velocity_items": current_velocity_items,
                    "required_velocity_items": required_velocity_items,
                    "ratio": ratio,
                },
            }
        )

    remaining_points = (
        float(statistics_df.iloc[-1]["remaining_points"])
        if "remaining_points" in statistics_df.columns
        else None
    )

    if remaining_points and "completed_points" in statistics_df.columns:
        current_velocity_points = float(statistics_df["completed_points"].mean())
        required_velocity_points = calculate_required_velocity(
            remaining_points, deadline_date, current_date, time_unit=time_unit
        )

        if required_velocity_points != float("inf"):
            pace_health_points = assess_pace_health(
                current_velocity_points, required_velocity_points
            )
            ratio_diff = abs(
                float(pace_health_items.get("ratio", 0))
                - float(pace_health_points.get("ratio", 0))
            )
            if ratio_diff > 0.15:
                signals.append(
                    {
                        "id": "pace_metric_divergence",
                        "severity": "warning",
                        "metrics": {
                            "ratio_items": float(pace_health_items.get("ratio", 0)),
                            "ratio_points": float(pace_health_points.get("ratio", 0)),
                        },
                    }
                )

    return signals
