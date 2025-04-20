"""
Error handling examples for the Burndown Chart application.

This module demonstrates how to use the standardized error handling components
from ui.error_states in callbacks for form validation, empty states, and error recovery.
"""

import dash
from dash import Input, Output, State, html, callback_context, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from ui.error_states import (
    create_error_alert,
    create_validation_message,
    create_form_field_with_validation,
    create_empty_state,
    create_error_boundary,
    create_error_recovery_button,
)
from ui.components import create_button
import logging

logger = logging.getLogger(__name__)


def register(app):
    """
    Register error handling callbacks with the application.

    Args:
        app: The Dash application instance
    """

    @app.callback(
        [
            Output("demo-form-validation-result", "children"),
            Output("demo-input-name", "valid"),
            Output("demo-input-name", "invalid"),
            Output("demo-name-feedback", "children"),
            Output("demo-name-feedback", "className"),
            Output("demo-input-email", "valid"),
            Output("demo-input-email", "invalid"),
            Output("demo-email-feedback", "children"),
            Output("demo-email-feedback", "className"),
        ],
        [Input("demo-form-submit", "n_clicks")],
        [
            State("demo-input-name", "value"),
            State("demo-input-email", "value"),
        ],
        prevent_initial_call=True,
    )
    def validate_form_demo(n_clicks, name, email):
        """
        Validate form inputs and display appropriate error messages.

        Args:
            n_clicks: Number of clicks on submit button
            name: Name input value
            email: Email input value

        Returns:
            Form validation results and feedback
        """
        # Initialize variables for validation results
        name_valid, name_invalid, name_feedback = False, False, ""
        email_valid, email_invalid, email_feedback = False, False, ""
        result = None

        # Check if the form was submitted
        if n_clicks is None:
            # Initial load - no validation yet
            return no_update, False, False, "", "d-none", False, False, "", "d-none"

        # Validate name
        if not name or len(name.strip()) < 3:
            name_invalid = True
            name_feedback = "Name must be at least 3 characters"
            name_feedback_class = "form-text text-danger small d-block"
        else:
            name_valid = True
            name_feedback_class = "d-none"

        # Validate email
        if not email or "@" not in email or "." not in email:
            email_invalid = True
            email_feedback = "Please enter a valid email address"
            email_feedback_class = "form-text text-danger small d-block"
        else:
            email_valid = True
            email_feedback_class = "d-none"

        # If all inputs are valid, show success message
        if name_valid and email_valid:
            result = create_error_alert(
                "Form submitted successfully!",
                severity="success",
                dismissable=True,
                icon=True,
            )
        else:
            # Show form error summary
            result = create_error_alert(
                "Please fix the errors in the form before submitting.",
                title="Validation Error",
                severity="danger",
                dismissable=True,
            )

        return (
            result,
            name_valid,
            name_invalid,
            name_feedback,
            name_feedback_class,
            email_valid,
            email_invalid,
            email_feedback,
            email_feedback_class,
        )

    @app.callback(
        Output("demo-empty-state-container", "children"),
        [Input("demo-empty-state-selector", "value")],
    )
    def show_empty_state_demo(empty_state_type):
        """
        Show different types of empty states based on selection.

        Args:
            empty_state_type: The type of empty state to show

        Returns:
            Empty state component
        """
        if empty_state_type == "default":
            return create_empty_state(
                message="No data is currently available.",
                title="No Data",
                icon="fas fa-inbox",
                action_button=create_button(
                    "Add Data",
                    id="demo-add-data-btn",
                    variant="primary",
                    icon_class="fas fa-plus",
                ),
                variant="default",
            )
        elif empty_state_type == "search":
            return create_empty_state(
                message="Your search returned no results. Please try different search terms.",
                title="No Results Found",
                icon="fas fa-search",
                action_button=create_button(
                    "Clear Search",
                    id="demo-clear-search-btn",
                    variant="secondary",
                    icon_class="fas fa-times",
                ),
                variant="info",
            )
        elif empty_state_type == "error":
            return create_empty_state(
                message="An error occurred while loading the data. Please try again.",
                title="Error Loading Data",
                icon="fas fa-exclamation-triangle",
                action_button=create_error_recovery_button(
                    id="demo-retry-btn",
                    text="Try Again",
                ),
                variant="error",
            )
        elif empty_state_type == "filter":
            return create_empty_state(
                message="No data matches the current filters. Try adjusting your filters to see results.",
                title="No Matching Data",
                icon="fas fa-filter",
                action_button=create_button(
                    "Reset Filters",
                    id="demo-reset-filters-btn",
                    variant="secondary",
                    icon_class="fas fa-redo",
                ),
                variant="warning",
            )
        else:
            # Default empty state
            return create_empty_state(
                message="Select an empty state type from the dropdown above to see examples.",
                title="Empty State Examples",
                icon="fas fa-info-circle",
                variant="default",
            )

    @app.callback(
        Output("demo-error-recovery-result", "children"),
        [
            Input("demo-trigger-error-btn", "n_clicks"),
            Input("demo-retry-load-btn", "n_clicks"),
        ],
        prevent_initial_call=True,
    )
    def demonstrate_error_recovery(error_clicks, retry_clicks):
        """
        Demonstrate error recovery with retry mechanism.

        Args:
            error_clicks: Clicks on trigger error button
            retry_clicks: Clicks on retry button

        Returns:
            Error recovery UI component
        """
        ctx = callback_context
        triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == "demo-trigger-error-btn":
            # Simulate a failed data load
            error_component = html.Div(
                [
                    create_error_alert(
                        "Failed to load data from the server. The server might be unavailable or the data might be corrupted.",
                        title="Data Load Error",
                        severity="danger",
                    ),
                    html.Div(
                        [
                            create_error_recovery_button(
                                id="demo-retry-load-btn",
                                text="Retry Loading Data",
                                icon="fas fa-sync",
                            ),
                            create_button(
                                "Contact Support",
                                id="demo-support-btn",
                                variant="outline-secondary",
                                icon_class="fas fa-headset",
                                className="ms-2",
                            ),
                        ],
                        className="mt-3 d-flex",
                    ),
                ]
            )

            return error_component

        elif triggered_id == "demo-retry-load-btn":
            # Simulate successful retry
            success_component = html.Div(
                [
                    create_error_alert(
                        "Data loaded successfully after retry!",
                        severity="success",
                    ),
                    html.Div(
                        dbc.Table(
                            [
                                html.Thead(
                                    html.Tr(
                                        [
                                            html.Th("ID"),
                                            html.Th("Name"),
                                            html.Th("Value"),
                                        ]
                                    )
                                ),
                                html.Tbody(
                                    [
                                        html.Tr(
                                            [
                                                html.Td("1"),
                                                html.Td("Item 1"),
                                                html.Td("42"),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("2"),
                                                html.Td("Item 2"),
                                                html.Td("37"),
                                            ]
                                        ),
                                        html.Tr(
                                            [
                                                html.Td("3"),
                                                html.Td("Item 3"),
                                                html.Td("23"),
                                            ]
                                        ),
                                    ]
                                ),
                            ],
                            bordered=True,
                            hover=True,
                            responsive=True,
                            className="mt-3",
                        ),
                        className="mt-3",
                    ),
                ]
            )

            return success_component

        # Default state
        return html.P(
            "Click 'Trigger Error' to simulate a data loading error and see recovery options."
        )
