"""
Tooltip Utilities Module

This module provides standardized tooltip components and styling utilities
for consistent tooltip appearance and behavior across the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
from functools import lru_cache
import time

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
    Format a consistent hover template string for Plotly charts.

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
    title=None, hover_mode="unified", tooltip_variant="dark"
):
    """
    Create a consistent chart layout configuration with tooltip settings.

    Args:
        title (str, optional): Chart title
        hover_mode (str): Hover mode setting (standard, unified, compare, y_unified)
        tooltip_variant (str): Tooltip style variant for the chart (default: "dark")

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
# TOOLTIP PERFORMANCE UTILITIES
#######################################################################

# Global cache for frequently accessed tooltip content
_tooltip_cache = {}
_cache_timestamps = {}
_CACHE_TTL = 300  # 5 minutes cache TTL


@lru_cache(maxsize=128)
def get_cached_tooltip_style(variant="default"):
    """
    Get tooltip styling configuration with LRU caching for performance.

    Args:
        variant (str): Tooltip style variant

    Returns:
        dict: Cached style configuration
    """
    return get_tooltip_style(variant)


@lru_cache(maxsize=64)
def get_cached_hover_config(variant="default"):
    """
    Get cached hoverlabel configuration for Plotly charts.

    Args:
        variant (str): Tooltip style variant

    Returns:
        dict: Cached hoverlabel configuration
    """
    return create_hoverlabel_config(variant)


def cache_tooltip_content(key, content, ttl=None):
    """
    Cache tooltip content for reuse across components.

    Args:
        key (str): Cache key for the content
        content: Content to cache (string or Dash component)
        ttl (int): Time to live in seconds (default: 300)
    """
    ttl = ttl or _CACHE_TTL
    _tooltip_cache[key] = content
    _cache_timestamps[key] = time.time() + ttl


def get_cached_tooltip_content(key):
    """
    Retrieve cached tooltip content if available and not expired.

    Args:
        key (str): Cache key

    Returns:
        Content if cached and valid, None otherwise
    """
    if key not in _tooltip_cache:
        return None

    # Check if cache entry has expired
    if key in _cache_timestamps and time.time() > _cache_timestamps[key]:
        # Remove expired entry
        del _tooltip_cache[key]
        del _cache_timestamps[key]
        return None

    return _tooltip_cache[key]


def clear_tooltip_cache():
    """Clear all cached tooltip content."""
    _tooltip_cache.clear()
    _cache_timestamps.clear()


def create_lazy_tooltip(
    id_suffix, content_generator, generator_args=None, cache_key=None, **tooltip_kwargs
):
    """
    Create a lazy-loaded tooltip that generates content on demand.

    Args:
        id_suffix: Suffix for component ID
        content_generator: Function that generates tooltip content
        generator_args: Arguments to pass to content generator
        cache_key: Optional cache key for content reuse
        **tooltip_kwargs: Additional arguments for tooltip creation

    Returns:
        Dash component with lazy-loaded tooltip
    """
    generator_args = generator_args or {}

    # Check cache first if cache key provided
    if cache_key:
        cached_content = get_cached_tooltip_content(cache_key)
        if cached_content is not None:
            return create_enhanced_tooltip(
                id_suffix=id_suffix, help_text=cached_content, **tooltip_kwargs
            )

    # Generate content
    try:
        content = content_generator(**generator_args)

        # Cache the generated content if cache key provided
        if cache_key:
            cache_tooltip_content(cache_key, content)

        return create_enhanced_tooltip(
            id_suffix=id_suffix, help_text=content, **tooltip_kwargs
        )
    except Exception as e:
        # Fallback to simple error message
        fallback_content = f"Error loading tooltip content: {str(e)}"
        return create_enhanced_tooltip(
            id_suffix=id_suffix,
            help_text=fallback_content,
            variant="error",
            **tooltip_kwargs,
        )


#######################################################################
# TOOLTIP POSITIONING UTILITIES
#######################################################################


def get_smart_placement(preferred="top", mobile_override=None):
    """
    Get smart tooltip placement that adapts to screen size.

    Args:
        preferred (str): Preferred placement (top, bottom, left, right)
        mobile_override (str): Override placement for mobile devices

    Returns:
        str: Optimal placement for the current context
    """
    # For mobile devices, prefer bottom placement to avoid viewport issues
    if mobile_override and _is_mobile_context():
        return mobile_override

    # Return preferred placement for desktop
    return preferred


def get_responsive_placement(element_position="center"):
    """
    Get responsive tooltip placement based on element position.

    Args:
        element_position (str): Position context (top, bottom, left, right, center)

    Returns:
        str: Recommended placement to avoid viewport edges
    """
    placement_map = {
        "top": "bottom",  # Elements at top show tooltip below
        "bottom": "top",  # Elements at bottom show tooltip above
        "left": "right",  # Elements at left show tooltip to right
        "right": "left",  # Elements at right show tooltip to left
        "center": "top",  # Center elements default to top
    }

    return placement_map.get(element_position, "top")


