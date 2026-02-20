"""
JIRA Scope Calculation Callback

Handles project scope calculation from JIRA issues.
"""

from datetime import datetime

from dash import Input, State, html, no_update
from dash.exceptions import PreventUpdate

from configuration import logger


def register(app):
    """Register JIRA scope calculation callback.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [],
        [Input("jira-scope-calculate-btn", "n_clicks")],
        [State("jira-jql-query", "value")],
        prevent_initial_call=True,
    )
    def calculate_jira_project_scope(n_clicks, jql_query):
        """
        Calculate project scope based on JIRA issues using status categories.

        Args:
            n_clicks: Number of clicks on calculate button
            jql_query: JQL query string

        Returns:
            Tuple: (
                status_content,
                time_content,
                estimated_items,
                total_items,
                estimated_points,
            )
        """
        if not n_clicks or n_clicks == 0:
            raise PreventUpdate

        try:
            # Load and validate JIRA configuration
            jira_config, ui_config = _load_and_validate_jira_config(jql_query)

            if jira_config is None:
                # Not configured - return error message
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                status_message = (
                    "[!] JIRA is not configured. Please click the "
                    "'Configure JIRA' button to set up your JIRA connection "
                    "before calculating project scope."
                )
                return (
                    html.Div(status_message, className="text-warning"),
                    f"Last attempt: {current_time}",
                    no_update,
                    no_update,
                    no_update,
                )

            # Calculate project scope from JIRA
            success, message, scope_data = _calculate_scope(jql_query, ui_config)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if success:
                return _handle_success(scope_data, jira_config, current_time)
            else:
                return _handle_error(message, current_time)

        except Exception as e:
            logger.error(f"[Scope] Error in JIRA scope calculation callback: {e}")
            return _handle_exception(e)


def _load_and_validate_jira_config(jql_query: str) -> tuple:
    """Load and validate JIRA configuration.

    Args:
        jql_query: JQL query string

    Returns:
        Tuple of (jira_config dict or None, ui_config dict)
    """
    from data.jira import construct_jira_endpoint
    from data.persistence import load_jira_configuration

    jira_config = load_jira_configuration()

    # Check if JIRA is configured
    is_configured = (
        jira_config.get("configured", False)
        and jira_config.get("base_url", "").strip() != ""
    )

    if not is_configured:
        return None, {}

    # Build UI config from loaded jira_config
    base_url = jira_config.get("base_url", "https://jira.atlassian.com")
    api_version = jira_config.get("api_version", "v2")

    ui_config = {
        "jql_query": jql_query or "",
        "api_endpoint": construct_jira_endpoint(base_url, api_version),
        "token": jira_config.get("token", ""),
        "story_points_field": jira_config.get("points_field", ""),
        "cache_max_size_mb": jira_config.get("cache_size_mb", 100),
        "max_results": jira_config.get("max_results_per_call", 1000),
    }

    return jira_config, ui_config


def _calculate_scope(jql_query: str, ui_config: dict) -> tuple:
    """Calculate project scope from JIRA.

    Args:
        jql_query: JQL query string
        ui_config: UI configuration dictionary

    Returns:
        Tuple of (success, message, scope_data)
    """
    from data.persistence import calculate_project_scope_from_jira

    return calculate_project_scope_from_jira(jql_query, ui_config)


def _handle_success(scope_data: dict, jira_config: dict, current_time: str) -> tuple:
    """Handle successful scope calculation.

    Args:
        scope_data: Calculated scope data
        jira_config: JIRA configuration
        current_time: Current timestamp string

    Returns:
        Tuple of (
            status_content,
            time_content,
            estimated_items,
            total_items,
            estimated_points,
        )
    """
    project_scope = scope_data
    points_field_available = project_scope.get("points_field_available", False)

    if points_field_available:
        # Use proper calculated values when points field is available
        estimated_items = project_scope.get("estimated_items", 0)
        total_items = project_scope.get("remaining_items", 0)
        estimated_points = project_scope.get("estimated_points", 0)

        status_message = (
            f"Project scope calculated from JIRA with {estimated_items} "
            f"estimated items out of {total_items} total remaining items."
        )
        status_class = "text-success"
    else:
        # Points field not configured - fallback to item counts only
        estimated_items = 0
        total_items = project_scope.get("remaining_items", 0)
        estimated_points = 0

        points_field = jira_config.get("points_field", "")
        if points_field and points_field.strip():
            status_message = (
                f"[!] Points field '{points_field.strip()}' is configured but "
                f"no valid data found. Only total item count ({total_items}) "
                "calculated."
            )
        else:
            status_message = (
                "[!] No points field configured. "
                f"Only total item count ({total_items}) calculated. "
                "Configure a valid points field for full scope calculation."
            )
        status_class = "text-warning"

    status_content = html.Div(
        [
            html.I(className="fas fa-check-circle me-2 text-success"),
            html.Span(status_message, className=status_class),
        ],
        className="mb-2",
    )
    time_content = html.Small(f"Last updated: {current_time}", className="text-muted")

    logger.info(
        "[Scope] Using JIRA scope values: "
        f"{total_items} items, {estimated_points:.1f} points"
    )

    return (
        status_content,
        time_content,
        estimated_items,
        total_items,
        estimated_points,
    )


def _handle_error(message: str, current_time: str) -> tuple:
    """Handle scope calculation error.

    Args:
        message: Error message
        current_time: Current timestamp string

    Returns:
        Tuple of (status_content, time_content, no_update, no_update, no_update)
    """
    status_content = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            html.Span(f"Error: {message}", className="text-danger"),
        ],
        className="mb-2",
    )
    time_content = html.Small(f"Last attempt: {current_time}", className="text-muted")

    return (
        status_content,
        time_content,
        no_update,
        no_update,
        no_update,
    )


def _handle_exception(e: Exception) -> tuple:
    """Handle unexpected exception.

    Args:
        e: Exception object

    Returns:
        Tuple of (status_content, time_content, no_update, no_update, no_update)
    """
    error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    status_content = html.Div(
        [
            html.I(className="fas fa-exclamation-triangle me-2 text-danger"),
            html.Span(f"Unexpected error: {str(e)}", className="text-danger"),
        ],
        className="mb-2",
    )
    time_content = html.Small(f"Error at: {error_time}", className="text-muted")

    return status_content, time_content, no_update, no_update, no_update
