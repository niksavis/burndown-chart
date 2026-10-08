from datetime import datetime
from urllib.parse import urlparse

import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, ctx, html, no_update
from dash.exceptions import PreventUpdate

from configuration import logger
from data.jira import test_jira_connection
from data.persistence.adapters import (
    load_jira_configuration,
    save_jira_configuration,
    validate_jira_config,
)
from ui.toast_notifications import (
    create_error_toast,
    create_success_toast,
    create_warning_toast,
)


@callback(
    Output("jira-config-modal", "is_open"),
    Input("jira-config-button", "n_clicks"),
    prevent_initial_call=True,
)
def open_jira_config_modal(n_clicks):

    if n_clicks:
        logger.info("Opening JIRA configuration modal")
        return True
    return no_update


@callback(
    [
        Output("jira-base-url-input", "value"),
        Output("jira-api-version-select", "value"),
        Output("jira-token-input", "value"),
        Output("jira-cache-size-input", "value"),
        Output("jira-max-results-input", "value"),
    ],
    Input("jira-config-modal", "is_open"),
)
def load_jira_config(is_open):

    if not is_open:
        raise PreventUpdate

    try:
        config = load_jira_configuration()
        logger.info("Loaded JIRA configuration for display")

        return (
            config.get("base_url", ""),
            config.get("api_version", "v3"),
            config.get("token", ""),
            config.get("cache_size_mb", 100),
            config.get("max_results_per_call", 100),
        )
    except Exception as e:
        logger.error(f"Error loading JIRA configuration: {e}")
        return ("", "v3", "", 100, 100)


@callback(
    [
        Output("jira-connection-status", "children"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("jira-test-connection-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value"),
    ],
    prevent_initial_call=True,
)
def test_jira_connection_callback(n_clicks, base_url, api_version, token):

    if not n_clicks:
        raise PreventUpdate

    if not base_url:
        toast = create_warning_toast(
            "Please fill in the JIRA Base URL before testing.",
            header="Missing Required Field",
        )
        return "", toast

    logger.info(f"Testing JIRA connection to {base_url} (authenticated: {bool(token)})")
    result = test_jira_connection(
        base_url.strip(), token.strip() if token else "", api_version
    )

    try:
        config = load_jira_configuration()
        config["last_test_timestamp"] = result.get("timestamp")
        config["last_test_success"] = result["success"]
        save_jira_configuration(config)
        logger.debug(
            "Saved test result: "
            f"success={result['success']}, "
            f"timestamp={result.get('timestamp')}"
        )
    except Exception as e:
        logger.warning(f"Could not save test result: {e}")

    if result["success"]:
        server_info = result.get("server_info", {})
        message = result.get("message", "Connection successful")
        server_title = server_info.get("serverTitle", "JIRA Server")
        version = server_info.get("version", "unknown")
        response_time = result.get("response_time_ms", 0)

        toast = create_success_toast(
            f"Server: {server_title} | Version: {version} | "
            f"Response: {response_time}ms. "
            "Click 'Save Configuration' to persist.",
            header=message,
            duration=6000,
        )

        return "", toast
    else:
        error_code = result.get("error_code", "")
        is_version_mismatch = error_code == "api_version_mismatch"

        error_message = result.get("message", "Connection Failed")
        error_details = result.get("error_details", "No additional details available")

        if is_version_mismatch:
            toast = create_warning_toast(
                error_details,
                header=error_message,
                duration=6000,
            )
        else:
            toast = create_error_toast(
                error_details,
                header=error_message,
                duration=6000,
            )

        return "", toast


@callback(
    [
        Output("jira-config-modal", "is_open", allow_duplicate=True),
        Output("jira-save-status", "children"),
        Output("jira-config-save-trigger", "data"),
        Output("app-notifications", "children", allow_duplicate=True),
    ],
    Input("jira-config-save-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value"),
        State("jira-cache-size-input", "value"),
        State("jira-max-results-input", "value"),
        State("jira-config-save-trigger", "data"),
    ],
    prevent_initial_call=True,
)
def save_jira_configuration_callback(
    n_clicks,
    base_url,
    api_version,
    token,
    cache_size,
    max_results,
    current_trigger,
):

    if not n_clicks:
        raise PreventUpdate

    ctx_triggered = ctx.triggered_id
    if ctx_triggered != "jira-config-save-button":
        raise PreventUpdate

    try:
        config = {
            "base_url": base_url.strip() if base_url else "",
            "api_version": api_version,
            "token": token.strip() if token else "",
            "cache_size_mb": int(cache_size) if cache_size else 100,
            "max_results_per_call": int(max_results) if max_results else 100,
            "configured": True,
        }

        is_valid, error_msg = validate_jira_config(config)
        if not is_valid:
            logger.warning(f"Invalid JIRA configuration: {error_msg}")
            return (
                no_update,
                "",
                no_update,
                create_error_toast(error_msg, header="Validation Error"),
            )

        cache_warning_toast = None
        if config["cache_size_mb"] > 500:
            cache_warning_toast = create_warning_toast(
                f"{config['cache_size_mb']}MB may impact disk space. "
                "Consider reducing if you experience storage issues.",
                header="High Cache Size",
            )
            logger.info(
                f"Warning: High cache size configured: {config['cache_size_mb']}MB"
            )

        try:
            existing_config = load_jira_configuration()
            for key in ["last_test_timestamp", "last_test_success", "points_field"]:
                if key in existing_config and key not in config:
                    config[key] = existing_config[key]
        except Exception as e:
            logger.debug(f"Could not preserve existing fields: {e}")

        success = save_jira_configuration(config)

        if success:
            logger.info("JIRA configuration saved successfully")
            toast = create_success_toast(
                "JIRA settings have been saved successfully.",
                header="Configuration Saved",
            )

            new_trigger = (current_trigger or 0) + 1

            if cache_warning_toast:
                return (
                    False,
                    "",
                    new_trigger,
                    html.Div([toast, cache_warning_toast]),
                )
            else:
                return (False, "", new_trigger, toast)
        else:
            logger.error("Failed to save JIRA configuration")
            return (
                no_update,
                "",
                no_update,
                create_error_toast(
                    "An error occurred while saving the configuration. "
                    "Please try again.",
                    header="Save Failed",
                ),
            )

    except Exception as e:
        logger.error(f"Exception while saving JIRA configuration: {e}")
        return (
            no_update,
            "",
            no_update,
            create_error_toast(f"Error: {str(e)}", header="Unexpected Error"),
        )


