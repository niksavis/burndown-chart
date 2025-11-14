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
            # Collapsible import/export panel content only (no banner - drops down from main banner)
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        [
                            # Header with icon (matching Parameters panel style)
                            html.H5(
                                [
                                    html.I(
                                        className="fas fa-exchange-alt me-2",
                                        style={"color": "#0dcaf0"},
                                    ),
                                    "Data Management",
                                ],
                                className="mb-4 mt-3 text-info",
                                style={"fontSize": "1.1rem", "fontWeight": "600"},
                            ),
                            # Section 1: Import Data
                            html.Div(
                                [
                                    html.H6(
                                        [
                                            html.I(
                                                className="fas fa-upload me-2",
                                                style={"color": "#198754"},
                                            ),
                                            "1. Import Data",
                                        ],
                                        className="mb-3 text-success",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                [
                                                    "Upload File",
                                                    html.Span(
                                                        " (JSON or CSV)",
                                                        className="text-muted",
                                                        style={"fontSize": "0.8rem"},
                                                    ),
                                                ],
                                                className="form-label fw-medium mb-2",
                                                style={"fontSize": "0.875rem"},
                                            ),
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
                                        className="mb-3",
                                    ),
                                ],
                                className="mb-4 pb-3 border-bottom",
                            ),
                            # Section 2: Export Data
                            html.Div(
                                [
                                    html.H6(
                                        [
                                            html.I(
                                                className="fas fa-download me-2",
                                                style={"color": "#6f42c1"},
                                            ),
                                            "2. Export Data",
                                        ],
                                        className="mb-3",
                                        style={
                                            "fontSize": "0.9rem",
                                            "fontWeight": "600",
                                            "color": "#6f42c1",
                                        },
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "Project Data Export",
                                                className="form-label fw-medium mb-2",
                                                style={"fontSize": "0.875rem"},
                                            ),
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
                                                style={"fontSize": "0.75rem"},
                                            ),
                                            dcc.Download(id="download-data"),
                                        ],
                                        className="mb-3",
                                    ),
                                ],
                            ),
                        ],
                        className="import-export-panel-expanded",
                        style={
                            "paddingTop": "1rem",
                            "paddingLeft": "1.25rem",
                            "paddingRight": "1.25rem",
                        },
                    ),
                    className="mb-4",
                ),
                id="import-export-collapse",
                is_open=is_open,
            ),
        ],
        id="import-export-panel",
        className="import-export-panel-container",
    )
