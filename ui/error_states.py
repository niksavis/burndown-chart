"""
Error States Module

This module provides standardized error state components for the application.
It implements consistent patterns for form validation, empty states, error boundaries, etc.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
from ui.styles import (
    create_error_style,
    create_error_message_style,
    create_form_error_style,
    create_empty_state_style,
    get_color,
    create_heading_style,
    create_icon,
)
from ui.components import create_button


def create_error_alert(
    message,
    title=None,
    severity="danger",
    dismissable=False,
    className="",
    id=None,
    icon=False,
):
    """
    Create a standardized error alert component.

    Args:
        message (str): The error message text
        title (str, optional): Title for the alert
        severity (str): Alert severity (danger, warning, info, success)
        dismissable (bool): Whether the alert can be dismissed
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID
        icon (bool): Whether to show an icon

    Returns:
        dbc.Alert: A styled error alert component
    """
    # Determine icon based on severity
    icon_map = {
        "danger": "danger",
        "warning": "warning",
        "info": "info",
        "success": "success",
    }

    # Create alert content
    content = []

    # Add title if provided
    if title:
        # Add icon to title if requested
        if icon:
            title_content = [
                create_icon(
                    icon_map.get(severity, "info"),
                    with_space_right=True,
                    className="me-2",
                ),
                html.Span(title),
            ]
        else:
            title_content = title

        content.append(html.H5(title_content, className="alert-heading mb-1"))

    # Add icon to message if requested and no title
    if icon and not title:
        message_content = [
            create_icon(
                icon_map.get(severity, "info"), with_space_right=True, className="me-2"
            ),
            html.Span(message),
        ]
        content.append(html.Div(message_content))
    else:
        content.append(html.Div(message))

    # Create the alert component
    return dbc.Alert(
        content,
        color=severity,
        dismissable=dismissable,
        className=f"mb-3 {className}",
        id=id,
    )


def create_validation_message(
    message,
    state="invalid",
    id=None,
    className="",
):
    """
    Create a standardized validation message for form fields.

    Args:
        message (str): The validation message text
        state (str): Validation state (valid, invalid, warning)
        id (str, optional): Component ID
        className (str, optional): Additional CSS classes

    Returns:
        html.Div: A styled validation message component
    """
    # Map validation states to styles
    state_map = {
        "valid": {
            "icon": "success",
            "color": "success",
            "class": "valid-feedback",
        },
        "invalid": {
            "icon": "danger",
            "color": "danger",
            "class": "invalid-feedback",
        },
        "warning": {
            "icon": "warning",
            "color": "warning",
            "class": "text-warning small",
        },
    }

    style_info = state_map.get(state, state_map["invalid"])

    # Create the validation message component
    return html.Div(
        [
            create_icon(
                style_info["icon"],
                color=style_info["color"],
                with_space_right=True,
                size="sm",
            ),
            html.Span(
                message, style=create_error_message_style(style_info["color"], "sm")
            ),
        ],
        className=f"{style_info['class']} d-block {className}",
        style={"display": "flex", "alignItems": "center"},
        id=id,
    )


def create_form_field_with_validation(
    field_id,
    label,
    field_type="input",
    field_props=None,
    validation_state=None,
    validation_message=None,
    required=False,
    help_text=None,
    tooltip=None,
    className="mb-3",
):
    """
    Create a form field with built-in validation.

    Args:
        field_id (str): ID for the form field
        label (str): Label text
        field_type (str): Type of field (input, select, checkbox, radio, textarea)
        field_props (dict): Properties to pass to the field component
        validation_state (str, optional): Validation state (valid, invalid, warning)
        validation_message (str, optional): Validation message
        required (bool): Whether the field is required
        help_text (str, optional): Help text to display below the field
        tooltip (str, optional): Tooltip text for an info icon
        className (str, optional): Additional CSS classes

    Returns:
        html.Div: A form group with the field and validation
    """
    # Initialize field properties
    props = field_props or {}
    props["id"] = field_id

    # Add validation properties if validation state is provided
    if validation_state:
        props["valid"] = validation_state == "valid"
        props["invalid"] = validation_state == "invalid"

    # Create label with required indicator if needed
    label_content = [
        html.Span(label),
    ]

    if required:
        label_content.append(html.Span(" *", className="text-danger"))

    if tooltip:
        tooltip_id = f"{field_id}-tooltip"
        label_content.append(
            html.Span(
                create_icon("info", size="sm", with_space_left=True, id=tooltip_id),
                className="ms-1",
            )
        )
        tooltip_component = dbc.Tooltip(tooltip, target=tooltip_id)
    else:
        tooltip_component = None

    # Create the field based on type
    if field_type == "input":
        field = dbc.Input(**props)
    elif field_type == "select":
        field = dbc.Select(**props)
    elif field_type == "textarea":
        field = dbc.Textarea(**props)
    elif field_type == "checkbox":
        field = dbc.Checkbox(**props)
    elif field_type == "radio":
        field = dbc.RadioItems(**props)
    else:
        field = dbc.Input(**props)

    # Create feedback component if validation message is provided
    if validation_message and validation_state:
        feedback = create_validation_message(
            validation_message,
            state=validation_state,
            id=f"{field_id}-feedback",
        )
    else:
        feedback = None

    # Create help text component if provided
    if help_text and not (validation_message and validation_state == "invalid"):
        help_component = html.Small(
            help_text,
            className="form-text text-muted",
        )
    else:
        help_component = None

    # Create the form group
    components = [
        html.Label(label_content, className="form-label", htmlFor=field_id),
        field,
    ]

    if feedback:
        components.append(feedback)

    if help_component:
        components.append(help_component)

    if tooltip_component:
        components.append(tooltip_component)

    return html.Div(components, className=className)


def create_empty_state(
    message,
    title=None,
    icon=None,
    action_button=None,
    variant="default",
    className="",
    id=None,
):
    """
    Create an empty state component for when no data is available.

    Args:
        message (str): The empty state message
        title (str, optional): Title for the empty state
        icon (str, optional): Icon class or name to show
        action_button (component, optional): Action button component
        variant (str): Empty state variant (default, info, warning, error)
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID

    Returns:
        html.Div: An empty state component
    """
    # Get style for the empty state
    style = create_empty_state_style(variant)

    # Create content components
    content = []

    # Add icon if provided
    if icon:
        content.append(
            html.Div(
                create_icon(icon, size="xl", color=variant),
                className="mb-3",
                style={"fontSize": "3rem"},
            )
        )

    # Add title if provided
    if title:
        content.append(
            html.H5(
                title,
                className="mb-2",
                style=create_heading_style(5, color=variant),
            )
        )

    # Add message
    content.append(
        html.P(
            message,
            className="mb-3",
            style={"color": get_color(variant) if variant != "default" else None},
        )
    )

    # Add action button if provided
    if action_button:
        content.append(
            html.Div(
                action_button,
                className="mt-2",
            )
        )

    # Create the empty state container
    return html.Div(
        content,
        className=f"empty-state {className}",
        style=style,
        id=id,
    )


def create_error_recovery_button(
    id="retry-btn",
    text="Retry",
    icon="fas fa-sync",
    variant="primary",
    size="md",
    className="",
):
    """
    Create a standardized error recovery button.

    Args:
        id (str): Button ID
        text (str): Button text
        icon (str): Icon class
        variant (str): Button variant
        size (str): Button size
        className (str): Additional CSS classes

    Returns:
        dbc.Button: A styled error recovery button
    """
    return create_button(
        text=text,
        id=id,
        variant=variant,
        size=size,
        icon_class=icon,
        className=f"error-recovery-btn {className}",
    )


def create_error_boundary(
    children,
    fallback_message,
    fallback_title=None,
    fallback_action=None,
    id=None,
    className="",
):
    """
    Create an error boundary component that shows fallback UI when children crash.

    Args:
        children: Child components that might error
        fallback_message (str): Message to show when an error occurs
        fallback_title (str, optional): Title for the fallback UI
        fallback_action (component, optional): Action component for the fallback UI
        id (str, optional): Component ID
        className (str): Additional CSS classes

    Returns:
        html.Div: An error boundary component
    """
    # The actual error boundary functionality would be implemented
    # with React ErrorBoundary, but this is a styling placeholder

    # Create the fallback UI
    fallback_ui = html.Div(
        [
            html.Div(
                create_icon("danger", size="xl", color="danger"),
                className="mb-3",
                style={"fontSize": "3rem"},
            ),
            html.H5(
                fallback_title or "An error occurred",
                className="mb-2",
                style=create_heading_style(5, color="danger"),
            ),
            html.P(
                fallback_message,
                className="mb-3",
            ),
            html.Div(
                fallback_action
                or create_error_recovery_button(
                    id=f"{id}-reset" if id else "error-boundary-reset",
                    text="Reset",
                ),
                className="mt-2",
            ),
        ],
        style=create_error_style("danger", background=True),
        className="p-4 text-center",
    )

    # In a real implementation, we would use a custom React component
    # that catches errors and switches between children and fallback_ui
    # For now, we'll just show the children since we can't catch errors

    return html.Div(
        children,
        id=id,
        className=f"error-boundary {className}",
    )
