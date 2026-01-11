"""
Tests for SensitiveDataFilter to ensure customer data and credentials are protected.
"""

import logging
from configuration.logging_config import SensitiveDataFilter


class TestSensitiveDataFilter:
    """Test sensitive data redaction in logs."""

    def setup_method(self):
        """Set up test logger with sensitive data filter."""
        self.filter = SensitiveDataFilter()
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)

    def test_redact_bearer_tokens(self):
        """Test that Bearer tokens are redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        # Authorization header with Bearer token gets matched by the combined pattern
        # which preserves the "Authorization: Bearer" prefix
        assert "Authorization: Bearer [REDACTED]" in record.msg
        assert "eyJhbG" not in record.msg

    def test_redact_api_tokens(self):
        """Test that API tokens in JSON are redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Config: {"token": "sk-test-12345abcdef", "url": "https://api.com"}',
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert '"token": "[REDACTED]"' in record.msg
        assert "sk-test-12345" not in record.msg

    def test_redact_passwords(self):
        """Test that passwords in JSON are redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Login: {"username": "admin", "password": "secretPass123!"}',
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert '"password": "[REDACTED]"' in record.msg
        assert "secretPass123" not in record.msg

    def test_preserve_production_urls(self):
        """Test that production URLs are NOT redacted (intentionally kept for debugging)."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Connected to JIRA: https://jira.realcompany.com/rest/api/2/search",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        # URLs are NOT redacted - kept for debugging purposes
        assert "jira.realcompany.com" in record.msg

    def test_preserve_localhost_urls(self):
        """Test that localhost URLs are NOT redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Local server: http://localhost:8050/api/test",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert "localhost:8050" in record.msg

    def test_preserve_example_com_urls(self):
        """Test that example.com URLs are NOT redacted (already safe)."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Example: https://jira.example.com/browse/PROJ-123",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert "jira.example.com" in record.msg

    def test_redact_email_addresses(self):
        """Test that email addresses are partially redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User john.doe@company.com completed task",
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert "***@company.com" in record.msg
        assert "john.doe" not in record.msg

    def test_redact_multiple_patterns(self):
        """Test that multiple sensitive patterns in one message are all redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=(
                'JIRA login: {"url": "https://jira.customer.com", '
                '"token": "abc123", "user": "admin@customer.com"}'
            ),
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        # Check redactions happened (but NOT URLs - kept for debugging)
        assert '"token": "[REDACTED]"' in record.msg  # Token redacted
        assert "***@customer.com" in record.msg  # Email redacted
        assert "jira.customer.com" in record.msg  # URL NOT redacted
        # Ensure no user credentials leaked
        assert "abc123" not in record.msg
        assert "admin@" not in record.msg

    def test_redact_in_args(self):
        """Test that sensitive data in log args is also redacted."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="API call failed: %s",
            args=("https://api.customer.com/users with token abc123",),
            exc_info=None,
        )
        self.filter.filter(record)
        # Check args were redacted (args is a tuple)
        assert record.args is not None and len(record.args) > 0
        redacted_arg = str(list(record.args)[0])
        # URLs are NOT redacted - kept for debugging
        assert "api.customer.com" in redacted_arg
        # Token should be redacted
        assert "[REDACTED]" in redacted_arg
        assert "abc123" not in redacted_arg

    def test_case_insensitive_redaction(self):
        """Test that redaction works regardless of case."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg='Config: {"TOKEN": "secret123", "Password": "pass456"}',
            args=(),
            exc_info=None,
        )
        self.filter.filter(record)
        assert "[REDACTED]" in record.msg
        assert "secret123" not in record.msg
        assert "pass456" not in record.msg
