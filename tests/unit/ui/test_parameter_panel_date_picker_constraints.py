"""Regression tests for parameter panel timeline date picker constraints."""

from dash import dcc

from ui.parameter_panel.expanded_panel import (
    _create_date_picker_field,
    create_parameter_panel_expanded,
)


def test_timeline_date_picker_allows_historical_dates() -> None:
    """Timeline date picker should not enforce a today-based minimum date."""
    field_components = _create_date_picker_field(
        "Deadline",
        "deadline-picker",
        "deadline",
        "Leave empty for open-ended timeline",
    )

    date_picker = field_components[1]
    assert isinstance(date_picker, dcc.DatePickerSingle)

    picker_props = date_picker.to_plotly_json().get("props", {})
    assert "min_date_allowed" not in picker_props


def test_timeline_date_pickers_hydrate_from_settings_on_refresh() -> None:
    """Expanded panel should render persisted timeline dates on initial load."""
    panel = create_parameter_panel_expanded(
        settings={
            "pert_factor": 6,
            "deadline": "2026-12-31",
            "milestone": "2026-09-15",
            "data_points_count": 20,
        },
        statistics=None,
    )

    panel_json = panel.to_plotly_json()
    panel_text = str(panel_json)
    assert "2026-12-31" in panel_text
    assert "2026-09-15" in panel_text
