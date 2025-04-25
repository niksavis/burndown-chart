"""
Settings form for the burndown chart application.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_settings_form(settings=None):
    """Create settings form for the application."""
    settings = settings or {}

    # Extract scope creep settings
    scope_creep_threshold = settings.get("scope_creep_threshold", 15)
    track_scope_changes = settings.get("track_scope_changes", True)

    # ...existing code...

    return html.Div(
        [
            # ...existing code...
            html.H5("Scope Tracking Settings", className="mt-4 mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Track Scope Changes", className="form-label"),
                            dbc.Switch(
                                id="track-scope-changes-switch",
                                value=track_scope_changes,
                                label="Enable scope change tracking",
                                className="mb-3",
                            ),
                        ],
                        width=12,
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "Scope Creep Threshold (%)", className="form-label"
                            ),
                            dbc.Input(
                                id="scope-creep-threshold-input",
                                type="number",
                                min=1,
                                max=100,
                                step=1,
                                value=scope_creep_threshold,
                            ),
                            html.Small(
                                "Alert when scope creep rate exceeds this threshold.",
                                className="text-muted",
                            ),
                        ],
                        width=12,
                    ),
                ]
            ),
            # ...existing code...
        ]
    )


def update_settings_from_form(current_settings, form_values):
    """Update settings dictionary from form values."""
    # ...existing code...

    # Update scope creep settings
    current_settings["scope_creep_threshold"] = form_values.get(
        "scope_creep_threshold", 15
    )
    current_settings["track_scope_changes"] = form_values.get(
        "track_scope_changes", True
    )

    return current_settings
