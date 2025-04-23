"""
Tooltip Utilities Module

This module provides standardized tooltip components and styling utilities
for consistent tooltip appearance and behavior across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
# (none currently needed)

# Third-party library imports
from dash import html
import dash_bootstrap_components as dbc

# Application imports
from ui.style_constants import TYPOGRAPHY, TOOLTIP_STYLES, HOVER_MODES

#######################################################################
# TOOLTIP STYLING FUNCTIONS
#######################################################################


def get_tooltip_style(variant="default"):
    """
    Get tooltip styling configuration for a specific variant.

    Args:
        variant (str): Tooltip style variant (default, success, warning, error, info, primary, dark)

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
        variant (str): Tooltip style variant (default, success, warning, error, info, primary, dark)

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

    This function formats hover templates for Plotly charts, properly handling
    Plotly's special syntax for format specifiers like %{y:.1f}.

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
            # Don't process the value string, pass it directly to Plotly
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
    Create a consistent chart layout configuration with tooltip settings.

    Args:
        title (str, optional): Chart title
        hover_mode (str): Hover mode setting (standard, unified, compare, y_unified)
        tooltip_variant (str): Tooltip style variant for the chart

    Returns:
        dict: Layout configuration dictionary
    """
    config = {
        "hovermode": get_hover_mode(hover_mode),
        "hoverlabel": create_hoverlabel_config(tooltip_variant),
        "margin": {"l": 40, "r": 40, "t": 60, "b": 40},
    }

    if title:
        config["title"] = {
            "text": title,
            "font": {"family": TYPOGRAPHY["font_family"]},
        }

    return config


#######################################################################
# TOOLTIP COMPONENTS
#######################################################################


def create_tooltip(
    content,
    target=None,
    id=None,
    position="top",
    variant="default",
    delay={"show": 200, "hide": 100},
    max_width="300px",
    className="",
    style=None,
):
    """
    Create a tooltip with consistent styling.

    This is the main tooltip creation function that should be used for
    most tooltip needs throughout the application.

    Args:
        content (str or component): The content to display in the tooltip
        target (str): The ID of the element that triggers the tooltip
        id (str, optional): The ID for the tooltip component itself
        position (str): Tooltip placement (top, bottom, left, right)
        variant (str): Tooltip style variant
        delay (dict): Delay for showing/hiding the tooltip
        max_width (str): Maximum width of the tooltip
        className (str): Additional CSS classes
        style (dict): Additional inline styles

    Returns:
        dbc.Tooltip: A styled tooltip component
    """
    # Set up base styling
    tooltip_style = {"maxWidth": max_width}
    if style:
        tooltip_style.update(style)

    # Apply variant-based class
    variant_class = f"tooltip-{variant}" if variant != "default" else ""
    full_class = f"{variant_class} {className}".strip()

    # Generate a default ID if none provided
    tooltip_id = id
    if tooltip_id is None and target is not None:
        tooltip_id = f"tooltip-for-{target}"

    tooltip_props = {
        "children": content,
        "target": target,
        "placement": position,
        "delay": delay,
        "className": full_class,
        "style": tooltip_style,
    }

    # Only add id if it's not None
    if tooltip_id is not None:
        tooltip_props["id"] = tooltip_id

    return dbc.Tooltip(**tooltip_props)


def create_info_tooltip(id_suffix, help_text, placement="right", variant="info"):
    """
    Create an information tooltip component with an info icon.

    Args:
        id_suffix: Suffix for the component ID
        help_text: Text to display in the tooltip
        placement: Tooltip placement position
        variant: Tooltip style variant

    Returns:
        Dash component with tooltip
    """
    target_id = f"info-tooltip-{id_suffix}"

    return html.Div(
        [
            html.I(
                className="fas fa-info-circle text-info ml-2",
                id=target_id,
                style={"cursor": "pointer", "marginLeft": "5px"},
            ),
            create_tooltip(
                help_text,
                target=target_id,
                position=placement,
                variant=variant,
            ),
        ],
        style={"display": "inline-block"},
    )


def create_enhanced_tooltip(
    id_suffix,
    help_text,
    target=None,
    variant="primary",
    placement="top",
    trigger_text=None,
    icon_class=None,
    delay={"show": 200, "hide": 100},
):
    """
    Create an enhanced tooltip component with consistent styling and animations.

    Args:
        id_suffix: Suffix for component ID
        help_text: Text to display in the tooltip (can be string or Dash component)
        target: Optional target ID (if not provided, will use info-icon)
        variant: Style variant (primary, info, success, warning, error)
        placement: Tooltip placement (top, bottom, left, right)
        trigger_text: Optional text to show as the tooltip trigger
        icon_class: FontAwesome icon class for custom icon (defaults to info circle)
        delay: Show/hide delay in milliseconds

    Returns:
        Dash component with enhanced tooltip
    """
    # Set up the tooltip target
    tooltip_target = f"tooltip-{id_suffix}"

    # Create the trigger element based on parameters
    if target:
        # If a target is specified, we just return the tooltip
        trigger = None
        tooltip_target = target
    elif trigger_text:
        # If trigger text is provided, create a span with the tooltip indicator class
        trigger = html.Span(
            [trigger_text],
            id=tooltip_target,
            className="tooltip-indicator",
            style={"cursor": "help"},
        )
    else:
        # Default to an info icon
        icon = icon_class or "fas fa-info-circle"
        trigger = html.I(
            className=f"{icon} text-{variant}",
            id=tooltip_target,
            style={"cursor": "help", "marginLeft": "5px", "fontSize": "1rem"},
        )

    # Create the tooltip
    tooltip = create_tooltip(
        content=help_text,
        target=tooltip_target,
        position=placement,
        variant=variant,
        delay=delay,
    )

    # Return the combined component
    if trigger:
        return html.Div(
            [trigger, tooltip],
            style={"display": "inline-block"},
        )
    else:
        return tooltip


def create_form_help_tooltip(id_suffix, field_label, help_text, variant="info"):
    """
    Create a form field label with integrated help tooltip.

    Args:
        id_suffix: Suffix for tooltip ID
        field_label: Label text for the form field
        help_text: Help text to display in the tooltip
        variant: Tooltip variant (primary, info, success, warning, error)

    Returns:
        Dash component with label and tooltip
    """
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


def create_contextual_help(id_suffix, help_text, trigger_text=None, variant="primary"):
    """
    Create a contextual help text with underline indicator for inline help.

    Args:
        id_suffix: Suffix for tooltip ID
        help_text: Help text to display in tooltip
        trigger_text: Text that triggers the tooltip (underlined with dotted line)
        variant: Tooltip variant

    Returns:
        Dash component with inline help
    """
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
