"""
Help System Components for Phase 9.2 Progressive Disclosure

This module provides help button components and help page infrastructure
for accessing comprehensive explanations while maintaining concise tooltips.
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from configuration.help_content import COMPREHENSIVE_HELP_CONTENT


def create_help_button(
    help_key, help_category, button_id=None, size="sm", className=""
):
    """
    Create a help button (question mark icon) for progressive disclosure.

    Args:
        help_key: Key for specific help content in COMPREHENSIVE_HELP_CONTENT
        help_category: Category of help content (forecast, velocity, scope, statistics, charts)
        button_id: Optional custom button ID, auto-generated if None
        size: Button size ("sm", "md", "lg")
        className: Additional CSS classes

    Returns:
        dbc.Button with question mark icon
    """
    if button_id is None:
        button_id = f"help-btn-{help_category}-{help_key}"

    return dbc.Button(
        html.I(className="fas fa-question-circle"),
        id=button_id,
        size=size,
        color="link",
        className=f"text-info p-1 {className}",
        style={
            "border": "none",
            "background": "transparent",
            "fontSize": "0.9rem",
            "lineHeight": "1",
        },
        title=f"Get detailed help about {help_key.replace('_', ' ')}",
    )


def create_help_modal(modal_id, title="Detailed Help"):
    """
    Create a modal dialog for displaying comprehensive help content.

    Args:
        modal_id: Unique ID for the modal
        title: Modal title text

    Returns:
        dbc.Modal component
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle(title)),
            dbc.ModalBody(
                id=f"{modal_id}-content",
                style={"maxHeight": "60vh", "overflowY": "auto"},
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        "Close", id=f"{modal_id}-close", color="secondary", size="sm"
                    )
                ]
            ),
        ],
        id=modal_id,
        size="lg",
        is_open=False,
        scrollable=True,
    )


def format_help_content(content):
    """
    Format comprehensive help content for display in modal.

    Args:
        content: Raw help content string with markdown-style formatting

    Returns:
        List of Dash components for rendering
    """
    if not content:
        return [html.P("Help content not available.", className="text-muted")]

    # Split content into lines and process formatting
    lines = content.strip().split("\n")
    components = []
    current_section = []

    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                components.extend(current_section)
                current_section = []
            continue

        # Process different formatting patterns
        if (
            line.startswith("📊 **")
            or line.startswith("🔢 **")
            or line.startswith("📈 **")
        ):
            # Section headers with emojis
            if current_section:
                components.extend(current_section)
                current_section = []
            header_text = line.replace("**", "").strip()
            components.append(html.H5(header_text, className="mt-3 mb-2 text-primary"))

        elif line.startswith("• ") or line.startswith("- "):
            # Bullet points
            bullet_text = line[2:].strip()
            current_section.append(html.Li(bullet_text, className="mb-1"))

        elif (
            line.startswith("💡 **")
            or line.startswith("🎯 **")
            or line.startswith("📅 **")
        ):
            # Highlighted insights
            if current_section:
                components.extend(current_section)
                current_section = []
            insight_text = line.replace("**", "").strip()
            components.append(
                dbc.Alert(insight_text, color="info", className="mt-2 mb-2")
            )

        elif "**" in line:
            # Bold text formatting
            parts = line.split("**")
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Odd indices are bold
                    formatted_parts.append(html.Strong(part))
                else:
                    formatted_parts.append(part)
            current_section.append(html.P(formatted_parts, className="mb-2"))

        else:
            # Regular text
            current_section.append(html.P(line, className="mb-2"))

    # Add any remaining content
    if current_section:
        if any(isinstance(comp, html.Li) for comp in current_section):
            # Wrap bullet points in ul
            components.append(html.Ul(current_section, className="mb-3"))
        else:
            components.extend(current_section)

    return components


