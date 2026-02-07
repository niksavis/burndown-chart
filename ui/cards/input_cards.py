"""
Input Card Components

This module provides card components for data import and configuration.
These cards handle user input for data sources, JIRA configuration,
and query management.

Input Cards:
- create_input_parameters_card: Data import configuration form
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html

from configuration import COLOR_PALETTE
from ui.button_utils import create_button
from ui.cards.settings_helpers import (
    _get_default_data_source,
    _get_default_jql_profile_id,
    _get_default_jql_query,
    _get_query_profile_options,
)
from ui.jira_config_modal import create_jira_config_button
from ui.jql_components import (
    create_character_count_display,
    should_show_character_warning,
)
from ui.jql_editor import create_jql_editor
from ui.styles import create_metric_card_header, create_standardized_card
from ui.tooltip_utils import create_info_tooltip


def create_input_parameters_card(
    current_settings: dict[str, Any],
    avg_points_per_item: float,
    estimated_total_points: float,
) -> dbc.Card:
    """
    Create the data import configuration card.

    Note: Project Timeline and Remaining Work Scope parameters have been moved to the
    Parameter Panel (collapsible top section) for better UX.

    Args:
        current_settings: Dictionary with current application settings
        avg_points_per_item: Current average points per item (unused but kept for compatibility)
        estimated_total_points: Estimated total points (unused but kept for compatibility)

    Returns:
        Dash Card component for data import configuration
    """
    # Create the card header
    header_content = create_metric_card_header(
        title="Data Import Configuration",
        tooltip_text="Configure data sources and import settings for your project.",
        tooltip_id="data-import-config",
    )

    # Create the card body content - only Data Import Configuration
    body_content = [
        # Data Source Selection
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-database me-2",
                            style={"color": COLOR_PALETTE["optimistic"]},
                        ),
                        "Data Source",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    [
                                        "Data Source:",
                                        create_info_tooltip(
                                            "data-source",
                                            "Choose between JIRA API (recommended) or JSON/CSV file upload.",
                                        ),
                                    ],
                                    className="fw-medium mb-2",
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
                            width=12,
                        ),
                    ],
                ),
                # Data Export Action
                html.Hr(className="my-3"),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.Label(
                                    "Export Options:", className="fw-medium mb-2"
                                ),
                                html.Div(
                                    [
                                        create_button(
                                            text="Export Data",
                                            id="export-project-data-button",
                                            variant="secondary",
                                            icon_class="fas fa-file-export",
                                        ),
                                        html.Small(
                                            "Export complete project data as JSON",
                                            className="text-muted mt-1 d-block",
                                        ),
                                        html.Div(
                                            dcc.Download(
                                                id="export-project-data-download"
                                            )
                                        ),
                                    ]
                                ),
                            ],
                            width=12,
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
        # Data Import Configuration
        html.Div(
            [
                html.H5(
                    [
                        html.I(
                            className="fas fa-upload me-2",
                            style={"color": COLOR_PALETTE["items"]},
                        ),
                        "Data Import Configuration",
                    ],
                    className="mb-3 border-bottom pb-2 d-flex align-items-center",
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
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Label(
                                            "Upload CSV/JSON File:",
                                            className="fw-medium",
                                        ),
                                        dcc.Upload(
                                            id="upload-data",
                                            children=html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-cloud-upload-alt fa-2x mb-2"
                                                    ),
                                                    html.Br(),
                                                    "Drag and Drop or Click to Select",
                                                ],
                                                className="d-flex flex-column justify-content-center align-items-center h-100",
                                                style={"lineHeight": "1.2"},
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
                                                "transition": "all 0.2s ease",
                                            },
                                            multiple=False,
                                        ),
                                    ],
                                    width=12,
                                    className="mb-3",
                                ),
                            ],
                        ),
                    ],
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
                        # Configure JIRA Button
                        create_jira_config_button(),
                        # JIRA Configuration Status Indicator
                        html.Div(
                            id="jira-config-status-indicator",
                            className="mt-2 mb-3",
                            children=[],
                        ),
                        # JQL Query Management Section
                        html.Div(
                            [
                                html.H6(
                                    [
                                        html.I(className="fas fa-code me-2"),
                                        "JQL Query Management",
                                    ],
                                    className="mb-3 text-primary border-bottom pb-2",
                                ),
                                # JQL Query Input
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Label(
                                                    "JQL Query:", className="fw-medium"
                                                ),
                                                create_jql_editor(
                                                    editor_id="jira-jql-query",
                                                    initial_value=_get_default_jql_query(),
                                                    placeholder="project = MYPROJECT AND created >= startOfYear()",
                                                    rows=1,
                                                ),
                                                html.Div(
                                                    id="jira-jql-character-count-container",
                                                    children=[
                                                        create_character_count_display(
                                                            count=len(
                                                                _get_default_jql_query()
                                                                or ""
                                                            ),
                                                            warning=should_show_character_warning(
                                                                _get_default_jql_query()
                                                            ),
                                                        )
                                                    ],
                                                    className="mb-2",
                                                ),
                                                html.Small(
                                                    "Write your JQL query here, then use the buttons below to save or manage it.",
                                                    className="text-muted",
                                                ),
                                            ],
                                            width=12,
                                            className="mb-3",
                                        ),
                                    ],
                                ),
                                # Query Actions
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
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
                                                        html.Div(
                                                            [
                                                                dcc.Dropdown(
                                                                    id="jql-profile-selector",
                                                                    options=_get_query_profile_options(),  # type: ignore[arg-type]
                                                                    value=_get_default_jql_profile_id(),
                                                                    placeholder="Select saved query",
                                                                    clearable=True,
                                                                    searchable=True,
                                                                    style={
                                                                        "minWidth": "200px",
                                                                        "maxWidth": "300px",
                                                                    },
                                                                ),
                                                            ],
                                                            className="d-inline-block me-2 mb-2",
                                                        ),
                                                        create_button(
                                                            text="Clear",
                                                            id="clear-jql-query-button",
                                                            variant="outline-secondary",
                                                            icon_class="fas fa-eraser",
                                                            size="sm",
                                                            className="me-2 mb-2",
                                                        ),
                                                    ],
                                                    className="d-flex flex-wrap justify-content-start",
                                                ),
                                            ],
                                            width=12,
                                            className="mb-3",
                                        ),
                                    ],
                                ),
                                # Feedback section
                                html.Div(
                                    id="jira-jql-query-save-status",
                                    className="text-center mt-2",
                                    children=[],
                                ),
                            ],
                            className="p-3 bg-light rounded mb-3",
                        ),
                        # Action Buttons
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                create_button(
                                                    text="Update Data",
                                                    id="update-data-unified",
                                                    variant="primary",
                                                    icon_class="fas fa-sync-alt",
                                                    className="mb-2",
                                                ),
                                                html.Small(
                                                    "Fetches JIRA data and automatically calculates project scope",
                                                    className="text-muted d-block",
                                                ),
                                            ]
                                        ),
                                    ],
                                    width=12,
                                    className="text-center mb-3",
                                ),
                            ],
                        ),
                        # Status indicator
                        html.Div(
                            id="jira-cache-status",
                            className="text-center text-muted small",
                            children="Ready to fetch JIRA data",
                        ),
                    ],
                ),
            ],
            className="mb-4 p-3 bg-light rounded-3",
        ),
    ]

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100 shadow-sm",
        body_className="p-3",
        shadow="sm",
    )
