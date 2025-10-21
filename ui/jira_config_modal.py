"""
JIRA Configuration Modal Component

This module provides a Bootstrap modal dialog for JIRA API configuration.
Users can configure their JIRA connection settings once, including base URL,
API version, authentication token, cache settings, and custom field mappings.

Feature: 003-jira-config-separation
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc
from dash import html


#######################################################################
# MODAL COMPONENT
#######################################################################


def create_jira_config_modal():
    """
    Create JIRA configuration modal dialog with form fields.

    Returns:
        dbc.Modal: Complete modal component with form fields for JIRA configuration
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("JIRA Configuration"), close_button=True),
            dbc.ModalBody(
                [
                    # Connection status feedback area
                    html.Div(id="jira-connection-status", className="mb-3"),
                    # Connection Settings (Base URL + API Version in one row)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "JIRA Base URL",
                                        html_for="jira-base-url-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-base-url-input",
                                        type="url",
                                        placeholder="https://your-company.atlassian.net",
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "API Version",
                                        html_for="jira-api-version-select",
                                        className="fw-bold",
                                    ),
                                    dbc.Select(
                                        id="jira-api-version-select",
                                        options=[
                                            {"label": "v3", "value": "v3"},
                                            {"label": "v2", "value": "v2"},
                                        ],
                                        value="v3",
                                    ),
                                ],
                                width=4,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.FormText(
                                    "Enter your JIRA instance URL (without /rest/api/...)",
                                    color="muted",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Authentication (Full width for security)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Personal Access Token",
                                        html_for="jira-token-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-token-input",
                                        type="password",
                                        placeholder="Enter your JIRA personal access token",
                                    ),
                                    dbc.FormText(
                                        "Create in JIRA: Profile → Security → Personal Access Tokens (read permissions)",
                                        color="muted",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Performance Settings (Cache Size + Max Results in one row)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Cache Size (MB)",
                                        html_for="jira-cache-size-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-cache-size-input",
                                        type="number",
                                        min=10,
                                        max=1000,
                                        step=10,
                                        value=100,
                                    ),
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Max Results/Call",
                                        html_for="jira-max-results-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-max-results-input",
                                        type="number",
                                        min=10,
                                        max=1000,
                                        step=10,
                                        value=100,
                                    ),
                                ],
                                width=6,
                            ),
                        ],
                        className="mb-2",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.FormText(
                                    "Cache: 10-1000 MB | Max Results: 10-1000 per API call (JIRA limit)",
                                    color="muted",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Field Mapping (Full width for technical field)
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Story Points Field",
                                        html_for="jira-points-field-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-points-field-input",
                                        type="text",
                                        placeholder="customfield_10016",
                                        value="customfield_10016",
                                    ),
                                    dbc.FormText(
                                        "JIRA custom field ID for story points (e.g., customfield_10016)",
                                        color="muted",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    # Save status feedback area
                    html.Div(id="jira-save-status"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Cancel",
                        id="jira-config-cancel-button",
                        color="secondary",
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-plug me-2"), "Test Connection"],
                        id="jira-test-connection-button",
                        color="info",
                        className="me-2",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save Configuration"],
                        id="jira-config-save-button",
                        color="primary",
                    ),
                ]
            ),
        ],
        id="jira-config-modal",
        size="lg",
        is_open=False,
        backdrop="static",  # Prevent closing by clicking outside
        keyboard=True,  # Allow closing with Escape key
        centered=True,
    )


def create_jira_config_button():
    """
    Create button to open JIRA configuration modal.

    Returns:
        dbc.Button: Configuration button for Data Source interface
    """
    return dbc.Button(
        [html.I(className="fas fa-cog me-2"), "Configure JIRA"],
        id="jira-config-button",
        color="primary",
        outline=False,
        className="mt-3 mb-3 w-100",  # Top and bottom margin, full width
        size="md",  # Standard size to match overall UI
    )
