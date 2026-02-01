"""Expanded parameter panel component with all input fields."""

from typing import Optional, cast
from datetime import datetime
import math

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.budget_settings_card import create_budget_settings_card
from ui.help_system import create_parameter_tooltip


def create_parameter_panel_expanded(
    settings: dict,
    id_suffix: str = "",
    statistics: Optional[list] = None,
) -> html.Div:
    """
    Create expanded parameter panel section with all input fields.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    When expanded, it displays ALL forecast-critical parameter input fields matching
    the functionality of the old Input Parameters card with improved UX using sliders.

    User Story 6: Contextual Help System - Adds help icons to parameter inputs.

    Args:
        settings: Dictionary containing current parameter values (pert_factor, deadline, etc.)
        id_suffix: Suffix for generating unique IDs
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        html.Div: Expanded parameter panel with complete input fields and help tooltips
    """
    panel_id = f"parameter-panel-expanded{'-' + id_suffix if id_suffix else ''}"

    # Extract settings with defaults
    pert_factor = settings.get("pert_factor", 3)
    # Date pickers use date=None and clearable=True (matching budget effective date)
    total_items = settings.get("total_items", 0)
    estimated_items = settings.get("estimated_items", 0)
    total_points = settings.get("total_points", 0)
    estimated_points = settings.get("estimated_points", 0)
    show_points = settings.get("show_points", False)
    data_points_count = settings.get("data_points_count", 10)

    # Calculate max data points from statistics if available
    # CRITICAL FIX: Count unique dates, not total rows (avoids duplicate date inflation)
    max_data_points = 52  # Default max
    if statistics and len(statistics) > 0:
        # Count unique dates to get actual week count
        unique_dates = set(
            stat.get("date") or stat.get("stat_date") for stat in statistics
        )
        max_data_points = len(unique_dates) if unique_dates else len(statistics)

    # Enforce minimum to prevent slider errors with new queries
    max_data_points = max(4, max_data_points)

    # Calculate dynamic marks for Data Points slider
    # 5 points: min (4), 1/4, 1/2 (middle), 3/4, max
    min_data_points = 4
    range_size = max_data_points - min_data_points
    quarter_point = math.ceil(min_data_points + range_size / 4)
    middle_point = math.ceil(min_data_points + range_size / 2)
    three_quarter_point = math.ceil(min_data_points + 3 * range_size / 4)

    data_points_marks: dict[int, dict[str, str]] = {
        min_data_points: {"label": str(min_data_points)},
        quarter_point: {"label": str(quarter_point)},
        middle_point: {"label": str(middle_point)},
        three_quarter_point: {"label": str(three_quarter_point)},
        max_data_points: {"label": str(max_data_points)},
    }

    return html.Div(
        [
            html.Div(
                [
                    # Tabbed interface matching Settings panel
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="Parameters",
                                tab_id="parameters-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        [
                                            # No header - tab label serves as title
                                            # Section 1: Project Timeline
                                            html.Div(
                                                _create_timeline_section(
                                                    pert_factor,
                                                    data_points_count,
                                                    data_points_marks,
                                                    max_data_points,
                                                ),
                                                className="mb-4 pb-3 border-bottom",
                                            ),
                                            # Section 2: Work Scope
                                            html.Div(
                                                _create_work_scope_section(
                                                    total_items,
                                                    estimated_items,
                                                    total_points,
                                                    estimated_points,
                                                    show_points,
                                                ),
                                            ),
                                        ],
                                        className="settings-tab-content",
                                    )
                                ],
                            ),
                            # Budget Tab
                            dbc.Tab(
                                label="Budget",
                                tab_id="budget-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        [create_budget_settings_card()],
                                        className="settings-tab-content",
                                    )
                                ],
                            ),
                        ],
                        id="parameter-tabs",
                        active_tab="parameters-tab",
                        className="settings-tabs",
                    ),
                ],
                className="tabbed-settings-panel blue-accent-panel",
            ),
        ],
        id=panel_id,
        className="parameter-panel-container",
    )


