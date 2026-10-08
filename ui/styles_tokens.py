from dash import html

from configuration import COLOR_PALETTE
from ui.style_constants import (
    NEUTRAL_COLORS,
    SEMANTIC_COLORS,
    TYPOGRAPHY,
)

SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "xxl": "3rem",
}

BREAKPOINTS = {
    "xs": "0px",
    "sm": "576px",
    "md": "768px",
    "lg": "992px",
    "xl": "1200px",
    "xxl": "1400px",
}

MEDIA_QUERIES = {
    "xs": "@media (max-width: 575.98px)",
    "sm": "@media (min-width: 576px)",
    "sm_only": "@media (min-width: 576px) and (max-width: 767.98px)",
    "md": "@media (min-width: 768px)",
    "md_only": "@media (min-width: 768px) and (max-width: 991.98px)",
    "lg": "@media (min-width: 992px)",
    "lg_only": "@media (min-width: 992px) and (max-width: 1199.98px)",
    "xl": "@media (min-width: 1200px)",
    "xl_only": "@media (min-width: 1200px) and (max-width: 1399.98px)",
    "xxl": "@media (min-width: 1400px)",
    "mobile": "@media (max-width: 767.98px)",
    "tablet": "@media (min-width: 768px) and (max-width: 991.98px)",
    "desktop": "@media (min-width: 992px)",
}

VERTICAL_RHYTHM = {
    "base": SPACING["md"],
    "heading": {
        "h1": SPACING["lg"],
        "h2": SPACING["md"],
        "h3": SPACING["md"],
        "h4": SPACING["sm"],
        "h5": SPACING["sm"],
        "h6": SPACING["xs"],
    },
    "paragraph": SPACING["md"],
    "list": SPACING["md"],
    "list_item": SPACING["xs"],
    "section": SPACING["xl"],
    "card": SPACING["lg"],
    "form_element": SPACING["md"],
    "after_title": SPACING["md"],
    "before_title": SPACING["lg"],
}

COMPONENT_SPACING = {
    "card_margin": SPACING["md"],
    "card_padding": SPACING["md"],
    "section_margin": SPACING["lg"],
    "content_block": SPACING["xl"],
    "form_group": SPACING["md"],
    "button_group": SPACING["md"],
    "table_cell_padding": SPACING["sm"],
}

BOOTSTRAP_SPACING = {
    "0": "0",
    "1": SPACING["xs"],
    "2": SPACING["sm"],
    "3": SPACING["md"],
    "4": SPACING["lg"],
    "5": SPACING["xl"],
}

ICON_SIZES = {
    "xs": "0.75rem",
    "sm": "0.875rem",
    "md": "1rem",
    "lg": "1.25rem",
    "xl": "1.5rem",
    "xxl": "2rem",
}

SEMANTIC_ICONS = {
    "items": "fas fa-tasks",
    "points": "fas fa-chart-line",
    "statistics": "fas fa-table",
    "chart": "fas fa-chart-bar",
    "data": "fas fa-database",
    "calendar": "fas fa-calendar-day",
    "date": "fas fa-calendar-alt",
    "deadline": "fas fa-calendar-times",
    "success": "fas fa-check-circle",
    "warning": "fas fa-exclamation-triangle",
    "danger": "fas fa-exclamation-circle",
    "info": "fas fa-info-circle",
    "trend_up": "fas fa-arrow-up",
    "trend_down": "fas fa-arrow-down",
    "trend_neutral": "fas fa-equals",
    "add": "fas fa-plus",
    "edit": "fas fa-pencil-alt",
    "delete": "fas fa-trash",
    "save": "fas fa-save",
    "download": "fas fa-download",
    "upload": "fas fa-upload",
    "export": "fas fa-file-export",
    "import": "fas fa-file-import",
    "back": "fas fa-arrow-left",
    "forward": "fas fa-arrow-right",
    "home": "fas fa-home",
    "settings": "fas fa-cog",
    "help": "fas fa-question-circle",
}

