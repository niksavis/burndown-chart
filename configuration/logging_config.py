import glob
import json
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from logging.handlers import RotatingFileHandler

from data.installation_context import get_installation_context

_installation_context = get_installation_context()
DEFAULT_LOG_DIR = str(_installation_context.logs_path)


class SensitiveDataFilter(logging.Filter):
    SENSITIVE_PATTERNS = [
        (
            r"Authorization:\s+Bearer\s+[A-Za-z0-9\-._~+/]+=*",
            "Authorization: Bearer [REDACTED]",
        ),
        (r"Authorization:\s+(?!Bearer)[^\s]+", "Authorization: [REDACTED]"),
        (r'"token":\s*"[^"]*"', '"token": "[REDACTED]"'),
        (r"\btoken\s+[A-Za-z0-9\-._~+/]+=*", "token [REDACTED]"),
        (r'"password":\s*"[^"]*"', '"password": "[REDACTED]"'),
        (r'"api_key":\s*"[^"]*"', '"api_key": "[REDACTED]"'),
        (
            r'api[_\-\s]?key["\']?\s*[:=]\s*["\']?[A-Za-z0-9\-._~+/]+=*',
            "api_key: [REDACTED]",
        ),
        (
            r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b",
            r"***@\1",
        ),
    ]

    def filter(self, record):

        msg = str(record.msg)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        record.msg = msg

        if record.args:
            redacted_args = []
            for arg in record.args:
                arg_str = str(arg)
                original_arg_str = arg_str
                for pattern, replacement in self.SENSITIVE_PATTERNS:
                    arg_str = re.sub(pattern, replacement, arg_str, flags=re.IGNORECASE)
                if arg_str != original_arg_str:
                    redacted_args.append(arg_str)
                else:
                    redacted_args.append(arg)
            record.args = tuple(redacted_args)

        return True


class JSONFormatter(logging.Formatter):
    def format(self, record):

        try:
            message = record.getMessage()
        except (TypeError, ValueError) as e:
            message = f"{record.msg} (formatting error: {e})"

        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": message,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(
    log_dir: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    log_level: str = "INFO",
) -> None:

    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR

    os.makedirs(log_dir, exist_ok=True)

    sensitive_filter = SensitiveDataFilter()

    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    app_handler.setLevel(getattr(logging, log_level.upper()))
    app_handler.setFormatter(JSONFormatter())
    app_handler.addFilter(sensitive_filter)

    error_handler = RotatingFileHandler(
        os.path.join(log_dir, "errors.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    error_handler.addFilter(sensitive_filter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    console_handler.addFilter(sensitive_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    root_logger.handlers = []

    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    waitress_logger = logging.getLogger("waitress")
    waitress_logger.setLevel(logging.WARNING)

    waitress_queue_logger = logging.getLogger("waitress.queue")
    waitress_queue_logger.setLevel(logging.ERROR)

    class WaitressFormatter(logging.Formatter):
        def format(self, record):
            try:
                return super().format(record)
            except TypeError, ValueError:
                return f"{record.levelname} - waitress - {record.msg}"

    waitress_handler = logging.StreamHandler()
    waitress_handler.setFormatter(
        WaitressFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    waitress_logger.handlers = [waitress_handler]


def shutdown_logging() -> None:

    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)


def cleanup_old_logs(log_dir: str | None = None, max_age_days: int = 30) -> int:

    logger = logging.getLogger(__name__)

    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR

    try:
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()

        log_pattern = os.path.join(log_dir, "*.log*")
        log_files = glob.glob(log_pattern)

        deleted_count = 0
        for log_file in log_files:
            try:
                file_mtime = os.path.getmtime(log_file)

                if file_mtime < cutoff_timestamp:
                    os.unlink(log_file)
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")

            except (OSError, PermissionError) as e:
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
