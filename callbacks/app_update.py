"""
Callbacks for application auto-update functionality.

Handles the workflow of checking git status, performing updates,
and managing the update modal UI states.
"""

import logging
from dash import callback, Input, Output, State, html, no_update

from utils.git_updater import check_git_status, perform_update

logger = logging.getLogger(__name__)


@callback(
    Output("update-modal", "is_open"),
    Output("update-result-section", "style"),
    Output("update-progress-section", "style"),
    Output("update-result-message", "children"),
    Output("update-result-icon", "children"),
    Output("update-commit-details", "children"),
    Output("update-confirm-btn", "style"),
    Output("update-cancel-btn", "style"),
    Output("update-close-btn", "style"),
    Output("update-status-text", "children"),
    Input("update-now-btn", "n_clicks"),
    Input("footer-update-indicator", "n_clicks"),
    Input("update-confirm-btn", "n_clicks"),
    Input("update-cancel-btn", "n_clicks"),
    Input("update-close-btn", "n_clicks"),
    State("update-modal", "is_open"),
    prevent_initial_call=True,
)
def manage_update_workflow(
    toast_clicks: int,
    footer_clicks: int,
    confirm_clicks: int,
    cancel_clicks: int,
    close_clicks: int,
    is_open: bool,
) -> tuple:
    """
    Manage the complete update workflow and modal UI states.

    Flow:
    1. "Update Now" button in toast OR footer indicator → Open modal with pre-flight check
    2. "Update Now" button in modal → Perform git pull
    3. "Cancel"/"Close" button → Close modal

    Returns:
        Tuple of (modal_open, result_section_style, progress_section_style,
                 result_message, result_icon, commit_details,
                 confirm_btn_style, cancel_btn_style, close_btn_style, status_text)
    """
    from dash import ctx

    triggered_id = ctx.triggered_id

    # Ignore if no actual click (prevents toast creation from triggering modal)
    # Check both None and 0 values to prevent spurious triggers
    if not any(
        [toast_clicks, footer_clicks, confirm_clicks, cancel_clicks, close_clicks]
    ):
        logger.debug(
            f"[UPDATE MODAL] Ignoring trigger with no clicks: toast={toast_clicks}, footer={footer_clicks}, confirm={confirm_clicks}, cancel={cancel_clicks}, close={close_clicks}"
        )
        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    # Cancel or close button clicked
    if triggered_id in ("update-cancel-btn", "update-close-btn"):
        return (
            False,  # Close modal
            {"display": "none"},  # Hide result section
            {"display": "none"},  # Hide progress section
            "",  # Clear result message
            "",  # Clear result icon
            "",  # Clear commit details
            {},  # Show confirm button
            {},  # Show cancel button
            {"display": "none"},  # Hide close button
            "",  # Clear status text
        )

    # "Update Now" button (toast) or footer indicator clicked - open modal with pre-flight check
    if triggered_id in ("update-now-btn", "footer-update-indicator"):
        logger.info(
            "Opening update modal from %s, performing pre-flight check", triggered_id
        )

        # Check git status
        status = check_git_status()

        if not status["can_update"]:
            # Show error state immediately
            error_icon = html.I(
                className="bi bi-exclamation-triangle-fill text-warning",
                style={"fontSize": "3rem"},
            )

            return (
                True,  # Open modal
                {},  # Show result section
                {"display": "none"},  # Hide progress section
                [
                    html.Strong("Cannot update:"),
                    html.Br(),
                    status["details"],
                ],
                error_icon,
                "",  # No commit details
                {"display": "none"},  # Hide confirm button
                {"display": "none"},  # Hide cancel button
                {},  # Show close button
                "",  # Clear status text
            )

        # Show ready-to-update state with warning if needed
        ready_icon = html.I(
            className="bi bi-info-circle-fill text-info",
            style={"fontSize": "3rem"},
        )

        warning_note = ""
        if status["has_uncommitted_changes"]:
            warning_note = html.Div(
                [
                    html.Hr(),
                    html.P(
                        [
                            html.I(
                                className="bi bi-exclamation-circle text-warning me-2"
                            ),
                            html.Strong("Note: "),
                            "Your uncommitted changes will be automatically stashed before updating "
                            "and restored afterward.",
                        ],
                        className="text-muted small mb-0",
                    ),
                ],
            )

        return (
            True,  # Open modal
            {},  # Show result section
            {"display": "none"},  # Hide progress section
            [
                html.P("Ready to update your application to the latest version."),
                html.P(
                    "This will pull the latest changes from GitHub and update your local installation.",
                    className="text-muted small",
                ),
                warning_note,
            ],
            ready_icon,
            "",  # No commit details yet
            {},  # Show confirm button
            {},  # Show cancel button
            {"display": "none"},  # Hide close button
            "",  # Clear status text
        )

    # "Update Now" button in modal clicked - perform the update
    if triggered_id == "update-confirm-btn":
        logger.info("Starting application update")

        # Show progress state
        # Note: In a real async scenario, we'd return progress first, then update.
        # For now, we do synchronous update and show result.

        result = perform_update()

        if result["success"]:
            # Success state
            success_icon = html.I(
                className="bi bi-check-circle-fill text-success",
                style={"fontSize": "3rem"},
            )

            commit_details = ""
            if result["pulled_commits"]:
                commit_details = html.Div(
                    [
                        html.Hr(),
                        html.P(
                            html.Strong("What's new:"),
                            className="mb-2",
                        ),
                        html.Pre(
                            result["pulled_commits"],
                            className="bg-light p-3 rounded",
                            style={
                                "fontSize": "0.85rem",
                                "maxHeight": "150px",
                                "overflowY": "auto",
                            },
                        ),
                    ],
                )

            restart_instructions = html.Div(
                [
                    html.Hr(),
                    html.P(
                        [
                            html.I(className="bi bi-arrow-clockwise text-primary me-2"),
                            html.Strong("Next step: "),
                            "Close this app and restart it to use the new version.",
                        ],
                        className="mb-0",
                    ),
                ],
                className="alert alert-info",
            )

            return (
                True,  # Keep modal open
                {},  # Show result section
                {"display": "none"},  # Hide progress section
                [
                    html.P(result["message"], className="text-success mb-0"),
                    restart_instructions,
                ],
                success_icon,
                commit_details,
                {"display": "none"},  # Hide confirm button
                {"display": "none"},  # Hide cancel button
                {},  # Show close button
                "",  # Clear status text
            )
        else:
            # Error state
            error_icon = html.I(
                className="bi bi-x-circle-fill text-danger",
                style={"fontSize": "3rem"},
            )

            return (
                True,  # Keep modal open
                {},  # Show result section
                {"display": "none"},  # Hide progress section
                [
                    html.P(
                        html.Strong("Update failed:"),
                        className="text-danger mb-2",
                    ),
                    html.P(result["message"]),
                    html.Hr(),
                    html.P(
                        [
                            "You can update manually by running: ",
                            html.Code("git pull origin main"),
                        ],
                        className="text-muted small mb-0",
                    ),
                ],
                error_icon,
                "",  # No commit details
                {"display": "none"},  # Hide confirm button
                {"display": "none"},  # Hide cancel button
                {},  # Show close button
                "",  # Clear status text
            )

    # Default: no change (return current state)
    return (
        is_open,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
    )
