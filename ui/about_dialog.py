"""
About Dialog Component

Modal dialog displaying application information, open source licenses,
and changelog. Provides transparency about the application and its dependencies.
"""

#######################################################################
# IMPORTS
#######################################################################
import sys
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import html

from configuration import __version__


#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _read_licenses_file() -> str:
    """Read the THIRD_PARTY_LICENSES.txt file from bundled resources.

    Returns:
        Content of the licenses file, or error message if not found
    """
    try:
        # Check if running as frozen executable
        is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        if is_frozen:
            # PyInstaller bundles resources in _MEIPASS directory
            meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            licenses_file = meipass / "licenses" / "THIRD_PARTY_LICENSES.txt"
        else:
            # Development mode - read from project licenses folder
            # Go up from ui/ to project root
            project_root = Path(__file__).parent.parent
            licenses_file = project_root / "licenses" / "THIRD_PARTY_LICENSES.txt"

        if licenses_file.exists():
            return licenses_file.read_text(encoding="utf-8")
        else:
            return f"License file not found at: {licenses_file}"

    except Exception as e:
        return f"Error reading licenses: {e}"


def _parse_licenses(licenses_text: str) -> list[dict]:
    """Parse the plain-vertical format license text into structured data.

    Args:
        licenses_text: Content from THIRD_PARTY_LICENSES.txt

    Returns:
        List of dicts with keys: name, version, license, url, description
    """
    licenses = []
    current_entry = {}
    field_order = ["name", "version", "license", "url", "description"]
    field_index = 0

    # Skip header lines
    lines = licenses_text.split("\n")
    in_header = True

    for line in lines:
        line = line.strip()

        # Skip header section (until we hit the separator line)
        if in_header:
            if line.startswith("==="):
                in_header = False
            continue

        # Empty line signals end of an entry
        if not line:
            if current_entry:
                licenses.append(current_entry)
                current_entry = {}
                field_index = 0
            continue

        # Parse field based on position (plain-vertical format)
        if field_index < len(field_order):
            field_name = field_order[field_index]
            current_entry[field_name] = line
            field_index += 1

    # Add last entry if exists
    if current_entry:
        licenses.append(current_entry)

    return licenses


def _create_license_accordion(licenses: list[dict]) -> html.Div:
    """Create accordion with all license entries.

    Args:
        licenses: List of license dicts

    Returns:
        html.Div containing accordion with all licenses
    """
    if not licenses:
        return html.Div("No licenses found", className="text-muted")

    accordion_items = []

    for idx, lic in enumerate(licenses):
        name = lic.get("name", "Unknown")
        version = lic.get("version", "")
        license_type = lic.get("license", "Unknown License")
        url = lic.get("url", "")
        description = lic.get("description", "")

        # Create accordion item
        accordion_items.append(
            dbc.AccordionItem(
                [
                    html.P(
                        [
                            html.Strong("License: "),
                            html.Span(license_type, className="text-muted"),
                        ],
                        className="mb-2",
                    ),
                    html.P(
                        [
                            html.Strong("Version: "),
                            html.Span(version, className="text-muted"),
                        ],
                        className="mb-2",
                    )
                    if version
                    else None,
                    html.P(
                        [
                            html.Strong("URL: "),
                            html.A(
                                url,
                                href=url,
                                target="_blank",
                                className="text-decoration-none",
                            ),
                        ],
                        className="mb-2",
                    )
                    if url and url.startswith("http")
                    else None,
                    html.P(
                        [
                            html.Strong("Description: "),
                            html.Span(description, className="text-muted small"),
                        ],
                        className="mb-0",
                    )
                    if description
                    else None,
                ],
                title=f"{name} ({version})" if version else name,
                item_id=f"license-{idx}",
            )
        )

    return html.Div(
        [
            html.P(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    f"Showing {len(licenses)} dependencies",
                ],
                className="text-muted small mb-3",
            ),
            dbc.Accordion(accordion_items, flush=True, start_collapsed=True),
        ]
    )


