"""
Environment Configuration Form Component

Provides UI for configuring production environment identifiers (multi-value support).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_environment_config_form(
    production_environment_values=None, available_environment_values=None
):
    """
    Create environment value configuration form.

    Args:
        production_environment_values: List of production identifier values
        available_environment_values: List of available environment values from JIRA field

    Returns:
        Dash component with environment configuration UI
    """
    production_environment_values = production_environment_values or []
    available_environment_values = available_environment_values or []

    # Create options for dropdown - include current values even if metadata not fetched
    env_options = [{"label": val, "value": val} for val in available_environment_values]

    # Add current values to options if not already present (ensures they display)
    existing_values = set(available_environment_values)
    for env_val in production_environment_values:
        if env_val and env_val not in existing_values:
            env_options.append({"label": env_val, "value": env_val})

    return html.Div(
        [
            # Production Identifiers
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Production Identifiers (Required for MTTR)",
                                className="fw-bold mb-2",
                            ),
                            dcc.Dropdown(
                                id="production-environment-values-dropdown",
                                options=env_options,  # type: ignore  # Dash accepts list[dict]
                                value=production_environment_values,
                                multi=True,
                                placeholder="Select production environment identifiers (e.g., PROD, Production)...",
                                className="mb-2",
                            ),
                            html.Div(
                                [
                                    html.Small(
                                        [
                                            html.I(className="fas fa-info-circle me-1"),
                                            "Any match counts as production bug for MTTR. ",
                                            "Select all values that identify production environment.",
                                        ],
                                        className="text-muted d-block mb-2",
                                    ),
                                    html.Small(
                                        [
                                            html.I(
                                                className="fas fa-sync me-1 text-info"
                                            ),
                                            html.Strong("How to populate: "),
                                            "Click ",
                                            html.Strong("'Fetch Metadata'"),
                                            " button to automatically load all values from your JIRA 'Affected Environment' field. ",
                                            "The system will extract unique values from existing issues.",
                                        ]
                                        if not available_environment_values
                                        else [
                                            html.I(
                                                className="fas fa-check-circle me-1 text-success"
                                            ),
                                            f"Loaded {len(available_environment_values)} unique value(s) from JIRA issues.",
                                        ],
                                        className="text-muted d-block mb-2",
                                    ),
                                    (
                                        html.Small(
                                            [
                                                html.I(
                                                    className="fas fa-lightbulb me-1 text-warning"
                                                ),
                                                html.Strong("Still no values? "),
                                                "Ensure 'Affected Environment' is mapped in the Fields tab, then click 'Fetch Metadata' again. ",
                                                "The system searches your actual JIRA issues to find all possible values.",
                                            ],
                                            className="text-muted d-block",
                                        )
                                        if not available_environment_values
                                        else html.Div()
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
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
        className="p-3",
    )
