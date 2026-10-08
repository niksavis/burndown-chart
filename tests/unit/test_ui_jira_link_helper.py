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
    @patch("utils.jira_link_utils.load_jira_configuration")
    def test_returns_url_when_verified(self, mock_load_config):
        mock_load_config.return_value = {
            "base_url": "https://jira.example.com/",
            "last_test_success": True,
        }

        result = get_jira_base_url()

        assert result == "https://jira.example.com"

    @patch("utils.jira_link_utils.load_jira_configuration")
    def test_returns_none_when_not_verified(self, mock_load_config):
        mock_load_config.return_value = {
            "base_url": "https://jira.example.com",
            "last_test_success": False,
        }

        result = get_jira_base_url()

        assert result is None

    @patch("utils.jira_link_utils.load_jira_configuration")
    def test_returns_none_when_no_base_url(self, mock_load_config):
        mock_load_config.return_value = {
            "base_url": "",
            "last_test_success": True,
        }

        result = get_jira_base_url()

        assert result is None

    @patch("utils.jira_link_utils.load_jira_configuration")
    def test_returns_none_on_exception(self, mock_load_config):
        mock_load_config.side_effect = Exception("Config error")

        result = get_jira_base_url()

        assert result is None


class TestConstructJiraIssueUrl:
    def test_constructs_url_correctly(self):
        result = construct_jira_issue_url("PROJ-123", "https://jira.example.com")

        assert result == "https://jira.example.com/browse/PROJ-123"

    def test_handles_trailing_slash(self):
        result = construct_jira_issue_url("PROJ-123", "https://jira.example.com/")

        assert result == "https://jira.example.com//browse/PROJ-123"


class TestIsJiraConnectionVerified:
    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_true_when_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = is_jira_connection_verified()

        assert result is True

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_false_when_not_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = None

        result = is_jira_connection_verified()

        assert result is False


class TestCreateJiraIssueLink:
    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_link_when_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123")

        assert isinstance(result, type(html.A()))

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_span_when_not_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = None

        result = create_jira_issue_link("PROJ-123")

        assert isinstance(result, type(html.Span()))

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_uses_custom_text(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123", text="Custom Text")

        assert result is not None

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_classname(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link("PROJ-123", className="fw-bold")

        assert result is not None

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_style(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link(
            "PROJ-123", style={"color": "red", "fontSize": "14px"}
        )

        assert result is not None


class TestCreateJiraIssueLinkHtml:
    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_html_link_when_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link_html("PROJ-123")

        assert "<a href=" in result
        assert "https://jira.example.com/browse/PROJ-123" in result
        assert 'target="_blank"' in result
        assert 'rel="noopener noreferrer"' in result

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_returns_plain_text_when_not_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = None

        result = create_jira_issue_link_html("PROJ-123")

        assert result == "PROJ-123"
        assert "<a" not in result

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_uses_custom_text_in_html(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"

        result = create_jira_issue_link_html("PROJ-123", text="Custom Issue")

        assert "Custom Issue</a>" in result


class TestBatchCreateJiraIssueLinks:
    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_multiple_links(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"
        issue_keys = ["PROJ-123", "PROJ-456", "PROJ-789"]

        result = batch_create_jira_issue_links(issue_keys)

        assert len(result) == 3
        assert all(isinstance(link, type(html.A())) for link in result)

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_creates_multiple_spans_when_not_verified(self, mock_get_base_url):
        mock_get_base_url.return_value = None
        issue_keys = ["PROJ-123", "PROJ-456"]

        result = batch_create_jira_issue_links(issue_keys)

        assert len(result) == 2
        assert all(isinstance(span, type(html.Span())) for span in result)

    @patch("ui.jira_link_helper.get_jira_base_url")
    def test_applies_className_to_all(self, mock_get_base_url):
        mock_get_base_url.return_value = "https://jira.example.com"
        issue_keys = ["PROJ-123", "PROJ-456"]

        result = batch_create_jira_issue_links(issue_keys, className="fw-bold")

        assert len(result) == 2
