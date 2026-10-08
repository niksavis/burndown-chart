from functools import lru_cache

import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, State, callback, dcc, html

from configuration.help_content_comprehensive import COMPREHENSIVE_HELP_CONTENT
from ui.help_layouts.weekly_progress_help import create_weekly_progress_help_layout
from ui.tooltip_utils import create_info_tooltip


@lru_cache(maxsize=128)
def _cached_format_help_content(content_hash, category, key):
    pass


def create_help_button(
    help_key, help_category, button_id=None, size="sm", className=""
):

    if button_id is None:
        button_id = f"help-btn-{help_category}-{help_key}"

    help_topic = help_key.replace("_", " ").title()

    return html.Button(
        html.I(className="fas fa-question-circle"),
        id=button_id,
        className=(f"btn btn-link text-info p-2 {className} help-button-enhanced"),
        style={
            "border": "none",
            "background": "transparent",
            "fontSize": "1rem",
            "lineHeight": "1",
            "minWidth": "2.75rem",
            "minHeight": "2.75rem",
            "borderRadius": "50%",
            "transition": "all 0.2s ease-in-out",
            "cursor": "pointer",
        },
        title=f"Get detailed help about {help_topic}",
        **{
            "aria-label": f"Get detailed help about {help_topic}",
            "role": "button",
            "tabIndex": 0,
            "type": "button",
        },
    )


