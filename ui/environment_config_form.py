"""
Environment Configuration Form Component

Provides UI for configuring production environment identifiers (multi-value support).
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_environment_config_form(
    production_environment_values=None, available_environment_values=None
):
    """
    Create environment value configuration form.

    Args:
        production_environment_values: List of production identifier values
        available_environment_values: List of available environment values
            from JIRA field

    Returns:
        Dash component with environment configuration UI
    """
    production_environment_values = production_environment_values or []
    available_environment_values = available_environment_values or []
    has_available_environment_values = bool(available_environment_values)

    info_icon_class = "fas fa-info-circle me-1 text-info"
    magic_icon_class = "fas fa-magic me-1 text-info"
    check_icon_class = "fas fa-check-circle me-1 text-success"
    hint_icon_class = "fas fa-lightbulb me-1 text-warning"
    muted_small_class = "text-muted d-block mb-2"
    muted_block_class = "text-muted d-block"

    auto_populated_help = [
        html.I(className=magic_icon_class),
        html.Strong("Auto-populated: "),
        "Values are loaded automatically from JIRA when you open this modal. ",
        "Use ",
        html.Strong("'Auto-Configure'"),
        " to detect production identifiers.",
    ]
    loaded_values_help = [
        html.I(className=check_icon_class),
        f"Loaded {len(available_environment_values)} unique value(s) from JIRA.",
    ]
    no_values_help = [
        html.I(className=hint_icon_class),
        html.Strong("No values showing? "),
        "Ensure JIRA is connected and 'Affected Environment' field is mapped in the ",
        "Fields tab. Re-open this modal to refresh the available values.",
    ]
    auto_help_content = (
        auto_populated_help
        if not has_available_environment_values
        else loaded_values_help
    )
    no_values_help_component = (
        html.Small(no_values_help, className=muted_block_class)
        if not has_available_environment_values
        else html.Div()
    )

    # Create options for dropdown - include current values even if metadata not fetched
    env_options = [{"label": val, "value": val} for val in available_environment_values]

    # Add current values to options if not already present (ensures they display)
    existing_values = set(available_environment_values)
    for env_val in production_environment_values:
        if env_val and env_val not in existing_values:
            env_options.append({"label": env_val, "value": env_val})

    return html.Div(
        [
            # DORA Metrics Environment Classification Card
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5(
                            "DORA Metrics Environment Classification", className="mb-0"
                        ),
                        className="bg-light",
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                "Configure production environment identifiers "
                                "for DORA MTTR (Mean Time to Recovery) "
                                "calculation.",
                                className="text-muted small mb-3",
                            ),
                            # Production Identifiers
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className=(
                                                            "fas fa-server "
                                                            "me-2 text-danger"
                                                        )
                                                    ),
                                                    "Production Identifiers (Required)",
                                                ],
                                                className="fw-bold mb-2",
                                            ),
                                            dcc.Dropdown(
                                                id="production-environment-values-dropdown",
                                                options=env_options,  # type: ignore  # Dash accepts list[dict]
                                                value=production_environment_values,
                                                multi=True,
                                                placeholder=(
                                                    "Select production environment "
                                                    "identifiers (e.g., PROD, "
                                                    "Production)..."
                                                ),
                                                className="mb-2",
                                            ),
                                            html.Div(
                                                [
                                                    html.Small(
                                                        [
                                                            html.I(
                                                                className=info_icon_class
                                                            ),
                                                            "Issues affecting these "
                                                            "environments are counted "
                                                            "for MTTR calculation. "
                                                            "Select all values that "
                                                            "identify your production "
                                                            "environment.",
                                                        ],
                                                        className=muted_small_class,
                                                    ),
                                                    html.Small(
                                                        auto_help_content,
                                                        className=muted_small_class,
                                                    ),
                                                    no_values_help_component,
                                                ],
                                            ),
                                        ],
                                        width=12,
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # Validation warnings
            html.Div(id="environment-config-validation-warnings", className="mt-3"),
            # Auto-detection info
            html.Div(
                id="environment-auto-detection-info",
                className="mt-3 alert alert-info",
                style={"display": "none"},
            ),
        ],
    )
