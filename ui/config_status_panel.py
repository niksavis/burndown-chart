from typing import Any

import dash_bootstrap_components as dbc
from dash import dcc, html


def get_action_button_config(action: str) -> dict[str, str] | None:

    config_map = {
        "configure_jira": {
            "text": "Configure JIRA",
            "icon": "fas fa-plug",
            "color": "primary",
            "id": "open-jira-config-modal",
        },
        "configure_fields": {
            "text": "Map Fields",
            "icon": "fas fa-project-diagram",
            "color": "info",
            "id": "open-field-mapping-modal",
        },
        "create_query": {
            "text": "Create Query",
            "icon": "fas fa-search",
            "color": "success",
            "id": "create-first-query-button",
        },
    }
    return config_map.get(action, None)


def create_setup_progress_display(config_status: dict[str, dict]) -> html.Div:

    if not config_status:
        return html.Div("Configuration status unavailable", className="text-muted")

    completed_steps = sum(
        1 for step in config_status.values() if step.get("complete", False)
    )
    total_steps = len(config_status)
    progress_percent = (completed_steps / total_steps * 100) if total_steps > 0 else 0

    return html.Div(
        [
            html.Div(
                [
                    html.H6("Setup Progress", className="mb-2 fw-semibold text-dark"),
                    html.Div(
                        [
                            html.Span(
                                f"{completed_steps}/{total_steps} Complete",
                                className="small text-muted me-2",
                            ),
                            html.Span(
                                f"({progress_percent:.0f}%)",
                                className="small text-primary fw-semibold",
                            ),
                        ]
                    ),
                ],
                className="d-flex justify-content-between align-items-center mb-3",
            ),
            dbc.Progress(
                value=progress_percent,
                color="success" if progress_percent == 100 else "primary",
                className="mb-4",
                style={"height": "8px"},
            ),
            html.Div(
                [
                    create_step_indicator(
                        "profile", "Profile", config_status.get("profile", {})
                    ),
                    create_step_indicator(
                        "jira", "JIRA Connection", config_status.get("jira", {})
                    ),
                    create_step_indicator(
                        "fields", "Field Mapping", config_status.get("fields", {})
                    ),
                    create_step_indicator(
                        "queries", "Queries", config_status.get("queries", {})
                    ),
                ],
                className="vstack gap-2",
            ),
        ],
        className="config-status-panel p-3 bg-light rounded border",
    )


def create_step_indicator(
    step_id: str, step_name: str, step_status: dict[str, Any]
) -> html.Div:

    enabled = step_status.get("enabled", False)
    complete = step_status.get("complete", False)
    message = step_status.get("message", "Status unknown")
    next_step = step_status.get("next_step", "")
    action = step_status.get("action", None)

    if complete:
        icon = "fas fa-check-circle text-success"
        badge_color = "success"
        badge_text = "Complete"
    elif enabled:
        icon = "fas fa-clock text-warning"
        badge_color = "warning"
        badge_text = "In Progress"
    else:
        icon = "fas fa-lock text-muted"
        badge_color = "secondary"
        badge_text = "Locked"

    clickable = enabled and not complete and action
    cursor_style = "pointer" if clickable else "default"

    action_button = None
    if clickable and action:
        button_config = get_action_button_config(action)
        if button_config:
            action_button = dbc.Button(
                [
                    html.I(className=button_config["icon"] + " me-1"),
                    button_config["text"],
                ],
                id=button_config["id"],
                color=button_config["color"],
                size="sm",
                outline=True,
                className="mt-2",
            )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.I(className=icon + " me-2"),
                            html.Span(step_name, className="fw-semibold"),
                        ],
                        className="d-flex align-items-center",
                    ),
                    dbc.Badge(badge_text, color=badge_color, className="ms-auto"),
                ],
                className="d-flex justify-content-between align-items-center mb-1",
            ),
            html.Div(message, className="small text-muted mb-1"),
            html.Div(
                f"Next: {next_step}"
                if (enabled and not complete and next_step)
                else "",
                className="small text-primary",
                style={
                    "display": "block"
                    if (enabled and not complete and next_step)
                    else "none"
                },
            ),
            action_button if action_button else html.Div(),
        ],
        id=f"config-step-{step_id}",
        className=f"config-step {'clickable' if clickable else 'disabled'}",
        style={
            "cursor": cursor_style,
            "padding": "12px 16px",
            "borderRadius": "8px",
            "border": "1px solid #dee2e6",
            "backgroundColor": "#ffffff" if enabled else "#f8f9fa",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.1)" if clickable else "none",
        },
    )


def create_configuration_status_store() -> dcc.Store:
    return dcc.Store(
        id="configuration-status-store",
        data={},
        storage_type="session",
    )


def create_config_status_panel() -> html.Div:

    return html.Div(
        [
            create_configuration_status_store(),
            html.Div(
                id="setup-progress-display",
                children=[
                    html.Div(
                        [
                            html.I(
                                className="fas fa-spinner fa-spin me-2 text-primary"
                            ),
                            "Loading configuration status...",
                        ],
                        className="text-muted p-3",
                    )
                ],
            ),
        ],
        id="config-status-panel-container",
    )


def get_section_classes(config_status: dict[str, dict]) -> dict[str, str]:

    if not config_status:
        return {
            "jira-config-section": "config-section disabled",
            "field-mapping-section": "config-section disabled",
            "query-management-section": "config-section disabled",
        }

    jira_enabled = config_status.get("profile", {}).get("complete", False)
    fields_enabled = config_status.get("jira", {}).get("complete", False)
    queries_enabled = config_status.get("fields", {}).get("complete", False)

    return {
        "jira-config-section": "config-section"
        if jira_enabled
        else "config-section disabled",
        "field-mapping-section": "config-section"
        if fields_enabled
        else "config-section disabled",
        "query-management-section": "config-section"
        if queries_enabled
        else "config-section disabled",
    }
