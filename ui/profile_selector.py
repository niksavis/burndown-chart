import dash_bootstrap_components as dbc
from dash import dcc, html

from data.profile_manager import get_active_profile, list_profiles


def create_profile_dropdown(id_suffix: str = "") -> dbc.Col:

    profiles = list_profiles()
    active_profile = get_active_profile()

    options = []
    for profile in profiles:
        jira_info = ""
        if profile.get("jira_url"):
            jira_info = f" • {profile['jira_url']}"

        label = f"{profile['name']}{jira_info}"
        if profile["id"] == (active_profile.id if active_profile else None):
            label += " [Active]"

        options.append({"label": label, "value": profile["id"]})

    value = (
        active_profile.id if active_profile else (profiles[0]["id"] if profiles else "")
    )

    return dbc.Col(
        [
            dcc.Store(id="profile-switch-trigger", data=0),
            html.Label(
                "Profile",
                className="form-label fw-bold mb-1",
            ),
            dcc.Dropdown(
                id=f"profile-selector{id_suffix}",
                options=options,
                value=value,
                placeholder="No profiles - click 'New' to create one"
                if not options
                else "Select a profile...",
                clearable=False,
            ),
        ],
        xs=12,
        lg=6,
        className="mb-3",
        id="profile-selector-container",
    )


def create_profile_actions(id_suffix: str = "") -> dbc.Col:

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
                    color="primary",
                    outline=True,
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="fas fa-copy me-1"), "Duplicate"],
                    id=f"duplicate-profile-btn{id_suffix}",
                    color="primary",
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
            style={"marginTop": "1.71rem"},
        ),
        xs=12,
        lg=6,
        className="mb-3",
    )


def create_profile_selector_panel(id_suffix: str = "") -> html.Div:

    return html.Div(
        [
            dbc.Row(
                [
                    create_profile_dropdown(id_suffix),
                    create_profile_actions(id_suffix),
                ],
                className="g-2",
            ),
        ],
        className="mb-0",
        style={"position": "relative"},
    )


def create_profile_tooltip_content(profile: dict) -> str:

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
