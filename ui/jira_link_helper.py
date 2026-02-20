"""JIRA Issue Link Helper Module

This module provides functions to create clickable links to JIRA issues.
Links are only generated when a verified JIRA connection exists.

Usage:
    from ui.jira_link_helper import create_jira_issue_link, create_jira_issue_link_html

    # Create Dash html.A component
    link = create_jira_issue_link("PROJ-123", "Fix login bug")

    # Create HTML string
    html_link = create_jira_issue_link_html("PROJ-456", "Task summary")
"""

import logging

from dash import html

logger = logging.getLogger(__name__)


def get_jira_base_url() -> str | None:
    """Get JIRA base URL from configuration if connection is verified.

    Returns:
        Base URL string (e.g., "https://jira.example.com") if verified, None otherwise
    """
    try:
        from data.persistence import load_jira_configuration

        config = load_jira_configuration()

        # Only return URL if connection was successfully tested
        if not config.get("last_test_success"):
            logger.debug("JIRA connection not verified, links disabled")
            return None

        base_url = config.get("base_url", "").rstrip("/")

        if not base_url:
            return None

        return base_url

    except Exception as e:
        logger.warning(f"Failed to load JIRA configuration: {e}")
        return None


def construct_jira_issue_url(issue_key: str, base_url: str) -> str:
    """Construct full JIRA issue URL.

    Args:
        issue_key: JIRA issue key (e.g., "PROJ-123")
        base_url: JIRA base URL (e.g., "https://jira.example.com")

    Returns:
        Full issue URL (e.g., "https://jira.example.com/browse/PROJ-123")
    """
    return f"{base_url}/browse/{issue_key}"


def is_jira_connection_verified() -> bool:
    """Check if JIRA connection has been successfully verified.

    Returns:
        True if connection verified, False otherwise
    """
    return get_jira_base_url() is not None


def create_jira_issue_link(
    issue_key: str,
    text: str | None = None,
    className: str | None = None,
    style: dict | None = None,
) -> html.A | html.Span:
    """Create Dash html.A component linking to JIRA issue.

    If JIRA connection is not verified, returns plain text instead of link.

    Args:
        issue_key: JIRA issue key (e.g., "PROJ-123")
        text: Link text (defaults to issue_key if not provided)
        className: CSS class name for link styling
        style: Inline style dict for link

    Returns:
        Dash html.A component if connection verified, html.Span otherwise

    Example:
        >>> link = create_jira_issue_link("PROJ-123", className="fw-bold")
        >>> # Returns: <a href="https://jira.example.com/browse/PROJ-123" target="_blank">PROJ-123</a>
    """
    display_text = text or issue_key

    # Check if JIRA connection is verified
    base_url = get_jira_base_url()

    if not base_url:
        # Return plain text if connection not verified
        return html.Span(display_text, className=className, style=style)

    # Construct issue URL
    issue_url = construct_jira_issue_url(issue_key, base_url)

    # Create link with target="_blank" to open in new tab
    return html.A(
        display_text,
        href=issue_url,
        target="_blank",
        rel="noopener noreferrer",  # Security best practice
        className=className,
        style=style,
        title=f"Open {issue_key} in JIRA",
    )


def create_jira_issue_link_html(issue_key: str, text: str | None = None) -> str:
    """Create HTML string for JIRA issue link.

    If JIRA connection is not verified, returns plain text.

    Args:
        issue_key: JIRA issue key (e.g., "PROJ-123")
        text: Link text (defaults to issue_key if not provided)

    Returns:
        HTML string with anchor tag if verified, plain text otherwise

    Example:
        >>> html = create_jira_issue_link_html("PROJ-123")
        >>> # Returns: '<a href="https://jira.example.com/browse/PROJ-123" target="_blank">PROJ-123</a>'
    """
    display_text = text or issue_key

    # Check if JIRA connection is verified
    base_url = get_jira_base_url()

    if not base_url:
        # Return plain text if connection not verified
        return display_text

    # Construct issue URL
    issue_url = construct_jira_issue_url(issue_key, base_url)

    # Return HTML anchor tag
    return f'<a href="{issue_url}" target="_blank" rel="noopener noreferrer" title="Open {issue_key} in JIRA">{display_text}</a>'


def batch_create_jira_issue_links(
    issue_keys: list[str], className: str | None = None, style: dict | None = None
) -> list[html.A | html.Span]:
    """Create multiple JIRA issue links at once.

    Useful for rendering lists of issues efficiently.

    Args:
        issue_keys: List of JIRA issue keys
        className: CSS class name for link styling
        style: Inline style dict for links

    Returns:
        List of Dash html.A or html.Span components

    Example:
        >>> links = batch_create_jira_issue_links(["PROJ-123", "PROJ-456"])
    """
    return [
        create_jira_issue_link(issue_key, className=className, style=style)
        for issue_key in issue_keys
    ]
