"""
Callbacks for application auto-update functionality.

Opens the GitHub releases page when user clicks update buttons.
"""

import logging
import webbrowser
from dash import callback, Input

logger = logging.getLogger(__name__)

GITHUB_RELEASES_URL = "https://github.com/niksavis/burndown-chart/releases/latest"


@callback(
    Input("update-now-btn", "n_clicks"),
    Input("footer-update-indicator", "n_clicks"),
    prevent_initial_call=True,
)
def open_github_releases(toast_clicks: int, footer_clicks: int) -> None:
    """
    Open GitHub releases page when user clicks update button.

    This allows users to download the latest version manually,
    consistent with the initial installation process.

    Args:
        toast_clicks: Number of clicks on toast "Update Now" button
        footer_clicks: Number of clicks on footer update indicator
    """
    from dash import ctx

    triggered_id = ctx.triggered_id

    # Ignore if no actual click
    if not any([toast_clicks, footer_clicks]):
        return

    logger.info(f"Opening GitHub releases page from {triggered_id}")

    try:
        webbrowser.open(GITHUB_RELEASES_URL)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
