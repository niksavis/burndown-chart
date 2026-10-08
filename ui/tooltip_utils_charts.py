from configuration.settings import CHART_HELP_TEXTS
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


def create_lazy_tooltip(
    id_suffix, content_generator, generator_args=None, cache_key=None, **tooltip_kwargs
):

    generator_args = generator_args or {}

    if cache_key:
        cached_content = get_cached_tooltip_content(cache_key)
        if cached_content is not None:
            return create_enhanced_tooltip(
                id_suffix=id_suffix, help_text=cached_content, **tooltip_kwargs
            )

    try:
        content = content_generator(**generator_args)

        if cache_key:
            cache_tooltip_content(cache_key, content)

        return create_enhanced_tooltip(
            id_suffix=id_suffix, help_text=content, **tooltip_kwargs
        )
    except Exception as e:
        fallback_content = f"Error loading tooltip content: {str(e)}"
        return create_enhanced_tooltip(
            id_suffix=id_suffix,
            help_text=fallback_content,
            variant="error",
            **tooltip_kwargs,
        )


def create_chart_tooltip_bundle(chart_type, chart_data=None, cache_enabled=True):

    cache_key = f"chart-tooltips-{chart_type}" if cache_enabled else None

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

    config = chart_configs.get(chart_type, chart_configs["burndown"])

    if cache_key:
        cache_tooltip_content(cache_key, config)

    return config


def create_responsive_tooltip_system(component_id, tooltips_config):

    tooltips = []

    for tooltip_id, config in tooltips_config.items():
        content = config.get("content", "")
        variant = config.get("variant", "dark")
        position = config.get("position", "top")
        trigger_class = config.get("trigger_class", "fas fa-info-circle")
        responsive = config.get("responsive", True)

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

    def get_help_text():
        try:
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

    summary_content = f"{basic_explanation}\n\n[Calc] Formula: {formula_text}"

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
