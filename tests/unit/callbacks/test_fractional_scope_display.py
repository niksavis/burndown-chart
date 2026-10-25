import pytest

from callbacks import query_switching
from callbacks.settings import helpers


@pytest.mark.parametrize("points", [0.0, 2.5, 1000.5])
def test_data_window_points_are_parseable_without_losing_fractions(
    monkeypatch: pytest.MonkeyPatch, points: float
) -> None:
    scope = {"remaining_items": 2, "remaining_total_points": points}
    monkeypatch.setattr(
        helpers, "load_unified_project_data", lambda: {"project_scope": scope}
    )
    result = helpers.calculate_remaining_work_for_data_window(4, [])
    assert result is not None
    assert float(result[3]) == points
    assert result[4]["total_points"] == points


@pytest.mark.parametrize("points", [0.0, 2.5, 1000.5])
def test_query_switch_points_are_parseable_without_losing_fractions(
    monkeypatch: pytest.MonkeyPatch, points: float
) -> None:
    scope = {"remaining_items": 2, "remaining_total_points": points}
    monkeypatch.setattr(query_switching, "switch_query", lambda _: None)
    monkeypatch.setattr(
        query_switching, "get_active_profile_id", lambda: "demo-fractional-points"
    )
    monkeypatch.setattr(query_switching, "get_query_dropdown_options", lambda _: [])
    monkeypatch.setattr(
        query_switching, "load_unified_project_data", lambda: {"project_scope": scope}
    )
    monkeypatch.setattr(query_switching, "load_app_settings", lambda: {})
    result = query_switching.load_query_cached_data(1, "main")
    assert float(result[2]) == points
    assert result[4]["total_points"] == points
