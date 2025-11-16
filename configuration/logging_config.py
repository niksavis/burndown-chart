"""
Logging configuration module with file rotation and sensitive data redaction.

This module provides centralized logging setup for the application with:
- File-based logging with automatic rotation (10MB limit, 5 backups)
- JSON formatting for structured logs
- Sensitive data redaction (tokens, passwords, API keys)
- Multiple log handlers (console, file, error-only file)
- Automatic cleanup of old log files (30-day retention)

Usage:
    from configuration.logging_config import setup_logging, cleanup_old_logs

    # Initialize logging at application startup
    setup_logging()
    cleanup_old_logs()

    # Use standard Python logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Application started")
"""

import logging
from logging.handlers import RotatingFileHandler
import json
import re
import os
import glob
from datetime import datetime, timedelta, timezone


class SensitiveDataFilter(logging.Filter):
    """
    Logging filter that redacts sensitive patterns before writing to file.

    This filter automatically redacts:
    - Bearer tokens (Authorization: Bearer ...)
    - API tokens (in JSON: "token": "...")
    - Passwords (in JSON: "password": "...")
    - API keys (in JSON: "api_key": "sk-...")
    - Production URLs (replaces real domains with example.com)
    - Email addresses (user@domain → ***@domain)

    The filter is applied to all log handlers to ensure no sensitive
    data appears in log files.
    """

    # Sensitive patterns to redact (pattern, replacement)
    # Patterns are applied in order, so more specific patterns should come first
    SENSITIVE_PATTERNS = [
        # Production URLs - replace real domains with example.com
        # Matches: https://jira.company.com/... → https://jira.example.com/...
        # Must come FIRST to avoid conflicts with Authorization header patterns
        # Preserves protocol and path for debugging context
        (
            r"https?://(?!(?:localhost|127\.0\.0\.1|example\.com|test\.))[a-zA-Z0-9][-a-zA-Z0-9.]*\.[a-zA-Z]{2,}",
            "https://jira.example.com",
        ),
        # Authorization header with Bearer token - matches the entire header
        # Captures: Authorization: Bearer abc123... → Authorization: Bearer [REDACTED]
        # This must come BEFORE the generic Authorization pattern to preserve "Bearer" keyword
        (
            r"Authorization:\s+Bearer\s+[A-Za-z0-9\-._~+/]+=*",
            "Authorization: Bearer [REDACTED]",
        ),
        # Generic token in Authorization header - matches any value after "Authorization:"
        # BUT excludes Bearer tokens (handled by pattern above)
        # Captures: Authorization: Basic abc123... → Authorization: [REDACTED]
        # Negative lookahead (?!Bearer) ensures we don't match "Authorization: Bearer" again
        (r"Authorization:\s+(?!Bearer)[^\s]+", "Authorization: [REDACTED]"),
        # JSON-style token field - matches "token": "value" in JSON objects
        # Captures: "token": "abc123xyz" → "token": "[REDACTED]"
        # [^"]* matches any character except quotes (until closing quote)
        (r'"token":\s*"[^"]*"', '"token": "[REDACTED]"'),
        # Standalone token in text - matches "token abc123" or "with token xyz789"
        # Captures: with token abc123 → with token [REDACTED]
        (r"\btoken\s+[A-Za-z0-9\-._~+/]+=*", "token [REDACTED]"),
        # JSON-style password field - matches "password": "value" in JSON objects
        # Captures: "password": "myP@ssw0rd" → "password": "[REDACTED]"
        (r'"password":\s*"[^"]*"', '"password": "[REDACTED]"'),
        # JSON-style api_key field - matches OpenAI-style keys (sk-...)
        # Captures: "api_key": "sk-proj-abc123" → "api_key": "[REDACTED]"
        (r'"api_key":\s*"[^"]*"', '"api_key": "[REDACTED]"'),
        # Generic API key patterns - handles various formats: "API key:", "api_key=", "apikey:", etc.
        # Captures: api_key=sk-abc123, API-KEY: "xyz789", apikey="test123"
        # [_\-\s]? allows optional separator (underscore, hyphen, or space)
        # [:=] matches colon or equals sign
        # ["\']? allows optional quotes around the value
        (
            r'api[_\-\s]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9\-._~+/]+=*',
            "api_key: [REDACTED]",
        ),
        # Email addresses - redact username but keep domain for debugging
        # Matches: john.doe@company.com → ***@company.com
        (
            r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b",
            r"***@\1",
        ),
    ]

    def filter(self, record):
        """
        Filter log record by redacting sensitive data.

        Applies all SENSITIVE_PATTERNS to the message before logging.
        Patterns are applied case-insensitively.

        Args:
            record (logging.LogRecord): Log record to filter

        Returns:
            bool: Always True (record is not suppressed, just modified)
        """
        # Apply redaction to message (case-insensitive)
        msg = str(record.msg)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg

        # Also redact args if present
        if record.args:
            redacted_args = []
            for arg in record.args:
                arg_str = str(arg)
                for pattern, replacement in self.SENSITIVE_PATTERNS:
                    arg_str = re.sub(pattern, replacement, arg_str, flags=re.IGNORECASE)
                redacted_args.append(arg_str)
            record.args = tuple(redacted_args)

        return True


