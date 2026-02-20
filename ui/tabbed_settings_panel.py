"""
Tabbed Settings Panel - Redesigned for Better UX

Replaces accordion-based panel to fix dropdown clipping issues.
Uses vertical tabs for easy navigation without overflow problems.

Sections:
1. Profile Settings (ALWAYS ENABLED)
2. JIRA Configuration (ENABLED WHEN PROFILE EXISTS)
3. Field Mappings (ENABLED WHEN JIRA CONNECTED)
4. Query Management (ENABLED WHEN JIRA CONFIGURED)
5. Data Operations (ENABLED WHEN QUERY SAVED)
6. Budget Configuration (ENABLED WHEN PROFILE EXISTS)
"""

import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.button_utils import create_panel_collapse_button
from ui.jira_config_modal import create_jira_config_button
from ui.jql_editor import create_jql_editor
from ui.profile_settings_card import create_profile_settings_card


def create_connect_tab_content() -> html.Div:
    """
    Create unified Connect tab with JIRA connection and field mapping.

    Combines JIRA configuration and field mapping for streamlined setup.
    Uses side-by-side layout with identical styling and structure.

    Returns:
        html.Div: Connect tab content with both JIRA and Fields sections
    """
    return html.Div(
        [
            dbc.Row(
                [
                    # JIRA Connection Column
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(className="fas fa-plug me-2 text-primary"),
                                    html.Span("JIRA Connection", className="fw-bold"),
                                ],
                                className="d-flex align-items-center mb-2",
                            ),
                            html.Div(
                                id="jira-config-status-indicator",
                                className="mb-2",
                                children=[
                                    html.I(
                                        className="fas fa-exclamation-triangle text-warning me-2"
                                    ),
                                    html.Span(
                                        "Configure JIRA to begin",
                                        className="text-muted small",
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            # Configure button
                            create_jira_config_button(compact=False),
                            # Status divs with minimal space (hidden when empty)
                            html.Div(
                                id="jira-connection-test-status",
                                style={"minHeight": "0px", "marginTop": "4px"},
                            ),
                            html.Div(id="jira-cache-status", style={"display": "none"}),
                        ],
                        xs=12,
                        md=6,
                        className="pe-md-3 mb-3 mb-md-0",
                    ),
                    # Field Mapping Column
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="fas fa-project-diagram me-2 text-primary"
                                    ),
                                    html.Span("Field Mapping", className="fw-bold"),
                                ],
                                className="d-flex align-items-center mb-2",
                            ),
                            html.Div(
                                id="field-mapping-status-indicator",
                                className="mb-2",
                                children=[
                                    html.I(
                                        className="fas fa-exclamation-triangle text-warning me-2"
                                    ),
                                    html.Span(
                                        "Configure field mappings to enable metrics",
                                        className="text-muted small",
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-cog me-2"),
                                    "Configure Fields",
                                ],
                                id="open-field-mapping-modal",
                                color="primary",
                                size="md",
                                className="w-100",
                            ),
                        ],
                        xs=12,
                        md=6,
                        className="ps-md-3 mb-3",
                    ),
                ],
                className="gx-0",
            ),
        ],
        className="settings-tab-content",
    )


