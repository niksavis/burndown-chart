"""
Cache management module with configuration-based invalidation.

This module provides enhanced caching functionality with:
- MD5 hash-based cache keys from configuration
- Cache validation (age, config hash, version)
- Automatic invalidation on configuration changes
- Cache metadata tracking

Usage:
    from data.cache_manager import (
        generate_cache_key,
        load_cache_with_validation,
        save_cache
    )

    # Generate cache key
    cache_key = generate_cache_key(
        jql_query="project = ACME",
        field_mappings={"points": "customfield_10002"},
        time_period_days=30
    )

    # Try to load from cache
    cache_hit, data = load_cache_with_validation(
        jql_query="project = ACME",
        field_mappings={"points": "customfield_10002"},
        time_period_days=30
    )

    if not cache_hit:
        # Fetch fresh data and cache it
        data = fetch_data()
        save_cache(
            jql_query="project = ACME",
            field_mappings={"points": "customfield_10002"},
            time_period_days=30,
            data=data
        )
"""

import hashlib
import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Tuple, Optional, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


def generate_cache_key(
    jql_query: str, field_mappings: Dict[str, str], time_period_days: int
) -> str:
    """
    Generate deterministic cache key from configuration parameters.

    DEPRECATED: Use generate_jira_data_cache_key() for JIRA data caching.
    This function is kept for backward compatibility only.

    The cache key is an MD5 hash of the normalized configuration:
    - JQL query
    - Field mappings (sorted for consistency)
    - Time period

    Same inputs always produce the same cache key.

    Args:
        jql_query: JIRA JQL query string
        field_mappings: Mapping of logical names to JIRA custom fields
        time_period_days: Time period for data fetch (30, 60, 90 days)

    Returns:
        32-character hexadecimal string (MD5 hash)

    Example:
        >>> cache_key = generate_cache_key(
        ...     jql_query="project = ACME AND status = Done",
        ...     field_mappings={"deployment_date": "customfield_10001"},
        ...     time_period_days=30
        ... )
        >>> len(cache_key)
        32
    """
    # Step 1: Build configuration dictionary with deterministic key ordering
    # This ensures the same inputs always produce the same hash
    config_data = {
        "jql": jql_query,
        # Sort field mappings by key name for consistent ordering
        # Example: {"deployment_date": "cf_10001", "points": "cf_10002"}
        # becomes: [("deployment_date", "cf_10001"), ("points", "cf_10002")]
        "fields": sorted(field_mappings.items()),
        "period": time_period_days,
    }

    # Step 2: Serialize to JSON with sorted keys for deterministic string representation
    # sort_keys=True ensures {"a": 1, "b": 2} always serializes the same way
    # This prevents hash changes due to dictionary key ordering variations
    config_str = json.dumps(config_data, sort_keys=True)

    # Step 3: Generate MD5 hash from the JSON string
    # MD5 chosen for speed (not security) - provides 32-character unique identifier
    # encode("utf-8") converts string to bytes for hashing
    # hexdigest() returns lowercase hexadecimal string (e.g., "a3c7f8e9...")
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def generate_jira_data_cache_key(jql_query: str, time_period_days: int) -> str:
    """
    Generate cache key for JIRA raw data (independent of field mappings).

    This key is ONLY based on what data we fetch from JIRA:
    - JQL query (which issues to fetch)
    - Time period (how far back to look)

    Field mappings DO NOT affect this key because they only control how we
    PROCESS the data, not what data we fetch. This allows field mapping changes
    to reuse existing cached JIRA data without requiring re-download.

    Args:
        jql_query: JIRA JQL query string
        time_period_days: Time period for data fetch (30, 60, 90 days)

    Returns:
        32-character hexadecimal string (MD5 hash)

    Example:
        >>> cache_key = generate_jira_data_cache_key(
        ...     jql_query="project = ACME AND status = Done",
        ...     time_period_days=30
        ... )
        >>> len(cache_key)
        32
    """
    config_data = {
        "jql": jql_query,
        "period": time_period_days,
    }

    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def generate_processing_config_hash(field_mappings: Dict[str, str]) -> str:
    """
    Generate hash for processing configuration (field mappings, WIP states, etc.).

    This hash changes when we modify HOW we process JIRA data:
    - Field mappings (which JIRA fields map to which metrics)
    - WIP states (which statuses count as "in progress")
    - Completion statuses (which statuses count as "done")

    This hash is stored WITH cached metrics to detect when metrics need
    recalculation, but does NOT affect JIRA data cache keys.

    Args:
        field_mappings: Mapping of logical names to JIRA custom fields

    Returns:
        32-character hexadecimal string (MD5 hash)

    Example:
        >>> config_hash = generate_processing_config_hash(
        ...     {"deployment_date": "customfield_10001"}
        ... )
        >>> len(config_hash)
        32
    """
    config_data = {
        "fields": sorted(field_mappings.items()),
    }

    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def load_cache_with_validation(
    cache_key: str, config_hash: str, max_age_hours: int = 24, cache_dir: str = "cache"
) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """
    Load cache data with validation checks.

    Validates cache by checking:
    - File exists
    - Not expired (within max_age_hours)
    - Config hash matches (same configuration)

    Args:
        cache_key: MD5 hash identifying this cache
        config_hash: Hash of current configuration
        max_age_hours: Maximum age in hours before cache expires (default: 24)
        cache_dir: Directory containing cache files (default: "cache")

    Returns:
        Tuple of (is_valid, data):
            - is_valid: True if cache is valid and fresh
            - data: Cached data if valid, None otherwise

    Example:
        >>> is_valid, data = load_cache_with_validation(
        ...     cache_key="abc123...",
        ...     config_hash="def456...",
        ...     max_age_hours=24
        ... )
        >>> if is_valid:
        ...     print(f"Loaded {len(data)} items from cache")
    """
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    # Check if cache file exists
    if not os.path.exists(cache_file):
        logger.debug(f"Cache miss: file not found ({cache_key})")
        return False, None

    try:
        # Load cache file
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)

        # Validate structure
        if "metadata" not in cache_data or "data" not in cache_data:
            logger.warning(f"Cache invalid: missing metadata or data ({cache_key})")
            return False, None

        metadata = cache_data["metadata"]

        # Check config hash
        if metadata.get("config_hash") != config_hash:
            logger.debug(f"Cache invalid: config mismatch ({cache_key})")
            return False, None

        # Check timestamp
        timestamp_str = metadata.get("timestamp")
        if not timestamp_str:
            logger.warning(f"Cache invalid: missing timestamp ({cache_key})")
            return False, None

        # Parse timestamp and check age
        cache_timestamp = datetime.fromisoformat(timestamp_str)

        # Make timestamps timezone-aware for comparison
        if cache_timestamp.tzinfo is None:
            # Naive timestamp - assume UTC
            cache_timestamp = cache_timestamp.replace(tzinfo=timezone.utc)

        now_utc = datetime.now(timezone.utc)
        age_hours = (now_utc - cache_timestamp).total_seconds() / 3600

        if age_hours > max_age_hours:
            logger.debug(
                f"Cache expired: {age_hours:.1f}h old (max: {max_age_hours}h) ({cache_key})"
            )
            return False, None

        # Cache is valid
        logger.info(
            f"Cache hit: loaded {len(cache_data['data'])} items ({age_hours:.1f}h old)"
        )
        return True, cache_data["data"]

    except (json.JSONDecodeError, ValueError, KeyError) as e:
        logger.error(f"Cache read error: {e} ({cache_key})", exc_info=True)
        return False, None


