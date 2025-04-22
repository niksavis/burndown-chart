"""
Error States Module

This module provides standardized error state components for the application.
It implements consistent patterns for form validation, empty states, error boundaries, etc.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import datetime
import json
import traceback
import uuid

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html, dcc

# Application imports
from ui.button_utils import create_button
from ui.icon_utils import create_icon
from ui.styles import (
    get_color,
    create_heading_style,
    get_font_size,
    get_font_weight,
    SEMANTIC_COLORS,
    NEUTRAL_COLORS,
)

#######################################################################
# ERROR STYLING FUNCTIONS
#######################################################################


def create_error_style(variant="danger", background=True):
    """
    Create a consistent error style dictionary.

    Args:
        variant (str): Error variant (danger, warning, info)
        background (bool): Whether to include background styling

    Returns:
        Dictionary with error styling properties
    """
    base_style = {
        "borderRadius": "0.375rem",
        "border": f"1px solid {get_color(variant)}",
    }

    if background:
        base_style["backgroundColor"] = (
            f"rgba({int(SEMANTIC_COLORS[variant].split(',')[0].replace('rgb(', ''))}, "
            + f"{int(SEMANTIC_COLORS[variant].split(',')[1])}, "
            + f"{int(SEMANTIC_COLORS[variant].split(',')[2].replace(')', ''))}, 0.1)"
        )

    return base_style


def create_error_message_style(color="danger", size="md"):
    """
    Create a consistent error message style.

    Args:
        color (str): Error color variant
        size (str): Text size

    Returns:
        Dictionary with error message styling
    """
    return {
        "color": get_color(color),
        "fontSize": get_font_size(size),
        "fontWeight": get_font_weight("medium"),
    }


def create_form_error_style(size="sm"):
    """
    Create a consistent form validation error style.

    Args:
        size (str): Text size for the error

    Returns:
        Dictionary with form error styling
    """
    return {
        "color": get_color("danger"),
        "fontSize": get_font_size(size),
        "marginTop": "0.25rem",
        "display": "block",
    }


def create_empty_state_style(variant="default"):
    """
    Create consistent styling for empty state components.

    Args:
        variant (str): Empty state variant (default, info, warning, error)

    Returns:
        dict: Dictionary with empty state styling properties
    """
    base_style = {
        "padding": "2rem",
        "borderRadius": "0.5rem",
        "textAlign": "center",
    }

    if variant != "default":
        base_style.update(create_error_style(variant, background=True))
    else:
        base_style.update(
            {
                "backgroundColor": NEUTRAL_COLORS["gray-100"],
                "border": f"1px solid {NEUTRAL_COLORS['gray-300']}",
            }
        )

    return base_style


# Original functions start here


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


def create_loading_error(
    message="Failed to load data",
    retry_callback=None,
    id=None,
    className="",
):
    """
    Create a standardized loading error component.

    Args:
        message (str): The error message
        retry_callback (function, optional): Callback function for retry button
        id (str, optional): Component ID
        className (str, optional): Additional CSS classes

    Returns:
        html.Div: A loading error component
    """
    retry_button = None
    if retry_callback:
        button_id = f"{id}-retry" if id else "loading-error-retry"
        retry_button = create_error_recovery_button(
            id=button_id,
            text="Retry",
            icon="refresh",
            variant="outline-primary",
        )

    return html.Div(
        [
            html.Div(
                create_icon("danger", size="lg", color="danger"),
                className="mb-2",
            ),
            html.Div(
                message,
                className="mb2",
                style=create_error_message_style("danger", "md"),
            ),
            html.Div(retry_button) if retry_button else None,
        ],
        className=f"text-center p-4 {className}",
        style=create_error_style("danger", background=True),
        id=id,
    )


def create_inline_error(
    message,
    id=None,
    className="",
    size="sm",
):
    """
    Create a small inline error message.

    Args:
        message (str): The error message
        id (str, optional): Component ID
        className (str, optional): Additional CSS classes
        size (str): Text size (sm, md, lg)

    Returns:
        html.Div: An inline error message component
    """
    return html.Div(
        [
            create_icon("danger", size=size, color="danger", with_space_right=True),
            html.Span(message),
        ],
        className=f"d-flex align-items-center {className}",
        style=create_error_message_style("danger", size),
        id=id,
    )


def create_error_card(
    title,
    message,
    details=None,
    action_button=None,
    id=None,
    className="",
    collapsible_details=True,
):
    """
    Create a card with error information.

    Args:
        title (str): Error title
        message (str): Error message
        details (str, optional): Technical error details
        action_button (component, optional): Action button component
        id (str, optional): Component ID
        className (str, optional): Additional CSS classes
        collapsible_details (bool): Whether technical details are collapsible

    Returns:
        dbc.Card: An error card component
    """
    details_id = f"{id}-details" if id else f"error-details-{str(uuid.uuid4())[:8]}"
    collapse_id = f"{details_id}-collapse"

    card_content = [
        dbc.CardHeader(
            html.H5(
                [create_icon("danger", with_space_right=True), title],
                className="mb-0 d-flex align-items-center",
            ),
            className="bg-danger text-white",
        ),
        dbc.CardBody(
            [
                html.P(message, className="card-text"),
                html.Div(
                    [
                        dbc.Button(
                            "Show Technical Details",
                            id=details_id,
                            color="link",
                            size="sm",
                            className="p-0 text-decoration-none",
                        )
                        if collapsible_details and details
                        else None,
                        dbc.Collapse(
                            dbc.Card(
                                dbc.CardBody(
                                    html.Pre(
                                        details,
                                        className="mb-0 text-danger",
                                        style={
                                            "whiteSpace": "pre-wrap",
                                            "fontSize": "0.875rem",
                                        },
                                    )
                                ),
                                className="mt-2 border-danger",
                            ),
                            id=collapse_id,
                            is_open=False,
                        )
                        if collapsible_details and details
                        else None,
                        html.Pre(
                            details,
                            className="mb-0 mt-3 p-2 bg-light border text-danger",
                            style={"whiteSpace": "pre-wrap", "fontSize": "0.875rem"},
                        )
                        if not collapsible_details and details
                        else None,
                    ]
                ),
                html.Div(
                    action_button,
                    className="mt-3",
                )
                if action_button
                else None,
            ]
        ),
    ]

    return dbc.Card(
        card_content,
        className=f"border-danger {className}",
        id=id,
    )


def format_exception(exception):
    """
    Format an exception for display.

    Args:
        exception: The exception to format

    Returns:
        str: Formatted exception text
    """
    if isinstance(exception, str):
        return exception

    try:
        return "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
    except:
        return str(exception)


def log_error(error, additional_context=None):
    """
    Log an error to the application's error log.

    Args:
        error: The error or exception
        additional_context (dict, optional): Additional context information

    Returns:
        None
    """
    try:
        error_data = {
            "timestamp": str(datetime.datetime.now()),
            "error": format_exception(error),
        }

        if additional_context:
            error_data["context"] = additional_context

        with open("burndown_errors.log", "a") as f:
            f.write(json.dumps(error_data) + "\n")
    except Exception as log_error:
        print(f"Failed to log error: {log_error}")
        print(f"Original error: {error}")
