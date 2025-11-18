"""Integration tests for VariableExtractor with DEFAULT_VARIABLE_COLLECTION.

These tests validate end-to-end extraction behavior with realistic JIRA structures.
Tests verify that the extraction system handles real-world data correctly,
including cases where data doesn't perfectly match default variable configurations.

Reference: specs/feature-012-rule-based-variable-mapping.md - T006
"""

import pytest
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION


@pytest.fixture
def deployment_issue_matching_defaults():
    """Deployment issue that matches DEFAULT_VARIABLE_COLLECTION expectations."""
    return {
        "key": "DEPLOY-123",
        "fields": {
            "project": {"key": "DEPLOY"},
            "issuetype": {"name": "Deployment"},
            "status": {"name": "Deployed"},  # Matches deployment_event priority 1
            "created": "2025-01-01T10:00:00.000Z",
            "customfield_10001": "Production",  # Environment filter field
        },
        "changelog": {
            "histories": [
                {
                    "created": "2025-01-15T14:30:00.000Z",
                    "items": [
                        {
                            "field": "status",
                            "fromString": "In Progress",
                            "toString": "Deployed",  # Matches deployment_timestamp priority 1
                        }
                    ],
                },
            ]
        },
    }


@pytest.fixture
def deployment_issue_fallback():
    """Deployment issue that uses fallback sources (realistic variation)."""
    return {
        "key": "DEPLOY-456",
        "fields": {
            "project": {"key": "DEPLOY"},
            "issuetype": {"name": "Task"},
            "status": {"name": "Done"},
            "created": "2025-01-05T12:00:00.000Z",
            "resolutiondate": "2025-01-20T16:00:00.000Z",
            "fixVersions": [{"name": "v1.2.0", "releaseDate": "2025-01-20"}],
        },
        "changelog": {
            "histories": []  # No changelog - tests fallback to fixVersion/resolutiondate
        },
    }


@pytest.fixture
def flow_work_item_complete():
    """Flow work item with full lifecycle (In Progress → Done)."""
    return {
        "key": "WORK-789",
        "fields": {
            "project": {"key": "WORK"},
            "issuetype": {"name": "Story"},
            "status": {"name": "Done"},
            "created": "2025-01-10T09:00:00.000Z",
            "resolutiondate": "2025-01-18T14:00:00.000Z",
            "customfield_10002": 8,  # Story points
        },
        "changelog": {
            "histories": [
                {
                    "created": "2025-01-11T10:00:00.000Z",
                    "items": [
                        {
                            "field": "status",
                            "fromString": "To Do",
                            "toString": "In Progress",
                        }
                    ],
                },
                {
                    "created": "2025-01-18T14:00:00.000Z",
                    "items": [
                        {
                            "field": "status",
                            "fromString": "In Progress",
                            "toString": "Done",
                        }
                    ],
                },
            ]
        },
    }


class TestDORAVariableExtraction:
    """Test DORA metric variable extraction with realistic data."""

    def test_extract_deployment_event_matching_defaults(
        self, deployment_issue_matching_defaults
    ):
        """Test deployment_event extraction when data matches default config."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable(
            "deployment_event", deployment_issue_matching_defaults
        )

        # Priority 1: FieldValueMatchSource(field="status.name", value="Deployed")
        assert result["found"] is True
        assert result["value"] is True
        assert result["source_type"] == "field_value_match"

    def test_extract_deployment_event_with_issuetype_fallback(
        self, deployment_issue_fallback
    ):
        """Test deployment_event uses fallback when primary sources don't match."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = deployment_issue_fallback.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "deployment_event", deployment_issue_fallback, changelog
        )

        # Priority 1: status="Deployed" (not in fixture)
        # Priority 2: changelog to Deployed (no changelog)
        # Priority 3: issuetype="Deployment" (is "Task")
        # Fallback: fixVersions not empty (HAS fixVersions)
        assert result["found"] is True
        assert isinstance(result["value"], bool)

    def test_extract_deployment_timestamp_from_changelog(
        self, deployment_issue_matching_defaults
    ):
        """Test deployment_timestamp extraction from changelog."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = deployment_issue_matching_defaults.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "deployment_timestamp", deployment_issue_matching_defaults, changelog
        )

        # Priority 1: ChangelogTimestampSource(field="status", transition_to="Deployed")
        assert result["found"] is True
        assert isinstance(result["value"], str)
        assert "2025-01-15" in result["value"]

    def test_extract_deployment_timestamp_fallback_to_fixversion(
        self, deployment_issue_fallback
    ):
        """Test deployment_timestamp falls back to fixVersion when changelog missing."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = deployment_issue_fallback.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "deployment_timestamp", deployment_issue_fallback, changelog
        )

        # Priority 1: No changelog match
        # Priority 2: FixVersionSource(field="fixVersions", selector="first")
        assert result["found"] is True
        assert isinstance(result["value"], str)
        assert "2025-01-20" in result["value"]


class TestFlowVariableExtraction:
    """Test Flow metric variable extraction."""

    def test_extract_is_completed(self, flow_work_item_complete):
        """Test is_completed extraction for Done status."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable("is_completed", flow_work_item_complete)

        # FieldValueMatchSource(field="status.name", operator="in", value=["Done", "Closed", "Resolved"])
        assert result["found"] is True
        assert result["value"] is True

    def test_extract_work_started_timestamp(self, flow_work_item_complete):
        """Test work_started_timestamp from status transition to In Progress."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = flow_work_item_complete.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "work_started_timestamp", flow_work_item_complete, changelog
        )

        # Priority 1: ChangelogTimestampSource(field="status", transition_to="In Progress")
        assert result["found"] is True
        assert isinstance(result["value"], str)
        assert "2025-01-11" in result["value"]

    def test_extract_work_completed_timestamp(self, flow_work_item_complete):
        """Test work_completed_timestamp from status transition to Done."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = flow_work_item_complete.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "work_completed_timestamp", flow_work_item_complete, changelog
        )

        # Priority 1: ChangelogTimestampSource(field="status", transition_to="Done")
        assert result["found"] is True
        assert isinstance(result["value"], str)
        assert "2025-01-18" in result["value"]


class TestCommonVariableExtraction:
    """Test common variable extraction."""

    def test_extract_project_key(self, deployment_issue_matching_defaults):
        """Test project_key extraction from nested field."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable(
            "project_key", deployment_issue_matching_defaults
        )

        # FieldValueSource(field="project.key")
        assert result["found"] is True
        assert result["value"] == "DEPLOY"

    def test_extract_issue_type(self, flow_work_item_complete):
        """Test issue_type extraction."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable("issue_type", flow_work_item_complete)

        # FieldValueSource(field="issuetype.name")
        assert result["found"] is True
        assert result["value"] == "Story"

    def test_extract_created_timestamp(self, deployment_issue_matching_defaults):
        """Test created_timestamp extraction."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable(
            "created_timestamp", deployment_issue_matching_defaults
        )

        # FieldValueSource(field="created", value_type="datetime")
        assert result["found"] is True
        assert isinstance(result["value"], str)
        assert "2025-01-01" in result["value"]


class TestBatchExtraction:
    """Test extract_all_variables functionality."""

    def test_extract_all_returns_found_values_only(
        self, deployment_issue_matching_defaults
    ):
        """Test extract_all returns only successfully extracted variables."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        results = extractor.extract_all_variables(deployment_issue_matching_defaults)

        # extract_all returns dict of variable_name -> value (not extraction result)
        assert isinstance(results, dict)

        # Should have extracted common variables that match
        assert "project_key" in results
        assert results["project_key"] == "DEPLOY"

        assert "issue_type" in results
        assert results["issue_type"] == "Deployment"

        assert "deployment_event" in results
        assert results["deployment_event"] is True

    def test_extract_all_excludes_missing_required_variables(
        self, deployment_issue_fallback
    ):
        """Test extract_all excludes variables that couldn't be extracted."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        results = extractor.extract_all_variables(deployment_issue_fallback)

        # Variables that match fixture should be present
        assert "project_key" in results

        # Variables that require specific changelog events won't be present
        # (work_started_timestamp needs "In Progress" transition)
        assert "work_started_timestamp" not in results


class TestMissingDataHandling:
    """Test graceful handling of missing/incomplete data."""

    def test_variable_not_found_returns_safe_structure(
        self, deployment_issue_matching_defaults
    ):
        """Test that variables not matching any source return found=False."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        # Try to extract Flow variable from deployment issue (won't match)
        result = extractor.extract_variable(
            "work_started_timestamp", deployment_issue_matching_defaults
        )

        # Should return structured response with found=False
        assert "found" in result
        assert result["found"] is False

    def test_extract_all_with_minimal_issue(self):
        """Test extract_all handles issues with only required fields."""
        minimal_issue = {
            "key": "MIN-1",
            "fields": {"project": {"key": "MIN"}, "issuetype": {"name": "Task"}},
        }

        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        results = extractor.extract_all_variables(minimal_issue)

        # Should extract basic fields that exist
        assert "project_key" in results
        assert results["project_key"] == "MIN"

        assert "issue_type" in results
        assert results["issue_type"] == "Task"

        # Complex variables requiring changelog shouldn't crash
        # (they just won't be in results dict)
        assert isinstance(results, dict)


class TestPriorityFallback:
    """Test priority-based fallback mechanism."""

    def test_deployment_timestamp_uses_higher_priority_when_available(
        self, deployment_issue_matching_defaults
    ):
        """Test deployment_timestamp prefers changelog over fixVersion."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        changelog = deployment_issue_matching_defaults.get("changelog", {}).get("histories", [])
        result = extractor.extract_variable(
            "deployment_timestamp", deployment_issue_matching_defaults, changelog
        )

        # Should use priority 1 (changelog) not priority 2 (fixVersion)
        assert result["found"] is True
        assert result["source_type"] == "changelog_timestamp"
        assert "2025-01-15" in result["value"]  # From changelog, not other sources

    def test_deployment_timestamp_falls_back_to_lower_priority(
        self, deployment_issue_fallback
    ):
        """Test deployment_timestamp uses fixVersion when changelog missing."""
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)
        result = extractor.extract_variable(
            "deployment_timestamp", deployment_issue_fallback
        )

        # Priority 1 (changelog) not available
        # Should use priority 2 (fixVersion) or priority 3 (resolutiondate)
        assert result["found"] is True
        assert result["source_type"] in ["fixversion_releasedate", "field_value"]
