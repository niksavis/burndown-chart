import logging
import sqlite3
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)


def extract_nested_field(fields_dict: dict, field_path: str) -> Any:

    if not field_path:
        return None

    if "." in field_path:
        parts = field_path.split(".")
        value = fields_dict
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
    else:
        return fields_dict.get(field_path)


def retry_on_db_lock(max_retries: int = 3, base_delay: float = 0.1):

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    if "database is locked" in error_msg or "locked" in error_msg:
                        if attempt < max_retries:
                            delay = base_delay * (2**attempt)
                            logger.warning(
                                f"Database locked in {func.__name__}, "
                                f"retrying in {delay}s "
                                f"(attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(
                                f"Database locked in {func.__name__} "
                                f"after {max_retries} retries"
                            )
                            raise RuntimeError(
                                "Database is locked after "
                                f"{max_retries} retry attempts. "
                                "This may indicate concurrent access "
                                "or a hung transaction. "
                                "Try closing other instances of the app "
                                "or wait a moment."
                            ) from e
                    else:
                        raise
                except Exception:
                    raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator
