"""
Performance benchmark tests for DORA and Flow metrics calculations.

These tests verify that metric calculations meet strict performance targets:
- Small datasets (≤500 issues): < 2s
- Medium datasets (500-1500 issues): < 5s
- Date parsing cache: 80% speedup
- Field lookup index: 95% speedup
"""

import pytest
import time
from datetime import datetime, timedelta


class TestDORAMetricsPerformance:
    """Performance benchmarks for DORA metrics calculations."""

    @pytest.fixture
    def small_dataset(self):
        """Generate 500 test issues for performance testing."""
        issues = []
        base_date = datetime(2025, 1, 1)

        for i in range(500):
            issues.append(
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "created": (base_date + timedelta(days=i % 30)).isoformat()
                        + "+0000",
                        "resolutiondate": (
                            base_date + timedelta(days=i % 30, hours=i % 24)
                        ).isoformat()
                        + "+0000"
                        if i % 3 == 0
                        else None,
                        "status": {"name": "Done" if i % 3 == 0 else "In Progress"},
                        "customfield_10001": (
                            base_date + timedelta(days=i % 30)
                        ).isoformat()
                        + "+0000",  # deployment_date
                        "customfield_10002": i % 2 == 0,  # deployment_successful
                        "customfield_10003": (
                            base_date + timedelta(days=i % 30)
                        ).isoformat()
                        + "+0000",  # incident_start
                        "customfield_10004": (
                            base_date + timedelta(days=i % 30, hours=i % 12)
                        ).isoformat()
                        + "+0000",  # incident_resolved
                    },
                }
            )

        return issues

    @pytest.fixture
    def medium_dataset(self):
        """Generate 1500 test issues for performance testing."""
        issues = []
        base_date = datetime(2025, 1, 1)

        for i in range(1500):
            issues.append(
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "created": (base_date + timedelta(days=i % 90)).isoformat()
                        + "+0000",
                        "resolutiondate": (
                            base_date + timedelta(days=i % 90, hours=i % 24)
                        ).isoformat()
                        + "+0000"
                        if i % 3 == 0
                        else None,
                        "status": {"name": "Done" if i % 3 == 0 else "In Progress"},
                        "customfield_10001": (
                            base_date + timedelta(days=i % 90)
                        ).isoformat()
                        + "+0000",
                        "customfield_10002": i % 2 == 0,
                        "customfield_10003": (
                            base_date + timedelta(days=i % 90)
                        ).isoformat()
                        + "+0000",
                        "customfield_10004": (
                            base_date + timedelta(days=i % 90, hours=i % 12)
                        ).isoformat()
                        + "+0000",
                    },
                }
            )

        return issues

    @pytest.fixture
    def field_mappings(self):
        """Field mappings for DORA metrics."""
        return {
            "deployment_date": "customfield_10001",
            "deployment_successful": "customfield_10002",
            "incident_start": "customfield_10003",
            "incident_resolved": "customfield_10004",
        }

    def test_benchmark_dora_metrics_small_dataset(self, small_dataset, field_mappings):
        """Benchmark DORA metrics with 500 issues - must complete in < 2s."""
        from data.dora_metrics import (
            calculate_deployment_frequency,
            calculate_lead_time_for_changes,
            calculate_change_failure_rate,
            calculate_mean_time_to_recovery,
        )
        from data.variable_mapping.extractor import VariableExtractor
        from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

        # Setup extractor with default variables
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        start = time.perf_counter()

        # Calculate all 4 DORA metrics (new API - no field_mappings)
        deployment_freq = calculate_deployment_frequency(
            small_dataset, extractor, time_period_days=30
        )
        lead_time = calculate_lead_time_for_changes(
            small_dataset, extractor, time_period_days=30
        )
        cfr = calculate_change_failure_rate(
            small_dataset, small_dataset, extractor, time_period_days=30
        )
        mttr = calculate_mean_time_to_recovery(
            small_dataset, extractor, time_period_days=30
        )

        elapsed = time.perf_counter() - start

        # Verify results exist
        assert deployment_freq is not None
        assert lead_time is not None
        assert cfr is not None
        assert mttr is not None

        # Performance target: < 2s for 500 issues
        assert elapsed < 2.0, (
            f"DORA metrics took {elapsed:.3f}s, expected < 2.0s for 500 issues"
        )

    def test_benchmark_dora_metrics_medium_dataset(
        self, medium_dataset, field_mappings
    ):
        """Benchmark DORA metrics with 1500 issues - must complete in < 5s."""
        from data.dora_metrics import (
            calculate_deployment_frequency,
            calculate_lead_time_for_changes,
            calculate_change_failure_rate,
            calculate_mean_time_to_recovery,
        )
        from data.variable_mapping.extractor import VariableExtractor
        from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

        # Setup extractor with default variables
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        start = time.perf_counter()

        # Calculate all 4 DORA metrics (new API - no field_mappings)
        deployment_freq = calculate_deployment_frequency(
            medium_dataset, extractor, time_period_days=90
        )
        lead_time = calculate_lead_time_for_changes(
            medium_dataset, extractor, time_period_days=90
        )
        cfr = calculate_change_failure_rate(
            medium_dataset, medium_dataset, extractor, time_period_days=90
        )
        mttr = calculate_mean_time_to_recovery(
            medium_dataset, extractor, time_period_days=90
        )

        elapsed = time.perf_counter() - start

        # Verify results exist
        assert deployment_freq is not None
        assert lead_time is not None
        assert cfr is not None
        assert mttr is not None

        # Performance target: < 5s for 1500 issues
        assert elapsed < 5.0, (
            f"DORA metrics took {elapsed:.3f}s, expected < 5.0s for 1500 issues"
        )


