"""
Profile Settings Card Component

Card for profile workspace management:
- Create new profiles
- Switch between profiles
- Delete profiles

Forecast parameters (PERT factor, deadline, data points) are in the Parameters panel,
as they work with any data source (imported CSV, manual entry, or JIRA).

Part of Feature 011: Profile-First Dependency Architecture
"""

import dash_bootstrap_components as dbc
from dash import html

from ui.profile_selector import create_profile_selector_panel


def create_profile_settings_card() -> html.Div:
    """
    Create profile settings card with workspace management.

    This card contains ONLY profile workspace management:
    - Profile selector (create, switch, delete profiles)

    NOTE: Forecast parameters (PERT factor, deadline, data points, milestones)
    are in the Parameters panel as they are data-source agnostic.

    Returns:
        html.Div: Profile settings configuration content
    """
    return html.Div(
        [
            # Section header matching Connect tab style
            html.Div(
                [
                    html.I(className="fas fa-user me-2 text-primary"),
                    html.Span("Profile Management", className="fw-bold"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            # Profile selector (existing component with create/switch/delete)
            create_profile_selector_panel(),
        ]
    )
