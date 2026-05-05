"""
Unit tests for DORA metrics handling of null/None fixVersions.

Guards against Bug 1: fixVersions stored as None (from JSON null) causing
TypeError when iterating in deployment counting and release map building.

Guards against Bug 3: load_dora_metrics_from_cache using snapshot-aware
week selection instead of only looking backward from today.
"""

from datetime import datetime

from data.fixversion_matcher import (
    build_fixversion_release_map,
    filter_issues_deployed_in_week,
    get_deployment_date_for_issue,
)
from data.metrics._weekly_dora_calc import _calculate_deployment_frequency
from data.metrics._weekly_dora_prep import (
    classify_dora_issues,
    count_deployments_for_week,
    filter_issues_by_deployment_week,
)

###############################################################################
# Helpers
###############################################################################

_FLOW_END_STATUSES = ["Done", "Resolved", "Closed"]

_FV_RELEASE = {"name": "v1.0", "releaseDate": "2026-05-22"}
_FV_NO_DATE = {"name": "v2.0"}


def _flat_issue(
    status: str = "Done",
    fix_versions=None,
    issue_type: str = "Operational Task",
    key: str = "OP-1",
) -> dict:
    """Build a flat (database) format issue."""
    issue = {
        "key": key,
        "issue_key": key,
        "status": status,
        "issue_type": issue_type,
        "fixVersions": fix_versions,
    }
    return issue


def _nested_issue(
    status: str = "Done",
    fix_versions=None,
    key: str = "DEV-1",
) -> dict:
    """Build a nested (JIRA API) format issue."""
    return {
        "key": key,
        "fields": {
            "status": {"name": status},
            "fixVersions": fix_versions,
        },
    }


###############################################################################
# count_deployments_for_week - None fixVersions
###############################################################################


class TestCountDeploymentsNullFixVersions:
    """Guard: count_deployments_for_week must not crash on None fixVersions."""

    def test_flat_issue_with_none_fixversions(self) -> None:
        """Flat issue with fixVersions=None should not raise."""
        issues = [_flat_issue(status="Done", fix_versions=None)]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
        )
        assert result["2026-W21"]["deployments"] == 0

    def test_nested_issue_with_none_fixversions(self) -> None:
        """Nested issue with fixVersions=None should not raise."""
        issues = [_nested_issue(status="Done", fix_versions=None)]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
        )
        assert result["2026-W21"]["deployments"] == 0

    def test_mixed_none_and_valid_fixversions(self) -> None:
        """Issues with None fixVersions mixed with valid ones count correctly."""
        issues = [
            _flat_issue(status="Done", fix_versions=None, key="OP-1"),
            _flat_issue(status="Done", fix_versions=[_FV_RELEASE], key="OP-2"),
        ]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
        )
        assert result["2026-W21"]["deployments"] == 1
        assert "v1.0" in result["2026-W21"]["release_names"]

    def test_empty_list_fixversions(self) -> None:
        """Issues with empty list fixVersions should return 0 deployments."""
        issues = [_flat_issue(status="Done", fix_versions=[])]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
        )
        assert result["2026-W21"]["deployments"] == 0


###############################################################################
# filter_issues_by_deployment_week - None fixVersions
###############################################################################


class TestFilterIssuesByDeploymentWeekNull:
    """Guard: filter_issues_by_deployment_week handles None fixVersions."""

    def test_flat_none_fixversions(self) -> None:
        issues = [_flat_issue(fix_versions=None)]
        result = filter_issues_by_deployment_week(
            issues, datetime(2026, 5, 18), datetime(2026, 5, 25)
        )
        assert result == []

    def test_nested_none_fixversions(self) -> None:
        issues = [_nested_issue(fix_versions=None)]
        result = filter_issues_by_deployment_week(
            issues, datetime(2026, 5, 18), datetime(2026, 5, 25)
        )
        assert result == []


###############################################################################
# build_fixversion_release_map - None fixVersions
###############################################################################


