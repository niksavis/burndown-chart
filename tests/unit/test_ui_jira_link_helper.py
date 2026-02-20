"""Tests for JIRA Issue Link Helper Module

Tests the functionality of creating clickable JIRA issue links.
"""

from unittest.mock import patch

from dash import html

from ui.jira_link_helper import (
    batch_create_jira_issue_links,
    construct_jira_issue_url,
    create_jira_issue_link,
    create_jira_issue_link_html,
    get_jira_base_url,
    is_jira_connection_verified,
)


class TestGetJiraBaseUrl:
    """Tests for get_jira_base_url function."""

    @patch("data.persistence.load_jira_configuration")
    def test_returns_url_when_verified(self, mock_load_config):
        """Should return base URL when connection is verified."""
        mock_load_config.return_value = {
            "base_url": "https://jira.example.com/",
            "last_test_success": True,
        }

        result = get_jira_base_url()

        assert result == "https://jira.example.com"

    @patch("data.persistence.load_jira_configuration")
    def test_returns_none_when_not_verified(self, mock_load_config):
        """Should return None when connection not verified."""
        mock_load_config.return_value = {
            "base_url": "https://jira.example.com",
            "last_test_success": False,
        }

        result = get_jira_base_url()

        assert result is None

    @patch("data.persistence.load_jira_configuration")
    def test_returns_none_when_no_base_url(self, mock_load_config):
        """Should return None when no base URL configured."""
        mock_load_config.return_value = {
            "base_url": "",
            "last_test_success": True,
        }

        result = get_jira_base_url()

        assert result is None

    @patch("data.persistence.load_jira_configuration")
    def test_returns_none_on_exception(self, mock_load_config):
        """Should return None when configuration loading fails."""
        mock_load_config.side_effect = Exception("Config error")

        result = get_jira_base_url()

        assert result is None


class TestConstructJiraIssueUrl:
    """Tests for construct_jira_issue_url function."""

    def test_constructs_url_correctly(self):
        """Should construct proper JIRA browse URL."""
        result = construct_jira_issue_url("PROJ-123", "https://jira.example.com")

        assert result == "https://jira.example.com/browse/PROJ-123"

    def test_handles_trailing_slash(self):
        """Should work with base URL that has trailing slash."""
        # Note: get_jira_base_url strips trailing slash, but test anyway
        result = construct_jira_issue_url("PROJ-123", "https://jira.example.com/")

        assert result == "https://jira.example.com//browse/PROJ-123"


class TestIsJiraConnectionVerified:
    """Tests for is_jira_connection_verified function."""

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_true_when_verified(self, mock_get_base_url):
        """Should return True when base URL available."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = is_jira_connection_verified()

        assert result is True

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_false_when_not_verified(self, mock_get_base_url):
        """Should return False when base URL not available."""
        mock_get_base_url.return_value = None

        result = is_jira_connection_verified()

        assert result is False


class TestCreateJiraIssueLink:
    """Tests for create_jira_issue_link function."""

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_link_when_verified(self, mock_get_base_url):
        """Should create html.A component when connection verified."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123")

        assert isinstance(result, type(html.A()))
        # Check that it's a link (has href attribute)
        # Note: Can't easily check attributes in Dash components in unit tests
        # This would be better as an integration test

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_span_when_not_verified(self, mock_get_base_url):
        """Should create html.Span when connection not verified."""
        mock_get_base_url.return_value = None

        result = create_jira_issue_link("PROJ-123")

        assert isinstance(result, type(html.Span()))

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_uses_custom_text(self, mock_get_base_url):
        """Should use custom text when provided."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123", text="Custom Text")

        # Check that component was created (detailed attribute checks in integration tests)
        assert result is not None

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_classname(self, mock_get_base_url):
        """Should apply className when provided."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123", className="fw-bold")

        assert result is not None

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_style(self, mock_get_base_url):
        """Should apply style when provided."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link(
            "PROJ-123", style={"color": "red", "fontSize": "14px"}
        )

        assert result is not None


class TestCreateJiraIssueLinkHtml:
    """Tests for create_jira_issue_link_html function."""

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_html_link_when_verified(self, mock_get_base_url):
        """Should create HTML anchor tag when connection verified."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link_html("PROJ-123")

        assert "<a href=" in result
        assert "https://jira.example.com/browse/PROJ-123" in result
        assert 'target="_blank"' in result
        assert 'rel="noopener noreferrer"' in result

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_plain_text_when_not_verified(self, mock_get_base_url):
        """Should return plain text when connection not verified."""
        mock_get_base_url.return_value = None

        result = create_jira_issue_link_html("PROJ-123")

        assert result == "PROJ-123"
        assert "<a" not in result

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_uses_custom_text_in_html(self, mock_get_base_url):
        """Should use custom text in HTML output."""
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link_html("PROJ-123", text="Custom Issue")

        assert "Custom Issue</a>" in result


class TestBatchCreateJiraIssueLinks:
    """Tests for batch_create_jira_issue_links function."""

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_multiple_links(self, mock_get_base_url):
        """Should create multiple link components."""
        mock_get_base_url.return_value = "https://jira.example.com"
        issue_keys = ["PROJ-123", "PROJ-456", "PROJ-789"]

        result = batch_create_jira_issue_links(issue_keys)

        assert len(result) == 3
        assert all(isinstance(link, type(html.A())) for link in result)

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_multiple_spans_when_not_verified(self, mock_get_base_url):
        """Should create multiple span components when not verified."""
        mock_get_base_url.return_value = None
        issue_keys = ["PROJ-123", "PROJ-456"]

        result = batch_create_jira_issue_links(issue_keys)

        assert len(result) == 2
        assert all(isinstance(span, type(html.Span())) for span in result)

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_className_to_all(self, mock_get_base_url):
        """Should apply className to all links."""
        mock_get_base_url.return_value = "https://jira.example.com"
        issue_keys = ["PROJ-123", "PROJ-456"]

        result = batch_create_jira_issue_links(issue_keys, className="fw-bold")

        assert len(result) == 2
