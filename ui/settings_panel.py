"""
Settings Panel Component

Collapsible panel for JIRA integration and import/export settings.
Follows the same pattern as the Parameter Panel for consistent UX.

User Story 6: Contextual Help System - Adds help icons to settings features.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.button_utils import create_button
from ui.components import create_character_count_display, should_show_character_warning
from ui.jql_editor import create_jql_editor
from ui.jira_config_modal import create_jira_config_button
from ui.help_system import create_settings_tooltip
from ui.query_selector import create_query_selector_panel
from ui.profile_selector import create_profile_selector_panel
from ui.profile_modals import (
    create_profile_creation_modal,
    create_profile_duplication_modal,
    create_profile_deletion_modal,
)
from ui.import_export_panel import create_import_export_panel


#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_default_jql_query():
    """Get default JQL query from settings."""
    try:
        from data.persistence import load_app_settings

        app_settings = load_app_settings()
        return app_settings.get("jql_query", "project = JRASERVER")
    except ImportError:
        return "project = JRASERVER"


def _get_default_jql_profile_id():
    """
    Get profile ID for dropdown initial value.

    Priority:
    1. If jql_query exactly matches a saved profile → return that profile ID
    2. Otherwise → return empty (dropdown shows no selection)

    This ensures the dropdown accurately reflects whether the current query
    matches a saved profile or is a custom query.
    """
    try:
        from data.persistence import load_app_settings
        from data.jira_query_manager import load_query_profiles

        app_settings = load_app_settings()
        jql_query = app_settings.get("jql_query", "")

        if not jql_query:
            return ""

        # Try to match current JQL query to a saved profile
        profiles = load_query_profiles()
        normalized_query = jql_query.strip().lower()

        for profile in profiles:
            profile_jql = profile.get("jql", "")
            if profile_jql.strip().lower() == normalized_query:
                return profile.get("id", "")

        # No match found - return empty (user has custom query)
        return ""

    except (ImportError, Exception):
        return ""


def _get_query_profile_options():
    """Get query profile dropdown options."""
    try:
        from data.jira_query_manager import load_query_profiles

        profiles = load_query_profiles()
        options = []
        for profile in profiles:
            label = profile.get("name", "Unnamed")
            if profile.get("is_default", False):
                label += " ★"
            options.append(
                {
                    "label": label,
                    "value": profile.get("id", ""),
                }
            )
        return options
    except (ImportError, Exception):
        return []


#######################################################################
# SETTINGS PANEL EXPANDED CONTENT
#######################################################################


def create_settings_panel_expanded(id_suffix: str = "") -> html.Div:
    """
    Create expanded settings panel content with JIRA integration and import/export.

    Args:
        id_suffix: Suffix for unique IDs

    Returns:
        html.Div: Expanded panel content
    """
    return html.Div(
        [
            dbc.Card(
                [
                    dbc.CardBody(
                        [
                            # Two column layout
                            dbc.Row(
                                [
                                    # Left Column: JIRA Integration
                                    dbc.Col(
                                        [
                                            # Header with config button
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-plug me-2 text-primary"
                                                    ),
                                                    html.Span(
                                                        "JIRA Integration",
                                                        className="fw-bold",
                                                    ),
                                                    html.Span(
                                                        create_settings_tooltip(
                                                            "jira_integration",
                                                            "jira-integration-help",
                                                        ),
                                                        style={"marginLeft": "0.25rem"},
                                                    ),
                                                ],
                                                className="d-flex align-items-center mb-2",
                                            ),
                                            # Status indicator and config button row
                                            html.Div(
                                                [
                                                    html.Div(
                                                        id="jira-config-status-indicator",
                                                        className="flex-grow-1 me-2",
                                                        style={
                                                            "minHeight": "2rem",
                                                            "overflowX": "auto",
                                                            "overflowY": "hidden",
                                                            "whiteSpace": "nowrap",
                                                        },
                                                        children=[],
                                                    ),
                                                    html.Div(
                                                        [
                                                            dbc.Button(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-project-diagram me-1"
                                                                    ),
                                                                    "Mappings",
                                                                ],
                                                                id="open-field-mapping-modal",
                                                                color="info",
                                                                size="sm",
                                                                outline=True,
                                                                className="me-2",
                                                                title="Configure JIRA mappings (fields, projects, types, statuses, environment)",
                                                            ),
                                                            create_jira_config_button(
                                                                compact=True
                                                            ),
                                                        ],
                                                        className="d-flex",
                                                        style={"flexShrink": "0"},
                                                    ),
                                                ],
                                                className="d-flex align-items-center mb-3",
                                            ),
                                            # JQL Query Editor - starts immediately after header
                                            html.Div(
                                                [
                                                    html.Label(
                                                        [
                                                            "JQL Query",
                                                            html.Span(
                                                                create_settings_tooltip(
                                                                    "jql_query",
                                                                    "jql-query-help",
                                                                ),
                                                                style={
                                                                    "marginLeft": "0.25rem"
                                                                },
                                                            ),
                                                        ],
                                                        className="form-label small text-muted mb-1",
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
                                                                count=len(
                                                                    _get_default_jql_query()
                                                                    or ""
                                                                ),
                                                                warning=should_show_character_warning(
                                                                    _get_default_jql_query()
                                                                ),
                                                            )
                                                        ],
                                                        className="mt-1 mb-2",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Profile Management - above Query Management
                                            create_profile_selector_panel(),
                                            # Query Selector - replaces old "Saved Queries"
                                            create_query_selector_panel(),
                                            # Hidden compatibility components for old JQL profile callbacks
                                            # TODO: Remove these after migrating all old JQL profile callbacks
                                            html.Div(
                                                [
                                                    dcc.Dropdown(
                                                        id="jira-query-profile-selector",
                                                        options=[],
                                                        value="",
                                                        style={"display": "none"},
                                                    ),
                                                    dbc.Button(
                                                        id="save-jql-query-button",
                                                        style={"display": "none"},
                                                    ),
                                                    dbc.Button(
                                                        id="edit-jql-query-button",
                                                        style={"display": "none"},
                                                    ),
                                                    dbc.Button(
                                                        id="delete-jql-query-button",
                                                        style={"display": "none"},
                                                    ),
                                                ],
                                                style={"display": "none"},
                                            ),
                                            # Action Buttons - side by side below Saved Queries
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Fetch Data ",
                                                                    html.Span(
                                                                        "(Hold 3s to force refresh)",
                                                                        className="text-muted",
                                                                        style={
                                                                            "fontSize": "0.75rem",
                                                                            "fontWeight": "normal",
                                                                        },
                                                                    ),
                                                                    html.Span(
                                                                        create_settings_tooltip(
                                                                            "update_data",
                                                                            "fetch-data-help",
                                                                        ),
                                                                        style={
                                                                            "marginLeft": "0.25rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                className="form-label small text-muted mb-1",
                                                            ),
                                                            create_button(
                                                                text="Update Data",
                                                                id="update-data-unified",
                                                                variant="primary",
                                                                icon_class="fas fa-sync-alt",
                                                                className="w-100 long-press-button",
                                                                size="md",
                                                            ),
                                                            dcc.Store(
                                                                id="force-refresh-store",
                                                                data=False,
                                                            ),
                                                            dcc.Loading(
                                                                id="update-data-loading",
                                                                type="dot",
                                                                color="#0d6efd",
                                                                children=html.Div(
                                                                    id="jira-cache-status",
                                                                    className="text-center text-muted small mt-2",
                                                                    style={
                                                                        "minHeight": "40px"
                                                                    },  # Fixed height for consistent loading position
                                                                    children="",
                                                                ),
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                [
                                                                    "Flow & DORA Metrics",
                                                                    html.Span(
                                                                        create_settings_tooltip(
                                                                            "calculate_metrics",
                                                                            "calculate-metrics-help",
                                                                        ),
                                                                        style={
                                                                            "marginLeft": "0.25rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                className="form-label small text-muted mb-1",
                                                            ),
                                                            create_button(
                                                                text="Calculate Metrics",
                                                                id="calculate-metrics-button",
                                                                variant="primary",
                                                                icon_class="fas fa-calculator",
                                                                className="w-100",
                                                                size="md",
                                                            ),
                                                            dcc.Loading(
                                                                id="calculate-metrics-loading",
                                                                type="dot",
                                                                color="#0d6efd",
                                                                children=html.Div(
                                                                    id="calculate-metrics-status",
                                                                    className="text-center text-muted small mt-2",
                                                                    style={
                                                                        "minHeight": "40px"
                                                                    },  # Fixed height for consistent loading position
                                                                    children="",
                                                                ),
                                                            ),
                                                        ],
                                                        md=6,
                                                    ),
                                                ],
                                                className="g-2",
                                            ),
                                        ],
                                        md=8,
                                        className="border-end",
                                    ),
                                    # Right Column: Import/Export
                                    dbc.Col(
                                        [
                                            # Header - aligned with left column
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-exchange-alt me-2 text-success"
                                                    ),
                                                    html.Span(
                                                        "Import / Export",
                                                        className="fw-bold",
                                                    ),
                                                    html.Span(
                                                        create_settings_tooltip(
                                                            "import_data",
                                                            "import-export-help",
                                                        ),
                                                        style={"marginLeft": "0.25rem"},
                                                    ),
                                                ],
                                                className="d-flex align-items-center mb-2",
                                            ),
                                            # Import - more compact
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Import Data",
                                                        className="form-label small text-muted mb-1",
                                                    ),
                                                    dcc.Upload(
                                                        id="upload-data",
                                                        children=html.Div(
                                                            [
                                                                html.I(
                                                                    className="fas fa-cloud-upload-alt fa-lg mb-1 text-primary"
                                                                ),
                                                                html.P(
                                                                    "Drop file or click",
                                                                    className="mb-0 small",
                                                                ),
                                                                html.Small(
                                                                    "JSON/CSV",
                                                                    className="text-muted",
                                                                    style={
                                                                        "fontSize": "0.75rem"
                                                                    },
                                                                ),
                                                            ],
                                                            className="text-center py-2",
                                                        ),
                                                        style={
                                                            "width": "100%",
                                                            "borderWidth": "2px",
                                                            "borderStyle": "dashed",
                                                            "borderRadius": "8px",
                                                            "borderColor": "#dee2e6",
                                                            "backgroundColor": "#f8f9fa",
                                                            "cursor": "pointer",
                                                        },
                                                        multiple=False,
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            # Export - more compact
                                            html.Div(
                                                [
                                                    html.Label(
                                                        "Export Data",
                                                        className="form-label small text-muted mb-1",
                                                    ),
                                                    create_button(
                                                        text="Export Data",
                                                        id="export-project-data-button",
                                                        variant="secondary",
                                                        icon_class="fas fa-file-export",
                                                        className="w-100",
                                                    ),
                                                    html.Div(
                                                        dcc.Download(
                                                            id="export-project-data-download"
                                                        )
                                                    ),
                                                ],
                                            ),
                                        ],
                                        md=4,
                                    ),
                                ],
                                className="g-3",
                            ),
                            # Hidden components for callback compatibility
                            html.Div(
                                [
                                    dcc.Dropdown(
                                        id="jira-query-profile-selector-mobile",
                                        options=[],
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        id="query-profile-status",
                                        style={"display": "none"},
                                    ),
                                    html.Button(
                                        id="load-default-jql-query-button",
                                        style={"display": "none"},
                                    ),
                                ],
                                style={"display": "none"},
                            ),
                        ],
                        style={"paddingTop": "0", "marginTop": "0"},
                    )
                ],
                className="shadow-sm",
            )
        ],
        className="settings-panel-expanded",
    )


#######################################################################
# SETTINGS PANEL CONTAINER
#######################################################################


def create_settings_panel(is_open: bool = False, id_suffix: str = "") -> html.Div:
    """
    Create complete collapsible settings panel.

    Args:
        is_open: Whether panel should start in expanded state
        id_suffix: Suffix for generating unique IDs

    Returns:
        html.Div: Complete settings panel with collapse functionality
    """
    collapse_id = f"settings-collapse{'-' + id_suffix if id_suffix else ''}"
    panel_id = f"settings-panel{'-' + id_suffix if id_suffix else ''}"

    return html.Div(
        [
            # Collapsible panel
            dbc.Collapse(
                create_settings_panel_expanded(id_suffix=id_suffix),
                id=collapse_id,
                is_open=is_open,
                style={"marginTop": "-1rem"},
            ),
            # Profile management modals
            create_profile_creation_modal(),
            create_profile_duplication_modal(),
            create_profile_deletion_modal(),
        ],
        id=panel_id,
        className="settings-panel-container",
        style={"marginTop": "0rem"},
    )
