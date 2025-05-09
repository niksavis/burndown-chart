"""
Caching Module

This module provides caching functionality for expensive operations
to improve performance of the application.
"""

#######################################################################
# IMPORTS
#######################################################################
# Standard library imports
import functools
import time
import hashlib
import json
import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Tuple,
    TypeVar,
    cast,
    Optional,
    Union,
    TypedDict,
)

# Application imports
from utils.dataframe_utils import df_to_hashable

#######################################################################
# TYPE DEFINITIONS
#######################################################################
F = TypeVar("F", bound=Callable[..., Any])


# Define more specific types for the cache structure
class CacheValue(TypedDict):
    """Type definition for a cache value."""

    value: Any
    timestamp: float


CacheKey = Tuple[Any, ...]
CacheNamespace = Dict[CacheKey, Tuple[Any, float]]
CacheStore = Dict[str, CacheNamespace]

#######################################################################
# CACHE DEFINITIONS
#######################################################################
# Global cache storage
_CACHE: CacheStore = {}

#######################################################################
# LOGGING
#######################################################################
logger = logging.getLogger("burndown_chart")

#######################################################################
# CACHE FUNCTIONS
#######################################################################


def _make_hashable(obj: Any) -> Any:
    """
    Convert an unhashable object to a hashable representation.

    Args:
        obj: The object to make hashable

    Returns:
        A hashable representation of the object
    """
    # Handle pandas DataFrame specially using our utility
    if str(type(obj)).endswith("pandas.core.frame.DataFrame'>"):
        return df_to_hashable(obj)

    # Handle other unhashable types
    if isinstance(obj, (dict, list)):
        try:
            # Convert to a stable JSON string and hash it
            return f"{type(obj).__name__}:{hashlib.md5(json.dumps(obj, sort_keys=True).encode()).hexdigest()}"
        except (TypeError, ValueError):
            # Fallback for objects that can't be JSON serialized
            return str(obj)

    # Already hashable types
    return obj


def memoize(max_age_seconds: int = 300) -> Callable[[F], F]:
    """
    Decorator to cache function results based on arguments.

    Args:
        max_age_seconds: Maximum age of cache entries in seconds before refreshing

    Returns:
        Decorated function with caching
    """

    def decorator(func: F) -> F:
        cache_key = f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Ensure the cache dictionary exists for this function
            if cache_key not in _CACHE:
                _CACHE[cache_key] = {}

            # Create a hashable key from the arguments
            key_parts = args
            if kwargs:
                for k, v in sorted(kwargs.items()):
                    key_parts += (k, v)

            # Convert any unhashable types to hashable representations
            try:
                hashable_key = tuple(_make_hashable(arg) for arg in key_parts)
            except Exception as e:
                logger.warning(
                    f"Failed to create hashable key: {str(e)}. Calling function without caching."
                )
                return func(*args, **kwargs)

            # Check if we have a valid cached value
            now = time.time()
            if hashable_key in _CACHE[cache_key]:
                value, timestamp = _CACHE[cache_key][hashable_key]
                if now - timestamp < max_age_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return value

            # Calculate the value and cache it
            logger.debug(f"Cache miss for {func.__name__}, calculating new value")
            result = func(*args, **kwargs)
            _CACHE[cache_key][hashable_key] = (result, now)
            return result

        return cast(F, wrapper)

    return decorator


def clear_cache(namespace: Optional[str] = None) -> None:
    """
    Clear the cache, optionally for a specific namespace only.

    Args:
        namespace: Optional function namespace to clear
    """
    global _CACHE

    if namespace is None:
        _CACHE = {}
        logger.debug("Cleared entire cache")
    elif namespace in _CACHE:
        _CACHE[namespace] = {}
        logger.debug(f"Cleared cache for namespace: {namespace}")


def get_cache_stats() -> Dict[str, Union[int, Dict[str, int]]]:
    """
    Get statistics about the cache usage.

    Returns:
        Dictionary with cache statistics including:
        - namespaces: Number of namespaces in the cache
        - total_entries: Total number of cached entries
        - entries_by_namespace: Dictionary mapping namespace names to entry counts
    """
    return {
        "namespaces": len(_CACHE),
        "total_entries": sum(len(entries) for entries in _CACHE.values()),
        "entries_by_namespace": {ns: len(entries) for ns, entries in _CACHE.items()},
    }
