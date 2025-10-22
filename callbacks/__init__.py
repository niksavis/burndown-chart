"""
Callbacks module for the burndown chart application.
"""

from callbacks import (
    bug_analysis,  # Bug analysis metrics callbacks (Feature 004)
    jira_config,  # JIRA configuration modal callbacks (Feature 003)
    jql_editor,  # JQL editor textarea-to-store sync
    mobile_navigation,  # Add mobile navigation callbacks
    # The 'export' module doesn't seem to exist and is causing an error
    # export,
    scope_metrics,  # Add the new scope_metrics module
    settings,
    statistics,
    visualization,
)


def register_all_callbacks(app):
    """Register all callbacks for the application."""
    statistics.register(app)
    visualization.register(app)
    settings.register(app)
    # Remove this line since 'export' module doesn't exist
    # export.register(app)
    scope_metrics.register(app)  # Register the new callbacks
    mobile_navigation.register(app)  # Register mobile navigation callbacks
    jql_editor.register_jql_editor_callbacks(app)  # Register JQL editor sync
    bug_analysis.register(app)  # Register bug analysis callbacks (Feature 004)
    # Note: jira_config callbacks auto-register via @callback decorator when imported
