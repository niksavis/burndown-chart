import hashlib
import json
import logging
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any

from data.exceptions import CacheError, PersistenceError
from data.metrics_cache import invalidate_cache as invalidate_metrics_cache_file
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


_backend_available = None
_backend_instance = None


def _get_backend():

    global _backend_available, _backend_instance

    if _backend_available is False:
        return None

    if _backend_instance is not None:
        return _backend_instance

    try:
        _backend_instance = get_backend()
        _backend_available = True
        return _backend_instance
    except (
        ImportError,
        ModuleNotFoundError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        AttributeError,
        sqlite3.Error,
    ) as e:
        logger.debug(f"Backend not available: {e}")
        _backend_available = False
        return None


def generate_cache_key(
    jql_query: str, field_mappings: dict[str, str], time_period_days: int
) -> str:

    config_data = {
        "jql": jql_query,
        "fields": sorted(field_mappings.items()),
        "period": time_period_days,
    }

    config_str = json.dumps(config_data, sort_keys=True)

    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def generate_jira_data_cache_key(jql_query: str, time_period_days: int) -> str:

    config_data = {
        "jql": jql_query,
        "period": time_period_days,
    }

    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def generate_processing_config_hash(field_mappings: dict[str, str]) -> str:

    config_data = {
        "fields": sorted(field_mappings.items()),
    }

    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.md5(config_str.encode("utf-8")).hexdigest()


def load_cache_with_validation(
    cache_key: str,
    config_hash: str,
    max_age_hours: int = 24,
    cache_dir: str = "cache",
    profile_id: str | None = None,
    query_id: str | None = None,
) -> tuple[bool, list[dict[str, Any]] | None]:

    backend = _get_backend()
    if backend:
        try:
            if not profile_id:
                profile_id = backend.get_app_state("active_profile_id")
            if not query_id:
                query_id = backend.get_app_state("active_query_id")

            if profile_id and query_id:
                cache_response = backend.get_jira_cache(profile_id, query_id, cache_key)
                if cache_response:
                    if (
                        "issues" not in cache_response
                        or "metadata" not in cache_response
                    ):
                        logger.warning(
                            "Database cache invalid: missing issues or metadata "
                            f"({cache_key})"
                        )
                    else:
                        metadata = cache_response["metadata"]

                        cached_config_hash = metadata.get("config_hash", "")
                        if cached_config_hash and cached_config_hash != config_hash:
                            logger.debug(
                                f"Database cache invalid: config mismatch ({cache_key})"
                            )
                        else:
                            timestamp_str = metadata.get("timestamp")
                            if timestamp_str:
                                cache_timestamp = datetime.fromisoformat(timestamp_str)
                                if cache_timestamp.tzinfo is None:
                                    cache_timestamp = cache_timestamp.replace(
                                        tzinfo=UTC
                                    )

                                now_utc = datetime.now(UTC)
                                age_hours = (
                                    now_utc - cache_timestamp
                                ).total_seconds() / 3600

                                if age_hours <= max_age_hours:
                                    logger.info(
                                        "Database cache hit: loaded "
                                        f"{len(cache_response['issues'])} items "
                                        f"({age_hours:.1f}h old)"
                                    )
                                    return True, cache_response["issues"]
                                else:
                                    logger.debug(
                                        f"Database cache expired: {age_hours:.1f}h "
                                        f"old (max: {max_age_hours}h) "
                                        f"({cache_key})"
                                    )
                else:
                    logger.debug(f"Database cache miss: no record found ({cache_key})")
        except (
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            sqlite3.Error,
            PersistenceError,
        ) as e:
            logger.exception("Database cache load failed")
            cache_error = CacheError("Failed to load cache from database")
            logger.debug("%s: %s", type(cache_error).__name__, e)

    logger.debug(f"Cache miss: no valid cache found ({cache_key})")
    return False, None


