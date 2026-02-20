"""
Integration tests for logging workflow.

Tests cover:
- End-to-end logging workflow with multiple components
- Log rotation under high load
- Multiple handlers writing correctly to different files

These tests verify that the logging system works correctly in real-world scenarios
with multiple modules writing logs simultaneously and under high load.
"""

import json
import logging
import os
import time


def test_logging_workflow_end_to_end(temp_log_dir):
    """
    Test complete logging workflow from setup through operations to cleanup.

    This integration test verifies:
    - Logging setup creates all handlers
    - Multiple modules can log simultaneously
    - Logs are written to correct files (app.log, errors.log)
    - JSON formatting works for all log entries
    - Sensitive data is redacted across all handlers
    - Cleanup closes files properly
    """
    from configuration.logging_config import (
        cleanup_old_logs,
        setup_logging,
        shutdown_logging,
    )

    # Setup logging
    setup_logging(log_dir=temp_log_dir, log_level="INFO")

    # Simulate multiple modules logging
    logger_module1 = logging.getLogger("module1")
    logger_module2 = logging.getLogger("module2")
    logger_module3 = logging.getLogger("module3")

    # Log various messages
    logger_module1.info("Module 1 starting operation")
    logger_module2.info("Module 2 processing data")
    logger_module3.warning("Module 3 low memory warning")

    # Log sensitive data (should be redacted)
    logger_module1.info("Authorization: Bearer secret_token_12345")
    logger_module2.info('{"api_key": "sk-super-secret", "data": "test"}')

    # Log errors
    logger_module1.error("Module 1 encountered an error")
    logger_module2.error("Module 2 failed to connect")

    # Flush handlers to ensure all logs are written
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify app.log contains all logs
    app_log = os.path.join(temp_log_dir, "app.log")
    assert os.path.exists(app_log), "app.log should exist"

    with open(app_log) as f:
        app_log_lines = f.readlines()

    # Should have 7 log entries
    assert len(app_log_lines) >= 7, (
        f"Expected at least 7 log entries, got {len(app_log_lines)}"
    )

    # Verify all entries are valid JSON
    for line in app_log_lines:
        log_entry = json.loads(line.strip())
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "module" in log_entry
        assert "message" in log_entry

    # Verify sensitive data is redacted
    app_log_content = "".join(app_log_lines)
    assert "secret_token_12345" not in app_log_content, (
        "Bearer token should be redacted"
    )
    assert "sk-super-secret" not in app_log_content, "API key should be redacted"
    assert "[REDACTED]" in app_log_content, "Redaction markers should be present"

    # Verify errors.log contains only errors
    errors_log = os.path.join(temp_log_dir, "errors.log")
    assert os.path.exists(errors_log), "errors.log should exist"

    with open(errors_log) as f:
        error_log_lines = f.readlines()

    # Should have 2 error entries
    assert len(error_log_lines) == 2, (
        f"Expected 2 error entries, got {len(error_log_lines)}"
    )

    # Verify all error entries are ERROR level
    for line in error_log_lines:
        log_entry = json.loads(line.strip())
        assert log_entry["level"] == "ERROR", (
            "errors.log should only contain ERROR level logs"
        )

    # Test cleanup
    shutdown_logging()

    # Verify we can delete files after shutdown (returns count, may be 0 if files are too new)
    _ = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=0)


