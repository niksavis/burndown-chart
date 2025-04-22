"""
UI Styles Module

This module provides standardized styling utilities for the application UI components.
It implements a design system with consistent colors, typography, and spacing.
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html
import dash_bootstrap_components as dbc

# Import from configuration
from configuration import COLOR_PALETTE

#######################################################################
# CONSTANTS
#######################################################################

# Extended semantic color mappings
SEMANTIC_COLORS = {
    "success": "rgb(40, 167, 69)",  # Bootstrap green
    "warning": "rgb(255, 193, 7)",  # Bootstrap yellow
    "danger": "rgb(220, 53, 69)",  # Bootstrap red
    "info": "rgb(13, 202, 240)",  # Bootstrap cyan
    "secondary": "rgb(108, 117, 125)",  # Bootstrap gray
    "light": "rgb(248, 249, 250)",  # Bootstrap light
    "dark": "rgb(33, 37, 41)",  # Bootstrap dark
}

# Neutral color palette
NEUTRAL_COLORS = {
    "white": "#ffffff",
    "gray-100": "#f8f9fa",
    "gray-200": "#e9ecef",
    "gray-300": "#dee2e6",
    "gray-400": "#ced4da",
    "gray-500": "#adb5bd",
    "gray-600": "#6c757d",
    "gray-700": "#495057",
    "gray-800": "#343a40",
    "gray-900": "#212529",
    "black": "#000000",
}

# Typography system
TYPOGRAPHY = {
    "font_family": "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
    "base_size": "1rem",  # 16px
    "scale": {
        "h1": "2rem",  # 32px
        "h2": "1.75rem",  # 28px
        "h3": "1.5rem",  # 24px
        "h4": "1.25rem",  # 20px
        "h5": "1.1rem",  # ~18px
        "h6": "1rem",  # 16px
        "small": "0.875rem",  # 14px
        "xs": "0.75rem",  # 12px
    },
    "weights": {"light": 300, "regular": 400, "medium": 500, "bold": 700},
}

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

# Tooltip styles configuration
TOOLTIP_STYLES = {
    "default": {
        "bgcolor": "rgba(255, 255, 255, 0.95)",
        "bordercolor": "rgba(200, 200, 200, 0.8)",
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "success": {
        "bgcolor": "rgba(240, 255, 240, 0.95)",
        "bordercolor": SEMANTIC_COLORS["success"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "warning": {
        "bgcolor": "rgba(255, 252, 235, 0.95)",
        "bordercolor": SEMANTIC_COLORS["warning"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "error": {
        "bgcolor": "rgba(255, 235, 235, 0.95)",
        "bordercolor": SEMANTIC_COLORS["danger"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
    "info": {
        "bgcolor": "rgba(235, 250, 255, 0.95)",
        "bordercolor": SEMANTIC_COLORS["info"],
        "fontcolor": NEUTRAL_COLORS["gray-800"],
        "fontsize": 14,
    },
}

# Plotly hovermode settings
HOVER_MODES = {
    "standard": "closest",  # Default Plotly hover mode
    "unified": "x unified",  # Unified x-axis hover
    "compare": "x",  # Compare data points
    "y_unified": "y unified",  # Unified y-axis hover
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
        breakpoint_key (str): Key for the breakpoint ('xs', 'sm', 'md', 'lg', 'xl', 'xxl')

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
        responsive_settings (dict): Dictionary mapping breakpoint keys to display settings
                                   Example: {'xs': 'block', 'md': 'flex'}

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
            max_width = f"(max-width: {int(get_breakpoint_value(next_bp).replace('px', '')) - 0.02}px)"
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


def create_text_style(size="md", weight="regular", color="dark"):
    """
    Create a consistent text style dictionary.

    Args:
        size: Size key from typography scale
        weight: Weight key from typography weights
        color: Color key for the text

    Returns:
        Dictionary with text styling properties
    """
    return {
        "fontSize": get_font_size(size),
        "fontWeight": get_font_weight(weight),
        "color": get_color(color),
        "fontFamily": TYPOGRAPHY["font_family"],
    }


def create_card_style(variant="default"):
    """
    Return consistent card styling based on variant.

    Args:
        variant: Card style variant (default, info, success, warning, danger)

    Returns:
        Dictionary with card styling properties
    """
    base_style = {
        "padding": SPACING["md"],
        "borderRadius": "0.375rem",  # Bootstrap default
        "boxShadow": "0 .125rem .25rem rgba(0,0,0,.075)",  # Bootstrap shadow-sm
    }

    variant_styles = {
        "default": {
            "backgroundColor": get_color("light"),
            "border": f"1px solid {get_color('gray-300')}",
        },
        "info": {
            "backgroundColor": "rgba(13, 202, 240, 0.1)",  # Light info background
            "border": f"1px solid {get_color('info')}",
        },
        "success": {
            "backgroundColor": "rgba(40, 167, 69, 0.1)",  # Light success background
            "border": f"1px solid {get_color('success')}",
        },
        "warning": {
            "backgroundColor": "rgba(255, 193, 7, 0.1)",  # Light warning background
            "border": f"1px solid {get_color('warning')}",
        },
        "danger": {
            "backgroundColor": "rgba(220, 53, 69, 0.1)",  # Light danger background
            "border": f"1px solid {get_color('danger')}",
        },
    }

    # Merge base style with variant-specific style
    return {**base_style, **variant_styles.get(variant, variant_styles["default"])}


def create_progress_bar_style(variant="default", height="20px"):
    """
    Create consistent progress bar styling.

    Args:
        variant: Color variant (default, success, warning, danger)
        height: Height of the progress bar

    Returns:
        Dictionary with progress bar styling properties
    """
    color_map = {
        "default": get_color("primary"),
        "success": get_color("success"),
        "warning": get_color("warning"),
        "danger": get_color("danger"),
    }

    return {
        "height": height,
        "backgroundColor": get_color("gray-200"),
        "borderRadius": "0.25rem",
        "color": color_map.get(variant, color_map["default"]),
    }


def create_heading_style(level, color=None, weight="bold"):
    """
    Create a consistent heading style dictionary.

    Args:
        level (int): Heading level (1-6)
        color (str, optional): Color key or value
        weight (str, optional): Weight key from typography weights

    Returns:
        dict: Style dictionary for heading
    """
    # Map level to h1, h2, etc.
    size_key = f"h{level}" if 1 <= level <= 6 else "h1"

    style = {
        "fontSize": get_font_size(size_key),
        "fontWeight": get_font_weight(weight),
        "fontFamily": TYPOGRAPHY["font_family"],
    }

    # Apply vertical rhythm for margins
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


def create_progress_bar(value, max_value=100, color=None, height=None, label=None):
    """
    Create a standardized progress bar component.

    Args:
        value (float): Current progress value
        max_value (float, optional): Maximum value
        color (str, optional): Color key or direct color value
        height (str, optional): Height of the progress bar
        label (str, optional): Text label to display

    Returns:
        dbc.Progress: A Dash Bootstrap Progress component
    """
    # Calculate percentage
    percentage = (value / max_value * 100) if max_value > 0 else 0

    # Determine color based on value
    if color is None:
        if percentage >= 100:
            bar_color = "success"
        elif percentage >= 66:
            bar_color = "info"
        elif percentage >= 33:
            bar_color = "warning"
        else:
            bar_color = "danger"
    else:
        bar_color = color

    # Create progress bar with consistent styling
    return dbc.Progress(
        value=min(percentage, 100),  # Cap at 100%
        color=bar_color,
        className="mb-2",
        style={"height": height or "1rem"},
        label=label,
    )


#######################################################################
# BUTTON STYLING FUNCTIONS
#######################################################################


def create_button_style(
    variant="primary", size="md", outline=False, disabled=False, touch_friendly=True
):
    """
    DEPRECATED: Use ui.button_utils.create_button_style instead.
    This function will be removed in a future release.

    Create a consistent button style based on design system.

    Args:
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        outline (bool): Whether the button should have outline style
        disabled (bool): Whether the button is disabled
        touch_friendly (bool): Whether to optimize for touch screens (mobile)

    Returns:
        dict: Dictionary with button styling properties
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_button_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.button_utils import create_button_style as new_create_button_style

    return new_create_button_style(
        variant=variant,
        size=size,
        outline=outline,
        disabled=disabled,
        touch_friendly=touch_friendly,
    )


