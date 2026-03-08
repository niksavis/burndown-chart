"""
Tooltip Utilities Cards Module

Card and metric tooltip builder components for consistent tooltip
appearance and behavior across Dash UI components.
"""

#######################################################################
# IMPORTS
#######################################################################
import dash_bootstrap_components as dbc

# Third-party library imports
from dash import html

# Local imports
from ui.tooltip_utils_core import (
    create_adaptive_tooltip_config,
    get_smart_placement,
)

#######################################################################
# TOOLTIP COMPONENTS
#######################################################################


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
        max_width (str | None): Maximum width of the tooltip
        className (str): Additional CSS classes
        style (dict): Additional inline styles

    Returns:
        dbc.Tooltip: A styled tooltip component
    """
    # Set up base styling
    if delay is None:
        delay = {"show": 200, "hide": 100}
    tooltip_style = {}
    if max_width:
        tooltip_style["maxWidth"] = max_width
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
        "trigger": trigger,
        "autohide": autohide,
        "className": full_class,
    }

    if tooltip_style:
        tooltip_props["style"] = tooltip_style

    # Only add id if it's not None
    if tooltip_id is not None:
        tooltip_props["id"] = tooltip_id

    return dbc.Tooltip(**tooltip_props)


def create_help_icon(
    tooltip_id: str,
    position: str = "inline",
    icon_class: str = "fas fa-info-circle",
    color: str = "#3b82f6",
) -> html.I:
    """
    Create a standardized help icon with consistent styling.

    This provides a unified way to add help icons across all tabs,
    ensuring consistent positioning, sizing, and color.

    Args:
        tooltip_id: Unique ID for the tooltip target
        position: Icon position - "inline", "header", or "trailing" (default: "inline")
        icon_class: FontAwesome icon class (default: "fas fa-info-circle")
        color: Icon color in hex (default: "#3b82f6" - Brand blue)

    Returns:
        html.I: Icon component with standardized styling

    Examples:
        >>> # Inline help icon next to text
        >>> icon = create_help_icon("items-scope-help", position="inline")

        >>> # Header help icon (aligned with titles)
        >>> icon = create_help_icon("weekly-chart-help", position="header")

        >>> # Trailing help icon (pushed to end of container)
        >>> icon = create_help_icon("forecast-help", position="trailing")
    """
    from ui.style_constants import HELP_ICON_POSITIONS

    # Get position-specific styling
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
    """
    Create an information tooltip component with an info icon.

    Uses the modern Bug Analysis design pattern with:
    - Inline help icon using create_help_icon()
    - Separate dbc.Tooltip with placement="top" by default
    - Consistent styling across the application
    - Dark/blackish background for better readability (default variant="dark")

    Supports multiple calling patterns for maximum compatibility:
    - create_info_tooltip(help_text, id_suffix) - NEW pattern (help text first)
    - create_info_tooltip(id_suffix, help_text) - OLD pattern (id first)
    - create_info_tooltip(help_text=..., id_suffix=...) - KEYWORD pattern
    - create_info_tooltip(id_suffix=..., help_text=...) - KEYWORD pattern (any order)

    Args:
        param1: Either help_text (if longer) or id_suffix (if shorter/simpler)
        param2: Either id_suffix (if param1 is help_text) or help_text (if param1 is id)
        placement: Tooltip placement position (default: "top")
        variant: Tooltip style variant (default: "dark" - blackish background)
        id_suffix: Explicit ID suffix (keyword argument)
        help_text: Explicit help text (keyword argument)

    Returns:
        Dash component with tooltip using Bug Analysis design pattern
    """
    # Handle keyword arguments first
    if id_suffix is not None and help_text is not None:
        # Both keyword args provided - use them directly
        pass
    elif param1 is not None and param2 is not None:
        # Positional arguments - auto-detect parameter order
        # Longer/more complex string is likely help_text
        if " " in str(param1) or len(str(param1)) > 50:
            help_text = param1
            id_suffix = param2
        else:
            # Assume old pattern: id_suffix, help_text
            id_suffix = param1
            help_text = param2
    elif id_suffix is not None:
        # Only id_suffix keyword provided, param1 must be help_text
        help_text = param1
    elif help_text is not None:
        # Only help_text keyword provided, param1 must be id_suffix
        id_suffix = param1
    else:
        raise ValueError(
            "create_info_tooltip requires both help_text and id_suffix parameters"
        )

    # Validate that we have both required parameters
    if id_suffix is None or help_text is None:
        raise ValueError(
            f"create_info_tooltip requires both help_text and id_suffix. "
            f"Got id_suffix={id_suffix!r}, help_text={help_text!r}"
        )

    # Validate placement to ensure it's a valid literal type
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

    # Use the modern help icon pattern from Bug Analysis
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
    """
    Create an enhanced tooltip component with consistent styling and animations.

    Args:
        id_suffix: Suffix for component ID
        help_text: Text to display in the tooltip (can be string or Dash component)
        target: Optional target ID (if not provided, will use info-icon)
        variant: Style variant (dark, primary, info, success, warning, error)
            - default: "dark"
        placement: Tooltip placement (top, bottom, left, right)
        trigger_text: Optional text to show as the tooltip trigger
        icon_class: FontAwesome icon class for custom icon (defaults to info circle)
        delay: Show/hide delay in milliseconds
        smart_positioning: Whether to use smart placement based on context
        dismissible: Whether to include a close button
        expandable: Whether to support expandable detailed content

    Returns:
        Dash component with enhanced tooltip
    """
    # Set up the tooltip target
    if delay is None:
        delay = {"show": 200, "hide": 100}
    tooltip_target = f"tooltip-{id_suffix}"

    # Apply smart positioning if enabled
    if smart_positioning:
        placement = get_smart_placement(placement, mobile_override="bottom")
        delay = create_adaptive_tooltip_config(delay.get("show", 200))

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

    # Enhance content for dismissible or expandable tooltips
    enhanced_content = help_text
    if dismissible or expandable:
        enhanced_content = _create_interactive_content(
            help_text, id_suffix, dismissible, expandable
        )

    # Create the tooltip
    tooltip = create_tooltip(
        content=enhanced_content,
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


def create_dismissible_tooltip(
    id_suffix, help_text, target=None, variant="dark", placement="top"
):
    """
    Create a dismissible tooltip with a close button.

    Args:
        id_suffix: Suffix for component ID
        help_text: Text to display in the tooltip
        target: Target element ID
        variant: Tooltip style variant (default: "dark")
        placement: Tooltip placement

    Returns:
        Dash component with dismissible tooltip
    """
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
    """
    Create an expandable tooltip with summary and detailed content.

    Args:
        id_suffix: Suffix for component ID
        summary_text: Brief summary text (always shown)
        detailed_text: Detailed explanation (shown when expanded)
        target: Target element ID
        variant: Tooltip style variant (default: "dark")
        placement: Tooltip placement

    Returns:
        Dash component with expandable tooltip
    """
    # Combine summary and detailed content
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
    """
    Create interactive content for tooltips with dismiss/expand functionality.

    Args:
        content: Original tooltip content
        id_suffix: ID suffix for interactive elements
        dismissible: Whether to add dismiss functionality
        expandable: Whether to add expand functionality

    Returns:
        Enhanced content with interactive elements
    """
    # Handle expandable content
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

    # Add dismiss button if requested
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
            # Add dismiss button to existing content
            interactive_content.children.append(dismiss_button)
        else:
            # Wrap content with dismiss button
            interactive_content = html.Div([interactive_content, dismiss_button])

    return interactive_content


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


def create_contextual_help(id_suffix, help_text, trigger_text=None, variant="dark"):
    """
    Create a contextual help text with underline indicator for inline help.

    Args:
        id_suffix: Suffix for tooltip ID
        help_text: Help text to display in tooltip
        trigger_text: Text that triggers the tooltip (underlined with dotted line)
        variant: Tooltip variant (default: "dark")

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