def create_help_system_layout():
    """
    Create the main help system layout with modal for comprehensive help.

    Returns:
        html.Div containing help system components
    """
    return html.Div(
        [
            # Main help modal
            create_help_modal("main-help-modal", "Comprehensive Help"),
            # Store component for tracking help content
            dcc.Store(id="help-content-store", data={}),
        ],
        id="help-system-container",
    )


# Callback for handling help button clicks and modal display
@callback(
    [
        Output("main-help-modal", "is_open"),
        Output("main-help-modal-content", "children"),
        Output("main-help-modal", "title"),
    ],
    [
        Input(
            {
                "type": "help-button",
                "category": dash.dependencies.ALL,
                "key": dash.dependencies.ALL,
            },
            "n_clicks",
        ),
        Input("main-help-modal-close", "n_clicks"),
    ],
    [State("main-help-modal", "is_open")],
)
def handle_help_modal(help_clicks, close_clicks, is_open):
    """
    Handle help button clicks and modal open/close operations.
    """
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, [], "Detailed Help"

    trigger_id = ctx.triggered[0]["prop_id"]

    # Handle close button
    if "close" in trigger_id:
        return False, [], "Detailed Help"

    # Handle help button clicks - pattern matching callback
    if help_clicks and any(click for click in help_clicks if click):
        # Get the triggered button info from ctx.triggered_id
        if hasattr(ctx, "triggered_id") and ctx.triggered_id:
            # Extract category and key from triggered button ID
            button_info = ctx.triggered_id
            category = button_info.get("category", "")
            key = button_info.get("key", "")

            # Get help content
            help_content = COMPREHENSIVE_HELP_CONTENT.get(category, {}).get(key, "")

            if not help_content:
                # Fallback error content
                help_content = f"Help content not found for category '{category}', key '{key}'. Please check the help content configuration."

            formatted_content = format_help_content(help_content)
            title = f"Help: {key.replace('_', ' ').title()}"

            return True, formatted_content, title

    return is_open, [], "Detailed Help"


def create_help_button_with_tooltip(
    tooltip_text,
    help_key,
    help_category,
    help_button_id=None,
    tooltip_placement="right",
):
    """
    Create a combined tooltip + help button system for progressive disclosure.

    Args:
        tooltip_text: Concise tooltip text (Phase 9.1 simplified)
        help_key: Key for comprehensive help content
        help_category: Category of help content
        help_button_id: Optional custom ID for help button
        tooltip_placement: Tooltip placement direction

    Returns:
        html.Span containing both tooltip icon and help button
    """
    from ui.tooltip_utils import create_info_tooltip

    if help_button_id is None:
        help_button_id = f"help-btn-{help_category}-{help_key}"

    tooltip_id = f"tooltip-{help_category}-{help_key}"

    return html.Span(
        [
            # Tooltip for immediate context (Phase 9.1)
            create_info_tooltip(tooltip_id, tooltip_text, placement=tooltip_placement),
            # Help button for comprehensive explanation (Phase 9.2)
            html.Span(
                [
                    dbc.Button(
                        html.I(className="fas fa-question-circle"),
                        id={
                            "type": "help-button",
                            "category": help_category,
                            "key": help_key,
                        },
                        size="sm",
                        color="link",
                        className="text-secondary p-1 ms-1",
                        style={
                            "border": "none",
                            "background": "transparent",
                            "fontSize": "0.8rem",
                            "lineHeight": "1",
                        },
                        title=f"Get detailed help about {help_key.replace('_', ' ')}",
                    )
                ],
                className="help-button-container",
            ),
        ],
        className="d-inline-flex align-items-center gap-1",
    )


# Helper function to register help content
def register_help_content(category, key, content):
    """
    Register additional help content dynamically.

    Args:
        category: Help category
        key: Help content key
        content: Comprehensive help content
    """
    if category not in COMPREHENSIVE_HELP_CONTENT:
        COMPREHENSIVE_HELP_CONTENT[category] = {}

    COMPREHENSIVE_HELP_CONTENT[category][key] = content
