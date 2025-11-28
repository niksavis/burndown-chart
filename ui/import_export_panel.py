"""
Import/Export Panel Component

Dedicated component for data import/export functionality.
Separated from main JIRA integration for cleaner UI organization.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_import_export_panel():
    """Create the import/export panel component (content only, no card wrapper)."""
    return html.Div(
        [
            # Import Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label(
                                "Import Data",
                                className="form-label small text-muted mb-1",
                            ),
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.I(
                                                    className="fas fa-cloud-upload-alt fa-lg mb-1 text-primary"
                                                ),
                                                html.P(
                                                    "Drop file or click",
                                                    className="mb-0 small",
                                                ),
                                                html.Small(
                                                    "JSON/CSV",
                                                    className="text-muted",
                                                    style={"fontSize": "0.75rem"},
                                                ),
                                            ],
                                            className="text-center py-2",
                                        )
                                    ],
                                ),
                                style={
                                    "position": "relative",
                                    "width": "100%",
                                    "borderWidth": "2px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "8px",
                                    "borderColor": "#dee2e6",
                                    "backgroundColor": "#f8f9fa",
                                    "cursor": "pointer",
                                },
                                multiple=False,
                                accept="application/json,.json,.csv",
                            ),
                        ],
                        md=6,
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "Export Data",
                                className="form-label small text-muted mb-1",
                            ),
                            dbc.Button(
                                [
                                    html.I(className="fas fa-download me-2"),
                                    "Export Data",
                                ],
                                id="export-project-data-button",
                                color="secondary",
                                className="w-100",
                                size="md",
                            ),
                            dcc.Download(id="download-data"),
                        ],
                        md=6,
                    ),
                ],
                className="g-3",
            ),
        ]
    )


def create_import_export_flyout(is_open: bool = False):
    """
    Create a flyout panel for import/export functionality.

    This creates a separate collapsible panel similar to the settings panel
    for data management operations.

    Args:
        is_open: Whether panel should start in expanded state

    Returns:
        html.Div: Complete import/export flyout panel
    """
    return html.Div(
        [
            # Collapsible import/export panel content (drops down from button)
            dbc.Collapse(
                html.Div(
                    [
                        # Tabbed interface matching Settings panel
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="Data",
                                    tab_id="data-tab",
                                    label_style={"width": "100%"},
                                    children=[
                                        html.Div(
                                            [
                                                # No header - tab label serves as title
                                                # Import section - compact
                                                html.Div(
                                                    [
                                                        dcc.Upload(
                                                            id="upload-data",
                                                            children=html.Div(
                                                                [
                                                                    html.I(
                                                                        className="fas fa-cloud-upload-alt fa-2x mb-2 text-primary"
                                                                    ),
                                                                    html.P(
                                                                        "Drop files here or click to browse",
                                                                        className="mb-1 fw-medium",
                                                                        style={
                                                                            "fontSize": "0.9rem"
                                                                        },
                                                                    ),
                                                                    html.Small(
                                                                        "Supports JSON and CSV files",
                                                                        className="text-muted",
                                                                        style={
                                                                            "fontSize": "0.75rem"
                                                                        },
                                                                    ),
                                                                ],
                                                                className="text-center py-4",
                                                            ),
                                                            style={
                                                                "width": "100%",
                                                                "borderWidth": "2px",
                                                                "borderStyle": "dashed",
                                                                "borderRadius": "8px",
                                                                "borderColor": "#dee2e6",
                                                                "backgroundColor": "#f8f9fa",
                                                                "cursor": "pointer",
                                                                "transition": "all 0.2s ease",
                                                            },
                                                            multiple=False,
                                                            accept="application/json,.json,.csv",
                                                        ),
                                                    ],
                                                    className="mb-4 pb-3 border-bottom",
                                                ),
                                                # Export section - compact, no redundant heading
                                                html.Div(
                                                    [
                                                        dbc.Button(
                                                            [
                                                                html.I(
                                                                    className="fas fa-file-export me-2"
                                                                ),
                                                                "Export Project Data",
                                                            ],
                                                            id="export-project-data-button",
                                                            color="secondary",
                                                            className="w-100 mb-2",
                                                            size="md",
                                                        ),
                                                        html.Small(
                                                            "Downloads complete project data as JSON file",
                                                            className="text-muted d-block text-center",
                                                            style={
                                                                "fontSize": "0.75rem"
                                                            },
                                                        ),
                                                        dcc.Download(
                                                            id="download-data"
                                                        ),
                                                    ],
                                                    className="mb-3",
                                                ),
                                            ],
                                            className="settings-tab-content",
                                        )
                                    ],
                                ),
                            ],
                            id="data-tabs",
                            active_tab="data-tab",
                            className="settings-tabs",
                        ),
                    ],
                    className="tabbed-settings-panel",
                ),
                id="import-export-collapse",
                is_open=is_open,
            ),
        ],
        id="import-export-panel",
        className="import-export-panel-container",
    )