class TestBuildFixversionReleaseMapNull:
    """Guard: build_fixversion_release_map handles None fixVersions."""

    def test_flat_none_fixversions(self) -> None:
        issues = [_flat_issue(status="Done", fix_versions=None)]
        result = build_fixversion_release_map(
            issues, flow_end_statuses=_FLOW_END_STATUSES
        )
        assert result == {}

    def test_nested_none_fixversions(self) -> None:
        issues = [_nested_issue(status="Done", fix_versions=None)]
        result = build_fixversion_release_map(
            issues, flow_end_statuses=_FLOW_END_STATUSES
        )
        assert result == {}

    def test_mixed_none_and_valid(self) -> None:
        """Valid fixVersions should still be picked up."""
        issues = [
            _flat_issue(status="Done", fix_versions=None, key="OP-1"),
            _flat_issue(status="Done", fix_versions=[_FV_RELEASE], key="OP-2"),
        ]
        result = build_fixversion_release_map(
            issues, flow_end_statuses=_FLOW_END_STATUSES
        )
        assert "v1.0" in result
        assert result["v1.0"] == datetime(2026, 5, 22)


###############################################################################
# get_deployment_date_for_issue - None fixVersions
###############################################################################


class TestGetDeploymentDateNull:
    """Guard: get_deployment_date_for_issue handles None fixVersions."""

    def test_flat_none_fixversions(self) -> None:
        issue = _flat_issue(fix_versions=None)
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = get_deployment_date_for_issue(issue, release_map)
        assert result is None

    def test_nested_none_fixversions(self) -> None:
        issue = _nested_issue(fix_versions=None)
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = get_deployment_date_for_issue(issue, release_map)
        assert result is None

    def test_valid_fixversion_returns_date(self) -> None:
        issue = _flat_issue(fix_versions=[{"name": "v1.0"}])
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = get_deployment_date_for_issue(issue, release_map)
        assert result == datetime(2026, 5, 22)


###############################################################################
# filter_issues_deployed_in_week - None fixVersions
###############################################################################


class TestFilterIssuesDeployedInWeekNull:
    """Guard: filter_issues_deployed_in_week handles None fixVersions."""

    def test_flat_none_fixversions(self) -> None:
        issues = [_flat_issue(fix_versions=None)]
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = filter_issues_deployed_in_week(
            issues, release_map, datetime(2026, 5, 18), datetime(2026, 5, 25)
        )
        assert result == []

    def test_valid_issue_in_week(self) -> None:
        issues = [_flat_issue(fix_versions=[{"name": "v1.0"}])]
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = filter_issues_deployed_in_week(
            issues, release_map, datetime(2026, 5, 18), datetime(2026, 5, 25)
        )
        assert len(result) == 1

    def test_valid_issue_outside_week(self) -> None:
        issues = [_flat_issue(fix_versions=[{"name": "v1.0"}])]
        release_map = {"v1.0": datetime(2026, 5, 22)}
        result = filter_issues_deployed_in_week(
            issues, release_map, datetime(2026, 5, 4), datetime(2026, 5, 11)
        )
        assert result == []


###############################################################################
# count_deployments_for_week - valid_fix_versions filtering
###############################################################################


class TestCountDeploymentsFixVersionFiltering:
    """Guard: fixVersion name must match valid_fix_versions set exactly."""

    def test_matching_fixversion_counted(self) -> None:
        issues = [_flat_issue(status="Done", fix_versions=[_FV_RELEASE])]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
            valid_fix_versions={"v1.0"},
        )
        assert result["2026-W21"]["deployments"] == 1

    def test_non_matching_fixversion_excluded(self) -> None:
        issues = [_flat_issue(status="Done", fix_versions=[_FV_RELEASE])]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
            valid_fix_versions={"v2.0"},  # Does not match v1.0
        )
        assert result["2026-W21"]["deployments"] == 0

    def test_status_filter_excludes_incomplete(self) -> None:
        issues = [_flat_issue(status="In Progress", fix_versions=[_FV_RELEASE])]
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W21",
            datetime(2026, 5, 18),
            datetime(2026, 5, 25),
        )
        assert result["2026-W21"]["deployments"] == 0

    def test_release_date_outside_week_excluded(self) -> None:
        issues = [_flat_issue(status="Done", fix_versions=[_FV_RELEASE])]
        # Week before the release date
        result = count_deployments_for_week(
            issues,
            _FLOW_END_STATUSES,
            "2026-W20",
            datetime(2026, 5, 11),
            datetime(2026, 5, 18),
        )
        assert result["2026-W20"]["deployments"] == 0


###############################################################################
# load_dora_metrics_from_cache - snapshot-aware week selection (Bug 3)
###############################################################################


