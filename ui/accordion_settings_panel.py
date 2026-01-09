"""
Accordion-based Settings Panel with Progressive Disclosure

New settings panel implementation for Feature 011: Profile-First Dependency Architecture.
Uses 5-section accordion with dependency indicators showing which sections are enabled.

Sections:
1. Profile Settings (ALWAYS ENABLED)
2. JIRA Configuration (ENABLED WHEN PROFILE EXISTS)
3. Field Mappings (ENABLED WHEN JIRA CONNECTED)
4. Query Management (ENABLED WHEN JIRA CONFIGURED)
5. Data Operations (ENABLED WHEN QUERY SAVED)
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.profile_settings_card import create_profile_settings_card
from ui.jira_config_modal import create_jira_config_button
from ui.query_selector import create_query_selector_panel
from ui.jql_editor import create_jql_editor


def create_jira_config_card() -> html.Div:
    """
    Create JIRA configuration card.

    Contains:
    - JIRA status indicator
    - Configure JIRA button (opens modal)
    - Test connection status

    Returns:
        html.Div: JIRA configuration content
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-plug me-2 text-primary"),
                    html.Span("JIRA Connection", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Status indicator
            html.Div(
                id="jira-config-status-indicator",
                className="mb-3",
                children=[
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2"),
                            "JIRA not configured. Click Configure to get started.",
                        ],
                        color="info",
                    )
                ],
            ),
            # Configure button
            create_jira_config_button(compact=False),
            html.Div(
                id="jira-connection-test-status",
                style={"minHeight": "0px", "marginTop": "4px"},
            ),
            # Hidden div for legacy callback compatibility
            html.Div(id="jira-cache-status", style={"display": "none"}),
        ]
    )


