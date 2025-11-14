"""
Improved Settings Panel Component

Restructured for better UX workflow:
1. JIRA Connection (setup)
2. Workspace Profiles (context)
3. Query Builder (what to fetch)
4. Data Actions (execute)
5. Import/Export (data management)
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
from ui.unsaved_changes_warning import create_unsaved_changes_warning
from ui.profile_modals import (
    create_profile_creation_modal,
    create_profile_duplication_modal,
    create_profile_deletion_modal,
)


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


def create_improved_settings_panel(is_open: bool = False):
    """
    Create an improved settings panel with better UX workflow as a flyout.

    This creates a collapsible settings panel similar to the parameter panel,
    with numbered workflow sections for better UX.

    Args:
        is_open: Whether panel should start in expanded state

    Returns:
        html.Div: Complete settings panel with collapse functionality
    """
    return html.Div(
        [
            # Collapsible settings panel content only (no banner - drops down from main banner)
            dbc.Collapse(
                create_settings_panel_content(),
                id="settings-collapse",
                is_open=is_open,
            ),
            # Modals
            create_profile_creation_modal(),
            create_profile_duplication_modal(),
            create_profile_deletion_modal(),
        ],
        id="settings-panel",
        className="settings-panel-container",
    )


def create_settings_panel_content():
    """
    Create the content for the settings panel flyout.

    Structure:
    1. JIRA Connection - establish connection first
    2. Workspace Profiles - choose or create workspace context
    3. Query Builder - define what data to fetch
    4. Data Actions - execute the fetch and calculations
    5. Import/Export - data management options (as separate flyout)
    """
    return dbc.Card(
        dbc.CardBody(
            [
                # Header with icon
                html.H5(
                    [
                        html.I(
                            className="fas fa-cog me-2",
                            style={"color": "#6c757d"},
                        ),
                        "Configuration Settings",
                    ],
                    className="mb-4 mt-3 text-secondary",
                    style={"fontSize": "1.1rem", "fontWeight": "600"},
                ),
                # Section 1: JIRA Connection
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="fas fa-plug me-2",
                                    style={"color": "#0d6efd"},
                                ),
                                "1. JIRA Connection",
                                html.Span(
                                    create_settings_tooltip(
                                        "jira_integration",
                                        "jira-integration-help",
                                    ),
                                    style={"marginLeft": "0.25rem"},
                                ),
                            ],
                            className="mb-3 text-primary",
                        ),
                        # Connection status and config buttons
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
                                                "Field Mappings",
                                            ],
                                            id="open-field-mapping-modal",
                                            color="info",
                                            size="sm",
                                            outline=True,
                                            className="me-2",
                                            title="Configure JIRA field mappings for DORA & Flow metrics",
                                        ),
                                        create_jira_config_button(compact=True),
                                    ],
                                    className="d-flex",
                                    style={"flexShrink": "0"},
                                ),
                            ],
                            className="d-flex align-items-center",
                        ),
                    ],
                    className="mb-4 pb-3 border-bottom",
                ),
                # Section 2: Workspace Profiles
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="fas fa-folder me-2",
                                    style={"color": "#fd7e14"},
                                ),
                                "2. Workspace Profile",
                                html.Span(
                                    create_settings_tooltip(
                                        "profile_management",
                                        "profile-help",
                                    ),
                                    style={"marginLeft": "0.25rem"},
                                ),
                            ],
                            className="mb-3 text-warning",
                        ),
                        create_profile_selector_panel(),
                    ],
                    className="mb-4 pb-3 border-bottom",
                ),
                # Section 3: Query Builder
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="fas fa-search me-2",
                                    style={"color": "#0dcaf0"},
                                ),
                                "3. Query Builder",
                                html.Span(
                                    create_settings_tooltip(
                                        "jql_query",
                                        "jql-query-help",
                                    ),
                                    style={"marginLeft": "0.25rem"},
                                ),
                            ],
                            className="mb-3 text-info",
                        ),
                        # Saved queries section
                        create_query_selector_panel(),
                        # JQL Editor with auto-save notice
                        html.Div(
                            [
                                html.Label(
                                    [
                                        "JQL Query",
                                        html.Span(
                                            " (Auto-saves when you Update Data)",
                                            className="text-success",
                                            style={"fontSize": "0.75rem"},
                                        ),
                                    ],
                                    className="form-label small text-muted mb-2",
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
                                    className="mt-1",
                                ),
                                # Unsaved changes warning
                                create_unsaved_changes_warning(),
                            ],
                            className="mt-3",
                        ),
                    ],
                    className="mb-4 pb-3 border-bottom",
                ),
                # Section 4: Data Actions
                html.Div(
                    [
                        html.H6(
                            [
                                html.I(
                                    className="fas fa-play me-2",
                                    style={"color": "#198754"},
                                ),
                                "4. Data Actions",
                            ],
                            className="mb-3 text-success",
                        ),
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
                                                    style={"marginLeft": "0.25rem"},
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
                                                style={"minHeight": "40px"},
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
                                                    style={"marginLeft": "0.25rem"},
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
                                                style={"minHeight": "40px"},
                                                children="",
                                            ),
                                        ),
                                    ],
                                    md=6,
                                ),
                            ],
                            className="g-3",
                        ),
                    ],
                    className="mb-4 pb-3 border-bottom",
                ),
                # Hidden compatibility components for old callbacks
                html.Div(
                    [
                        dcc.Dropdown(
                            id="jira-query-profile-selector",
                            options=[],
                            value="",
                            style={"display": "none"},
                        ),
                        dcc.Dropdown(
                            id="jira-query-profile-selector-mobile",
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
                        dbc.Button(
                            id="load-default-jql-query-button",
                            style={"display": "none"},
                        ),
                        html.Div(id="query-profile-status", style={"display": "none"}),
                    ],
                    style={"display": "none"},
                ),
            ],
            className="settings-panel-expanded",
            style={"paddingTop": "0px", "marginTop": "0px"},
        ),
        className="mb-4",
    )


# Keep the old function for backward compatibility but redirect to new one
def create_settings_panel():
    """Create the settings panel - redirects to improved version."""
    return create_improved_settings_panel()
