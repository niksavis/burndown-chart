"""
About Dialog Component

Modal dialog displaying application information, open source licenses,
and changelog. Provides transparency about the application and its dependencies.
"""

#######################################################################
# IMPORTS
#######################################################################
import sys

import dash_bootstrap_components as dbc
from dash import html

from configuration import __version__


#######################################################################
# HELPER FUNCTIONS
#######################################################################


def _get_app_info_tab() -> dbc.Tab:
    """Create App Info tab with version and system information.
    
    Returns:
        dbc.Tab containing application information
    """
    # Get Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Check if running as frozen executable
    is_frozen = getattr(sys, 'frozen', False)
    install_type = "Standalone Executable" if is_frozen else "Development Mode"
    
    content = html.Div([
        html.H5("Burndown Chart", className="mb-3"),
        html.P([
            html.Strong("Version: "),
            html.Span(__version__, className="text-muted")
        ], className="mb-2"),
        html.P([
            html.Strong("Installation: "),
            html.Span(install_type, className="text-muted")
        ], className="mb-2"),
        html.P([
            html.Strong("Python: "),
            html.Span(python_version, className="text-muted")
        ], className="mb-3"),
        
        html.Hr(),
        
        html.H6("About", className="mb-2"),
        html.P([
            "PERT-based agile forecasting tool with JIRA integration. ",
            "Provides probabilistic sprint planning using statistical modeling."
        ], className="text-muted mb-3"),
        
        html.H6("Author", className="mb-2"),
        html.P([
            html.I(className="fas fa-user me-2"),
            "Niksa Visic"
        ], className="text-muted mb-3"),
        
        html.H6("License", className="mb-2"),
        html.P([
            "MIT License - Free and open source software"
        ], className="text-muted"),
    ], style={"maxHeight": "400px", "overflowY": "auto"})
    
    return dbc.Tab(
        content,
        label="App Info",
        tab_id="about-tab-app-info",
        label_style={"cursor": "pointer"}
    )


def _get_open_source_tab() -> dbc.Tab:
    """Create Open Source tab with attribution and license links.
    
    Returns:
        dbc.Tab containing open source attribution
    """
    content = html.Div([
        html.H5("Open Source Software", className="mb-3"),
        html.P([
            "This application is built with open source technologies and libraries. ",
            "We are grateful to the open source community for making this project possible."
        ], className="text-muted mb-3"),
        
        html.Hr(),
        
        html.H6("Core Technologies", className="mb-3"),
        
        # Python
        html.Div([
            html.Strong("Python"),
            html.Span(" - Programming Language", className="text-muted ms-2"),
            html.Br(),
            html.Small([
                html.A("python.org", href="https://www.python.org", target="_blank", className="text-decoration-none")
            ], className="text-muted")
        ], className="mb-3"),
        
        # Dash / Plotly
        html.Div([
            html.Strong("Dash / Plotly"),
            html.Span(" - Interactive Web Framework", className="text-muted ms-2"),
            html.Br(),
            html.Small([
                html.A("plotly.com/dash", href="https://plotly.com/dash", target="_blank", className="text-decoration-none")
            ], className="text-muted")
        ], className="mb-3"),
        
        # Bootstrap
        html.Div([
            html.Strong("Bootstrap"),
            html.Span(" - UI Component Library", className="text-muted ms-2"),
            html.Br(),
            html.Small([
                html.A("getbootstrap.com", href="https://getbootstrap.com", target="_blank", className="text-decoration-none")
            ], className="text-muted")
        ], className="mb-3"),
        
        html.Hr(),
        
        html.P([
            "For a complete list of all dependencies and their licenses, ",
            "see the ",
            html.Strong("Licenses"),
            " tab."
        ], className="text-muted small"),
        
    ], style={"maxHeight": "400px", "overflowY": "auto"})
    
    return dbc.Tab(
        content,
        label="Open Source",
        tab_id="about-tab-open-source",
        label_style={"cursor": "pointer"}
    )


def _get_licenses_tab() -> dbc.Tab:
    """Create Licenses tab with third-party license information.
    
    Returns:
        dbc.Tab containing license information placeholder
    """
    # Placeholder - will be populated by t064
    content = html.Div([
        html.H5("Third-Party Licenses", className="mb-3"),
        html.P([
            "This application uses the following open source libraries. ",
            "Click on a library name to view its license details."
        ], className="text-muted mb-3"),
        
        html.Hr(),
        
        # Placeholder for license list (will be implemented in t064)
        html.Div(id="about-licenses-list", children=[
            dbc.Spinner(
                html.Div("Loading licenses...", className="text-muted"),
                color="primary",
                size="sm"
            )
        ]),
        
    ], style={"maxHeight": "400px", "overflowY": "auto"})
    
    return dbc.Tab(
        content,
        label="Licenses",
        tab_id="about-tab-licenses",
        label_style={"cursor": "pointer"}
    )


def _get_changelog_tab() -> dbc.Tab:
    """Create Changelog tab with version history.
    
    Returns:
        dbc.Tab containing changelog information
    """
    content = html.Div([
        html.H5("Changelog", className="mb-3"),
        
        # Version 2.5.0
        html.Div([
            html.H6([
                html.Code("v2.5.0", className="me-2"),
                html.Small("Current Version", className="badge bg-success")
            ], className="mb-2"),
            html.Ul([
                html.Li("Auto-update functionality with standalone updater"),
                html.Li("Build system with PyInstaller for standalone executables"),
                html.Li("License management and attribution"),
                html.Li("About dialog with open source information"),
            ], className="small text-muted mb-3")
        ]),
        
        html.Hr(),
        
        # Version 2.0.0+
        html.Div([
            html.H6([
                html.Code("v2.0.0+", className="me-2"),
            ], className="mb-2"),
            html.Ul([
                html.Li("PERT-based probabilistic forecasting"),
                html.Li("JIRA integration with JQL query support"),
                html.Li("DORA and Flow metrics dashboards"),
                html.Li("Budget tracking and scope management"),
                html.Li("Bug analysis and quality insights"),
                html.Li("Multiple profile support"),
            ], className="small text-muted mb-3")
        ]),
        
        html.Hr(),
        
        html.P([
            html.I(className="fas fa-info-circle me-2"),
            "For detailed release notes, visit the ",
            html.A("GitHub Releases", 
                   href="https://github.com/niksavis/burndown-chart/releases",
                   target="_blank",
                   className="text-decoration-none"),
            " page."
        ], className="text-muted small"),
        
    ], style={"maxHeight": "400px", "overflowY": "auto"})
    
    return dbc.Tab(
        content,
        label="Changelog",
        tab_id="about-tab-changelog",
        label_style={"cursor": "pointer"}
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
                dbc.ModalTitle([
                    html.I(className="fas fa-info-circle me-2"),
                    "About Burndown Chart"
                ]),
                close_button=True
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
                    active_tab="about-tab-app-info"
                ),
                className="p-0"
            ),
            dbc.ModalFooter(
                dbc.Button(
                    "Close",
                    id="about-close-button",
                    color="secondary",
                    className="ms-auto"
                )
            )
        ],
        id="about-modal",
        size="lg",
        is_open=False,
        centered=True,
        scrollable=True
    )
