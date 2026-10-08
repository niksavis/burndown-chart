import re
from typing import Literal

import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import get_button_style
from ui.styles import TYPOGRAPHY


def create_action_button(
    text: str,
    icon: str | None = None,
    variant: str = "primary",
    size: str = "md",
    id_suffix: str = "",
    **kwargs,
) -> dbc.Button:

    if not text or text.strip() == "":
        raise ValueError("Button text is required and cannot be empty")

    valid_variants = [
        "primary",
        "secondary",
        "success",
        "danger",
        "warning",
        "info",
        "light",
        "dark",
        "link",
    ]
    if variant not in valid_variants:
        raise ValueError(
            f"Invalid variant '{variant}'. Must be one of: {', '.join(valid_variants)}"
        )

    text_slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    button_id = f"btn-{text_slug}"
    if id_suffix:
        button_id += f"-{id_suffix}"

    children = []
    if icon:
        icon_class = f"fas fa-{icon}" if not icon.startswith("fa-") else icon
        children.append(html.I(className=icon_class, style={"marginRight": "0.5rem"}))
    children.append(text)

    button_style = get_button_style(variant, size)

    custom_style = kwargs.pop("style", {})
    if custom_style:
        button_style.update(custom_style)

    aria_label = kwargs.pop("aria_label", text)
    if "title" not in kwargs:
        kwargs["title"] = aria_label

    return dbc.Button(
        children, id=button_id, color=variant, size=size, style=button_style, **kwargs
    )


def create_button_style(
    variant="primary", size="md", outline=False, disabled=False, touch_friendly=True
):

    base_style = {
        "fontFamily": TYPOGRAPHY["font_family"],
        "fontWeight": TYPOGRAPHY["weights"]["medium"],
        "borderRadius": "0.375rem",
        "transition": "all 0.2s ease-in-out",
        "textAlign": "center",
        "display": "inline-flex",
        "alignItems": "center",
        "justifyContent": "center",
        "boxShadow": "none",
    }

    if touch_friendly:
        size_styles = {
            "sm": {
                "fontSize": "0.875rem",
                "padding": "0.4rem 0.7rem",
                "lineHeight": "1.5",
                "minHeight": "38px",
            },
            "md": {
                "fontSize": "1rem",
                "padding": "0.5rem 0.875rem",
                "lineHeight": "1.5",
                "minHeight": "44px",
            },
            "lg": {
                "fontSize": "1.25rem",
                "padding": "0.625rem 1.1rem",
                "lineHeight": "1.5",
                "minHeight": "50px",
            },
        }
    else:
        size_styles = {
            "sm": {
                "fontSize": "0.875rem",
                "padding": "0.25rem 0.5rem",
                "lineHeight": "1.5",
            },
            "md": {
                "fontSize": "1rem",
                "padding": "0.375rem 0.75rem",
                "lineHeight": "1.5",
            },
            "lg": {
                "fontSize": "1.25rem",
                "padding": "0.5rem 1rem",
                "lineHeight": "1.5",
            },
        }

    base_style.update(size_styles.get(size, size_styles["md"]))

    if disabled:
        base_style.update(
            {
                "opacity": "0.65",
                "pointerEvents": "none",
                "cursor": "not-allowed",
            }
        )

    return base_style


def create_button(
    text=None,
    id=None,
    variant="primary",
    size="md",
    outline=False,
    icon_class=None,
    icon_position="left",
    tooltip=None,
    tooltip_placement: Literal[
        "auto",
        "auto-start",
        "auto-end",
        "top",
        "top-start",
        "top-end",
        "right",
        "right-start",
        "right-end",
        "bottom",
        "bottom-start",
        "bottom-end",
        "left",
        "left-start",
        "left-end",
    ] = "top",
    className="",
    style=None,
    disabled=False,
    **kwargs,
):

    if text is None and icon_class is None:
        text = "Button"

    button_color = variant
    if outline:
        button_color = f"outline-{variant}"

    icon = None
    icon_right = None

    if icon_class:
        if icon_position == "left":
            icon = html.I(className=icon_class, style={"marginRight": "0.5rem"})
        else:
            icon_right = html.I(className=icon_class, style={"marginLeft": "0.5rem"})

    button_style = create_button_style(variant, size, outline, disabled)
    if style:
        button_style.update(style)

    button_content = []
    if icon:
        button_content.append(icon)
    if text:
        button_content.append(text)
    if icon_right:
        button_content.append(icon_right)

    if not text and icon_class:
        button_content = html.I(className=icon_class)

    button = dbc.Button(
        button_content,
        id=id,
        color=button_color,
        size=size,
        className=className,
        style=button_style,
        disabled=disabled,
        **kwargs,
    )

    if tooltip and id:
        return html.Div(
            [
                button,
                dbc.Tooltip(
                    tooltip,
                    target=id,
                    placement=tooltip_placement,
                    trigger="click",
                    autohide=True,
                ),
            ],
            style={"display": "inline-block"},
        )

    return button


def create_button_group(buttons, vertical=False, className=""):

    return dbc.ButtonGroup(buttons, vertical=vertical, className=className)


