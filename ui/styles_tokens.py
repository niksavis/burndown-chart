"""
UI Styles Module

This module provides standardized styling utilities for the application UI components.
It implements a design system with consistent colors, typography, and spacing.
"""

#######################################################################
# IMPORTS
#######################################################################

from dash import html

# Import from configuration
from configuration import COLOR_PALETTE

# Import constants from style_constants.py
from ui.style_constants import (
    NEUTRAL_COLORS,
    SEMANTIC_COLORS,
    TYPOGRAPHY,
)

#######################################################################
# CONSTANTS
#######################################################################

# Spacing standards
SPACING = {
    "xs": "0.25rem",  # 4px
    "sm": "0.5rem",  # 8px
    "md": "1rem",  # 16px
    "lg": "1.5rem",  # 24px
    "xl": "2rem",  # 32px
    "xxl": "3rem",  # 48px
}

# Bootstrap breakpoints system
BREAKPOINTS = {
    "xs": "0px",  # Extra small devices (portrait phones)
    "sm": "576px",  # Small devices (landscape phones)
    "md": "768px",  # Medium devices (tablets)
    "lg": "992px",  # Large devices (desktops)
    "xl": "1200px",  # Extra large devices (large desktops)
    "xxl": "1400px",  # Extra extra large (larger desktops)
}

# Media query templates for responsive design
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
    "mobile": "@media (max-width: 767.98px)",  # xs and sm combined
    "tablet": "@media (min-width: 768px) and (max-width: 991.98px)",  # md only
    "desktop": "@media (min-width: 992px)",  # lg, xl, and xxl combined
}

# Vertical Rhythm System - Controls spacing between text elements
VERTICAL_RHYTHM = {
    # Base spacing
    "base": SPACING["md"],  # 16px - Default paragraph spacing
    # Heading margins (bottom spacing)
    "heading": {
        "h1": SPACING["lg"],  # 24px
        "h2": SPACING["md"],  # 16px
        "h3": SPACING["md"],  # 16px
        "h4": SPACING["sm"],  # 8px
        "h5": SPACING["sm"],  # 8px
        "h6": SPACING["xs"],  # 4px
    },
    # Text element spacing
    "paragraph": SPACING["md"],  # 16px - Space after paragraphs
    "list": SPACING["md"],  # 16px - Space after lists
    "list_item": SPACING["xs"],  # 4px - Space between list items
    # Component spacing
    "section": SPACING["xl"],  # 32px - Space between major sections
    "card": SPACING["lg"],  # 24px - Space after cards
    "form_element": SPACING["md"],  # 16px - Space between form elements
    # Text block spacing
    "after_title": SPACING["md"],  # 16px - Space after page/section title
    "before_title": SPACING["lg"],  # 24px - Space before page/section title
}

# Component spacing for standard layout patterns
COMPONENT_SPACING = {
    "card_margin": SPACING["md"],  # 16px - External card margins
    "card_padding": SPACING["md"],  # 16px - Internal card padding
    "section_margin": SPACING["lg"],  # 24px - Section margins
    "content_block": SPACING["xl"],  # 32px - Space between major content blocks
    "form_group": SPACING["md"],  # 16px - Space between form groups
    "button_group": SPACING["md"],  # 16px - Space after button groups
    "table_cell_padding": SPACING["sm"],  # 8px - Table cell padding
}

# Bootstrap spacing mapping for reference
BOOTSTRAP_SPACING = {
    "0": "0",
    "1": SPACING["xs"],
    "2": SPACING["sm"],
    "3": SPACING["md"],
    "4": SPACING["lg"],
    "5": SPACING["xl"],
}

# Icon system constants
ICON_SIZES = {
    "xs": "0.75rem",  # 12px
    "sm": "0.875rem",  # 14px
    "md": "1rem",  # 16px
    "lg": "1.25rem",  # 20px
    "xl": "1.5rem",  # 24px
    "xxl": "2rem",  # 32px
}

