"""Shared velocity and throughput recommendation signals."""

from __future__ import annotations

from typing import Any

import pandas as pd


def build_velocity_trend_signals(statistics_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Build velocity trend signals from statistics data.

    Args:
        statistics_df: Project statistics with completed items.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if statistics_df.empty:
        return []

    mid_point = len(statistics_df) // 2
    if mid_point <= 0:
        return []

    recent_velocity = float(statistics_df.iloc[mid_point:]["completed_items"].mean())
    historical_velocity = float(
        statistics_df.iloc[:mid_point]["completed_items"].mean()
    )

    signals: list[dict[str, Any]] = []

    if historical_velocity > 0 and recent_velocity > historical_velocity * 1.1:
        pct_change = (recent_velocity / historical_velocity - 1) * 100
        signals.append(
            {
                "id": "velocity_acceleration",
                "severity": "success",
                "metrics": {
                    "pct_change": pct_change,
                    "recent_velocity": recent_velocity,
                    "historical_velocity": historical_velocity,
                },
            }
        )
    elif historical_velocity > 0 and recent_velocity < historical_velocity * 0.9:
        pct_change = (1 - recent_velocity / historical_velocity) * 100
        signals.append(
            {
                "id": "velocity_decline",
                "severity": "warning",
                "metrics": {
                    "pct_change": pct_change,
                    "recent_velocity": recent_velocity,
                    "historical_velocity": historical_velocity,
                },
            }
        )

    return signals


def build_throughput_signals(statistics_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Build throughput efficiency signals from statistics data.

    Args:
        statistics_df: Project statistics with completed items.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if statistics_df.empty:
        return []

    if len(statistics_df) < 8:
        return []

    mid_point = len(statistics_df) // 2
    recent_items = float(statistics_df.iloc[mid_point:]["completed_items"].sum())
    prev_items = float(statistics_df.iloc[:mid_point]["completed_items"].sum())

    signals: list[dict[str, Any]] = []

    if prev_items > 0 and recent_items > prev_items * 1.2:
        pct_increase = (recent_items / prev_items - 1) * 100
        signals.append(
            {
                "id": "throughput_increase",
                "severity": "success",
                "metrics": {
                    "pct_increase": pct_increase,
                    "recent_items": recent_items,
                    "prev_items": prev_items,
                },
            }
        )

    return signals


def build_velocity_consistency_signals(
    statistics_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Build velocity consistency signals from statistics data.

    Args:
        statistics_df: Project statistics with completed items.

    Returns:
        List of signal dictionaries with severity and metrics.
    """
    if statistics_df.empty:
        return []

    mean_velocity = float(statistics_df["completed_items"].mean())
    if mean_velocity <= 0:
        return []

    velocity_cv = float(statistics_df["completed_items"].std() / mean_velocity * 100)

    signals: list[dict[str, Any]] = []

    if velocity_cv < 20:
        signals.append(
            {
                "id": "velocity_consistent",
                "severity": "success",
                "metrics": {"velocity_cv": velocity_cv},
            }
        )
    elif velocity_cv > 50:
        signals.append(
            {
                "id": "velocity_inconsistent",
                "severity": "warning",
                "metrics": {"velocity_cv": velocity_cv},
            }
        )

    return signals
