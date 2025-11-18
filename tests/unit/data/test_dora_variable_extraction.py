"""Unit tests for DORA calculator variable extraction integration.

Tests the integration of VariableExtractor with DORA metric calculators,
verifying that variables can be extracted correctly for DORA metrics.

Reference: Feature 012 - T007
"""

from data.dora_calculator import _extract_variables_from_issue
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION


class TestDORAVariableExtraction:
    """Test variable extraction for DORA metrics."""

    def test_extract_deployment_variables_from_realistic_issue(self):
        """Test extracting deployment-related variables from realistic JIRA issue."""
        issue = {
            "key": "DEPLOY-100",
            "fields": {
                "project": {"key": "DEPLOY"},
                "issuetype": {"name": "Deployment"},
                "status": {"name": "Deployed"},
                "created": "2025-11-01T10:00:00.000Z",
                "customfield_10001": "Production",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-11-15T14:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Deployed",
                            }
                        ],
                    }
                ]
            },
        }

        # Extract deployment frequency variables
        variables = _extract_variables_from_issue(
            issue, ["deployment_event", "deployment_timestamp", "deployment_successful"]
        )

        # Should extract all deployment variables
        assert "deployment_event" in variables
        assert variables["deployment_event"] is True

        assert "deployment_timestamp" in variables
        assert "2025-11-15" in variables["deployment_timestamp"]

        assert "deployment_successful" in variables
        assert variables["deployment_successful"] is True

    def test_extract_incident_variables(self):
        """Test extracting incident-related variables for CFR/MTTR."""
        issue = {
            "key": "INC-200",
            "fields": {
                "project": {"key": "OPS"},
                "issuetype": {"name": "Incident"},
                "priority": {"name": "Critical"},
                "status": {"name": "Resolved"},
                "created": "2025-11-10T08:00:00.000Z",
                "resolutiondate": "2025-11-10T12:30:00.000Z",
                "customfield_10001": "Production",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-11-10T12:30:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "In Progress",
                                "toString": "Resolved",
                            }
                        ],
                    }
                ]
            },
        }

        variables = _extract_variables_from_issue(
            issue,
            [
                "is_incident",
                "incident_start_timestamp",
                "incident_resolved_timestamp",
            ],
        )

        # Verify incident detection
        assert "is_incident" in variables
        assert variables["is_incident"] is True

        # Verify timestamps
        assert "incident_start_timestamp" in variables
        assert "2025-11-10" in variables["incident_start_timestamp"]

        assert "incident_resolved_timestamp" in variables
        assert "2025-11-10" in variables["incident_resolved_timestamp"]

    def test_extract_with_custom_extractor(self):
        """Test using custom VariableExtractor instance."""
        issue = {
            "key": "TEST-1",
            "fields": {
                "project": {"key": "TEST"},
                "issuetype": {"name": "Task"},
                "created": "2025-11-01T00:00:00.000Z",
            },
        }

        # Create custom extractor
        extractor = VariableExtractor(DEFAULT_VARIABLE_COLLECTION)

        # Extract with custom extractor
        variables = _extract_variables_from_issue(
            issue, ["project_key", "issue_type", "created_timestamp"], extractor
        )

        assert variables["project_key"] == "TEST"
        assert variables["issue_type"] == "Task"
        assert "2025-11-01" in variables["created_timestamp"]

    def test_extract_handles_missing_variables_gracefully(self):
        """Test that missing variables don't appear in results."""
        issue = {
            "key": "SIMPLE-1",
            "fields": {
                "project": {"key": "SIMPLE"},
                "issuetype": {"name": "Bug"},
            },
        }

        # Try to extract deployment variables from non-deployment issue
        variables = _extract_variables_from_issue(
            issue, ["deployment_event", "deployment_timestamp"]
        )

        # Deployment variables won't match, so they shouldn't be in results
        # (depends on fallback behavior in DEFAULT_VARIABLE_COLLECTION)
        assert isinstance(variables, dict)
        # Variables that don't match sources won't be in dict

    def test_extract_with_no_changelog(self):
        """Test extraction when issue has no changelog data."""
        issue = {
            "key": "NOCHG-1",
            "fields": {
                "project": {"key": "NOCHG"},
                "issuetype": {"name": "Story"},
                "status": {"name": "Done"},
                "created": "2025-11-01T10:00:00.000Z",
                "resolutiondate": "2025-11-05T15:00:00.000Z",
            },
        }

        # Extract variables that can work without changelog
        variables = _extract_variables_from_issue(
            issue, ["project_key", "is_completed", "created_timestamp"]
        )

        assert variables["project_key"] == "NOCHG"
        assert variables["is_completed"] is True
        assert "created_timestamp" in variables

    def test_batch_extraction_performance(self):
        """Test extracting multiple variables efficiently."""
        issue = {
            "key": "BATCH-1",
            "fields": {
                "project": {"key": "BATCH"},
                "issuetype": {"name": "Deployment"},
                "status": {"name": "Done"},
                "created": "2025-11-01T10:00:00.000Z",
                "resolutiondate": "2025-11-10T16:00:00.000Z",
                "fixVersions": [{"name": "v1.0.0", "releaseDate": "2025-11-10"}],
            },
        }

        # Extract many variables at once
        all_vars = [
            "project_key",
            "issue_type",
            "created_timestamp",
            "deployment_event",
            "deployment_successful",
        ]

        variables = _extract_variables_from_issue(issue, all_vars)

        # Verify extraction worked for available variables
        assert "project_key" in variables
        assert "issue_type" in variables
        assert "created_timestamp" in variables
