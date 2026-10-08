import datetime
import json
import logging
import traceback
import uuid

import dash_bootstrap_components as dbc
from dash import html

from ui.button_utils import create_button
from ui.icon_utils import create_icon
from ui.style_constants import NEUTRAL_COLORS, SEMANTIC_COLORS, rgb_to_rgba
from ui.styles import (
    create_heading_style,
    get_color,
    get_font_size,
    get_font_weight,
)

logger = logging.getLogger(__name__)


def create_error_style(
    variant: str = "danger", background: bool = True
) -> dict[str, str]:

    base_style: dict[str, str] = {
        "borderRadius": "0.375rem",
        "border": f"1px solid {get_color(variant)}",
    }

    if background:
        base_style["backgroundColor"] = rgb_to_rgba(SEMANTIC_COLORS[variant], 0.1)

    return base_style


def create_error_message_style(color="danger", size="md"):

    return {
        "color": get_color(color),
        "fontSize": get_font_size(size),
        "fontWeight": get_font_weight("medium"),
    }


def create_form_error_style(size="sm"):

    return {
        "color": get_color("danger"),
        "fontSize": get_font_size(size),
        "marginTop": "0.25rem",
        "display": "block",
    }


def create_empty_state_style(variant="default"):

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


def create_error_alert(
    message,
    title=None,
    severity="danger",
    dismissable=False,
    className="",
    id=None,
    icon=False,
):

    icon_map = {
        "danger": "danger",
        "warning": "warning",
        "info": "info",
        "success": "success",
    }

    content = []

    if title:
        if icon:
            title_content = [
                create_icon(
                    icon_map.get(severity, "info"),
                    className="me-2",
                ),
                html.Span(title),
            ]
        else:
            title_content = title

        content.append(html.H5(title_content, className="alert-heading mb-1"))

    if icon and not title:
        message_content = [
            create_icon(
                icon_map.get(severity, "info"),
                className="me-2",
            ),
            html.Span(message),
        ]
        content.append(html.Div(message_content))
    else:
        content.append(html.Div(message))

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

    return html.Div(
        [
            create_icon(
                style_info["icon"],
                color=style_info["color"],
                className=f"me-2 {style_info.get('icon_class', '')}",
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

    props = field_props or {}
    props["id"] = field_id

    if validation_state:
        props["valid"] = validation_state == "valid"
        props["invalid"] = validation_state == "invalid"

    label_content = [
        html.Span(label),
    ]

    if required:
        label_content.append(html.Span(" *", className="text-danger"))

    if tooltip:
        tooltip_id = f"{field_id}-tooltip"
        label_content.append(
            html.Span(
                create_icon("info", size="sm"),
                className="ms-1",
                id=tooltip_id,
            )
        )
        tooltip_component = dbc.Tooltip(
            tooltip,
            target=tooltip_id,
            trigger="click",
            autohide=True,
        )
    else:
        tooltip_component = None

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

    if validation_message and validation_state:
        feedback = create_validation_message(
            validation_message,
            state=validation_state,
            id=f"{field_id}-feedback",
        )
    else:
        feedback = None

    if help_text and not (validation_message and validation_state == "invalid"):
        help_component = html.Small(
            help_text,
            className="form-text text-muted",
        )
    else:
        help_component = None

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

    style = create_empty_state_style(variant)

    content = []

    if icon:
        content.append(
            html.Div(
                create_icon(icon, size="xl", color=variant),
                className="mb-3",
                style={"fontSize": "3rem"},
            )
        )

    if title:
        content.append(
            html.H5(
                title,
                className="mb-2",
                style=create_heading_style(5, color=variant),
            )
        )

    content.append(
        html.P(
            message,
            className="mb-3",
            style={"color": get_color(variant) if variant != "default" else None},
        )
    )

    if action_button:
        content.append(
            html.Div(
                action_button,
                className="mt-2",
            )
        )

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
            html.Div(retry_button if retry_button else []),
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

    return html.Div(
        [
            create_icon("danger", size=size, color="danger", className="me-2"),
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

    details_id = f"{id}-details" if id else f"error-details-{str(uuid.uuid4())[:8]}"
    collapse_id = f"{details_id}-collapse"

    card_content = [
        dbc.CardHeader(
            html.H5(
                [create_icon("danger", className="me-2"), title],
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

    if isinstance(exception, str):
        return exception

    try:
        return "".join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
    except Exception:
        return str(exception)


def log_error(error, additional_context=None):

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
        logger.error(f"Failed to log error: {log_error}")
        logger.error(f"Original error: {error}")
