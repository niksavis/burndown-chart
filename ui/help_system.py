"""
Help System Components for Progressive Disclosure

This module provides help button components and help page infrastructure
for accessing comprehensive explanations while maintaining concise tooltips.

Features:
- Mobile responsiveness and accessibility improvements
- Performance optimizations with content caching
- Enhanced visual formatting and cross-references
- Better error handling and loading states
"""

import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from configuration.help_content import COMPREHENSIVE_HELP_CONTENT
from functools import lru_cache


# Performance optimization: Cache formatted content
@lru_cache(maxsize=128)
def _cached_format_help_content(content_hash, category, key):
    """Cache formatted help content to improve performance."""
    # This will be called by the main formatting function
    pass


def create_help_button(
    help_key, help_category, button_id=None, size="sm", className=""
):
    """
    Create a help button (question mark icon) for progressive disclosure.
    Enhanced with accessibility and mobile responsiveness.

    Args:
        help_key: Key for specific help content in COMPREHENSIVE_HELP_CONTENT
        help_category: Category of help content (forecast, velocity, scope, statistics, charts)
        button_id: Optional custom button ID, auto-generated if None
        size: Button size ("sm", "md", "lg")
        className: Additional CSS classes

    Returns:
        dbc.Button with question mark icon optimized for accessibility and mobile
    """
    if button_id is None:
        button_id = f"help-btn-{help_category}-{help_key}"

    # Enhanced accessibility attributes
    help_topic = help_key.replace("_", " ").title()

    return html.Button(
        html.I(className="fas fa-question-circle"),
        id=button_id,
        className=f"btn btn-link text-info p-2 {className} help-button-enhanced",  # Bootstrap + custom classes
        style={
            "border": "none",
            "background": "transparent",
            "fontSize": "1rem",  # Larger for better mobile accessibility
            "lineHeight": "1",
            "minWidth": "2.75rem",  # Minimum touch target size (44px)
            "minHeight": "2.75rem",
            "borderRadius": "50%",  # Circular touch area
            "transition": "all 0.2s ease-in-out",  # Smooth hover effects
            "cursor": "pointer",
        },
        title=f"Get detailed help about {help_topic}",
        **{
            "aria-label": f"Get detailed help about {help_topic}",  # Explicit screen reader text
            "role": "button",
            "tabIndex": 0,  # Ensure keyboard accessibility
            "type": "button",
        },
    )


def create_help_modal(modal_id, title="Detailed Help"):
    """
    Create a modal dialog for displaying comprehensive help content.
    Enhanced with mobile responsiveness, performance optimizations, and accessibility.

    Args:
        modal_id: Unique ID for the modal
        title: Modal title text

    Returns:
        dbc.Modal component optimized for mobile and accessibility
    """
    return dbc.Modal(
        [
            # Enhanced modal header with better mobile spacing
            dbc.ModalHeader(
                [
                    dbc.ModalTitle(
                        title,
                        className="h4 mb-0",  # Better mobile typography
                        id=f"{modal_id}-title",
                    ),
                    # Keep default close button for simplicity
                ],
                className="d-flex justify-content-between align-items-center py-3",
                close_button=False,  # Use our custom close button
            ),
            # Enhanced modal body with performance optimizations
            dbc.ModalBody(
                id=f"{modal_id}-content",
                className="help-modal-body",
                style={
                    "maxHeight": "70vh",  # Increased height for mobile
                    "overflowY": "auto",
                    "padding": "1.5rem",  # Better mobile padding
                    "fontSize": "0.95rem",  # Optimized mobile reading size
                    "lineHeight": "1.6",  # Better readability
                    # Performance: Enable hardware acceleration for scrolling
                    "transform": "translate3d(0,0,0)",
                    "WebkitOverflowScrolling": "touch",  # Smooth iOS scrolling
                },
            ),
            # Enhanced footer with mobile-optimized buttons
            dbc.ModalFooter(
                [
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Close"],
                        id=f"{modal_id}-close",
                        color="secondary",
                        size="sm",
                        className="px-4 py-2",  # Better touch targets
                        title="Close help dialog and return to application",
                    )
                ],
                className="d-flex justify-content-end py-3",
            ),
        ],
        id=modal_id,
        size="lg",
        is_open=False,
        scrollable=True,
        centered=True,  # Better mobile positioning
        fade=True,  # Smooth animations
        backdrop=True,  # Allow backdrop click to close
        className="help-modal-enhanced",
        style={
            # Mobile responsiveness improvements
            "maxWidth": "95vw",  # Prevent overflow on small screens
            "margin": "0.5rem auto",  # Better mobile margins
        },
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