def _create_timeline_section(
    pert_factor: int,
    data_points_count: int,
    data_points_marks: dict,
    max_data_points: int,
) -> list:
    """Create Project Timeline section with date pickers and sliders."""
    return [
        html.H6(
            [
                html.I(
                    className="fas fa-calendar-alt me-2",
                    style={"color": "#0d6efd"},
                ),
                "Project Timeline",
            ],
            className="mb-3 text-primary",
            style={"fontSize": "0.9rem", "fontWeight": "600"},
        ),
        dbc.Row(
            [
                # Deadline Date Picker
                dbc.Col(
                    _create_date_picker_field(
                        "Deadline",
                        "deadline-picker",
                        "deadline",
                        "Leave empty for open-ended timeline",
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
                # Milestone Date Picker
                dbc.Col(
                    _create_date_picker_field(
                        "Milestone (optional)",
                        "milestone-picker",
                        "milestone",
                        "Optional intermediate target date",
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
                # Forecast Range Slider
                dbc.Col(
                    _create_forecast_range_slider(pert_factor),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
                # Data Points Slider
                dbc.Col(
                    _create_data_points_slider(
                        data_points_count, data_points_marks, max_data_points
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
            ],
            className="g-3",
        ),
    ]


def _create_date_picker_field(
    label: str, picker_id: str, help_topic: str, help_text: str
) -> list:
    """Create a date picker field with label and help tooltip."""
    return [
        html.Label(
            [
                label,
                html.Span(
                    create_parameter_tooltip(help_topic, f"{help_topic}-help"),
                    style={"marginLeft": "0.25rem"},
                ),
            ],
            className="form-label fw-medium",
            style={"fontSize": "0.875rem"},
        ),
        dcc.DatePickerSingle(
            id=picker_id,
            date=None,
            display_format="YYYY-MM-DD",
            placeholder="Optional",
            clearable=True,
            first_day_of_week=1,
            min_date_allowed=datetime.now().strftime("%Y-%m-%d"),
            className="w-100",
            style={"fontSize": "0.875rem"},
        ),
        html.Small(
            help_text,
            className="text-muted d-block mt-1",
            style={"fontSize": "0.75rem"},
        ),
        html.Div(
            id=f"{picker_id.replace('-picker', '')}-feedback",
            className="invalid-feedback",
        ),
    ]


def _create_forecast_range_slider(pert_factor: int) -> list:
    """Create Forecast Range slider with color-coded marks."""
    return [
        html.Label(
            [
                "Forecast Range",
                html.Span(
                    create_parameter_tooltip("pert_factor", "pert-factor-help"),
                    style={"marginLeft": "0.25rem"},
                ),
            ],
            className="form-label fw-medium",
            style={"fontSize": "0.875rem"},
        ),
        dcc.Slider(
            id="pert-factor-slider",
            min=3,
            max=12,
            value=pert_factor,
            marks={
                3: {"label": "3", "style": {"color": "#ff6b6b"}},
                4: {"label": "4"},
                5: {"label": "5"},
                6: {"label": "6 (rec)", "style": {"color": "#51cf66"}},
                7: {"label": "7"},
                8: {"label": "8"},
                9: {"label": "9"},
                10: {"label": "10"},
                11: {"label": "11"},
                12: {"label": "12", "style": {"color": "#339af0"}},
            },
            step=1,
            tooltip={"placement": "bottom", "always_visible": False},
            className="mt-2",
        ),
    ]


def _create_data_points_slider(
    data_points_count: int,
    data_points_marks: dict,
    max_data_points: int,
) -> list:
    """Create Data Points slider with dynamic marks."""
    return [
        html.Label(
            [
                "Data Points",
                html.Span(
                    create_parameter_tooltip("data_points", "data-points-help"),
                    style={"marginLeft": "0.25rem"},
                ),
            ],
            className="form-label fw-medium",
            style={"fontSize": "0.875rem"},
        ),
        dcc.Slider(
            id="data-points-input",
            min=4,
            max=max_data_points,
            value=data_points_count,
            marks=data_points_marks,  # type: ignore[arg-type]
            step=1,
            tooltip={"placement": "bottom", "always_visible": False},
            className="mt-2",
        ),
    ]


def _create_work_scope_section(
    total_items: int,
    estimated_items: int,
    total_points: float,
    estimated_points: float,
    show_points: bool,
) -> list:
    """Create Work Scope section with items/points inputs."""
    return [
        # Section header with Points Tracking toggle
        html.Div(
            [
                html.H6(
                    [
                        html.I(
                            className="fas fa-tasks me-2",
                            style={"color": "#20c997"},
                        ),
                        "Remaining Work Scope",
                    ],
                    className="mb-0 text-success",
                    style={"fontSize": "0.9rem", "fontWeight": "600"},
                ),
                dcc.Checklist(
                    id="points-toggle",
                    options=[{"label": "Points Tracking", "value": "show"}],
                    value=["show"] if show_points else [],
                    className="m-0",
                    labelStyle={
                        "display": "flex",
                        "alignItems": "center",
                        "fontSize": "0.8rem",
                        "color": "#6c757d",
                        "margin": "0",
                    },
                    inputStyle={"marginRight": "8px", "marginTop": "0"},
                    style={"fontSize": "0.8rem"},
                ),
            ],
            className="d-flex justify-content-between align-items-center mb-3",
        ),
        # Single Row: All 4 fields with equal width
        dbc.Row(
            [
                dbc.Col(
                    _create_work_scope_field(
                        "Estimated Items",
                        "estimated-items-input",
                        estimated_items,
                        "estimated_items",
                        "number",
                        "Items with estimates (0 if none). ",
                        False,
                        "0 if unknown",
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
                dbc.Col(
                    _create_work_scope_field(
                        "Remaining Items",
                        "total-items-input",
                        total_items,
                        "remaining_items",
                        "number",
                        "All open issues. ",
                        False,
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                ),
                dbc.Col(
                    _create_work_scope_field(
                        "Estimated Points",
                        "estimated-points-input",
                        estimated_points,
                        "estimated_points",
                        "number",
                        "Story points sum (0 if none). ",
                        not show_points,
                        "0 if unknown",
                    ),
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                    id="estimated-points-col",
                ),
                dbc.Col(
                    [
                        html.Label(
                            [
                                "Remaining Points",
                                html.Span(
                                    " (auto-calculated)", className="text-muted small"
                                ),
                                html.Span(
                                    create_parameter_tooltip(
                                        "remaining_points", "remaining-points-help"
                                    ),
                                    style={"marginLeft": "0.25rem"},
                                ),
                            ],
                            className="form-label fw-medium",
                            style={"fontSize": "0.875rem"},
                        ),
                        dbc.Input(
                            id="total-points-display",
                            type="text",
                            value=f"{total_points:.1f}",
                            disabled=True,
                            className="form-control-sm",
                            style={"backgroundColor": "#e9ecef"},
                        ),
                        html.Small(
                            [
                                html.Span(
                                    id="remaining-points-formula",
                                    children="= Est. Points + (avg × unestimated).",
                                ),
                                " ",
                                html.Span(
                                    "JIRA overwrites.",
                                    style={"color": "#856404", "fontStyle": "italic"},
                                ),
                            ],
                            className="text-muted d-block mt-1",
                            style={"fontSize": "0.75rem"},
                        ),
                    ],
                    xs=12,
                    md=6,
                    lg=3,
                    className="mb-3",
                    id="total-points-col",
                ),
            ],
            className="g-3",
        ),
    ]


def _create_work_scope_field(
    label: str,
    input_id: str,
    value: int | float,
    help_topic: str,
    input_type: str,
    help_text: str,
    disabled: bool = False,
    placeholder: str = "",
) -> list:
    """Create a work scope input field with label and help tooltip."""
    label_suffix = (
        " (optional)" if "estimated" in label.lower() else " (currently open)"
    )

    return [
        html.Label(
            [
                label,
                html.Span(label_suffix, className="text-muted small"),
                html.Span(
                    create_parameter_tooltip(help_topic, f"{help_topic}-help"),
                    style={"marginLeft": "0.25rem"},
                ),
            ],
            className="form-label fw-medium",
            style={"fontSize": "0.875rem"},
        ),
        dbc.Input(
            id=input_id,
            type=cast(str, input_type),  # type: ignore[arg-type]
            value=value,
            min=0,
            step=0.5 if "points" in input_id else 1,
            placeholder=placeholder,
            disabled=disabled,
            className="form-control-sm",
        ),
        html.Small(
            [
                help_text,
                html.Span(
                    "JIRA overwrites.",
                    style={"color": "#856404", "fontStyle": "italic"},
                ),
            ],
            className="text-muted d-block mt-1",
            style={"fontSize": "0.75rem"},
        ),
        html.Div(
            id=f"{input_id.replace('-input', '')}-feedback",
            className="invalid-feedback",
        )
        if "total-items" in input_id
        else html.Span(),
    ]
