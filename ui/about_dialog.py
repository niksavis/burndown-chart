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

    Defensive parsing that handles format variations gracefully without breaking UI.

    Args:
        licenses_text: Content from THIRD_PARTY_LICENSES.txt

    Returns:
        List of dicts with keys: name, version, license, url, description
    """
    licenses = []
    current_entry = {}
    field_order = ["name", "version", "license", "url", "description"]
    field_index = 0

    try:
        lines = licenses_text.split("\n")

        # Defensive: Find where actual licenses start by looking for separator pattern
        # Expected format: first 11 lines are header, but check for separator to be safe
        start_index = 0
        separator_count = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("==="):
                separator_count += 1
                if separator_count == 2:
                    # Start after second separator and skip any blank lines
                    start_index = i + 1
                    while start_index < len(lines) and not lines[start_index].strip():
                        start_index += 1
                    break

        # Fallback: if no separators found, assume first 11 lines are header
        if start_index == 0:
            start_index = min(11, len(lines))

        # Parse license entries starting after header
        for line in lines[start_index:]:
            line = line.strip()

            # Empty line signals end of an entry
            if not line:
                # Only add entry if it has all required fields
                if current_entry and len(current_entry) == len(field_order):
                    licenses.append(current_entry)
                # Reset for incomplete entries too (defensive)
                current_entry = {}
                field_index = 0
                continue

            # Parse field based on position (plain-vertical format)
            if field_index < len(field_order):
                field_name = field_order[field_index]
                current_entry[field_name] = line
                field_index += 1
            # Defensive: ignore extra lines beyond expected 5 fields

        # Add last entry if exists and complete
        if current_entry and len(current_entry) == len(field_order):
            licenses.append(current_entry)

    except Exception as e:
        # Defensive: if parsing fails completely, return empty list
        # This prevents UI crash but logs the error
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"License parsing failed: {e}", exc_info=True)
        return []

    return licenses


def _create_license_accordion(licenses: list[dict]) -> html.Div | dbc.Alert:
    """Create accordion with all license entries.

    Args:
        licenses: List of license dicts

    Returns:
        html.Div containing accordion with all licenses or Alert if empty
    """
    if not licenses:
        return dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2"),
                "License information could not be parsed. The application uses open source dependencies - ",
                "please see the project repository for full license details.",
            ],
            color="info",
            className="mb-0",
        )

    accordion_items = []

    for idx, lic in enumerate(licenses):
        name = lic.get("name", "Unknown")
        version = lic.get("version", "")
        license_type = lic.get("license", "Unknown License")
        url = lic.get("url", "")
        description = lic.get("description", "")

        # Create accordion item with enhanced title for searchability
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
                # Include license type in title for searchability
                title=f"{name} ({version}) - {license_type}"
                if version
                else f"{name} - {license_type}",
                item_id=f"license-{idx}",
                className="license-item",
            )
        )

    return html.Div(
        [
            html.P(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    html.Span(
                        f"Showing {len(licenses)} dependencies",
                        id="license-count-text",
                    ),
                ],
                className="text-muted small mb-3",
            ),
            dbc.Accordion(
                accordion_items,
                id="licenses-accordion",
                flush=True,
                start_collapsed=True,
            ),
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
        className="p-3",
        style={"minHeight": "500px", "maxHeight": "500px", "overflowY": "auto"},
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
        className="p-3",
        style={"minHeight": "500px", "maxHeight": "500px", "overflowY": "auto"},
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
                dbc.Alert(
                    [
                        html.I(className="fas fa-exclamation-triangle me-2"),
                        licenses_text,
                    ],
                    color="warning",
                ),
            ],
            className="p-3",
            style={"maxHeight": "500px", "overflowY": "auto"},
        )
    else:
        # Parse licenses
        licenses = _parse_licenses(licenses_text)

        # Extract unique license types for autocomplete
        license_types = sorted(
            set(lic.get("license", "") for lic in licenses if lic.get("license"))
        )

        content = html.Div(
            [
                html.H5("Third-Party Software Licenses", className="mb-3"),
                html.P(
                    [
                        "This application bundles the following open source dependencies. ",
                        "Expand each item to view full license details.",
                    ],
                    className="text-muted mb-3",
                ),
                # Search/filter input with autocomplete and clear button
                html.Div(
                    [
                        dbc.InputGroup(
                            [
                                dbc.Input(
                                    id="license-search-input",
                                    type="text",
                                    placeholder="Search by name or license type...",
                                    size="sm",
                                    list="license-types-datalist",
                                    debounce=300,  # 300ms debounce for better performance
                                ),
                                dbc.InputGroupText(
                                    html.I(className="fas fa-search"),
                                    className="bg-light border-start-0",
                                    style={"cursor": "default"},
                                ),
                            ],
                            size="sm",
                            className="mb-2",
                        ),
                        html.Datalist(
                            [html.Option(value=lt) for lt in license_types],
                            id="license-types-datalist",
                        ),
                    ],
                    className="mb-3",
                ),
                # No results message (hidden by default)
                dbc.Alert(
                    [
                        html.I(className="fas fa-search me-2"),
                        "No licenses match your search. Try a different term.",
                    ],
                    id="license-no-results",
                    color="info",
                    className="mb-3",
                    style={"display": "none"},
                ),
                _create_license_accordion(licenses),
            ],
            className="p-3",
            style={"minHeight": "500px", "maxHeight": "500px", "overflowY": "auto"},
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
    changelog_content = _read_and_parse_changelog()

    content = html.Div(
        [
            html.H5("Changelog", className="mb-3"),
            changelog_content,
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
        className="p-3",
        style={"minHeight": "500px", "maxHeight": "500px", "overflowY": "auto"},
    )

    return dbc.Tab(
        content,
        label="Changelog",
        tab_id="about-tab-changelog",
        label_style={"cursor": "pointer"},
    )


def _read_and_parse_changelog() -> html.Div:
    """Read and parse changelog.md file.

    Returns:
        html.Div containing parsed changelog sections or fallback content
    """
    import sys
    from pathlib import Path

    # Determine changelog path (works for both dev and frozen)
    if getattr(sys, "frozen", False):
        # Running as frozen executable - changelog should be in same dir as exe
        base_path = Path(sys.executable).parent
    else:
        # Running in development - changelog in project root
        base_path = Path(__file__).parent.parent

    changelog_file = base_path / "changelog.md"

    if not changelog_file.exists():
        # Fallback to hardcoded content if file not found
        return html.Div(
            [
                html.Div(
                    [
                        html.H6(
                            [
                                html.Code("v2.5.0", className="me-2"),
                                html.Small(
                                    "Current Version", className="badge bg-success"
                                ),
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
                dbc.Alert(
                    [
                        html.I(className="fas fa-info-circle me-2"),
                        "Changelog file not found. See GitHub Releases for full version history.",
                    ],
                    color="info",
                    className="mb-0",
                ),
            ]
        )

    try:
        content = changelog_file.read_text(encoding="utf-8")

        # Parse markdown sections by version (## v{version})
        version_sections = []
        lines = content.split("\n")

        current_version = None
        current_content = []

        for line in lines:
            if line.startswith("## v"):
                # Save previous section
                if current_version and current_content:
                    version_sections.append(
                        (current_version, "\n".join(current_content))
                    )

                # Start new section
                current_version = line.replace("## ", "").strip()
                current_content = []
            elif line.startswith("# Changelog"):
                # Skip main title
                continue
            elif current_version:
                # Accumulate content for current version
                current_content.append(line)

        # Save last section
        if current_version and current_content:
            version_sections.append((current_version, "\n".join(current_content)))

        # Convert to HTML
        if not version_sections:
            return html.Div(
                dbc.Alert(
                    "No version history found in changelog.",
                    color="info",
                )
            )

        elements = []
        for idx, (version, section_content) in enumerate(version_sections):
            # Parse section content
            section_lines = [
                line for line in section_content.split("\n") if line.strip()
            ]

            # Extract date if present
            date_text = None
            items = []

            for line in section_lines:
                if line.strip().startswith("*Released:"):
                    date_text = line.strip().replace("*", "")
                elif line.strip().startswith("###"):
                    # Skip section headings - not currently displayed
                    continue
                elif line.strip().startswith("-"):
                    items.append(html.Li(line.strip()[2:]))  # Remove "- " prefix

            # Build version section
            version_header: list = [html.Code(version, className="me-2")]
            if idx == 0:
                version_header.append(
                    html.Small("Latest", className="badge bg-success")
                )

            version_div = html.Div(
                [
                    html.H6(version_header, className="mb-2"),
                    html.P(date_text, className="text-muted small mb-2")
                    if date_text
                    else None,
                    html.Ul(items, className="small text-muted mb-3")
                    if items
                    else None,
                ]
            )

            elements.append(version_div)

            # Add separator except for last item
            if idx < len(version_sections) - 1:
                elements.append(html.Hr())

        return html.Div(elements)

    except Exception as e:
        # Fallback on parse error
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Error parsing changelog: {e}", exc_info=True)

        return html.Div(
            dbc.Alert(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error reading changelog: {str(e)}",
                ],
                color="warning",
            )
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
