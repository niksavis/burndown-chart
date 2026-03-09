"""Shared JIRA link helpers for visualization and UI layers."""

from __future__ import annotations

import logging

from dash import html

from data.persistence import load_jira_configuration

logger = logging.getLogger(__name__)


def get_jira_base_url() -> str | None:
    """Get verified JIRA base URL from persisted configuration."""
    try:
        config = load_jira_configuration()

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
    """Construct full JIRA issue URL."""
    return f"{base_url}/browse/{issue_key}"


def is_jira_connection_verified() -> bool:
    """Return True when a verified JIRA connection is available."""
    return get_jira_base_url() is not None


def create_jira_issue_link(
    issue_key: str,
    text: str | None = None,
    className: str | None = None,
    style: dict | None = None,
) -> html.A | html.Span:
    """Create Dash anchor element to a JIRA issue when connection is verified."""
    display_text = text or issue_key
    base_url = get_jira_base_url()

    if not base_url:
        return html.Span(display_text, className=className, style=style)

    issue_url = construct_jira_issue_url(issue_key, base_url)

    return html.A(
        display_text,
        href=issue_url,
        target="_blank",
        rel="noopener noreferrer",
        className=className,
        style=style,
        title=f"Open {issue_key} in JIRA",
    )


def create_jira_issue_link_html(issue_key: str, text: str | None = None) -> str:
    """Create HTML link string to a JIRA issue when connection is verified."""
    display_text = text or issue_key
    base_url = get_jira_base_url()

    if not base_url:
        return display_text

    issue_url = construct_jira_issue_url(issue_key, base_url)

    return (
        f'<a href="{issue_url}" target="_blank"'
        f' rel="noopener noreferrer" title="Open {issue_key} in JIRA">'
        f"{display_text}</a>"
    )


def batch_create_jira_issue_links(
    issue_keys: list[str],
    className: str | None = None,
    style: dict | None = None,
) -> list[html.A | html.Span]:
    """Create links for a list of JIRA issue keys."""
    return [
        create_jira_issue_link(issue_key, className=className, style=style)
        for issue_key in issue_keys
    ]
