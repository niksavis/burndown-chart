import dash_bootstrap_components as dbc
from dash import dcc, html

from ui.button_utils import create_panel_collapse_button
from ui.jira_config_modal import create_jira_config_button
from ui.jql_editor import create_jql_editor
from ui.profile_settings_card import create_profile_settings_card

PROFILE_REQUIRED_TOOLTIP = "Create or import a profile first."


def create_connect_tab_content() -> html.Div:

    return html.Div(
        [
            dbc.Row(
                [
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
                                        className=(
                                            "fas fa-exclamation-triangle "
                                            "text-warning me-2"
                                        )
                                    ),
                                    html.Span(
                                        "Configure JIRA to begin",
                                        className="text-muted small",
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            create_jira_config_button(compact=False),
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
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className=(
                                            "fas fa-project-diagram me-2 text-primary"
                                        )
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
                                        className=(
                                            "fas fa-exclamation-triangle "
                                            "text-warning me-2"
                                        )
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

    return html.Div(
        [
            dcc.Store(
                id="query-original-state", data={"name": "", "jql": "", "id": ""}
            ),
            html.Div(
                [
                    html.I(className="fas fa-search me-2 text-primary"),
                    html.Span("Query Management", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-3",
            ),
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
                            style={"marginTop": "1.71rem"},
                        ),
                        xs=12,
                        lg=6,
                        className="mb-2",
                    ),
                ],
                className="g-2",
            ),
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
                        placeholder=(
                            "project = EXAMPLE AND created >= -12w "
                            "ORDER BY created DESC"
                        ),
                        rows=4,
                    ),
                    html.Div(id="jql-validation-feedback", className="mt-2"),
                ],
                className="mb-3",
            ),
            dbc.ButtonGroup(
                [
                    dbc.Button(
                        [html.I(className="fas fa-save me-2"), "Save"],
                        id="save-query-btn",
                        color="success",
                        disabled=True,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-copy me-2"), "Save As"],
                        id="save-as-query-btn",
                        color="primary",
                        outline=True,
                        disabled=True,
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Discard"],
                        id="discard-query-changes-btn",
                        color="danger",
                        outline=True,
                        disabled=True,
                    ),
                ],
                className="mb-3 w-100",
            ),
            html.Div(
                id="query-save-status",
                style={"minHeight": "0px", "marginBottom": "4px"},
            ),
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
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-sync-alt"),
                            html.Span("Update Data"),
                        ],
                        id="update-data-unified",
                        color="primary",
                        disabled=True,
                        className="long-press-button action-button",
                        style={},
                    ),
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
                        },
                    ),
                ],
                style={"position": "relative", "marginBottom": "1rem"},
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
        ],
        className="settings-tab-content",
    )


def create_tabbed_settings_panel() -> html.Div:

    return html.Div(
        [
            dcc.Store(id="configuration-status-store", data={}),
            html.Span(
                PROFILE_REQUIRED_TOOLTIP,
                id="tab-profile-required-description",
                className="visually-hidden",
            ),
            html.Div(
                [
                    create_panel_collapse_button("settings-collapse"),
                    dbc.Tabs(
                        [
                            dbc.Tab(
                                id="profile-settings-tab",
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
                                id="connect-settings-tab",
                                label="Connect",
                                tab_id="connect-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        id="jira-config-section-content",
                                        children=[create_connect_tab_content()],
                                    ),
                                    html.Div(
                                        id="field-mapping-section-content",
                                        style={"display": "none"},
                                    ),
                                ],
                            ),
                            dbc.Tab(
                                id="queries-settings-tab",
                                label="Queries",
                                tab_id="queries-tab",
                                label_style={"width": "100%"},
                                children=[
                                    html.Div(
                                        id="query-management-section-content",
                                        children=[
                                            create_queries_and_data_tab_content()
                                        ],
                                    ),
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
                    dbc.Tooltip(
                        PROFILE_REQUIRED_TOOLTIP,
                        id="connect-tab-disabled-tooltip",
                        target="connect-settings-tab",
                        placement="bottom",
                        class_name="tooltip-info",
                    ),
                    dbc.Tooltip(
                        PROFILE_REQUIRED_TOOLTIP,
                        id="queries-tab-disabled-tooltip",
                        target="queries-settings-tab",
                        placement="bottom",
                        class_name="tooltip-info",
                    ),
                ],
                className="panel-tabs-container",
            ),
            html.Div(id="dependency-status-display", className="mt-3 d-none"),
            dcc.Textarea(id="jira-jql-query", value="", style={"display": "none"}),
        ],
        className="tabbed-settings-panel blue-accent-panel",
    )
