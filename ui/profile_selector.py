"""
Profile selector UI component.

Provides dropdown for profile selection and management buttons.
Follows the same pattern as query_selector.py for consistency.
"""

from typing import Dict
from dash import html, dcc
import dash_bootstrap_components as dbc

from data.profile_manager import list_profiles, get_active_profile


def create_profile_dropdown(id_suffix: str = "") -> dbc.Col:
    """Create profile dropdown selector.

    Args:
        id_suffix: Optional suffix for component IDs

    Returns:
        Bootstrap column containing profile dropdown
    """
    # Load profiles
    profiles = list_profiles()
    active_profile = get_active_profile()

    # Build dropdown options
    options = []
    for profile in profiles:
        # Create label with metadata tooltip info
        jira_info = ""
        if profile.get("jira_url"):
            jira_info = f" • {profile['jira_url']}"

        label = f"{profile['name']}{jira_info}"
        if profile["id"] == (active_profile.id if active_profile else None):
            label += " [Active]"

        options.append({"label": label, "value": profile["id"]})

    # Determine initial value
    value = (
        active_profile.id if active_profile else (profiles[0]["id"] if profiles else "")
    )

    return dbc.Col(
        [
            # Hidden store to trigger dropdown refresh after profile switches
            dcc.Store(id="profile-switch-trigger", data=0),
            html.Label(
                "Profile",
                htmlFor=f"profile-selector{id_suffix}",
                className="form-label fw-bold mb-1",
            ),
            dcc.Dropdown(
                id=f"profile-selector{id_suffix}",
                options=options,
                value=value,
                placeholder="Select a profile...",
                clearable=False,
            ),
        ],
        xs=12,
        lg=6,
        className="mb-2",
        id="profile-selector-container",  # ID for CSS z-index stacking context
    )


def create_profile_actions(id_suffix: str = "") -> dbc.Col:
    """Create profile action buttons (create, rename, duplicate, delete).

    Args:
        id_suffix: Optional suffix for component IDs

    Returns:
        Bootstrap column containing action buttons
    """
    return dbc.Col(
        dbc.ButtonGroup(
            [
                dbc.Button(
                    [html.I(className="fas fa-plus me-1"), "New"],
                    id=f"create-profile-btn{id_suffix}",
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-edit me-1"), "Rename"],
                    id=f"rename-profile-btn{id_suffix}",
                    color="secondary",
                    outline=True,
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-copy me-1"), "Duplicate"],
                    id=f"duplicate-profile-btn{id_suffix}",
                    color="secondary",
                    outline=True,
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-trash me-1"), "Delete"],
                    id=f"delete-profile-btn{id_suffix}",
                    color="danger",
                    outline=True,
                ),
            ],
            className="w-100",
            style={"marginTop": "1.71rem"},  # Align with dropdown (label height + mb-1)
        ),
        xs=12,
        lg=6,
        className="mb-2",
    )


def create_profile_selector_panel(id_suffix: str = "") -> dbc.Card:
    """Create complete profile selector panel with dropdown and actions.

    Args:
        id_suffix: Optional suffix for component IDs

    Returns:
        Bootstrap card containing profile management UI
    """
    # Use same UI regardless of profile count - simpler and consistent
    return dbc.Card(
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        create_profile_dropdown(id_suffix),
                        create_profile_actions(id_suffix),
                    ],
                    className="g-2",
                ),
            ]
        ),
        className="mb-3",
    )


def create_profile_tooltip_content(profile: Dict) -> str:
    """Create tooltip content for profile hover.

    Args:
        profile: Profile data dict

    Returns:
        HTML string for tooltip
    """
    parts = []

    if profile.get("description"):
        parts.append(f"{profile['description']}")

    if profile.get("jira_url"):
        parts.append(f"URL: {profile['jira_url']}")

    pert_factor = profile.get("pert_factor", 1.2)
    parts.append(f"PERT Factor: {pert_factor}")

    query_count = profile.get("query_count", 0)
    parts.append(f"{query_count} queries")

    if profile.get("created_at"):
        parts.append(f"Created: {profile['created_at'][:10]}")

    return "<br>".join(parts)
