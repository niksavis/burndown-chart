from data.cache_manager import (
    CacheInvalidationTrigger,
    generate_cache_key,
)


class TestCacheKeyGeneration:
    def test_generate_cache_key_consistency(self):
        jql_query = "project = TEST AND status = Done"
        field_mappings = {
            "deployment_date": "customfield_10001",
            "points": "customfield_10002",
        }
        time_period = 30

        key1 = generate_cache_key(jql_query, field_mappings, time_period)
        key2 = generate_cache_key(jql_query, field_mappings, time_period)

        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 32

    def test_generate_cache_key_changes_on_input(self):
        jql_query1 = "project = TEST"
        jql_query2 = "project = PROD"
        field_mappings = {"deployment_date": "customfield_10001"}
        time_period = 30

        key1 = generate_cache_key(jql_query1, field_mappings, time_period)
        key2 = generate_cache_key(jql_query2, field_mappings, time_period)

        assert key1 != key2


class TestCacheValidation:
    pass


class TestCacheSaveOperations:
    pass


class TestCacheInvalidation:
    pass


class TestCacheInvalidationTriggers:
    def test_cache_invalidation_trigger_detects_jql_changes(self):
        old_config = {"jql_query": "project = TEST", "fields": "key"}
        new_config = {"jql_query": "project = PROD", "fields": "key"}

        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        assert should_invalidate is True

    def test_cache_invalidation_trigger_detects_field_changes(self):
        old_config = {
            "jql_query": "project = TEST",
            "field_mappings": {"deployment_date": "customfield_10001"},
        }
        new_config = {
            "jql_query": "project = TEST",
            "field_mappings": {"deployment_date": "customfield_10002"},
        }

        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        assert should_invalidate is True

    def test_cache_invalidation_trigger_detects_period_changes(self):
        old_config = {"jql_query": "project = TEST", "time_period": 30}
        new_config = {"jql_query": "project = TEST", "time_period": 90}

        trigger = CacheInvalidationTrigger()
        should_invalidate = trigger.should_invalidate(old_config, new_config)

        assert should_invalidate is True