def create_field_mapping_card() -> html.Div:
    """
    Create field mappings configuration card.

    Contains:
    - Field mapping status
    - Configure mappings button (opens modal)

    Returns:
        html.Div: Field mapping configuration content
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-project-diagram me-2 text-primary"),
                    html.Span("Field Mappings", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            html.P(
                "Configure JIRA custom field mappings for DORA metrics, Flow metrics, "
                "and project classification.",
                className="text-muted small",
            ),
            dbc.Button(
                [html.I(className="fas fa-cog me-2"), "Configure Mappings"],
                id="open-field-mapping-modal",
                color="info",
                size="md",
            ),
            html.Div(
                id="field-mapping-section-status",
                style={"minHeight": "0px", "marginTop": "4px"},
            ),
        ]
    )


def create_query_management_card() -> html.Div:
    """
    Create query management card with integrated JQL editor.

    Contains:
    - Query selector (create, switch, delete queries)
    - Integrated JQL editor
    - Save query button
    - Query metadata display

    Returns:
        html.Div: Query management content
    """
    return html.Div(
        [
            # Query selector
            create_query_selector_panel(),
            html.Hr(),
            # Integrated JQL editor
            html.Div(
                [
                    html.Label("JQL Query", className="form-label fw-bold"),
                    html.P(
                        "Enter JIRA Query Language (JQL) to filter issues",
                        className="text-muted small",
                    ),
                    create_jql_editor(
                        editor_id="query-jql-editor",
                        initial_value="project = EXAMPLE AND created >= -12w ORDER BY created DESC",
                        placeholder="project = EXAMPLE AND created >= -12w",
                        rows=4,
                    ),
                    # Performance tip about DevOps projects
                    html.Div(
                        [
                            html.I(className="fas fa-info-circle text-info me-2"),
                            html.Span(
                                "Tip: Query development projects only. "
                                "Configure DevOps projects in Field Mappings for optimized fetching.",
                                className="small text-muted",
                            ),
                        ],
                        className="alert alert-info border-info mt-2 py-2 px-3",
                        style={"fontSize": "0.8rem"},
                    ),
                    html.Div(id="jql-validation-feedback", className="mt-2"),
                ],
                className="mb-3",
            ),
            # Action buttons
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Query"],
                        id="save-query-btn",
                        color="success",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Cancel"],
                        id="cancel-query-edit-btn",
                        color="secondary",
                        outline=True,
                    ),
                ],
                className="mt-3",
            ),
            html.Div(
                id="query-save-status",
                style={"minHeight": "0px", "marginTop": "4px"},
            ),
        ]
    )


def create_data_operations_card() -> html.Div:
    """
    Create data operations card.

    Contains:
    - Update JIRA data button (requires saved query)
    - Import/Export panel
    - Data status indicators

    Returns:
        html.Div: Data operations content
    """
    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-database me-2 text-primary"),
                    html.Span("Data Operations", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Update data button
            html.Div(
                [
                    # Alert for query save requirement (managed by callback)
                    dbc.Alert(
                        id="data-operations-alert",
                        is_open=False,
                        dismissable=True,
                        className="mb-3",
                    ),
                    dbc.Button(
                        [
                            html.I(
                                className="fas fa-sync-alt",
                                style={"marginRight": "0.5rem"},
                            ),
                            "Update Data",
                        ],
                        id="update-data-unified",
                        color="primary",
                        size="lg",
                        disabled=True,  # Enabled by callback when query saved
                        className="mb-3 long-press-button",
                    ),
                    # Hidden store for force refresh functionality (long-press)
                    dcc.Store(id="force-refresh-store", data=False),
                    # Progress bar (hidden when not in use, fixed height to prevent layout shift)
                    html.Div(
                        id="update-data-progress-container",
                        className="mb-2",
                        style={"display": "none", "minHeight": "60px"},
                        children=[
                            html.Div(
                                id="progress-label",
                                className="small text-muted mb-1",
                                children="Processing: 0%",
                            ),
                            dbc.Progress(
                                id="progress-bar",
                                value=0,
                                striped=True,
                                animated=True,
                                color="primary",
                                style={"height": "24px"},
                            ),
                        ],
                    ),
                    # Interval for polling progress
                    dcc.Interval(
                        id="progress-poll-interval",
                        interval=250,  # Poll every 250ms (smoother updates, faster phase detection)
                        disabled=True,  # Disabled by default
                    ),
                    # Status message (hidden - progress bar shows status now)
                    html.Div(
                        html.Div(id="update-data-status"),
                        style={
                            "display": "none"
                        },  # Hidden - progress bar handles all status
                    ),
                    html.Div(
                        [
                            html.Small(
                                [
                                    html.I(className="fas fa-info-circle me-1"),
                                    "Use the ",
                                    html.Strong("Data"),
                                    " button in the top bar to import/export project data.",
                                ],
                                className="text-muted",
                            )
                        ],
                        className="mt-3 p-2 bg-light rounded",
                    ),
                ]
            ),
        ]
    )


def create_accordion_settings_panel() -> html.Div:
    """
    Create accordion-based settings panel with progressive disclosure.

    This is the new implementation for Feature 011. Uses 5-section accordion
    where sections progressively unlock as dependencies are satisfied.

    Returns:
        html.Div: Complete accordion settings panel
    """
    return html.Div(
        [
            # Configuration status store (updated by callback to track dependencies)
            dcc.Store(id="configuration-status-store", data={}),
            # 5-section accordion
            dbc.Accordion(
                [
                    # Section 1: Profile Settings (ALWAYS ENABLED)
                    dbc.AccordionItem(
                        [create_profile_settings_card()],
                        title="1. Profile Settings",
                        id="profile-section-accordion",
                        item_id="profile-section",
                    ),
                    # Section 2: JIRA Configuration (ENABLED WHEN PROFILE EXISTS)
                    dbc.AccordionItem(
                        [
                            html.Div(
                                id="jira-config-section-content",
                                children=[create_jira_config_card()],
                            )
                        ],
                        title="2. JIRA Configuration",
                        id="jira-section-accordion",
                        item_id="jira-section",
                    ),
                    # Section 3: Field Mappings (ENABLED WHEN JIRA CONNECTED)
                    dbc.AccordionItem(
                        [
                            html.Div(
                                id="field-mapping-section-content",
                                children=[create_field_mapping_card()],
                            )
                        ],
                        title="3. Field Mappings",
                        id="field-mapping-section-accordion",
                        item_id="field-mapping-section",
                    ),
                    # Section 4: Query Management (ENABLED WHEN JIRA CONFIGURED)
                    dbc.AccordionItem(
                        [
                            html.Div(
                                id="query-management-section-content",
                                children=[create_query_management_card()],
                            )
                        ],
                        title="4. Query Management",
                        id="query-section-accordion",
                        item_id="query-section",
                    ),
                    # Section 5: Data Operations (ENABLED WHEN QUERY SAVED)
                    dbc.AccordionItem(
                        [
                            html.Div(
                                id="data-actions-section-content",
                                children=[create_data_operations_card()],
                            )
                        ],
                        title="5. Data Operations",
                        id="data-actions-section-accordion",
                        item_id="data-actions-section",
                    ),
                ],
                id="settings-accordion",
                always_open=False,  # Only one section open at a time
                start_collapsed=False,  # Start with first section open
                active_item="profile-section",  # Profile section open by default
            ),
            # Status indicators (updated by callback)
            html.Div(id="dependency-status-display", className="mt-3"),
            # Hidden components for backward compatibility with legacy callbacks
            # NOTE: import-export-collapse is now in import_export_panel.py (real flyout)
            # Hidden textarea for legacy jira-jql-query references in settings.py
            dcc.Textarea(id="jira-jql-query", value="", style={"display": "none"}),
        ],
        className="accordion-settings-panel",
    )