def save_cache(
    cache_key: str,
    data: List[Dict[str, Any]],
    config_hash: str,
    cache_dir: str = "cache",
) -> None:
    """
    Save data to cache with metadata.

    Creates cache file with structure:
    {
        "metadata": {
            "timestamp": "2025-11-09T10:00:00+00:00",
            "cache_key": "abc123...",
            "config_hash": "def456..."
        },
        "data": [...]
    }

    Args:
        cache_key: MD5 hash identifying this cache
        data: Data to cache (list of dictionaries)
        config_hash: Hash of current configuration
        cache_dir: Directory to store cache files (default: "cache")

    Example:
        >>> save_cache(
        ...     cache_key="abc123...",
        ...     data=[{"key": "TEST-1", "summary": "Test"}],
        ...     config_hash="def456..."
        ... )
    """
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)

    # Create cache data with metadata
    cache_data = {
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cache_key": cache_key,
            "config_hash": config_hash,
        },
        "data": data,
    }

    # Write to cache file
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Cache saved: {len(data)} items ({cache_key})")

    except (IOError, OSError) as e:
        logger.error(f"Cache write error: {e} ({cache_key})", exc_info=True)


def invalidate_cache(cache_key: str, cache_dir: str = "cache") -> None:
    """
    Invalidate (delete) cache file.

    Args:
        cache_key: MD5 hash identifying cache to invalidate
        cache_dir: Directory containing cache files (default: "cache")

    Example:
        >>> invalidate_cache("abc123...")
    """
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    if os.path.exists(cache_file):
        try:
            os.remove(cache_file)
            logger.info(f"Cache invalidated: {cache_key}")
        except (IOError, OSError) as e:
            logger.error(f"Cache deletion error: {e} ({cache_key})", exc_info=True)
    else:
        logger.debug(f"Cache file not found for invalidation: {cache_key}")


