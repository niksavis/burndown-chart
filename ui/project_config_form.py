"""
Project Configuration Form Component

Provides UI for configuring JIRA project classification (development vs devops projects).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_project_config_form(
    development_projects=None, devops_projects=None, available_projects=None
):
    """
    Create project classification configuration form.

    Args:
        development_projects: List of development project keys
        devops_projects: List of devops project keys
        available_projects: List of available project dictionaries from JIRA

    Returns:
        Dash component with project configuration UI
    """
    development_projects = development_projects or []
    devops_projects = devops_projects or []
    available_projects = available_projects or []

    # Create options for dropdown - include current values even if metadata not fetched
    project_options = [
        {
            "label": f"{p.get('key', '')} - {p.get('name', '')}",
            "value": p.get("key", ""),
        }
        for p in available_projects
    ]

    # Add current values to options if not already present (ensures they display)
    existing_keys = {p.get("key", "") for p in available_projects}
    for proj in development_projects + devops_projects:
        if proj and proj not in existing_keys:
            project_options.append({"label": proj, "value": proj})

    return html.Div(
        [
            # Development Projects
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Development Projects", className="fw-bold mb-2"
                            ),
                            dcc.Dropdown(
                                id="development-projects-dropdown",
                                options=project_options,  # type: ignore  # Dash accepts list[dict]
                                value=development_projects,
                                multi=True,
                                placeholder="Select development projects...",
                                className="mb-2",
                            ),
                            html.Small(
                                [
                                    html.I(
                                        className="fas fa-info-circle me-1 text-info"
                                    ),
                                    "Burndown, velocity, Flow metrics",
                                ],
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # DevOps Projects
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("DevOps Projects", className="fw-bold mb-2"),
                            dcc.Dropdown(
                                id="devops-projects-dropdown",
                                options=project_options,  # type: ignore  # Dash accepts list[dict]
                                value=devops_projects,
                                multi=True,
                                placeholder="Select DevOps projects...",
                                className="mb-2",
                            ),
                            html.Small(
                                [
                                    html.I(
                                        className="fas fa-info-circle me-1 text-info"
                                    ),
                                    "Optional. Specify projects containing operational tasks (deployments, incidents). ",
                                    "If empty, all issues will be scanned for DORA-relevant fields.",
                                ],
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Validation warnings
            html.Div(id="project-config-validation-warnings", className="mt-3"),
            # Auto-detection info
            html.Div(id="project-auto-detection-info", className="mt-3"),
        ],
        className="p-3",
    )
