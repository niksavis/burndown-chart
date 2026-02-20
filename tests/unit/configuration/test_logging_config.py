"""
Unit tests for logging configuration module.

Tests cover:
- Log directory creation
- Log file creation (app.log, errors.log)
- Rotating file handler rotation
- JSON formatter output
- Sensitive data filter redaction (tokens, passwords, API keys)
- Old log cleanup functionality

All tests use temporary directories for isolation (no project root pollution).
"""

import json
import logging
import os
import time
from typing import cast


def test_setup_logging_creates_log_directory(temp_log_dir):
    """Test that setup_logging creates log directory if it doesn't exist."""
    from configuration.logging_config import setup_logging, shutdown_logging

    # Log directory should not exist yet
    log_dir = os.path.join(temp_log_dir, "test_logs")
    assert not os.path.exists(log_dir)

    # Setup logging should create it
    setup_logging(log_dir=log_dir)

    # Verify directory was created
    assert os.path.exists(log_dir)
    assert os.path.isdir(log_dir)

    # Close all log file handles before teardown
    shutdown_logging()


def test_setup_logging_creates_log_files(temp_log_dir):
    """Test that setup_logging creates app.log and errors.log files."""
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    # Log something to trigger file creation
    logger = logging.getLogger("test")
    logger.info("Test message")
    logger.error("Test error")

    # Verify log files were created
    app_log = os.path.join(temp_log_dir, "app.log")
    errors_log = os.path.join(temp_log_dir, "errors.log")

    assert os.path.exists(app_log), "app.log should be created"
    assert os.path.exists(errors_log), "errors.log should be created"

    # Close all log file handles before teardown
    shutdown_logging()


def test_rotating_file_handler_rotation(temp_log_dir):
    """Test that log files rotate when they exceed max size."""
    from configuration.logging_config import setup_logging, shutdown_logging

    # Set small max_bytes for testing
    max_bytes = 1024  # 1KB
    setup_logging(log_dir=temp_log_dir, max_bytes=max_bytes, backup_count=3)

    logger = logging.getLogger("test_rotation")

    # Write enough data to trigger rotation
    # Each log line is roughly 200 bytes, so 10 lines should exceed 1KB
    for i in range(20):
        logger.info(f"Test message {i} with some extra padding to increase size" * 5)

    # Check if rotation occurred (.log.1 backup file should exist)
    app_log_backup = os.path.join(temp_log_dir, "app.log.1")

    # Note: Rotation may not happen immediately, give it a moment
    time.sleep(0.1)

    # Verify rotation happened (backup file exists)
    assert os.path.exists(app_log_backup), (
        "Backup file should be created after rotation"
    )

    # Close all log file handles before teardown
    shutdown_logging()


def test_json_formatter_output(temp_log_dir):
    """Test that log entries are formatted as JSON."""
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_json")
    test_message = "Test JSON formatting"
    logger.info(test_message)

    # Read the log file
    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read().strip()

    # Verify it's valid JSON
    log_entry = json.loads(log_content)

    # Verify expected fields exist
    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert "module" in log_entry
    assert "message" in log_entry

    # Verify values
    assert log_entry["level"] == "INFO"
    assert test_message in log_entry["message"]

    # Close all log file handles before teardown
    shutdown_logging()


def test_sensitive_data_filter_redacts_tokens(temp_log_dir):
    """Test that Bearer tokens are automatically redacted."""
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_token")
    sensitive_message = "Authorization: Bearer abc123def456"
    logger.info(sensitive_message)

    # Read the log file
    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    # Verify token is redacted
    assert "abc123def456" not in log_content, "Token should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    # Close all log file handles before teardown
    shutdown_logging()


def test_sensitive_data_filter_redacts_passwords(temp_log_dir):
    """Test that passwords in JSON are automatically redacted."""
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_password")
    sensitive_message = '{"username": "admin", "password": "secret123"}'
    logger.info(sensitive_message)

    # Read the log file
    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    # Verify password is redacted
    assert "secret123" not in log_content, "Password should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    # Close all log file handles before teardown
    shutdown_logging()


