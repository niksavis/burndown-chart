import dash_bootstrap_components as dbc
from dash import html

from ui.style_constants import HELP_ICON_POSITIONS
from ui.tooltip_utils_core import (
    create_adaptive_tooltip_config,
    get_smart_placement,
)


def create_tooltip(
    content,
    target=None,
    id=None,
    position="top",
    variant="default",
    delay=None,
    trigger="click",
    autohide=True,
    max_width=None,
    className="",
    style=None,
):

    if delay is None:
        delay = {"show": 200, "hide": 100}
    tooltip_style = {}
    if max_width:
        tooltip_style["maxWidth"] = max_width
    if style:
        tooltip_style.update(style)

    variant_class = f"tooltip-{variant}" if variant != "default" else ""
    full_class = f"{variant_class} {className}".strip()

    tooltip_id = id
    if tooltip_id is None and target is not None:
        tooltip_id = f"tooltip-for-{target}"

    tooltip_props = {
        "children": content,
        "target": target,
        "placement": position,
        "delay": delay,
        "trigger": trigger,
        "autohide": autohide,
        "className": full_class,
    }

    if tooltip_style:
        tooltip_props["style"] = tooltip_style

    if tooltip_id is not None:
        tooltip_props["id"] = tooltip_id

    return dbc.Tooltip(**tooltip_props)


def create_help_icon(
    tooltip_id: str,
    position: str = "inline",
    icon_class: str = "fas fa-info-circle",
    color: str = "#3b82f6",
) -> html.I:

    position_config = HELP_ICON_POSITIONS.get(position, HELP_ICON_POSITIONS["inline"])

    return html.I(
        className=f"{icon_class} text-info {position_config['class']}",
        id=f"info-tooltip-{tooltip_id}",
        style={
            "cursor": "pointer",
            "fontSize": "0.875rem",
            "verticalAlign": position_config["vertical_align"],
        },
    )


def create_info_tooltip(
    param1=None,
    param2=None,
    placement="top",
    variant="dark",
    id_suffix=None,
    help_text=None,
):

    if id_suffix is not None and help_text is not None:
        pass
    elif param1 is not None and param2 is not None:
        if " " in str(param1) or len(str(param1)) > 50:
            help_text = param1
            id_suffix = param2
        else:
            id_suffix = param1
            help_text = param2
    elif id_suffix is not None:
        help_text = param1
    elif help_text is not None:
        id_suffix = param1
    else:
        raise ValueError(
            "create_info_tooltip requires both help_text and id_suffix parameters"
        )

    if id_suffix is None or help_text is None:
        raise ValueError(
            f"create_info_tooltip requires both help_text and id_suffix. "
            f"Got id_suffix={id_suffix!r}, help_text={help_text!r}"
        )

    valid_placements = {
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
    }
    validated_placement = placement if placement in valid_placements else "top"

    return html.Span(
        [
            create_help_icon(id_suffix, position="inline"),
            create_tooltip(
                help_text,
                target=f"info-tooltip-{id_suffix}",
                position=validated_placement,
                variant=variant,
            ),
        ],
        style={"display": "inline"},
    )


def create_enhanced_tooltip(
    id_suffix,
    help_text,
    target=None,
    variant="dark",
    placement="top",
    trigger_text=None,
    icon_class=None,
    delay=None,
    smart_positioning=True,
    dismissible=False,
    expandable=False,
):

    if delay is None:
        delay = {"show": 200, "hide": 100}
    tooltip_target = f"tooltip-{id_suffix}"

    if smart_positioning:
        placement = get_smart_placement(placement, mobile_override="bottom")
        delay = create_adaptive_tooltip_config(delay.get("show", 200))

    if target:
        trigger = None
        tooltip_target = target
    elif trigger_text:
        trigger = html.Span(
            [trigger_text],
            id=tooltip_target,
            className="tooltip-indicator",
            style={"cursor": "help"},
        )
    else:
        icon = icon_class or "fas fa-info-circle"
        trigger = html.I(
            className=f"{icon} text-{variant}",
            id=tooltip_target,
            style={"cursor": "help", "marginLeft": "5px", "fontSize": "1rem"},
        )

    enhanced_content = help_text
    if dismissible or expandable:
        enhanced_content = _create_interactive_content(
            help_text, id_suffix, dismissible, expandable
        )

    tooltip = create_tooltip(
        content=enhanced_content,
        target=tooltip_target,
        position=placement,
        variant=variant,
        delay=delay,
    )

    if trigger:
        return html.Div(
            [trigger, tooltip],
            style={"display": "inline-block"},
        )
    else:
        return tooltip


def create_dismissible_tooltip(
    id_suffix, help_text, target=None, variant="dark", placement="top"
):

    return create_enhanced_tooltip(
        id_suffix=id_suffix,
        help_text=help_text,
        target=target,
        variant=variant,
        placement=placement,
        dismissible=True,
        smart_positioning=True,
    )


def create_expandable_tooltip(
    id_suffix,
    summary_text,
    detailed_text,
    target=None,
    variant="dark",
    placement="top",
):

    combined_content = {"summary": summary_text, "details": detailed_text}

    return create_enhanced_tooltip(
        id_suffix=id_suffix,
        help_text=combined_content,
        target=target,
        variant=variant,
        placement=placement,
        expandable=True,
        smart_positioning=True,
    )


def _create_interactive_content(
    content, id_suffix, dismissible=False, expandable=False
):

    if expandable and isinstance(content, dict):
        summary = content.get("summary", "")
        details = content.get("details", "")

        interactive_content = html.Div(
            [
                html.Div(summary, className="tooltip-summary"),
                html.Hr(style={"margin": "8px 0"}),
                html.Div(
                    [
                        html.Small(
                            "Click to expand...",
                            id=f"expand-trigger-{id_suffix}",
                            className="text-muted",
                            style={"cursor": "pointer", "textDecoration": "underline"},
                        ),
                        html.Div(
                            details,
                            id=f"expand-content-{id_suffix}",
                            style={"display": "none", "marginTop": "8px"},
                        ),
                    ]
                ),
            ]
        )
    else:
        interactive_content = html.Div(
            content if isinstance(content, list) else [content]
        )

    if dismissible:
        dismiss_button = html.Button(
            "x",
            id=f"dismiss-{id_suffix}",
            className="btn-close btn-close-white ms-2",
            style={
                "border": "none",
                "background": "transparent",
                "color": "inherit",
                "fontSize": "1.2rem",
                "padding": "0",
                "cursor": "pointer",
                "float": "right",
            },
        )

        if isinstance(interactive_content, html.Div) and interactive_content.children:
            interactive_content.children.append(dismiss_button)
        else:
            interactive_content = html.Div([interactive_content, dismiss_button])

    return interactive_content


def create_form_help_tooltip(id_suffix, field_label, help_text, variant="info"):

    return html.Label(
        [
            field_label,
            create_enhanced_tooltip(
                id_suffix=id_suffix,
                help_text=help_text,
                variant=variant,
                placement="right",
                delay={"show": 300, "hide": 100},
            ),
        ],
        className="form-label d-flex align-items-center",
        style={"gap": "4px"},
    )


def create_contextual_help(id_suffix, help_text, trigger_text=None, variant="dark"):

    trigger_text = trigger_text or "Learn more"

    return html.Span(
        [
            html.Span(
                trigger_text,
                id=f"context-help-{id_suffix}",
                className="text-primary",
                style={"borderBottom": "1px dotted #0d6efd", "cursor": "help"},
            ),
            create_tooltip(
                help_text,
                target=f"context-help-{id_suffix}",
                variant=variant,
            ),
        ],
    )
