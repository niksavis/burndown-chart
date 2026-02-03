"""Settings tab content component."""

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_settings_tab_content(
    settings: dict,
    id_suffix: str = "",
) -> html.Div:
    """
    Create settings tab content for data source configuration and import/export.

    This replaces the old Data Import Configuration card, now accessible from
    the Parameter Panel Settings tab.

    Args:
        settings: Dictionary containing current settings
        id_suffix: Suffix for generating unique IDs

    Returns:
        html.Div: Settings tab content with data source config and import/export
    """
    from ui.jql_editor import create_jql_editor
    from ui.jira_config_modal import create_jira_config_button
    from ui.button_utils import create_button
    from ui.jql_components import (
        create_character_count_display,
        should_show_character_warning,
    )

    # Import helper functions from cards module
    import sys
    import os

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from ui.cards.settings_helpers import (
        _get_default_data_source,
        _get_default_jql_query,
        _get_default_jql_profile_id,
        _get_query_profile_options,
    )

    return html.Div(
        [
            # Data Source Selection
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-database me-2",
                                style={"color": "#20c997"},
                            ),
                            "Data Source",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dbc.RadioItems(
                        id="data-source-selection",
                        options=[
                            {"label": "JIRA API", "value": "JIRA"},
                            {"label": "JSON/CSV Import", "value": "CSV"},
                        ],
                        value=_get_default_data_source(),
                        inline=True,
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # CSV Upload Container
            html.Div(
                id="csv-upload-container",
                style={
                    "display": "none"
                    if _get_default_data_source() == "JIRA"
                    else "block"
                },
                children=[
                    html.H6(
                        [
                            html.I(
                                className="fas fa-upload me-2",
                                style={"color": "#0d6efd"},
                            ),
                            "File Upload",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    dcc.Upload(
                        id="upload-data",
                        children=html.Div(
                            [
                                html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                                html.Br(),
                                "Drag and Drop or Click to Select",
                            ],
                            className="text-center",
                        ),
                        style={
                            "width": "100%",
                            "height": "100px",
                            "borderWidth": "2px",
                            "borderStyle": "dashed",
                            "borderRadius": "8px",
                            "borderColor": "#dee2e6",
                            "backgroundColor": "#f8f9fa",
                            "cursor": "pointer",
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                        },
                        multiple=False,
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # JIRA Configuration Container
            html.Div(
                id="jira-config-container",
                style={
                    "display": "block"
                    if _get_default_data_source() == "JIRA"
                    else "none"
                },
                children=[
                    # JIRA Connection Button
                    html.H6(
                        [
                            html.I(
                                className="fas fa-plug me-2", style={"color": "#0d6efd"}
                            ),
                            "JIRA Connection",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_jira_config_button(),
                    html.Div(
                        id="jira-config-status-indicator",
                        className="mt-2 mb-3",
                        children=[],
                    ),
                    # JQL Query Management
                    html.Div(
                        [
                            html.H6(
                                [
                                    html.I(
                                        className="fas fa-code me-2",
                                        style={"color": "#6610f2"},
                                    ),
                                    "JQL Query",
                                ],
                                className="mb-3",
                                style={"fontSize": "0.9rem", "fontWeight": "600"},
                            ),
                            create_jql_editor(
                                editor_id="jira-jql-query",
                                initial_value=_get_default_jql_query(),
                                placeholder="project = MYPROJECT AND created >= startOfYear()",
                                rows=3,
                            ),
                            html.Div(
                                id="jira-jql-character-count-container",
                                children=[
                                    create_character_count_display(
                                        count=len(_get_default_jql_query() or ""),
                                        warning=should_show_character_warning(
                                            _get_default_jql_query()
                                        ),
                                    )
                                ],
                                className="mb-2",
                            ),
                            # Query Actions
                            html.Div(
                                [
                                    create_button(
                                        text="Save Query",
                                        id="save-jql-query-button",
                                        variant="primary",
                                        icon_class="fas fa-save",
                                        size="sm",
                                        className="me-2 mb-2",
                                    ),
                                    dcc.Dropdown(
                                        id="jql-profile-selector",
                                        options=_get_query_profile_options(),  # type: ignore[arg-type]
                                        value=_get_default_jql_profile_id(),
                                        placeholder="Select saved query",
                                        clearable=True,
                                        searchable=True,
                                        style={
                                            "minWidth": "200px",
                                            "maxWidth": "300px",
                                            "display": "inline-block",
                                        },
                                        className="me-2 mb-2",
                                    ),
                                    create_button(
                                        text="Clear",
                                        id="clear-jql-query-button",
                                        variant="outline-secondary",
                                        icon_class="fas fa-eraser",
                                        size="sm",
                                        className="mb-2",
                                    ),
                                ],
                                className="d-flex flex-wrap align-items-center mb-2",
                            ),
                            html.Div(
                                id="jira-jql-query-save-status",
                                className="text-center mt-2 mb-3",
                                children=[],
                            ),
                            # Update Data Button
                            create_button(
                                text="Update Data",
                                id="update-data-unified",
                                variant="primary",
                                icon_class="fas fa-sync-alt",
                                className="w-100 mb-2",
                            ),
                            html.Div(
                                id="jira-cache-status",
                                className="text-center text-muted small",
                                children="Ready to fetch JIRA data",
                            ),
                        ],
                        className="mb-3",
                    ),
                ],
                className="mb-4 pb-3 border-bottom",
            ),
            # Export Options
            html.Div(
                [
                    html.H6(
                        [
                            html.I(
                                className="fas fa-file-export me-2",
                                style={"color": "#6c757d"},
                            ),
                            "Export Data",
                        ],
                        className="mb-3",
                        style={"fontSize": "0.9rem", "fontWeight": "600"},
                    ),
                    create_button(
                        text="Export Project Data",
                        id="export-project-data-button",
                        variant="secondary",
                        icon_class="fas fa-file-export",
                        className="w-100 mb-2",
                    ),
                    html.Small(
                        "Export complete project data as JSON",
                        className="text-muted d-block text-center",
                    ),
                    html.Div(dcc.Download(id="export-project-data-download")),
                ],
            ),
        ],
        style={"padding": "1rem"},
    )
