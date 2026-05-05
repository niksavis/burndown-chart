"""Tests for dashboard forecast scope alignment with current remaining work."""

from datetime import datetime

import pandas as pd

from callbacks.visualization_helpers import dashboard_tab


def test_render_dashboard_uses_current_remaining_scope_for_forecast(
    monkeypatch,
) -> None:
    """Forecast should use unified project remaining scope, not settings totals."""
    stats_df = pd.DataFrame(
        {
            "date": [datetime(2026, 4, 28)],
            "week_label": ["2026-W18"],
            "completed_items": [5],
            "completed_points": [20],
        }
    )
    settings = {
        "pert_factor": 1.2,
        "deadline": "2026-06-30",
        "data_points_count": 0,
        "total_items": 500,
        "total_points": 2000,
        "show_milestone": False,
    }
    captured: dict = {}

    monkeypatch.setattr(
        dashboard_tab,
        "load_unified_project_data",
        lambda: {
            "project_scope": {
                "remaining_items": 30,
                "remaining_total_points": 120,
            }
        },
    )
    monkeypatch.setattr(
        dashboard_tab,
        "compute_cumulative_values",
        lambda df, _items, _points: df,
    )

    def fake_create_forecast_plot(**kwargs):
        captured["forecast_total_items"] = kwargs["total_items"]
        captured["forecast_total_points"] = kwargs["total_points"]
        return None, {
            "pert_time_items": 12.0,
            "pert_time_points": 10.0,
        }

    monkeypatch.setattr(
        dashboard_tab, "create_forecast_plot", fake_create_forecast_plot
    )
    monkeypatch.setattr(
        dashboard_tab,
        "calculate_weekly_averages",
        lambda _records, data_points_count: (1.0, 2.0, 1.0, 2.0),
    )
    monkeypatch.setattr(
        dashboard_tab,
        "calculate_velocity_from_dataframe",
        lambda _df, _col: 1.5,
    )
    monkeypatch.setattr(
        dashboard_tab,
        "_load_budget_data",
        lambda _dpc, _pert: ("", "", "", None),
    )
    monkeypatch.setattr(dashboard_tab, "load_extended_metrics", lambda *_args: {})

    def fake_create_comprehensive_dashboard(**kwargs):
        captured["dashboard_total_items"] = kwargs["total_items"]
        captured["dashboard_total_points"] = kwargs["total_points"]
        return "dashboard"

    monkeypatch.setattr(
        dashboard_tab,
        "create_comprehensive_dashboard",
        fake_create_comprehensive_dashboard,
    )

    result = dashboard_tab._render_dashboard_tab(stats_df, settings, show_points=True)

    assert result == "dashboard"
    assert captured["forecast_total_items"] == 30
    assert captured["forecast_total_points"] == 120
    assert captured["dashboard_total_items"] == 30
    assert captured["dashboard_total_points"] == 120
