"""
Grid Templates Module (Updated)

This module contains utility functions for creating content layouts and form elements.
Note: This module has been streamlined as part of deprecation cleanup.

Key functions:
- create_form_group: Create a standardized form group
- create_content_section: Create a standardized content section
- create_tab_content: Create standardized tab content
"""

#######################################################################
# IMPORTS
#######################################################################
from dash import html
import dash_bootstrap_components as dbc

# Import styling functions from ui.styles
from ui.styles import (
    SPACING,
    NEUTRAL_COLORS,
    COMPONENT_SPACING,
    get_vertical_rhythm,
)

#######################################################################
# FORM LAYOUT TEMPLATES
#######################################################################


def create_form_group(
    label, input_component, help_text=None, feedback=None, invalid=False
):
    """
    Create a standardized form group with consistent spacing and alignment.

    Args:
        label: Label text or component
        input_component: The input component
        help_text: Optional help text to display below the input
        feedback: Optional validation feedback text
        invalid: Whether the input is invalid

    Returns:
        A form group div with proper spacing and alignment
    """
    # Use vertical rhythm spacing for form elements
    margin_bottom = get_vertical_rhythm("form_element")

    components = [
        html.Label(label, className="mb-2"),
        input_component,
    ]

    if help_text:
        components.append(html.Small(help_text, className="form-text text-muted mt-1"))

    if feedback:
        feedback_class = "invalid-feedback d-block" if invalid else "invalid-feedback"
        components.append(html.Div(feedback, className=feedback_class))

    return html.Div(components, style={"marginBottom": margin_bottom})


#######################################################################
# CONTENT LAYOUT TEMPLATES
#######################################################################


def create_content_section(title, body, footer=None, section_class=None):
    """
    Create a standardized content section with title, body, and optional footer.

    Args:
        title: Section title component or text
        body: Section body content
        footer: Optional section footer content
        section_class: Additional CSS classes for the section

    Returns:
        A content section div
    """
    components = []

    # Calculate margins using our vertical rhythm system
    title_margin = get_vertical_rhythm("after_title")
    section_margin = get_vertical_rhythm("section")

    # Add title with proper spacing
    if isinstance(title, str):
        components.append(html.H3(title, style={"marginBottom": title_margin}))
    else:
        components.append(html.Div(title, style={"marginBottom": title_margin}))

    # Add body
    components.append(html.Div(body))

    # Add footer if provided
    if footer:
        footer_style = {
            "marginTop": get_vertical_rhythm("paragraph"),
            "paddingTop": get_vertical_rhythm("paragraph"),
            "borderTop": f"1px solid {NEUTRAL_COLORS['gray-300']}",
        }
        components.append(html.Div(footer, style=footer_style))

    # Combine any additional classes with our section margin
    section_style = {"marginBottom": section_margin}

    return html.Div(components, className=section_class, style=section_style)


def create_tab_content(content, padding=None):
    """
    Create standardized tab content with consistent padding.

    Args:
        content: The content to display in the tab
        padding: Padding class to apply

    Returns:
        A div with the tab content and consistent styling
    """
    # Use consistent padding from our spacing system
    if padding is None:
        padding = f"p-{COMPONENT_SPACING['card_padding'].replace('rem', '')}"

    return html.Div(content, className=f"{padding} border border-top-0 rounded-bottom")
