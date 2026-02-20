"""
Error Handling Utilities

This module provides standardized error handling functions for consistent error
management across the application.
"""

import logging
import traceback
from collections.abc import Callable
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

# Configure logger
logger = logging.getLogger(__name__)


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """
    Log an error with consistent formatting and context information.

    Args:
        error: The exception that occurred
        context: Additional context information about where/why the error occurred
    """
    error_message = f"ERROR: {type(error).__name__}: {str(error)}"

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_message = f"{error_message} [Context: {context_str}]"

    logger.error(error_message)
    logger.debug(traceback.format_exc())


def create_error_component(
    error_message: str = "An error occurred",
    error_details: str | None = None,
    retry_callback: Callable | None = None,
    component_id: str | None = None,
    severity: str = "danger",
) -> html.Div:
    """
    Create a standardized error component for UI error display.

    Args:
        error_message: User-friendly error message
        error_details: Technical details (shown in collapsible section)
        retry_callback: Function to call if user clicks retry
        component_id: ID for the error component
        severity: Alert severity (danger, warning, info)

    Returns:
        A Dash component displaying the error
    """
    # Create the children list for the alert
    children = [
        html.H4(
            [html.I(className="fas fa-exclamation-triangle me-2"), "Error"],
            className="alert-heading mb-2",
        ),
        html.P(error_message, className="mb-2"),
    ]

    # Add error details if provided
    if error_details:
        collapse_id = (
            f"{component_id}-collapse" if component_id else "error-details-collapse"
        )
        button_id = f"{component_id}-toggle" if component_id else "error-details-toggle"

        children.extend(
            [
                html.Hr(className="my-2"),
                dbc.Button(
                    "Show Technical Details",
                    id=button_id,
                    color="link",
                    size="sm",
                    className="p-0 text-decoration-none",
                ),
                dbc.Collapse(
                    dbc.Card(
                        dbc.CardBody(
                            html.Pre(error_details, className="small text-muted mb-0")
                        ),
                        className="mt-2 border-0 bg-light",
                    ),
                    id=collapse_id,
                    is_open=False,
                ),
            ]
        )

    # Add retry button if callback provided
    if retry_callback:
        retry_id = f"{component_id}-retry" if component_id else "error-retry-button"
        retry_button = dbc.Button(
            [html.I(className="fas fa-redo-alt me-1"), "Retry"],
            id=retry_id,
            color="primary",
            size="sm",
            className="mt-2",
        )
        children.append(retry_button)

    # Create the alert with all children
    alert = dbc.Alert(
        children,
        color=severity,
        className="mb-3",
    )

    # Return the error component
    return html.Div(alert, id=component_id, className="error-container")


def try_except_callback(callback_fn: Callable) -> Callable:
    """
    Decorator for Dash callbacks to standardize error handling.

    Args:
        callback_fn: The callback function to wrap with error handling

    Returns:
        Wrapped function with error handling
    """

    def wrapper(*args, **kwargs):
        try:
            return callback_fn(*args, **kwargs)
        except Exception as e:
            log_error(e, {"callback": callback_fn.__name__, "args": args})
            return create_error_component(
                error_message="An error occurred while processing your request.",
                error_details=str(e),
            )

    return wrapper
