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

    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. "
            f"Must be one of: {', '.join(valid_input_types)}"
        )

    if not input_id:
        label_slug = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        input_id = f"input-{label_slug}"

    spacing = get_spacing("sm")

    input_field = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        placeholder=placeholder,
        value=value,
        required=required,
        size=size,
        **kwargs,
    )

    label_content = label
    if required:
        label_content = [
            label,
            html.Span(" *", style={"color": get_color("danger")}),
        ]

    label_element = dbc.Label(
        label_content, html_for=input_id, style={"marginBottom": spacing}
    )

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

    if not label or label.strip() == "":
        raise ValueError("Label is required and cannot be empty")

    if not input_id or input_id.strip() == "":
        raise ValueError("input_id is required and cannot be empty")

    valid_input_types = ["text", "number", "date", "email", "password", "tel", "url"]
    if input_type not in valid_input_types:
        raise ValueError(
            f"Invalid input_type '{input_type}'. "
            f"Must be one of: {', '.join(valid_input_types)}"
        )

    help_text_id = f"{input_id}-help" if help_text else None
    error_id = f"{input_id}-error" if error_message else None

    input_element = dbc.Input(
        type=input_type,  # type: ignore[arg-type]
        id=input_id,
        value=value,
        size=size,
        **kwargs,
    )

    components = [dbc.Label(label, html_for=input_id), input_element]

    if help_text:
        components.append(dbc.FormText(help_text, id=help_text_id, color="muted"))

    if error_message and kwargs.get("invalid", False):
        components.append(dbc.FormFeedback(error_message, id=error_id, type="invalid"))

    return html.Div(components, style={"marginBottom": get_spacing("md")})


def create_validation_message(message, show=False, type="invalid"):

    class_name = "d-none"
    if show:
        if type == "valid":
            class_name = "valid-feedback d-block"
        elif type == "warning":
            class_name = "text-warning d-block"
        else:
            class_name = "invalid-feedback d-block"

    base_style = create_form_feedback_style(type)

    icon_class = ""
    if type == "valid":
        icon_class = "fas fa-check-circle me-1"
    elif type == "warning":
        icon_class = "fas fa-exclamation-triangle me-1"
    elif type == "invalid":
        icon_class = "fas fa-times-circle me-1"

    return html.Div(
        [html.I(className=icon_class) if icon_class else "", message],
        className=class_name,
        style=base_style,
    )