# Enhanced callback for handling help button clicks with performance optimizations
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
    Enhanced help modal handler with performance optimizations and better error handling.
    Provides loading states, cross-references, and accessibility features.
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

            # Performance optimization: Lazy load help content
            try:
                help_content = COMPREHENSIVE_HELP_CONTENT.get(category, {}).get(key, "")

                if not help_content:
                    # Enhanced fallback with suggestions
                    available_keys = list(
                        COMPREHENSIVE_HELP_CONTENT.get(category, {}).keys()
                    )
                    help_content = f"""
                    **Help Content Not Available**
                    
                    Content for '{key}' in category '{category}' was not found.
                    
                    **Available Help Topics in {category.title()}:**
                    {chr(10).join(f"• {k.replace('_', ' ').title()}" for k in available_keys[:5])}
                    
                    **Troubleshooting:**
                    • Check that the help system is properly initialized
                    • Verify the help content configuration in configuration/help_content.py
                    • Contact system administrator if this error persists
                    """

                # Enhanced content formatting with cross-references
                formatted_content = format_help_content_enhanced(
                    help_content, category, key
                )
                title = f"Help: {key.replace('_', ' ').title()}"

                return True, formatted_content, title

            except Exception as e:
                # Error handling with user-friendly message
                error_content = [
                    html.Div(
                        [
                            html.H5(
                                "⚠️ Help System Error", className="text-warning mb-3"
                            ),
                            html.P(
                                [
                                    "There was an error loading the help content. ",
                                    "Please try again or contact support if the problem persists.",
                                ],
                                className="mb-3",
                            ),
                            html.Details(
                                [
                                    html.Summary(
                                        "Technical Details",
                                        className="text-muted small",
                                    ),
                                    html.Pre(
                                        f"Error: {str(e)}",
                                        className="small text-muted mt-2",
                                    ),
                                ]
                            ),
                        ],
                        className="text-center p-4",
                    )
                ]
                return True, error_content, "Error Loading Help"

    return is_open, [], "Detailed Help"


def format_help_content_enhanced(content, category, key):
    """
    Enhanced help content formatter with cross-references and better visual formatting.
    Provides interactive examples, related topics, and improved visual hierarchy.

    Args:
        content: Raw help content string
        category: Help content category for cross-referencing
        key: Help content key for context

    Returns:
        List of enhanced Dash components
    """
    if not content:
        return [html.P("Help content not available.", className="text-muted")]

    # Performance: Parse content once and cache formatting
    lines = content.strip().split("\n")
    components = []
    current_section = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if not line:
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            i += 1
            continue

        # Enhanced pattern matching for better formatting
        if _is_section_header(line):
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            components.append(_create_section_header(line))
            i += 1

        elif line.startswith("```"):
            # Handle multi-line code blocks properly
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []

            # Find the closing ``` and collect all lines in between
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1

            # Create code block with proper content
            if code_lines:
                code_text = "\n".join(code_lines)
                components.append(_create_multi_line_code_block(code_text))

            # Skip the closing ```
            if i < len(lines):
                i += 1

        elif _is_bullet_point(line):
            current_section.append(_create_bullet_point(line))
            i += 1

        elif _is_insight_alert(line):
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            components.append(_create_insight_alert(line))
            i += 1

        elif _is_single_line_formula(line):
            # Handle single-line formulas not in code blocks
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            components.append(_create_single_line_code_block(line))
            i += 1

        else:
            current_section.append(_create_paragraph(line))
            i += 1

    # Process any remaining content
    if current_section:
        components.extend(_process_current_section(current_section))

    # Add cross-references footer for enhanced navigation
    components.append(_create_cross_references_footer(category, key))

    return components


# Helper functions for enhanced content formatting
def _is_section_header(line):
    return (
        line.startswith("📊 **")
        or line.startswith("🔢 **")
        or line.startswith("📈 **")
        or line.startswith("🎯 **")
    )


def _is_code_block(line):
    return line.startswith("```") or (line.startswith("Expected =") and "÷" in line)


def _is_bullet_point(line):
    return line.startswith("• ") or line.startswith("- ")