DEFAULT_ICON_STYLES = {
    "marginRight": SPACING["sm"],
    "display": "inline-block",
    "verticalAlign": "middle",
    "lineHeight": "1",
}


def get_breakpoint_value(breakpoint_key):

    return BREAKPOINTS.get(breakpoint_key, BREAKPOINTS["md"])


def get_media_query(breakpoint_key):

    return MEDIA_QUERIES.get(breakpoint_key, MEDIA_QUERIES["md"])


def create_responsive_style(base_style, breakpoint_styles=None):

    if not breakpoint_styles:
        return base_style

    style = base_style.copy()

    for breakpoint, breakpoint_style in breakpoint_styles.items():
        media_query = get_media_query(breakpoint)
        style[media_query] = breakpoint_style

    return style


def create_responsive_container(content, responsive_settings=None):

    if not responsive_settings:
        return html.Div(content)

    class_names = []

    for breakpoint, display in responsive_settings.items():
        if breakpoint == "xs":
            class_names.append(f"d-{display}")
        else:
            class_names.append(f"d-{breakpoint}-{display}")

    return html.Div(content, className=" ".join(class_names))


def create_responsive_text(text, responsive_sizes=None):

    if not responsive_sizes:
        return html.Div(text)

    class_names = []

    for breakpoint, size in responsive_sizes.items():
        if breakpoint == "xs":
            class_names.append(f"fs-{size}")
        else:
            class_names.append(f"fs-{breakpoint}-{size}")

    return html.Div(text, className=" ".join(class_names))


def next_breakpoint(breakpoint):

    breakpoint_order = ["xs", "sm", "md", "lg", "xl", "xxl"]
    try:
        current_index = breakpoint_order.index(breakpoint)
        if current_index < len(breakpoint_order) - 1:
            return breakpoint_order[current_index + 1]
    except ValueError, IndexError:
        pass
    return None


def get_breakpoint_range(start_breakpoint, end_breakpoint=None):

    breakpoint_order = ["xs", "sm", "md", "lg", "xl", "xxl"]

    if start_breakpoint not in breakpoint_order:
        return MEDIA_QUERIES["md"]

    min_width = get_breakpoint_value(start_breakpoint)

    if end_breakpoint and end_breakpoint in breakpoint_order:
        next_bp = next_breakpoint(end_breakpoint)
        if next_bp:
            next_width_px = int(get_breakpoint_value(next_bp).replace("px", ""))
            max_width = f"(max-width: {next_width_px - 0.02}px)"
            return f"@media (min-width: {min_width}) and {max_width}"

    return f"@media (min-width: {min_width})"


def get_color(color_key):

    if color_key in COLOR_PALETTE:
        return COLOR_PALETTE[color_key]
    elif color_key in SEMANTIC_COLORS:
        return SEMANTIC_COLORS[color_key]
    elif color_key in NEUTRAL_COLORS:
        return NEUTRAL_COLORS[color_key]
    else:
        return "#000000"


def get_font_size(size_key):

    return TYPOGRAPHY["scale"].get(size_key, TYPOGRAPHY["base_size"])


def get_font_weight(weight_key):

    return TYPOGRAPHY["weights"].get(weight_key, TYPOGRAPHY["weights"]["regular"])


def get_spacing(spacing_key):

    return SPACING.get(spacing_key, SPACING["md"])


def get_vertical_rhythm(key: str, fallback: str = "base") -> str:

    parts = key.split(".", 1)
    if len(parts) == 1:
        return VERTICAL_RHYTHM.get(key, VERTICAL_RHYTHM.get(fallback, SPACING["md"]))
    category, subkey = parts
    if category in VERTICAL_RHYTHM and isinstance(VERTICAL_RHYTHM[category], dict):
        return VERTICAL_RHYTHM[category].get(
            subkey, VERTICAL_RHYTHM.get(fallback, SPACING["md"])
        )
    return VERTICAL_RHYTHM.get(fallback, SPACING["md"])
