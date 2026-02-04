"""
Issue Type Configuration Form Component

Provides UI for configuring JIRA issue type mappings for DORA and Flow metrics.
"""

from dash import html, dcc
import dash_bootstrap_components as dbc
import logging

logger = logging.getLogger(__name__)


def create_issue_type_config_form(
    devops_task_types=None,
    bug_types=None,
    story_types=None,  # DEPRECATED: Use flow_type_mappings instead
    task_types=None,  # DEPRECATED: Use flow_type_mappings instead
    available_issue_types=None,
    flow_type_mappings=None,
    available_effort_categories=None,
    parent_issue_types=None,  # NEW: Parent types for epic/feature hierarchy
):
    """
    Create issue type mapping configuration form.

    Args:
        devops_task_types: List of DevOps task type names (DORA)
        bug_types: List of incident type names for production incidents (DORA MTTR) - can include Bug, Incident, Production Issue, etc.
        story_types: DEPRECATED - Use flow_type_mappings instead
        task_types: DEPRECATED - Use flow_type_mappings instead
        available_issue_types: List of available issue type dictionaries from JIRA
        flow_type_mappings: Dict with Flow type mappings (Feature, Defect, etc.)
        available_effort_categories: List of effort category values from JIRA
        parent_issue_types: List of parent issue type names (Epic, Initiative, Feature, etc.)

    Returns:
        Dash component with issue type configuration UI
    """
    devops_task_types = devops_task_types or []
    bug_types = bug_types or []
    parent_issue_types = parent_issue_types or []
    available_issue_types = available_issue_types or []
    available_effort_categories = available_effort_categories or []

    # Initialize flow_type_mappings with defaults if not provided
    if flow_type_mappings is None:
        flow_type_mappings = {
            "Feature": {"issue_types": [], "effort_categories": []},
            "Defect": {"issue_types": [], "effort_categories": []},
            "Technical_Debt": {"issue_types": [], "effort_categories": []},
            "Risk": {"issue_types": [], "effort_categories": []},
        }

    # Create options for dropdowns - include current values even if metadata not fetched
    issue_type_options = [
        {"label": it.get("name", ""), "value": it.get("name", "")}
        for it in available_issue_types
    ]

    # Add current values to options if not already present (ensures they display)
    existing_types = {it.get("name", "") for it in available_issue_types}
    for issue_type in devops_task_types + bug_types + parent_issue_types:
        if issue_type and issue_type not in existing_types:
            issue_type_options.append({"label": issue_type, "value": issue_type})

    # Add flow type issue types to options
    for flow_type, config in flow_type_mappings.items():
        # Skip if config is None (can happen with incomplete mappings)
        if config is None:
            continue
        for issue_type in config.get("issue_types", []):
            if issue_type and issue_type not in existing_types:
                issue_type_options.append({"label": issue_type, "value": issue_type})
                existing_types.add(issue_type)

    logger.info(
        f"[IssueTypeForm] Created {len(issue_type_options)} issue type options from "
        f"{len(available_issue_types)} available types, "
        f"{len(devops_task_types)} devops types, {len(bug_types)} bug types"
    )
    logger.info(
        f"[IssueTypeForm] Technical Debt current value: "
        f"{flow_type_mappings.get('Technical Debt', {}).get('issue_types', [])}"
    )

    # Create effort category options
    effort_category_options = [
        {"label": cat, "value": cat} for cat in available_effort_categories
    ]

    # Add current effort categories to options if not present
    existing_categories = set(available_effort_categories)
    for flow_type, config in flow_type_mappings.items():
        # Skip if config is None (can happen with incomplete mappings)
        if config is None:
            continue
        for category in config.get("effort_categories", []):
            if category and category not in existing_categories:
                effort_category_options.append({"label": category, "value": category})
                existing_categories.add(category)

    return html.Div(
        [
            # Parent Issue Types Section - NEW: At top for hierarchy configuration
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("Parent Issue Types", className="mb-0"),
                        className="bg-light",
                    ),
                    dbc.CardBody(
                        [
                            html.Div(
                                [
                                    html.I(className="fas fa-sitemap me-2 text-info"),
                                    html.Strong("Hierarchy Configuration"),
                                ],
                                className="mb-2",
                            ),
                            html.P(
                                [
                                    "Issue types that act as parents in work hierarchy (Epic, Initiative, Feature, Portfolio Epic). ",
                                    html.Strong(
                                        "These types are included in queries but excluded from burndown calculations."
                                    ),
                                ],
                                className="text-muted small mb-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className="fas fa-layer-group me-2 text-primary"
                                                    ),
                                                    "Parent Types",
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                "Select issue types that represent parents (not included in velocity/burndown)",
                                                className="text-muted small mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="parent-issue-types-dropdown",
                                                options=issue_type_options,  # type: ignore
                                                value=parent_issue_types,
                                                multi=True,
                                                placeholder="Select parent types (e.g., Epic, Initiative, Feature)...",
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                            html.Small(
                                                [
                                                    html.I(
                                                        className="fas fa-info-circle me-1 text-info"
                                                    ),
                                                    "Common: Epic, Initiative, Feature. ",
                                                    "Parent issues will be fetched in the same query as child issues for complete data, ",
                                                    "but filtered from metrics calculations.",
                                                ],
                                                className="text-muted",
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                                className="mb-2",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
            # DORA Metrics Section - Card containing all DORA type configs
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("DORA Metrics Type Classification", className="mb-0"),
                        className="bg-light",
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                "Configure issue types used to identify deployments and production incidents for DORA metrics calculation.",
                                className="text-muted small mb-3",
                            ),
                            # DevOps Task Types
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className="fas fa-rocket me-2 text-primary"
                                                    ),
                                                    "DevOps Task Types",
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                "Deployment Frequency & Lead Time",
                                                className="text-muted small mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="devops-task-types-dropdown",
                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                value=devops_task_types,
                                                multi=True,
                                                placeholder="Type or select issue types...",
                                                className="mb-2",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Incident Types
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label(
                                                [
                                                    html.I(
                                                        className="fas fa-exclamation-triangle me-2 text-danger"
                                                    ),
                                                    "Incident Types",
                                                ],
                                                className="form-label fw-bold",
                                            ),
                                            html.P(
                                                "Change Failure Rate & MTTR",
                                                className="text-muted small mb-2",
                                            ),
                                        ],
                                        width=12,
                                        md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                id="bug-types-dropdown",
                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                value=bug_types,
                                                multi=True,
                                                placeholder="Type or select incident types...",
                                                clearable=True,
                                                searchable=True,
                                                optionHeight=50,
                                                maxHeight=300,
                                            ),
                                        ],
                                        width=12,
                                        md=8,
                                    ),
                                ],
                            ),
                        ]
                    ),
                ],
                className="mb-4",
            ),
            # Flow Metrics Section - Card containing all Flow type configs
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.H5("Flow Metrics Type Classification", className="mb-0"),
                        className="bg-light",
                    ),
                    dbc.CardBody(
                        [
                            html.P(
                                "Configure AND-filter: Issue Type + Effort Category → Flow Type. Leave Effort Categories empty to match all issues of that type.",
                                className="text-muted small mb-3",
                            ),
                            # Feature Types - Grouped Card
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-lightbulb me-2 text-success"
                                                    ),
                                                    html.Strong("Feature Types"),
                                                    html.Span(
                                                        " - New capabilities and improvements (Target: 40-70%)",
                                                        className="text-muted small ms-2",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "1. Issue Types",
                                                                className="form-label fw-bold",
                                                            ),
                                                            html.P(
                                                                "Required: Select at least one issue type",
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-feature-issue-types-dropdown",
                                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Feature", {}
                                                                ).get(
                                                                    "issue_types", []
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select issue types...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "2. Effort Categories (optional)",
                                                                className="form-label fw-bold",
                                                            ),
                                                            html.P(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-info-circle me-1 text-info"
                                                                    ),
                                                                    "Leave empty to match ALL above issue types",
                                                                ],
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-feature-effort-categories-dropdown",
                                                                options=effort_category_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Feature", {}
                                                                ).get(
                                                                    "effort_categories",
                                                                    [],
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select categories...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="border-start border-flow-feature border-4",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Defect Types - Grouped Card
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-bug me-2 text-danger"
                                                    ),
                                                    html.Strong("Defect Types"),
                                                    html.Span(
                                                        " - Bug fixes and production incidents (Target: < 20%)",
                                                        className="text-muted small ms-2",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "1. Issue Types",
                                                                className="form-label fw-bold",
                                                            ),
                                                            html.P(
                                                                "Required: Select at least one issue type",
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-defect-issue-types-dropdown",
                                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Defect", {}
                                                                ).get(
                                                                    "issue_types", []
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select issue types...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "2. Effort Categories (optional)",
                                                                className="form-label",
                                                            ),
                                                            html.P(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-info-circle me-1 text-info"
                                                                    ),
                                                                    "Leave empty to match ALL above issue types",
                                                                ],
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-defect-effort-categories-dropdown",
                                                                options=effort_category_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Defect", {}
                                                                ).get(
                                                                    "effort_categories",
                                                                    [],
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select categories...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="border-start border-flow-defect border-4",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Technical Debt Types - Grouped Card
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-wrench me-2"
                                                    ),
                                                    html.Strong("Technical Debt Types"),
                                                    html.Span(
                                                        " - Refactoring and technical improvements (Target: 10-20%)",
                                                        className="text-muted small ms-2",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "1. Issue Types",
                                                                className="form-label fw-bold",
                                                            ),
                                                            html.P(
                                                                "Required: Select at least one issue type",
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-technical-debt-issue-types-dropdown",
                                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Technical Debt", {}
                                                                ).get(
                                                                    "issue_types", []
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select issue types...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "2. Effort Categories (optional)",
                                                                className="form-label",
                                                            ),
                                                            html.P(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-info-circle me-1 text-info"
                                                                    ),
                                                                    "Leave empty to match ALL above issue types",
                                                                ],
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-technical-debt-effort-categories-dropdown",
                                                                options=effort_category_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Technical Debt", {}
                                                                ).get(
                                                                    "effort_categories",
                                                                    [],
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select categories...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="border-start border-flow-tech-debt border-4",
                                    ),
                                ],
                                className="mb-3",
                            ),
                            # Risk Types - Grouped Card
                            dbc.Card(
                                [
                                    dbc.CardBody(
                                        [
                                            html.Div(
                                                [
                                                    html.I(
                                                        className="fas fa-shield-alt me-2"
                                                    ),
                                                    html.Strong("Risk Types"),
                                                    html.Span(
                                                        " - Security, compliance, and experiments (Target: < 10%)",
                                                        className="text-muted small ms-2",
                                                    ),
                                                ],
                                                className="mb-3",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "1. Issue Types",
                                                                className="form-label fw-bold",
                                                            ),
                                                            html.P(
                                                                "Required: Select at least one issue type",
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-risk-issue-types-dropdown",
                                                                options=issue_type_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Risk", {}
                                                                ).get(
                                                                    "issue_types", []
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select issue types...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "2. Effort Categories (optional)",
                                                                className="form-label",
                                                            ),
                                                            html.P(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-info-circle me-1 text-info"
                                                                    ),
                                                                    "Leave empty to match ALL above issue types",
                                                                ],
                                                                className="text-muted small mb-2",
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=4,
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                id="flow-risk-effort-categories-dropdown",
                                                                options=effort_category_options,  # type: ignore  # Dash accepts list[dict]
                                                                value=flow_type_mappings.get(
                                                                    "Risk", {}
                                                                ).get(
                                                                    "effort_categories",
                                                                    [],
                                                                ),
                                                                multi=True,
                                                                placeholder="Type or select categories...",
                                                                className="mb-2",
                                                                clearable=True,
                                                                searchable=True,
                                                                optionHeight=50,
                                                                maxHeight=300,
                                                            ),
                                                        ],
                                                        width=12,
                                                        md=8,
                                                    ),
                                                ],
                                            ),
                                        ],
                                        className="border-start border-flow-risk border-4",
                                    ),
                                ],
                                className="mb-3",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
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
    )
