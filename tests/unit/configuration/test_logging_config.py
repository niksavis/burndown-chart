import json
import logging
import os
import time
from typing import cast


def test_setup_logging_creates_log_directory(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    log_dir = os.path.join(temp_log_dir, "test_logs")
    assert not os.path.exists(log_dir)

    setup_logging(log_dir=log_dir)

    assert os.path.exists(log_dir)
    assert os.path.isdir(log_dir)

    shutdown_logging()


def test_setup_logging_creates_log_files(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test")
    logger.info("Test message")
    logger.error("Test error")

    app_log = os.path.join(temp_log_dir, "app.log")
    errors_log = os.path.join(temp_log_dir, "errors.log")

    assert os.path.exists(app_log), "app.log should be created"
    assert os.path.exists(errors_log), "errors.log should be created"

    shutdown_logging()


def test_rotating_file_handler_rotation(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    max_bytes = 1024
    setup_logging(log_dir=temp_log_dir, max_bytes=max_bytes, backup_count=3)

    logger = logging.getLogger("test_rotation")

    for i in range(20):
        logger.info(f"Test message {i} with some extra padding to increase size" * 5)

    app_log_backup = os.path.join(temp_log_dir, "app.log.1")

    time.sleep(0.1)

    assert os.path.exists(app_log_backup), (
        "Backup file should be created after rotation"
    )

    shutdown_logging()


def test_json_formatter_output(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_json")
    test_message = "Test JSON formatting"
    logger.info(test_message)

    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read().strip()

    log_entry = json.loads(log_content)

    assert "timestamp" in log_entry
    assert "level" in log_entry
    assert "module" in log_entry
    assert "message" in log_entry

    assert log_entry["level"] == "INFO"
    assert test_message in log_entry["message"]

    shutdown_logging()


def test_sensitive_data_filter_redacts_tokens(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_token")
    sensitive_message = "Authorization: Bearer abc123def456"
    logger.info(sensitive_message)

    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    assert "abc123def456" not in log_content, "Token should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    shutdown_logging()


def test_sensitive_data_filter_redacts_passwords(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_password")
    sensitive_message = '{"username": "admin", "password": "secret123"}'
    logger.info(sensitive_message)

    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    assert "secret123" not in log_content, "Password should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    shutdown_logging()


def test_sensitive_data_filter_redacts_api_keys(temp_log_dir):
    from configuration.logging_config import setup_logging, shutdown_logging

    setup_logging(log_dir=temp_log_dir)

    logger = logging.getLogger("test_redact_api_key")
    sensitive_message = '{"api_key": "sk-1234567890abcdef", "data": "test"}'
    logger.info(sensitive_message)

    app_log = os.path.join(temp_log_dir, "app.log")
    with open(app_log) as f:
        log_content = f.read()

    assert "sk-1234567890abcdef" not in log_content, "API key should be redacted"
    assert "[REDACTED]" in log_content, "Should contain redaction marker"

    shutdown_logging()


def test_cleanup_old_logs_deletes_old_files(temp_log_dir):
    from configuration.logging_config import cleanup_old_logs

    old_log = os.path.join(temp_log_dir, "old.log")
    with open(old_log, "w") as f:
        f.write("old log content")

    old_time = time.time() - (35 * 24 * 60 * 60)
    os.utime(old_log, (old_time, old_time))

    recent_log = os.path.join(temp_log_dir, "recent.log")
    with open(recent_log, "w") as f:
        f.write("recent log content")

    deleted_count = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=30)

    assert not os.path.exists(old_log), "Old log file should be deleted"
    assert deleted_count == 1, "Should report 1 file deleted"


def test_cleanup_old_logs_preserves_recent_files(temp_log_dir):
    from configuration.logging_config import cleanup_old_logs

    recent_log = os.path.join(temp_log_dir, "recent.log")
    with open(recent_log, "w") as f:
        f.write("recent log content")

    deleted_count = cleanup_old_logs(log_dir=temp_log_dir, max_age_days=30)

    assert os.path.exists(recent_log), "Recent log file should be preserved"
    assert deleted_count == 0, "Should report 0 files deleted"


def test_sensitive_data_filter_preserves_numeric_types(temp_log_dir):

    from configuration.logging_config import SensitiveDataFilter

    filter_instance = SensitiveDataFilter()

    record = logging.LogRecord(
        name="waitress.queue",
        level=logging.WARNING,
        pathname="task.py",
        lineno=113,
        msg="Task queue depth is %d",
        args=(2,),
        exc_info=None,
    )

    result = filter_instance.filter(record)

    assert result is True

    assert record.args is not None
    args_tuple = cast(tuple[int], record.args)
    assert args_tuple == (2,), f"Expected (2,), got {args_tuple}"
    assert isinstance(args_tuple[0], int), f"Expected int, got {type(args_tuple[0])}"

    message = record.getMessage()
    assert message == "Task queue depth is 2"


def test_sensitive_data_filter_converts_to_string_when_redacting():
    from configuration.logging_config import SensitiveDataFilter

    filter_instance = SensitiveDataFilter()

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

    assert record.args is not None
    args_tuple = cast(tuple[str], record.args)
    assert "[REDACTED]" in str(args_tuple[0])
    assert "sk-secret123" not in str(args_tuple[0])