@callback(
    Output("jira-config-modal", "is_open", allow_duplicate=True),
    Input("jira-config-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_jira_config(n_clicks):

    if n_clicks:
        logger.info("JIRA configuration modal cancelled")
        return False
    return no_update


@callback(
    Output("jira-config-status-indicator", "children"),
    [
        Input("jira-config-modal", "is_open"),
        Input("jira-config-save-button", "n_clicks"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=False,
)
def update_jira_config_status(modal_is_open, save_clicks, profile_id):

    import time  # noqa: PLC0415

    try:
        if ctx.triggered and ctx.triggered[0]["prop_id"] == "profile-selector.value":
            time.sleep(0.1)

        jira_config = load_jira_configuration()

        is_configured = (
            jira_config.get("configured", False)
            and jira_config.get("base_url", "").strip() != ""
        )

        if is_configured:
            base_url = jira_config.get("base_url", "")
            api_version = jira_config.get("api_version", "v2")
            token = jira_config.get("token", "")

            logger.info(
                "Status indicator: Testing connection to "
                f"{base_url} with API {api_version}"
            )
            test_result = test_jira_connection(base_url, token, api_version)
            logger.info(
                "Status indicator: Test result - "
                f"success={test_result['success']}, "
                f"error_code={test_result.get('error_code', 'none')}"
            )

            if (
                not test_result["success"]
                and test_result.get("error_code") == "api_version_mismatch"
            ):
                opposite_version = "v2" if api_version == "v3" else "v3"
                return html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle text-warning me-2"
                        ),
                        html.Span(
                            f"[WARN] API {api_version} not supported - "
                            f"Switch to {opposite_version} in Configure JIRA",
                            className="text-warning small fw-bold",
                        ),
                    ],
                    className="d-flex align-items-center",
                )

            if not test_result["success"]:
                return html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle text-danger me-2"),
                        html.Span(
                            "JIRA Connection Error - "
                            f"{test_result.get('message', 'Unknown error')}",
                            className="text-danger small",
                        ),
                    ],
                    className="d-flex align-items-center",
                )

            try:
                parsed = urlparse(base_url)
                domain = parsed.netloc if parsed.netloc else base_url
            except Exception:
                domain = base_url

            return html.Div(
                [
                    html.I(className="fas fa-check-circle text-success me-2"),
                    html.Span(
                        f"Connected: {domain}",
                        className="text-success small",
                        title=f"Full URL: {base_url} (API {api_version})",
                    ),
                ],
                className="d-flex align-items-center",
                style={"overflow": "hidden", "textOverflow": "ellipsis"},
            )
        else:
            return html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                    html.Span(
                        "Configure JIRA to begin",
                        className="text-muted small",
                    ),
                ],
                className="d-flex align-items-center",
            )

    except Exception as e:
        logger.error(f"Error loading JIRA configuration status: {e}", exc_info=True)
        return html.Div(
            [
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                html.Span(
                    f"Error: {str(e)}",
                    className="text-danger small",
                ),
            ],
            className="d-flex align-items-center",
        )


@callback(
    Output("jira-last-test-display", "children"),
    Input("jira-config-modal", "is_open"),
)
def display_last_test_info(is_open):

    if not is_open:
        raise PreventUpdate

    try:
        config = load_jira_configuration()
        last_test_timestamp = config.get("last_test_timestamp")
        last_test_success = config.get("last_test_success")

        if last_test_timestamp is None:
            return html.Div()

        try:
            dt = datetime.fromisoformat(last_test_timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_time = last_test_timestamp

        if last_test_success:
            icon = "fas fa-check-circle"
            color = "success"
            status_text = "Successful"
        else:
            icon = "fas fa-exclamation-circle"
            color = "warning"
            status_text = "Failed"

        return dbc.Alert(
            html.Div(
                [
                    html.I(className=f"{icon} me-2"),
                    html.Span(
                        [
                            html.Span(
                                f"Last test: {formatted_time} — ", className="fw-bold"
                            ),
                            html.Span(status_text),
                        ]
                    ),
                ],
                className="d-flex align-items-center",
            ),
            color=color,
            className="small",
        )
    except Exception as e:
        logger.debug(f"Could not load last test info: {e}")
        return html.Div()


@callback(
    Output("jira-api-version-warning", "children"),
    Input("jira-api-version-select", "value"),
    State("jira-config-modal", "is_open"),
)
def show_api_version_warning(selected_version, is_open):

    if not is_open:
        raise PreventUpdate

    try:
        config = load_jira_configuration()
        current_version = config.get("api_version", "v3")

        if selected_version != current_version:
            opposite_version = "v2" if selected_version == "v3" else "v3"

            return dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        html.Span(
                            [
                                html.Strong("API Version Change"),
                                html.Br(),
                                html.Small(
                                    f"Switching from {opposite_version} "
                                    f"to {selected_version}. "
                                    "The API endpoint will be updated automatically. "
                                    "Test the connection after saving "
                                    "to verify compatibility.",
                                    style={"opacity": "0.85"},
                                ),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="info",
                dismissable=True,
                className="small",
            )
        else:
            return html.Div()
    except Exception as e:
        logger.debug(f"Could not load config for version warning: {e}")
        return html.Div()
