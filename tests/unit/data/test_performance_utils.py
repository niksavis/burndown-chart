"""
Unit tests for performance utilities module.

Tests the @log_performance decorator, CalculationContext, FieldMappingIndex,
parse_jira_date with LRU cache, and PerformanceTimer context manager.
"""

import logging
import time

import pytest

from data.performance_utils import (
    CalculationContext,
    FieldMappingIndex,
    PerformanceTimer,
    log_performance,
    parse_jira_date,
)


class TestLogPerformanceDecorator:
    """Test the @log_performance decorator."""

    def test_log_performance_decorator_logs_duration(self, caplog):
        """Test that @log_performance logs function execution duration."""

        @log_performance
        def slow_function():
            time.sleep(0.1)
            return "result"

        with caplog.at_level(logging.INFO):
            result = slow_function()

        assert result == "result"
        assert any("slow_function" in record.message for record in caplog.records)
        assert any(
            "duration" in record.message.lower()
            or "completed" in record.message.lower()
            for record in caplog.records
        )

    def test_log_performance_decorator_logs_errors(self, caplog):
        """Test that @log_performance logs errors with stack traces."""

        @log_performance
        def failing_function():
            raise ValueError("Test error")

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                failing_function()

        assert any(
            "error" in record.message.lower() or "failed" in record.message.lower()
            for record in caplog.records
        )
        assert any("ValueError" in record.message for record in caplog.records)


class TestCalculationContext:
    """Test the CalculationContext class for shared filtering."""

    def test_calculation_context_caches_filters(self):
        """Test that CalculationContext caches filtered results."""
        # Sample issues data
        issues = [
            {
                "key": "TEST-1",
                "fields": {"status": {"name": "Done"}, "created": "2025-01-01"},
            },
            {
                "key": "TEST-2",
                "fields": {"status": {"name": "In Progress"}, "created": "2025-01-02"},
            },
            {
                "key": "TEST-3",
                "fields": {"status": {"name": "Done"}, "created": "2025-01-03"},
            },
        ]

        context = CalculationContext(issues)

        # First call - should compute
        done_issues_1 = context.get_filtered_issues(
            lambda issue: issue["fields"]["status"]["name"] == "Done"
        )
        assert len(done_issues_1) == 2

        # Second call with same filter - should return cached
        done_issues_2 = context.get_filtered_issues(
            lambda issue: issue["fields"]["status"]["name"] == "Done"
        )
        assert done_issues_1 is done_issues_2  # Same object reference

    def test_calculation_context_cache_hit_performance(self):
        """Test that cache hits are significantly faster than computing."""
        # Large dataset
        issues = [
            {"key": f"TEST-{i}", "fields": {"priority": i % 3}} for i in range(1000)
        ]
        context = CalculationContext(issues)

        # First call - compute
        start = time.perf_counter()
        result_1 = context.get_filtered_issues(
            lambda issue: issue["fields"]["priority"] == 0
        )
        compute_time = time.perf_counter() - start

        # Second call - cached
        start = time.perf_counter()
        result_2 = context.get_filtered_issues(
            lambda issue: issue["fields"]["priority"] == 0
        )
        cache_time = time.perf_counter() - start

        assert len(result_1) == len(result_2)
        assert cache_time < compute_time / 10  # Cache should be >10x faster


class TestFieldMappingIndex:
    """Test the FieldMappingIndex class for O(1) field lookups."""

    def test_field_mapping_index_bidirectional(self):
        """Test bidirectional field mapping lookups."""
        field_mappings = {
            "deployment_date": "customfield_10001",
            "flow_item_type": "customfield_10002",
            "work_type": "customfield_10003",
        }

        index = FieldMappingIndex(field_mappings)

        # Forward lookup (logical name -> JIRA field)
        assert index.get_jira_field("deployment_date") == "customfield_10001"
        assert index.get_jira_field("work_type") == "customfield_10003"

        # Reverse lookup (JIRA field -> logical name)
        assert index.get_logical_name("customfield_10001") == "deployment_date"
        assert index.get_logical_name("customfield_10003") == "work_type"

        # Non-existent lookups
        assert index.get_jira_field("nonexistent") is None
        assert index.get_logical_name("customfield_99999") is None

    def test_field_mapping_index_o1_complexity(self):
        """Test that field lookups are O(1) using dict-based index."""
        # Large field mapping set
        field_mappings = {f"field_{i}": f"customfield_{i}" for i in range(1000)}
        index = FieldMappingIndex(field_mappings)

        # Time 1000 lookups
        start = time.perf_counter()
        for i in range(1000):
            index.get_jira_field(f"field_{i}")
        lookup_time = time.perf_counter() - start

        # Should be very fast (< 0.01s for 1000 O(1) lookups)
        assert lookup_time < 0.01


class TestParseJiraDate:
    """Test the parse_jira_date function with LRU caching."""

    def test_parse_jira_date_caching(self):
        """Test that parse_jira_date caches results using @lru_cache."""
        # Clear cache before test
        parse_jira_date.cache_clear()

        # First call - should parse
        date_str = "2025-01-15T10:30:00.000+0000"
        result_1 = parse_jira_date(date_str)
        cache_info_1 = parse_jira_date.cache_info()

        # Second call with same input - should hit cache
        result_2 = parse_jira_date(date_str)
        cache_info_2 = parse_jira_date.cache_info()

        assert result_1 == result_2
        assert cache_info_2.hits == cache_info_1.hits + 1  # Cache hit increased

    def test_parse_jira_date_formats(self):
        """Test that parse_jira_date handles multiple JIRA date formats."""
        # ISO 8601 with timezone
        date1 = parse_jira_date("2025-01-15T10:30:00.000+0000")
        assert date1 is not None
        assert date1.year == 2025
        assert date1.month == 1
        assert date1.day == 15

        # ISO 8601 without milliseconds
        date2 = parse_jira_date("2025-01-15T10:30:00+0000")
        assert date2 is not None
        assert date2.year == 2025
        assert date2.month == 1

        # Date only
        date3 = parse_jira_date("2025-01-15")
        assert date3 is not None
        assert date3.year == 2025
        assert date3.month == 1
        assert date3.day == 15

        # None input
        assert parse_jira_date(None) is None

        # Invalid format
        assert parse_jira_date("invalid-date") is None


class TestPerformanceTimer:
    """Test the PerformanceTimer context manager."""

    def test_performance_timer_accuracy(self):
        """Test that PerformanceTimer accurately measures elapsed time."""
        timer = PerformanceTimer()
        with timer:
            time.sleep(0.1)

        # Should be approximately 0.1s (allow 0.05s tolerance)
        assert 0.05 < timer.elapsed < 0.15

    def test_performance_timer_context_manager(self, caplog):
        """Test that PerformanceTimer works as context manager with logging."""
        with caplog.at_level(logging.INFO):
            with PerformanceTimer("test_operation") as timer:
                time.sleep(0.05)

        assert timer.elapsed > 0
        # Check if logging occurred
        assert any("test_operation" in record.message for record in caplog.records)
