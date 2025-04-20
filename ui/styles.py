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
        "margin": f"{get_spacing('md')} 0 {get_spacing('sm')} 0",
    }

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


def create_button_style(variant="primary", size="md", outline=False, disabled=False):
    """
    Create a consistent button style based on design system.

    Args:
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        outline (bool): Whether the button should have outline style
        disabled (bool): Whether the button is disabled

    Returns:
        dict: Dictionary with button styling properties
    """
    # Base style shared across all buttons
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

    # Size-specific styles
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

    # Apply size-specific styles
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
    # Determine button color
    button_color = variant
    if outline:
        button_color = f"outline-{variant}"

    # Build icon content if provided
    icon = (
        html.I(className=icon_class, style={"marginRight": "0.5rem"})
        if icon_class and icon_position == "left"
        else None
    )
    icon_right = (
        html.I(className=icon_class, style={"marginLeft": "0.5rem"})
        if icon_class and icon_position == "right"
        else None
    )

    # Combine base styling with any custom styles
    button_style = create_button_style(variant, size, outline)
    if style:
        button_style.update(style)

    # Build the button content with optional icon
    if icon and icon_right:
        button_content = [icon, text, icon_right]
    elif icon:
        button_content = [icon, text]
    elif icon_right:
        button_content = [text, icon_right]
    else:
        button_content = text

    # Create the button component with all styling
    button = dbc.Button(
        button_content,
        id=id,
        color=button_color,
        size=size,
        className=className,
        style=button_style,
        **kwargs,
    )

    # Wrap in tooltip if specified
    if tooltip:
        return html.Div(
            [button, dbc.Tooltip(tooltip, target=id, placement=tooltip_placement)],
            style={"display": "inline-block"},
        )

    return button


def create_button_group(buttons, vertical=False, className=""):
    """
    Create a button group with consistent styling.

    Args:
        buttons (list): List of button components
        vertical (bool): Whether to stack buttons vertically
        className (str): Additional CSS classes

    Returns:
        dbc.ButtonGroup: A styled button group component
    """
    return dbc.ButtonGroup(buttons, vertical=vertical, className=className)