def create_button(
    text,
    id=None,
    variant="primary",
    size="md",
    outline=False,
    icon_class=None,
    icon_position="left",
    tooltip=None,
    tooltip_placement="top",
    className="",
    style=None,
    **kwargs,
):
    """
    DEPRECATED: Use ui.button_utils.create_button instead.
    This function will be removed in a future release.

    Create a standardized Bootstrap button component with optional icon.

    Args:
        text (str): Button text content
        id (str, optional): Button ID for callbacks
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        outline (bool): Whether to use outline style
        icon_class (str, optional): Font Awesome icon class (e.g., "fas fa-download")
        icon_position (str): Icon position relative to text ("left" or "right")
        tooltip (str, optional): Tooltip text
        tooltip_placement (str): Tooltip placement (top, bottom, left, right)
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        Component: A styled button component, possibly wrapped in a tooltip
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_button instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.button_utils import create_button as new_create_button

    return new_create_button(
        text=text,
        id=id,
        variant=variant,
        size=size,
        outline=outline,
        icon_class=icon_class,
        icon_position=icon_position,
        tooltip=tooltip,
        tooltip_placement=tooltip_placement,
        className=className,
        style=style,
        **kwargs,
    )


def create_button_group(buttons, vertical=False, className=""):
    """
    DEPRECATED: Use ui.button_utils.create_button_group instead.
    This function will be removed in a future release.

    Create a button group with consistent styling.

    Args:
        buttons (list): List of button components
        vertical (bool): Whether to stack buttons vertically
        className (str): Additional CSS classes

    Returns:
        dbc.ButtonGroup: A styled button group component
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_button_group instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.button_utils import create_button_group as new_create_button_group

    return new_create_button_group(
        buttons=buttons, vertical=vertical, className=className
    )


