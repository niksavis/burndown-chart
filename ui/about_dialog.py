import sys
from pathlib import Path

import dash_bootstrap_components as dbc
from dash import html

from configuration import __version__


def _parse_markdown_text(text: str) -> list:

    import re  # noqa: PLC0415

    pattern = r"(\*\*.*?\*\*|`.*?`|\[.*?\]\(.*?\))"
    parts = re.split(pattern, text)

    components = []
    for part in parts:
        if not part:
            continue

        if part.startswith("**") and part.endswith("**"):
            bold_text = part[2:-2]
            components.append(html.Strong(bold_text))
        elif part.startswith("`") and part.endswith("`"):
            code_text = part[1:-1]
            components.append(html.Code(code_text, className="mx-1"))
        elif part.startswith("[") and "](" in part:
            link_match = re.match(r"\[(.*?)\]\((.*?)\)", part)
            if link_match:
                link_text, url = link_match.groups()
                components.append(
                    html.A(
                        link_text,
                        href=url,
                        target="_blank",
                        className="text-decoration-none",
                    )
                )
            else:
                components.append(html.Span(part))
        else:
            components.append(html.Span(part))

    return components if components else [html.Span(text)]


def _read_licenses_file() -> str:

    try:
        is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        if is_frozen:
            meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
            licenses_file = meipass / "licenses" / "THIRD_PARTY_LICENSES.txt"
        else:
            project_root = Path(__file__).parent.parent
            licenses_file = project_root / "licenses" / "THIRD_PARTY_LICENSES.txt"

        if licenses_file.exists():
            return licenses_file.read_text(encoding="utf-8")
        else:
            return f"License file not found at: {licenses_file}"

    except Exception as e:
        return f"Error reading licenses: {e}"


def _parse_licenses(licenses_text: str) -> list[dict]:

    licenses = []
    current_entry = {}
    field_order = ["name", "version", "license", "url", "description"]
    field_index = 0

    try:
        lines = licenses_text.split("\n")

        start_index = 0
        separator_count = 0
        for i, line in enumerate(lines):
            if line.strip().startswith("==="):
                separator_count += 1
                if separator_count == 2:
                    start_index = i + 1
                    while start_index < len(lines) and not lines[start_index].strip():
                        start_index += 1
                    break

        if start_index == 0:
            start_index = min(11, len(lines))

        for line in lines[start_index:]:
            line = line.strip()

            if not line:
                if current_entry and len(current_entry) == len(field_order):
                    licenses.append(current_entry)
                current_entry = {}
                field_index = 0
                continue

            if field_index < len(field_order):
                field_name = field_order[field_index]
                current_entry[field_name] = line
                field_index += 1

        if current_entry and len(current_entry) == len(field_order):
            licenses.append(current_entry)

    except Exception as e:
        import logging  # noqa: PLC0415

        logger = logging.getLogger(__name__)
        logger.error(f"License parsing failed: {e}", exc_info=True)
        return []

    return licenses


