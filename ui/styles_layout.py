from dash import html

from configuration import COLOR_PALETTE
from ui.style_constants import NEUTRAL_COLORS, SEMANTIC_COLORS, TYPOGRAPHY, rgb_to_rgba
from ui.styles_components import create_text_style
from ui.styles_tokens import (
    SPACING,
    get_color,
    get_font_size,
    get_font_weight,
    get_vertical_rhythm,
)


def apply_vertical_rhythm(element_type="paragraph", style=None):

    rhythm_style = {}
    base_style = style or {}

    if element_type.startswith("heading."):
        _, level = element_type.split(".")
        rhythm_style["marginBottom"] = get_vertical_rhythm(
            f"heading.{level}", "heading.h6"
        )
        rhythm_style["marginTop"] = get_vertical_rhythm("before_title")
    elif element_type == "paragraph":
        rhythm_style["marginBottom"] = get_vertical_rhythm("paragraph")
    elif element_type == "list":
        rhythm_style["marginBottom"] = get_vertical_rhythm("list")
    elif element_type == "list_item":
        rhythm_style["marginBottom"] = get_vertical_rhythm("list_item")
    elif element_type == "section":
        rhythm_style["marginBottom"] = get_vertical_rhythm("section")
    elif element_type == "card":
        rhythm_style["marginBottom"] = get_vertical_rhythm("card")

    return {**rhythm_style, **base_style}


def create_rhythm_text(
    text, element_type, size=None, weight=None, color=None, className=""
):

    text_style = create_text_style(
        size=size or "md", weight=weight or "regular", color=color or "dark"
    )

    rhythm_style = apply_vertical_rhythm(element_type, text_style)

    return html.Div(text, className=className, style=rhythm_style)


def create_vertical_spacer(size="md"):

    if size in SPACING:
        height = SPACING[size]
    elif "." in size:
        height = get_vertical_rhythm(size)
    else:
        height = get_vertical_rhythm(size, "base")

    return html.Div(style={"height": height})


def update_heading_style(level, color=None, weight="bold"):

    size_key = f"h{level}" if 1 <= level <= 6 else "h1"

    style = {
        "fontSize": get_font_size(size_key),
        "fontWeight": get_font_weight(weight),
        "fontFamily": TYPOGRAPHY["font_family"],
    }

    style["marginBottom"] = get_vertical_rhythm(f"heading.{size_key}", "heading.h6")
    style["marginTop"] = get_vertical_rhythm("before_title") if level <= 2 else "0"

    if color:
        style["color"] = (
            get_color(color)
            if color in COLOR_PALETTE
            or color in SEMANTIC_COLORS
            or color in NEUTRAL_COLORS
            else color
        )

    return style


def create_content_section(
    content,
    title=None,
    title_level=2,
    title_color=None,
    className="",
    style=None,
    section_type="section",
    id=None,
):

    margin_bottom = get_vertical_rhythm(section_type, "section")

    section_style = {
        "marginBottom": margin_bottom,
    }

    if style:
        section_style.update(style)

    elements = []

    if title:
        title_style = update_heading_style(title_level, color=title_color)
        elements.append(
            html.H2(title, style=title_style)
            if title_level == 2
            else html.H1(title, style=title_style)
            if title_level == 1
            else html.H3(title, style=title_style)
            if title_level == 3
            else html.H4(title, style=title_style)
            if title_level == 4
            else html.H5(title, style=title_style)
            if title_level == 5
            else html.H6(title, style=title_style)
        )

    if isinstance(content, list):
        elements.extend(content)
    else:
        elements.append(content)

    return html.Div(elements, className=className, style=section_style, id=id)


def apply_content_spacing(layout_elements):

    if not layout_elements or not isinstance(layout_elements, list):
        return layout_elements

    spaced_elements = []

    for i, element in enumerate(layout_elements):
        spaced_elements.append(element)

        if i < len(layout_elements) - 1:
            spaced_elements.append(create_vertical_spacer("section"))

    return spaced_elements


LOADING_STYLES = {
    "default": {
        "spinner_color": get_color("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": get_color("dark"),
        "size": "md",
    },
    "light": {
        "spinner_color": get_color("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.9)",
        "text_color": get_color("dark"),
        "size": "md",
    },
    "dark": {
        "spinner_color": get_color("white"),
        "overlay_color": "rgba(0, 0, 0, 0.7)",
        "text_color": get_color("white"),
        "size": "md",
    },
    "transparent": {
        "spinner_color": get_color("primary"),
        "overlay_color": "rgba(255, 255, 255, 0.4)",
        "text_color": get_color("dark"),
        "size": "md",
    },
    "success": {
        "spinner_color": get_color("success"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": get_color("success"),
        "size": "md",
    },
    "danger": {
        "spinner_color": get_color("danger"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": get_color("danger"),
        "size": "md",
    },
    "warning": {
        "spinner_color": get_color("warning"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": get_color("warning"),
        "size": "md",
    },
    "info": {
        "spinner_color": get_color("info"),
        "overlay_color": "rgba(255, 255, 255, 0.8)",
        "text_color": get_color("info"),
        "size": "md",
    },
}

SPINNER_SIZES = {
    "xs": {"width": "1rem", "height": "1rem", "border_width": "0.15rem"},
    "sm": {"width": "1.5rem", "height": "1.5rem", "border_width": "0.2rem"},
    "md": {"width": "2rem", "height": "2rem", "border_width": "0.25rem"},
    "lg": {"width": "3rem", "height": "3rem", "border_width": "0.3rem"},
    "xl": {"width": "4rem", "height": "4rem", "border_width": "0.35rem"},
}

SKELETON_ANIMATION = (
    "@keyframes skeleton-loading { "
    "0% { background-color: rgba(200, 200, 200, 0.2); } "
    "50% { background-color: rgba(200, 200, 200, 0.6); } "
    "100% { background-color: rgba(200, 200, 200, 0.2); } "
    "}"
)


def create_loading_style(style_key="default", size_key="md"):

    base_style = LOADING_STYLES.get(style_key, LOADING_STYLES["default"])

    size_config = SPINNER_SIZES.get(size_key, SPINNER_SIZES["md"])

    return {**base_style, **size_config}


FORM_VALIDATION_STATES = {
    "valid": {
        "borderColor": SEMANTIC_COLORS["success"],
        "boxShadow": f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['success'], 0.25)}",
    },
    "warning": {
        "borderColor": SEMANTIC_COLORS["warning"],
        "boxShadow": f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['warning'], 0.25)}",
    },
    "danger": {
        "borderColor": SEMANTIC_COLORS["danger"],
        "boxShadow": f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['danger'], 0.25)}",
    },
    "info": {
        "borderColor": SEMANTIC_COLORS["info"],
        "boxShadow": f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['info'], 0.25)}",
    },
}