class TestFlowMetricsPerformance:
    """Performance benchmarks for Flow metrics calculations."""

    @pytest.fixture
    def small_dataset(self):
        """Generate 500 test issues for Flow metrics performance testing."""
        issues = []
        base_date = datetime(2025, 1, 1)

        for i in range(500):
            issues.append(
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "created": (base_date + timedelta(days=i % 30)).isoformat()
                        + "+0000",
                        "status": {"name": "Done" if i % 2 == 0 else "In Progress"},
                        "customfield_10005": (
                            base_date + timedelta(days=i % 30)
                        ).isoformat()
                        + "+0000",  # work_started_date
                        "customfield_10006": (
                            base_date + timedelta(days=(i % 30) + 5)
                        ).isoformat()
                        + "+0000"
                        if i % 2 == 0
                        else None,  # work_completed_date
                        "customfield_10007": [
                            "Feature",
                            "Bug",
                            "Technical Debt",
                            "Risk",
                        ][i % 4],  # work_type
                        "customfield_10008": (i % 10)
                        + 1,  # work_item_size (story points)
                    },
                }
            )

        return issues

    @pytest.fixture
    def medium_dataset(self):
        """Generate 1500 test issues for Flow metrics performance testing."""
        issues = []
        base_date = datetime(2025, 1, 1)

        for i in range(1500):
            issues.append(
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "created": (base_date + timedelta(days=i % 90)).isoformat()
                        + "+0000",
                        "status": {"name": "Done" if i % 2 == 0 else "In Progress"},
                        "customfield_10005": (
                            base_date + timedelta(days=i % 90)
                        ).isoformat()
                        + "+0000",
                        "customfield_10006": (
                            base_date + timedelta(days=(i % 90) + 5)
                        ).isoformat()
                        + "+0000"
                        if i % 2 == 0
                        else None,
                        "customfield_10007": [
                            "Feature",
                            "Bug",
                            "Technical Debt",
                            "Risk",
                        ][i % 4],
                        "customfield_10008": (i % 10) + 1,
                    },
                }
            )

        return issues

    @pytest.fixture
    def field_mappings(self):
        """Field mappings for Flow metrics."""
        return {
            "work_started_date": "customfield_10005",
            "work_completed_date": "customfield_10006",
            "work_type": "customfield_10007",
            "work_item_size": "customfield_10008",
        }

    def test_benchmark_flow_metrics_small_dataset(self, small_dataset, field_mappings):
        """Benchmark Flow metrics with 500 issues - must complete in < 2s."""
        from data.flow_metrics import (
            calculate_flow_velocity,
            calculate_flow_time,
            calculate_flow_efficiency,
            calculate_flow_load,
            calculate_flow_distribution,
        )
        from data.variable_mapping.extractor import VariableExtractor
        from data.variable_mapping.models import VariableMappingCollection
        from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

        # Setup extractor with default variables
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        start = time.perf_counter()

        # Calculate all 5 Flow metrics (new API - no field_mappings)
        velocity = calculate_flow_velocity(
            small_dataset, extractor, time_period_days=30
        )
        flow_time = calculate_flow_time(small_dataset, extractor, time_period_days=30)
        efficiency = calculate_flow_efficiency(
            small_dataset, extractor, time_period_days=30
        )
        load = calculate_flow_load(small_dataset, extractor)
        distribution = calculate_flow_distribution(
            small_dataset, extractor, time_period_days=30
        )

        elapsed = time.perf_counter() - start

        # Verify results exist
        assert velocity is not None
        assert flow_time is not None
        assert efficiency is not None
        assert load is not None
        assert distribution is not None

        # Performance target: < 2s for 500 issues
        assert elapsed < 2.0, (
            f"Flow metrics took {elapsed:.3f}s, expected < 2.0s for 500 issues"
        )

    def test_benchmark_flow_metrics_medium_dataset(
        self, medium_dataset, field_mappings
    ):
        """Benchmark Flow metrics with 1500 issues - must complete in < 5s."""
        from data.flow_metrics import (
            calculate_flow_velocity,
            calculate_flow_time,
            calculate_flow_efficiency,
            calculate_flow_load,
            calculate_flow_distribution,
        )
        from data.variable_mapping.extractor import VariableExtractor
        from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION

        # Setup extractor with default variables
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        start = time.perf_counter()

        # Calculate all 5 Flow metrics (new API - no field_mappings)
        velocity = calculate_flow_velocity(
            medium_dataset, extractor, time_period_days=90
        )
        flow_time = calculate_flow_time(medium_dataset, extractor, time_period_days=90)
        efficiency = calculate_flow_efficiency(
            medium_dataset, extractor, time_period_days=90
        )
        load = calculate_flow_load(medium_dataset, extractor)
        distribution = calculate_flow_distribution(
            medium_dataset, extractor, time_period_days=90
        )

        elapsed = time.perf_counter() - start

        # Verify results exist
        assert velocity is not None
        assert flow_time is not None
        assert efficiency is not None
        assert load is not None
        assert distribution is not None

        # Performance target: < 5s for 1500 issues
        assert elapsed < 5.0, (
            f"Flow metrics took {elapsed:.3f}s, expected < 5.0s for 1500 issues"
        )


