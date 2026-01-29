"""
Parameter Panel Components Module

This module contains parameter panel UI components for User Story 1:
Quick Parameter Adjustments While Viewing Charts. It provides both
collapsed (compact) and expanded (detailed) views of project parameters.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from typing import Optional

import dash_bootstrap_components as dbc

# Third-party library imports
from dash import dcc, html

# Application imports
from ui.budget_settings_card import create_budget_settings_card


#######################################################################
# PARAMETER PANEL COMPONENTS (User Story 1)
#######################################################################


def create_parameter_bar_collapsed(
    pert_factor: float,
    deadline: str,
    scope_items: int,
    scope_points: int,
    id_suffix: str = "",
    remaining_items: int | None = None,
    remaining_points: int | None = None,
    total_items: int | None = None,
    total_points: int | None = None,
    show_points: bool = True,
    data_points: int | None = None,
    profile_name: str | None = None,
    query_name: str | None = None,
) -> html.Div:
    """
    Create collapsed parameter bar showing key values and expand button.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    When collapsed, it displays a compact summary of current parameter values with an
    expand button to show the full parameter panel.

    Args:
        pert_factor: Current PERT factor value
        deadline: Current deadline date string
        scope_items: Total number of items in scope (fallback)
        scope_points: Total story points in scope (fallback)
        id_suffix: Suffix for generating unique IDs
        remaining_items: Number of items remaining currently (displayed in bar)
        remaining_points: Number of points remaining currently (displayed in bar)
        total_items: Total remaining items (used for display)
        total_points: Total remaining points (used for display)
        show_points: Whether to show points data
        data_points: Number of weeks of data used for forecasting
        profile_name: Name of active profile (if in profiles mode)
        query_name: Name of active query (if in profiles mode)

    Returns:
        html.Div: Collapsed parameter bar component

    Example:
        >>> create_parameter_bar_collapsed(1.5, "2025-12-31", 100, 500, remaining_items=50)
    """
    from ui.style_constants import DESIGN_TOKENS

    bar_id = f"parameter-bar-collapsed{'-' + id_suffix if id_suffix else ''}"
    expand_btn_id = f"btn-expand-parameters{'-' + id_suffix if id_suffix else ''}"

    # Display the total items/points (remaining scope) for Remaining label
    # Use remaining values only if total values not available (fallback to current scope)
    display_items = (
        total_items
        if total_items is not None and total_items > 0
        else (remaining_items if remaining_items is not None else scope_items)
    )
    display_points = (
        total_points
        if total_points is not None and total_points > 0
        else (remaining_points if remaining_points is not None else scope_points)
    )

    # Determine label based on what we're showing
    items_label = (
        "Remaining" if (total_items is not None and total_items > 0) else "Scope"
    )

    # Create points display only if enabled
    points_display = []
    if show_points:
        # Round points to 1 decimal for display
        display_points_rounded = round(display_points, 1)
        points_display = [
            html.Span(
                [
                    html.I(className="fas fa-chart-bar me-1"),
                    html.Span(
                        f"{items_label}: ",
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                    html.Span(
                        f"{display_points_rounded:.1f}", style={"fontSize": "0.85em"}
                    ),
                ],
                className="param-summary-item",
                title=f"{items_label}: {display_points_rounded:.1f} points",
            ),
        ]

    # Detect initial icon state from task_progress.json to avoid flash on page load
    profile_icon_class = "fas fa-folder me-1"
    query_icon_class = "fas fa-search me-1"

    try:
        from pathlib import Path
        import json

        progress_file = Path("task_progress.json")
        if progress_file.exists():
            with open(progress_file, "r", encoding="utf-8") as f:
                progress_data = json.load(f)

            status = progress_data.get("status", "idle")
            phase = progress_data.get("phase", "fetch")
            cancelled = progress_data.get("cancelled", False)

            # Apply same logic as banner_status_icons callback
            if status == "in_progress" and not cancelled:
                profile_icon_class = "fas fa-folder me-1 text-warning"
                if phase == "fetch":
                    query_icon_class = "fas fa-spinner fa-spin me-1 text-warning"
                elif phase == "calculate":
                    query_icon_class = "fas fa-calculator fa-pulse me-1 text-success"
                else:
                    query_icon_class = "fas fa-search fa-pulse me-1 text-warning"
    except Exception:
        # Silently fail - will use defaults and callback will update shortly
        pass

    # Build profile/query display section if in profiles mode
    profile_query_display = []
    if profile_name and query_name:
        profile_query_display = [
            html.Span(
                [
                    html.I(
                        id="profile-status-icon",
                        className=profile_icon_class,
                    ),
                    html.Span(
                        profile_name,
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                ],
                className="param-summary-item me-2",
                title=f"Profile: {profile_name}",
            ),
            html.Span(
                [
                    html.I(
                        id="query-status-icon",
                        className=query_icon_class,
                    ),
                    html.Span(
                        query_name,
                        className="text-muted d-none d-xl-inline",
                        style={"fontSize": "0.85em"},
                    ),
                ],
                className="param-summary-item me-3",
                title=f"Query: {query_name}",
            ),
        ]

    return html.Div(
        [
            # Single row with all items on the same level
            html.Div(
                [
                    # Summary items (left side)
                    html.Div(
                        profile_query_display
                        + [
                            html.Span(
                                [
                                    html.I(className="fas fa-sliders-h me-1"),
                                    html.Span(
                                        "Range: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{pert_factor}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Forecast Range: {pert_factor} weeks (samples best/worst case velocity from your history)",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-chart-line me-1"),
                                    html.Span(
                                        "Data: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{data_points}w", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Data Points: {data_points} weeks of historical data used for forecasting",
                                style={"display": "inline" if data_points else "none"},
                            )
                            if data_points
                            else html.Span(),
                            html.Span(
                                [
                                    html.I(className="fas fa-calendar me-1"),
                                    html.Span(
                                        "Deadline: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{deadline}", style={"fontSize": "0.85em"}
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"Project deadline: {deadline}",
                            ),
                            html.Span(
                                [
                                    html.I(className="fas fa-tasks me-1"),
                                    html.Span(
                                        f"{items_label}: ",
                                        className="text-muted d-none d-xl-inline",
                                        style={"fontSize": "0.85em"},
                                    ),
                                    html.Span(
                                        f"{display_items:,}",
                                        style={"fontSize": "0.85em"},
                                    ),
                                ],
                                className="param-summary-item me-1 me-sm-2",
                                title=f"{items_label}: {display_items:,} items",
                            ),
                        ]
                        + points_display,
                        className="d-flex align-items-center flex-wrap flex-grow-1",
                    ),
                    # Buttons (right side)
                    html.Div(
                        [
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-cog",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Settings",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="settings-button",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Expand Settings",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-sliders-h",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Parameters",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id=expand_btn_id,
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                    "flexShrink": "0",
                                },
                                title="Adjust project parameters",
                            ),
                            dbc.Button(
                                [
                                    html.I(
                                        className="fas fa-exchange-alt",
                                        style={"fontSize": "1rem"},
                                    ),
                                    html.Span(
                                        "Data",
                                        className="d-none d-xxl-inline",
                                        style={"marginLeft": "0.5rem"},
                                    ),
                                ],
                                id="toggle-import-export-panel",
                                color="primary",
                                outline=True,
                                size="sm",
                                className="me-1",
                                style={
                                    "minWidth": "38px",
                                    "height": "38px",
                                    "padding": "0 8px",
                                    "display": "flex",
                                    "alignItems": "center",
                                    "justifyContent": "center",
                                },
                                title="Expand Data",
                            ),
                        ],
                        className="d-flex justify-content-end align-items-center flex-nowrap flex-shrink-0",
                        style={"minWidth": "fit-content"},
                    ),
                ],
                className="d-flex align-items-center justify-content-between flex-wrap",
            ),
        ],
        className="parameter-bar-collapsed",
        id=bar_id,
        style={
            "padding": "6px 12px",  # Aligned with tabs row for visual consistency
            "backgroundColor": DESIGN_TOKENS["colors"]["gray-100"],
            "borderRadius": DESIGN_TOKENS["layout"]["borderRadius"]["md"],
            "marginBottom": "0",  # Compact: no margin
        },
    )


def create_settings_tab_content(
    settings: dict,
    id_suffix: str = "",
) -> html.Div:
    """
    Create settings tab content for data source configuration and import/export.

    This replaces the old Data Import Configuration card, now accessible from
    the Parameter Panel Settings tab.

    Args:
        settings: Dictionary containing current settings
        id_suffix: Suffix for generating unique IDs

    Returns:
        html.Div: Settings tab content with data source config and import/export
    """
    from ui.jql_editor import create_jql_editor
    from ui.jira_config_modal import create_jira_config_button
    from ui.button_utils import create_button
    from ui.jql_components import (
        create_character_count_display,
        should_show_character_warning,
    )

    # Import helper functions from cards module
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ui.cards import (
        _get_default_data_source,
        _get_default_jql_query,
        _get_default_jql_profile_id,
        _get_query_profile_options,
    )

    return html.Div(
        [
            # Data Source Selection
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-database me-2",
                                style={"color": "#20c997"},
                            ),
                            "Data Source",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dbc.RadioItems(
                        id="data-source-selection",
                        options=[
                            {"label": "JIRA API", "value": "JIRA"},
                            {"label": "JSON/CSV Import", "value": "CSV"},
                        ],
                        value=_get_default_data_source(),
                        inline=True,
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # CSV Upload Container
            html.Div(
                id="csv-upload-container",
                style={
                    "display": "none"
                    if _get_default_data_source() == "JIRA"
                    else "block"
                },
                children=[
                    html.H6(
                        [
                            html.I(
                                className="fas fa-upload me-2",
                                style={"color": "#0d6efd"},
                            ),
                            "File Upload",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            [
                                html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                                html.Br(),
                                "Drag and Drop or Click to Select",
                            ],
                            className="text-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "100px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "8px",
                            "borderColor": "#dee2e6",
                            "backgroundColor": "#f8f9fa",
                            "cursor": "pointer",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                        multiple=False,
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # JIRA Configuration Container
            html.Div(
                id="jira-config-container",
                style={
                    "display": "block"
                    if _get_default_data_source() == "JIRA"
                    else "none"
                },
                children=[
                    # JIRA Connection Button
                    html.H6(
                        [
                            html.I(
                                className="fas fa-plug me-2", style={"color": "#0d6efd"}
                            ),
                            "JIRA Connection",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_jira_config_button(),
                    html.Div(
                        id="jira-config-status-indicator",
                        className="mt-2 mb-3",
                        children=[],
                    ),
                    # JQL Query Management
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className="fas fa-code me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "JQL Query",
                                ],
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"},
                            ),
                            create_jql_editor(
                                editor_id="jira-jql-query",
                                initial_value=_get_default_jql_query(),
                                placeholder="project = MYPROJECT AND created >= startOfYear()",
                                rows=3,
                            ),
                            html.Div(
                                id="jira-jql-character-count-container",
                                children=[
                                    create_character_count_display(
                                        count=len(_get_default_jql_query() or ""),
                                        warning=should_show_character_warning(
                                            _get_default_jql_query()
                                        ),
                                    )
                                ],
                                className="mb-2",
                            ),
                            # Query Actions
                            html.Div(
                                [
                                    create_button(
                                        text="Save Query",
                                        id="save-jql-query-button",
                                        variant="primary",
                                        icon_class="fas fa-save",
                                        size="sm",
                                        className="me-2 mb-2",
                                    ),
                                    dcc.Dropdown(
                                        id="jql-profile-selector",
                                        options=_get_query_profile_options(),
                                        value=_get_default_jql_profile_id(),
                                        placeholder="Select saved query",
                                        clearable=True,
                                        searchable=True,
                                        style={
                                            "minWidth": "200px",
                                            "maxWidth": "300px",
                                            "display": "inline-block",
                                        },
                                        className="me-2 mb-2",
                                    ),
                                    create_button(
                                        text="Clear",
                                        id="clear-jql-query-button",
                                        variant="outline-secondary",
                                        icon_class="fas fa-eraser",
                                        size="sm",
                                        className="mb-2",
                                    ),
                                ],
                                className="d-flex flex-wrap align-items-center mb-2",
                            ),
                            html.Div(
                                id="jira-jql-query-save-status",
                                className="text-center mt-2 mb-3",
                                children=[],
                            ),
                            # Update Data Button
                            create_button(
                                text="Update Data",
                                id="update-data-unified",
                                variant="primary",
                                icon_class="fas fa-sync-alt",
                                className="w-100 mb-2",
                            ),
                            html.Div(
                                id="jira-cache-status",
                                className="text-center text-muted small",
                                children="Ready to fetch JIRA data",
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # Export Options
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-file-export me-2",
                                style={"color": "#6c757d"},
                            ),
                            "Export Data",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_button(
                        text="Export Project Data",
                        id="export-project-data-button",
                        variant="secondary",
                        icon_class="fas fa-file-export",
                        className="w-100 mb-2",
                    ),
                    html.Small(
                        "Export complete project data as JSON",
                        className="text-muted d-block text-center",
                    ),
                    html.Div(dcc.Download(id="export-project-data-download")),
                ],
            ),
        ],
        style={"padding": "1rem"},
    )


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

    Example:
        >>> settings = {"pert_factor": 3, "deadline": "2025-12-31", "show_milestone": True}
        >>> create_parameter_panel_expanded(settings)
    """
    from datetime import datetime
    from ui.help_system import create_parameter_tooltip

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
    import math

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
                                                [
                                                    html.H6(
                                                        [
                                                            html.I(
                                                                className="fas fa-calendar-alt me-2",
                                                                style={
                                                                    "color": "#0d6efd"
                                                                },
                                                            ),
                                                            "Project Timeline",
                                                        ],
                                                        className="mb-3 text-primary",
                                                        style={
                                                            "fontSize": "0.9rem",
                                                            "fontWeight": "600",
                                                        },
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            # Deadline Date Picker
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Deadline",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "deadline",
                                                                                    "deadline-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.DatePickerSingle(
                                                                        id="deadline-picker",
                                                                        date=None,
                                                                        display_format="YYYY-MM-DD",
                                                                        placeholder="Optional",
                                                                        clearable=True,
                                                                        first_day_of_week=1,
                                                                        min_date_allowed=datetime.now().strftime(
                                                                            "%Y-%m-%d"
                                                                        ),
                                                                        className="w-100",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    html.Small(
                                                                        "Leave empty for open-ended timeline",
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="deadline-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Milestone Date Picker (optional - activated when date is entered)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Milestone (optional)",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "milestone",
                                                                                    "milestone-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.DatePickerSingle(
                                                                        id="milestone-picker",
                                                                        date=None,
                                                                        display_format="YYYY-MM-DD",
                                                                        placeholder="Optional",
                                                                        clearable=True,
                                                                        first_day_of_week=1,
                                                                        min_date_allowed=datetime.now().strftime(
                                                                            "%Y-%m-%d"
                                                                        ),
                                                                        className="w-100",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    html.Small(
                                                                        "Optional intermediate target date",
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="milestone-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Forecast Range Slider (formerly PERT Factor)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Forecast Range",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "pert_factor",
                                                                                    "pert-factor-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.Slider(
                                                                        id="pert-factor-slider",
                                                                        min=3,
                                                                        max=12,
                                                                        value=pert_factor,
                                                                        marks={
                                                                            3: {
                                                                                "label": "3",
                                                                                "style": {
                                                                                    "color": "#ff6b6b"
                                                                                },
                                                                            },
                                                                            4: {
                                                                                "label": "4"
                                                                            },
                                                                            5: {
                                                                                "label": "5"
                                                                            },
                                                                            6: {
                                                                                "label": "6 (rec)",
                                                                                "style": {
                                                                                    "color": "#51cf66"
                                                                                },
                                                                            },
                                                                            7: {
                                                                                "label": "7"
                                                                            },
                                                                            8: {
                                                                                "label": "8"
                                                                            },
                                                                            9: {
                                                                                "label": "9"
                                                                            },
                                                                            10: {
                                                                                "label": "10"
                                                                            },
                                                                            11: {
                                                                                "label": "11"
                                                                            },
                                                                            12: {
                                                                                "label": "12",
                                                                                "style": {
                                                                                    "color": "#339af0"
                                                                                },
                                                                            },
                                                                        },
                                                                        step=1,
                                                                        tooltip={
                                                                            "placement": "bottom",
                                                                            "always_visible": False,
                                                                        },
                                                                        className="mt-2",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Data Points Slider
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Data Points",
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "data_points",
                                                                                    "data-points-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dcc.Slider(
                                                                        id="data-points-input",
                                                                        min=4,  # Fixed minimum of 4 weeks for meaningful trend analysis
                                                                        max=max_data_points,
                                                                        value=data_points_count,
                                                                        marks=data_points_marks,  # type: ignore[arg-type]
                                                                        step=1,
                                                                        tooltip={
                                                                            "placement": "bottom",
                                                                            "always_visible": False,
                                                                        },
                                                                        className="mt-2",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                        ],
                                                        className="g-3",
                                                    ),
                                                ],
                                                className="mb-4 pb-3 border-bottom",
                                            ),
                                            # Section 2: Work Scope
                                            html.Div(
                                                [
                                                    # Section header with inline Points Tracking toggle
                                                    html.Div(
                                                        [
                                                            html.H6(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-tasks me-2",
                                                                        style={
                                                                            "color": "#20c997"
                                                                        },
                                                                    ),
                                                                    "Remaining Work Scope",
                                                                ],
                                                                className="mb-0 text-success",
                                                                style={
                                                                    "fontSize": "0.9rem",
                                                                    "fontWeight": "600",
                                                                },
                                                            ),
                                                            dcc.Checklist(
                                                                id="points-toggle",
                                                                options=[
                                                                    {
                                                                        "label": "Points Tracking",
                                                                        "value": "show",
                                                                    }
                                                                ],
                                                                value=["show"]
                                                                if show_points
                                                                else [],
                                                                className="m-0",
                                                                labelStyle={
                                                                    "display": "flex",
                                                                    "alignItems": "center",
                                                                    "fontSize": "0.8rem",
                                                                    "color": "#6c757d",
                                                                    "margin": "0",
                                                                },
                                                                inputStyle={
                                                                    "marginRight": "8px",
                                                                    "marginTop": "0",
                                                                },
                                                                style={
                                                                    "fontSize": "0.8rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="d-flex justify-content-between align-items-center mb-3",
                                                    ),
                                                    # Single Row: All 4 fields with equal width
                                                    dbc.Row(
                                                        [
                                                            # Estimated Items
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Estimated Items",
                                                                            html.Span(
                                                                                " (optional)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "estimated_items",
                                                                                    "estimated-items-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="estimated-items-input",
                                                                        type="number",
                                                                        value=estimated_items,
                                                                        min=0,
                                                                        step=1,
                                                                        placeholder="0 if unknown",
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Small(
                                                                        [
                                                                            "Items with estimates (0 if none). ",
                                                                            html.Span(
                                                                                "JIRA overwrites.",
                                                                                style={
                                                                                    "color": "#856404",
                                                                                    "fontStyle": "italic",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Remaining Items
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Remaining Items",
                                                                            html.Span(
                                                                                " (currently open)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "remaining_items",
                                                                                    "remaining-items-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="total-items-input",
                                                                        type="number",
                                                                        value=total_items,
                                                                        min=0,
                                                                        step=1,
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Small(
                                                                        [
                                                                            "All open issues. ",
                                                                            html.Span(
                                                                                "JIRA overwrites.",
                                                                                style={
                                                                                    "color": "#856404",
                                                                                    "fontStyle": "italic",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                    html.Div(
                                                                        id="total-items-feedback",
                                                                        className="invalid-feedback",
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                            ),
                                                            # Estimated Points
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Estimated Points",
                                                                            html.Span(
                                                                                " (optional)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "estimated_points",
                                                                                    "estimated-points-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="estimated-points-input",
                                                                        type="number",
                                                                        value=estimated_points,
                                                                        min=0,
                                                                        step=0.5,
                                                                        placeholder="0 if unknown",
                                                                        disabled=not show_points,
                                                                        className="form-control-sm",
                                                                    ),
                                                                    html.Small(
                                                                        [
                                                                            "Story points sum (0 if none). ",
                                                                            html.Span(
                                                                                "JIRA overwrites.",
                                                                                style={
                                                                                    "color": "#856404",
                                                                                    "fontStyle": "italic",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                xs=12,
                                                                md=6,
                                                                lg=3,
                                                                className="mb-3",
                                                                id="estimated-points-col",
                                                            ),
                                                            # Remaining Points (auto-calculated)
                                                            dbc.Col(
                                                                [
                                                                    html.Label(
                                                                        [
                                                                            "Remaining Points",
                                                                            html.Span(
                                                                                " (auto-calculated)",
                                                                                className="text-muted small",
                                                                            ),
                                                                            html.Span(
                                                                                create_parameter_tooltip(
                                                                                    "remaining_points",
                                                                                    "remaining-points-help",
                                                                                ),
                                                                                style={
                                                                                    "marginLeft": "0.25rem"
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="form-label fw-medium",
                                                                        style={
                                                                            "fontSize": "0.875rem"
                                                                        },
                                                                    ),
                                                                    dbc.Input(
                                                                        id="total-points-display",
                                                                        type="text",
                                                                        value=f"{total_points:.1f}",
                                                                        disabled=True,
                                                                        className="form-control-sm",
                                                                        style={
                                                                            "backgroundColor": "#e9ecef"
                                                                        },
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
                                                                                style={
                                                                                    "color": "#856404",
                                                                                    "fontStyle": "italic",
                                                                                },
                                                                            ),
                                                                        ],
                                                                        className="text-muted d-block mt-1",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
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
                                                ],
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
        # All styling via CSS for consistency (DRY principle)
    )


def create_parameter_panel(
    settings: dict,
    is_open: bool = False,
    id_suffix: str = "",
    statistics: Optional[list] = None,
) -> html.Div:
    """
    Create complete collapsible parameter panel combining collapsed bar and expanded section.

    This component supports User Story 1: Quick Parameter Adjustments While Viewing Charts.
    It combines the collapsed bar (always visible) with the expanded panel (toggleable)
    using Bootstrap's Collapse component for smooth transitions.

    Args:
        settings: Dictionary containing current parameter values
        is_open: Whether panel should start in expanded state
        id_suffix: Suffix for generating unique IDs
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        html.Div: Complete parameter panel with collapse functionality

    Example:
        >>> settings = {"pert_factor": 1.5, "deadline": "2025-12-31"}
        >>> create_parameter_panel(settings, is_open=False)
    """
    panel_id = f"parameter-panel{'-' + id_suffix if id_suffix else ''}"
    collapse_id = f"parameter-collapse{'-' + id_suffix if id_suffix else ''}"

    # Extract key values for collapsed bar
    pert_factor = settings.get("pert_factor", 3)
    deadline = (
        settings.get("deadline", "2025-12-31") or "2025-12-31"
    )  # Ensure valid default for display
    total_items = settings.get("total_items", 0)
    total_points = settings.get("total_points", 0)
    data_points = settings.get("data_points_count")
    show_points = settings.get("show_points", True)

    # CRITICAL FIX: Pass total_items/total_points as BOTH scope AND remaining values
    # The serve_layout() calculates these as remaining work at START of window,
    # so we should display them as "Remaining" not "Scope"
    # This ensures the initial banner matches the callback-updated banner

    # Get active profile and query names for display
    from data.profile_manager import get_active_profile_and_query_display_names

    display_names = get_active_profile_and_query_display_names()
    profile_name = display_names.get("profile_name")
    query_name = display_names.get("query_name")

    return html.Div(
        [
            # Collapsed bar (always visible)
            create_parameter_bar_collapsed(
                pert_factor=pert_factor,
                deadline=deadline,
                scope_items=total_items,
                scope_points=total_points,
                remaining_items=total_items
                if total_items > 0
                else None,  # Display as Remaining
                remaining_points=total_points
                if total_points > 0
                else None,  # Display as Remaining
                total_items=total_items if total_items > 0 else None,  # Remaining Items
                total_points=total_points
                if total_points > 0
                else None,  # Remaining Points
                show_points=show_points,  # Respect Points Tracking toggle
                id_suffix=id_suffix,
                data_points=data_points,
                profile_name=profile_name,
                query_name=query_name,
            ),
            # Expanded panel (toggleable)
            dbc.Collapse(
                create_parameter_panel_expanded(
                    settings, id_suffix=id_suffix, statistics=statistics
                ),
                id=collapse_id,
                is_open=is_open,
            ),
        ],
        id=panel_id,
        className="parameter-panel-container",
    )


#######################################################################
# MOBILE PARAMETER BOTTOM SHEET (Phase 7: User Story 5 - T068)
#######################################################################


def create_mobile_parameter_fab() -> html.Div:
    """
    Create a floating action button (FAB) to trigger mobile parameter bottom sheet.

    This FAB appears only on mobile devices (<768px) and provides quick access
    to parameter adjustments via a bottom sheet interface optimized for touch.

    Returns:
        html.Div: FAB component with mobile-only visibility

    Example:
        >>> fab = create_mobile_parameter_fab()
    """
    from ui.style_constants import DESIGN_TOKENS

    return html.Div(
        [
            dbc.Button(
                html.I(className="fas fa-sliders-h", style={"fontSize": "1.25rem"}),
                id="mobile-param-fab",
                color="primary",
                className="mobile-param-fab",
                style={
                    "position": "fixed",
                    "bottom": "80px",  # Above mobile bottom nav
                    "right": DESIGN_TOKENS["mobile"]["fabPosition"],
                    "width": DESIGN_TOKENS["mobile"]["fabSize"],
                    "height": DESIGN_TOKENS["mobile"]["fabSize"],
                    "borderRadius": "50%",
                    "boxShadow": DESIGN_TOKENS["layout"]["shadow"]["lg"],
                    "zIndex": DESIGN_TOKENS["layout"]["zIndex"]["fixed"],
                    "display": "none",  # Hidden by default, shown via CSS media query
                },
                title="Adjust Parameters",
            ),
        ],
        className="d-md-none",  # Only visible on mobile
    )


def create_mobile_parameter_bottom_sheet(
    settings: dict, statistics: Optional[list] = None
) -> dbc.Offcanvas:
    """
    Create mobile-optimized parameter bottom sheet using dbc.Offcanvas.

    NOTE: This component is currently unused (FAB never added to layout).
    Timeline pickers (Deadline/Milestone) removed - desktop pickers use responsive
    dbc.Col (xs=12, md=6, lg=3) which already works on mobile, eliminating duplication.

    This component provides a touch-friendly alternative to the sticky parameter
    panel for mobile devices. It slides up from the bottom and contains
    parameter inputs in a mobile-optimized layout.

    Args:
        settings: Dictionary containing current parameter values
        statistics: Optional list of statistics data points for calculating max data points

    Returns:
        dbc.Offcanvas: Mobile parameter bottom sheet component

    Example:
        >>> settings = {"pert_factor": 3}
        >>> sheet = create_mobile_parameter_bottom_sheet(settings)
    """
    from ui.style_constants import DESIGN_TOKENS

    # Extract settings with defaults
    pert_factor = settings.get("pert_factor", 3)
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
    import math

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

    return dbc.Offcanvas(
        [
            # Header with close button
            html.Div(
                [
                    html.H5(
                        [
                            html.I(className="fas fa-sliders-h me-2"),
                            "Parameters",
                        ],
                        className="mb-0",
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-3 pb-3 border-bottom",
            ),
            # Scrollable content area
            html.Div(
                [
                    # NOTE: Timeline section (Deadline/Milestone) removed - desktop pickers
                    # use responsive dbc.Col (xs=12, md=6, lg=3) which already works on mobile.
                    # Mobile bottom sheet is unused (FAB never added to layout), so these
                    # duplicate pickers were dead code. Date inputs now unified in Parameters tab.
                    # Confidence Window Section (formerly PERT Factor)
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Forecast Settings",
                                ],
                                className="mb-3",
                            ),
                            # Confidence Window Slider
                            html.Div(
                                [
                                    html.Label(
                                        "Confidence Window",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-pert-factor-slider",
                                        min=3,
                                        max=12,
                                        value=pert_factor,
                                        marks={
                                            3: {"label": "3"},
                                            4: {"label": "4"},
                                            5: {"label": "5"},
                                            6: {"label": "6 (rec)"},
                                            7: {"label": "7"},
                                            8: {"label": "8"},
                                            9: {"label": "9"},
                                            10: {"label": "10"},
                                            11: {"label": "11"},
                                            12: {"label": "12"},
                                        },
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Data Points Slider
                            html.Div(
                                [
                                    html.Label(
                                        "Data Points (weeks)",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dcc.Slider(
                                        id="mobile-data-points-input",
                                        min=4,  # Fixed minimum of 4 weeks for meaningful trend analysis
                                        max=max_data_points,
                                        value=data_points_count,
                                        marks=data_points_marks,  # type: ignore[arg-type]
                                        step=1,
                                        tooltip={
                                            "placement": "top",
                                            "always_visible": False,
                                        },
                                        className="mb-2",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        className="mb-4 pb-3 border-bottom",
                    ),
                    # Scope Section
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(className="fas fa-tasks me-2"),
                                    "Work Scope",
                                ],
                                className="mb-3",
                            ),
                            # Remaining Items
                            html.Div(
                                [
                                    html.Label(
                                        "Remaining Items",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-total-items-input",
                                        type="number",
                                        value=total_items,
                                        min=0,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Estimated Items
                            html.Div(
                                [
                                    html.Label(
                                        "Estimated Items",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-estimated-items-input",
                                        type="number",
                                        value=estimated_items,
                                        min=0,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Points Toggle
                            html.Div(
                                [
                                    dbc.Checkbox(
                                        id="mobile-points-toggle",
                                        label="Enable Points Tracking",
                                        value=show_points,
                                        className="mb-3",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Remaining Points (if points enabled)
                            html.Div(
                                [
                                    html.Label(
                                        "Remaining Points",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-total-points-input",
                                        type="number",
                                        value=total_points,
                                        min=0,
                                        disabled=not show_points,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-total-points-container",
                            ),
                            # Estimated Points (if points enabled)
                            html.Div(
                                [
                                    html.Label(
                                        "Estimated Points",
                                        className="form-label fw-medium",
                                        style={"fontSize": "0.875rem"},
                                    ),
                                    dbc.Input(
                                        id="mobile-estimated-points-input",
                                        type="number",
                                        value=estimated_points,
                                        min=0,
                                        disabled=not show_points,
                                        className="mb-3",
                                        style={
                                            "minHeight": DESIGN_TOKENS["mobile"][
                                                "touchTargetMin"
                                            ]
                                        },
                                    ),
                                ],
                                className="mb-3",
                                style={"display": "block" if show_points else "none"},
                                id="mobile-estimated-points-container",
                            ),
                        ],
                        className="mb-4",
                    ),
                ],
                style={
                    "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
                    "overflowY": "auto",
                },
            ),
        ],
        id="mobile-parameter-sheet",
        is_open=False,
        placement="bottom",
        backdrop=True,
        scrollable=True,
        style={
            "maxHeight": DESIGN_TOKENS["mobile"]["bottomSheetMaxHeight"],
        },
        className="mobile-parameter-sheet",
    )
