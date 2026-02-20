"""JQL Query Test Callback.

This module handles the JQL query validation and testing callback:
- Test JQL query validity against JIRA API
- ScriptRunner function detection and warnings
- Loading state management (clientside)

Related modules:
- data.jira: JIRA API integration and JQL testing
- data.persistence: JIRA configuration loading
"""

from __future__ import annotations

import logging
from typing import Any

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

# Get logger
logger = logging.getLogger(__name__)


def register(app: Any) -> None:
    """Register JQL query test callbacks.

    Args:
        app: Dash application instance
    """

    @app.callback(
        [
            Output("jql-test-results", "children"),
            Output("jql-test-results", "style"),
        ],
        [Input("test-jql-query-button", "n_clicks")],
        [State("jira-jql-query", "value")],
        prevent_initial_call=True,
    )
    def test_jql_query_validity(n_clicks: int | None, jql_query: str) -> tuple:
        """Test JQL query validity - useful for ScriptRunner function validation.

        Args:
            n_clicks: Number of button clicks
            jql_query: JQL query string to test

        Returns:
            Tuple of (results_html, results_style)
        """
        if not n_clicks:
            raise PreventUpdate

        if not jql_query or not jql_query.strip():
            return (
                html.Div(
                    [
                        html.I(
                            className="fas fa-exclamation-triangle me-2 text-primary"
                        ),
                        html.Span(
                            "Please enter a JQL query to test.", className="text-dark"
                        ),
                    ],
                    className="alert alert-info mb-0 border-primary",
                ),
                {"display": "block"},
            )

        try:
            from data.jira import test_jql_query, validate_jql_for_scriptrunner
            from data.persistence import load_jira_configuration

            # Load JIRA configuration
            loaded_jira_config = load_jira_configuration()

            # Check if JIRA is configured
            is_configured = (
                loaded_jira_config.get("configured", False)
                and loaded_jira_config.get("base_url", "").strip() != ""
            )

            if not is_configured:
                return _create_unconfigured_result()

            # Build JIRA config for testing
            jira_config = _build_jira_config(loaded_jira_config, jql_query)

            # Check for ScriptRunner function warnings
            is_compatible, scriptrunner_warning = validate_jql_for_scriptrunner(
                jql_query
            )

            # Test the query
            is_valid, test_message = test_jql_query(jira_config)

            if is_valid:
                return _create_success_result(
                    test_message, is_compatible, scriptrunner_warning
                )
            else:
                return _create_error_result(
                    test_message, is_compatible, scriptrunner_warning
                )

        except ImportError:
            return _create_import_error_result()
        except Exception as e:
            logger.error(f"Error testing JQL query: {e}")
            return _create_exception_result(str(e))

    # Clientside callback for Test Query button loading state
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks && n_clicks > 0) {
                setTimeout(function() {
                    const button = document.getElementById('test-jql-query-button');
                    const resultsArea = document.getElementById('jql-test-results');
                    
                    if (button) {
                        console.log('[JQL Test] Button clicked - setting lock to TRUE');
                        
                        // Lock test results to prevent hiding during test
                        if (typeof window.setJQLTestResultsLock === 'function') {
                            window.setJQLTestResultsLock(true);
                        }
                        
                        // Remove hidden class so Dash callback
                        // can show results
                        if (resultsArea) {
                            console.log(
                                '[JQL Test] Removing hidden class from results area'
                            );
                            resultsArea.className = resultsArea.className
                                .replace('jql-test-results-hidden', '')
                                .trim();
                        }
                        
                        // Set loading state
                        button.disabled = true;
                        button.innerHTML =
                            '<i class="fas fa-spinner fa-spin me-1"></i>Testing...';
                        
                        // Reset after timeout or when operation completes
                        const resetButton = function() {
                            if (button && button.disabled) {
                                button.disabled = false;
                                button.innerHTML =
                                    '<i class="fas fa-check-circle me-1"></i>' +
                                    '<span class="d-none d-sm-inline">' +
                                    'Test Query</span>';
                            }
                        };
                        
                        // Shorter timeout for test operations
                        setTimeout(resetButton, 5000);
                        
                        // Monitor for completion using children changes
                        const observer = new MutationObserver(function(mutations) {
                            if (resultsArea && resultsArea.children.length > 0) {
                                setTimeout(resetButton, 500);
                                observer.disconnect();
                            }
                        });
                        
                        if (resultsArea) {
                            observer.observe(resultsArea, { childList: true });
                        }
                    }
                }, 50);
            }
            return null;
        }
        """,
        Output("test-jql-query-button", "title"),
        [Input("test-jql-query-button", "n_clicks")],
        prevent_initial_call=True,
    )


# Helper functions


def _create_unconfigured_result() -> tuple:
    """Create result for unconfigured JIRA."""
    return (
        html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                html.Strong("JIRA Not Configured", className="text-dark"),
                html.Br(),
                html.Small(
                    "Please click the 'Configure JIRA' button above to set up your "
                    "JIRA connection before testing queries.",
                    className="text-dark opacity-75",
                ),
            ],
            className="alert alert-light border-warning mb-0",
        ),
        {"display": "block"},
    )


def _build_jira_config(loaded_jira_config: dict, jql_query: str) -> dict:
    """Build JIRA config for testing.

    Args:
        loaded_jira_config: Loaded JIRA configuration
        jql_query: JQL query string

    Returns:
        JIRA config dictionary
    """
    from data.jira import construct_jira_endpoint

    base_url = loaded_jira_config.get("base_url", "https://jira.atlassian.com")
    api_version = loaded_jira_config.get("api_version", "v2")

    return {
        "jql_query": jql_query.strip(),
        "api_endpoint": construct_jira_endpoint(base_url, api_version),
        "token": loaded_jira_config.get("token", ""),
        "story_points_field": loaded_jira_config.get("points_field", ""),
        "cache_max_size_mb": loaded_jira_config.get("cache_size_mb", 100),
        "max_results": loaded_jira_config.get("max_results_per_call", 1000),
    }


def _create_success_result(
    test_message: str, is_compatible: bool, scriptrunner_warning: str
) -> tuple:
    """Create success result display.

    Args:
        test_message: Test result message
        is_compatible: Whether query is compatible (no ScriptRunner functions)
        scriptrunner_warning: Warning message for ScriptRunner functions

    Returns:
        Tuple of (results_html, results_style)
    """
    if is_compatible:
        # Pure success: no ScriptRunner functions
        success_content = [
            html.I(className="fas fa-check-circle me-2 text-success"),
            html.Strong("JQL Query Valid", className="text-dark"),
            html.Br(),
            html.Small(test_message, className="text-dark opacity-75"),
        ]
        alert_class = "alert alert-light border-success mb-0"
    else:
        # Success with warning: ScriptRunner functions detected
        success_content = [
            html.I(className="fas fa-check-circle me-2 text-success"),
            html.Strong("JQL Query Valid", className="text-dark"),
            html.Br(),
            html.Small(test_message, className="text-dark opacity-75"),
            html.Br(),
            html.Br(),
            html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
            html.Strong("ScriptRunner Functions Detected", className="text-dark"),
            html.Br(),
            html.Small(scriptrunner_warning, className="text-dark opacity-75"),
        ]
        alert_class = "alert alert-light border-warning mb-0"

    return (
        html.Div(success_content, className=alert_class),
        {"display": "block"},
    )


def _create_error_result(
    test_message: str, is_compatible: bool, scriptrunner_warning: str
) -> tuple:
    """Create error result display.

    Args:
        test_message: Error message from test
        is_compatible: Whether query is compatible (no ScriptRunner functions)
        scriptrunner_warning: Warning message for ScriptRunner functions

    Returns:
        Tuple of (results_html, results_style)
    """
    error_content = [
        html.I(className="fas fa-times-circle me-2 text-danger"),
        html.Strong("JQL Query Invalid", className="text-dark"),
        html.Br(),
        html.Div(
            [
                html.Strong("JIRA API Error:", className="text-dark mt-2 d-block"),
                html.Code(
                    test_message,
                    className="text-dark d-block p-2 bg-light border rounded mt-1",
                ),
            ]
        ),
    ]

    # Add specific guidance for ScriptRunner issues
    if not is_compatible:
        error_content.extend(
            [
                html.Br(),
                html.Br(),
                html.I(className="fas fa-lightbulb me-2 text-primary"),
                html.Strong("ScriptRunner Functions Detected", className="text-dark"),
                html.Br(),
                html.Small(
                    "Your query contains ScriptRunner functions (issueFunction, "
                    "subtasksOf, epicsOf, etc.). These require the ScriptRunner "
                    "add-on to be installed on your JIRA instance. If the error "
                    "mentions 'function' or 'unknown function', ScriptRunner may "
                    "not be available.",
                    className="text-dark",
                ),
            ]
        )

    return (
        html.Div(error_content, className="alert alert-light border-danger mb-0"),
        {"display": "block"},
    )


def _create_import_error_result() -> tuple:
    """Create result for import error."""
    return (
        html.Div(
            [
                html.I(className="fas fa-exclamation-triangle me-2 text-secondary"),
                html.Span(
                    "JIRA integration not available - cannot test query.",
                    className="text-secondary",
                ),
            ],
            className="alert alert-light border-secondary mb-0",
        ),
        {"display": "block"},
    )


def _create_exception_result(error_message: str) -> tuple:
    """Create result for general exception.

    Args:
        error_message: Exception message

    Returns:
        Tuple of (results_html, results_style)
    """
    return (
        html.Div(
            [
                html.I(className="fas fa-times-circle me-2 text-danger"),
                html.Span(
                    f"Error testing query: {error_message}", className="text-dark"
                ),
            ],
            className="alert alert-light border-danger mb-0",
        ),
        {"display": "block"},
    )