def create_action_buttons(
    primary_action=None, secondary_action=None, tertiary_action=None, alignment="right"
):
    """
    DEPRECATED: Use ui.button_utils.create_action_buttons instead.
    This function will be removed in a future release.

    Create a set of action buttons following the button hierarchy pattern.

    Args:
        primary_action (dict): Primary action button config (text, id, icon, onClick)
        secondary_action (dict): Secondary action button config
        tertiary_action (dict): Tertiary action button config (often a text link)
        alignment (str): Button alignment (left, center, right)

    Returns:
        html.Div: A div containing the action buttons with appropriate styling
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_action_buttons instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.button_utils import create_action_buttons as new_create_action_buttons

    return new_create_action_buttons(
        primary_action=primary_action,
        secondary_action=secondary_action,
        tertiary_action=tertiary_action,
        alignment=alignment,
    )


def create_icon_button(
    icon_class,
    id=None,
    variant="primary",
    size="md",
    tooltip=None,
    tooltip_placement="top",
    className="",
    style=None,
    **kwargs,
):
    """
    DEPRECATED: Use ui.button_utils.create_icon_button instead.
    This function will be removed in a future release.

    Create a button with only an icon (no text).

    Args:
        icon_class (str): Font Awesome icon class
        id (str, optional): Button ID for callbacks
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        tooltip (str, optional): Tooltip text
        tooltip_placement (str): Tooltip placement (top, bottom, left, right)
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        Component: An icon button component, possibly wrapped in a tooltip
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.button_utils.create_icon_button instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.button_utils import create_icon_button as new_create_icon_button

    return new_create_icon_button(
        icon_class=icon_class,
        id=id,
        variant=variant,
        size=size,
        tooltip=tooltip,
        tooltip_placement=tooltip_placement,
        className=className,
        style=style,
        **kwargs,
    )


#######################################################################
# TOOLTIP STYLING FUNCTIONS
#######################################################################


def get_tooltip_style(variant="default"):
    """
    DEPRECATED: Use ui.tooltip_utils.get_tooltip_style instead.
    This function will be removed in a future release.

    Get tooltip styling configuration for a specific variant.

    Args:
        variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: Style configuration for the tooltip
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.get_tooltip_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.tooltip_utils import get_tooltip_style as new_get_tooltip_style

    return new_get_tooltip_style(variant)


def create_hoverlabel_config(variant="default"):
    """
    DEPRECATED: Use ui.tooltip_utils.create_hoverlabel_config instead.
    This function will be removed in a future release.

    Create a consistent hoverlabel configuration for Plotly charts.

    Args:
        variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: hoverlabel configuration for Plotly
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_hoverlabel_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.tooltip_utils import (
        create_hoverlabel_config as new_create_hoverlabel_config,
    )

    return new_create_hoverlabel_config(variant)


def get_hover_mode(mode_key="standard"):
    """
    DEPRECATED: Use ui.tooltip_utils.get_hover_mode instead.
    This function will be removed in a future release.

    Get the appropriate hover mode setting for Plotly charts.

    Args:
        mode_key (str): Key for hover mode (standard, unified, compare, y_unified)

    Returns:
        str: Plotly hover mode setting
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.get_hover_mode instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.tooltip_utils import get_hover_mode as new_get_hover_mode

    return new_get_hover_mode(mode_key)


def format_hover_template(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):
    """
    DEPRECATED: Use ui.tooltip_utils.format_hover_template instead.
    This function will be removed in a future release.

    Create a consistent hover template string for Plotly charts.

    Args:
        title (str, optional): Title to display at the top of the tooltip
        fields (dict, optional): Dictionary of {label: value_template} pairs
        extra_info (str, optional): Additional information for the <extra> tag
        include_extra_tag (bool, optional): Whether to include the <extra> tag

    Returns:
        str: Formatted hover template string for Plotly
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.format_hover_template instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.tooltip_utils import format_hover_template as new_format_hover_template

    return new_format_hover_template(
        title=title,
        fields=fields,
        extra_info=extra_info,
        include_extra_tag=include_extra_tag,
    )