def create_action_buttons(
    primary_action=None, secondary_action=None, tertiary_action=None, alignment="right"
):

    buttons = []

    if tertiary_action:
        tertiary_btn = create_button(
            tertiary_action.get("text", "Cancel"),
            id=tertiary_action.get("id"),
            variant="link",
            size="md",
            icon_class=tertiary_action.get("icon"),
            className="me-2",
        )
        buttons.append(tertiary_btn)

    if secondary_action:
        secondary_btn = create_button(
            secondary_action.get("text", "Cancel"),
            id=secondary_action.get("id"),
            variant="secondary",
            size="md",
            icon_class=secondary_action.get("icon"),
            className="me-2",
        )
        buttons.append(secondary_btn)

    if primary_action:
        primary_btn = create_button(
            primary_action.get("text", "Submit"),
            id=primary_action.get("id"),
            variant="primary",
            size="md",
            icon_class=primary_action.get("icon"),
        )
        buttons.append(primary_btn)

    flex_align = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(
        alignment, "flex-end"
    )

    return html.Div(
        buttons, className="d-flex mt-3", style={"justifyContent": flex_align}
    )


def create_icon_button(
    icon_class,
    label,
    id=None,
    color="primary",
    tooltip=None,
    className=None,
    **kwargs,
):
    button_kwargs = {
        k: v for k, v in kwargs.items() if k not in ["tooltip", "className"]
    }

    final_class = f"btn btn-{color} icon-only"
    if className:
        final_class += f" {className}"

    button = html.Button(
        html.I(className=icon_class),
        id=id,
        className=final_class,
        title=tooltip if tooltip else label,
        **{"aria-label": label, **button_kwargs},
    )

    return button


def create_close_button(
    id=None,
    variant="light",
    size="sm",
    tooltip="Close",
    className="",
    style=None,
    disabled=False,
    **kwargs,
):

    button_style = {
        "position": "absolute",
        "top": "8px",
        "right": "8px",
        "padding": "4px 8px",
        "zIndex": "1050",
    }

    if style:
        button_style.update(style)

    return create_icon_button(
        icon_class="fas fa-times",
        label="Close",
        id=id,
        color=variant if variant else "secondary",
        tooltip=tooltip,
        className=className,
        style=button_style,
        disabled=disabled,
        **{k: v for k, v in kwargs.items() if k not in ["size", "variant"]},
    )


def create_menu_button(
    id=None,
    variant="light",
    size="sm",
    tooltip="Menu",
    className="",
    style=None,
    disabled=False,
    **kwargs,
):

    return create_icon_button(
        icon_class="fas fa-bars",
        label="Menu",
        id=id,
        color=variant if variant else "primary",
        tooltip=tooltip,
        className=className,
        style=style,
        disabled=disabled,
        **{k: v for k, v in kwargs.items() if k not in ["size", "variant"]},
    )


def create_segmented_button_group(
    options,
    id=None,
    value=None,
    size="md",
    variant="outline-primary",
    className="",
    style=None,
):

    buttons = []

    for i, option in enumerate(options):
        label = option.get("label", f"Option {i + 1}")
        option_value = option.get("value", i)
        icon_class = option.get("icon_class")

        active = value == option_value if value is not None else i == 0

        content = []
        if icon_class:
            content.append(html.I(className=f"{icon_class} me-1"))
        if label:
            content.append(label)

        button = dbc.Button(
            content,
            id={"type": f"{id}-option", "index": i} if id else None,
            className=f"px-3 {'active' if active else ''}",
            color=variant.replace("outline-", "")
            if active and "outline-" in variant
            else variant,
            size=size,
            style={"boxShadow": "none", "borderRadius": "0"}
            if i > 0 and i < len(options) - 1
            else {
                "boxShadow": "none",
                "borderRadius": "0.375rem 0 0 0.375rem"
                if i == 0
                else "0 0.375rem 0.375rem 0",
            },
        )
        buttons.append(button)

    return html.Div(
        dbc.ButtonGroup(buttons, id=id, className=className, style=style or {}),
        className="segmented-button-group",
    )


def create_pill_button(
    text=None,
    id=None,
    icon_class=None,
    selected=False,
    variant="outline-primary",
    size="sm",
    className="",
    style=None,
    **kwargs,
):

    pill_style = {
        "borderRadius": "50rem",
        "fontWeight": "500" if selected else "normal",
    }

    if style:
        pill_style.update(style)

    content = []
    if icon_class:
        content.append(html.I(className=f"{icon_class} me-1"))
    if text:
        content.append(text)

    button_variant = (
        variant.replace("outline-", "")
        if selected and "outline-" in variant
        else variant
    )

    return dbc.Button(
        content,
        id=id,
        color=button_variant,
        size=size,
        className=f"rounded-pill {className} {'active' if selected else ''}",
        style=pill_style,
        **kwargs,
    )


def create_panel_collapse_button(panel_id: str) -> html.Button:

    button_id = f"{panel_id}-btn"

    return html.Button(
        html.I(className="fas fa-chevron-up"),
        id=button_id,
        className="panel-collapse-btn",
        title="Collapse panel",
        **{"aria-label": "Collapse panel"},  # type: ignore[arg-type]
    )