def invalidate_metrics_cache_only() -> None:
    """
    Invalidate ONLY metrics cache (snapshots and calculated metrics).

    This preserves JIRA raw data cache files in cache/*.json, allowing
    metrics to be recalculated from existing JIRA data when only field
    mappings change.

    Use this when:
    - Field mappings change (WIP states, completion statuses, etc.)
    - Metric calculation logic changes
    - You want to recalculate metrics without re-downloading JIRA data

    Files invalidated:
    - metrics_snapshots.json
    - metrics_cache.json (DORA/Flow metrics cache)

    Files preserved:
    - cache/*.json (JIRA raw issue data)
    """
    try:
        # Remove metrics snapshots
        if os.path.exists("metrics_snapshots.json"):
            os.remove("metrics_snapshots.json")
            logger.info("[OK] Invalidated metrics_snapshots.json")

        # Remove DORA/Flow metrics cache
        from data.metrics_cache import invalidate_cache as invalidate_metrics_cache_file

        invalidate_metrics_cache_file()  # Removes metrics_cache.json
        logger.info("[OK] Invalidated metrics_cache.json (DORA/Flow)")

        logger.info(
            "[OK] Metrics cache invalidated - JIRA data cache preserved for reuse"
        )

    except Exception as e:
        logger.error(f"Error invalidating metrics cache: {e}", exc_info=True)


def invalidate_all_cache() -> None:
    """
    Invalidate ALL cache files (JIRA data + metrics).

    This forces a complete re-download of JIRA data and recalculation of metrics.

    Use this when:
    - JQL query changes
    - Time period changes
    - JIRA configuration changes (base URL, token, etc.)
    - You suspect cache corruption

    Files invalidated:
    - cache/*.json (JIRA raw issue data)
    - metrics_snapshots.json
    - metrics_cache.json
    - jira_cache.json (legacy)
    """
    try:
        # Remove JIRA data cache files
        import glob

        cache_files = glob.glob("cache/*.json")
        for cache_file in cache_files:
            try:
                os.remove(cache_file)
            except Exception as e:
                logger.debug(f"Could not remove cache file {cache_file}: {e}")
        logger.info(f"[OK] Invalidated {len(cache_files)} JIRA cache files")

        # Remove legacy jira_cache.json
        if os.path.exists("jira_cache.json"):
            os.remove("jira_cache.json")
            logger.info("[OK] Invalidated jira_cache.json (legacy)")

        # Remove metrics cache
        invalidate_metrics_cache_only()

        logger.info("[OK] All cache invalidated - full JIRA re-download required")

    except Exception as e:
        logger.error(f"Error invalidating all cache: {e}", exc_info=True)


class CacheInvalidationTrigger:
    """
    Detects when cache should be invalidated based on configuration changes.

    Checks for changes in:
    - JQL query
    - Field mappings
    - Time period
    """

    def should_invalidate(
        self, old_config: Dict[str, Any], new_config: Dict[str, Any]
    ) -> bool:
        """
        Check if configuration changes require cache invalidation.

        Args:
            old_config: Previous configuration
            new_config: Current configuration

        Returns:
            True if cache should be invalidated, False otherwise

        Example:
            >>> trigger = CacheInvalidationTrigger()
            >>> old = {"jql_query": "project = TEST"}
            >>> new = {"jql_query": "project = PROD"}
            >>> trigger.should_invalidate(old, new)
            True
        """
        # Check JQL query changes
        if old_config.get("jql_query") != new_config.get("jql_query"):
            logger.info("Cache invalidation: JQL query changed")
            return True

        # Check field mappings changes
        old_fields = old_config.get("field_mappings", {})
        new_fields = new_config.get("field_mappings", {})
        if old_fields != new_fields:
            logger.info("Cache invalidation: field mappings changed")
            return True

        # Check time period changes
        if old_config.get("time_period") != new_config.get("time_period"):
            logger.info("Cache invalidation: time period changed")
            return True

        # No changes detected
        return False