# Semantic icon mappings
SEMANTIC_ICONS = {
    # Data & Charts
    "items": "fas fa-tasks",
    "points": "fas fa-chart-line",
    "statistics": "fas fa-table",
    "chart": "fas fa-chart-bar",
    "data": "fas fa-database",
    "calendar": "fas fa-calendar-day",
    "date": "fas fa-calendar-alt",
    "deadline": "fas fa-calendar-times",
    # Status indicators
    "success": "fas fa-check-circle",
    "warning": "fas fa-exclamation-triangle",
    "danger": "fas fa-exclamation-circle",
    "info": "fas fa-info-circle",
    # Trends
    "trend_up": "fas fa-arrow-up",
    "trend_down": "fas fa-arrow-down",
    "trend_neutral": "fas fa-equals",
    # Actions
    "add": "fas fa-plus",
    "edit": "fas fa-pencil-alt",
    "delete": "fas fa-trash",
    "save": "fas fa-save",
    "download": "fas fa-download",
    "upload": "fas fa-upload",
    "export": "fas fa-file-export",
    "import": "fas fa-file-import",
    # Navigation
    "back": "fas fa-arrow-left",
    "forward": "fas fa-arrow-right",
    "home": "fas fa-home",
    "settings": "fas fa-cog",
    "help": "fas fa-question-circle",
}

# Default icon styling
DEFAULT_ICON_STYLES = {
    "marginRight": SPACING["sm"],  # Default right margin for icon+text pattern
    "display": "inline-block",  # Ensure proper alignment with text
    "verticalAlign": "middle",  # Default vertical alignment
    "lineHeight": "1",  # Prevent height discrepancies
}

#######################################################################
# RESPONSIVE DESIGN UTILITIES
#######################################################################


def get_breakpoint_value(breakpoint_key):
    """
    Get the pixel value for a specific breakpoint.

    Args:
        breakpoint_key (str): Key for the breakpoint
            ('xs', 'sm', 'md', 'lg', 'xl', 'xxl')

    Returns:
        str: Pixel value for the breakpoint
    """
    return BREAKPOINTS.get(breakpoint_key, BREAKPOINTS["md"])


def get_media_query(breakpoint_key):
    """
    Get the media query for a specific breakpoint.

    Args:
        breakpoint_key (str): Key for the media query

    Returns:
        str: Media query string
    """
    return MEDIA_QUERIES.get(breakpoint_key, MEDIA_QUERIES["md"])


def create_responsive_style(base_style, breakpoint_styles=None):
    """
    Create a style dictionary with responsive breakpoints.

    Args:
        base_style (dict): Base style that applies to all breakpoints
        breakpoint_styles (dict): Dictionary mapping breakpoint keys to style overrides

    Returns:
        dict: Style dictionary with responsive adjustments
    """
    if not breakpoint_styles:
        return base_style

    # Start with the base style
    style = base_style.copy()

    # Add breakpoint-specific styles
    for breakpoint, breakpoint_style in breakpoint_styles.items():
        media_query = get_media_query(breakpoint)
        style[media_query] = breakpoint_style

    return style


def create_responsive_container(content, responsive_settings=None):
    """
    Create a container with responsive behavior across different breakpoints.

    Args:
        content: Content to place inside the container
        responsive_settings (dict): Dictionary mapping breakpoint keys
            to display settings. Example: {'xs': 'block', 'md': 'flex'}

    Returns:
        html.Div: A responsive container
    """
    if not responsive_settings:
        return html.Div(content)

    # Build className based on responsive settings
    class_names = []

    for breakpoint, display in responsive_settings.items():
        if breakpoint == "xs":
            class_names.append(f"d-{display}")
        else:
            class_names.append(f"d-{breakpoint}-{display}")

    return html.Div(content, className=" ".join(class_names))


def create_responsive_text(text, responsive_sizes=None):
    """
    Create text with responsive font sizes across different breakpoints.

    Args:
        text (str): The text content
        responsive_sizes (dict): Dictionary mapping breakpoint keys to font size classes
                                Example: {'xs': '6', 'md': '5', 'lg': '4'}

    Returns:
        html.Div: Text with responsive font sizes
    """
    if not responsive_sizes:
        return html.Div(text)

    # Build className based on responsive settings
    class_names = []

    for breakpoint, size in responsive_sizes.items():
        if breakpoint == "xs":
            class_names.append(f"fs-{size}")
        else:
            class_names.append(f"fs-{breakpoint}-{size}")

    return html.Div(text, className=" ".join(class_names))


