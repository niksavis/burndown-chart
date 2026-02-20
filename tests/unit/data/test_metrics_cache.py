"""Unit tests for metrics_cache module.

Tests caching functionality with TTL, LRU eviction, and cache invalidation
with proper test isolation using temporary files.
"""

import json
import os
import tempfile
import time
from datetime import datetime
from unittest.mock import patch

import pytest

from data.metrics_cache import (
    CACHE_VERSION,
    generate_cache_key,
    get_cache_stats,
    invalidate_cache,
    load_cached_metrics,
    save_cached_metrics,
)


@pytest.fixture
def temp_cache_file():
    """Create isolated temporary cache file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_metrics():
    """Sample metrics data for testing."""
    return {
        "deployment_frequency": {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "performance_tier": "High",
            "error_state": "success",
        },
        "lead_time_for_changes": {
            "metric_name": "lead_time_for_changes",
            "value": 3.5,
            "unit": "days",
            "performance_tier": "High",
            "error_state": "success",
        },
    }


class TestGenerateCacheKey:
    """Test cache key generation."""

    def test_cache_key_format(self):
        """Test cache key has correct format."""
        key = generate_cache_key("dora", "2025-01-01", "2025-01-31", "a3f5c8d9")

        assert key == "dora_2025-01-01_2025-01-31_a3f5c8d9"
        assert isinstance(key, str)

    def test_different_inputs_produce_different_keys(self):
        """Test different inputs produce unique keys."""
        key1 = generate_cache_key("dora", "2025-01-01", "2025-01-31", "a3f5c8d9")
        key2 = generate_cache_key("flow", "2025-01-01", "2025-01-31", "a3f5c8d9")
        key3 = generate_cache_key("dora", "2025-02-01", "2025-02-28", "a3f5c8d9")
        key4 = generate_cache_key("dora", "2025-01-01", "2025-01-31", "b4e6d1a2")

        assert key1 != key2  # Different metric type
        assert key1 != key3  # Different date range
        assert key1 != key4  # Different field hash


class TestSaveAndLoadCachedMetrics:
    """Test saving and loading metrics from cache."""

    def test_save_and_load_metrics(self, temp_cache_file, sample_metrics):
        """Test saving metrics and loading them back."""
        cache_key = "dora_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save metrics
            result = save_cached_metrics(cache_key, sample_metrics, ttl_seconds=3600)
            assert result is True

            # Load metrics
            loaded_metrics = load_cached_metrics(cache_key)
            assert loaded_metrics is not None
            assert loaded_metrics["deployment_frequency"]["value"] == 45.2
            assert loaded_metrics["lead_time_for_changes"]["value"] == 3.5

    def test_load_nonexistent_key_returns_none(self, temp_cache_file):
        """Test loading non-existent cache key returns None."""
        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            loaded_metrics = load_cached_metrics("nonexistent_key")
            assert loaded_metrics is None

    def test_load_expired_entry_returns_none(self, temp_cache_file, sample_metrics):
        """Test loading expired cache entry returns None."""
        cache_key = "dora_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save with very short TTL
            save_cached_metrics(cache_key, sample_metrics, ttl_seconds=1)

            # Wait for expiration
            time.sleep(1.1)

            # Should return None (expired)
            loaded_metrics = load_cached_metrics(cache_key)
            assert loaded_metrics is None

    def test_cache_version_mismatch_returns_none(self, temp_cache_file, sample_metrics):
        """Test cache version mismatch returns None."""
        cache_key = "dora_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save metrics
            save_cached_metrics(cache_key, sample_metrics)

            # Modify cache version
            with open(temp_cache_file) as f:
                cache = json.load(f)
            cache["cache_version"] = "0.9"
            with open(temp_cache_file, "w") as f:
                json.dump(cache, f)

            # Should return None (version mismatch)
            loaded_metrics = load_cached_metrics(cache_key)
            assert loaded_metrics is None

    def test_multiple_entries_in_cache(self, temp_cache_file, sample_metrics):
        """Test multiple cache entries can coexist."""
        key1 = "dora_2025-01-01_2025-01-31_test123"
        key2 = "flow_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save two different entries
            save_cached_metrics(key1, sample_metrics, ttl_seconds=3600)
            save_cached_metrics(
                key2, {"flow_velocity": {"value": 30}}, ttl_seconds=3600
            )

            # Both should be retrievable
            metrics1 = load_cached_metrics(key1)
            metrics2 = load_cached_metrics(key2)

            assert metrics1 is not None
            assert metrics2 is not None
            assert "deployment_frequency" in metrics1
            assert "flow_velocity" in metrics2


class TestCacheEviction:
    """Test LRU eviction policy."""

    def test_lru_eviction_when_exceeding_max_entries(self, temp_cache_file):
        """Test LRU eviction when cache exceeds MAX_ENTRIES."""
        with (
            patch("data.metrics_cache.CACHE_FILE", temp_cache_file),
            patch("data.metrics_cache.MAX_ENTRIES", 5),
        ):  # Set low limit for testing
            # Add 6 entries (exceeds limit of 5)
            for i in range(6):
                cache_key = f"test_key_{i}"
                metrics = {"test_metric": {"value": i}}
                save_cached_metrics(cache_key, metrics)

                # Small delay to ensure different timestamps
                time.sleep(0.01)

            # First entry should be evicted
            oldest_entry = load_cached_metrics("test_key_0")
            assert oldest_entry is None

            # Newest entries should exist
            newest_entry = load_cached_metrics("test_key_5")
            assert newest_entry is not None


class TestCacheInvalidation:
    """Test cache invalidation."""

    def test_invalidate_specific_key(self, temp_cache_file, sample_metrics):
        """Test invalidating specific cache key."""
        key1 = "dora_2025-01-01_2025-01-31_test123"
        key2 = "flow_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save two entries
            save_cached_metrics(key1, sample_metrics)
            save_cached_metrics(key2, {"flow_velocity": {"value": 30}})

            # Invalidate one key
            result = invalidate_cache(key1)
            assert result is True

            # First should be gone
            metrics1 = load_cached_metrics(key1)
            assert metrics1 is None

            # Second should still exist
            metrics2 = load_cached_metrics(key2)
            assert metrics2 is not None

    def test_invalidate_all_cache(self, temp_cache_file, sample_metrics):
        """Test clearing entire cache."""
        key1 = "dora_2025-01-01_2025-01-31_test123"
        key2 = "flow_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Save two entries
            save_cached_metrics(key1, sample_metrics)
            save_cached_metrics(key2, {"flow_velocity": {"value": 30}})

            # Invalidate all
            result = invalidate_cache(None)
            assert result is True

            # Cache file should be deleted
            assert not os.path.exists(temp_cache_file)

            # Both should return None
            metrics1 = load_cached_metrics(key1)
            metrics2 = load_cached_metrics(key2)
            assert metrics1 is None
            assert metrics2 is None

    def test_invalidate_nonexistent_cache_succeeds(self):
        """Test invalidating non-existent cache file succeeds."""
        # Use non-existent file path
        fake_path = "/tmp/nonexistent_cache_xyz123.json"

        with patch("data.metrics_cache.CACHE_FILE", fake_path):
            result = invalidate_cache(None)
            assert result is True  # Should not raise error


class TestCacheStats:
    """Test cache statistics."""

    def test_stats_for_empty_cache(self):
        """Test stats when cache doesn't exist."""
        with patch("data.metrics_cache.CACHE_FILE", "/tmp/nonexistent.json"):
            stats = get_cache_stats()

            assert stats["total_entries"] == 0
            assert stats["valid_entries"] == 0
            assert stats["expired_entries"] == 0
            assert stats["cache_file_size_kb"] == 0
            assert stats["oldest_entry"] is None
            assert stats["newest_entry"] is None

    def test_stats_with_entries(self, temp_cache_file, sample_metrics):
        """Test stats with cache entries."""
        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Add entries
            save_cached_metrics("key1", sample_metrics, ttl_seconds=3600)
            time.sleep(0.01)
            save_cached_metrics("key2", sample_metrics, ttl_seconds=3600)

            stats = get_cache_stats()

            assert stats["total_entries"] == 2
            assert stats["valid_entries"] == 2
            assert stats["expired_entries"] == 0
            assert stats["cache_file_size_kb"] > 0
            assert stats["oldest_entry"] is not None
            assert stats["newest_entry"] is not None

    def test_stats_with_expired_entries(self, temp_cache_file, sample_metrics):
        """Test stats correctly count expired entries."""
        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            # Add expired entry
            save_cached_metrics("expired_key", sample_metrics, ttl_seconds=1)

            # Add valid entry
            time.sleep(1.1)
            save_cached_metrics("valid_key", sample_metrics, ttl_seconds=3600)

            stats = get_cache_stats()

            assert stats["total_entries"] == 2
            assert stats["valid_entries"] == 1
            assert stats["expired_entries"] == 1


