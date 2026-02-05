"""
Update Notification Component

Displays a notification banner when a new version is available,
with an "Update Now" button to download and install the update.
"""

#######################################################################
# IMPORTS
#######################################################################
# Third-party library imports
import dash_bootstrap_components as dbc
from dash import html
from typing import Optional

# Application imports
from data.update_manager import UpdateProgress, UpdateState

#######################################################################
# COMPONENT FUNCTIONS
#######################################################################


def create_update_notification(
    update_progress: Optional[UpdateProgress],
) -> Optional[dbc.Alert]:
    """Create update notification alert when update is available.

    Args:
        update_progress: UpdateProgress object from app.VERSION_CHECK_RESULT

    Returns:
        dbc.Alert component if update available, None otherwise
    """
    # Only show alert if update is available
    if not update_progress or update_progress.state != UpdateState.AVAILABLE:
        return None

    # Extract version information
    current_version = update_progress.current_version or "unknown"
    available_version = update_progress.available_version or "unknown"

    # Create alert content
    alert_content = [
        html.Div(
            [
                html.I(className="fas fa-arrow-circle-up me-2"),
                html.Strong(f"Version {available_version} Available"),
            ],
            className="d-flex align-items-center mb-2",
        ),
        html.P(
            f"A new version of Burndown is available. "
            f"You are currently running version {current_version}.",
            className="mb-2",
            style={"fontSize": "0.9rem"},
        ),
    ]

    # Add release notes if available
    if update_progress.release_notes:
        # Truncate release notes if too long (show first 200 chars)
        notes = update_progress.release_notes
        if len(notes) > 200:
            notes = notes[:200] + "..."

        alert_content.append(
            html.Div(
                [
                    html.Strong("What's New:", className="d-block mb-1"),
                    html.P(
                        notes,
                        className="mb-2",
                        style={
                            "fontSize": "0.85rem",
                            "whiteSpace": "pre-wrap",
                            "opacity": "0.9",
                        },
                    ),
                ]
            )
        )

    # Add Update Now button
    alert_content.append(
        html.Div(
            [
                dbc.Button(
                    [
                        html.I(className="fas fa-download me-2"),
                        "Update Now",
                    ],
                    id="update-now-button",
                    color="primary",
                    size="sm",
                    className="me-2",
                ),
                dbc.Button(
                    "Dismiss",
                    id="update-dismiss-button",
                    color="secondary",
                    outline=True,
                    size="sm",
                ),
            ],
            className="d-flex gap-2",
        )
    )

    # Create the alert
    return dbc.Alert(
        alert_content,
        id="update-notification-alert",
        color="info",
        dismissable=True,
        is_open=True,
        className="mb-3",
        style={
            "borderLeft": "4px solid #0dcaf0",
        },
    )


def create_update_downloading_alert(
    progress_percent: int = 0,
) -> dbc.Alert:
    """Create alert showing download progress.

    Args:
        progress_percent: Download progress (0-100)

    Returns:
        dbc.Alert component with progress bar
    """
    return dbc.Alert(
        [
            html.Div(
                [
                    html.I(className="fas fa-spinner fa-spin me-2"),
                    html.Strong("Downloading Update..."),
                ],
                className="d-flex align-items-center mb-2",
            ),
            dbc.Progress(
                value=progress_percent,
                label=f"{progress_percent}%",
                className="mb-2",
                style={"height": "20px"},
            ),
            html.P(
                "Please wait while the update is being downloaded. "
                "This may take a few minutes depending on your connection.",
                className="mb-0",
                style={"fontSize": "0.85rem", "opacity": "0.8"},
            ),
        ],
        id="update-downloading-alert",
        color="info",
        dismissable=False,
        is_open=True,
        className="mb-3",
    )


def create_update_ready_alert() -> dbc.Alert:
    """Create alert when update is ready to install.

    Returns:
        dbc.Alert component with install button
    """
    return dbc.Alert(
        [
            html.Div(
                [
                    html.I(className="fas fa-check-circle me-2"),
                    html.Strong("Update Ready to Install"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.P(
                "The update has been downloaded successfully. "
                "Click 'Install Now' to apply the update. "
                "The application will restart automatically.",
                className="mb-2",
                style={"fontSize": "0.9rem"},
            ),
            dbc.Button(
                [
                    html.I(className="fas fa-sync-alt me-2"),
                    "Install Now",
                ],
                id="update-install-button",
                color="success",
                size="sm",
            ),
        ],
        id="update-ready-alert",
        color="success",
        dismissable=False,
        is_open=True,
        className="mb-3",
        style={
            "borderLeft": "4px solid #198754",
        },
    )


def create_update_error_alert(error_message: str) -> dbc.Alert:
    """Create alert when update check or download fails.

    Args:
        error_message: Human-readable error description

    Returns:
        dbc.Alert component with error message
    """
    return dbc.Alert(
        [
            html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    html.Strong("Update Failed"),
                ],
                className="d-flex align-items-center mb-2",
            ),
            html.P(
                error_message,
                className="mb-2",
                style={"fontSize": "0.9rem"},
            ),
            html.P(
                "You can check for updates manually by visiting the GitHub releases page.",
                className="mb-0",
                style={"fontSize": "0.85rem", "opacity": "0.8"},
            ),
        ],
        id="update-error-alert",
        color="warning",
        dismissable=True,
        is_open=True,
        className="mb-3",
    )