def create_adaptive_tooltip_config(base_delay=200, mobile_delay=300):
    """
    Create adaptive tooltip configuration that adjusts for device type.

    Args:
        base_delay (int): Base delay in milliseconds for desktop
        mobile_delay (int): Delay for mobile devices (usually longer)

    Returns:
        dict: Delay configuration
    """
    if _is_mobile_context():
        return {"show": mobile_delay, "hide": mobile_delay // 2}

    return {"show": base_delay, "hide": base_delay // 2}


def _is_mobile_context():
    """
    Determine if we're in a mobile context (placeholder for client-side logic).

    Note: This is a server-side approximation. In a real implementation,
    this would be enhanced with client-side device detection.

    Returns:
        bool: True if likely mobile context
    """
    # Server-side placeholder - in practice this could be enhanced with
    # user agent detection or client-side callbacks
    return False


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
    delay={"show": 200, "hide": 100},
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
        variant: Style variant (dark, primary, info, success, warning, error) - default: "dark"
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
            "×",
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


def create_chart_tooltip_bundle(chart_type, chart_data=None, cache_enabled=True):
    """
    Create a comprehensive tooltip bundle for specific chart types.

    Args:
        chart_type (str): Type of chart (burndown, velocity, scope, etc.)
        chart_data (dict): Optional chart-specific data for dynamic content
        cache_enabled (bool): Whether to use caching for performance

    Returns:
        dict: Bundle of tooltip configurations for the chart
    """
    cache_key = f"chart-tooltips-{chart_type}" if cache_enabled else None

    # Define chart-specific tooltip configurations
    chart_configs = {
        "burndown": {
            "layout": create_chart_layout_config(
                title="Burndown Chart", hover_mode="unified", tooltip_variant="dark"
            ),
            "hover_template": format_hover_template(
                title="Burndown Progress",
                fields={
                    "Date": "%{x}",
                    "Remaining": "%{y:.1f} points",
                    "Ideal": "%{customdata:.1f} points",
                },
            ),
        },
        "velocity": {
            "layout": create_chart_layout_config(
                title="Velocity Chart", hover_mode="compare", tooltip_variant="dark"
            ),
            "hover_template": format_hover_template(
                title="Sprint Velocity",
                fields={
                    "Sprint": "%{x}",
                    "Completed": "%{y:.1f} points",
                    "Committed": "%{customdata:.1f} points",
                },
            ),
        },
        "scope": {
            "layout": create_chart_layout_config(
                title="Scope Changes", hover_mode="unified", tooltip_variant="dark"
            ),
            "hover_template": format_hover_template(
                title="Scope Change",
                fields={
                    "Date": "%{x}",
                    "Total Scope": "%{y:.1f} points",
                    "Change": "%{customdata:+.1f} points",
                },
            ),
        },
    }

    # Get configuration for the requested chart type
    config = chart_configs.get(chart_type, chart_configs["burndown"])

    # Cache the configuration if enabled
    if cache_key:
        cache_tooltip_content(cache_key, config)

    return config


def create_responsive_tooltip_system(component_id, tooltips_config):
    """
    Create a responsive tooltip system that adapts to screen size and context.

    Args:
        component_id (str): Base ID for the tooltip system
        tooltips_config (dict): Configuration for multiple tooltips

    Returns:
        list: List of responsive tooltip components
    """
    tooltips = []

    for tooltip_id, config in tooltips_config.items():
        # Extract configuration
        content = config.get("content", "")
        variant = config.get("variant", "dark")  # Default to dark theme
        position = config.get("position", "top")
        trigger_class = config.get("trigger_class", "fas fa-info-circle")
        responsive = config.get("responsive", True)

        # Create responsive tooltip
        tooltip = create_enhanced_tooltip(
            id_suffix=f"{component_id}-{tooltip_id}",
            help_text=content,
            variant=variant,
            placement=position,
            icon_class=trigger_class,
            smart_positioning=responsive,
            dismissible=config.get("dismissible", False),
            expandable=config.get("expandable", False),
        )

        tooltips.append(tooltip)

    return tooltips


def create_tooltip_with_settings_integration(setting_key, id_suffix, variant="info"):
    """
    Create a tooltip that integrates with the application's settings system.

    Args:
        setting_key (str): Key to look up in CHART_HELP_TEXTS or similar
        id_suffix (str): Suffix for component ID
        variant (str): Tooltip variant

    Returns:
        Dash component with settings-integrated tooltip
    """
    # This would integrate with configuration.settings.CHART_HELP_TEXTS
    # For now, we'll create a placeholder that shows the pattern

    def get_help_text():
        # In practice, this would import and access CHART_HELP_TEXTS
        try:
            from configuration.settings import CHART_HELP_TEXTS

            return CHART_HELP_TEXTS.get(setting_key, f"Help for {setting_key}")
        except ImportError:
            return f"Help text for {setting_key} (settings integration available)"

    return create_lazy_tooltip(
        id_suffix=id_suffix,
        content_generator=get_help_text,
        cache_key=f"settings-{setting_key}",
        variant=variant,
        smart_positioning=True,
    )


def create_formula_tooltip(
    id_suffix,
    formula_name,
    basic_explanation,
    formula_text,
    example_calculation=None,
    mathematical_context=None,
    variant="info",
    placement="top",
):
    """
    Create a specialized tooltip for mathematical formulas with progressive disclosure.

    This function builds on Phase 7's expandable tooltip infrastructure to provide
    comprehensive mathematical documentation with step-by-step explanations.

    Args:
        id_suffix (str): Suffix for component ID
        formula_name (str): Name of the formula (e.g., "PERT Expected Value")
        basic_explanation (str): Simple explanation for basic users
        formula_text (str): Mathematical formula (e.g., "(O + 4×ML + P) ÷ 6")
        example_calculation (str, optional): Step-by-step numerical example
        mathematical_context (str, optional): Advanced mathematical context
        variant (str): Tooltip style variant
        placement (str): Tooltip placement

    Returns:
        Dash component with formula-specific expandable tooltip
    """
    # Create summary content (basic level)
    summary_content = f"{basic_explanation}\n\n[Calc] Formula: {formula_text}"

    # Create detailed content (intermediate/advanced level)
    detailed_parts = []

    if example_calculation:
        detailed_parts.append(f"[Example] Calculation:\n{example_calculation}")

    if mathematical_context:
        detailed_parts.append(f"[Math] Context:\n{mathematical_context}")

    detailed_content = (
        "\n\n".join(detailed_parts)
        if detailed_parts
        else "Additional mathematical details available on request."
    )

    return create_expandable_tooltip(
        id_suffix=f"formula-{id_suffix}",
        summary_text=summary_content,
        detailed_text=detailed_content,
        variant=variant,
        placement=placement,
    )


def create_calculation_step_tooltip(
    id_suffix,
    calculation_name,
    steps,
    interpretation=None,
    variant="primary",
    placement="top",
):
    """
    Create a tooltip that shows step-by-step calculation process.

    Ideal for showing mathematical processes with numbered steps and
    clear interpretation of results.

    Args:
        id_suffix (str): Suffix for component ID
        calculation_name (str): Name of the calculation process
        steps (list): List of calculation steps
        interpretation (str, optional): Interpretation of the final result
        variant (str): Tooltip style variant
        placement (str): Tooltip placement

    Returns:
        Dash component with step-by-step calculation tooltip
    """
    # Format steps with numbers
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        formatted_steps.append(f"{i}. {step}")

    summary_content = f"{calculation_name}\n\nStep-by-step process:"
    detailed_content = "\n".join(formatted_steps)

    if interpretation:
        detailed_content += f"\n\n[Result] {interpretation}"

    return create_expandable_tooltip(
        id_suffix=f"calc-{id_suffix}",
        summary_text=summary_content,
        detailed_text=detailed_content,
        variant=variant,
        placement=placement,
    )


def create_statistical_context_tooltip(
    id_suffix,
    metric_name,
    statistical_explanation,
    confidence_info=None,
    data_requirements=None,
    variant="success",
    placement="top",
):
    """
    Create a tooltip that explains statistical context and confidence levels.

    Perfect for explaining why certain calculations are used and what
    confidence levels mean in practical terms.

    Args:
        id_suffix (str): Suffix for component ID
        metric_name (str): Name of the statistical metric
        statistical_explanation (str): Core statistical explanation
        confidence_info (str, optional): Information about confidence levels
        data_requirements (str, optional): Minimum data requirements
        variant (str): Tooltip style variant
        placement (str): Tooltip placement

    Returns:
        Dash component with statistical context tooltip
    """
    summary_content = f"{metric_name}\n\n{statistical_explanation}"

    detailed_parts = []
    if confidence_info:
        detailed_parts.append(f"[Stats] Confidence: {confidence_info}")

    if data_requirements:
        detailed_parts.append(f"[Data] Requirements: {data_requirements}")

    detailed_content = (
        "\n\n".join(detailed_parts)
        if detailed_parts
        else "Additional statistical context available."
    )

    return create_expandable_tooltip(
        id_suffix=f"stats-{id_suffix}",
        summary_text=summary_content,
        detailed_text=detailed_content,
        variant=variant,
        placement=placement,
    )


#######################################################################
# UNIFIED HELP ICON COMPONENT
#######################################################################


def create_help_icon(
    tooltip_id: str,
    position: str = "inline",
    icon_class: str = "fas fa-info-circle",
    color: str = "#17a2b8",
) -> html.I:
    """
    Create a standardized help icon with consistent styling.

    This provides a unified way to add help icons across all tabs,
    ensuring consistent positioning, sizing, and color.

    Args:
        tooltip_id: Unique ID for the tooltip target
        position: Icon position - "inline", "header", or "trailing" (default: "inline")
        icon_class: FontAwesome icon class (default: "fas fa-info-circle")
        color: Icon color in hex (default: "#17a2b8" - Bootstrap info color)

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
