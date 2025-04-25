"""
Callbacks module for the burndown chart application.
"""

from callbacks import (
    statistics,
    visualization,
    settings,
    # The 'export' module doesn't seem to exist and is causing an error
    # export,
    scope_metrics,  # Add the new scope_metrics module
)


def register_all_callbacks(app):
    """Register all callbacks for the application."""
    statistics.register(app)
    visualization.register(app)
    settings.register(app)
    # Remove this line since 'export' module doesn't exist
    # export.register(app)
    scope_metrics.register(app)  # Register the new callbacks
