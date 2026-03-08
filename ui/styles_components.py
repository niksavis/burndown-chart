"""Component-level style builders for form inputs, progress bars, and headings.

This module re-exports the design tokens from styles_tokens so callers
that previously imported them from ui.styles continue to work.
"""

import dash_bootstrap_components as dbc

from configuration import COLOR_PALETTE
from ui.style_constants import (
    NEUTRAL_COLORS,
    SEMANTIC_COLORS,
    TYPOGRAPHY,
    rgb_to_rgba,
)
from ui.styles_tokens import (
    SPACING,
    get_color,
    get_font_size,
    get_font_weight,
    get_vertical_rhythm,
)


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
            "backgroundColor": NEUTRAL_COLORS.get("gray-100"),
            "border": f"1px solid {NEUTRAL_COLORS.get('gray-300')}",
        },
        "info": {
            "backgroundColor": rgb_to_rgba(SEMANTIC_COLORS.get("info"), 0.1),
            "border": f"1px solid {SEMANTIC_COLORS.get('info')}",
        },
        "success": {
            "backgroundColor": rgb_to_rgba(SEMANTIC_COLORS.get("success"), 0.1),
            "border": f"1px solid {SEMANTIC_COLORS.get('success')}",
        },
        "warning": {
            "backgroundColor": rgb_to_rgba(SEMANTIC_COLORS.get("warning"), 0.1),
            "border": f"1px solid {SEMANTIC_COLORS.get('warning')}",
        },
        "danger": {
            "backgroundColor": rgb_to_rgba(SEMANTIC_COLORS.get("danger"), 0.1),
            "border": f"1px solid {SEMANTIC_COLORS.get('danger')}",
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

# These functions have been moved to ui.button_utils
# Use the equivalent functions from button_utils.py instead:
# - create_button_style
# - create_button
# - create_button_group
# - create_action_buttons
# - create_icon_button


#######################################################################
# TOOLTIP STYLING FUNCTIONS
#######################################################################

# These functions have been moved to ui.tooltip_utils
# Use the equivalent functions from tooltip_utils.py instead:
# - get_tooltip_style
# - create_hoverlabel_config
# - get_hover_mode
# - format_hover_template
# - create_chart_layout_config


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

    # Apply size with mobile-first touch target optimization
    size_styles = {
        "sm": {
            # Minimum 38px for small inputs
            "height": "max(calc(1.5em + 0.5rem + 2px), 38px)",
            "padding": "0.25rem 0.5rem",
            "fontSize": "0.875rem",
        },
        "md": {
            # Minimum 44px touch target
            "height": "max(calc(1.5em + 0.75rem + 2px), 44px)",
            "padding": "0.375rem 0.75rem",
            "fontSize": "1rem",
        },
        "lg": {
            # Larger touch target for lg
            "height": "max(calc(1.5em + 1rem + 2px), 48px)",
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
                "boxShadow": (
                    f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['danger'], 0.25)}"
                ),
            }
        )
        return base_style

    # Apply variant styles
    variant_styles = {
        "default": {},
        "success": {
            "borderColor": SEMANTIC_COLORS["success"],
            "boxShadow": (
                f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['success'], 0.25)}"
            ),
        },
        "warning": {
            "borderColor": SEMANTIC_COLORS["warning"],
            "boxShadow": (
                f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['warning'], 0.25)}"
            ),
        },
        "danger": {
            "borderColor": SEMANTIC_COLORS["danger"],
            "boxShadow": (
                f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['danger'], 0.25)}"
            ),
        },
        "info": {
            "borderColor": SEMANTIC_COLORS["info"],
            "boxShadow": f"0 0 0 0.2rem {rgb_to_rgba(SEMANTIC_COLORS['info'], 0.25)}",
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

# These functions have been moved to ui.icon_utils
# Use the equivalent functions from icon_utils.py instead:
# - get_icon_class
# - create_icon
# - create_icon_text
# - create_icon_stack


#######################################################################
# CARD STYLING FUNCTIONS
#######################################################################
