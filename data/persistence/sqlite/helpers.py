"""
Helper functions for SQLite backend operations.

This module provides utility functions used across multiple SQLite backend operations.
"""

import logging
import sqlite3
import time
from functools import wraps
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


def extract_nested_field(fields_dict: Dict, field_path: str) -> Any:
    """Extract value from nested field path (e.g., 'resolved.resolutiondate').

    Args:
        fields_dict: JIRA fields dictionary
        field_path: Field path, may contain dots for nested access

    Returns:
        Field value or None if not found
    """
    if not field_path:
        return None

    # Handle nested field paths (e.g., "resolved.resolutiondate")
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
        # Simple field (e.g., "created", "resolutiondate")
        return fields_dict.get(field_path)


def retry_on_db_lock(max_retries: int = 3, base_delay: float = 0.1):
    """
    Decorator to retry database operations when database is locked.

    Implements exponential backoff: 0.1s, 0.2s, 0.4s for default settings.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 0.1)

    Example:
        @retry_on_db_lock(max_retries=3, base_delay=0.1)
        def save_profile(self, profile: Dict) -> None:
            # Database operation that might encounter locks
            ...
    """

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

                    # Only retry on database lock errors
                    if "database is locked" in error_msg or "locked" in error_msg:
                        if attempt < max_retries:
                            delay = base_delay * (2**attempt)
                            logger.warning(
                                f"Database locked in {func.__name__}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(
                                f"Database locked in {func.__name__} after {max_retries} retries"
                            )
                            raise RuntimeError(
                                f"Database is locked after {max_retries} retry attempts. "
                                "This may indicate concurrent access or a hung transaction. "
                                "Try closing other instances of the app or wait a moment."
                            ) from e
                    else:
                        # Non-lock error - don't retry
                        raise
                except Exception:
                    # Non-OperationalError exceptions should not be retried
                    raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator
