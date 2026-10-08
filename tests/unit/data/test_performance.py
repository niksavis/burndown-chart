import time
from datetime import datetime, timedelta

import pytest


class TestDORAMetricsPerformance:
    @pytest.fixture
    def small_dataset(self):
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
                        + "+0000",
                        "customfield_10002": i % 2 == 0,
                        "customfield_10003": (
                            base_date + timedelta(days=i % 30)
                        ).isoformat()
                        + "+0000",
                        "customfield_10004": (
                            base_date + timedelta(days=i % 30, hours=i % 12)
                        ).isoformat()
                        + "+0000",
                    },
                }
            )

        return issues

    @pytest.fixture
    def medium_dataset(self):
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
        return {
            "deployment_date": "customfield_10001",
            "deployment_successful": "customfield_10002",
            "incident_start": "customfield_10003",
            "incident_resolved": "customfield_10004",
        }

    def test_benchmark_dora_metrics_small_dataset(self, small_dataset, field_mappings):
        from data.dora_metrics import (
            calculate_change_failure_rate,
            calculate_deployment_frequency,
            calculate_lead_time_for_changes,
            calculate_mean_time_to_recovery,
        )

        start = time.perf_counter()

        deployment_freq = calculate_deployment_frequency(
            small_dataset, time_period_days=30
        )
        lead_time = calculate_lead_time_for_changes(small_dataset, time_period_days=30)
        cfr = calculate_change_failure_rate(
            small_dataset, small_dataset, time_period_days=30
        )
        mttr = calculate_mean_time_to_recovery(small_dataset, time_period_days=30)

        elapsed = time.perf_counter() - start

        assert deployment_freq is not None
        assert lead_time is not None
        assert cfr is not None
        assert mttr is not None

        assert elapsed < 2.0, (
            f"DORA metrics took {elapsed:.3f}s, expected < 2.0s for 500 issues"
        )

    def test_benchmark_dora_metrics_medium_dataset(
        self, medium_dataset, field_mappings
    ):
        from data.dora_metrics import (
            calculate_change_failure_rate,
            calculate_deployment_frequency,
            calculate_lead_time_for_changes,
            calculate_mean_time_to_recovery,
        )

        start = time.perf_counter()

        deployment_freq = calculate_deployment_frequency(
            medium_dataset, time_period_days=90
        )
        lead_time = calculate_lead_time_for_changes(medium_dataset, time_period_days=90)
        cfr = calculate_change_failure_rate(
            medium_dataset, medium_dataset, time_period_days=90
        )
        mttr = calculate_mean_time_to_recovery(medium_dataset, time_period_days=90)

        elapsed = time.perf_counter() - start

        assert deployment_freq is not None
        assert lead_time is not None
        assert cfr is not None
        assert mttr is not None

        assert elapsed < 5.0, (
            f"DORA metrics took {elapsed:.3f}s, expected < 5.0s for 1500 issues"
        )


class TestFlowMetricsPerformance:
    @pytest.fixture
    def small_dataset(self):
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
    def medium_dataset(self):
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
        return {
            "work_type": "customfield_10007",
            "work_item_size": "customfield_10008",
        }

    def test_benchmark_flow_metrics_small_dataset(self, small_dataset, field_mappings):
        from data.flow_metrics import (
            calculate_flow_distribution,
            calculate_flow_efficiency,
            calculate_flow_load,
            calculate_flow_time,
            calculate_flow_velocity,
        )

        start = time.perf_counter()

        velocity = calculate_flow_velocity(small_dataset, time_period_days=30)
        flow_time = calculate_flow_time(small_dataset, time_period_days=30)
        efficiency = calculate_flow_efficiency(small_dataset, time_period_days=30)
        load = calculate_flow_load(small_dataset)
        distribution = calculate_flow_distribution(small_dataset, time_period_days=30)

        elapsed = time.perf_counter() - start

        assert velocity is not None
        assert flow_time is not None
        assert efficiency is not None
        assert load is not None
        assert distribution is not None

        assert elapsed < 2.0, (
            f"Flow metrics took {elapsed:.3f}s, expected < 2.0s for 500 issues"
        )

    def test_benchmark_flow_metrics_medium_dataset(
        self, medium_dataset, field_mappings
    ):
        from data.flow_metrics import (
            calculate_flow_distribution,
            calculate_flow_efficiency,
            calculate_flow_load,
            calculate_flow_time,
            calculate_flow_velocity,
        )

        start = time.perf_counter()

        velocity = calculate_flow_velocity(medium_dataset, time_period_days=90)
        flow_time = calculate_flow_time(medium_dataset, time_period_days=90)
        efficiency = calculate_flow_efficiency(medium_dataset, time_period_days=90)
        load = calculate_flow_load(medium_dataset)
        distribution = calculate_flow_distribution(medium_dataset, time_period_days=90)

        elapsed = time.perf_counter() - start

        assert velocity is not None
        assert flow_time is not None
        assert efficiency is not None
        assert load is not None
        assert distribution is not None

        assert elapsed < 5.0, (
            f"Flow metrics took {elapsed:.3f}s, expected < 5.0s for 1500 issues"
        )


class TestDateParsingPerformance:
    def test_benchmark_date_parsing_cache_speedup(self):
        from dateutil import parser as dateutil_parser

        from data.performance_utils import parse_jira_date

        date_strings = [
            f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}T10:30:00.000+0000"
            for i in range(1000)
        ]

        start = time.perf_counter()
        for date_str in date_strings:
            dateutil_parser.parse(date_str)
        baseline_time = time.perf_counter() - start

        parse_jira_date.cache_clear()
        start = time.perf_counter()
        for date_str in date_strings:
            parse_jira_date(date_str)
        cached_time = time.perf_counter() - start

        speedup_percent = ((baseline_time - cached_time) / baseline_time) * 100

        assert speedup_percent >= 65.0, (
            f"Date parsing speedup: {speedup_percent:.1f}%, expected >= 65%"
        )


class TestFieldLookupPerformance:
    def test_benchmark_field_lookup_speedup(self):
        from data.performance_utils import FieldMappingIndex

        field_mappings = {
            f"metric_field_{i}": f"customfield_{10000 + i}" for i in range(100)
        }

        lookup_keys = [f"metric_field_{i % 100}" for i in range(1000)]

        start = time.perf_counter()
        for key in lookup_keys:
            for logical_name, jira_field in field_mappings.items():
                if logical_name == key:
                    _ = jira_field
                    break
        baseline_time = time.perf_counter() - start

        index = FieldMappingIndex(field_mappings)
        start = time.perf_counter()
        for key in lookup_keys:
            index.get_jira_field(key)
        indexed_time = time.perf_counter() - start

        speedup_percent = ((baseline_time - indexed_time) / baseline_time) * 100

        assert speedup_percent >= 60.0, (
            f"Field lookup speedup: {speedup_percent:.1f}%, expected >= 60%"
        )
