"""
Button Utilities Module

This module provides standardized button components and styling utilities
for consistent button appearance and behavior across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import re
from typing import Optional, Literal

# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html

# Application imports
from ui.styles import TYPOGRAPHY
from ui.style_constants import get_button_style


#######################################################################
# ATOMIC COMPONENT BUILDERS (Following Component Contracts)
#######################################################################


def create_action_button(
    text: str,
    icon: Optional[str] = None,
    variant: str = "primary",
    size: str = "md",
    id_suffix: str = "",
    **kwargs,
) -> dbc.Button:
    """
    Create a standardized action button with optional icon.

    This function follows the component builder contract specification
    in specs/006-ux-ui-redesign/contracts/component-builders.md

    Args:
        text: Button label text (required)
        icon: Font Awesome icon name (e.g., "save", "trash") without "fa-" prefix
        variant: Button style - "primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "link"
        size: Button size - "sm", "md", "lg"
        id_suffix: Unique identifier suffix for button ID
        **kwargs: Additional props (onClick, disabled, className, etc.)

    Returns:
        dbc.Button configured with consistent styling and design tokens

    Raises:
        ValueError: If text is empty or variant is invalid

    Examples:
        >>> create_action_button("Save", "save", variant="primary")
        >>> create_action_button("Delete", "trash", variant="danger", size="sm")
        >>> create_action_button("Cancel", variant="secondary", disabled=True)

    ID Pattern: btn-{text-slugified}[-{id_suffix}]

    Accessibility:
        - Includes aria-label matching text
        - Supports disabled state
        - Minimum 44px touch target on mobile
    """
    # Validation
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

    # Generate ID from text
    text_slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    button_id = f"btn-{text_slug}"
    if id_suffix:
        button_id += f"-{id_suffix}"

    # Build button content with optional icon
    children = []
    if icon:
        # Add "fa-" prefix if not present
        icon_class = f"fas fa-{icon}" if not icon.startswith("fa-") else icon
        children.append(html.I(className=icon_class, style={"marginRight": "0.5rem"}))
    children.append(text)

    # Get standardized styling from design tokens
    button_style = get_button_style(variant, size)

    # Extract custom style from kwargs if provided
    custom_style = kwargs.pop("style", {})
    if custom_style:
        button_style.update(custom_style)

    # Get aria-label from kwargs or use text
    # Note: dbc.Button uses 'title' attribute for accessibility, not 'aria-label'
    aria_label = kwargs.pop("aria_label", text)
    if "title" not in kwargs:
        kwargs["title"] = aria_label

    # Create button with consistent styling
    return dbc.Button(
        children, id=button_id, color=variant, size=size, style=button_style, **kwargs
    )


#######################################################################
# BUTTON STYLING FUNCTIONS (Legacy - to be migrated to design tokens)
#######################################################################


def create_button_style(
    variant="primary", size="md", outline=False, disabled=False, touch_friendly=True
):
    """
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

    # Size-specific styles with mobile optimization
    if touch_friendly:
        # Touch-optimized sizes (minimum 44px height for touch targets on mobile)
        size_styles = {
            "sm": {
                "fontSize": "0.875rem",
                "padding": "0.4rem 0.7rem",  # Increased for better touch targets
                "lineHeight": "1.5",
                "minHeight": "38px",  # Minimum height for touch targets
            },
            "md": {
                "fontSize": "1rem",
                "padding": "0.5rem 0.875rem",  # Increased for better touch targets
                "lineHeight": "1.5",
                "minHeight": "44px",  # Optimal touch target size
            },
            "lg": {
                "fontSize": "1.25rem",
                "padding": "0.625rem 1.1rem",  # Increased for better touch targets
                "lineHeight": "1.5",
                "minHeight": "50px",  # Larger touch target
            },
        }
    else:
        # Standard sizes
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
    """
    Create a standardized Bootstrap button component with optional icon.

    Args:
        text (str, optional): Button text content (required if no icon_class)
        id (str, optional): Button ID for callbacks
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        outline (bool): Whether to use outline style
        icon_class (str, optional): Font Awesome icon class (e.g., "fas fa-download")
        icon_position (str): Icon position relative to text ("left" or "right")
        tooltip (str, optional): Tooltip text
        tooltip_placement: Tooltip placement (auto, top, bottom, left, right, etc.)
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        disabled (bool): Whether the button is disabled
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        Component: A styled button component, possibly wrapped in a tooltip
    """
    # Input validation
    if text is None and icon_class is None:
        text = "Button"  # Default text if neither text nor icon is provided

    # Determine button color
    button_color = variant
    if outline:
        button_color = f"outline-{variant}"

    # Build icon content if provided
    icon = None
    icon_right = None

    if icon_class:
        if icon_position == "left":
            icon = html.I(className=icon_class, style={"marginRight": "0.5rem"})
        else:  # icon_position == "right"
            icon_right = html.I(className=icon_class, style={"marginLeft": "0.5rem"})

    # Combine base styling with any custom styles
    button_style = create_button_style(variant, size, outline, disabled)
    if style:
        button_style.update(style)

    # Build the button content with optional icon
    button_content = []
    if icon:
        button_content.append(icon)
    if text:
        button_content.append(text)
    if icon_right:
        button_content.append(icon_right)

    # If only icon and no text, just use the icon
    if not text and icon_class:
        button_content = html.I(className=icon_class)

    # Create the button component with all styling
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

    # Wrap in tooltip if specified
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
    label,
    id=None,
    color="primary",
    tooltip=None,
    className=None,
    **kwargs,
):
    """Create an icon-only button with accessibility features."""
    # Remove conflicting arguments from kwargs
    button_kwargs = {
        k: v for k, v in kwargs.items() if k not in ["tooltip", "className"]
    }

    # Build the final className
    final_class = f"btn btn-{color} icon-only"
    if className:
        final_class += f" {className}"

    button = html.Button(
        html.I(className=icon_class),
        id=id,
        className=final_class,
        title=tooltip if tooltip else label,  # Use title for tooltip text
        **{"aria-label": label, **button_kwargs},  # Add aria-label directly
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
    """
    Create a standardized close button (X).

    Args:
        id (str, optional): Button ID for callbacks
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        tooltip (str): Tooltip text
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        disabled (bool): Whether the button is disabled
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        Component: A close button component
    """
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
        label="Close",  # Add the required label parameter
        id=id,
        color=variant if variant else "secondary",  # Convert variant to color
        tooltip=tooltip,
        className=className,
        style=button_style,
        disabled=disabled,
        **{
            k: v for k, v in kwargs.items() if k not in ["size", "variant"]
        },  # Filter out invalid attributes
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
    """
    Create a standardized menu button (hamburger icon).

    Args:
        id (str, optional): Button ID for callbacks
        variant (str): Button variant (primary, secondary, success, danger, warning, info, light, dark)
        size (str): Button size (sm, md, lg)
        tooltip (str): Tooltip text
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        disabled (bool): Whether the button is disabled
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        Component: A menu button component
    """
    return create_icon_button(
        icon_class="fas fa-bars",
        label="Menu",  # Add the required label parameter
        id=id,
        color=variant if variant else "primary",  # Convert variant to color
        tooltip=tooltip,
        className=className,
        style=style,
        disabled=disabled,
        **{
            k: v for k, v in kwargs.items() if k not in ["size", "variant"]
        },  # Filter out invalid attributes
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
    """
    Create a segmented button group (radio-style buttons).

    Args:
        options (list): List of dictionaries with 'label', 'value', and optional 'icon_class'
        id (str, optional): Component ID
        value (any, optional): Currently selected value
        size (str): Button size (sm, md, lg)
        variant (str): Button variant (primary, secondary, success, danger, etc.)
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles

    Returns:
        dbc.ButtonGroup: A segmented button group component
    """
    buttons = []

    for i, option in enumerate(options):
        label = option.get("label", f"Option {i + 1}")
        option_value = option.get("value", i)
        icon_class = option.get("icon_class")

        # Check if this option is selected
        active = value == option_value if value is not None else i == 0

        # Create button content
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
    """
    Create a pill-style button that can be toggled.

    Args:
        text (str, optional): Button text
        id (str, optional): Button ID
        icon_class (str, optional): Font Awesome icon class
        selected (bool): Whether the button is selected
        variant (str): Button variant (primary, secondary, success, danger, etc.)
        size (str): Button size (sm, md, lg)
        className (str): Additional CSS classes
        style (dict, optional): Additional inline styles
        **kwargs: Additional keyword arguments to pass to dbc.Button

    Returns:
        dbc.Button: A pill-style button component
    """
    # Default style for pill buttons
    pill_style = {
        "borderRadius": "50rem",
        "fontWeight": "500" if selected else "normal",
    }

    if style:
        pill_style.update(style)

    # Content for the pill button
    content = []
    if icon_class:
        content.append(html.I(className=f"{icon_class} me-1"))
    if text:
        content.append(text)

    # Use solid variant if selected, otherwise use outline variant
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