def create_help_modal(modal_id, title="Detailed Help"):

    return dbc.Modal(
        [
            dbc.ModalHeader(
                [
                    dbc.ModalTitle(
                        title,
                        className="h4 mb-0",
                        id=f"{modal_id}-title",
                    ),
                ],
                className="d-flex justify-content-between align-items-center py-3",
                close_button=False,
            ),
            dbc.ModalBody(
                id=f"{modal_id}-content",
                className="help-modal-body",
                style={
                    "maxHeight": "70vh",
                    "overflowY": "auto",
                    "padding": "1.5rem",
                    "fontSize": "0.95rem",
                    "lineHeight": "1.6",
                    "transform": "translate3d(0,0,0)",
                    "WebkitOverflowScrolling": "touch",
                },
            ),
            dbc.ModalFooter(
                [
                    dbc.Button(
                        [html.I(className="fas fa-times me-2"), "Close"],
                        id=f"{modal_id}-close",
                        color="secondary",
                        size="sm",
                        className="px-4 py-2",
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
        centered=True,
        fade=True,
        backdrop=True,
        className="help-modal-enhanced",
        style={
            "maxWidth": "95vw",
            "margin": "0.5rem auto",
        },
    )


def format_help_content(content):

    if not content:
        return [html.P("Help content not available.", className="text-muted")]

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

        if (
            line.startswith("[Stats] **")
            or line.startswith("[Calc] **")
            or line.startswith("[Trend] **")
        ):
            if current_section:
                components.extend(current_section)
                current_section = []
            header_text = line.replace("**", "").strip()
            components.append(html.H5(header_text, className="mt-3 mb-2 text-primary"))

        elif line.startswith("• ") or line.startswith("- "):
            bullet_text = line[2:].strip()
            current_section.append(html.Li(bullet_text, className="mb-1"))

        elif (
            line.startswith("[Note] **")
            or line.startswith("[Tip] **")
            or line.startswith("[Date] **")
        ):
            if current_section:
                components.extend(current_section)
                current_section = []
            insight_text = line.replace("**", "").strip()
            components.append(
                dbc.Alert(insight_text, color="info", className="mt-2 mb-2")
            )

        elif "**" in line:
            parts = line.split("**")
            formatted_parts = []
            for i, part in enumerate(parts):
                if i % 2 == 1:
                    formatted_parts.append(html.Strong(part))
                else:
                    formatted_parts.append(part)
            current_section.append(html.P(formatted_parts, className="mb-2"))

        else:
            current_section.append(html.P(line, className="mb-2"))

    if current_section:
        if any(isinstance(comp, html.Li) for comp in current_section):
            components.append(html.Ul(current_section, className="mb-3"))
        else:
            components.extend(current_section)

    return components


def create_help_system_layout():

    return html.Div(
        [
            create_help_modal("main-help-modal", "Comprehensive Help"),
            dcc.Store(id="help-content-store", data={}),
        ],
        id="help-system-container",
    )


@callback(
    [
        Output("main-help-modal", "is_open"),
        Output("main-help-modal-content", "children"),
        Output("main-help-modal-title", "children"),
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
    ctx = dash.callback_context

    if not ctx.triggered:
        return False, [], "Detailed Help"

    trigger_id = ctx.triggered[0]["prop_id"]

    if "close" in trigger_id:
        return False, [], "Detailed Help"

    if help_clicks and any(click for click in help_clicks if click):
        if hasattr(ctx, "triggered_id") and ctx.triggered_id:
            button_info = ctx.triggered_id
            category = button_info.get("category", "")
            key = button_info.get("key", "")

            try:
                help_content = COMPREHENSIVE_HELP_CONTENT.get(category, {}).get(key, "")

                if not help_content:
                    available_keys = list(
                        COMPREHENSIVE_HELP_CONTENT.get(category, {}).keys()
                    )
                    topic_suggestions = chr(10).join(
                        f"• {key_name.replace('_', ' ').title()}"
                        for key_name in available_keys[:5]
                    )
                    help_content = f"""
                    **Help Content Not Available**
                    
                    Content for '{key}' in category '{category}' was not found.
                    
                    **Available Help Topics in {category.title()}:**
                    {topic_suggestions}
                    
                    **Troubleshooting:**
                    • Check that the help system is properly initialized
                                        • Verify help content in
                                            configuration/help_content.py
                    • Contact system administrator if this error persists
                    """

                formatted_content = format_help_content_enhanced(
                    help_content, category, key
                )
                title = f"Help: {key.replace('_', ' ').title()}"

                return True, formatted_content, title

            except Exception as e:
                error_content = [
                    html.Div(
                        [
                            html.H5(
                                "[!] Help System Error", className="text-warning mb-3"
                            ),
                            html.P(
                                [
                                    "There was an error loading the help content. ",
                                    "Please try again or contact support if "
                                    "the problem persists.",
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

    if category == "statistics" and key == "weekly_progress_data_explanation":
        return create_weekly_progress_help_layout()

    if not content:
        return [html.P("Help content not available.", className="text-muted")]

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

        if _is_section_header(line):
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            components.append(_create_section_header(line))
            i += 1

        elif line.startswith("```"):
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []

            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1

            if code_lines:
                code_text = "\n".join(code_lines)
                components.append(_create_multi_line_code_block(code_text))

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
            if current_section:
                components.extend(_process_current_section(current_section))
                current_section = []
            components.append(_create_single_line_code_block(line))
            i += 1

        else:
            current_section.append(_create_paragraph(line))
            i += 1

    if current_section:
        components.extend(_process_current_section(current_section))

    components.append(_create_cross_references_footer(category, key))

    return components


def _is_section_header(line):
    return (
        line.startswith("[Stats] **")
        or line.startswith("[Calc] **")
        or line.startswith("[Trend] **")
        or line.startswith("[Tip] **")
    )


def _is_code_block(line):
    return line.startswith("```") or (line.startswith("Expected =") and "÷" in line)


def _is_bullet_point(line):
    return line.startswith("• ") or line.startswith("- ")


def _is_insight_alert(line):
    return (
        line.startswith("[Note] **")
        or line.startswith("[Tip] **")
        or line.startswith("[Date] **")
        or line.startswith("[!] **")
    )


def _is_single_line_formula(line):
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

    icon_mapping = {
        "[Stats]": ("fas fa-chart-bar", "text-primary"),
        "[Calc]": ("fas fa-calculator", "text-success"),
        "[Trend]": ("fas fa-chart-line", "text-info"),
        "[!]": ("fas fa-exclamation-triangle", "text-warning"),
        "[Tip]": ("fas fa-lightbulb", "text-warning"),
        "[Note]": ("fas fa-info-circle", "text-info"),
        "[Link]": ("fas fa-link", "text-secondary"),
    }

    icon_element = None
    for tag, (icon_class, icon_color) in icon_mapping.items():
        if tag in header_text:
            header_text = header_text.replace(tag, "").strip()
            icon_element = html.I(className=f"{icon_class} {icon_color} me-2")
            break

    if icon_element:
        return html.H5(
            [icon_element, header_text],
            className="mt-4 mb-3 text-primary border-bottom pb-2",
        )

    return html.H5(header_text, className="mt-4 mb-3 text-primary border-bottom pb-2")


def _create_code_block(line):
    code_text = line.replace("```", "").strip()
    return html.Pre(
        code_text, className="bg-light p-3 rounded border-start border-primary border-3"
    )


def _create_multi_line_code_block(code_text):
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

    alert_mapping = {
        "[!]": ("fas fa-exclamation-triangle", "warning"),
        "[Note]": ("fas fa-sticky-note", "info"),
        "[Tip]": ("fas fa-lightbulb", "success"),
        "[Date]": ("fas fa-calendar-alt", "info"),
    }

    icon_class = "fas fa-info-circle"
    alert_color = "info"

    for tag, (icon, color) in alert_mapping.items():
        if tag in insight_text:
            insight_text = insight_text.replace(tag, "").strip()
            icon_class = icon
            alert_color = color
            break

    return dbc.Alert(
        [html.I(className=f"{icon_class} me-2"), insight_text],
        color=alert_color,
        className="my-3 border-start border-3",
    )


def _create_paragraph(line):
    if "**" in line:
        return _format_bold_text(line)
    return html.P(line, className="mb-2")


def _format_bold_text(line):
    parts = line.split("**")
    formatted_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            formatted_parts.append(html.Strong(part))
        else:
            formatted_parts.append(part)
    return html.P(formatted_parts, className="mb-2")


def _process_current_section(current_section):
    if any(isinstance(comp, html.Li) for comp in current_section):
        return [html.Ul(current_section, className="mb-3")]
    return current_section


def _create_cross_references_footer(category, key):
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
        return html.Div()

    return html.Div(
        [
            html.Hr(className="my-4"),
            html.H6(
                [html.I(className="fas fa-link text-secondary me-2"), "Related Topics"],
                className="text-secondary mb-2",
            ),
            html.P(
                [
                    "For more information, see: "
                    + ", ".join(topic.replace("_", " ").title() for topic in related)
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

    if help_button_id is None:
        help_button_id = f"help-btn-{help_category}-{help_key}"

    tooltip_id = f"tooltip-{help_category}-{help_key}"

    return html.Span(
        [
            create_info_tooltip(tooltip_id, tooltip_text, placement=tooltip_placement),
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


def register_help_content(category, key, content):

    if category not in COMPREHENSIVE_HELP_CONTENT:
        COMPREHENSIVE_HELP_CONTENT[category] = {}

    COMPREHENSIVE_HELP_CONTENT[category][key] = content


def create_dashboard_metric_tooltip(metric_key, id_suffix=None):

    if id_suffix is None:
        id_suffix = f"dashboard-{metric_key}"

    help_content = COMPREHENSIVE_HELP_CONTENT.get("dashboard", {})
    tooltip_text = help_content.get(metric_key, f"Help for {metric_key}")

    return create_info_tooltip(
        help_text=tooltip_text, id_suffix=id_suffix, placement="top", variant="dark"
    )


def create_parameter_tooltip(param_key, id_suffix=None):

    if id_suffix is None:
        id_suffix = f"param-{param_key}"

    help_content = COMPREHENSIVE_HELP_CONTENT.get("parameters", {})
    tooltip_text = help_content.get(param_key, f"Help for {param_key}")

    return create_info_tooltip(
        help_text=tooltip_text, id_suffix=id_suffix, placement="right", variant="dark"
    )


def create_metric_help_icon(metric_key, category="dashboard", show_modal_link=False):

    help_content = COMPREHENSIVE_HELP_CONTENT.get(category, {})
    tooltip_text = help_content.get(metric_key, f"Help for {metric_key}")

    detail_key = f"{metric_key}_detail"
    has_detail = detail_key in help_content

    if has_detail and show_modal_link:
        tooltip_text = f"{tooltip_text} Click for detailed explanation."

    return create_info_tooltip(
        help_text=tooltip_text,
        id_suffix=f"{category}-{metric_key}",
        placement="top",
        variant="dark",
    )


def create_settings_tooltip(settings_key, id_suffix=None):

    if id_suffix is None:
        id_suffix = f"settings-{settings_key}"

    help_content = COMPREHENSIVE_HELP_CONTENT.get("settings", {})
    tooltip_text = help_content.get(settings_key, f"Help for {settings_key}")

    return create_info_tooltip(
        help_text=tooltip_text, id_suffix=id_suffix, placement="right", variant="dark"
    )