def _get_app_info_tab() -> dbc.Tab:
    """Create App Info tab with version and system information.

    Returns:
        dbc.Tab containing application information
    """
    # Get Python version
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # Check if running as frozen executable
    is_frozen = getattr(sys, "frozen", False)
    install_type = "Standalone Executable" if is_frozen else "Development Mode"

    content = html.Div(
        [
            html.H5("Burndown Chart", className="mb-3"),
            html.P(
                [
                    html.Strong("Version: "),
                    html.Span(__version__, className="text-muted"),
                ],
                className="mb-2",
            ),
            html.P(
                [
                    html.Strong("Installation: "),
                    html.Span(install_type, className="text-muted"),
                ],
                className="mb-2",
            ),
            html.P(
                [
                    html.Strong("Python: "),
                    html.Span(python_version, className="text-muted"),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.H6("About", className="mb-2"),
            html.P(
                [
                    "Project forecasting and metrics platform with JIRA integration. ",
                    "Delivers probabilistic completion forecasts, comprehensive project health scores, ",
                    "and industry-standard performance metrics (DORA, Flow) using statistical modeling ",
                    "based on your team's actual velocity and work patterns.",
                ],
                className="text-muted mb-3",
            ),
            html.H6("Author", className="mb-2"),
            html.P(
                [html.I(className="fas fa-user me-2"), "Niksa Visic"],
                className="text-muted mb-3",
            ),
            html.H6("License", className="mb-2"),
            html.P(
                ["MIT License - Free and open source software"], className="text-muted"
            ),
        ],
        style={"maxHeight": "400px", "overflowY": "auto"},
    )

    return dbc.Tab(
        content,
        label="App Info",
        tab_id="about-tab-app-info",
        label_style={"cursor": "pointer"},
    )


def _get_open_source_tab() -> dbc.Tab:
    """Create Open Source tab with attribution and license links.

    Returns:
        dbc.Tab containing open source attribution
    """
    content = html.Div(
        [
            html.H5("Open Source Software", className="mb-3"),
            html.P(
                [
                    "This application is built with open source technologies and libraries. ",
                    "We are grateful to the open source community for making this project possible.",
                ],
                className="text-muted mb-3",
            ),
            html.Hr(),
            html.H6("Core Technologies", className="mb-3"),
            # Python
            html.Div(
                [
                    html.Strong("Python"),
                    html.Span(" - Programming Language", className="text-muted ms-2"),
                    html.Br(),
                    html.Small(
                        [
                            html.A(
                                "python.org",
                                href="https://www.python.org",
                                target="_blank",
                                className="text-decoration-none",
                            )
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-3",
            ),
            # Dash / Plotly
            html.Div(
                [
                    html.Strong("Dash / Plotly"),
                    html.Span(
                        " - Interactive Web Framework", className="text-muted ms-2"
                    ),
                    html.Br(),
                    html.Small(
                        [
                            html.A(
                                "plotly.com/dash",
                                href="https://plotly.com/dash",
                                target="_blank",
                                className="text-decoration-none",
                            )
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-3",
            ),
            # Bootstrap
            html.Div(
                [
                    html.Strong("Bootstrap"),
                    html.Span(" - UI Component Library", className="text-muted ms-2"),
                    html.Br(),
                    html.Small(
                        [
                            html.A(
                                "getbootstrap.com",
                                href="https://getbootstrap.com",
                                target="_blank",
                                className="text-decoration-none",
                            )
                        ],
                        className="text-muted",
                    ),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.P(
                [
                    "For a complete list of all dependencies and their licenses, ",
                    "see the ",
                    html.Strong("Licenses"),
                    " tab.",
                ],
                className="text-muted small",
            ),
        ],
        style={"maxHeight": "400px", "overflowY": "auto"},
    )

    return dbc.Tab(
        content,
        label="Open Source",
        tab_id="about-tab-open-source",
        label_style={"cursor": "pointer"},
    )


def _get_licenses_tab() -> dbc.Tab:
    """Create Licenses tab with third-party license information.

    Returns:
        dbc.Tab containing license information
    """
    # Read and parse licenses
    licenses_text = _read_licenses_file()

    # Check if we got an error message
    if licenses_text.startswith("License file not found") or licenses_text.startswith(
        "Error reading"
    ):
        content = html.Div(
            [
                html.H5("Third-Party Licenses", className="mb-3"),
                html.P(
                    "This application uses open source libraries.",
                    className="text-muted mb-3",
                ),
                html.Hr(),
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        licenses_text,
                    ],
                    color="warning",
                ),
            ],
            style={"maxHeight": "400px", "overflowY": "auto"},
        )
    else:
        # Parse licenses
        licenses = _parse_licenses(licenses_text)

        content = html.Div(
            [
                html.H5("Third-Party Licenses", className="mb-3"),
                html.P(
                    [
                        "This application uses the following open source libraries. ",
                        "Expand each item to view license details.",
                    ],
                    className="text-muted mb-3",
                ),
                html.Hr(),
                _create_license_accordion(licenses),
            ],
            style={"maxHeight": "400px", "overflowY": "auto"},
        )

    return dbc.Tab(
        content,
        label="Licenses",
        tab_id="about-tab-licenses",
        label_style={"cursor": "pointer"},
    )


def _get_changelog_tab() -> dbc.Tab:
    """Create Changelog tab with version history.

    Returns:
        dbc.Tab containing changelog information
    """
    content = html.Div(
        [
            html.H5("Changelog", className="mb-3"),
            # Version 2.5.0
            html.Div(
                [
                    html.H6(
                        [
                            html.Code("v2.5.0", className="me-2"),
                            html.Small("Current Version", className="badge bg-success"),
                        ],
                        className="mb-2",
                    ),
                    html.Ul(
                        [
                            html.Li(
                                "Auto-update functionality with standalone updater"
                            ),
                            html.Li(
                                "Build system with PyInstaller for standalone executables"
                            ),
                            html.Li("License management and attribution"),
                            html.Li("About dialog with open source information"),
                        ],
                        className="small text-muted mb-3",
                    ),
                ]
            ),
            html.Hr(),
            # Version 2.0.0+
            html.Div(
                [
                    html.H6(
                        [
                            html.Code("v2.0.0+", className="me-2"),
                        ],
                        className="mb-2",
                    ),
                    html.Ul(
                        [
                            html.Li("PERT-based probabilistic forecasting"),
                            html.Li("JIRA integration with JQL query support"),
                            html.Li("DORA and Flow metrics dashboards"),
                            html.Li("Budget tracking and scope management"),
                            html.Li("Bug analysis and quality insights"),
                            html.Li("Multiple profile support"),
                        ],
                        className="small text-muted mb-3",
                    ),
                ]
            ),
            html.Hr(),
            html.P(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "For detailed release notes, visit the ",
                    html.A(
                        "GitHub Releases",
                        href="https://github.com/niksavis/burndown-chart/releases",
                        target="_blank",
                        className="text-decoration-none",
                    ),
                    " page.",
                ],
                className="text-muted small",
            ),
        ],
        style={"maxHeight": "400px", "overflowY": "auto"},
    )

    return dbc.Tab(
        content,
        label="Changelog",
        tab_id="about-tab-changelog",
        label_style={"cursor": "pointer"},
    )


#######################################################################
# MAIN COMPONENT
#######################################################################


def create_about_dialog() -> dbc.Modal:
    """Create About modal dialog with tabs.

    Returns:
        dbc.Modal component with tabs for App Info, Open Source, Licenses, and Changelog
    """
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "About Burndown Chart",
                    ]
                ),
                close_button=True,
            ),
            dbc.ModalBody(
                dbc.Tabs(
                    [
                        _get_app_info_tab(),
                        _get_open_source_tab(),
                        _get_licenses_tab(),
                        _get_changelog_tab(),
                    ],
                    id="about-tabs",
                    active_tab="about-tab-app-info",
                ),
                className="p-0",
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="about-close-button",
                    color="secondary",
                    className="ms-auto",
                )
            ),
        ],
        id="about-modal",
        size="lg",
        is_open=False,
        centered=True,
        scrollable=True,
    )