def create_action_buttons(
    primary_action=None, secondary_action=None, tertiary_action=None, alignment="right"
):
    """
    Create a set of action buttons following the button hierarchy pattern.

    Args:
        primary_action (dict): Primary action button config (text, id, icon, onClick)
        secondary_action (dict): Secondary action button config
        tertiary_action (dict): Tertiary action button config (often a text link)
        alignment (str): Button alignment (left, center, right)

    Returns:
        html.Div: A div containing the action buttons with appropriate styling
    """
    buttons = []

    # Add tertiary action (usually a link-style button)
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

    # Add secondary action
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

    # Add primary action
    if primary_action:
        primary_btn = create_button(
            primary_action.get("text", "Submit"),
            id=primary_action.get("id"),
            variant="primary",
            size="md",
            icon_class=primary_action.get("icon"),
        )
        buttons.append(primary_btn)

    # Set the flex alignment based on the alignment parameter
    flex_align = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(
        alignment, "flex-end"
    )

    return html.Div(
        buttons, className="d-flex mt-3", style={"justifyContent": flex_align}
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
    # Size adjustments for icon-only buttons to make them more square
    size_padding = {"sm": "0.25rem", "md": "0.375rem", "lg": "0.5rem"}

    button_style = create_button_style(variant, size)
    button_style.update(
        {
            "padding": size_padding.get(size, "0.375rem"),
            "borderRadius": "0.375rem",
            "width": "auto",
            "height": "auto",
            "minWidth": "36px",
            "minHeight": "36px",
        }
    )

    if style:
        button_style.update(style)

    button = dbc.Button(
        html.I(className=icon_class),
        id=id,
        color=variant,
        size=size,
        className=f"d-flex align-items-center justify-content-center {className}",
        style=button_style,
        **kwargs,
    )

    # Wrap in tooltip if specified
    if tooltip and id:
        return html.Div(
            [button, dbc.Tooltip(tooltip, target=id, placement=tooltip_placement)],
            style={"display": "inline-block"},
        )

    return button


#######################################################################
# TOOLTIP STYLING FUNCTIONS
#######################################################################


def get_tooltip_style(variant="default"):
    """
    Get tooltip styling configuration for a specific variant.

    Args:
        variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: Style configuration for the tooltip
    """
    if variant in TOOLTIP_STYLES:
        return TOOLTIP_STYLES[variant]
    return TOOLTIP_STYLES["default"]


def create_hoverlabel_config(variant="default"):
    """
    Create a consistent hoverlabel configuration for Plotly charts.

    Args:
        variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: hoverlabel configuration for Plotly
    """
    style = get_tooltip_style(variant)

    return {
        "bgcolor": style["bgcolor"],
        "bordercolor": style["bordercolor"],
        "font": {
            "family": TYPOGRAPHY["font_family"],
            "size": style["fontsize"],
            "color": style["fontcolor"],
        },
    }


def get_hover_mode(mode_key="standard"):
    """
    Get the appropriate hover mode setting for Plotly charts.

    Args:
        mode_key (str): Key for hover mode (standard, unified, compare, y_unified)

    Returns:
        str: Plotly hover mode setting
    """
    return HOVER_MODES.get(mode_key, HOVER_MODES["standard"])


def format_hover_template(
    title=None, fields=None, extra_info=None, include_extra_tag=True
):
    """
    Create a consistent hover template string for Plotly charts.

    Args:
        title (str, optional): Title to display at the top of the tooltip
        fields (dict, optional): Dictionary of {label: value_template} pairs
        extra_info (str, optional): Additional information for the <extra> tag
        include_extra_tag (bool, optional): Whether to include the <extra> tag

    Returns:
        str: Formatted hover template string for Plotly
    """
    template = []

    # Add title if provided
    if title:
        template.append(f"<b>{title}</b><br>")

    # Add fields if provided
    if fields:
        for label, value in fields.items():
            template.append(f"{label}: {value}<br>")

    # Join all template parts
    hover_text = "".join(template)

    # Add extra tag if requested
    if include_extra_tag:
        if extra_info:
            return f"{hover_text}<extra>{extra_info}</extra>"
        return f"{hover_text}<extra></extra>"

    return hover_text


def create_chart_layout_config(
    title=None, hover_mode="unified", tooltip_variant="default"
):
    """
    Create a consistent layout configuration for Plotly charts.

    Args:
        title (str, optional): Chart title
        hover_mode (str): Hover mode key (standard, unified, compare, y_unified)
        tooltip_variant (str): Tooltip style variant (default, success, warning, error, info)

    Returns:
        dict: Layout configuration for Plotly charts
    """
    layout = {
        "hovermode": get_hover_mode(hover_mode),
        "hoverlabel": create_hoverlabel_config(tooltip_variant),
        "paper_bgcolor": "white",
        "plot_bgcolor": "rgba(255, 255, 255, 0.9)",
    }

    if title:
        layout["title"] = title

    return layout


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
    Get Font Awesome icon class from semantic icon key.

    Args:
        icon_key (str): Semantic icon name (e.g. 'success', 'items')

    Returns:
        str: Font Awesome icon class
    """
    return SEMANTIC_ICONS.get(icon_key, icon_key)


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
    icon_class = get_icon_class(icon)

    # Apply fixed width class if needed
    if with_fixed_width and "fa-fw" not in icon_class:
        icon_class = f"{icon_class} fa-fw"

    # Apply spacing classes
    if with_space_right:
        className = f"{className} me-2"
    if with_space_left:
        className = f"{className} ms-2"

    # Ensure icon has proper base class (font awesome)
    if not any(
        prefix in icon_class for prefix in ["fas ", "far ", "fab ", "fal ", "fad "]
    ):
        icon_class = f"fas {icon_class}"

    # Build icon style
    icon_style = dict(DEFAULT_ICON_STYLES)

    # Add color if provided
    if color:
        icon_style["color"] = get_color(color)

    # Add size if provided
    if size in ICON_SIZES:
        icon_style["fontSize"] = ICON_SIZES[size]
    elif size:  # direct CSS value
        icon_style["fontSize"] = size

    # Add custom styles
    if style:
        icon_style.update(style)

    return html.I(
        className=icon_class + (f" {className}" if className else ""),
        style=icon_style,
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
    # Set alignment style
    alignment_class = {
        "top": "align-items-start",
        "center": "align-items-center",
        "bottom": "align-items-end",
    }.get(alignment, "align-items-center")

    # Create the basic container
    container_class = f"d-flex {alignment_class} {className}"

    # Handle icon color (icon_color overrides color)
    used_icon_color = icon_color if icon_color is not None else color

    # Handle icon size (icon_size overrides size)
    used_icon_size = icon_size if icon_size is not None else size

    # Create the icon
    icon_element = create_icon(
        icon=icon,
        color=used_icon_color,
        size=used_icon_size,
        with_fixed_width=True,
    )

    # Build text style
    text_element_style = {}
    if text_style:
        text_element_style.update(text_style)

    if color:
        text_element_style["color"] = get_color(color)

    # Create text element
    text_element = html.Span(text, style=text_element_style)

    # Position icon and text based on icon_position
    if icon_position == "right":
        content = [text_element, html.Span(icon_element, className="ms-2")]
    else:  # left is default
        content = [html.Span(icon_element, className="me-2"), text_element]

    # Return combined element
    return html.Div(content, className=container_class, id=id)


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
    # Convert size key to numerical value for calculations
    size_value = ICON_SIZES.get(size, ICON_SIZES["md"])
    stack_size = f"calc({size_value} * 2)"

    # Adjust secondary icon size to be slightly smaller
    secondary_size = f"calc({size_value} * 0.65)"

    # Get icon classes
    primary_icon_class = get_icon_class(primary_icon)
    secondary_icon_class = get_icon_class(secondary_icon)

    stack_style = {
        "position": "relative",
        "display": "inline-block",
        "width": stack_size,
        "height": stack_size,
    }

    primary_style = {
        "position": "absolute",
        "top": "0",
        "left": "0",
        "fontSize": size_value,
    }

    secondary_style = {
        "position": "absolute",
        "bottom": "0",
        "right": "0",
        "fontSize": secondary_size,
        "backgroundColor": "white",
        "borderRadius": "50%",
        "padding": "1px",
    }

    if primary_color:
        primary_style["color"] = get_color(primary_color)

    if secondary_color:
        secondary_style["color"] = get_color(secondary_color)

    return html.Span(
        [
            html.I(className=primary_icon_class, style=primary_style),
            html.I(className=secondary_icon_class, style=secondary_style),
        ],
        className=f"icon-stack {className}",
        style=stack_style,
        id=id,
    )