def next_breakpoint(breakpoint):
    """
    Get the next larger breakpoint based on the standard Bootstrap breakpoint sequence.

    Args:
        breakpoint (str): Current breakpoint key

    Returns:
        str: Next larger breakpoint key, or None if already at the largest
    """
    breakpoint_order = ["xs", "sm", "md", "lg", "xl", "xxl"]
    try:
        current_index = breakpoint_order.index(breakpoint)
        if current_index < len(breakpoint_order) - 1:
            return breakpoint_order[current_index + 1]
    except (ValueError, IndexError):
        pass
    return None


def get_breakpoint_range(start_breakpoint, end_breakpoint=None):
    """
    Get a media query for a range of breakpoints.

    Args:
        start_breakpoint (str): Starting breakpoint key
        end_breakpoint (str): Ending breakpoint key (optional)

    Returns:
        str: Media query for the specified range
    """
    breakpoint_order = ["xs", "sm", "md", "lg", "xl", "xxl"]

    if start_breakpoint not in breakpoint_order:
        return MEDIA_QUERIES["md"]  # Default fallback

    min_width = get_breakpoint_value(start_breakpoint)

    if end_breakpoint and end_breakpoint in breakpoint_order:
        next_bp = next_breakpoint(end_breakpoint)
        if next_bp:
            next_width_px = int(get_breakpoint_value(next_bp).replace("px", ""))
            max_width = f"(max-width: {next_width_px - 0.02}px)"
            return f"@media (min-width: {min_width}) and {max_width}"

    return f"@media (min-width: {min_width})"


#######################################################################
# STYLE UTILITY FUNCTIONS
#######################################################################


def get_color(color_key):
    """
    Return color from COLOR_PALETTE, SEMANTIC_COLORS, or NEUTRAL_COLORS.

    Args:
        color_key: String key of the color to retrieve

    Returns:
        Color value or default if not found
    """
    # Check in all color collections
    if color_key in COLOR_PALETTE:
        return COLOR_PALETTE[color_key]
    elif color_key in SEMANTIC_COLORS:
        return SEMANTIC_COLORS[color_key]
    elif color_key in NEUTRAL_COLORS:
        return NEUTRAL_COLORS[color_key]
    else:
        return "#000000"  # Default to black if color not found


def get_font_size(size_key):
    """
    Return font size from typography scale.

    Args:
        size_key: String key of the font size to retrieve

    Returns:
        Font size value or default if not found
    """
    return TYPOGRAPHY["scale"].get(size_key, TYPOGRAPHY["base_size"])


def get_font_weight(weight_key):
    """
    Return font weight from typography weights.

    Args:
        weight_key: String key of the font weight to retrieve

    Returns:
        Font weight value or default if not found
    """
    return TYPOGRAPHY["weights"].get(weight_key, TYPOGRAPHY["weights"]["regular"])


def get_spacing(spacing_key):
    """
    Return spacing value from spacing scale.

    Args:
        spacing_key: String key of the spacing to retrieve

    Returns:
        Spacing value or default if not found
    """
    return SPACING.get(spacing_key, SPACING["md"])


def get_vertical_rhythm(key: str, fallback: str = "base") -> str:
    """
    Get spacing value from the vertical rhythm system.

    Args:
        key: Key in format 'category' or 'category.subcategory'.
             Example: 'paragraph' or 'heading.h1'
        fallback: Fallback key if the requested key is not found

    Returns:
        CSS spacing value string
    """
    parts = key.split(".", 1)
    if len(parts) == 1:
        return VERTICAL_RHYTHM.get(key, VERTICAL_RHYTHM.get(fallback, SPACING["md"]))
    category, subkey = parts
    if category in VERTICAL_RHYTHM and isinstance(VERTICAL_RHYTHM[category], dict):
        return VERTICAL_RHYTHM[category].get(
            subkey, VERTICAL_RHYTHM.get(fallback, SPACING["md"])
        )
    return VERTICAL_RHYTHM.get(fallback, SPACING["md"])
