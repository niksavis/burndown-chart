from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from dash import no_update

from callbacks.settings.core_settings import register
from callbacks.settings.parameter_panel import register as register_parameter_panel
from data import metrics_snapshots


class CallbackRegistry:
    def __init__(self) -> None:
        self.functions: dict[str, Callable[..., Any]] = {}

    def callback(self, *args: Any, **kwargs: Any) -> Callable:
        def capture(function: Callable[..., Any]) -> Callable[..., Any]:
            self.functions[function.__name__] = function
            return function

        return capture


def test_parameter_button_remount_does_not_replay_stale_panel_state() -> None:
    app = CallbackRegistry()
    register_parameter_panel(app)
    result = app.functions["toggle_parameter_panel"](
        0, True, {"is_open": True}, False, False
    )
    assert result == (no_update, no_update, no_update, no_update)


@pytest.mark.parametrize(
    "statistics", [[], [{"date": "2026-01-26", "completed_items": 4}]]
)
def test_completed_profile_switch_publishes_the_new_statistics(
    statistics: list,
) -> None:
    app = CallbackRegistry()
    register(app)
    with (
        patch(
            "callbacks.settings.core_settings.get_active_profile",
            return_value=SimpleNamespace(id="demo-empty"),
        ),
        patch(
            "callbacks.settings.core_settings.load_app_settings",
            return_value={"show_points": True},
        ),
        patch(
            "callbacks.settings.core_settings.load_unified_project_data",
            return_value={"statistics": statistics},
        ),
    ):
        result = app.functions["reload_settings_after_import_or_switch"](0, 1)
    assert result[2] == statistics


def test_snapshot_cache_distinguishes_profiles_with_the_same_query_id() -> None:
    state = {"active_profile_id": "demo-complete", "active_query_id": "main"}
    backend = MagicMock()
    backend.get_app_state.side_effect = state.get

    def snapshots(profile: str, query: str, metric: str, **kwargs: Any) -> list[dict]:
        if profile != "demo-complete" or metric != "flow":
            return []
        return [
            {
                "snapshot_date": "2026-01-26",
                "metric_name": "flow_velocity",
                "metric_value": {"completed_count": 4},
            }
        ]

    backend.get_metrics_snapshots.side_effect = snapshots
    metrics_snapshots.clear_snapshots_cache()
    try:
        with patch.object(metrics_snapshots, "get_backend", return_value=backend):
            first = metrics_snapshots.load_snapshots()
            assert first["2026-W05"]["flow_velocity"]["completed_count"] == 4
            state["active_profile_id"] = "demo-empty"
            assert metrics_snapshots.load_snapshots() == {}
    finally:
        metrics_snapshots.clear_snapshots_cache()
