"""Unit tests for DORA metrics calculations.

Tests all four DORA metrics with mocked profile configuration matching:
- Profile: Drei Jira Production (p_955acc063e55)
- DevOps Project: RI (Operational Tasks)
- Development Project: A935

Each test is isolated and doesn't require running the app.

DORA Metrics Tested:
1. Deployment Frequency - deployments and releases per time period
2. Lead Time for Changes - time from code commit to deployment
3. Change Failure Rate - percentage of deployments causing issues
4. Mean Time to Recovery - time from incident to resolution/deployment
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch
from typing import Dict, Any, Optional


#######################################################################
# TEST FIXTURES - Mock Profile Configuration
#######################################################################


@pytest.fixture
def mock_profile_config() -> Dict[str, Any]:
    """Mock profile configuration matching Drei Jira Production.

    Based on profile.json:
    - devops_projects: ["RI"]
    - devops_task_types: ["Operational Task"]
    - development_projects: ["A935"]
    - bug_types: ["Bug"]
    - flow_end_statuses: ["Done", "Resolved", "Closed", "Canceled"]
    """
    return {
        "field_mappings": {
            "dora": {
                "deployment_date": "fixVersions",
                "target_environment": "customfield_11309=PROD",
                "code_commit_date": "status:In Progress.DateTime",
                "incident_detected_at": "created",
                "incident_resolved_at": "fixVersions",
                "change_failure": "customfield_12708=Yes",
                "affected_environment": "customfield_11309=PROD",
                "severity_level": "customfield_11000",
            },
            "flow": {
                "flow_item_type": "issuetype",
                "effort_category": "customfield_13204",
                "status": "status",
                "completed_date": "resolutiondate",
            },
            "values": {},
        },
        "flow_end_statuses": ["Done", "Resolved", "Closed", "Canceled"],
        "active_statuses": ["In Progress", "In Review", "Testing"],
        "wip_statuses": [
            "In Progress",
            "In Review",
            "Testing",
            "Ready for Testing",
            "In Deployment",
        ],
        "flow_start_statuses": ["In Progress", "In Review"],
        "bug_types": ["Bug"],
        "devops_task_types": ["Operational Task"],
        "production_environment_values": ["PROD"],
    }


@pytest.fixture
def mock_load_app_settings(mock_profile_config):
    """Patch load_app_settings to return mock profile config."""
    with patch("data.persistence.load_app_settings") as mock:
        mock.return_value = mock_profile_config
        yield mock


#######################################################################
# HELPER FUNCTIONS - Create Test Issues
#######################################################################


def create_operational_task(
    key: str,
    status: str = "Done",
    fix_version_name: str = "Release_2025_01",
    release_date: str = "2025-01-15",
    change_failure: Optional[str] = None,
) -> Dict[str, Any]:
    """Create mock Operational Task issue.

    Operational Tasks are from DevOps projects (RI) and represent deployments.
    They have fixVersions with releaseDates indicating when deployed.

    Args:
        key: Issue key (e.g., "RI-123")
        status: Issue status (e.g., "Done")
        fix_version_name: Name of fixVersion
        release_date: Release date in YYYY-MM-DD format
        change_failure: Value for change_failure field (e.g., "Yes")

    Returns:
        Mock JIRA issue dictionary
    """
    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Operational Task"},
            "status": {"name": status},
            "fixVersions": [
                {
                    "id": f"fv-{fix_version_name}",
                    "name": fix_version_name,
                    "releaseDate": release_date,
                    "released": True,
                }
            ],
            "project": {"key": "RI"},
        },
    }

    if change_failure is not None:
        # Simulates customfield_12708=Yes mapping
        issue["fields"]["customfield_12708"] = {"value": change_failure}

    return issue


def create_development_issue(
    key: str,
    status: str = "Done",
    fix_version_name: str = "Release_2025_01",
    in_progress_timestamp: str = "2025-01-01T10:00:00.000+0000",
    resolution_date: Optional[str] = None,
) -> Dict[str, Any]:
    """Create mock development issue (Task/Story).

    Development issues are from development projects (A935) and represent work items.
    They have changelog for status transitions and fixVersions linking to deployments.

    Args:
        key: Issue key (e.g., "A935-456")
        status: Current status
        fix_version_name: Name of fixVersion (links to Operational Task)
        in_progress_timestamp: When status changed to "In Progress"
        resolution_date: Optional resolution date

    Returns:
        Mock JIRA issue dictionary with changelog
    """
    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Task"},
            "status": {"name": status},
            "fixVersions": [
                {
                    "id": f"fv-{fix_version_name}",
                    "name": fix_version_name,
                }
            ],
            "project": {"key": "A935"},
            "created": "2024-12-15T09:00:00.000+0000",
        },
        "changelog": {
            "histories": [
                {
                    "created": in_progress_timestamp,
                    "items": [
                        {
                            "field": "status",
                            "fromString": "To Do",
                            "toString": "In Progress",
                        }
                    ],
                }
            ]
        },
    }

    if resolution_date:
        issue["fields"]["resolutiondate"] = resolution_date

    return issue


def create_bug_issue(
    key: str,
    status: str = "Done",
    fix_version_name: Optional[str] = None,
    created: str = "2025-01-10T08:00:00.000+0000",
    resolution_date: Optional[str] = None,
    affected_environment: str = "PROD",
) -> Dict[str, Any]:
    """Create mock Bug issue.

    Bugs are from development projects with bug_types: ["Bug"].
    They have affected_environment to filter for production incidents.

    Args:
        key: Issue key (e.g., "A935-789")
        status: Current status
        fix_version_name: Optional fixVersion (for deployment-based MTTR)
        created: When bug was created (incident detected)
        resolution_date: When bug was resolved
        affected_environment: Environment value (e.g., "PROD")

    Returns:
        Mock JIRA issue dictionary
    """
    issue = {
        "key": key,
        "fields": {
            "issuetype": {"name": "Bug"},
            "status": {"name": status},
            "project": {"key": "A935"},
            "created": created,
            # Simulates customfield_11309=PROD mapping
            "customfield_11309": {"value": affected_environment},
        },
    }

    if fix_version_name:
        issue["fields"]["fixVersions"] = [
            {
                "id": f"fv-{fix_version_name}",
                "name": fix_version_name,
            }
        ]

    if resolution_date:
        issue["fields"]["resolutiondate"] = resolution_date

    return issue


#######################################################################
# TEST CLASS: Deployment Frequency
#######################################################################


class TestDeploymentFrequency:
    """Test Deployment Frequency metric calculation.

    Measures how often code is deployed to production:
    - Deployments: Count of Operational Tasks with fixVersion.releaseDate
    - Releases: Count of DISTINCT fixVersions with releaseDate
    """

    def test_deployment_frequency_basic_calculation(self, mock_load_app_settings):
        """Test basic deployment frequency calculation.

        Given: 5 Operational Tasks with 3 distinct releases over 30 days
        Expected: ~1.17 deployments/week, 0.7 releases/week
        """
        from data.dora_metrics import calculate_deployment_frequency

        # Create 5 operational tasks with 3 distinct releases
        issues = [
            create_operational_task(
                "RI-1", fix_version_name="Release_1", release_date="2025-01-05"
            ),
            create_operational_task(
                "RI-2", fix_version_name="Release_1", release_date="2025-01-05"
            ),
            create_operational_task(
                "RI-3", fix_version_name="Release_2", release_date="2025-01-15"
            ),
            create_operational_task(
                "RI-4", fix_version_name="Release_3", release_date="2025-01-25"
            ),
            create_operational_task(
                "RI-5", fix_version_name="Release_3", release_date="2025-01-25"
            ),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        # Verify no error
        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )

        # Verify counts
        assert result["deployment_count"] == 5, "Should count 5 deployments"
        assert result["release_count"] == 3, "Should count 3 distinct releases"
        assert set(result["release_names"]) == {"Release_1", "Release_2", "Release_3"}

        # Verify frequencies (5 deployments / 30 days * 7 = 1.17/week)
        assert result["deployments_per_week"] == pytest.approx(5 / 30 * 7, rel=0.01)
        assert result["releases_per_week"] == pytest.approx(3 / 30 * 7, rel=0.01)

        # Verify performance tier is set
        assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_deployment_frequency_no_issues(self, mock_load_app_settings):
        """Test deployment frequency with no issues."""
        from data.dora_metrics import calculate_deployment_frequency

        result = calculate_deployment_frequency(
            issues=[],
            time_period_days=30,
        )

        assert result["error_state"] == "no_data"
        assert "No issues" in result["error_message"]

    def test_deployment_frequency_incomplete_issues_excluded(
        self, mock_load_app_settings
    ):
        """Test that incomplete issues are excluded from count."""
        from data.dora_metrics import calculate_deployment_frequency

        issues = [
            create_operational_task(
                "RI-1", status="Done", fix_version_name="Release_1"
            ),
            create_operational_task(
                "RI-2", status="In Progress", fix_version_name="Release_1"
            ),  # Incomplete
            create_operational_task(
                "RI-3", status="Done", fix_version_name="Release_2"
            ),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        assert result["deployment_count"] == 2, "Should only count completed tasks"

    def test_deployment_frequency_no_release_date_excluded(
        self, mock_load_app_settings
    ):
        """Test that issues without releaseDate are excluded."""
        from data.dora_metrics import calculate_deployment_frequency

        # Create issue without releaseDate
        issue_no_release = {
            "key": "RI-1",
            "fields": {
                "issuetype": {"name": "Operational Task"},
                "status": {"name": "Done"},
                "fixVersions": [
                    {
                        "id": "fv-1",
                        "name": "No-Release-Date",
                        # No releaseDate!
                    }
                ],
            },
        }

        issues = [
            issue_no_release,
            create_operational_task("RI-2", fix_version_name="Release_1"),
        ]

        result = calculate_deployment_frequency(
            issues=issues,
            time_period_days=30,
        )

        assert result["deployment_count"] == 1, (
            "Should only count issues with releaseDate"
        )

    def test_deployment_frequency_performance_tiers(self, mock_load_app_settings):
        """Test performance tier classification."""
        from data.dora_metrics import calculate_deployment_frequency

        # Elite: Multiple per day (28 deployments over 7 days = 4/day)
        elite_issues = [
            create_operational_task(f"RI-{i}", fix_version_name=f"R{i}")
            for i in range(28)
        ]
        result = calculate_deployment_frequency(elite_issues, time_period_days=7)
        assert result["performance_tier"] == "elite"

        # Low: Less than monthly (1 deployment over 60 days)
        low_issues = [create_operational_task("RI-1")]
        result = calculate_deployment_frequency(low_issues, time_period_days=60)
        assert result["performance_tier"] == "low"


#######################################################################
# TEST CLASS: Lead Time for Changes
#######################################################################


class TestLeadTimeForChanges:
    """Test Lead Time for Changes metric calculation.

    Measures time from code commit (status:In Progress) to production deployment
    (fixVersion.releaseDate from Operational Task).
    """

    @pytest.fixture
    def fixversion_release_map(self) -> Dict[str, datetime]:
        """Create fixVersion → releaseDate map from Operational Tasks."""
        return {
            "Release_2025_01": datetime(2025, 1, 15, 0, 0, tzinfo=timezone.utc),
            "Release_2025_02": datetime(2025, 2, 1, 0, 0, tzinfo=timezone.utc),
        }

    def test_lead_time_basic_calculation(
        self, mock_load_app_settings, fixversion_release_map
    ):
        """Test basic lead time calculation.

        Given: 2 development issues with known In Progress dates and deployment dates
        Expected: Average lead time calculated correctly
        """
        from data.dora_metrics import calculate_lead_time_for_changes

        # Issue 1: In Progress Jan 5 → Deployed Jan 15 = 10 days
        # Issue 2: In Progress Jan 10 → Deployed Jan 15 = 5 days
        # Average: 7.5 days
        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Release_2025_01",
                in_progress_timestamp="2025-01-05T10:00:00.000+0000",
            ),
            create_development_issue(
                "A935-2",
                fix_version_name="Release_2025_01",
                in_progress_timestamp="2025-01-10T10:00:00.000+0000",
            ),
        ]

        result = calculate_lead_time_for_changes(
            issues=issues,
            time_period_days=30,
            fixversion_release_map=fixversion_release_map,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["sample_count"] == 2
        # Average should be around 7.5 days (10 + 5) / 2
        assert result["value"] == pytest.approx(7.5, rel=0.1)
        assert result["unit"] == "days"
        assert result["performance_tier"] in ["elite", "high", "medium", "low"]

    def test_lead_time_no_matching_fixversion(self, mock_load_app_settings):
        """Test lead time when dev issues have no matching fixVersion in release map."""
        from data.dora_metrics import calculate_lead_time_for_changes

        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Unknown_Release",  # Not in release map
            )
        ]

        # Empty release map - no Operational Tasks with this fixVersion
        result = calculate_lead_time_for_changes(
            issues=issues,
            fixversion_release_map={},
        )

        assert result["error_state"] == "no_data"
        # When release map is empty, fallback to issue's own fixVersions (legacy)
        # which will fail with "missing deployment" if no releaseDate
        assert (
            "missing deployment" in result["error_message"].lower()
            or "no fixversion match" in result["error_message"].lower()
        )

    def test_lead_time_missing_in_progress_timestamp(
        self, mock_load_app_settings, fixversion_release_map
    ):
        """Test lead time when issue has no In Progress transition."""
        from data.dora_metrics import calculate_lead_time_for_changes

        # Issue without changelog (no In Progress transition)
        issue = {
            "key": "A935-1",
            "fields": {
                "status": {"name": "Done"},
                "fixVersions": [{"name": "Release_2025_01"}],
            },
            "changelog": {"histories": []},  # Empty changelog
        }

        result = calculate_lead_time_for_changes(
            issues=[issue],
            fixversion_release_map=fixversion_release_map,
        )

        assert result["error_state"] == "no_data"
        assert "missing start" in result["error_message"].lower()

    def test_lead_time_hours_unit_for_short_times(self, mock_load_app_settings):
        """Test that short lead times are displayed in hours."""
        from data.dora_metrics import calculate_lead_time_for_changes

        # Same day deployment (12 hours lead time)
        release_map = {
            "Release_Quick": datetime(2025, 1, 1, 22, 0, tzinfo=timezone.utc),
        }
        issues = [
            create_development_issue(
                "A935-1",
                fix_version_name="Release_Quick",
                in_progress_timestamp="2025-01-01T10:00:00.000+0000",  # 12 hours before
            )
        ]

        result = calculate_lead_time_for_changes(
            issues=issues,
            fixversion_release_map=release_map,
        )

        assert result["unit"] == "hours"
        assert result["value"] == pytest.approx(12, rel=0.1)
        assert result["performance_tier"] == "elite"  # < 1 day


#######################################################################
# TEST CLASS: Change Failure Rate
#######################################################################


class TestChangeFailureRate:
    """Test Change Failure Rate metric calculation.

    Measures percentage of deployments that caused a change failure.
    Uses change_failure field (customfield_12708=Yes) to identify failures.
    """

    def test_cfr_basic_calculation(self, mock_load_app_settings):
        """Test basic CFR calculation.

        Given: 5 deployments, 2 with change_failure=Yes
        Expected: 40% failure rate
        """
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="No"),
            create_operational_task("RI-3", change_failure="Yes"),
            create_operational_task("RI-4", change_failure="No"),
            create_operational_task("RI-5", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],  # Not used in current implementation
            time_period_days=30,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["total_deployments"] == 5
        assert result["failed_deployments"] == 2
        assert result["value"] == pytest.approx(40.0, rel=0.01)
        assert result["unit"] == "%"

    def test_cfr_zero_failures(self, mock_load_app_settings):
        """Test CFR when no failures."""
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="No"),
            create_operational_task("RI-2", change_failure="No"),
            create_operational_task("RI-3", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["value"] == 0.0
        assert result["performance_tier"] == "elite"  # 0% is elite

    def test_cfr_all_failures(self, mock_load_app_settings):
        """Test CFR when all deployments fail."""
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="Yes"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["value"] == 100.0
        assert result["performance_tier"] == "low"

    def test_cfr_release_tracking(self, mock_load_app_settings):
        """Test that CFR tracks both deployments and releases."""
        from data.dora_metrics import calculate_change_failure_rate

        # 4 deployments across 2 releases, 1 release has failure
        issues = [
            create_operational_task(
                "RI-1", fix_version_name="R1", change_failure="Yes"
            ),
            create_operational_task("RI-2", fix_version_name="R1", change_failure="No"),
            create_operational_task("RI-3", fix_version_name="R2", change_failure="No"),
            create_operational_task("RI-4", fix_version_name="R2", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["total_deployments"] == 4
        assert result["failed_deployments"] == 1
        assert result["total_releases"] == 2
        assert result["failed_releases"] == 1  # R1 had a failure
        assert "R1" in result["failed_release_names"]

    def test_cfr_incomplete_issues_excluded(self, mock_load_app_settings):
        """Test that incomplete issues are excluded from CFR."""
        from data.dora_metrics import calculate_change_failure_rate

        issues = [
            create_operational_task("RI-1", status="Done", change_failure="Yes"),
            create_operational_task(
                "RI-2", status="In Progress", change_failure="Yes"
            ),  # Excluded
            create_operational_task("RI-3", status="Done", change_failure="No"),
        ]

        result = calculate_change_failure_rate(
            deployment_issues=issues,
            incident_issues=[],
        )

        assert result["total_deployments"] == 2
        assert result["failed_deployments"] == 1
        assert result["value"] == 50.0

    def test_cfr_performance_tiers(self, mock_load_app_settings):
        """Test CFR performance tier classification."""
        from data.dora_metrics import calculate_change_failure_rate

        # Elite: 0-15%
        issues = [create_operational_task(f"RI-{i}") for i in range(10)]
        issues[0]["fields"]["customfield_12708"] = {"value": "Yes"}  # 10%
        result = calculate_change_failure_rate(issues, [])
        assert result["performance_tier"] == "elite"

        # Low: > 45%
        issues = [
            create_operational_task("RI-1", change_failure="Yes"),
            create_operational_task("RI-2", change_failure="Yes"),
        ]
        result = calculate_change_failure_rate(issues, [])
        assert result["performance_tier"] == "low"


#######################################################################
# TEST CLASS: Mean Time to Recovery
#######################################################################


class TestMeanTimeToRecovery:
    """Test Mean Time to Recovery (MTTR) metric calculation.

    Measures time from incident creation to resolution/deployment.

    Two modes:
    - incident_resolved_at: "resolutiondate" → Bug created → Bug resolved
    - incident_resolved_at: "fixVersions" → Bug created → Bug deployed
    """

    @pytest.fixture
    def fixversion_release_map(self) -> Dict[str, datetime]:
        """Create fixVersion → releaseDate map for deployment-based MTTR."""
        return {
            "Hotfix_2025_01": datetime(2025, 1, 12, 10, 0, tzinfo=timezone.utc),
        }

    def test_mttr_resolution_mode(self, mock_load_app_settings):
        """Test MTTR using resolutiondate mode (team fix time).

        Bug created → Bug resolved
        """
        from data.dora_metrics import calculate_mean_time_to_recovery

        # Override profile to use resolutiondate
        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        # Bug 1: Created Jan 10 08:00, Resolved Jan 10 20:00 = 12 hours
        # Bug 2: Created Jan 10 08:00, Resolved Jan 11 08:00 = 24 hours
        # Average: 18 hours
        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-10T20:00:00.000+0000",
            ),
            create_bug_issue(
                "A935-2",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-11T08:00:00.000+0000",
            ),
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
            time_period_days=30,
        )

        assert "error_state" not in result, (
            f"Unexpected error: {result.get('error_message')}"
        )
        assert result["incident_count"] == 2
        assert result["value"] == pytest.approx(18, rel=0.1)
        assert result["unit"] == "hours"

    def test_mttr_deployment_mode(self, mock_load_app_settings, fixversion_release_map):
        """Test MTTR using fixVersions mode (deployment time).

        Bug created → Bug deployed (via fixVersion.releaseDate)
        """
        from data.dora_metrics import calculate_mean_time_to_recovery

        # Profile already has incident_resolved_at: "fixVersions"

        # Bug: Created Jan 10 08:00, Deployed Jan 12 10:00 = 50 hours
        bugs = [
            create_bug_issue(
                "A935-1",
                fix_version_name="Hotfix_2025_01",
                created="2025-01-10T08:00:00.000+0000",
            )
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
            fixversion_release_map=fixversion_release_map,
        )

        assert "error_state" not in result
        assert result["incident_count"] == 1
        # ~50 hours = ~2.08 days
        assert result["unit"] == "days"
        assert result["value"] == pytest.approx(50 / 24, rel=0.1)

    def test_mttr_no_incidents(self, mock_load_app_settings):
        """Test MTTR with no incidents."""
        from data.dora_metrics import calculate_mean_time_to_recovery

        result = calculate_mean_time_to_recovery(
            incident_issues=[],
        )

        assert result["error_state"] == "no_data"

    def test_mttr_missing_resolution(self, mock_load_app_settings):
        """Test MTTR when bugs have no resolution date."""
        from data.dora_metrics import calculate_mean_time_to_recovery

        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date=None,  # Not resolved yet
            )
        ]

        result = calculate_mean_time_to_recovery(
            incident_issues=bugs,
        )

        assert result["error_state"] == "no_data"
        assert "missing end" in result["error_message"].lower()

    def test_mttr_performance_tiers(self, mock_load_app_settings):
        """Test MTTR performance tier classification."""
        from data.dora_metrics import calculate_mean_time_to_recovery

        mock_load_app_settings.return_value["field_mappings"]["dora"][
            "incident_resolved_at"
        ] = "resolutiondate"

        # Elite: < 1 hour
        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-10T08:00:00.000+0000",
                resolution_date="2025-01-10T08:30:00.000+0000",  # 30 minutes
            )
        ]
        result = calculate_mean_time_to_recovery(bugs)
        assert result["performance_tier"] == "elite"

        # Low: > 1 week (168 hours)
        bugs = [
            create_bug_issue(
                "A935-1",
                created="2025-01-01T08:00:00.000+0000",
                resolution_date="2025-01-15T08:00:00.000+0000",  # 14 days
            )
        ]
        result = calculate_mean_time_to_recovery(bugs)
        assert result["performance_tier"] == "low"


#######################################################################
# TEST CLASS: Shared fixVersion Functions
#######################################################################


class TestFixVersionMatcher:
    """Test shared fixVersion matching functions.

    These functions are used by Lead Time and MTTR to find deployment dates.
    """

    def test_build_fixversion_release_map(self):
        """Test building fixVersion → releaseDate map from Operational Tasks."""
        from data.fixversion_matcher import build_fixversion_release_map

        op_tasks = [
            create_operational_task(
                "RI-1", fix_version_name="R1", release_date="2025-01-15"
            ),
            create_operational_task(
                "RI-2", fix_version_name="R2", release_date="2025-01-20"
            ),
            create_operational_task(
                "RI-3", fix_version_name="R1", release_date="2025-01-15"
            ),  # Duplicate
        ]

        result = build_fixversion_release_map(
            operational_tasks=op_tasks,
            flow_end_statuses=["Done", "Resolved", "Closed"],
        )

        assert len(result) == 2
        assert "R1" in result
        assert "R2" in result
        assert result["R1"] == datetime(2025, 1, 15)
        assert result["R2"] == datetime(2025, 1, 20)

    def test_get_deployment_date_for_issue(self):
        """Test getting deployment date for an issue from release map."""
        from data.fixversion_matcher import get_deployment_date_for_issue

        release_map = {
            "Release_1": datetime(2025, 1, 15, tzinfo=timezone.utc),
            "Release_2": datetime(2025, 2, 1, tzinfo=timezone.utc),
        }

        # Issue with one fixVersion
        issue = create_development_issue("A935-1", fix_version_name="Release_1")
        result = get_deployment_date_for_issue(issue, release_map)
        assert result == datetime(2025, 1, 15, tzinfo=timezone.utc)

        # Issue with multiple fixVersions - should return earliest
        issue["fields"]["fixVersions"] = [
            {"name": "Release_2"},
            {"name": "Release_1"},
        ]
        result = get_deployment_date_for_issue(issue, release_map)
        assert result == datetime(2025, 1, 15, tzinfo=timezone.utc)  # Earliest

        # Issue with no matching fixVersion
        issue["fields"]["fixVersions"] = [{"name": "Unknown_Release"}]
        result = get_deployment_date_for_issue(issue, release_map)
        assert result is None

    def test_filter_issues_deployed_in_week(self):
        """Test filtering issues by deployment week."""
        from data.fixversion_matcher import filter_issues_deployed_in_week

        release_map = {
            "Week1": datetime(2025, 1, 8, tzinfo=timezone.utc),  # In week
            "Week2": datetime(2025, 1, 15, tzinfo=timezone.utc),  # After week
            "Week0": datetime(2025, 1, 1, tzinfo=timezone.utc),  # Before week
        }

        issues = [
            create_development_issue("A-1", fix_version_name="Week1"),
            create_development_issue("A-2", fix_version_name="Week2"),
            create_development_issue("A-3", fix_version_name="Week0"),
        ]

        week_start = datetime(2025, 1, 6, tzinfo=timezone.utc)
        week_end = datetime(2025, 1, 13, tzinfo=timezone.utc)

        result = filter_issues_deployed_in_week(
            issues, release_map, week_start, week_end
        )

        assert len(result) == 1
        assert result[0]["key"] == "A-1"


#######################################################################
# TEST CLASS: Field Value Parsing
#######################################################################


class TestFieldValueParsing:
    """Test field=Value syntax parsing for environment and change failure fields."""

    def test_parse_field_value_filter_simple(self):
        """Test parsing field without =Value."""
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter("customfield_11309")
        assert field_id == "customfield_11309"
        assert filter_values is None

    def test_parse_field_value_filter_single_value(self):
        """Test parsing field=Value syntax."""
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter("customfield_11309=PROD")
        assert field_id == "customfield_11309"
        assert filter_values == ["PROD"]

    def test_parse_field_value_filter_multiple_values(self):
        """Test parsing field=Value1|Value2 syntax."""
        from data.dora_metrics import parse_field_value_filter

        field_id, filter_values = parse_field_value_filter(
            "customfield_11309=PROD|Production|Live"
        )
        assert field_id == "customfield_11309"
        assert filter_values == ["PROD", "Production", "Live"]

    def test_check_field_value_match_string(self):
        """Test checking string field values."""
        from data.dora_metrics import check_field_value_match

        issue = {"fields": {"customfield_11309": "PROD"}}
        assert check_field_value_match(issue, "customfield_11309", ["PROD"]) is True
        assert check_field_value_match(issue, "customfield_11309", ["DEV"]) is False
        # Case insensitive
        assert check_field_value_match(issue, "customfield_11309", ["prod"]) is True

    def test_check_field_value_match_dict(self):
        """Test checking dict field values (single select)."""
        from data.dora_metrics import check_field_value_match

        issue = {"fields": {"customfield_11309": {"value": "PROD", "id": "123"}}}
        assert check_field_value_match(issue, "customfield_11309", ["PROD"]) is True
        assert check_field_value_match(issue, "customfield_11309", ["DEV"]) is False

    def test_is_production_environment(self):
        """Test production environment check with =Value syntax."""
        from data.dora_metrics import is_production_environment

        # With =Value syntax
        issue = {"fields": {"customfield_11309": {"value": "PROD"}}}
        assert is_production_environment(issue, "customfield_11309=PROD") is True
        assert is_production_environment(issue, "customfield_11309=DEV") is False

        # Without =Value, uses fallback
        assert (
            is_production_environment(
                issue, "customfield_11309", fallback_values=["PROD"]
            )
            is True
        )


#######################################################################
# TEST CLASS: Trend Calculation
#######################################################################


class TestTrendCalculation:
    """Test trend direction and percentage calculation."""

    def test_trend_up(self):
        """Test upward trend detection."""
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=5.0)
        assert result["trend_direction"] == "up"
        assert result["trend_percentage"] == pytest.approx(100.0, rel=0.01)

    def test_trend_down(self):
        """Test downward trend detection."""
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=5.0, previous_value=10.0)
        assert result["trend_direction"] == "down"
        assert result["trend_percentage"] == pytest.approx(-50.0, rel=0.01)

    def test_trend_stable(self):
        """Test stable trend (< 5% change)."""
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=9.8)
        assert result["trend_direction"] == "stable"

    def test_trend_no_previous(self):
        """Test trend with no previous value."""
        from data.dora_metrics import _calculate_trend

        result = _calculate_trend(current_value=10.0, previous_value=None)
        assert result["trend_direction"] == "stable"
        assert result["trend_percentage"] == 0.0
