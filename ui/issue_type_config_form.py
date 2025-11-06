"""
Issue Type Configuration Form Component

Provides UI for configuring JIRA issue type mappings (DevOps tasks, bugs, stories, tasks).
"""

from dash import html, dcc
import dash_bootstrap_components as dbc


def create_issue_type_config_form(
    devops_task_types=None,
    bug_types=None,
    story_types=None,
    task_types=None,
    available_issue_types=None,
):
    """
    Create issue type mapping configuration form.

    Args:
        devops_task_types: List of DevOps task type names
        bug_types: List of bug type names
        story_types: List of story type names
        task_types: List of task type names
        available_issue_types: List of available issue type dictionaries from JIRA

    Returns:
        Dash component with issue type configuration UI
    """
    devops_task_types = devops_task_types or []
    bug_types = bug_types or []
    story_types = story_types or []
    task_types = task_types or []
    available_issue_types = available_issue_types or []

    # Create options for dropdowns - include current values even if metadata not fetched
    issue_type_options = [
        {"label": it.get("name", ""), "value": it.get("name", "")}
        for it in available_issue_types
    ]

    # Add current values to options if not already present (ensures they display)
    existing_types = {it.get("name", "") for it in available_issue_types}
    for issue_type in devops_task_types + bug_types + story_types + task_types:
        if issue_type and issue_type not in existing_types:
            issue_type_options.append({"label": issue_type, "value": issue_type})

    return html.Div(
        [
            # DevOps Task Types
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "DevOps Task Types (Required for DORA)",
                                className="fw-bold mb-2",
                            ),
                            dcc.Dropdown(
                                id="devops-task-types-dropdown",
                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                value=devops_task_types,
                                multi=True,
                                placeholder="Select DevOps task types...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Deployment tracking for DORA Frequency",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Bug Types
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Bug Types (Required for MTTR)",
                                className="fw-bold mb-2",
                            ),
                            dcc.Dropdown(
                                id="bug-types-dropdown",
                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                value=bug_types,
                                multi=True,
                                placeholder="Select bug types...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Production incident tracking for DORA MTTR",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Story Types
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Story Types (Optional)", className="fw-bold mb-2"
                            ),
                            dcc.Dropdown(
                                id="story-types-dropdown",
                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                value=story_types,
                                multi=True,
                                placeholder="Select story types...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Work classification (future use)",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Task Types
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Task Types (Optional)", className="fw-bold mb-2"
                            ),
                            dcc.Dropdown(
                                id="task-types-dropdown",
                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                value=task_types,
                                multi=True,
                                placeholder="Select task types...",
                                className="mb-2",
                            ),
                            html.Small(
                                "ℹ️ Work classification (future use)",
                                className="text-muted d-block mb-3",
                            ),
                        ],
                        width=12,
                    )
                ]
            ),
            # Validation warnings
            html.Div(id="issue-type-config-validation-warnings", className="mt-3"),
            # Auto-detection info
            html.Div(
                id="issue-type-auto-detection-info",
                className="mt-3 alert alert-info",
                style={"display": "none"},
            ),
        ],
        className="p-3",
    )