def _create_license_accordion(licenses: list[dict]) -> html.Div | dbc.Alert:

    if not licenses:
        return dbc.Alert(
            [
                html.I(className="fas fa-info-circle me-2 text-info"),
                (
                    "License information could not be parsed. "
                    "The application uses open source dependencies - "
                ),
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
                    html.I(className="fas fa-info-circle me-2 text-info"),
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

    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    is_frozen = getattr(sys, "frozen", False)
    install_type = "Standalone Executable" if is_frozen else "Development Mode"

    latest_release = _get_latest_release_notes()

    content_sections = [
        html.H5("Burndown", className="mb-3"),
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
    ]

    if latest_release:
        version, date, items = latest_release
        content_sections.extend(
            [
                html.Hr(),
                html.H6(
                    [
                        "What's New in ",
                        html.Code(version, className="ms-1"),
                    ],
                    className="mb-2",
                ),
                html.P(
                    [
                        html.I(className="fas fa-calendar-alt me-2"),
                        html.Small(date, className="text-muted"),
                    ],
                    className="mb-2",
                ),
                html.Ul(
                    [
                        html.Li(_parse_markdown_text(item), className="mb-1")
                        for item in items
                    ],
                    className="text-muted small mb-2",
                ),
                html.P(
                    [
                        html.A(
                            [
                                html.I(className="fas fa-history me-1"),
                                "View full changelog",
                            ],
                            href="#",
                            id="view-changelog-link",
                            className="text-decoration-none",
                        ),
                    ],
                    className="mb-3",
                ),
            ]
        )

    content_sections.extend(
        [
            html.Hr(),
            html.H6("About", className="mb-2"),
            html.P(
                [
                    "Project forecasting and metrics platform with JIRA integration. ",
                    (
                        "Delivers probabilistic completion forecasts, "
                        "comprehensive project health scores, "
                    ),
                    (
                        "and industry-standard performance metrics "
                        "(DORA, Flow) using statistical modeling "
                    ),
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
        ]
    )

    content = html.Div(
        content_sections,
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

    content = html.Div(
        [
            html.H5("Open Source Software", className="mb-3"),
            html.P(
                [
                    (
                        "This application is built with open source "
                        "technologies and libraries. "
                    ),
                    (
                        "We are grateful to the open source community "
                        "for making this project possible."
                    ),
                ],
                className="text-muted mb-3",
            ),
            html.Hr(),
            html.H6("Core Technologies", className="mb-3"),
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

    licenses_text = _read_licenses_file()

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
        licenses = _parse_licenses(licenses_text)

        license_types = sorted(
            set(lic.get("license", "") for lic in licenses if lic.get("license"))
        )

        content = html.Div(
            [
                html.H5("Third-Party Software Licenses", className="mb-3"),
                html.P(
                    [
                        (
                            "This application bundles the following "
                            "open source dependencies. "
                        ),
                        "Expand each item to view full license details.",
                    ],
                    className="text-muted mb-3",
                ),
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
                                    debounce=300,
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

    changelog_content = _read_and_parse_changelog()

    content = html.Div(
        [
            html.H5("Changelog", className="mb-3"),
            changelog_content,
            html.Hr(),
            html.P(
                [
                    html.I(className="fas fa-info-circle me-2 text-info"),
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


def _get_latest_release_notes() -> tuple[str, str, list[str]] | None:

    import sys  # noqa: PLC0415

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).parent.parent

    changelog_file = base_path / "changelog.md"

    if not changelog_file.exists():
        return None

    try:
        content = changelog_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        version = None
        date = None
        items = []
        in_version_section = False

        for line in lines:
            if line.startswith("## v"):
                if in_version_section:
                    break
                version = line.replace("## ", "").strip()
                in_version_section = True
            elif in_version_section:
                if line.strip().lstrip("*_").startswith("Released:"):
                    date = line.strip().strip("*_").replace("Released:", "").strip()
                elif line.strip().startswith("- "):
                    item = line.strip()[2:]
                    items.append(item)

        if version and items:
            return (version, date or "Date unknown", items[:5])

        return None

    except Exception:
        return None


def _read_and_parse_changelog() -> html.Div:

    import sys  # noqa: PLC0415

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).parent.parent

    changelog_file = base_path / "changelog.md"

    if not changelog_file.exists():
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
                                    "Build system with PyInstaller "
                                    "for standalone executables"
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
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        (
                            "Changelog file not found. See GitHub Releases "
                            "for full version history."
                        ),
                    ],
                    color="info",
                    className="mb-0",
                ),
            ]
        )

    try:
        content = changelog_file.read_text(encoding="utf-8")

        version_sections = []
        lines = content.split("\n")

        current_version = None
        current_content = []

        for line in lines:
            if line.startswith("## v"):
                if current_version and current_content:
                    version_sections.append(
                        (current_version, "\n".join(current_content))
                    )

                current_version = line.replace("## ", "").strip()
                current_content = []
            elif line.startswith("# Changelog"):
                continue
            elif current_version:
                current_content.append(line)

        if current_version and current_content:
            version_sections.append((current_version, "\n".join(current_content)))

        if not version_sections:
            return html.Div(
                dbc.Alert(
                    "No version history found in changelog.",
                    color="info",
                )
            )

        elements = []
        for idx, (version, section_content) in enumerate(version_sections):
            section_lines = [
                line for line in section_content.split("\n") if line.strip()
            ]

            date_text = None
            items = []

            for line in section_lines:
                if line.strip().lstrip("*_").startswith("Released:"):
                    date_text = line.strip().strip("*_")
                elif line.strip().startswith("###"):
                    continue
                elif line.strip().startswith("-"):
                    item_text = line.strip()[2:]
                    items.append(html.Li(_parse_markdown_text(item_text)))

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

            if idx < len(version_sections) - 1:
                elements.append(html.Hr())

        return html.Div(elements)

    except Exception as e:
        import logging  # noqa: PLC0415

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


def create_about_dialog() -> dbc.Modal:

    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle(
                    [
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        "About Burndown",
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
