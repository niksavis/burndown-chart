"""Unit tests for data/recommendations/correlation_signals.py.

Tests each cross-domain correlation signal (H1-H7) in isolation with
controlled metric inputs, and verifies that missing optional inputs
produce no errors (graceful skipping).
"""

import pandas as pd

from data.recommendations.correlation_signals import build_correlation_signals


def _make_df(
    completed: list[int],
    created: list[int] | None = None,
) -> pd.DataFrame:
    """Build a minimal statistics DataFrame."""
    n = len(completed)
    rows = {"completed_items": completed}
    if created is not None:
        rows["created_items"] = created
    else:
        rows["created_items"] = [0] * n
    return pd.DataFrame(rows)


def _find(signals: list[dict], signal_id: str) -> dict | None:
    return next((s for s in signals if s.get("id") == signal_id), None)


class TestGracefulHandling:
    def test_empty_dataframe_returns_empty(self):
        signals = build_correlation_signals(pd.DataFrame())
        assert signals == []

    def test_no_optional_params_returns_empty(self):
        df = _make_df([5, 6, 5, 7])
        signals = build_correlation_signals(df)
        assert isinstance(signals, list)

    def test_none_budget_skips_h1_h2_h3(self):
        df = _make_df([1, 10, 1, 10, 1, 10], created=[5, 5, 5, 5, 5, 5])
        signals = build_correlation_signals(df, budget_data=None)
        ids = [s["id"] for s in signals]
        assert "unstable_delivery_scope_creep" not in ids
        assert "budget_forecast_uncertainty" not in ids
        assert "performance_surplus" not in ids


class TestH1UnstableDeliveryScopeCreep:
    def _budget(self):
        return {"runway_weeks": 10}

    def test_fires_when_high_cv_and_scope_growing(self):
        # High CV: alternating 1/10 creates high variance
        # Scope growing: created > completed
        completed = [1, 10] * 6
        created = [8, 8] * 6
        df = _make_df(completed, created)
        signals = build_correlation_signals(df, budget_data=self._budget())
        s = _find(signals, "unstable_delivery_scope_creep")
        assert s is not None
        assert s["severity"] == "danger"

    def test_does_not_fire_when_low_cv(self):
        df = _make_df([5, 5, 5, 5, 5, 5], created=[1, 1, 1, 1, 1, 1])
        signals = build_correlation_signals(df, budget_data=self._budget())
        assert _find(signals, "unstable_delivery_scope_creep") is None

    def test_does_not_fire_when_scope_not_growing(self):
        # High CV but created_sum (12) does not exceed completed_sum*0.2 (13.2)
        completed = [1, 10] * 6  # sum = 66
        created = [1, 1] * 6  # sum = 12; 12 < 66 * 0.2 = 13.2
        df = _make_df(completed, created)
        signals = build_correlation_signals(df, budget_data=self._budget())
        assert _find(signals, "unstable_delivery_scope_creep") is None


class TestH2BudgetForecastUncertainty:
    def test_fires_when_low_runway_and_wide_pert_spread(self):
        df = _make_df([5, 5, 5, 5])
        budget = {"runway_weeks": 4}
        pert = {"pert_optimistic_days": 10, "pert_pessimistic_days": 45}
        signals = build_correlation_signals(df, budget_data=budget, pert_data=pert)
        s = _find(signals, "budget_forecast_uncertainty")
        assert s is not None
        assert s["severity"] == "danger"

    def test_does_not_fire_when_runway_is_adequate(self):
        df = _make_df([5, 5, 5, 5])
        budget = {"runway_weeks": 12}
        pert = {"pert_optimistic_days": 10, "pert_pessimistic_days": 45}
        signals = build_correlation_signals(df, budget_data=budget, pert_data=pert)
        assert _find(signals, "budget_forecast_uncertainty") is None

    def test_does_not_fire_when_pert_spread_is_narrow(self):
        df = _make_df([5, 5, 5, 5])
        budget = {"runway_weeks": 4}
        pert = {"pert_optimistic_days": 20, "pert_pessimistic_days": 30}
        signals = build_correlation_signals(df, budget_data=budget, pert_data=pert)
        assert _find(signals, "budget_forecast_uncertainty") is None


class TestH3PerformanceSurplus:
    def test_fires_when_velocity_accelerating_and_budget_surplus(self):
        # First half slow, second half fast → acceleration
        completed = [3, 3, 3, 3, 6, 6, 6, 6]
        df = _make_df(completed)
        budget = {"runway_weeks": 20}
        pert = {"pert_time_items": 42}  # 6 weeks
        signals = build_correlation_signals(df, budget_data=budget, pert_data=pert)
        s = _find(signals, "performance_surplus")
        assert s is not None
        assert s["severity"] == "success"

    def test_does_not_fire_when_velocity_not_accelerating(self):
        df = _make_df([5, 5, 5, 5, 5, 5, 5, 5])
        budget = {"runway_weeks": 20}
        pert = {"pert_time_items": 14}
        signals = build_correlation_signals(df, budget_data=budget, pert_data=pert)
        assert _find(signals, "performance_surplus") is None


