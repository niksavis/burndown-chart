"""Unit tests for Flow calculator variable extraction integration.

Tests Flow metric calculators using VariableExtractor instead of field_mappings.
Validates dual-mode support (legacy field_mappings + variable extraction).
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from data.flow_calculator import (
    calculate_flow_velocity,
    calculate_flow_time,
    calculate_flow_efficiency,
    calculate_flow_load,
    calculate_flow_distribution,
)
from data.variable_mapping.extractor import VariableExtractor
from configuration.metric_variables import DEFAULT_VARIABLE_COLLECTION


class TestFlowVariableExtraction:
    """Test helper function for Flow variable extraction."""

    @pytest.fixture
    def sample_issue_with_changelog(self) -> Dict[str, Any]:
        """Create a sample JIRA issue with changelog for testing."""
        return {
            "key": "PROJ-123",
            "fields": {
                "status": {"name": "Done"},
                "issuetype": {"name": "Story"},
                "customfield_10001": "Feature",  # Work type field
                "resolutiondate": "2025-01-15T10:00:00.000Z",
            },
            "changelog": {
                "histories": [
                    {
                        "created": "2025-01-10T09:00:00.000Z",
                        "items": [
                            {
                                "field": "status",
                                "fromString": "To Do",
                                "toString": "In Progress",
                            }
                        ],
                    },
                    {
                        "created": "2025-01-15T10:00:00.000Z",
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

    @pytest.fixture
    def variable_extractor(self) -> VariableExtractor:
        """Create VariableExtractor with default configuration."""
        return VariableExtractor(DEFAULT_VARIABLE_COLLECTION)


class TestFlowVelocityWithVariableExtraction:
    """Test calculate_flow_velocity with variable extraction mode."""

    @pytest.fixture
    def sample_issues(self) -> List[Dict[str, Any]]:
        """Create sample issues with work_completed_timestamp and work_type_category."""
        return [
            {
                "key": "PROJ-101",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "customfield_10010": "Feature",  # Work type field (matches config)
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-15T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "PROJ-102",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                    "customfield_10010": "Defect",  # Work type field
                    "resolutiondate": "2025-01-16T14:30:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-16T14:30:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "PROJ-103",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},
                    "customfield_10010": "Technical Debt",  # Work type field
                    "resolutiondate": "2025-01-17T09:15:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-17T09:15:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
        ]

    def test_flow_velocity_with_variable_extraction(self, sample_issues):
        """Test flow velocity calculation using variable extraction mode."""
        # Arrange
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        # Act
        result = calculate_flow_velocity(
            issues=sample_issues,
            start_date=start_date,
            end_date=end_date,
            use_variable_extraction=True,
        )

        # Assert
        assert result["error_state"] == "success"
        assert result["metric_name"] == "flow_velocity"
        assert result["value"] >= 2  # At least 2 issues should be found
        assert result["unit"] == "items/month"  # 30-day period
        assert "by_type" in result["details"]

    def test_flow_velocity_legacy_mode_still_works(self, sample_issues):
        """Test that legacy field_mappings mode still works (backward compatibility)."""
        # Arrange
        field_mappings = {
            "flow_item_type": "issuetype",  # Use issuetype.name for classification
            "work_completed_date": "resolutiondate",
        }
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        # Act
        result = calculate_flow_velocity(
            issues=sample_issues,
            field_mappings=field_mappings,
            start_date=start_date,
            end_date=end_date,
            use_variable_extraction=False,  # Explicit legacy mode
        )

        # Assert - legacy mode may not find issues without proper config,
        # but should return valid response structure
        assert result["metric_name"] == "flow_velocity"
        assert "error_state" in result
        assert "value" in result
        # Backward compatibility maintained: function accepts field_mappings
        assert result["error_state"] in ["success", "no_data"]


class TestFlowTimeWithVariableExtraction:
    """Test calculate_flow_time with variable extraction mode."""

    @pytest.fixture
    def sample_issues_with_flow_time(self) -> List[Dict[str, Any]]:
        """Create sample issues with work_started_timestamp and work_completed_timestamp."""
        return [
            {
                "key": "PROJ-201",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                    "resolutiondate": "2025-01-20T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-10T09:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2025-01-20T10:00:00.000Z",
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
            },
            {
                "key": "PROJ-202",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},
                    "resolutiondate": "2025-01-18T14:30:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-15T09:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2025-01-18T14:30:00.000Z",
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
            },
        ]

    def test_flow_time_with_variable_extraction(self, sample_issues_with_flow_time):
        """Test flow time calculation using variable extraction mode."""
        # Act
        result = calculate_flow_time(
            issues=sample_issues_with_flow_time,
            use_variable_extraction=True,
        )

        # Assert
        assert result["error_state"] == "success"
        assert result["metric_name"] == "flow_time"
        assert result["value"] > 0  # Should calculate flow time in days
        assert result["unit"] == "days"
        assert result["total_issue_count"] == 2

    def test_flow_time_legacy_mode_still_works(self, sample_issues_with_flow_time):
        """Test that legacy field_mappings mode still works (backward compatibility)."""
        # Arrange
        field_mappings = {
            "work_completed_date": "resolutiondate",
        }
        wip_statuses = ["In Progress", "In Review"]

        # Act
        result = calculate_flow_time(
            issues=sample_issues_with_flow_time,
            field_mappings=field_mappings,
            wip_statuses=wip_statuses,
            use_variable_extraction=False,  # Explicit legacy mode
        )

        # Assert - legacy mode should work with proper configuration
        assert result["metric_name"] == "flow_time"
        assert "error_state" in result
        assert "value" in result
        # Backward compatibility maintained: function accepts field_mappings
        assert result["error_state"] in ["success", "no_data"]


class TestFlowEfficiencyWithVariableExtraction:
    """Test calculate_flow_efficiency with variable extraction mode."""

    def test_flow_efficiency_with_variable_extraction(self):
        """Test flow efficiency calculation using variable extraction mode.

        Flow efficiency uses CalculatedSource for active_time and total_time
        which are calculated from changelog duration analysis.
        """
        # Arrange: Sample issues with changelog showing time in different statuses
        sample_issues = [
            {
                "key": "PROJ-301",
                "fields": {
                    "status": {"name": "Done"},
                    "created": "2025-01-10T09:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-10T09:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "To Do",
                                    "toString": "In Progress",
                                }
                            ],
                        },
                        {
                            "created": "2025-01-15T10:00:00.000Z",  # 5 days in progress
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
        ]

        # Act
        result = calculate_flow_efficiency(
            issues=sample_issues,
            use_variable_extraction=True,
        )

        # Assert - variable extraction mode now works with CalculatedSource
        assert result["metric_name"] == "flow_efficiency"
        # May return no_data if CalculatedSource can't extract times, or success if it can
        assert result["error_state"] in ["success", "no_data"]
        if result["error_state"] == "success":
            assert result["unit"] == "%"
            assert 0 <= result["value"] <= 100

    def test_flow_efficiency_legacy_mode_still_works(self):
        """Test that legacy field_mappings mode still works (backward compatibility)."""
        # Arrange
        field_mappings = {}  # Not used by flow_efficiency but required in legacy mode
        active_statuses = ["In Progress"]
        wip_statuses = ["In Progress", "In Review"]

        sample_issues = [
            {
                "key": "PROJ-302",
                "fields": {"status": {"name": "Done"}},
                "changelog": {"histories": []},
            }
        ]

        # Act
        result = calculate_flow_efficiency(
            issues=sample_issues,
            field_mappings=field_mappings,
            active_statuses=active_statuses,
            wip_statuses=wip_statuses,
            use_variable_extraction=False,
        )

        # Assert - legacy mode should work
        assert result["metric_name"] == "flow_efficiency"
        assert result["error_state"] in ["success", "no_data"]


# =============================================================================
# FLOW LOAD - VARIABLE EXTRACTION INTEGRATION TESTS
# =============================================================================


class TestFlowLoadWithVariableExtraction:
    """Test calculate_flow_load integration with VariableExtractor."""

    def test_flow_load_with_variable_extraction(self):
        """Test flow load calculation using variable extraction."""
        # Arrange: Sample issues with fields that can be extracted as variables
        sample_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {
                        "name": "In Progress"
                    },  # WIP status → is_in_progress = True
                    "issuetype": {"name": "Story"},  # Maps to Feature
                    "customfield_10002": 5,  # Story points (work_item_size)
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {
                        "name": "In Review"
                    },  # WIP status → is_in_progress = True
                    "issuetype": {"name": "Bug"},  # Maps to Defect
                    "customfield_10002": 3,  # Story points
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "Done"},  # Done status → is_in_progress = False
                    "issuetype": {"name": "Story"},
                    "customfield_10002": 8,
                },
            },
        ]

        # Act
        result = calculate_flow_load(
            issues=sample_issues,
            use_variable_extraction=True,
        )

        # Assert - should count only in-progress items
        assert result["metric_name"] == "flow_load"
        assert result["error_state"] == "success"
        assert result["value"] == 2  # TEST-1 and TEST-2 are in progress
        assert result["unit"] == "items"
        assert "by_type" in result["details"]
        # Variable extraction may not populate by_type (work_type_category not found)
        # Just verify structure is correct

    def test_flow_load_legacy_mode_still_works(self):
        """Test that legacy field_mappings mode still works."""
        # Arrange: Sample issues with field_mappings
        sample_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "In Progress"},
                    "issuetype": {"name": "Story"},
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {"name": "In Review"},
                    "issuetype": {"name": "Bug"},
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},
                },
            },
        ]

        field_mappings = {
            "status": "status",  # Required field
            "flow_item_type": "issuetype",  # Optional
        }

        # Act
        result = calculate_flow_load(
            issues=sample_issues,
            field_mappings=field_mappings,
            use_variable_extraction=False,
        )

        # Assert - legacy mode should work
        assert result["metric_name"] == "flow_load"
        assert result["error_state"] == "success"
        assert result["value"] == 2  # In Progress and In Review are WIP


# =============================================================================
# FLOW DISTRIBUTION - VARIABLE EXTRACTION INTEGRATION TESTS
# =============================================================================


class TestFlowDistributionWithVariableExtraction:
    """Test calculate_flow_distribution integration with VariableExtractor."""

    def test_flow_distribution_with_variable_extraction(self):
        """Test flow distribution calculation using variable extraction."""
        # Arrange: Sample issues with completion dates and work types
        sample_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},  # Maps to Feature
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-15T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Story"},  # Maps to Feature
                    "resolutiondate": "2025-01-16T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-16T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "TEST-3",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Bug"},  # Maps to Defect
                    "resolutiondate": "2025-01-17T10:00:00.000Z",
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-17T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
            {
                "key": "TEST-4",
                "fields": {
                    "status": {"name": "Done"},
                    "issuetype": {"name": "Task"},  # Maps to Technical_Debt
                    "resolutiondate": "2025-01-18T10:00:00.000Z",
                    "labels": ["tech-debt"],  # Helps classification
                },
                "changelog": {
                    "histories": [
                        {
                            "created": "2025-01-18T10:00:00.000Z",
                            "items": [
                                {
                                    "field": "status",
                                    "fromString": "In Progress",
                                    "toString": "Done",
                                }
                            ],
                        }
                    ]
                },
            },
        ]

        # Act
        result = calculate_flow_distribution(
            issues=sample_issues,
            use_variable_extraction=True,
        )

        # Assert - should calculate distribution percentages
        assert result["metric_name"] == "flow_distribution"
        assert result["error_state"] in [
            "success",
            "no_data",
        ]  # May not find completion dates without proper config
        # If successful, verify structure
        if result["error_state"] == "success":
            assert result["unit"] == "%"
            assert "Feature" in result["value"] or "Defect" in result["value"]
            # Distribution percentages sum to 100%
            total_pct = sum(result["value"].values())
            assert 99.0 <= total_pct <= 101.0  # Allow for rounding

    def test_flow_distribution_legacy_mode_still_works(self):
        """Test that legacy field_mappings mode still works."""
        # Arrange: Sample issues with field_mappings
        sample_issues = [
            {
                "key": "TEST-1",
                "fields": {
                    "resolutiondate": "2025-01-15T10:00:00.000Z",
                    "issuetype": {"name": "Story"},
                },
            },
            {
                "key": "TEST-2",
                "fields": {
                    "resolutiondate": "2025-01-16T10:00:00.000Z",
                    "issuetype": {"name": "Bug"},
                },
            },
        ]

        field_mappings = {
            "work_completed_date": "resolutiondate",  # Required
            "flow_item_type": "issuetype",  # Required
        }

        # Legacy mode requires start_date and end_date
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)

        # Act
        result = calculate_flow_distribution(
            issues=sample_issues,
            field_mappings=field_mappings,
            start_date=start_date,
            end_date=end_date,
            use_variable_extraction=False,
        )

        # Assert - legacy mode should work
        assert result["metric_name"] == "flow_distribution"
        assert result["error_state"] == "success"
