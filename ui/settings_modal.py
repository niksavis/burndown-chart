"""
Settings Modal Component

This module provides a comprehensive settings modal for data source configuration,
import/export, and JQL query management. Consolidates all configuration options
that were previously in the Data Import Configuration card.

Feature: Configuration UI consolidation for better UX
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.button_utils import create_button
from ui.jql_components import (
    create_character_count_display,
    should_show_character_warning,
)
from ui.jql_editor import create_jql_editor

#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_default_data_source():
    """Get default data source from settings."""
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        data_source = app_settings.get("last_used_data_source", "JIRA")
        return data_source if data_source else "JIRA"
    except (ImportError, Exception):
        return "JIRA"


def _get_default_jql_query():
    """Get default JQL query from settings."""
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jql_profile_id():
    """Get active JQL profile ID from settings."""
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("active_jql_profile_id", "")
    except (ImportError, Exception):
        return ""


def _get_query_profile_options():
    """Get query profile dropdown options."""
    try:
        from data.jira.query_profiles import load_query_profiles

        profiles = load_query_profiles()
        options = []
        for profile in profiles:
            options.append(
                {
                    "label": profile.get("name", "Unnamed"),
                    "value": profile.get("id", ""),
                }
            )
        return options
    except (ImportError, Exception):
        return []


#######################################################################
# MODAL TABS CONTENT
#######################################################################


def create_data_source_tab():
    """Create Data Source tab content."""
    return html.Div(
        [
            html.P(
                "Choose between JIRA API (recommended) or JSON/CSV file upload.",
                className="text-muted mb-3",
            ),
            dbc.RadioItems(
                id="data-source-selection",
                options=[
                    {"label": "JIRA API", "value": "JIRA"},
                    {"label": "JSON/CSV Import", "value": "CSV"},
                ],
                value=_get_default_data_source(),
                inline=False,
                className="mb-3",
            ),
        ],
        className="p-3",
    )


def create_import_export_tab():
    """Create Import/Export tab content."""
    return html.Div(
        [
            # Import Section
            html.H6("Import Data", className="mb-3"),
            html.P(
                "Upload project data from JSON or CSV file.",
                className="text-muted small mb-2",
            ),
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.I(
                            className="fas fa-cloud-upload-alt fa-3x mb-2 text-primary"
                        ),
                        html.P("Drag and Drop or Click to Select", className="mb-0"),
                        html.Small(
                            "Supports CSV and JSON formats",
                            className="text-muted",
                        ),
                    ],
                    className="text-center py-4",
                ),
                style={
                    "width": "100%",
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
            html.Hr(className="my-4"),
            # Export Section
            html.H6("Export Data", className="mb-3"),
            html.P(
                "Export complete project data as JSON for backup or sharing.",
                className="text-muted small mb-3",
            ),
            create_button(
                text="Export Project Data",
                id="export-project-data-button",
                variant="secondary",
                icon_class="fas fa-file-export",
                className="w-100",
            ),
            html.Div(dcc.Download(id="export-project-data-download")),
        ],
        className="p-3",
    )


def create_jira_integration_tab():
    """Create JIRA Integration tab content (formerly JQL Queries)."""
    from ui.jira_config_modal import create_jira_config_button

    return html.Div(
        [
            # JIRA Configuration Section
            html.H6("JIRA Configuration", className="mb-3"),
            html.P(
                "Configure your JIRA connection settings (URL, token, custom fields).",
                className="text-muted small mb-3",
            ),
            create_jira_config_button(),
            html.Div(
                id="jira-config-status-indicator",
                className="mt-2 mb-3",
                children=[],
            ),
            html.Hr(className="my-4"),
            # JQL Editor
            html.H6("JQL Query Editor", className="mb-3"),
            html.P(
                "Write your JQL query to fetch issues from JIRA.",
                className="text-muted small mb-2",
            ),
            create_jql_editor(
                editor_id="jira-jql-query",
                initial_value=_get_default_jql_query(),
                placeholder="project = MYPROJECT AND created >= startOfYear()",
                rows=4,
            ),
            html.Div(
                id="jira-jql-character-count-container",
                children=[
                    create_character_count_display(
                        count=len(_get_default_jql_query() or ""),
                        warning=should_show_character_warning(_get_default_jql_query()),
                    )
                ],
                className="mb-3",
            ),
            # Query Management Actions
            html.H6("Saved Queries", className="mb-3 mt-4"),
            html.P(
                "Save your current query, or select a saved query "
                "to load it into the editor above.",
                className="text-muted small mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dcc.Dropdown(
                                id="jira-query-profile-selector",
                                options=_get_query_profile_options(),
                                value=_get_default_jql_profile_id(),
                                placeholder="Select saved query to load...",
                                clearable=True,
                                searchable=True,
                                className="mb-2",
                            ),
                        ],
                        xs=12,
                        md=5,
                    ),
                    dbc.Col(
                        [
                            dbc.ButtonGroup(
                                [
                                    create_button(
                                        text="Save",
                                        id="save-jql-query-button",
                                        variant="primary",
                                        icon_class="fas fa-save",
                                        size="sm",
                                    ),
                                    create_button(
                                        text="Edit",
                                        id="edit-jql-query-button",
                                        variant="outline-secondary",
                                        icon_class="fas fa-edit",
                                        size="sm",
                                    ),
                                    create_button(
                                        text="Delete",
                                        id="delete-jql-query-button",
                                        variant="outline-danger",
                                        icon_class="fas fa-trash",
                                        size="sm",
                                    ),
                                ],
                                className="w-100",
                            ),
                        ],
                        xs=12,
                        md=7,
                    ),
                ],
                className="g-2",
            ),
            html.Div(
                id="jira-jql-query-save-status",
                className="text-center mt-2",
                children=[],
            ),
            # Hidden components for mobile compatibility (callbacks may reference these)
            html.Div(
                [
                    dcc.Dropdown(
                        id="jira-query-profile-selector-mobile",
                        options=[],
                        style={"display": "none"},
                    ),
                    html.Div(id="query-profile-status", style={"display": "none"}),
                    html.Button(
                        id="load-default-jql-query-button", style={"display": "none"}
                    ),
                ],
                style={"display": "none"},
            ),
            html.Hr(className="my-4"),
            # Update Data Action
            html.H6("Fetch JIRA Data", className="mb-3"),
            html.P(
                "Fetches JIRA data using the query above "
                "and automatically calculates project scope.",
                className="text-muted small mb-3",
            ),
            create_button(
                text="Update Data",
                id="update-data-unified",
                variant="primary",
                icon_class="fas fa-sync-alt",
                className="w-100",
                size="md",
            ),
            html.Div(
                id="jira-cache-status",
                className="text-center text-muted small mt-2",
                children="Ready to fetch JIRA data",
            ),
        ],
        className="p-3",
    )


#######################################################################
# MODAL COMPONENT
#######################################################################


def create_settings_modal():
    """
    Create comprehensive settings modal with tabs for configuration.

    Returns:
        dbc.Modal: Complete modal component with tabbed interface for:
        - Import/Export (CSV upload, JSON export)
        - JIRA Integration (JIRA config, JQL editor, saved queries, fetch data)
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle([html.I(className="fas fa-cog me-2"), "Settings"]),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                create_import_export_tab(),
                                label="Import/Export",
                                tab_id="tab-import-export",
                                label_style={"cursor": "pointer"},
                                active_label_style={"fontWeight": "600"},
                            ),
                            dbc.Tab(
                                create_jira_integration_tab(),
                                label="JIRA Integration",
                                tab_id="tab-jira-integration",
                                label_style={"cursor": "pointer"},
                                active_label_style={"fontWeight": "600"},
                            ),
                        ],
                        id="settings-modal-tabs",
                        active_tab="tab-import-export",
                    ),
                ],
                style={"maxHeight": "70vh", "overflowY": "auto"},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Close",
                        id="settings-modal-close-button",
                        color="secondary",
                        className="ms-auto",
                    ),
                ]
            ),
        ],
        id="settings-modal",
        size="lg",
        is_open=False,
        backdrop=True,
        keyboard=True,
        centered=True,
        scrollable=True,
        className="settings-modal-custom",
    )


def create_settings_button():
    """
    Create button to open settings modal.

    Returns:
        dbc.Button: Settings button for top navigation
    """
    return dbc.Button(
        [
            html.I(className="fas fa-cog me-2"),
            html.Span("Settings", className="d-none d-md-inline"),
        ],
        id="settings-button",
        color="primary",
        outline=True,
        size="sm",
        className="ms-2",
        title="Configure data sources, import/export, and JQL queries",
    )


#######################################################################
# QUERY MANAGEMENT MODALS
#######################################################################


# REMOVED: create_save_query_modal() - replaced by ui/save_query_modal.py


# REMOVED: create_delete_query_modal() - replaced by ui/delete_query_modal.py


# REMOVED: create_edit_query_modal() - replaced by integrated query management callbacks
