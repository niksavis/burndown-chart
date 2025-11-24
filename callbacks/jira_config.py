"""
JIRA Configuration Callbacks

This module handles all callback logic for the JIRA configuration modal.
It provides callbacks for opening/closing the modal, loading/saving configuration,
and testing JIRA connections.

Feature: 003-jira-config-separation
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import callback, Output, Input, State, no_update, html, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from data.persistence import (
    load_jira_configuration,
    save_jira_configuration,
    validate_jira_config,
)
from data.jira_simple import test_jira_connection
from configuration import logger


#######################################################################
# CALLBACK: OPEN MODAL
#######################################################################


@callback(
    Output("jira-config-modal", "is_open"),
    Input("jira-config-button", "n_clicks"),
    prevent_initial_call=True,
)
def open_jira_config_modal(n_clicks):
    """
    Open JIRA configuration modal when user clicks the configuration button.

    Args:
        n_clicks: Number of times the button has been clicked

    Returns:
        True to open the modal, no_update otherwise
    """
    if n_clicks:
        logger.info("Opening JIRA configuration modal")
        return True
    return no_update


#######################################################################
# CALLBACK: LOAD CONFIGURATION
#######################################################################


@callback(
    [
        Output("jira-base-url-input", "value"),
        Output("jira-api-version-select", "value"),
        Output("jira-token-input", "value"),
        Output("jira-cache-size-input", "value"),
        Output("jira-max-results-input", "value"),
        Output("jira-points-field-input", "value"),
    ],
    Input("jira-config-modal", "is_open"),
)
def load_jira_config(is_open):
    """
    Load and display existing JIRA configuration when modal opens.

    Args:
        is_open: Whether the modal is currently open

    Returns:
        Tuple of (base_url, api_version, token, cache_size, max_results, points_field)
    """
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
            config.get("points_field", "customfield_10016"),
        )
    except Exception as e:
        logger.error(f"Error loading JIRA configuration: {e}")
        # Return defaults on error
        return ("", "v3", "", 100, 100, "customfield_10016")


#######################################################################
# CALLBACK: TEST CONNECTION
#######################################################################


@callback(
    Output("jira-connection-status", "children"),
    Input("jira-test-connection-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value"),
    ],
    prevent_initial_call=True,
)
def test_jira_connection_callback(n_clicks, base_url, api_version, token):
    """
    Test JIRA connection and display result feedback.

    Args:
        n_clicks: Number of times test button has been clicked
        base_url: JIRA base URL
        api_version: API version (v2 or v3)
        token: Personal access token

    Returns:
        Alert component with success or error message
    """
    if not n_clicks:
        raise PreventUpdate

    # Validate required fields (only base_url is required, token is optional for public servers)
    if not base_url:
        return dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Span(
                        [
                            html.Strong("Missing Required Field"),
                            html.Br(),
                            "Please fill in the JIRA Base URL before testing the connection.",
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="warning",
            dismissable=True,
        )

    # Call test function (token is optional)
    logger.info(f"Testing JIRA connection to {base_url} (authenticated: {bool(token)})")
    result = test_jira_connection(
        base_url.strip(), token.strip() if token else "", api_version
    )

    # Save test result to configuration (T025 - User Story 2)
    try:
        config = load_jira_configuration()
        config["last_test_timestamp"] = result.get("timestamp")
        config["last_test_success"] = result["success"]
        save_jira_configuration(config)
        logger.debug(
            f"Saved test result: success={result['success']}, timestamp={result.get('timestamp')}"
        )
    except Exception as e:
        logger.warning(f"Could not save test result: {e}")

    if result["success"]:
        server_info = result.get("server_info", {})
        message = result.get("message", "Connection successful")
        return dbc.Alert(
            html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    html.Div(
                        [
                            html.Strong(message),
                            html.Br(),
                            html.Small(
                                [
                                    f"Server: {server_info.get('serverTitle', 'JIRA Server')}",
                                    html.Br(),
                                    f"Version: {server_info.get('version', 'unknown')}",
                                    html.Br(),
                                    f"Response time: {result.get('response_time_ms', 0)}ms",
                                ],
                                className="d-block mb-2",
                                style={"opacity": "0.85"},
                            ),
                            html.Small(
                                [
                                    html.I(className="fas fa-info-circle me-1"),
                                    "Click ",
                                    html.Strong('"Save Configuration"'),
                                    " below to persist these settings.",
                                ],
                                className="text-muted fst-italic",
                                style={"fontSize": "0.85rem"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="success",
            dismissable=True,
            duration=8000,  # Extended to 8 seconds to give time to read the save reminder
        )
    else:
        # Check if this is an API version mismatch error
        error_code = result.get("error_code", "")
        is_version_mismatch = error_code == "api_version_mismatch"

        return dbc.Alert(
            html.Div(
                [
                    html.I(
                        className="fas fa-exclamation-triangle me-2"
                        if is_version_mismatch
                        else "fas fa-exclamation-circle me-2"
                    ),
                    html.Span(
                        [
                            html.Strong(result.get("message", "Connection Failed")),
                            html.Br(),
                            html.Small(
                                result.get(
                                    "error_details", "No additional details available"
                                ),
                                style={"opacity": "0.85"},
                            ),
                        ]
                    ),
                ],
                className="d-flex align-items-start",
            ),
            color="warning" if is_version_mismatch else "danger",
            dismissable=True,
        )


#######################################################################
# CALLBACK: SAVE CONFIGURATION
#######################################################################


@callback(
    [
        Output("jira-config-modal", "is_open", allow_duplicate=True),
        Output("jira-save-status", "children"),
    ],
    Input("jira-config-save-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value"),
        State("jira-cache-size-input", "value"),
        State("jira-max-results-input", "value"),
        State("jira-points-field-input", "value"),
    ],
    prevent_initial_call=True,
)
def save_jira_configuration_callback(
    n_clicks, base_url, api_version, token, cache_size, max_results, points_field
):
    """
    Validate and save JIRA configuration to app_settings.json.

    Args:
        n_clicks: Number of times save button has been clicked
        base_url: JIRA base URL
        api_version: API version (v2 or v3)
        token: Personal access token
        cache_size: Cache size limit in MB
        max_results: Maximum results per API call
        points_field: Custom field ID for story points

    Returns:
        Tuple of (modal_is_open, status_message)
    """
    if not n_clicks:
        raise PreventUpdate

    try:
        # Build configuration object
        config = {
            "base_url": base_url.strip() if base_url else "",
            "api_version": api_version,
            "token": token.strip() if token else "",
            "cache_size_mb": int(cache_size) if cache_size else 100,
            "max_results_per_call": int(max_results) if max_results else 100,
            "points_field": points_field.strip()
            if points_field
            else "customfield_10016",
            "configured": True,
        }

        # Validate configuration
        is_valid, error_msg = validate_jira_config(config)
        if not is_valid:
            logger.warning(f"Invalid JIRA configuration: {error_msg}")
            return (
                no_update,
                dbc.Alert(
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-circle me-2"),
                            html.Span(
                                [
                                    html.Strong("Validation Error"),
                                    html.Br(),
                                    html.Small(error_msg, style={"opacity": "0.85"}),
                                ]
                            ),
                        ],
                        className="d-flex align-items-start",
                    ),
                    color="danger",
                    dismissable=True,
                ),
            )

        # Warn about high cache sizes (T026 - User Story 2)
        cache_warning = None
        if config["cache_size_mb"] > 500:
            cache_warning = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        html.Span(
                            [
                                html.Strong("High Cache Size"),
                                html.Br(),
                                html.Small(
                                    f"{config['cache_size_mb']}MB may impact disk space. "
                                    "Consider reducing if you experience storage issues.",
                                    style={"opacity": "0.85"},
                                ),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="warning",
                dismissable=True,
                className="mb-2",
            )
            logger.info(
                f"Warning: High cache size configured: {config['cache_size_mb']}MB"
            )

        # Preserve existing fields not in form (T027 - User Story 2)
        try:
            existing_config = load_jira_configuration()
            # Preserve fields like last_test_timestamp, last_test_success
            for key in ["last_test_timestamp", "last_test_success"]:
                if key in existing_config and key not in config:
                    config[key] = existing_config[key]
        except Exception as e:
            logger.debug(f"Could not preserve existing fields: {e}")

        # Save configuration
        success = save_jira_configuration(config)

        if success:
            logger.info("JIRA configuration saved successfully")
            # Keep modal open, show success message with auto-dismiss
            success_message = dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-check-circle me-2"),
                        html.Span(
                            [
                                html.Strong("Configuration Saved"),
                                html.Br(),
                                html.Small(
                                    "JIRA settings have been saved successfully.",
                                    style={"opacity": "0.85"},
                                ),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="success",
                dismissable=True,
                duration=4000,  # Auto-dismiss after 4 seconds
            )

            # Combine success message with cache warning if present
            if cache_warning:
                return (no_update, html.Div([success_message, cache_warning]))
            else:
                return (no_update, success_message)
        else:
            logger.error("Failed to save JIRA configuration")
            return (
                no_update,
                dbc.Alert(
                    html.Div(
                        [
                            html.I(className="fas fa-exclamation-circle me-2"),
                            html.Span(
                                [
                                    html.Strong("Save Failed"),
                                    html.Br(),
                                    html.Small(
                                        "An error occurred while saving the configuration. Please try again.",
                                        style={"opacity": "0.85"},
                                    ),
                                ]
                            ),
                        ],
                        className="d-flex align-items-start",
                    ),
                    color="danger",
                    dismissable=True,
                ),
            )

    except Exception as e:
        logger.error(f"Exception while saving JIRA configuration: {e}")
        return (
            no_update,
            dbc.Alert(
                html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle me-2"),
                        html.Span(
                            [
                                html.Strong("Unexpected Error"),
                                html.Br(),
                                html.Small(
                                    f"Error: {str(e)}", style={"opacity": "0.85"}
                                ),
                            ]
                        ),
                    ],
                    className="d-flex align-items-start",
                ),
                color="danger",
                dismissable=True,
            ),
        )


#######################################################################
# CALLBACK: CANCEL CONFIGURATION
#######################################################################


@callback(
    Output("jira-config-modal", "is_open", allow_duplicate=True),
    Input("jira-config-cancel-button", "n_clicks"),
    prevent_initial_call=True,
)
def cancel_jira_config(n_clicks):
    """
    Close the JIRA configuration modal without saving changes.

    Args:
        n_clicks: Number of times cancel button has been clicked

    Returns:
        False to close the modal, no_update otherwise
    """
    if n_clicks:
        logger.info("JIRA configuration modal cancelled")
        return False
    return no_update


#######################################################################
# CALLBACK: UPDATE CONFIGURATION STATUS INDICATOR
#######################################################################


@callback(
    Output("jira-config-status-indicator", "children"),
    [
        Input("jira-config-modal", "is_open"),
        Input("jira-config-save-button", "n_clicks"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=False,  # Run on page load to show initial status
)
def update_jira_config_status(modal_is_open, save_clicks, profile_id):
    """
    Update the JIRA configuration status indicator to show whether JIRA is configured.

    Args:
        modal_is_open: Whether the modal is currently open
        save_clicks: Number of times save button has been clicked (triggers refresh)
        profile_id: Active profile ID (triggers refresh on profile switch)

    Returns:
        Status indicator component showing configuration state
    """
    from data.persistence import load_jira_configuration
    import time

    try:
        # If triggered by profile switch, wait briefly for switch to complete
        if ctx.triggered and ctx.triggered[0]["prop_id"] == "profile-selector.value":
            time.sleep(0.1)  # 100ms delay to let profile switch complete

        jira_config = load_jira_configuration()

        # Check if JIRA is configured (has base_url, token is optional for public servers)
        is_configured = (
            jira_config.get("configured", False)
            and jira_config.get("base_url", "").strip() != ""
        )

        if is_configured:
            base_url = jira_config.get("base_url", "")
            api_version = jira_config.get("api_version", "v3")
            token = jira_config.get("token", "")

            # Test the connection to verify API version actually works
            from data.jira_simple import test_jira_connection

            logger.info(
                f"Status indicator: Testing connection to {base_url} with API {api_version}"
            )
            test_result = test_jira_connection(base_url, token, api_version)
            logger.info(
                f"Status indicator: Test result - success={test_result['success']}, error_code={test_result.get('error_code', 'none')}"
            )

            # If connection test failed due to API version mismatch, show warning
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
                            f"[WARN] API {api_version} not supported - Switch to {opposite_version} in Configure JIRA",
                            className="text-warning small fw-bold",
                        ),
                    ],
                    className="d-flex align-items-center",
                )

            # If connection test failed for other reasons, show error
            if not test_result["success"]:
                return html.Div(
                    [
                        html.I(className="fas fa-exclamation-circle text-danger me-2"),
                        html.Span(
                            f"JIRA Connection Error - {test_result.get('message', 'Unknown error')}",
                            className="text-danger small",
                        ),
                    ],
                    className="d-flex align-items-center",
                )

            # Connection successful - show green status with shortened URL
            # Extract domain from URL for more compact display
            try:
                from urllib.parse import urlparse

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


#######################################################################
# CALLBACK: TEST CONNECTION
#######################################################################


@callback(
    Output("jira-last-test-display", "children"),
    Input("jira-config-modal", "is_open"),
)
def display_last_test_info(is_open):
    """
    Display last connection test timestamp and result.

    Args:
        is_open: Whether the modal is currently open

    Returns:
        Component showing last test information or empty div
    """
    if not is_open:
        raise PreventUpdate

    try:
        config = load_jira_configuration()
        last_test_timestamp = config.get("last_test_timestamp")
        last_test_success = config.get("last_test_success")

        if last_test_timestamp is None:
            return html.Div()  # No test history yet

        # Format the timestamp
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(last_test_timestamp.replace("Z", "+00:00"))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            formatted_time = last_test_timestamp

        # Determine status icon and color
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
        return html.Div()  # Silently return empty if error


#######################################################################
# CALLBACK: SHOW API VERSION WARNING
#######################################################################


@callback(
    Output("jira-api-version-warning", "children"),
    Input("jira-api-version-select", "value"),
    State("jira-config-modal", "is_open"),
)
def show_api_version_warning(selected_version, is_open):
    """
    Display warning when user changes API version.

    Args:
        selected_version: Currently selected API version (v2 or v3)
        is_open: Whether the modal is currently open

    Returns:
        Warning alert or empty div
    """
    if not is_open:
        raise PreventUpdate

    try:
        config = load_jira_configuration()
        current_version = config.get("api_version", "v3")

        # Show warning if version changed from saved config
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
                                    f"Switching from {opposite_version} to {selected_version}. "
                                    "The API endpoint will be updated automatically. "
                                    "Test the connection after saving to verify compatibility.",
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
            return html.Div()  # No change, no warning
    except Exception as e:
        logger.debug(f"Could not load config for version warning: {e}")
        return html.Div()


#######################################################################
# NOTE: Auto-dismiss alerts (4-second duration) provide clean UX
#       without needing explicit clear-on-close callback
#######################################################################