def create_chart_layout_config(
    title=None, hover_mode="unified", tooltip_variant="default"
):
    """
    DEPRECATED: Use ui.tooltip_utils.create_chart_layout_config instead.
    This function will be removed in a future release.

    Create a consistent layout configuration for Plotly charts.

    Args:
        title (str, optional): Chart title
        hover_mode (str): Hover mode key (standard, unified, compare, y_unified)
        tooltip_variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: Layout configuration for Plotly charts
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.tooltip_utils.create_chart_layout_config instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.tooltip_utils import (
        create_chart_layout_config as new_create_chart_layout_config,
    )

    return new_create_chart_layout_config(
        title=title, hover_mode=hover_mode, tooltip_variant=tooltip_variant
    )


#######################################################################
# FORM ELEMENT STYLING
#######################################################################


def create_input_style(
    variant="default", disabled=False, size="md", readonly=False, error=False
):
    """
    Create consistent styling for input fields.

    Args:
        variant (str): Input style variant (default, success, warning, danger)
        disabled (bool): Whether the input is disabled
        size (str): Input size (sm, md, lg)
        readonly (bool): Whether the input is read-only
        error (bool): Whether the input has validation errors

    Returns:
        dict: Dictionary with input styling properties
    """
    # Base style
    base_style = {
        "borderRadius": "0.25rem",
        "transition": "border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out",
    }

    # Apply size
    size_styles = {
        "sm": {
            "height": "calc(1.5em + 0.5rem + 2px)",
            "padding": "0.25rem 0.5rem",
            "fontSize": "0.875rem",
        },
        "md": {
            "height": "calc(1.5em + 0.75rem + 2px)",
            "padding": "0.375rem 0.75rem",
            "fontSize": "1rem",
        },
        "lg": {
            "height": "calc(1.5em + 1rem + 2px)",
            "padding": "0.5rem 1rem",
            "fontSize": "1.25rem",
        },
    }
    base_style.update(size_styles.get(size, size_styles["md"]))

    # Apply disabled styles
    if disabled:
        base_style.update(
            {
                "backgroundColor": NEUTRAL_COLORS["gray-200"],
                "opacity": "1",
                "cursor": "not-allowed",
            }
        )

    # Apply readonly styles
    if readonly:
        base_style.update(
            {
                "backgroundColor": NEUTRAL_COLORS["gray-100"],
                "opacity": "1",
                "cursor": "default",
            }
        )

    # Apply error styles - takes precedence over variant
    if error:
        base_style.update(
            {
                "borderColor": SEMANTIC_COLORS["danger"],
                "boxShadow": f"0 0 0 0.2rem rgba({int(SEMANTIC_COLORS['danger'].split(',')[0].replace('rgb(', ''))}, "
                + f"{int(SEMANTIC_COLORS['danger'].split(',')[1])}, "
                + f"{int(SEMANTIC_COLORS['danger'].split(',')[2].replace(')', ''))}, 0.25)",
            }
        )
        return base_style

    # Apply variant styles
    variant_styles = {
        "default": {},
        "success": {
            "borderColor": SEMANTIC_COLORS["success"],
            "boxShadow": f"0 0 0 0.2rem rgba(40, 167, 69, 0.25)",
        },
        "warning": {
            "borderColor": SEMANTIC_COLORS["warning"],
            "boxShadow": f"0 0 0 0.2rem rgba(255, 193, 7, 0.25)",
        },
        "danger": {
            "borderColor": SEMANTIC_COLORS["danger"],
            "boxShadow": f"0 0 0 0.2rem rgba(220, 53, 69, 0.25)",
        },
        "info": {
            "borderColor": SEMANTIC_COLORS["info"],
            "boxShadow": f"0 0 0 0.2rem rgba(13, 202, 240, 0.25)",
        },
    }

    base_style.update(variant_styles.get(variant, variant_styles["default"]))
    return base_style


def create_label_style(required=False, size="md", disabled=False, error=False):
    """
    Create consistent styling for input labels.

    Args:
        required (bool): Whether the field is required
        size (str): Label size (sm, md, lg)
        disabled (bool): Whether the label is for a disabled field
        error (bool): Whether the label is for a field with errors

    Returns:
        dict: Dictionary with label styling properties
    """
    # Base style
    base_style = {
        "display": "inline-block",
        "marginBottom": "0.5rem",
        "fontWeight": TYPOGRAPHY["weights"]["medium"],
    }

    # Apply size
    size_map = {
        "sm": TYPOGRAPHY["scale"]["small"],
        "md": TYPOGRAPHY["scale"]["h6"],
        "lg": TYPOGRAPHY["scale"]["h5"],
    }
    base_style["fontSize"] = size_map.get(size, size_map["md"])

    # Apply disabled styles
    if disabled:
        base_style["color"] = NEUTRAL_COLORS["gray-600"]

    # Apply error styles
    if error:
        base_style["color"] = SEMANTIC_COLORS["danger"]

    return base_style


def create_input_group_style(size="md"):
    """
    Create consistent styling for input groups.

    Args:
        size (str): Input group size (sm, md, lg)

    Returns:
        dict: Dictionary with input group styling properties
    """
    return {
        "display": "flex",
        "position": "relative",
        "width": "100%",
        "marginBottom": "1rem",
    }


def create_form_feedback_style(type="invalid"):
    """
    Create consistent styling for form feedback messages.

    Args:
        type (str): Feedback type (valid, invalid)

    Returns:
        dict: Dictionary with form feedback styling properties
    """
    base_style = {
        "display": "block",
        "width": "100%",
        "marginTop": "0.25rem",
        "fontSize": TYPOGRAPHY["scale"]["small"],
    }

    if type == "valid":
        base_style["color"] = SEMANTIC_COLORS["success"]
    else:
        base_style["color"] = SEMANTIC_COLORS["danger"]

    return base_style


def create_slider_style(disabled=False, vertical=False, error=False):
    """
    Create consistent styling for sliders.

    Args:
        disabled (bool): Whether the slider is disabled
        vertical (bool): Whether the slider is vertical
        error (bool): Whether the slider has validation errors

    Returns:
        dict: Dictionary with slider styling properties
    """
    base_style = {
        "margin": "1rem 0",
    }

    if vertical:
        base_style["height"] = "300px"

    if disabled:
        base_style["opacity"] = "0.5"
        base_style["cursor"] = "not-allowed"

    return base_style


def create_datepicker_style(size="md", disabled=False, error=False):
    """
    Create consistent styling for date pickers.

    Args:
        size (str): Date picker size (sm, md, lg)
        disabled (bool): Whether the date picker is disabled
        error (bool): Whether the date picker has validation errors

    Returns:
        dict: Dictionary with date picker styling properties
    """
    # Start with input style as a base
    base_style = create_input_style(disabled=disabled, size=size, error=error)

    # Add date picker specific styles
    base_style.update(
        {
            "width": "100%",
            "borderRadius": "0.25rem",
        }
    )

    return base_style


#######################################################################
# ICON UTILITY FUNCTIONS
#######################################################################


def get_icon_class(icon_key):
    """
    DEPRECATED: Use ui.icon_utils.get_icon_class instead.
    This function will be removed in a future release.

    Get Font Awesome icon class from semantic icon key.

    Args:
        icon_key (str): Semantic icon name (e.g. 'success', 'items')

    Returns:
        str: Font Awesome icon class
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.icon_utils.get_icon_class instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.icon_utils import get_icon_class as new_get_icon_class

    return new_get_icon_class(icon_key)


