import dash_bootstrap_components as dbc
from dash import html


def create_jira_config_modal():

    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("JIRA Configuration"), close_button=True),
            dbc.ModalBody(
                [
                    html.Div(
                        id="jira-connection-status",
                        style={"minHeight": "0px", "marginBottom": "4px"},
                    ),
                    html.Div(id="jira-last-test-display", className="mb-3"),
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
                                        required=True,
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
                                            {"label": "v2", "value": "v2"},
                                            {"label": "v3", "value": "v3"},
                                        ],
                                        value="v2",
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
                                    (
                                        "Enter your JIRA instance URL "
                                        "(without /rest/api/...)"
                                    ),
                                    color="muted",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-2",
                    ),
                    html.Div(id="jira-api-version-warning", className="mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Personal Access Token (Optional)",
                                        html_for="jira-token-input",
                                        className="fw-bold",
                                    ),
                                    dbc.Input(
                                        id="jira-token-input",
                                        type="password",
                                        placeholder=(
                                            "Leave empty for public JIRA servers"
                                        ),
                                        required=False,
                                    ),
                                    dbc.FormText(
                                        "Required for private JIRA instances. "
                                        "Public servers (e.g., Apache, "
                                        "Jenkins) do not need authentication.",
                                        color="muted",
                                    ),
                                ],
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
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
                                        value=500,
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
                                    "Cache: 10-1000 MB | Page Size: 10-1000 "
                                    "(JIRA API limit 1000/page). App uses "
                                    "pagination to fetch all issues automatically.",
                                    color="muted",
                                ),
                                width=12,
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(id="jira-save-status"),
                ]
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Close",
                        id="jira-config-cancel-button",
                        color="secondary",
                        outline=True,
                        className="me-auto",
                    ),
                    dbc.Button(
                        [html.I(className="fas fa-plug me-2"), "Test Connection"],
                        id="jira-test-connection-button",
                        color="info",
                        outline=True,
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
        backdrop="static",
        keyboard=True,
        centered=True,
    )


def create_jira_config_button(compact: bool = False):

    if compact:
        return dbc.Button(
            html.I(className="fas fa-cog"),
            id="jira-config-button",
            color="primary",
            outline=True,
            size="sm",
            title="Configure JIRA Connection",
            className="mb-3",
        )
    else:
        return dbc.Button(
            [html.I(className="fas fa-cog me-2"), "Configure JIRA"],
            id="jira-config-button",
            color="primary",
            outline=False,
            className="w-100",
            size="md",
        )
