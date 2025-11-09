"""
Unit tests for data/cache_manager.py

Tests the cache management system for JIRA data including:
- Cache key generation from query parameters
- Cache validation (expiration, config changes)
- Cache save/load operations
- Cache invalidation triggers
"""

import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta

# Import all cache manager functions
from data.cache_manager import (
    generate_cache_key,
    load_cache_with_validation,
    save_cache,
    invalidate_cache,
    CacheInvalidationTrigger,
)


class TestCacheKeyGeneration:
    """Test cache key generation consistency and changes"""

    def test_generate_cache_key_consistency(self):
        """Test that same inputs produce same cache key"""
        # Given
        jql_query = "project = TEST AND status = Done"
        field_mappings = {
            "deployment_date": "customfield_10001",
            "points": "customfield_10002",
        }
        time_period = 30

        # When
        key1 = generate_cache_key(jql_query, field_mappings, time_period)
        key2 = generate_cache_key(jql_query, field_mappings, time_period)

        # Then
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5 hash length

    def test_generate_cache_key_changes_on_input(self):
        """Test that different inputs produce different cache keys"""
        # Given
        jql_query1 = "project = TEST"
        jql_query2 = "project = PROD"
        field_mappings = {"deployment_date": "customfield_10001"}
        time_period = 30

        # When
        key1 = generate_cache_key(jql_query1, field_mappings, time_period)
        key2 = generate_cache_key(jql_query2, field_mappings, time_period)

        # Then
        assert key1 != key2


class TestCacheValidation:
    """Test cache loading and validation logic"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create isolated temporary cache directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_load_cache_with_validation_success(self, temp_cache_dir):
        """Test loading valid cache with fresh timestamp and matching config"""
        # Given
        cache_key = "test_cache_key_123"
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")

        cache_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "config_hash": "abc123",
                "cache_key": cache_key,
            },
            "data": [{"key": "TEST-1", "summary": "Test issue"}],
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # When
        is_valid, loaded_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash="abc123",
            max_age_hours=24,
            cache_dir=temp_cache_dir,
        )

        # Then
        assert is_valid is True
        assert loaded_data == cache_data["data"]

    def test_load_cache_with_validation_expired(self, temp_cache_dir):
        """Test that expired cache is marked invalid"""
        # Given
        cache_key = "test_cache_key_456"
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")

        # Create cache with old timestamp (25 hours ago)
        old_timestamp = (datetime.now() - timedelta(hours=25)).isoformat()
        cache_data = {
            "metadata": {
                "timestamp": old_timestamp,
                "config_hash": "abc123",
                "cache_key": cache_key,
            },
            "data": [{"key": "TEST-1"}],
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # When
        is_valid, loaded_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash="abc123",
            max_age_hours=24,
            cache_dir=temp_cache_dir,
        )

        # Then
        assert is_valid is False
        assert loaded_data is None

    def test_load_cache_with_validation_config_mismatch(self, temp_cache_dir):
        """Test that cache with different config hash is invalid"""
        # Given
        cache_key = "test_cache_key_789"
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")

        cache_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "config_hash": "old_hash_xyz",
                "cache_key": cache_key,
            },
            "data": [{"key": "TEST-1"}],
        }

        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

        # When
        is_valid, loaded_data = load_cache_with_validation(
            cache_key=cache_key,
            config_hash="new_hash_abc",  # Different hash
            max_age_hours=24,
            cache_dir=temp_cache_dir,
        )

        # Then
        assert is_valid is False
        assert loaded_data is None


class TestCacheSaveOperations:
    """Test cache save functionality"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create isolated temporary cache directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_save_cache_creates_file(self, temp_cache_dir):
        """Test that save_cache creates a file in cache directory"""
        # Given
        cache_key = "test_save_key_001"
        data = [{"key": "TEST-1", "summary": "Test issue"}]
        config_hash = "save_test_hash"

        # When
        save_cache(
            cache_key=cache_key,
            data=data,
            config_hash=config_hash,
            cache_dir=temp_cache_dir,
        )

        # Then
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
        assert os.path.exists(cache_file)

    def test_save_cache_includes_metadata(self, temp_cache_dir):
        """Test that saved cache includes all required metadata"""
        # Given
        cache_key = "test_save_key_002"
        data = [{"key": "TEST-2"}]
        config_hash = "metadata_test_hash"

        # When
        save_cache(
            cache_key=cache_key,
            data=data,
            config_hash=config_hash,
            cache_dir=temp_cache_dir,
        )

        # Then
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")
        with open(cache_file, "r") as f:
            saved_cache = json.load(f)

        assert "metadata" in saved_cache
        assert "data" in saved_cache
        assert saved_cache["metadata"]["cache_key"] == cache_key
        assert saved_cache["metadata"]["config_hash"] == config_hash
        assert "timestamp" in saved_cache["metadata"]
        assert saved_cache["data"] == data


class TestCacheInvalidation:
    """Test cache invalidation operations"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create isolated temporary cache directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    def test_invalidate_cache_deletes_file(self, temp_cache_dir):
        """Test that invalidate_cache removes cache file"""
        # Given
        cache_key = "test_invalidate_key_001"
        cache_file = os.path.join(temp_cache_dir, f"{cache_key}.json")

        # Create cache file
        with open(cache_file, "w") as f:
            json.dump({"data": []}, f)

        assert os.path.exists(cache_file)

        # When
        invalidate_cache(cache_key=cache_key, cache_dir=temp_cache_dir)

        # Then
        assert not os.path.exists(cache_file)


class TestCacheInvalidationTriggers:
    """Test automatic cache invalidation triggers"""

    def test_cache_invalidation_trigger_detects_jql_changes(self):
        """Test that JQL query changes trigger invalidation"""
        # Given
        old_config = {"jql_query": "project = TEST", "fields": "key"}
        new_config = {"jql_query": "project = PROD", "fields": "key"}

        # When
        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        # Then
        assert should_invalidate is True

    def test_cache_invalidation_trigger_detects_field_changes(self):
        """Test that field mapping changes trigger invalidation"""
        # Given
        old_config = {
            "jql_query": "project = TEST",
            "field_mappings": {"deployment_date": "customfield_10001"},
        }
        new_config = {
            "jql_query": "project = TEST",
            "field_mappings": {"deployment_date": "customfield_10002"},
        }

        # When
        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        # Then
        assert should_invalidate is True

    def test_cache_invalidation_trigger_detects_period_changes(self):
        """Test that time period changes trigger invalidation"""
        # Given
        old_config = {"jql_query": "project = TEST", "time_period": 30}
        new_config = {"jql_query": "project = TEST", "time_period": 90}

        # When
        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        # Then
        assert should_invalidate is True