def create_icon(
    icon,
    color=None,
    size="md",
    className="",
    style=None,
    with_fixed_width=True,
    with_space_right=False,
    with_space_left=False,
    id=None,
):
    """
    DEPRECATED: Use ui.icon_utils.create_icon instead.
    This function will be removed in a future release.

    Create a standardized icon component with consistent styling.

    Args:
        icon (str): Icon key from SEMANTIC_ICONS or direct Font Awesome class
        color (str, optional): Color key or CSS color value
        size (str, optional): Size key from ICON_SIZES or CSS size
        className (str, optional): Additional CSS classes
        style (dict, optional): Additional inline styles
        with_fixed_width (bool): Apply the 'fa-fw' class for fixed width icons
        with_space_right (bool): Add space to the right of the icon
        with_space_left (bool): Add space to the left of the icon
        id (str, optional): Component ID

    Returns:
        html.I: Icon component with standardized styling
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.icon_utils.create_icon instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.icon_utils import create_icon as new_create_icon

    return new_create_icon(
        icon=icon,
        color=color,
        size=size,
        className=className,
        style=style,
        with_fixed_width=with_fixed_width,
        with_space_right=with_space_right,
        with_space_left=with_space_left,
        id=id,
    )


def create_icon_text(
    icon,
    text,
    color=None,
    icon_color=None,
    size="md",
    icon_size=None,
    icon_position="left",
    className="",
    text_style=None,
    alignment="center",
    id=None,
):
    """
    DEPRECATED: Use ui.icon_utils.create_icon_text instead.
    This function will be removed in a future release.

    Create a standardized icon + text combination with proper alignment.

    Args:
        icon (str): Icon key from SEMANTIC_ICONS or direct Font Awesome class
        text (str): Text content
        color (str, optional): Color for both icon and text
        icon_color (str, optional): Color for icon only (overrides color)
        size (str, optional): Size for both icon and text
        icon_size (str, optional): Size for icon only (overrides size)
        icon_position (str): 'left' or 'right'
        className (str, optional): Additional CSS classes
        text_style (dict, optional): Additional text styles
        alignment (str): Vertical alignment (top, center, bottom)
        id (str, optional): Component ID

    Returns:
        html.Div: Icon + text combination with standardized alignment
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.icon_utils.create_icon_text instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.icon_utils import create_icon_text as new_create_icon_text

    return new_create_icon_text(
        icon=icon,
        text=text,
        color=color,
        icon_color=icon_color,
        size=size,
        icon_size=icon_size,
        icon_position=icon_position,
        className=className,
        text_style=text_style,
        alignment=alignment,
        id=id,
    )


