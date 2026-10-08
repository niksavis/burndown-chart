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
    def test_log_performance_decorator_logs_duration(self, caplog):

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
    def test_calculation_context_caches_filters(self):
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

        done_issues_1 = context.get_filtered_issues(
            lambda issue: issue["fields"]["status"]["name"] == "Done"
        )
        assert len(done_issues_1) == 2

        done_issues_2 = context.get_filtered_issues(
            lambda issue: issue["fields"]["status"]["name"] == "Done"
        )
        assert done_issues_1 is done_issues_2

    def test_calculation_context_cache_hit_performance(self):
        issues = [
            {"key": f"TEST-{i}", "fields": {"priority": i % 3}} for i in range(1000)
        ]
        context = CalculationContext(issues)

        start = time.perf_counter()
        result_1 = context.get_filtered_issues(
            lambda issue: issue["fields"]["priority"] == 0
        )
        compute_time = time.perf_counter() - start

        start = time.perf_counter()
        result_2 = context.get_filtered_issues(
            lambda issue: issue["fields"]["priority"] == 0
        )
        cache_time = time.perf_counter() - start

        assert len(result_1) == len(result_2)
        assert cache_time < compute_time / 10


class TestFieldMappingIndex:
    def test_field_mapping_index_bidirectional(self):
        field_mappings = {
            "deployment_date": "customfield_10001",
            "flow_item_type": "customfield_10002",
            "work_type": "customfield_10003",
        }

        index = FieldMappingIndex(field_mappings)

        assert index.get_jira_field("deployment_date") == "customfield_10001"
        assert index.get_jira_field("work_type") == "customfield_10003"

        assert index.get_logical_name("customfield_10001") == "deployment_date"
        assert index.get_logical_name("customfield_10003") == "work_type"

        assert index.get_jira_field("nonexistent") is None
        assert index.get_logical_name("customfield_99999") is None

    def test_field_mapping_index_o1_complexity(self):
        field_mappings = {f"field_{i}": f"customfield_{i}" for i in range(1000)}
        index = FieldMappingIndex(field_mappings)

        start = time.perf_counter()
        for i in range(1000):
            index.get_jira_field(f"field_{i}")
        lookup_time = time.perf_counter() - start

        assert lookup_time < 0.01


class TestParseJiraDate:
    def test_parse_jira_date_caching(self):
        parse_jira_date.cache_clear()

        date_str = "2025-01-15T10:30:00.000+0000"
        result_1 = parse_jira_date(date_str)
        cache_info_1 = parse_jira_date.cache_info()

        result_2 = parse_jira_date(date_str)
        cache_info_2 = parse_jira_date.cache_info()

        assert result_1 == result_2
        assert cache_info_2.hits == cache_info_1.hits + 1

    def test_parse_jira_date_formats(self):
        date1 = parse_jira_date("2025-01-15T10:30:00.000+0000")
        assert date1 is not None
        assert date1.year == 2025
        assert date1.month == 1
        assert date1.day == 15

        date2 = parse_jira_date("2025-01-15T10:30:00+0000")
        assert date2 is not None
        assert date2.year == 2025
        assert date2.month == 1

        date3 = parse_jira_date("2025-01-15")
        assert date3 is not None
        assert date3.year == 2025
        assert date3.month == 1
        assert date3.day == 15

        assert parse_jira_date(None) is None

        assert parse_jira_date("invalid-date") is None


class TestPerformanceTimer:
    def test_performance_timer_accuracy(self):
        timer = PerformanceTimer()
        with timer:
            time.sleep(0.1)

        assert 0.05 < timer.elapsed < 0.15

    def test_performance_timer_context_manager(self, caplog):
        with caplog.at_level(logging.INFO):
            with PerformanceTimer("test_operation") as timer:
                time.sleep(0.05)

        assert timer.elapsed > 0
        assert any("test_operation" in record.message for record in caplog.records)