def test_sensitive_data_filter_redacts_api_keys(temp_log_dir):
    """Test that API keys are automatically redacted."""
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_api_key")
    sensitive_message = '{"api_key": "sk-1234567890abcdef", "data": "test"}'
    logger.info(sensitive_message)

    # Read the log file
    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    # Verify API key is redacted
    assert "sk-1234567890abcdef" not in log_content, "API key should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    # Close all log file handles before teardown
    shutdown_logging()


def test_cleanup_old_logs_deletes_old_files(temp_log_dir):
    """Test that cleanup_old_logs deletes files older than max_age_days."""
    from configuration.logging_config import cleanup_old_logs

    # Create an old log file
    old_log = os.path.join(temp_log_dir, "old.log")
    with open(old_log, "w") as f:
        f.write("old log content")

    # Modify file timestamp to be 35 days old
    old_time = time.time() - (35 * 24 * 60 * 60)  # 35 days ago
    os.utime(old_log, (old_time, old_time))

    # Create a recent log file
    recent_log = os.path.join(temp_log_dir, "recent.log")
    with open(recent_log, "w") as f:
        f.write("recent log content")

    # Run cleanup with 30-day threshold
    deleted_count = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=30)

    # Verify old file was deleted
    assert not os.path.exists(old_log), "Old log file should be deleted"
    assert deleted_count == 1, "Should report 1 file deleted"


def test_cleanup_old_logs_preserves_recent_files(temp_log_dir):
    """Test that cleanup_old_logs preserves files newer than max_age_days."""
    from configuration.logging_config import cleanup_old_logs

    # Create a recent log file
    recent_log = os.path.join(temp_log_dir, "recent.log")
    with open(recent_log, "w") as f:
        f.write("recent log content")

    # Run cleanup with 30-day threshold
    deleted_count = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=30)

    # Verify recent file was NOT deleted
    assert os.path.exists(recent_log), "Recent log file should be preserved"
    assert deleted_count == 0, "Should report 0 files deleted"


def test_sensitive_data_filter_preserves_numeric_types(temp_log_dir):
    """Test that numeric argument types are preserved after filtering.

    This prevents TypeError when using %d format strings with numeric arguments,
    like waitress's 'Task queue depth is %d' message.
    """
    from configuration.logging_config import SensitiveDataFilter

    # Create a filter instance
    filter_instance = SensitiveDataFilter()

    # Create a mock LogRecord with numeric args (similar to waitress)
    record = logging.LogRecord(
        name="waitress.queue",
        level=logging.WARNING,
        pathname="task.py",
        lineno=113,
        msg="Task queue depth is %d",
        args=(2,),  # Integer argument
        exc_info=None,
    )

    # Apply filter
    result = filter_instance.filter(record)

    # Filter should return True (don't suppress the record)
    assert result is True

    # Args should still contain integer, not string
    assert record.args is not None
    args_tuple = cast(tuple[int], record.args)
    assert args_tuple == (2,), f"Expected (2,), got {args_tuple}"
    assert isinstance(args_tuple[0], int), f"Expected int, got {type(args_tuple[0])}"

    # getMessage should work without TypeError
    message = record.getMessage()
    assert message == "Task queue depth is 2"


def test_sensitive_data_filter_converts_to_string_when_redacting():
    """Test that args are converted to string only when redaction occurs."""
    from configuration.logging_config import SensitiveDataFilter

    filter_instance = SensitiveDataFilter()

    # Create a record with a sensitive value in args
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="API key: %s",
        args=('{"api_key": "sk-secret123"}',),
        exc_info=None,
    )

    filter_instance.filter(record)

    # Args should be redacted and converted to string
    assert record.args is not None
    args_tuple = cast(tuple[str], record.args)
    assert "[REDACTED]" in str(args_tuple[0])
    assert "sk-secret123" not in str(args_tuple[0])