def create_icon_stack(
    primary_icon,
    secondary_icon,
    primary_color=None,
    secondary_color=None,
    size="md",
    className="",
    id=None,
):
    """
    DEPRECATED: Use ui.icon_utils.create_icon_stack instead.
    This function will be removed in a future release.

    Create a stacked icon combination (one icon overlaying another).

    Args:
        primary_icon (str): Primary icon class or key
        secondary_icon (str): Secondary icon class or key
        primary_color (str, optional): Color for primary icon
        secondary_color (str, optional): Color for secondary icon
        size (str, optional): Size key from ICON_SIZES
        className (str, optional): Additional CSS classes
        id (str, optional): Component ID

    Returns:
        html.Span: Stacked icon combination
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.icon_utils.create_icon_stack instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.icon_utils import create_icon_stack as new_create_icon_stack

    return new_create_icon_stack(
        primary_icon=primary_icon,
        secondary_icon=secondary_icon,
        primary_color=primary_color,
        secondary_color=secondary_color,
        size=size,
        className=className,
        id=id,
    )


#######################################################################
# CARD STYLING FUNCTIONS
#######################################################################


def create_standardized_card(
    header_content,
    body_content,
    className="",
    card_style=None,
    body_className="",
    header_className="",
    footer_content=None,
    footer_className="",
    shadow="sm",
):
    """
    Create a standardized Bootstrap card with consistent padding and spacing.

    Args:
        header_content: Content for the card header
        body_content: Content for the card body
        className (str, optional): Additional classes for the card
        card_style (dict, optional): Custom styles for the card
        body_className (str, optional): Additional classes for the card body
        header_className (str, optional): Additional classes for the card header
        footer_content (optional): Content for the card footer (if needed)
        footer_className (str, optional): Additional classes for the card footer
        shadow (str): Shadow size (sm, md, lg, none)

    Returns:
        dbc.Card: A standardized Bootstrap card component
    """
    import dash_bootstrap_components as dbc

    # Add vertical rhythm spacing using our component spacing
    className = f"{className} mb-{BOOTSTRAP_SPACING['3']}"

    # Apply consistent internal padding
    body_className = f"{body_className} py-3 px-3"
    header_className = f"{header_className} py-2 px-3"
    footer_className = f"{footer_className} py-2 px-3"

    # Add shadow class if requested
    if shadow and shadow != "none":
        if shadow in ["sm", "md", "lg"]:
            className = f"{className} shadow-{shadow}"
        else:
            className = f"{className} shadow-sm"  # Default to small shadow

    # Create the card components
    card_components = []

    # Add header if content is provided
    if header_content:
        card_components.append(
            dbc.CardHeader(header_content, className=header_className)
        )

    # Add body content
    card_components.append(dbc.CardBody(body_content, className=body_className))

    # Add footer if content is provided
    if footer_content:
        card_components.append(
            dbc.CardFooter(footer_content, className=footer_className)
        )

    # Create the final card with all components
    return dbc.Card(
        card_components,
        className=className,
        style=card_style,
    )


def create_card_header_with_tooltip(title, tooltip_id=None, tooltip_text=None):
    """
    Create a standardized card header with an optional tooltip.

    Args:
        title (str): Card title text
        tooltip_id (str, optional): ID for the tooltip
        tooltip_text (str, optional): Tooltip text content

    Returns:
        list: Components for card header with tooltip
    """
    from dash import html

    # Import the tooltip function from components module if needed
    from ui.components import create_info_tooltip

    if tooltip_id and tooltip_text:
        return [
            html.H4(title, className="d-inline"),
            create_info_tooltip(tooltip_id, tooltip_text),
        ]
    else:
        return html.H4(title, className="d-inline")


#######################################################################
# VERTICAL RHYTHM FUNCTIONS
#######################################################################


def get_vertical_rhythm(key, fallback="base"):
    """
    Get spacing value from vertical rhythm system.

    Args:
        key (str): Key in format 'category' or 'category.subcategory'.
                   Example: 'paragraph' or 'heading.h1'
        fallback (str): Fallback key if the requested key is not found

    Returns:
        str: CSS spacing value
    """
    parts = key.split(".", 1)
    if len(parts) == 1:
        # Simple key like 'paragraph'
        return VERTICAL_RHYTHM.get(key, VERTICAL_RHYTHM.get(fallback, SPACING["md"]))
    else:
        # Nested key like 'heading.h1'
        category, subkey = parts
        if category in VERTICAL_RHYTHM and isinstance(VERTICAL_RHYTHM[category], dict):
            return VERTICAL_RHYTHM[category].get(
                subkey, VERTICAL_RHYTHM.get(fallback, SPACING["md"])
            )
        return VERTICAL_RHYTHM.get(fallback, SPACING["md"])


def apply_vertical_rhythm(element_type="paragraph", style=None):
    """
    Add vertical rhythm spacing to a style dictionary.

    Args:
        element_type (str): Type of element ('paragraph', 'heading.h1', etc.)
        style (dict, optional): Existing style dictionary to extend

    Returns:
        dict: Style dictionary with vertical rhythm applied
    """
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
    """
    Create text elements with proper vertical rhythm applied.

    Args:
        text (str or list): Text content
        element_type (str): Type of element ('paragraph', 'heading.h1', etc.)
        size (str, optional): Text size
        weight (str, optional): Text weight
        color (str, optional): Text color
        className (str, optional): Additional CSS classes

    Returns:
        html.Div: Text element with proper rhythm
    """
    text_style = create_text_style(
        size=size or "md", weight=weight or "regular", color=color or "dark"
    )

    rhythm_style = apply_vertical_rhythm(element_type, text_style)

    return html.Div(text, className=className, style=rhythm_style)


def create_vertical_spacer(size="md"):
    """
    Create a vertical spacing element of a specific size.

    Args:
        size (str): Size key from SPACING or a specific rhythm key

    Returns:
        html.Div: A div that acts as a spacer
    """
    if size in SPACING:
        height = SPACING[size]
    elif "." in size:
        height = get_vertical_rhythm(size)
    else:
        height = get_vertical_rhythm(size, "base")

    return html.Div(style={"height": height})


def update_heading_style(level, color=None, weight="bold"):
    """
    Update create_heading_style to use the vertical rhythm system.

    Args:
        level (int): Heading level (1-6)
        color (str, optional): Color key or value
        weight (str, optional): Weight key from typography weights

    Returns:
        dict: Style dictionary for heading with proper rhythm
    """
    # Map level to h1, h2, etc.
    size_key = f"h{level}" if 1 <= level <= 6 else "h1"

    style = {
        "fontSize": get_font_size(size_key),
        "fontWeight": get_font_weight(weight),
        "fontFamily": TYPOGRAPHY["font_family"],
    }

    # Apply vertical rhythm margin
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
    """
    Create a content section with proper vertical rhythm spacing.

    Args:
        content: The main content of the section
        title (str, optional): Section title
        title_level (int): Heading level for title (1-6)
        title_color (str, optional): Color for the title
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        section_type (str): Type of section for rhythm ('section', 'subsection', etc.)
        id (str, optional): ID for the section

    Returns:
        html.Div: A section with proper vertical rhythm
    """
    from dash import html

    # Get section margin based on type
    margin_bottom = get_vertical_rhythm(section_type, "section")

    # Start with base section styles
    section_style = {
        "marginBottom": margin_bottom,
    }

    # Add any custom styles
    if style:
        section_style.update(style)

    # Create content elements
    elements = []

    # Add title if provided
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

    # Add main content
    if isinstance(content, list):
        elements.extend(content)
    else:
        elements.append(content)

    # Create the section container
    return html.Div(elements, className=className, style=section_style, id=id)


def apply_content_spacing(layout_elements):
    """
    Apply consistent spacing between layout elements.

    This function wraps multiple content elements with proper vertical spacing.

    Args:
        layout_elements (list): List of layout elements to space properly

    Returns:
        list: Elements with proper spacing applied
    """
    from dash import html

    if not layout_elements or not isinstance(layout_elements, list):
        return layout_elements

    spaced_elements = []

    for i, element in enumerate(layout_elements):
        spaced_elements.append(element)

        # Add spacer between elements, but not after the last one
        if i < len(layout_elements) - 1:
            spaced_elements.append(create_vertical_spacer("section"))

    return spaced_elements


#######################################################################
# LOADING STATE COMPONENTS
#######################################################################

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

SKELETON_ANIMATION = "@keyframes skeleton-loading { 0% { background-color: rgba(200, 200, 200, 0.2); } 50% { background-color: rgba(200, 200, 200, 0.6); } 100% { background-color: rgba(200, 200, 200, 0.2); } }"


def get_loading_style(style_key="default", size_key="md"):
    """
    Get loading spinner styling based on predefined styles.

    Args:
        style_key (str): Key for loading style (default, light, dark, etc.)
        size_key (str): Size of the spinner (xs, sm, md, lg, xl)

    Returns:
        dict: Style configuration for loading spinner
    """
    # Get base style
    base_style = LOADING_STYLES.get(style_key, LOADING_STYLES["default"])

    # Get size configuration
    size_config = SPINNER_SIZES.get(size_key, SPINNER_SIZES["md"])

    # Return combined configuration
    return {**base_style, **size_config}


def create_spinner_style(style_key="default", size_key="md", custom_style=None):
    """
    DEPRECATED: Use loading_utils.create_spinner_style instead.
    This function will be removed in a future release.

    Create CSS style for spinner components.

    Args:
        style_key (str): Color style key
        size_key (str): Size key (sm, md, lg)
        custom_style (dict): Additional custom styles to apply

    Returns:
        dict: Dictionary of CSS styles for the spinner
    """
    import warnings

    warnings.warn(
        "create_spinner_style is deprecated. Use loading_utils.create_spinner_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from ui.loading_utils import create_spinner_style as new_create_spinner_style

    return new_create_spinner_style(style_key, size_key, custom_style)


def create_loading_overlay_style(style_key="default", custom_style=None):
    """
    DEPRECATED: Use loading_utils module instead.
    This function will be removed in a future release.

    Create CSS style for loading overlays.

    Args:
        style_key (str): Color style key
        custom_style (dict): Additional custom styles to apply

    Returns:
        dict: Dictionary of CSS styles for the loading overlay
    """
    import warnings

    warnings.warn(
        "create_loading_overlay_style is deprecated. Use loading_utils module instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    # Return styles from loading_utils if possible, otherwise use original implementation
    try:
        from ui.loading_utils import LOADING_STYLES

        # Default styles
        overlay_style = {
            "position": "absolute",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "backgroundColor": LOADING_STYLES.get(style_key, LOADING_STYLES["default"])[
                "overlay_color"
            ],
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "zIndex": "1000",
        }

        # Add any custom styles
        if custom_style:
            overlay_style.update(custom_style)

        return overlay_style
    except (ImportError, KeyError):
        # Fallback to original implementation
        # Base color mapping
        colors = {
            "default": "rgba(255, 255, 255, 0.8)",
            "light": "rgba(255, 255, 255, 0.9)",
            "dark": "rgba(0, 0, 0, 0.7)",
            "transparent": "rgba(255, 255, 255, 0.4)",
        }

        # Get color from mapping or use default
        overlay_color = colors.get(style_key, colors["default"])

        # Default overlay styles
        overlay_style = {
            "position": "absolute",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "backgroundColor": overlay_color,
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "zIndex": "1000",
        }

        # Add any custom styles
        if custom_style:
            overlay_style.update(custom_style)

        return overlay_style


def create_spinner(
    style_key="primary", size_key="md", text=None, className="", id=None
):
    """
    DEPRECATED: Use loading_utils.create_spinner instead.
    This function will be removed in a future release.

    Create a spinner loading indicator with optional text.

    Args:
        style_key (str): Color style key (primary, secondary, etc.)
        size_key (str): Size key (sm, md, lg)
        text (str): Optional text to display under the spinner
        className (str): Additional CSS classes
        id (str): Component ID

    Returns:
        html.Div: A spinner component
    """
    import warnings

    warnings.warn(
        "create_spinner is deprecated. Use loading_utils.create_spinner instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from ui.loading_utils import create_spinner as new_create_spinner

    return new_create_spinner(style_key, size_key, text, className, id)


def create_loading_overlay(
    children,
    style_key="primary",
    size_key="md",
    text=None,
    is_loading=False,
    opacity=0.7,
    className="",
):
    """
    DEPRECATED: Use loading_utils.create_loading_overlay instead.
    This function will be removed in a future release.

    Create a loading overlay that covers content while loading.

    Args:
        children: Content to display when not loading
        style_key (str): Color style for the spinner
        size_key (str): Size of the spinner
        text (str): Optional text to display during loading
        is_loading (bool): Whether to show the loading state
        opacity (float): Opacity of the overlay background
        className (str): Additional CSS classes

    Returns:
        html.Div: A component with loading overlay
    """
    import warnings

    warnings.warn(
        "create_loading_overlay is deprecated. Use loading_utils.create_loading_overlay instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from ui.loading_utils import create_loading_overlay as new_create_loading_overlay

    return new_create_loading_overlay(
        children, style_key, size_key, text, is_loading, opacity, className
    )


def create_skeleton_loader(
    type="text", lines=1, width="100%", height=None, className=""
):
    """
    DEPRECATED: Use loading_utils.create_skeleton_loader instead.
    This function will be removed in a future release.

    Create skeleton loading placeholders for content.

    Args:
        type (str): Type of skeleton ('text', 'card', 'circle', 'chart', 'image')
        lines (int): Number of lines for text skeletons
        width (str): Width of the skeleton
        height (str): Height of the skeleton (optional)
        className (str): Additional CSS classes

    Returns:
        html.Div: Skeleton loader component
    """
    import warnings

    warnings.warn(
        "create_skeleton_loader is deprecated. Use loading_utils.create_skeleton_loader instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    from ui.loading_utils import create_skeleton_loader as new_create_skeleton_loader

    return new_create_skeleton_loader(type, lines, width, height, className)


#######################################################################
# ERROR STYLE FUNCTIONS
#######################################################################


# These functions have been moved to ui.error_states
# Use the equivalent functions from error_states.py instead:
# - create_error_style
# - create_error_message_style
# - create_form_error_style
# - create_empty_state_style


def create_error_style(variant="danger", background=True):
    """
    DEPRECATED: Use ui.error_states.create_error_style instead.
    This function will be removed in a future release.
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.error_states.create_error_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.error_states import create_error_style as new_create_error_style

    return new_create_error_style(variant=variant, background=background)


def create_error_message_style(color="danger", size="md"):
    """
    DEPRECATED: Use ui.error_states.create_error_message_style instead.
    This function will be removed in a future release.
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.error_states.create_error_message_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.error_states import (
        create_error_message_style as new_create_error_message_style,
    )

    return new_create_error_message_style(color=color, size=size)


def create_form_error_style(size="sm"):
    """
    DEPRECATED: Use ui.error_states.create_form_error_style instead.
    This function will be removed in a future release.
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.error_states.create_form_error_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.error_states import create_form_error_style as new_create_form_error_style

    return new_create_form_error_style(size=size)


def create_empty_state_style(variant="default"):
    """
    DEPRECATED: Use ui.error_states.create_empty_state_style instead.
    This function will be removed in a future release.
    """
    import warnings

    warnings.warn(
        "This function is deprecated. Use ui.error_states.create_empty_state_style instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from ui.error_states import create_empty_state_style as new_create_empty_state_style

    return new_create_empty_state_style(variant=variant)
