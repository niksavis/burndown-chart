"""Shared scope recommendation signals."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_scope_signals(statistics_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Build scope-related signals from statistics data.

    Args:
        statistics_df: Project statistics with created/completed columns.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if statistics_df.empty:
        return []

    if "created_items" not in statistics_df.columns:
        return []

    if "completed_items" not in statistics_df.columns:
        return []

    signals: list[dict[str, Any]] = []
    weeks_count = int(len(statistics_df))
    total_created = float(statistics_df["created_items"].sum())
    total_completed = float(statistics_df["completed_items"].sum())

    if weeks_count >= 4:
        recent_stats = statistics_df.tail(4)
        recent_created = float(recent_stats["created_items"].sum())
        recent_completed = float(recent_stats["completed_items"].sum())
        weeks_over = int(
            (recent_stats["created_items"] > recent_stats["completed_items"]).sum()
        )
        recent_net = recent_completed - recent_created

        if recent_created > recent_completed and weeks_over >= 3:
            excess_pct = (
                (recent_created - recent_completed) / recent_completed * 100
                if recent_completed > 0
                else 0
            )
            signals.append(
                {
                    "id": "scope_creep_acceleration",
                    "severity": "warning",
                    "metrics": {
                        "weeks_over": weeks_over,
                        "recent_created": recent_created,
                        "recent_completed": recent_completed,
                        "excess_pct": excess_pct,
                    },
                }
            )

        if recent_net > 0 and weeks_over >= 4:
            signals.append(
                {
                    "id": "scope_burndown_acceleration",
                    "severity": "success",
                    "metrics": {
                        "weeks_over": weeks_over,
                        "recent_net": recent_net,
                    },
                }
            )

    if total_created > 0:
        ratio = total_created / total_completed if total_completed > 0 else 0
        severity = "warning" if total_created > total_completed * 0.2 else "info"
        signals.append(
            {
                "id": "scope_growth_ratio",
                "severity": severity,
                "metrics": {
                    "weeks_count": weeks_count,
                    "total_created": total_created,
                    "total_completed": total_completed,
                    "ratio": ratio,
                },
            }
        )

    return signals
