"""
Form Components Module

Reusable form controls with validation support.
Extracted from ui/components.py during refactoring (bd-rnol).
"""

import re
from typing import Any

import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import get_color, get_spacing
from ui.styles import create_form_feedback_style


def create_input_field(
    label: str,
    input_type: str = "text",
    input_id: str = "",
    placeholder: str = "",
    value: Any = None,
    required: bool = False,
    size: str = "md",
    **kwargs,
) -> html.Div:
    """
    Create a labeled input field with validation support.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        label: Display label for input field (required)
        input_type: HTML input type - "text", "number", "date", "email", "password", "tel", "url"
        input_id: Unique ID for input element (if empty, generated from label)
        placeholder: Placeholder text
        value: Initial/current value
        required: Whether field is required
        size: Input size - "sm", "md", "lg"
        **kwargs: Additional props (min, max, step, disabled, invalid, valid, etc.)

    Returns:
        html.Div containing dbc.Label and dbc.Input

    Raises:
        ValueError: If label is empty or input_type is invalid

    Examples:
        >>> create_input_field("Deadline", input_type="date", value="2025-12-31")
        >>> create_input_field("PERT Factor", input_type="number", min=1.0, max=3.0, step=0.1)
        >>> create_input_field("Email", input_type="email", required=True)

    ID Pattern: input-{label-slugified} or provided input_id

    Accessibility:
        - Label properly associated with input via htmlFor/id
        - Required fields marked with aria-required
        - Invalid state communicated via aria-invalid
    """
    # Validation
    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        )

    # Generate ID from label if not provided
    if not input_id:
        label_slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        input_id = f"input-{label_slug}"

    # dbc.Input handles accessibility internally via 'required' and 'invalid' props
    # No need to add aria-* attributes manually

    # Get spacing from design tokens
    spacing = get_spacing("sm")

    # Create the input field
    # Note: dbc.Input automatically handles aria-required when required=True
    # and aria-invalid when invalid=True
    input_field = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        placeholder=placeholder,
        value=value,
        required=required,
        size=size,
        **kwargs,
    )

    # Create label with required indicator
    label_content = label
    if required:
        label_content = [
            label,
            html.Span(" *", style={"color": get_color("danger")}),
        ]

    label_element = dbc.Label(
        label_content, html_for=input_id, style={"marginBottom": spacing}
    )

    # Return wrapped in div
    return html.Div(
        [label_element, input_field],
        style={"marginBottom": get_spacing("md")},
    )


def create_labeled_input(
    label: str,
    input_id: str,
    input_type: str = "text",
    value: Any = None,
    help_text: str = "",
    error_message: str = "",
    size: str = "md",
    **kwargs,
) -> html.Div:
    """
    Create input field with label, help text, and error message support.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        label: Display label text (required)
        input_id: Unique ID for input (required)
        input_type: HTML input type
        value: Initial value
        help_text: Optional help text displayed below input
        error_message: Error message (shown only if invalid=True in kwargs)
        size: Component size
        **kwargs: Additional props passed to dbc.Input (invalid, valid, disabled, etc.)

    Returns:
        html.Div containing label, input, help text, and error feedback

    Raises:
        ValueError: If label or input_id is empty

    Examples:
        >>> create_labeled_input("PERT Factor", "pert-input", input_type="number",
        ...                      help_text="Typically 1.5-2.0", min=1.0, max=3.0)
        >>> create_labeled_input("Deadline", "deadline-input", input_type="date",
        ...                      error_message="Date must be in future", invalid=True)

    Accessibility:
        - Help text linked via aria-describedby
        - Error messages linked via aria-describedby
        - Invalid state properly communicated
    """
    # Validation
    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    if not input_id or input_id.strip() == "":
        raise ValueError("input_id is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. Must be one of: {', '.join(valid_input_types)}"
        )

    # Build aria-describedby references for accessibility
    # Note: dbc.Input doesn't accept aria-describedby directly, but we can
    # link help text and errors through proper HTML structure and IDs
    help_text_id = f"{input_id}-help" if help_text else None
    error_id = f"{input_id}-error" if error_message else None

    # Create input element
    # dbc.Input handles aria-invalid automatically when invalid=True
    input_element = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        value=value,
        size=size,
        **kwargs,
    )

    # Create components list
    components = [dbc.Label(label, html_for=input_id), input_element]

    # Add help text if provided
    if help_text:
        components.append(dbc.FormText(help_text, id=help_text_id, color="muted"))

    # Add error feedback if provided and invalid
    if error_message and kwargs.get("invalid", False):
        components.append(dbc.FormFeedback(error_message, id=error_id, type="invalid"))

    # Return as Div (FormGroup is deprecated in dbc 2.x)
    return html.Div(components, style={"marginBottom": get_spacing("md")})


def create_validation_message(message, show=False, type="invalid"):
    """
    Create a validation message for form inputs with consistent styling.

    Args:
        message (str): The validation message to display
        show (bool): Whether to show the message (default: False)
        type (str): The type of validation (valid, invalid, warning)

    Returns:
        html.Div: A validation message component
    """
    # Determine the appropriate style class based on validation type
    class_name = "d-none"
    if show:
        if type == "valid":
            class_name = "valid-feedback d-block"
        elif type == "warning":
            class_name = "text-warning d-block"
        else:
            class_name = "invalid-feedback d-block"

    # Get the base style from the styling function
    base_style = create_form_feedback_style(type)

    # Add icon based on the type
    icon_class = ""
    if type == "valid":
        icon_class = "fas fa-check-circle me-1"
    elif type == "warning":
        icon_class = "fas fa-exclamation-triangle me-1"
    elif type == "invalid":
        icon_class = "fas fa-times-circle me-1"

    # Return the validation message component
    return html.Div(
        [html.I(className=icon_class) if icon_class else "", message],
        className=class_name,
        style=base_style,
    )