def save_cache(
    cache_key: str,
    data: list[dict[str, Any]],
    config_hash: str,
    cache_dir: str = "cache",
    profile_id: str | None = None,
    query_id: str | None = None,
) -> None:

    backend = _get_backend()
    if backend:
        try:
            if not profile_id:
                profile_id = backend.get_app_state("active_profile_id")
            if not query_id:
                query_id = backend.get_app_state("active_query_id")

            if profile_id and query_id:
                cache_response = {
                    "issues": data,
                    "metadata": {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "cache_key": cache_key,
                        "config_hash": config_hash,
                    },
                }
                expires_at = datetime.now(UTC) + timedelta(hours=24)
                backend.save_jira_cache(
                    profile_id, query_id, cache_key, cache_response, expires_at
                )
                logger.info(f"Cache saved to database: {len(data)} items ({cache_key})")
                return
        except (
            OSError,
            RuntimeError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
            sqlite3.Error,
            PersistenceError,
        ) as e:
            logger.exception("Database cache save failed")
            cache_error = CacheError("Failed to save cache to database")
            logger.debug("%s: %s", type(cache_error).__name__, e)

    logger.warning(
        "Cache not saved: database backend unavailable or no active "
        f"profile/query ({cache_key})"
    )


def invalidate_cache(cache_key: str, cache_dir: str = "cache") -> None:

    logger.debug(
        "invalidate_cache called but deprecated - cache managed by database "
        f"({cache_key})"
    )


def invalidate_metrics_cache_only() -> None:

    try:
        if os.path.exists("metrics_snapshots.json"):
            os.remove("metrics_snapshots.json")
            logger.info("[OK] Invalidated metrics_snapshots.json")

        invalidate_metrics_cache_file()
        logger.info("[OK] Invalidated metrics_cache.json (DORA/Flow)")

        logger.info(
            "[OK] Metrics cache invalidated - JIRA data cache preserved for reuse"
        )

    except (OSError, RuntimeError, ValueError, TypeError, ImportError) as e:
        logger.exception("Error invalidating metrics cache")
        cache_error = CacheError("Failed to invalidate metrics cache")
        logger.debug("%s: %s", type(cache_error).__name__, e)


def invalidate_all_cache() -> None:

    try:
        import glob  # noqa: PLC0415

        cache_files = glob.glob("cache/*.json")
        for cache_file in cache_files:
            try:
                os.remove(cache_file)
            except OSError as e:
                logger.debug(f"Could not remove cache file {cache_file}: {e}")
        logger.info(f"[OK] Invalidated {len(cache_files)} JIRA cache files")

        if os.path.exists("jira_cache.json"):
            os.remove("jira_cache.json")
            logger.info("[OK] Invalidated jira_cache.json (legacy)")

        invalidate_metrics_cache_only()

        logger.info("[OK] All cache invalidated - full JIRA re-download required")

    except (OSError, RuntimeError, ValueError, TypeError, ImportError) as e:
        logger.exception("Error invalidating all cache")
        cache_error = CacheError("Failed to invalidate all cache")
        logger.debug("%s: %s", type(cache_error).__name__, e)


class CacheInvalidationTrigger:
    def should_invalidate(
        self, old_config: dict[str, Any], new_config: dict[str, Any]
    ) -> bool:

        if old_config.get("jql_query") != new_config.get("jql_query"):
            logger.info("Cache invalidation: JQL query changed")
            return True

        old_fields = old_config.get("field_mappings", {})
        new_fields = new_config.get("field_mappings", {})
        if old_fields != new_fields:
            logger.info("Cache invalidation: field mappings changed")
            return True

        if old_config.get("time_period") != new_config.get("time_period"):
            logger.info("Cache invalidation: time period changed")
            return True

        return False


def has_jira_data_for_query(profile_id: str, query_id: str) -> bool:

    try:
        backend = get_backend()
        issues = backend.get_issues(profile_id, query_id, limit=1)
        return len(issues) > 0
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("Error checking JIRA data")
        cache_error = CacheError("Failed to check JIRA data cache state")
        logger.debug("%s: %s", type(cache_error).__name__, e)
        return False
