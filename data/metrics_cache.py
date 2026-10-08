import json
import logging
import os
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

CACHE_FILE = "metrics_cache.json"
CACHE_VERSION = "1.0"
MAX_ENTRIES = 100
DEFAULT_TTL_SECONDS = 3600

EVICTION_POLICY = "LRU"


def generate_cache_key(
    metric_type: str, start_date: str, end_date: str, field_hash: str
) -> str:

    return f"{metric_type}_{start_date}_{end_date}_{field_hash}"


def load_cached_metrics(cache_key: str) -> dict | None:

    if not os.path.exists(CACHE_FILE):
        logger.debug(f"Cache miss: {cache_key} (file not found)")
        return None

    try:
        with open(CACHE_FILE) as f:
            content = f.read().strip()
            if not content:
                logger.debug(f"Cache miss: {cache_key} (empty cache file)")
                return None
            cache = json.loads(content)

        if cache.get("cache_version") != CACHE_VERSION:
            logger.warning(
                f"Cache version mismatch: expected {CACHE_VERSION}, "
                f"got {cache.get('cache_version')}"
            )
            return None

        if cache_key not in cache.get("entries", {}):
            logger.debug(f"Cache miss: {cache_key} (key not found)")
            return None

        entry = cache["entries"][cache_key]

        expires_at = datetime.fromisoformat(entry["expires_at"])
        if datetime.now(UTC) > expires_at:
            logger.debug(f"Cache miss: {cache_key} (expired)")
            return None

        entry["last_accessed"] = datetime.now(UTC).isoformat()
        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

        logger.info(f"Cache hit: {cache_key}")
        return entry["metrics"]

    except Exception as e:
        logger.error(f"Error loading cache: {e}")
        return None


def save_cached_metrics(
    cache_key: str, metrics: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS
) -> bool:

    try:
        cache = None
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE) as f:
                    content = f.read().strip()
                    if content:
                        cache = json.loads(content)
            except json.JSONDecodeError, ValueError:
                logger.warning("Cache file corrupted, recreating")
                cache = None

        if cache is None:
            cache = {
                "cache_version": CACHE_VERSION,
                "entries": {},
                "max_entries": MAX_ENTRIES,
                "eviction_policy": EVICTION_POLICY,
            }

        calculated_at = datetime.now(UTC)
        expires_at = calculated_at + timedelta(seconds=ttl_seconds)

        entry = {
            "cache_key": cache_key,
            "metrics": metrics,
            "calculated_at": calculated_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "last_accessed": calculated_at.isoformat(),
            "ttl_seconds": ttl_seconds,
        }

        cache["entries"][cache_key] = entry

        if len(cache["entries"]) > MAX_ENTRIES:
            _evict_lru_entries(cache)

        with open(CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)

        logger.info(f"Cached metrics: {cache_key} (TTL: {ttl_seconds}s)")
        return True

    except Exception as e:
        logger.error(f"Error saving cache: {e}")
        return False


def _evict_lru_entries(cache: dict) -> None:

    entries = cache.get("entries", {})

    sorted_keys = sorted(
        entries.keys(), key=lambda k: entries[k].get("last_accessed", "")
    )

    while len(entries) > MAX_ENTRIES:
        oldest_key = sorted_keys.pop(0)
        del entries[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key} (LRU policy)")


def invalidate_cache(cache_key: str | None = None) -> bool:

    try:
        if cache_key is None:
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
                logger.info("Cleared entire metrics cache")
            return True

        if not os.path.exists(CACHE_FILE):
            return True

        with open(CACHE_FILE) as f:
            content = f.read().strip()
            if not content:
                return True
            cache = json.loads(content)

        if cache_key in cache.get("entries", {}):
            del cache["entries"][cache_key]

            with open(CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)

            logger.info(f"Invalidated cache entry: {cache_key}")

        return True

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return False


def get_cache_stats() -> dict:

    if not os.path.exists(CACHE_FILE):
        return {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
            "cache_file_size_kb": 0,
            "oldest_entry": None,
            "newest_entry": None,
        }

    try:
        with open(CACHE_FILE) as f:
            content = f.read().strip()
            if not content:
                return {
                    "total_entries": 0,
                    "valid_entries": 0,
                    "expired_entries": 0,
                    "cache_file_size_kb": 0,
                    "oldest_entry": None,
                    "newest_entry": None,
                }
            cache = json.loads(content)

        entries = cache.get("entries", {})
        now = datetime.now(UTC)

        valid_count = 0
        expired_count = 0
        for entry in entries.values():
            expires_at = datetime.fromisoformat(entry["expires_at"])
            if now <= expires_at:
                valid_count += 1
            else:
                expired_count += 1

        calculated_times = [
            entry.get("calculated_at")
            for entry in entries.values()
            if entry.get("calculated_at")
        ]
        oldest = min(calculated_times) if calculated_times else None
        newest = max(calculated_times) if calculated_times else None

        file_size_bytes = os.path.getsize(CACHE_FILE)
        file_size_kb = file_size_bytes / 1024

        return {
            "total_entries": len(entries),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "cache_file_size_kb": round(file_size_kb, 2),
            "oldest_entry": oldest,
            "newest_entry": newest,
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "total_entries": 0,
            "valid_entries": 0,
            "expired_entries": 0,
            "cache_file_size_kb": 0,
            "oldest_entry": None,
            "newest_entry": None,
        }