class JSONFormatter(logging.Formatter):
    """
    Format log records as JSON for structured logging.

    Output format:
    {
        "timestamp": "2025-11-09T14:30:45.123456Z",
        "level": "INFO",
        "module": "data.dora_calculator",
        "function": "calculate_deployment_frequency",
        "line": 125,
        "message": "Calculated deployment frequency for 850 issues in 1.234s",
        "exception": "..." (if present)
    }
    """

    def format(self, record):
        """
        Format log record as JSON.

        Args:
            record (logging.LogRecord): Log record to format

        Returns:
            str: JSON-formatted log entry
        """
        # Get message safely (handle Waitress type formatting errors in Python 3.13)
        try:
            message = record.getMessage()
        except (TypeError, ValueError) as e:
            # Fallback: Use raw message without formatting if args don't match format string
            message = f"{record.msg} (formatting error: {e})"

        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": message,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_dir: str = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: str = "INFO",
) -> None:
    """
    Initialize application logging with file handlers, rotation, and redaction filters.

    Creates three log handlers:
    1. app.log - All logs (INFO and above) with JSON formatting
    2. errors.log - Error logs only (ERROR and above) with JSON formatting
    3. Console - Plain text for development (INFO and above)

    All handlers use SensitiveDataFilter to redact sensitive data.

    Args:
        log_dir: Directory for log files, created if doesn't exist
        max_bytes: Maximum size per log file before rotation (default 10MB)
        backup_count: Number of rotated backup files to keep (default 5)
        log_level: Minimum log level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

    Raises:
        OSError: If log directory cannot be created
        PermissionError: If log files cannot be written

    Example:
        >>> setup_logging(log_dir='logs', log_level='INFO')
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started")
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Create sensitive data filter (shared by all handlers)
    sensitive_filter = SensitiveDataFilter()

    # Main application log (all levels)
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    app_handler.setLevel(getattr(logging, log_level.upper()))
    app_handler.setFormatter(JSONFormatter())
    app_handler.addFilter(sensitive_filter)

    # Error-only log
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "errors.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    error_handler.addFilter(sensitive_filter)

    # Console handler (plain text for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    console_handler.addFilter(sensitive_filter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []

    # Add our handlers
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)


def shutdown_logging() -> None:
    """
    Properly shutdown all logging handlers and close log files.

    This is critical for Windows environments where file handles must be
    explicitly closed before files can be deleted or moved. Closes all
    handlers on the root logger to release file locks.

    Call this before cleanup operations that need to delete/move log files.

    Example:
        >>> setup_logging()
        >>> # ... application code ...
        >>> shutdown_logging()  # Close all log files
        >>> os.remove('logs/app.log')  # Now safe to delete
    """
    root_logger = logging.getLogger()

    # Close and remove all handlers
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)


def cleanup_old_logs(log_dir: str = "logs", max_age_days: int = 30) -> int:
    """
    Delete log files older than specified age.

    Scans log directory for all .log* files and deletes those with
    modification time older than max_age_days.

    Args:
        log_dir: Directory containing log files
        max_age_days: Delete files older than this many days

    Returns:
        Number of files deleted (int)

    Side Effects:
        - Deletes log files with modification time older than max_age_days
        - Logs deletion operations to application log

    Example:
        >>> deleted_count = cleanup_old_logs(log_dir='logs', max_age_days=30)
        >>> print(f"Deleted {deleted_count} old log files")
    """
    logger = logging.getLogger(__name__)

    try:
        # Calculate cutoff timestamp
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()

        # Find all log files (including rotated ones: .log, .log.1, .log.2, etc.)
        log_pattern = os.path.join(log_dir, "*.log*")
        log_files = glob.glob(log_pattern)

        deleted_count = 0
        for log_file in log_files:
            try:
                # Get file modification time
                file_mtime = os.path.getmtime(log_file)

                # Delete if older than cutoff
                if file_mtime < cutoff_timestamp:
                    os.unlink(log_file)
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")

            except (OSError, PermissionError) as e:
                # Log warning but continue with other files
                logger.warning(f"Failed to delete {log_file}: {e}")

        if deleted_count > 0:
            logger.info(
                f"Cleanup complete: deleted {deleted_count} log files "
                f"older than {max_age_days} days"
            )

        return deleted_count

    except Exception as e:
        logger.error(f"Log cleanup failed: {e}", exc_info=True)
        return 0