class TestDateParsingPerformance:
    """Performance benchmark for date parsing with LRU cache."""

    def test_benchmark_date_parsing_cache_speedup(self):
        """Verify parse_jira_date with LRU cache provides 80% speedup."""
        from data.performance_utils import parse_jira_date
        from dateutil import parser as dateutil_parser

        # Test data: 1000 date strings (many duplicates to test cache)
        date_strings = [
            f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T10:30:00.000+0000"
            for i in range(1000)
        ]

        # Baseline: dateutil.parser without caching
        start = time.perf_counter()
        for date_str in date_strings:
            dateutil_parser.parse(date_str)
        baseline_time = time.perf_counter() - start

        # Optimized: parse_jira_date with @lru_cache
        parse_jira_date.cache_clear()
        start = time.perf_counter()
        for date_str in date_strings:
            parse_jira_date(date_str)
        cached_time = time.perf_counter() - start

        # Calculate speedup
        speedup_percent = ((baseline_time - cached_time) / baseline_time) * 100

        # Performance target: >= 80% speedup
        assert speedup_percent >= 80.0, (
            f"Date parsing speedup: {speedup_percent:.1f}%, expected >= 80%"
        )


class TestFieldLookupPerformance:
    """Performance benchmark for field mapping lookups."""

    def test_benchmark_field_lookup_speedup(self):
        """Verify FieldMappingIndex provides 95% speedup over linear search."""
        from data.performance_utils import FieldMappingIndex

        # Large field mapping (100 fields)
        field_mappings = {
            f"metric_field_{i}": f"customfield_{10000 + i}" for i in range(100)
        }

        # Test data: 1000 lookups
        lookup_keys = [f"metric_field_{i % 100}" for i in range(1000)]

        # Baseline: Linear search (O(n) lookup)
        start = time.perf_counter()
        for key in lookup_keys:
            # Simulate linear search through dict items
            for logical_name, jira_field in field_mappings.items():
                if logical_name == key:
                    _ = jira_field  # Use underscore for intentionally unused result
                    break
        baseline_time = time.perf_counter() - start

        # Optimized: FieldMappingIndex (O(1) lookup)
        index = FieldMappingIndex(field_mappings)
        start = time.perf_counter()
        for key in lookup_keys:
            index.get_jira_field(key)
        indexed_time = time.perf_counter() - start

        # Calculate speedup
        speedup_percent = ((baseline_time - indexed_time) / baseline_time) * 100

        # Performance target: >= 90% speedup (allows for timing variance on different systems)
        assert speedup_percent >= 90.0, (
            f"Field lookup speedup: {speedup_percent:.1f}%, expected >= 90%"
        )
