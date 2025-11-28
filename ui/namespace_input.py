"""Namespace syntax input component with autocomplete.

Provides a user-friendly input field for namespace syntax with real-time
autocomplete suggestions from JIRA metadata.

Reference: specs/namespace-syntax-analysis.md
"""

import dash_bootstrap_components as dbc
from dash import dcc, html
from typing import List, Optional, Any, Union


def create_namespace_input(
    field_id: str,
    current_value: Optional[str] = None,
    placeholder: str = "Type namespace path (e.g., *.created, DevOps.Status:Deployed.DateTime)",
    label: Optional[str] = None,
    help_text: Optional[str] = None,
) -> html.Div:
    """Create namespace input field with autocomplete.

    Args:
        field_id: Unique ID for the input component
        current_value: Current namespace path value
        placeholder: Placeholder text for empty input
        label: Optional label text
        help_text: Optional help text shown below input

    Returns:
        dbc.FormGroup containing namespace input with autocomplete

    Examples:
        >>> create_namespace_input(
        ...     field_id="deployment_timestamp",
        ...     current_value="DevOps.Status:Deployed.DateTime",
        ...     label="Deployment Timestamp",
        ...     help_text="When deployment occurred"
        ... )
    """
    input_component = dcc.Dropdown(
        id={"type": "namespace-input", "field": field_id},
        options=[],  # Populated dynamically by callback
        value=current_value,
        placeholder=placeholder,
        searchable=True,
        clearable=True,
        optionHeight=60,
        maxHeight=300,
        multi=False,
        persistence=False,
        style={"fontFamily": "monospace"},
    )

    components = []

    if label:
        components.append(
            html.Label(
                label,
                html_for={"type": "namespace-input", "field": field_id},
                className="form-label fw-bold",
            )
        )

    components.append(input_component)

    if help_text:
        components.append(html.Small(help_text, className="form-text text-muted"))

    return html.Div(components, className="mb-3")


def create_namespace_input_with_toggle(
    field_id: Union[str, Any],  # Accept string or dict for pattern-matching IDs
    current_value: Optional[str] = None,
    field_options: Optional[List[Any]] = None,
    placeholder: str = "Type namespace path or select field",
    label: Optional[str] = None,
    help_text: Optional[str] = None,
    show_syntax_help: bool = True,
) -> dbc.Card:
    """Create namespace input with toggle between simple and advanced modes.

    Provides two input modes:
    1. Simple mode: Traditional dropdown field selector
    2. Advanced mode: Namespace syntax input with autocomplete

    Args:
        field_id: Unique ID for the input component (string or dict for pattern-matching)
        current_value: Current value (field ID or namespace path)
        field_options: Options for dropdown mode (traditional field selection)
        placeholder: Placeholder text
        label: Optional label text
        help_text: Optional help text
        show_syntax_help: Whether to show collapsible syntax help

    Returns:
        dbc.Card containing dual-mode input

    Examples:
        >>> create_namespace_input_with_toggle(
        ...     field_id="deployment_timestamp",
        ...     current_value="DevOps.Status:Deployed.DateTime",
        ...     label="Deployment Timestamp"
        ... )
    """
    # Determine current mode based on value format
    is_namespace_syntax = current_value and (
        "." in current_value or ":" in current_value
    )

    card_header = dbc.CardHeader(
        [
            html.Div(
                [
                    html.Label(
                        label if label else field_id,
                        className="fw-bold mb-0",
                    ),
                    dbc.ButtonGroup(
                        [
                            dbc.Button(
                                [html.I(className="fas fa-list me-1"), "Simple"],
                                id={"type": "mode-toggle-simple", "field": field_id},
                                color="primary"
                                if not is_namespace_syntax
                                else "outline-primary",
                                size="sm",
                                active=not is_namespace_syntax,
                            ),
                            dbc.Button(
                                [html.I(className="fas fa-code me-1"), "Advanced"],
                                id={"type": "mode-toggle-advanced", "field": field_id},
                                color="primary"
                                if is_namespace_syntax
                                else "outline-primary",
                                size="sm",
                                active=bool(is_namespace_syntax),
                            ),
                        ],
                        size="sm",
                    ),
                ],
                className="d-flex justify-content-between align-items-center",
            )
        ]
    )

    # Simple mode: Traditional dropdown
    simple_mode = dbc.Collapse(
        dcc.Dropdown(
            id={"type": "field-mapping-dropdown", "field": field_id},
            options=field_options or [],
            value=current_value if not is_namespace_syntax else None,
            placeholder="Select Jira field...",
            searchable=True,
            clearable=True,
            optionHeight=50,
            maxHeight=300,
        ),
        id={"type": "collapse-simple", "field": field_id},
        is_open=not is_namespace_syntax,
    )

    # Advanced mode: Namespace syntax input
    advanced_mode = dbc.Collapse(
        [
            dcc.Dropdown(
                id={"type": "namespace-input", "field": field_id},
                options=[],  # Populated dynamically by autocomplete callback
                value=current_value if is_namespace_syntax else None,
                placeholder=placeholder,
                searchable=True,
                clearable=True,
                optionHeight=60,
                maxHeight=300,
                style={"fontFamily": "monospace"},
            ),
            # Syntax help (collapsible)
            dbc.Collapse(
                dbc.Alert(
                    [
                        html.H6("Namespace Syntax Examples", className="alert-heading"),
                        html.Hr(),
                        html.Ul(
                            [
                                html.Li(
                                    [
                                        html.Code("*.created"),
                                        " - Creation date from any project",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Code("DevOps.status.name"),
                                        " - Status name from DevOps project",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Code("*.Status:Deployed.DateTime"),
                                        " - When status changed to Deployed",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Code("DevOps|Platform.customfield_10100"),
                                        " - Field from multiple projects",
                                    ]
                                ),
                                html.Li(
                                    [
                                        html.Code("*.fixVersions.releaseDate"),
                                        " - First fix version release date",
                                    ]
                                ),
                            ],
                            className="mb-0",
                        ),
                    ],
                    color="light",
                    className="mt-2 mb-0",
                ),
                id={"type": "syntax-help-collapse", "field": field_id},
                is_open=show_syntax_help,
            ),
        ],
        id={"type": "collapse-advanced", "field": field_id},
        is_open=bool(is_namespace_syntax),
    )

    card_body = dbc.CardBody(
        [
            simple_mode,
            advanced_mode,
            html.Small(
                help_text if help_text else "",
                className="form-text text-muted",
            )
            if help_text
            else None,
        ]
    )

    return dbc.Card(
        [card_header, card_body],
        className="mb-3",
    )