class TestCacheFileStructure:
    """Test cache file structure and format."""

    def test_cache_file_structure(self, temp_cache_file, sample_metrics):
        """Test cache file has correct structure."""
        cache_key = "dora_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            save_cached_metrics(cache_key, sample_metrics)

            # Read and verify structure
            with open(temp_cache_file) as f:
                cache = json.load(f)

            assert "cache_version" in cache
            assert cache["cache_version"] == CACHE_VERSION
            assert "entries" in cache
            assert "max_entries" in cache
            assert "eviction_policy" in cache

            # Check entry structure
            entry = cache["entries"][cache_key]
            assert "cache_key" in entry
            assert "metrics" in entry
            assert "calculated_at" in entry
            assert "expires_at" in entry
            assert "last_accessed" in entry
            assert "ttl_seconds" in entry

    def test_timestamps_are_iso_format(self, temp_cache_file, sample_metrics):
        """Test all timestamps are in ISO 8601 format."""
        cache_key = "dora_2025-01-01_2025-01-31_test123"

        with patch("data.metrics_cache.CACHE_FILE", temp_cache_file):
            save_cached_metrics(cache_key, sample_metrics)

            with open(temp_cache_file) as f:
                cache = json.load(f)

            entry = cache["entries"][cache_key]

            # All timestamps should parse as ISO 8601
            datetime.fromisoformat(entry["calculated_at"])
            datetime.fromisoformat(entry["expires_at"])
            datetime.fromisoformat(entry["last_accessed"])
