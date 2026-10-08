import json
import logging
import os
import time


def test_logging_workflow_end_to_end(temp_log_dir):

    from configuration.logging_config import (
        cleanup_old_logs,
        setup_logging,
        shutdown_logging,
    )

    setup_logging(log_dir=temp_log_dir, log_level="INFO")

    logger_module1 = logging.getLogger("module1")
    logger_module2 = logging.getLogger("module2")
    logger_module3 = logging.getLogger("module3")

    logger_module1.info("Module 1 starting operation")
    logger_module2.info("Module 2 processing data")
    logger_module3.warning("Module 3 low memory warning")

    logger_module1.info("Authorization: Bearer secret_token_12345")
    logger_module2.info('{"api_key": "sk-super-secret", "data": "test"}')

    logger_module1.error("Module 1 encountered an error")
    logger_module2.error("Module 2 failed to connect")

    for handler in logging.getLogger().handlers:
        handler.flush()

    app_log = os.path.join(temp_log_dir, "app.log")
    assert os.path.exists(app_log), "app.log should exist"

    with open(app_log) as f:
        app_log_lines = f.readlines()

    assert len(app_log_lines) >= 7, (
        f"Expected at least 7 log entries, got {len(app_log_lines)}"
    )

    for line in app_log_lines:
        log_entry = json.loads(line.strip())
        assert "timestamp" in log_entry
        assert "level" in log_entry
        assert "module" in log_entry
        assert "message" in log_entry

    app_log_content = "".join(app_log_lines)
    assert "secret_token_12345" not in app_log_content, (
        "Bearer token should be redacted"
    )
    assert "sk-super-secret" not in app_log_content, "API key should be redacted"
    assert "[REDACTED]" in app_log_content, "Redaction markers should be present"

    errors_log = os.path.join(temp_log_dir, "errors.log")
    assert os.path.exists(errors_log), "errors.log should exist"

    with open(errors_log) as f:
        error_log_lines = f.readlines()

    assert len(error_log_lines) == 2, (
        f"Expected 2 error entries, got {len(error_log_lines)}"
    )

    for line in error_log_lines:
        log_entry = json.loads(line.strip())
        assert log_entry["level"] == "ERROR", (
            "errors.log should only contain ERROR level logs"
        )

    shutdown_logging()

    _ = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=0)


def test_log_rotation_under_load(temp_log_dir):

    from configuration.logging_config import setup_logging, shutdown_logging

    max_bytes = 2048
    backup_count = 3
    setup_logging(log_dir=temp_log_dir, max_bytes=max_bytes, backup_count=backup_count)

    logger = logging.getLogger("load_test")

    message_count = 50
    for i in range(message_count):
        logger.info(f"Load test message {i:03d} with padding to increase size " * 5)

    for handler in logging.getLogger().handlers:
        handler.flush()

    time.sleep(0.2)

    app_log = os.path.join(temp_log_dir, "app.log")
    assert os.path.exists(app_log), "app.log should exist"

    app_log_1 = os.path.join(temp_log_dir, "app.log.1")

    assert os.path.exists(app_log_1), (
        "At least one rotation should have occurred (app.log.1 should exist)"
    )

    log_files = [app_log]
    for i in range(1, backup_count + 1):
        backup_file = os.path.join(temp_log_dir, f"app.log.{i}")
        if os.path.exists(backup_file):
            log_files.append(backup_file)

    total_entries = 0
    for log_file in log_files:
        with open(log_file) as f:
            for line in f:
                if line.strip():
                    log_entry = json.loads(line.strip())
                    assert "message" in log_entry
                    total_entries += 1

    assert total_entries >= 10, (
        f"Expected at least 10 log entries, found {total_entries}"
    )
    assert len(log_files) >= 2, (
        f"Expected at least 2 log files (rotation occurred), found {len(log_files)}"
    )

    shutdown_logging()


def test_multiple_handlers_write_correctly(temp_log_dir):

    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir, log_level="INFO")

    logger = logging.getLogger("multi_handler_test")

    logger.debug("Debug message - should not appear (below INFO threshold)")
    logger.info("Info message - should appear in app.log only")
    logger.warning("Warning message - should appear in app.log only")
    logger.error("Error message - should appear in both app.log and errors.log")
    logger.critical("Critical message - should appear in both app.log and errors.log")

    logger.info("API key: sk-test-12345")
    logger.error('{"password": "admin123", "username": "admin"}')

    for handler in logging.getLogger().handlers:
        handler.flush()

    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        app_log_lines = [line for line in f if line.strip()]

    assert len(app_log_lines) == 6, (
        "app.log should have 6 entries "
        "(INFO, WARNING, ERROR, CRITICAL, + 2 sensitive), "
        f"got {len(app_log_lines)}"
    )

    errors_log = os.path.join(temp_log_dir, "errors.log")
    with open(errors_log) as f:
        error_log_lines = [line for line in f if line.strip()]

    assert len(error_log_lines) == 3, (
        "errors.log should have 3 entries "
        "(ERROR, CRITICAL, + 1 sensitive ERROR), "
        f"got {len(error_log_lines)}"
    )

    app_log_content = "".join(app_log_lines)
    error_log_content = "".join(error_log_lines)

    assert "Error message" in app_log_content
    assert "Critical message" in app_log_content
    assert "Error message" in error_log_content
    assert "Critical message" in error_log_content

    assert "Info message" not in error_log_content
    assert "Warning message" not in error_log_content

    assert "sk-test-12345" not in app_log_content
    assert "sk-test-12345" not in error_log_content
    assert "admin123" not in app_log_content
    assert "admin123" not in error_log_content
    assert "[REDACTED]" in app_log_content
    assert "[REDACTED]" in error_log_content

    shutdown_logging()
