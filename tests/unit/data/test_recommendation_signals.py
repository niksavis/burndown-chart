"""Tests for shared recommendation signals."""

from datetime import datetime, timedelta

import pandas as pd

from data.recommendations.budget_signals import (
    build_budget_forecast_signals,
    build_budget_health_signals,
)
from data.recommendations.pace_signals import build_required_pace_signals
from data.recommendations.velocity_signals import (
    build_throughput_signals,
    build_velocity_consistency_signals,
    build_velocity_trend_signals,
)


def test_velocity_trend_acceleration_signal():
    """Velocity acceleration should emit a signal."""
    statistics_df = pd.DataFrame({"completed_items": [5, 5, 5, 10, 10, 10]})

    signals = build_velocity_trend_signals(statistics_df)

    assert any(signal["id"] == "velocity_acceleration" for signal in signals)


def test_throughput_increase_signal():
    """Throughput increase should emit a signal."""
    statistics_df = pd.DataFrame({"completed_items": [4, 4, 4, 4, 8, 8, 8, 8]})

    signals = build_throughput_signals(statistics_df)

    assert any(signal["id"] == "throughput_increase" for signal in signals)


def test_velocity_consistency_inconsistent_signal():
    """High variance velocity should emit an inconsistency signal."""
    statistics_df = pd.DataFrame({"completed_items": [1, 12, 1, 12]})

    signals = build_velocity_consistency_signals(statistics_df)

    assert any(signal["id"] == "velocity_inconsistent" for signal in signals)


def test_budget_health_critical_signal():
    """Critical budget utilization should emit a critical signal."""
    budget_data = {
        "utilization_percentage": 95.0,
        "runway_weeks": 2.0,
        "burn_rate": 1000.0,
        "currency_symbol": "$",
    }

    signals = build_budget_health_signals(budget_data)

    assert any(signal["id"] == "budget_critical" for signal in signals)


def test_budget_health_no_consumption_signal():
    """Infinite runway should emit no-consumption signal only."""
    budget_data = {
        "utilization_percentage": 0.0,
        "runway_weeks": float("inf"),
        "burn_rate": 0.0,
        "currency_symbol": "$",
    }

    signals = build_budget_health_signals(budget_data)

    assert len(signals) == 1
    assert signals[0]["id"] == "budget_no_consumption"


def test_budget_forecast_shortfall_signal():
    """Short runway vs forecast should emit exhaustion signal."""
    signals = build_budget_forecast_signals(5.0, 10.0, 13.0)

    assert any(
        signal["id"] == "budget_exhaustion_before_completion" for signal in signals
    )


def test_required_pace_critically_behind_signal():
    """Low velocity against a near deadline should emit critical pace signal."""
    deadline = (datetime.now().date() + timedelta(days=7)).isoformat()
    statistics_df = pd.DataFrame(
        {
            "completed_items": [10.0, 10.0, 10.0],
            "remaining_items": [70.0, 70.0, 70.0],
        }
    )

    signals = build_required_pace_signals(statistics_df, deadline)

    assert any(signal["id"] == "pace_critically_behind" for signal in signals)


def test_required_pace_on_track_signal():
    """Slightly ahead pace should emit on-track signal."""
    deadline = (datetime.now().date() + timedelta(days=14)).isoformat()
    statistics_df = pd.DataFrame(
        {
            "completed_items": [5.5, 5.5, 5.5],
            "remaining_items": [10.0, 10.0, 10.0],
        }
    )

    signals = build_required_pace_signals(statistics_df, deadline)

    assert any(signal["id"] == "pace_on_track" for signal in signals)
