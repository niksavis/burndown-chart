"""
ARIA Utilities

This module provides utilities for adding ARIA attributes to components
to improve accessibility.
"""

from dash import html
import dash_bootstrap_components as dbc


def add_aria_label_to_icon_button(component, label, options=None):
    """
    Enhances icon-only buttons with proper ARIA labels.

    Args:
        component: The button component to enhance
        label: The accessible label
        options: Additional options (role, includeTooltip, tooltipPlacement)

    Returns:
        The enhanced component or a list containing the component and tooltip
    """
    options = options or {}

    # Default options
    default_options = {
        "role": "button",
        "include_tooltip": True,
        "tooltip_placement": "top",
    }

    # Merge options
    for key, value in default_options.items():
        if key not in options:
            options[key] = value

    # Add ARIA attributes
    if not hasattr(component, "className"):
        component.className = ""

    component.className += " has-aria-label"
    component.role = options["role"]

    # Convert component.children to a list if it's not already
    if not isinstance(component.children, list):
        component.children = [component.children]

    # Add aria-label attribute using the correct Dash property format
    if hasattr(component, "children"):
        # For HTML components, aria-label should be passed as a constructor argument
        # Since we can't modify it after creation, we'll use title instead
        pass

    # Use title attribute for accessibility (works for screen readers)
    if not hasattr(component, "title") or component.title is None:
        component.title = label

    # Add tooltip if requested
    if options["include_tooltip"] and hasattr(component, "id"):
        tooltip = dbc.Tooltip(
            label, target=component.id, placement=options["tooltip_placement"]
        )
        return [component, tooltip]

    return component


def enhance_checkbox(component, label):
    """
    Enhances a checkbox with proper ARIA attributes.

    Args:
        component: The checkbox component to enhance
        label: The accessible label text

    Returns:
        The enhanced component
    """
    if not hasattr(component, "className"):
        component.className = ""

    component.className += " has-aria-label"
    component.role = "checkbox"

    if hasattr(component, "checked"):
        component["aria-checked"] = bool(component.checked)

    return component


def create_screen_reader_only(text):
    """
    Creates visually hidden text for screen readers.

    Args:
        text: The text content for screen readers

    Returns:
        A component that's visually hidden but accessible to screen readers
    """
    return html.Span(
        text,
        style={
            "position": "absolute",
            "width": "1px",
            "height": "1px",
            "padding": "0",
            "margin": "-1px",
            "overflow": "hidden",
            "clip": "rect(0, 0, 0, 0)",
            "whiteSpace": "nowrap",
            "borderWidth": "0",
        },
    )


def enhance_data_table(table_component, options=None):
    """
    Add appropriate ARIA roles to tables.

    Args:
        table_component: The table component to enhance
        options: Additional options like caption

    Returns:
        The enhanced table component
    """
    options = options or {}

    # Set role="table" on the table element
    table_component.role = "table"

    # Add caption if provided
    if "caption" in options:
        # Find or create a caption element
        caption = None
        children = (
            table_component.children
            if isinstance(table_component.children, list)
            else [table_component.children]
        )

        for i, child in enumerate(children):
            if isinstance(child, html.Caption):
                caption = child
                caption.children = options["caption"]
                break

        if not caption:
            caption = html.Caption(options["caption"])
            children.insert(0, caption)
            table_component.children = children

    # Recursively process table children to add appropriate roles
    def process_table_children(element):
        if not element or not isinstance(element, html.Base):
            return element

        # Add appropriate role based on element type
        if isinstance(element, html.Thead):
            element.role = "rowgroup"  # type: ignore[attr-defined]
        elif isinstance(element, html.Tbody):
            element.role = "rowgroup"  # type: ignore[attr-defined]
        elif isinstance(element, html.Tr):
            element.role = "row"  # type: ignore[attr-defined]
        elif isinstance(element, html.Th):
            element.role = "columnheader"  # type: ignore[attr-defined]
        elif isinstance(element, html.Td):
            element.role = "cell"  # type: ignore[attr-defined]

        # Process children recursively
        if hasattr(element, "children"):
            if isinstance(element.children, list):
                element.children = [
                    process_table_children(child) for child in element.children
                ]
            else:
                element.children = process_table_children(element.children)

        return element

    # Process children
    if hasattr(table_component, "children"):
        if isinstance(table_component.children, list):
            table_component.children = [
                process_table_children(child) for child in table_component.children
            ]
        else:
            table_component.children = process_table_children(table_component.children)

    return table_component
