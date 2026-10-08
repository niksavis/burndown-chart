import functools
import hashlib
import json
import logging
import time
from collections.abc import Callable
from typing import (
    Any,
    TypedDict,
    TypeVar,
    cast,
)

import pandas as pd

from utils.dataframe_utils import df_to_hashable

F = TypeVar("F", bound=Callable[..., Any])


class CacheValue(TypedDict):
    value: Any
    timestamp: float


CacheKey = tuple[Any, ...]
CacheNamespace = dict[CacheKey, tuple[Any, float]]
CacheStore = dict[str, CacheNamespace]

_CACHE: CacheStore = {}

logger = logging.getLogger("burndown_chart")


def _make_hashable(obj: Any) -> Any:

    if isinstance(obj, pd.DataFrame):
        return df_to_hashable(obj)

    if isinstance(obj, (dict, list)):
        try:
            hash_value = hashlib.md5(
                json.dumps(obj, sort_keys=True).encode()
            ).hexdigest()
            return f"{type(obj).__name__}:{hash_value}"
        except TypeError, ValueError:
            return str(obj)

    return obj


def memoize(max_age_seconds: int = 300) -> Callable[[F], F]:

    def decorator(func: F) -> F:
        cache_key = f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if cache_key not in _CACHE:
                _CACHE[cache_key] = {}

            key_parts = args
            if kwargs:
                for k, v in sorted(kwargs.items()):
                    key_parts += (k, v)

            try:
                hashable_key = tuple(_make_hashable(arg) for arg in key_parts)
            except Exception as e:
                logger.warning(
                    "Failed to create hashable key: "
                    f"{str(e)}. Calling function without caching."
                )
                return func(*args, **kwargs)

            now = time.time()
            if hashable_key in _CACHE[cache_key]:
                value, timestamp = _CACHE[cache_key][hashable_key]
                if now - timestamp < max_age_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return value

            logger.debug(f"Cache miss for {func.__name__}, calculating new value")
            result = func(*args, **kwargs)
            _CACHE[cache_key][hashable_key] = (result, now)
            return result

        return cast(F, wrapper)

    return decorator


def clear_cache(namespace: str | None = None) -> None:

    global _CACHE

    if namespace is None:
        _CACHE = {}
        logger.debug("Cleared entire cache")
    elif namespace in _CACHE:
        _CACHE[namespace] = {}
        logger.debug(f"Cleared cache for namespace: {namespace}")


def get_cache_stats() -> dict[str, int | dict[str, int]]:

    return {
        "namespaces": len(_CACHE),
        "total_entries": sum(len(entries) for entries in _CACHE.values()),
        "entries_by_namespace": {ns: len(entries) for ns, entries in _CACHE.items()},
    }