def create_syntax_help_section() -> dbc.Collapse:
    """Create collapsible syntax help section for namespace paths.

    Returns:
        dbc.Collapse containing comprehensive syntax documentation
    """
    return dbc.Collapse(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H5("Namespace Syntax Reference", className="card-title"),
                    html.P(
                        "Use namespace paths to access JIRA fields with intuitive dot notation.",
                        className="card-text",
                    ),
                    html.H6("Basic Syntax", className="mt-3"),
                    html.Code(
                        "[Project.]Field[.Property][:ChangelogValue][.Extractor]"
                    ),
                    html.H6("Examples by Category", className="mt-3"),
                    dbc.Accordion(
                        [
                            dbc.AccordionItem(
                                [
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Code("*.created"),
                                                    " - Issue creation date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.updated"),
                                                    " - Last updated date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.resolutiondate"),
                                                    " - Resolution date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code(
                                                        "DevOps.customfield_10100"
                                                    ),
                                                    " - Custom field from DevOps",
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                title="Simple Fields",
                            ),
                            dbc.AccordionItem(
                                [
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Code("*.status.name"),
                                                    " - Status name",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.priority.id"),
                                                    " - Priority ID",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.assignee.displayName"),
                                                    " - Assignee name",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.project.key"),
                                                    " - Project key",
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                title="Object Properties",
                            ),
                            dbc.AccordionItem(
                                [
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Code(
                                                        "*.Status:Deployed.DateTime"
                                                    ),
                                                    " - When deployed",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code(
                                                        "*.Status:InProgress.Occurred"
                                                    ),
                                                    " - Was it in progress?",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code(
                                                        "*.Assignee:john@example.com.DateTime"
                                                    ),
                                                    " - When assigned",
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                title="Changelog Events",
                            ),
                            dbc.AccordionItem(
                                [
                                    html.Ul(
                                        [
                                            html.Li(
                                                [
                                                    html.Code("DevOps|Platform.field"),
                                                    " - Field from multiple projects",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code(
                                                        "*.fixVersions.releaseDate"
                                                    ),
                                                    " - First version release date",
                                                ]
                                            ),
                                            html.Li(
                                                [
                                                    html.Code("*.components.name"),
                                                    " - First component name",
                                                ]
                                            ),
                                        ]
                                    )
                                ],
                                title="Advanced",
                            ),
                        ],
                        start_collapsed=True,
                    ),
                ]
            ),
            className="mt-3",
        ),
        id="namespace-syntax-help",
        is_open=False,
    )