class TestLoadDoraMetricsWeekSelection:
    """Guard: load_dora_metrics_from_cache uses snapshot weeks, not just today."""

    def test_returns_none_when_no_snapshots(self, monkeypatch) -> None:
        """When no snapshot data exists, returns None."""
        monkeypatch.setattr(
            "data.dora_metrics_calculator.get_metric_snapshot", lambda *a: None
        )
        monkeypatch.setattr("data.metrics_snapshots.load_snapshots", lambda: {})

        from data.dora_metrics_calculator import load_dora_metrics_from_cache

        result = load_dora_metrics_from_cache(n_weeks=4)
        assert result is None

    def test_includes_future_week_with_data(self, monkeypatch) -> None:
        """Weeks with saved DORA data beyond today are included."""
        # Simulate snapshots for a future week (2026-W21 = May 18-24)
        fake_snapshots = {
            "2026-W19": {
                "dora_deployment_frequency": {
                    "deployment_count": 0,
                    "release_count": 0,
                    "timestamp": "2026-05-05T10:00:00",
                },
            },
            "2026-W20": {
                "dora_deployment_frequency": {
                    "deployment_count": 0,
                    "release_count": 0,
                    "timestamp": "2026-05-12T10:00:00",
                },
            },
            "2026-W21": {
                "dora_deployment_frequency": {
                    "deployment_count": 2,
                    "release_count": 1,
                    "release_names": ["v1.0"],
                    "timestamp": "2026-05-22T10:00:00",
                },
            },
        }

        monkeypatch.setattr(
            "data.metrics_snapshots.load_snapshots",
            lambda: fake_snapshots,
        )

        def mock_get_snapshot(week_label, metric_name):
            return fake_snapshots.get(week_label, {}).get(metric_name)

        monkeypatch.setattr(
            "data.dora_metrics_calculator.get_metric_snapshot",
            mock_get_snapshot,
        )

        from data.dora_metrics_calculator import load_dora_metrics_from_cache

        result = load_dora_metrics_from_cache(n_weeks=12)
        assert result is not None
        # W21 should be in weekly_labels
        labels = result["deployment_frequency"]["weekly_labels"]
        assert "2026-W21" in labels
        # Deployment count from W21 should be included
        values = result["deployment_frequency"]["weekly_values"]
        w21_idx = labels.index("2026-W21")
        assert values[w21_idx] == 2


###############################################################################
# classify_dora_issues - resilient issue type matching
###############################################################################


class TestClassifyDoraIssuesTypeMatching:
    """Guard: issue type matching is case-insensitive and whitespace-tolerant."""

    def test_matches_operational_task_case_insensitively(self) -> None:
        app_settings = {
            "devops_task_types": ["Operational Task"],
            "bug_types": ["Bug"],
            "production_environment_values": ["production"],
            "field_mappings": {"dora": {"affected_environment": ""}},
        }
        all_issues_raw = [
            {
                "key": "OPS-1",
                "fields": {
                    "issuetype": {"name": " operational task "},
                    "fixVersions": [{"name": "R_20260422_www.drei.at_1"}],
                },
            }
        ]
        all_issues = [
            {
                "key": "DEV-1",
                "fields": {
                    "issuetype": {"name": "Story"},
                    "fixVersions": [{"name": "R_20260422_www.drei.at_1"}],
                },
            }
        ]

        operational_tasks, development_issues, production_bugs = classify_dora_issues(
            all_issues,
            all_issues_raw,
            app_settings,
        )

        assert len(operational_tasks) == 1
        assert len(development_issues) == 1
        assert production_bugs == []


###############################################################################
# _calculate_deployment_frequency - release-map fallback
###############################################################################


class TestDeploymentFrequencyFallback:
    """Guard: deployment count falls back to release map when no op tasks loaded."""

    def test_release_map_fallback_when_no_operational_tasks(self) -> None:
        week_start = datetime(2026, 4, 20)
        week_end = datetime(2026, 4, 27)
        release_map = {
            "R_20260422_www.drei.at_1": datetime(2026, 4, 22),
            "R_20260415_www.drei.at_1": datetime(2026, 4, 15),
        }

        result = _calculate_deployment_frequency(
            operational_tasks=[],
            flow_end_statuses=_FLOW_END_STATUSES,
            week_label="2026-W17",
            week_start=week_start,
            week_end=week_end,
            development_fix_versions={"R_20260422_www.drei.at_1"},
            fixversion_release_map=release_map,
        )

        assert result["deployment_count"] == 1
        assert result["release_count"] == 1
        assert result["release_names"] == ["R_20260422_www.drei.at_1"]