def create_queries_and_data_tab_content() -> html.Div:
    """
    Create unified Queries tab with query management and data operations.

    Combines query selector, JQL editor, and data fetch operations in a streamlined workflow:
    - Select/create query from dropdown
    - Edit query name and JQL
    - Save/Save As/Discard changes
    - Update data to activate query

    Returns:
        html.Div: Queries tab content with unified query workflow
    """
    return html.Div(
        [
            # Hidden store for tracking original query state (for unsaved changes detection)
            dcc.Store(
                id="query-original-state", data={"name": "", "jql": "", "id": ""}
            ),
            # Section header
            html.Div(
                [
                    html.I(className="fas fa-search me-2 text-primary"),
                    html.Span("Query Management", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            # Query selector row with Load Data and Delete Query buttons
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Query:", className="form-label fw-bold mb-1"),
                            dcc.Dropdown(
                                id="query-selector",
                                placeholder="Select a query or create new...",
                                clearable=False,
                                className="mb-1",
                            ),
                        ],
                        xs=12,
                        lg=6,
                        className="mb-2",
                    ),
                    dbc.Col(
                        dbc.ButtonGroup(
                            [
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-folder-open me-1"),
                                        "Load",
                                    ],
                                    id="load-query-data-btn",
                                    color="primary",
                                    outline=True,
                                    className="me-1",
                                    title="Load cached data for selected query",
                                ),
                                dbc.Button(
                                    [
                                        html.I(className="fas fa-trash-alt me-1"),
                                        "Delete",
                                    ],
                                    id="delete-query-btn",
                                    color="danger",
                                    outline=True,
                                    title="Delete query",
                                ),
                            ],
                            className="w-100",
                            style={
                                "marginTop": "1.71rem"
                            },  # Align with dropdown (label height + mb-1)
                        ),
                        xs=12,
                        lg=6,
                        className="mb-2",
                    ),
                ],
                className="g-2",
            ),
            # Query name input
            html.Div(
                [
                    html.Label("Query Name:", className="form-label fw-bold mb-1"),
                    dbc.Input(
                        id="query-name-input",
                        type="text",
                        placeholder="Auto-generated from JQL query...",
                        debounce=True,
                        className="mb-3",
                    ),
                ],
                className="mb-3",
            ),
            # JQL editor
            html.Div(
                [
                    html.Label("JQL Query", className="form-label fw-bold mb-1"),
                    html.P(
                        "Enter JIRA Query Language (JQL) to filter issues",
                        className="text-muted small mb-2",
                    ),
                    create_jql_editor(
                        editor_id="query-jql-editor",
                        initial_value="",
                        placeholder="project = EXAMPLE AND created >= -12w ORDER BY created DESC",
                        rows=4,
                    ),
                    html.Div(id="jql-validation-feedback", className="mt-2"),
                ],
                className="mb-3",
            ),
            # Action buttons - Save, Save As, Discard
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save"],
                        id="save-query-btn",
                        color="success",
                        disabled=True,  # Enabled when changes detected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Save As"],
                        id="save-as-query-btn",
                        color="primary",
                        outline=True,
                        disabled=True,  # Enabled when changes detected
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Discard"],
                        id="discard-query-changes-btn",
                        color="danger",
                        outline=True,
                        disabled=True,  # Enabled when changes detected
                    ),
                ],
                className="mb-3 w-100",
            ),
            html.Div(
                id="query-save-status",
                style={"minHeight": "0px", "marginBottom": "4px"},
            ),
            # Alert for query save requirement (shown when needed)
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    "Query must be saved before fetching data.",
                ],
                id="data-operations-alert",
                color="warning",
                is_open=False,
                dismissable=False,
                className="mb-3",
            ),
            # Button container - Update Data and Cancel buttons in same position
            html.Div(
                [
                    # Update Data button (activates query)
                    dbc.Button(
                        [
                            html.I(className="fas fa-sync-alt"),
                            html.Span("Update Data"),
                        ],
                        id="update-data-unified",
                        color="primary",
                        disabled=True,  # Enabled when query is saved
                        className="long-press-button action-button",
                        style={},  # Visible by default, controlled by progress_bar callback
                    ),
                    # Cancel button (shown during operation, replaces Update Data button)
                    dbc.Button(
                        [
                            html.I(className="fas fa-times-circle"),
                            html.Span("Cancel Operation"),
                        ],
                        id="cancel-operation-btn",
                        color="danger",
                        className="action-button",
                        style={
                            "display": "none",
                            "position": "absolute",
                            "top": 0,
                            "left": 0,
                            "right": 0,
                        },  # Overlays Update Data button
                    ),
                ],
                style={"position": "relative", "marginBottom": "1rem"},
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
                style={"display": "none"},  # Hidden - progress bar handles all status
            ),
        ],
        className="settings-tab-content",
    )


def create_tabbed_settings_panel() -> html.Div:
    """
    Create tabbed settings panel with consolidated tabs.

    This replaces the accordion to fix dropdown clipping issues.

    Tabs:
    1. Profile - User profile and workspace management
    2. Connect - JIRA connection and field mapping (combined)
    3. Queries - Query management and data operations (combined)
    4. Budget - Budget configuration and tracking

    Returns:
        html.Div: Complete tabbed settings panel with 4 consolidated tabs
    """
    return html.Div(
        [
            # Configuration status store
            dcc.Store(id="configuration-status-store", data={}),
            # Tabs row with collapse button
            html.Div(
                [
                    # Collapse button (positioned absolutely, so order doesn't matter)
                    create_panel_collapse_button("settings-collapse"),
                    # Tabs
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                label="Profile",
                                tab_id="profile-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        [create_profile_settings_card()],
                                        className="settings-tab-content",
                                    )
                                ],
                            ),
                            dbc.Tab(
                                label="Connect",
                                tab_id="connect-tab",
                                label_style={"width": "100%"},
                                children=[
                                    # Combined JIRA + Fields content
                                    html.Div(
                                        id="jira-config-section-content",
                                        children=[create_connect_tab_content()],
                                    ),
                                    # Keep legacy field-mapping-section-content for callbacks
                                    html.Div(
                                        id="field-mapping-section-content",
                                        style={"display": "none"},
                                    ),
                                ],
                            ),
                            dbc.Tab(
                                label="Queries",
                                tab_id="queries-tab",
                                label_style={"width": "100%"},
                                children=[
                                    # Combined Queries + Data content
                                    html.Div(
                                        id="query-management-section-content",
                                        children=[
                                            create_queries_and_data_tab_content()
                                        ],
                                    ),
                                    # Keep legacy data-actions-section-content for callbacks
                                    html.Div(
                                        id="data-actions-section-content",
                                        style={"display": "none"},
                                    ),
                                ],
                            ),
                        ],
                        id="settings-tabs",
                        active_tab="profile-tab",
                        className="settings-tabs",
                    ),
                ],
                className="panel-tabs-container",
            ),
            # Status indicators
            html.Div(id="dependency-status-display", className="mt-3 d-none"),
            # Hidden components for backward compatibility with legacy callbacks
            # Hidden textarea for legacy jira-jql-query references in settings.py
            dcc.Textarea(id="jira-jql-query", value="", style={"display": "none"}),
        ],
        className="tabbed-settings-panel blue-accent-panel",
    )
