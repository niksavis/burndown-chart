import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.jira_config_modal import create_jira_config_button
from ui.jql_editor import create_jql_editor
from ui.profile_settings_card import create_profile_settings_card
from ui.query_selector import create_query_selector_panel


def create_jira_config_card() -> html.Div:

    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-plug me-2 text-primary"),
                    html.Span("JIRA Connection", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            html.Div(
                id="jira-config-status-indicator",
                className="mb-3",
                children=[
                    dbc.Alert(
                        [
                            html.I(className="fas fa-info-circle me-2 text-info"),
                            "JIRA not configured. Click Configure to get started.",
                        ],
                        color="info",
                    )
                ],
            ),
            create_jira_config_button(compact=False),
            html.Div(
                id="jira-connection-test-status",
                style={"minHeight": "0px", "marginTop": "4px"},
            ),
            html.Div(id="jira-cache-status", style={"display": "none"}),
        ]
    )


def create_field_mapping_card() -> html.Div:

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

    return html.Div(
        [
            create_query_selector_panel(),
            html.Hr(),
            html.Div(
                [
                    html.Label("JQL Query", className="form-label fw-bold"),
                    html.P(
                        "Enter JIRA Query Language (JQL) to filter issues",
                        className="text-muted small",
                    ),
                    create_jql_editor(
                        editor_id="query-jql-editor",
                        initial_value=(
                            "project = EXAMPLE AND created >= -12w "
                            "ORDER BY created DESC"
                        ),
                        placeholder="project = EXAMPLE AND created >= -12w",
                        rows=4,
                    ),
                    html.Div(
                        [
                            html.I(className="fas fa-info-circle text-info me-2"),
                            html.Span(
                                "Tip: Query development projects only. "
                                "Configure DevOps projects in Field "
                                "Mappings for optimized fetching.",
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

    return html.Div(
        [
            html.Div(
                [
                    html.I(className="fas fa-database me-2 text-primary"),
                    html.Span("Data Operations", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
            html.Div(
                [
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
                        disabled=True,
                        className="mb-3 long-press-button",
                    ),
                    dcc.Store(id="force-refresh-store", data=False),
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
                    dcc.Interval(
                        id="progress-poll-interval",
                        interval=250,
                        disabled=True,
                    ),
                    html.Div(
                        html.Div(id="update-data-status"),
                        style={"display": "none"},
                    ),
                    html.Div(
                        [
                            html.Small(
                                [
                                    html.I(
                                        className="fas fa-info-circle me-1 text-info"
                                    ),
                                    "Use the ",
                                    html.Strong("Data"),
                                    (
                                        " button in the top bar "
                                        "to import/export project data."
                                    ),
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

    return html.Div(
        [
            dcc.Store(id="configuration-status-store", data={}),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [create_profile_settings_card()],
                        title="1. Profile Settings",
                        id="profile-section-accordion",
                        item_id="profile-section",
                    ),
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
                always_open=False,
                start_collapsed=False,
                active_item="profile-section",
            ),
            html.Div(id="dependency-status-display", className="mt-3"),
            dcc.Textarea(id="jira-jql-query", value="", style={"display": "none"}),
        ],
        className="accordion-settings-panel",
    )
