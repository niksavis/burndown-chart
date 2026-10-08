import logging
import time
from collections.abc import Callable
from datetime import datetime
from functools import lru_cache, wraps
from typing import Any

from dateutil import parser as dateutil_parser

logger = logging.getLogger(__name__)


def log_performance(func: Callable) -> Callable:

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        func_name = func.__name__

        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.info(f"{func_name} completed in {elapsed:.3f}s")
            return result

        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(
                f"[X] {func_name} failed after {elapsed:.3f}s: {type(e).__name__}: {e}",
                exc_info=True,
            )
            raise

    return wrapper


class PerformanceTimer:
    def __init__(self, operation_name: str | None = None):

        self.operation_name = operation_name
        self.start_time: float | None = None
        self.elapsed: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - (self.start_time or 0)

        if self.operation_name:
            if exc_type is None:
                logger.info(
                    f"⏱️  {self.operation_name} completed in {self.elapsed:.3f}s"
                )
            else:
                logger.error(
                    f"[X] {self.operation_name} failed after {self.elapsed:.3f}s: "
                    f"{exc_type.__name__}: {exc_val}"
                )

        return False


@lru_cache(maxsize=1000)
def parse_jira_date(date_string: str | None) -> datetime | None:

    if date_string is None:
        return None

    try:
        if len(date_string) == 10 and date_string[4] == "-" and date_string[7] == "-":
            return datetime.strptime(date_string, "%Y-%m-%d")

        if "T" in date_string:
            if date_string.endswith("Z"):
                normalized = date_string[:-1] + "+0000"
            else:
                normalized = date_string

            if "." in normalized:
                return datetime.strptime(normalized, "%Y-%m-%dT%H:%M:%S.%f%z")

            return datetime.strptime(normalized, "%Y-%m-%dT%H:%M:%S%z")

        return dateutil_parser.parse(date_string)
    except (ValueError, TypeError) as e:
        try:
            return dateutil_parser.parse(date_string)
        except ValueError, TypeError:
            logger.warning(f"Failed to parse date '{date_string}': {e}")
            return None


class FieldMappingIndex:
    def __init__(self, field_mappings: dict[str, str]):

        self._forward_index: dict[str, str] = dict(field_mappings)

        self._reverse_index: dict[str, str] = {
            jira_field: logical_name
            for logical_name, jira_field in field_mappings.items()
        }

    def get_jira_field(self, logical_name: str) -> str | None:

        return self._forward_index.get(logical_name)

    def get_logical_name(self, jira_field: str) -> str | None:

        return self._reverse_index.get(jira_field)


class CalculationContext:
    def __init__(self, issues: list[dict[str, Any]]):

        self._issues = issues
        self._filter_cache: dict[int, list[dict[str, Any]]] = {}

    def get_filtered_issues(
        self, filter_func: Callable[[dict[str, Any]], bool]
    ) -> list[dict[str, Any]]:

        filter_key = hash(filter_func.__code__.co_code)

        if filter_key in self._filter_cache:
            logger.debug(f"Cache hit for filter (key: {filter_key})")
            return self._filter_cache[filter_key]

        logger.debug(f"Cache miss for filter (key: {filter_key}), computing...")
        filtered_issues = [issue for issue in self._issues if filter_func(issue)]
        self._filter_cache[filter_key] = filtered_issues

        return filtered_issues

    def get_issue_count(self) -> int:
        return len(self._issues)

    def clear_cache(self):
        self._filter_cache.clear()
