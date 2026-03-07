"""
Unit tests for data/recommendations/scope_signals.py

Uses real pandas DataFrames — no mocking, no I/O, no database.
"""

import pandas as pd

from data.recommendations.scope_signals import build_scope_signals

###############################################################################
# Helpers
###############################################################################


def _df(created: list[int], completed: list[int]) -> pd.DataFrame:
    return pd.DataFrame({"created_items": created, "completed_items": completed})


def _signal_ids(signals: list[dict]) -> set[str]:
    return {s["id"] for s in signals}


###############################################################################
# Edge cases / guard clauses
###############################################################################


class TestBuildScopeSignalsEdgeCases:
    def test_empty_dataframe_returns_empty(self) -> None:
        assert build_scope_signals(pd.DataFrame()) == []

    def test_missing_created_items_column_returns_empty(self) -> None:
        df = pd.DataFrame({"completed_items": [5, 6, 7, 8]})
        assert build_scope_signals(df) == []

    def test_missing_completed_items_column_returns_empty(self) -> None:
        df = pd.DataFrame({"created_items": [5, 6, 7, 8]})
        assert build_scope_signals(df) == []

    def test_fewer_than_4_rows_no_scope_creep_signal(self) -> None:
        # Less than 4 weeks — scope_creep/scope_burndown blocks are skipped
        df = _df([10, 10, 10], [5, 5, 5])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_creep_acceleration" not in ids

    def test_all_zeros_no_scope_growth_ratio_signal(self) -> None:
        df = _df([0, 0, 0, 0], [0, 0, 0, 0])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_growth_ratio" not in ids


###############################################################################
# scope_creep_acceleration signal
###############################################################################


class TestScopeCreepAcceleration:
    def test_scope_creep_detected_when_high_and_sustained(self) -> None:
        # 4 recent weeks: created >> completed in all 4
        df = _df(
            # older weeks don't matter here, we use tail(4)
            [20, 20, 20, 20],
            [5, 5, 5, 5],
        )
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_creep_acceleration" in ids

    def test_scope_creep_requires_3_or_more_over_weeks(self) -> None:
        # Only 2 out of 4 recent weeks are over (created > completed)
        df = _df(
            [3, 3, 20, 20],
            # week 0,1: completed > created; week 2,3: created > completed
            [5, 5, 10, 10],
        )
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_creep_acceleration" not in ids

    def test_scope_creep_not_when_completed_exceeds_created(self) -> None:
        df = _df([3, 3, 3, 3], [10, 10, 10, 10])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_creep_acceleration" not in ids

    def test_scope_creep_signal_has_required_metrics(self) -> None:
        df = _df([20, 20, 20, 20], [5, 5, 5, 5])
        signals = build_scope_signals(df)
        creep = next(s for s in signals if s["id"] == "scope_creep_acceleration")
        assert "severity" in creep
        assert "metrics" in creep
        metrics = creep["metrics"]
        assert "weeks_over" in metrics
        assert "recent_created" in metrics
        assert "recent_completed" in metrics
        assert "excess_pct" in metrics


###############################################################################
# scope_burndown_acceleration signal
###############################################################################


class TestScopeBurndownAcceleration:
    def test_burndown_not_triggered_when_completed_exceeds_created_in_aggregate(
        self,
    ) -> None:
        # scope_burndown requires recent_net > 0 AND weeks_over >= 4.
        # weeks_over counts weeks where created > completed. If all 4 tail
        # weeks have created > completed, recent_net < 0. The two conditions
        # are mutually exclusive with a 4-row tail window, so signal never fires.
        df = _df([3, 3, 3, 3], [10, 10, 10, 10])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_burndown_acceleration" not in ids

    def test_burndown_requires_all_4_recent_weeks_over(self) -> None:
        # Only 3 out of 4 weeks have completed > created
        df = _df([10, 3, 3, 3], [3, 10, 10, 10])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_burndown_acceleration" not in ids


###############################################################################
# scope_growth_ratio signal
###############################################################################


class TestScopeGrowthRatio:
    def test_growth_ratio_added_when_created_items_exist(self) -> None:
        df = _df([5, 5], [10, 10])
        ids = _signal_ids(build_scope_signals(df))
        assert "scope_growth_ratio" in ids

    def test_growth_ratio_warning_when_created_more_than_20pct_of_completed(
        self,
    ) -> None:
        # created = 10, completed = 5 → ratio > 0.2
        df = _df([10], [5])
        signals = build_scope_signals(df)
        ratio_signal = next(
            (s for s in signals if s["id"] == "scope_growth_ratio"), None
        )
        assert ratio_signal is not None
        assert ratio_signal["severity"] == "warning"

    def test_growth_ratio_info_when_low(self) -> None:
        # created = 1, completed = 100 → ratio < 0.2
        df = _df([1], [100])
        signals = build_scope_signals(df)
        ratio_signal = next(
            (s for s in signals if s["id"] == "scope_growth_ratio"), None
        )
        assert ratio_signal is not None
        assert ratio_signal["severity"] == "info"

    def test_growth_ratio_zero_completed_no_crash(self) -> None:
        df = _df([5], [0])
        signals = build_scope_signals(df)
        ratio_signal = next(
            (s for s in signals if s["id"] == "scope_growth_ratio"), None
        )
        assert ratio_signal is not None
        assert ratio_signal["metrics"]["ratio"] == 0  # 0 / 0 guard

    def test_growth_ratio_signal_has_required_metrics(self) -> None:
        df = _df([5, 5], [10, 10])
        signals = build_scope_signals(df)
        ratio = next(s for s in signals if s["id"] == "scope_growth_ratio")
        m = ratio["metrics"]
        assert "weeks_count" in m
        assert "total_created" in m
        assert "total_completed" in m
        assert "ratio" in m
