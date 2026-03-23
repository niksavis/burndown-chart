"""Unit tests for Sprint Tracker callback behavior."""

from types import SimpleNamespace

from dash import no_update

import callbacks.sprint_tracker as sprint_tracker_callbacks


def test_update_sprint_charts_returns_single_no_update_when_hidden(monkeypatch):
    """Hidden charts path must return a single no_update sentinel."""
    monkeypatch.setattr(
        sprint_tracker_callbacks,
        "callback_context",
        SimpleNamespace(triggered=[]),
    )

    result = sprint_tracker_callbacks.update_sprint_charts(
        selected_sprint="Sprint 24",
        charts_visible=False,
        points_toggle_list=[],
    )

    assert result is no_update
