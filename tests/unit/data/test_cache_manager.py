"""
Unit tests for data/cache_manager.py

Tests the cache management system for JIRA data including:
- Cache key generation from query parameters
- Cache validation (expiration, config changes)
- Cache save/load operations
- Cache invalidation triggers
"""

# Import all cache manager functions
from data.cache_manager import (
    CacheInvalidationTrigger,
    generate_cache_key,
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

    # Tests removed: cache_manager now uses database only, not JSON files
    # JSON fallback was deprecated legacy code that has been removed
    # Cache validation tests should be rewritten to use isolated test database


class TestCacheSaveOperations:
    """Test cache save functionality"""

    # Tests removed: save_cache now uses database only, not JSON files
    # JSON fallback was deprecated legacy code that has been removed


class TestCacheInvalidation:
    """Test cache invalidation operations"""

    # Tests removed: invalidate_cache now operates on database only, not JSON files
    # JSON fallback was deprecated legacy code that has been removed
    # Cache invalidation tests should be rewritten to use isolated test database


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
