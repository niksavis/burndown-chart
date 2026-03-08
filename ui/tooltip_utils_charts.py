"""
Tooltip Utilities Charts Module

Chart-specific tooltip builders and advanced tooltip patterns including
lazy loading, formula tooltips, and statistical context tooltips.
"""

#######################################################################
# IMPORTS
#######################################################################
# Local imports
from ui.tooltip_utils_cards import (
    create_enhanced_tooltip,
    create_expandable_tooltip,
)
from ui.tooltip_utils_core import (
    cache_tooltip_content,
    create_chart_layout_config,
    format_hover_template,
    get_cached_tooltip_content,
)

#######################################################################
# LAZY TOOLTIP UTILITIES
#######################################################################


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
# CHART TOOLTIP BUILDERS
#######################################################################


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


#######################################################################
# FORMULA AND STATISTICAL TOOLTIPS
#######################################################################


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
        formula_text (str): Mathematical formula (e.g., "(O + 4xML + P) / 6")
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