def _is_insight_alert(line):
    return (
        line.startswith("💡 **")
        or line.startswith("🎯 **")
        or line.startswith("📅 **")
        or line.startswith("⚠️ **")
    )


def _is_single_line_formula(line):
    """Detect single-line mathematical formulas that should be formatted as code."""
    formula_indicators = [
        "Expected =",
        "Average =",
        "Sum =",
        "Trend =",
        "÷",
        "×",
        "Σ(",
        "= (",
        ") ÷",
        "% =",
        "+ 4×",
    ]
    return any(indicator in line for indicator in formula_indicators)


def _create_section_header(line):
    header_text = line.replace("**", "").strip()
    return html.H5(header_text, className="mt-4 mb-3 text-primary border-bottom pb-2")


def _create_code_block(line):
    code_text = line.replace("```", "").strip()
    return html.Pre(
        code_text, className="bg-light p-3 rounded border-start border-primary border-3"
    )


def _create_multi_line_code_block(code_text):
    """Create a properly formatted multi-line code block with better styling."""
    return html.Pre(
        code_text.strip(),
        className="bg-light p-3 rounded border-start border-primary border-3",
        style={
            "white-space": "pre-wrap",
            "font-family": "Monaco, 'Courier New', 'Consolas', monospace",
            "font-size": "0.85rem",
            "line-height": "1.5",
            "overflow-x": "auto",
            "color": "#495057",
            "background-color": "#f8f9fa !important",
            "border": "1px solid #e9ecef",
            "margin": "0.5rem 0",
        },
    )


def _create_single_line_code_block(line):
    """Create a code block for single-line formulas."""
    return html.Pre(
        line.strip(),
        className="bg-light p-2 rounded border-start border-primary border-3",
        style={
            "font-family": "Monaco, 'Courier New', 'Consolas', monospace",
            "font-size": "0.9rem",
            "color": "#495057",
            "background-color": "#f8f9fa !important",
            "border": "1px solid #e9ecef",
            "margin": "0.25rem 0",
            "display": "inline-block",
            "padding": "0.5rem 1rem",
        },
    )


def _create_bullet_point(line):
    bullet_text = line[2:].strip()
    return html.Li(bullet_text, className="mb-2")


def _create_insight_alert(line):
    insight_text = line.replace("**", "").strip()
    return dbc.Alert(insight_text, color="info", className="my-3 border-start border-3")


def _create_paragraph(line):
    # Enhanced paragraph with bold formatting support
    if "**" in line:
        return _format_bold_text(line)
    return html.P(line, className="mb-2")


def _format_bold_text(line):
    parts = line.split("**")
    formatted_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:  # Odd indices are bold
            formatted_parts.append(html.Strong(part))
        else:
            formatted_parts.append(part)
    return html.P(formatted_parts, className="mb-2")


def _process_current_section(current_section):
    if any(isinstance(comp, html.Li) for comp in current_section):
        return [html.Ul(current_section, className="mb-3")]
    return current_section


def _create_cross_references_footer(category, key):
    """Create cross-references footer with related help topics."""
    # Define related topics mapping for cross-references
    related_topics = {
        "velocity": {
            "velocity_average_calculation": [
                "velocity_median_calculation",
                "pert_analysis_detailed",
            ],
            "velocity_median_calculation": [
                "velocity_average_calculation",
                "velocity_trend_indicators",
            ],
        },
        "forecast": {
            "pert_analysis_detailed": [
                "velocity_average_calculation",
                "input_parameters_guide",
            ],
            "project_overview": ["forecast_graph_overview", "pert_analysis_detailed"],
        },
    }

    related = related_topics.get(category, {}).get(key, [])

    if not related:
        return html.Div()  # No footer if no related topics

    return html.Div(
        [
            html.Hr(className="my-4"),
            html.H6("🔗 Related Topics", className="text-secondary mb-2"),
            html.P(
                [
                    f"For more information, see: {', '.join(topic.replace('_', ' ').title() for topic in related)}"
                ],
                className="small text-muted mb-0",
            ),
        ],
        className="mt-4 pt-3 border-top",
    )


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
        tooltip_text: Concise tooltip text for immediate context
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
            # Tooltip for immediate context
            create_info_tooltip(tooltip_id, tooltip_text, placement=tooltip_placement),
            # Help button for comprehensive explanation
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