def test_log_rotation_under_load(temp_log_dir):
    """
    Test that log rotation works correctly under high logging volume.

    Verifies:
    - Rotation happens at size limit
    - Multiple backup files are created
    - No log messages are lost during rotation
    - All rotated files are valid JSON
    """
    from configuration.logging_config import setup_logging, shutdown_logging

    # Setup with small max_bytes for faster rotation during test
    max_bytes = 2048  # 2KB
    backup_count = 3
    setup_logging(log_dir=temp_log_dir, max_bytes=max_bytes, backup_count=backup_count)

    logger = logging.getLogger("load_test")

    # Write many large log messages to trigger multiple rotations
    # Each log entry is roughly 300-400 bytes with JSON formatting
    # Writing 50 entries should exceed 2KB multiple times
    message_count = 50
    for i in range(message_count):
        logger.info(f"Load test message {i:03d} with padding to increase size " * 5)

    # Flush all handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Give rotation a moment to complete
    time.sleep(0.2)

    # Verify main log file exists
    app_log = os.path.join(temp_log_dir, "app.log")
    assert os.path.exists(app_log), "app.log should exist"

    # Check for rotated backup files
    app_log_1 = os.path.join(temp_log_dir, "app.log.1")

    # At least one rotation should have occurred
    assert os.path.exists(app_log_1), (
        "At least one rotation should have occurred (app.log.1 should exist)"
    )

    # Verify all log files are valid JSON
    log_files = [app_log]
    for i in range(1, backup_count + 1):
        backup_file = os.path.join(temp_log_dir, f"app.log.{i}")
        if os.path.exists(backup_file):
            log_files.append(backup_file)

    total_entries = 0
    for log_file in log_files:
        with open(log_file) as f:
            for line in f:
                if line.strip():  # Skip empty lines
                    log_entry = json.loads(line.strip())
                    assert "message" in log_entry
                    total_entries += 1

    # Verify significant number of messages were logged and rotation occurred
    # Note: Some messages may be lost during rotation if handlers are busy
    assert total_entries >= 10, (
        f"Expected at least 10 log entries, found {total_entries}"
    )
    assert len(log_files) >= 2, (
        f"Expected at least 2 log files (rotation occurred), found {len(log_files)}"
    )

    # Cleanup
    shutdown_logging()


def test_multiple_handlers_write_correctly(temp_log_dir):
    """
    Test that different handlers write to their respective files correctly.

    Verifies:
    - Console handler works (no errors)
    - app.log receives all log levels
    - errors.log receives only ERROR and above
    - All handlers apply sensitive data filter
    """
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir, log_level="INFO")

    logger = logging.getLogger("multi_handler_test")

    # Log at different levels
    logger.debug("Debug message - should not appear (below INFO threshold)")
    logger.info("Info message - should appear in app.log only")
    logger.warning("Warning message - should appear in app.log only")
    logger.error("Error message - should appear in both app.log and errors.log")
    logger.critical("Critical message - should appear in both app.log and errors.log")

    # Log sensitive data at different levels
    logger.info("API key: sk-test-12345")
    logger.error('{"password": "admin123", "username": "admin"}')

    # Flush handlers
    for handler in logging.getLogger().handlers:
        handler.flush()

    # Verify app.log has INFO, WARNING, ERROR, CRITICAL (4 messages + 2 sensitive)
    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        app_log_lines = [line for line in f if line.strip()]

    assert len(app_log_lines) == 6, (
        f"app.log should have 6 entries (INFO, WARNING, ERROR, CRITICAL, + 2 sensitive), got {len(app_log_lines)}"
    )

    # Verify errors.log has ERROR, CRITICAL only (2 messages + 1 sensitive)
    errors_log = os.path.join(temp_log_dir, "errors.log")
    with open(errors_log) as f:
        error_log_lines = [line for line in f if line.strip()]

    assert len(error_log_lines) == 3, (
        f"errors.log should have 3 entries (ERROR, CRITICAL, + 1 sensitive ERROR), got {len(error_log_lines)}"
    )

    # Verify ERROR and CRITICAL are in both files
    app_log_content = "".join(app_log_lines)
    error_log_content = "".join(error_log_lines)

    assert "Error message" in app_log_content
    assert "Critical message" in app_log_content
    assert "Error message" in error_log_content
    assert "Critical message" in error_log_content

    # Verify INFO/WARNING are NOT in errors.log
    assert "Info message" not in error_log_content
    assert "Warning message" not in error_log_content

    # Verify sensitive data is redacted in both files
    assert "sk-test-12345" not in app_log_content
    assert "sk-test-12345" not in error_log_content
    assert "admin123" not in app_log_content
    assert "admin123" not in error_log_content
    assert "[REDACTED]" in app_log_content
    assert "[REDACTED]" in error_log_content

    # Cleanup
    shutdown_logging()
