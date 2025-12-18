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


def _create_import_export_tab():
    """Create simplified Import/Export tab - just JSON data with project_data and metrics."""
    return html.Div(
        [
            # Import Section
            html.Div(
                [
                    html.I(className="fas fa-file-import me-2 text-primary"),
                    html.Span("Import Project Data", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.P(
                "Upload project data JSON containing statistics and metrics",
                className="text-muted small mb-2",
                style={"fontSize": "0.8rem"},
            ),
            dcc.Upload(
                id="upload-data",
                children=html.Div(
                    [
                        html.I(
                            className="fas fa-cloud-upload-alt fa-lg mb-1 text-primary"
                        ),
                        html.P(
                            "Drop JSON file or click to browse",
                            className="mb-1 fw-medium",
                            style={"fontSize": "0.85rem"},
                        ),
                        html.Small(
                            html.Span(".json", className="badge bg-primary"),
                            className="text-muted",
                        ),
                    ],
                    className="text-center py-2",
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
                accept=".json,application/json",
            ),
            # Divider
            html.Hr(className="my-3"),
            # Export Section
            html.Div(
                [
                    html.I(className="fas fa-file-export me-2 text-primary"),
                    html.Span("Export Project Data", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.P(
                "Download project statistics and calculated metrics as JSON",
                className="text-muted small mb-2",
                style={"fontSize": "0.8rem"},
            ),
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-download"),
                            html.Span("Export Data"),
                        ],
                        id="export-project-data-button",
                        color="primary",
                        className="action-button",
                    ),
                ],
                style={"marginBottom": "1rem"},
            ),
            dcc.Download(id="export-project-data-download"),
            # Hidden elements (kept for backward compatibility with callbacks)
            html.Div(
                [
                    dbc.RadioItems(
                        id="export-type-radio",
                        options=[],
                        value="quick",
                        style={"display": "none"},
                    ),
                    dbc.Collapse(
                        id="export-options-collapse",
                        is_open=False,
                        children=[
                            dbc.Checklist(
                                id="export-options-checklist",
                                options=[],
                                value=[],
                                style={"display": "none"},
                            ),
                            html.Div(
                                id="export-size-estimate", style={"display": "none"}
                            ),
                        ],
                    ),
                    dbc.Button(id="export-profile-button", style={"display": "none"}),
                    dcc.Download(id="export-profile-download"),
                ],
                style={"display": "none"},
            ),
        ],
        className="settings-tab-content",
    )


def _create_reports_tab():
    """Create simplified Reports tab - uses Data Points slider value from Parameters panel."""
    return html.Div(
        [
            # Report Section Header
            html.Div(
                [
                    html.I(className="fas fa-file-alt me-2 text-success"),
                    html.Span("Generate HTML Report", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.P(
                "Create a self-contained HTML file with all metrics for sharing",
                className="text-muted small mb-2",
                style={"fontSize": "0.8rem"},
            ),
            # Info about time period
            html.Div(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    html.Span(
                        [
                            "Report will include data from the ",
                            html.Strong(id="report-weeks-display", children="12"),
                            " weeks shown in your current Data Points view",
                        ],
                        style={"fontSize": "0.85rem"},
                    ),
                ],
                className="alert alert-info py-2 mb-3",
                style={"fontSize": "0.8rem"},
            ),
            # Generate button
            html.Div(
                [
                    dbc.Button(
                        [
                            html.I(className="fas fa-download"),
                            html.Span("Generate Report"),
                        ],
                        id="generate-report-button",
                        color="primary",
                        className="action-button",
                    ),
                ],
                id="generate-report-button-container",
                style={"marginBottom": "1rem"},
            ),
            dcc.Download(id="report-download"),
            # Hidden elements (kept for backward compatibility with callbacks)
            html.Div(
                [
                    dbc.Checklist(
                        id="report-sections-checklist",
                        options=[],
                        value=["burndown", "dora", "flow"],
                        style={"display": "none"},
                    ),
                    dbc.RadioItems(
                        id="report-time-period-radio",
                        options=[],
                        value=12,
                        style={"display": "none"},
                    ),
                    html.Div(id="report-size-estimate", style={"display": "none"}),
                ],
                style={"display": "none"},
            ),
        ],
        className="settings-tab-content",
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
                                    label="Reports",
                                    tab_id="reports-tab",
                                    children=_create_reports_tab(),
                                ),
                                dbc.Tab(
                                    label="Import/Export",
                                    tab_id="import-export-tab",
                                    children=_create_import_export_tab(),
                                ),
                            ],
                            id="data-tabs",
                            active_tab="reports-tab",
                            className="settings-tabs",
                        ),
                    ],
                    className="tabbed-settings-panel blue-accent-panel",
                ),
                id="import-export-collapse",
                is_open=is_open,
            ),
        ],
        id="import-export-panel",
        className="import-export-panel-container",
    )