class TestH4HighWipLongLeadTime:
    def test_fires_when_wip_high_and_lead_time_long(self):
        df = _make_df([5, 5, 5, 5])
        flow = {"has_data": True, "avg_wip": 25, "median_flow_time": 10}
        signals = build_correlation_signals(df, flow_metrics=flow)
        s = _find(signals, "high_wip_long_lead_time")
        assert s is not None
        assert s["severity"] == "warning"

    def test_does_not_fire_when_wip_low(self):
        df = _make_df([5, 5, 5, 5])
        flow = {"has_data": True, "avg_wip": 8, "median_flow_time": 12}
        signals = build_correlation_signals(df, flow_metrics=flow)
        assert _find(signals, "high_wip_long_lead_time") is None

    def test_does_not_fire_when_lead_time_short(self):
        df = _make_df([5, 5, 5, 5])
        flow = {"has_data": True, "avg_wip": 25, "median_flow_time": 3}
        signals = build_correlation_signals(df, flow_metrics=flow)
        assert _find(signals, "high_wip_long_lead_time") is None

    def test_does_not_fire_when_no_data(self):
        df = _make_df([5, 5, 5, 5])
        flow = {"has_data": False, "avg_wip": 30, "median_flow_time": 15}
        signals = build_correlation_signals(df, flow_metrics=flow)
        assert _find(signals, "high_wip_long_lead_time") is None


class TestH5BugVelocityDrain:
    def test_fires_when_high_bug_pct_and_declining_velocity(self):
        # First half fast, second half slow → decline
        completed = [8, 8, 8, 8, 4, 4, 4, 4]
        df = _make_df(completed)
        bug = {"has_data": True, "bug_investment_pct": 30, "resolution_rate": 60}
        signals = build_correlation_signals(df, bug_metrics=bug)
        s = _find(signals, "bug_velocity_drain")
        assert s is not None
        assert s["severity"] == "warning"

    def test_does_not_fire_when_bug_pct_low(self):
        completed = [8, 8, 8, 8, 4, 4, 4, 4]
        df = _make_df(completed)
        bug = {"has_data": True, "bug_investment_pct": 10, "resolution_rate": 60}
        signals = build_correlation_signals(df, bug_metrics=bug)
        assert _find(signals, "bug_velocity_drain") is None

    def test_does_not_fire_when_velocity_not_declining(self):
        df = _make_df([5, 5, 5, 5, 5, 5, 5, 5])
        bug = {"has_data": True, "bug_investment_pct": 35, "resolution_rate": 60}
        signals = build_correlation_signals(df, bug_metrics=bug)
        assert _find(signals, "bug_velocity_drain") is None


class TestH6QualityScopePressure:
    def test_fires_when_low_resolution_and_scope_growing(self):
        completed = [5, 5, 5, 5]
        created = [8, 8, 8, 8]
        df = _make_df(completed, created)
        bug = {"has_data": True, "resolution_rate": 40}
        signals = build_correlation_signals(df, bug_metrics=bug)
        s = _find(signals, "quality_scope_pressure")
        assert s is not None
        assert s["severity"] == "danger"

    def test_does_not_fire_when_resolution_rate_ok(self):
        completed = [5, 5, 5, 5]
        created = [8, 8, 8, 8]
        df = _make_df(completed, created)
        bug = {"has_data": True, "resolution_rate": 70}
        signals = build_correlation_signals(df, bug_metrics=bug)
        assert _find(signals, "quality_scope_pressure") is None

    def test_does_not_fire_when_scope_not_growing(self):
        completed = [8, 8, 8, 8]
        created = [3, 3, 3, 3]
        df = _make_df(completed, created)
        bug = {"has_data": True, "resolution_rate": 35}
        signals = build_correlation_signals(df, bug_metrics=bug)
        assert _find(signals, "quality_scope_pressure") is None


class TestH7DoraVelocityDivergence:
    def test_fires_when_low_dora_and_accelerating_velocity(self):
        completed = [3, 3, 3, 3, 6, 6, 6, 6]
        df = _make_df(completed)
        dora = {"overall_tier": "low"}
        signals = build_correlation_signals(df, dora_metrics=dora)
        s = _find(signals, "dora_velocity_divergence")
        assert s is not None
        assert s["severity"] == "info"

    def test_fires_for_medium_tier(self):
        completed = [3, 3, 3, 3, 6, 6, 6, 6]
        df = _make_df(completed)
        dora = {"overall_tier": "medium"}
        signals = build_correlation_signals(df, dora_metrics=dora)
        assert _find(signals, "dora_velocity_divergence") is not None

    def test_does_not_fire_for_elite_tier(self):
        completed = [3, 3, 3, 3, 6, 6, 6, 6]
        df = _make_df(completed)
        dora = {"overall_tier": "elite"}
        signals = build_correlation_signals(df, dora_metrics=dora)
        assert _find(signals, "dora_velocity_divergence") is None

    def test_does_not_fire_when_velocity_not_accelerating(self):
        df = _make_df([5, 5, 5, 5, 5, 5, 5, 5])
        dora = {"overall_tier": "low"}
        signals = build_correlation_signals(df, dora_metrics=dora)
        assert _find(signals, "dora_velocity_divergence") is None
