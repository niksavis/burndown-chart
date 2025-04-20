"""
Error states demonstration page.

This module provides a demonstration page for the error states components,
allowing developers to see and interact with the various error handling patterns.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from ui.error_states import (
    create_error_alert,
    create_validation_message,
    create_form_field_with_validation,
    create_empty_state,
    create_error_boundary,
    create_error_recovery_button,
)
from ui.components import create_button
from ui.styles import create_heading_style


def create_error_demo_layout():
    """
    Create a layout for demonstrating error state components.

    Returns:
        html.Div: The demo page layout
    """
    return html.Div(
        [
            html.H2("Error States Components", style=create_heading_style(2)),
            html.P(
                "This page demonstrates the standard error state components for "
                "consistent error handling across the application.",
                className="lead mb-4",
            ),
            # Section 1: Error Alerts
            html.Div(
                [
                    html.H3("Error Alerts", style=create_heading_style(3)),
                    html.P(
                        "Use error alerts to display feedback messages at the section level."
                    ),
                    html.Div(
                        [
                            create_error_alert(
                                "This is a standard error message.",
                                severity="danger",
                                icon=True,
                            ),
                            create_error_alert(
                                "This is a warning message with a title.",
                                title="Warning",
                                severity="warning",
                                icon=True,
                            ),
                            create_error_alert(
                                "This is an informational message that can be dismissed.",
                                severity="info",
                                dismissable=True,
                                icon=True,
                            ),
                            create_error_alert(
                                "This is a success message with icon.",
                                severity="success",
                                icon=True,
                            ),
                        ]
                    ),
                ],
                className="mb-5",
            ),
            # Section 2: Form Validation
            html.Div(
                [
                    html.H3("Form Validation", style=create_heading_style(3)),
                    html.P(
                        "Demonstrate form validation patterns with inline error messages."
                    ),
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.Div(id="demo-form-validation-result"),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Name",
                                                htmlFor="demo-input-name",
                                                className="form-label",
                                            ),
                                            dbc.Input(
                                                id="demo-input-name",
                                                placeholder="Enter your name",
                                                type="text",
                                            ),
                                            html.Div(
                                                id="demo-name-feedback",
                                                className="d-none",
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Email",
                                                htmlFor="demo-input-email",
                                                className="form-label",
                                            ),
                                            dbc.Input(
                                                id="demo-input-email",
                                                placeholder="Enter your email",
                                                type="email",
                                            ),
                                            html.Div(
                                                id="demo-email-feedback",
                                                className="d-none",
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    create_button(
                                        "Submit",
                                        id="demo-form-submit",
                                        variant="primary",
                                    ),
                                ]
                            ),
                        ],
                        className="mb-4",
                    ),
                    # Form with built-in validation component
                    html.H4(
                        "Form Fields with Built-in Validation",
                        style=create_heading_style(4),
                    ),
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    create_form_field_with_validation(
                                        field_id="demo-name-field",
                                        label="Name",
                                        field_type="input",
                                        field_props={
                                            "placeholder": "Enter your name",
                                            "value": "John Doe",
                                        },
                                        required=True,
                                        validation_state="valid",
                                        validation_message="Looks good!",
                                        help_text="Your full name",
                                    ),
                                    create_form_field_with_validation(
                                        field_id="demo-email-field",
                                        label="Email",
                                        field_type="input",
                                        field_props={
                                            "placeholder": "Enter your email",
                                            "type": "email",
                                            "value": "invalid-email",
                                        },
                                        required=True,
                                        validation_state="invalid",
                                        validation_message="Please enter a valid email address",
                                        tooltip="We'll never share your email with anyone else",
                                    ),
                                    create_form_field_with_validation(
                                        field_id="demo-status-field",
                                        label="Status",
                                        field_type="select",
                                        field_props={
                                            "options": [
                                                {"label": "Active", "value": "active"},
                                                {
                                                    "label": "Inactive",
                                                    "value": "inactive",
                                                },
                                                {
                                                    "label": "Pending",
                                                    "value": "pending",
                                                },
                                            ]
                                        },
                                        required=False,
                                        validation_state="warning",
                                        validation_message="Please select a status",
                                        help_text="The current status of your account",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-5",
            ),
            # Section 3: Empty States
            html.Div(
                [
                    html.H3("Empty States", style=create_heading_style(3)),
                    html.P("Empty states provide feedback when no data is available."),
                    html.Div(
                        [
                            dbc.Label("Select empty state type:"),
                            dbc.Select(
                                id="demo-empty-state-selector",
                                options=[
                                    {
                                        "label": "Default Empty State",
                                        "value": "default",
                                    },
                                    {"label": "No Search Results", "value": "search"},
                                    {"label": "Error Loading Data", "value": "error"},
                                    {"label": "No Filter Results", "value": "filter"},
                                ],
                                value="",
                            ),
                        ],
                        className="mb-3",
                    ),
                    html.Div(id="demo-empty-state-container", className="mb-3"),
                    # Additional empty state examples
                    html.H4("Additional Empty States", style=create_heading_style(4)),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    create_empty_state(
                                        message="Get started by adding your first project.",
                                        title="Welcome!",
                                        icon="fas fa-rocket",
                                        action_button=create_button(
                                            "Create Project",
                                            id="demo-create-project-btn",
                                            variant="primary",
                                            icon_class="fas fa-plus",
                                        ),
                                        variant="info",
                                    ),
                                ],
                                md=6,
                            ),
                            dbc.Col(
                                [
                                    create_empty_state(
                                        message="No team members have been added to this project yet.",
                                        title="No Team Members",
                                        icon="fas fa-users",
                                        action_button=create_button(
                                            "Invite Members",
                                            id="demo-invite-members-btn",
                                            variant="success",
                                            icon_class="fas fa-user-plus",
                                        ),
                                        variant="default",
                                    ),
                                ],
                                md=6,
                            ),
                        ]
                    ),
                ],
                className="mb-5",
            ),
            # Section 4: Error Recovery
            html.Div(
                [
                    html.H3("Error Recovery", style=create_heading_style(3)),
                    html.P(
                        "Demonstrate error recovery patterns with retry mechanisms."
                    ),
                    dbc.Card(
                        [
                            dbc.CardBody(
                                [
                                    html.P(
                                        "This example shows how to handle errors with recovery options."
                                    ),
                                    create_button(
                                        "Trigger Error",
                                        id="demo-trigger-error-btn",
                                        variant="danger",
                                        icon_class="fas fa-exclamation-triangle",
                                    ),
                                    html.Div(
                                        id="demo-error-recovery-result",
                                        className="mt-3",
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-5",
            ),
            # Section 5: Error Boundary
            html.Div(
                [
                    html.H3("Error Boundaries", style=create_heading_style(3)),
                    html.P(
                        "Error boundaries provide a fallback UI when components fail."
                    ),
                    create_error_boundary(
                        children=html.Div(
                            [
                                html.P("This content is wrapped in an error boundary."),
                                html.P("If it crashes, a fallback UI will be shown."),
                                create_button(
                                    "Simulate Error",
                                    id="demo-simulate-error-btn",
                                    variant="outline-danger",
                                    size="sm",
                                ),
                            ],
                            className="p-3 border",
                        ),
                        fallback_message="Something went wrong in this component.",
                        fallback_title="Component Error",
                        fallback_action=create_error_recovery_button(
                            id="demo-reset-error-btn",
                            text="Reset Component",
                        ),
                        id="demo-error-boundary",
                    ),
                ],
                className="mb-5",
            ),
        ],
        className="container py-4",
    )
