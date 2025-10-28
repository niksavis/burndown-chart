"""Integration tests for field mapping workflow.

Tests the complete workflow of configuring, saving, and using Jira field mappings.
Ensures proper isolation using tempfile and mocking.
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from data.field_mapper import (
    fetch_available_jira_fields,
    validate_field_mapping,
    save_field_mappings,
    load_field_mappings,
    get_field_mappings_hash,
)


class TestFieldMappingWorkflow:
    """Test complete field mapping configuration workflow."""

    @pytest.fixture
    def temp_settings_file(self):
        """Create temporary settings file for test isolation."""
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as f:
            temp_file = f.name
            # Initialize with empty structure
            json.dump({"field_mappings": {}}, f)

        yield temp_file

        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def mock_jira_fields(self):
        """Mock Jira fields metadata (as expected by validate_field_mapping)."""
        return {
            "customfield_10100": {
                "field_name": "Deployment Date",
                "field_type": "datetime",
                "is_custom": True,
            },
            "customfield_10101": {
                "field_name": "Target Environment",
                "field_type": "select",
                "is_custom": True,
            },
            "customfield_10102": {
                "field_name": "Code Commit Date",
                "field_type": "datetime",
                "is_custom": True,
            },
            "customfield_10103": {
                "field_name": "Incident Flag",
                "field_type": "checkbox",
                "is_custom": True,
            },
        }

    def test_configure_and_save_mappings(self, temp_settings_file, mock_jira_fields):
        """Test complete workflow: fetch fields, validate, save mappings.
        
        Workflow:
        1. Fetch available Jira fields
        2. Validate field type compatibility
        3. Save mappings to configuration
        4. Load mappings back and verify
        """
        # Step 1: Mock fetching Jira fields (already have mock_jira_fields)

        # Step 2: Validate field mappings using correct field_metadata format
        test_mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                    "target_environment": "customfield_10101",
                }
            }
        }

        # Validate deployment_date mapping (datetime -> datetime)
        is_valid, error = validate_field_mapping(
            "deployment_date", "customfield_10100", mock_jira_fields
        )
        assert is_valid is True
        assert error is None

        # Validate target_environment mapping (select -> select)
        is_valid, error = validate_field_mapping(
            "target_environment", "customfield_10101", mock_jira_fields
        )
        assert is_valid is True
        assert error is None

        # Step 3: Save mappings
        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            with patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file):
                success = save_field_mappings(test_mappings)
                assert success is True

        # Step 4: Load mappings and verify
        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            with patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file):
                loaded_mappings = load_field_mappings()
                assert "field_mappings" in loaded_mappings
                assert loaded_mappings["field_mappings"]["dora"]["deployment_date"] == "customfield_10100"
                assert loaded_mappings["field_mappings"]["dora"]["target_environment"] == "customfield_10101"

    def test_mapping_change_invalidates_cache(self, temp_settings_file):
        """Test that changing field mappings invalidates the cache.
        
        Workflow:
        1. Save initial mappings
        2. Get hash of mappings
        3. Change mappings
        4. Verify hash changed (cache should be invalidated)
        """
        # Initial mappings
        initial_mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                }
            }
        }

        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            with patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file):
                # Save initial mappings
                save_field_mappings(initial_mappings)
                initial_hash = get_field_mappings_hash()
                assert initial_hash is not None
                assert len(initial_hash) > 0

                # Change mappings
                updated_mappings = {
                    "field_mappings": {
                        "dora": {
                            "deployment_date": "customfield_10200",  # Different field
                        }
                    }
                }
                save_field_mappings(updated_mappings)
                updated_hash = get_field_mappings_hash()

                # Verify hash changed
                assert updated_hash != initial_hash

                # Verify new mapping was saved
                loaded = load_field_mappings()
                assert loaded["field_mappings"]["dora"]["deployment_date"] == "customfield_10200"

    def test_invalid_field_type_mapping(self, mock_jira_fields):
        """Test that invalid field type mappings are rejected."""
        # Try to map datetime field to text requirement
        is_valid, error = validate_field_mapping(
            "deployment_date",  # Requires datetime
            "customfield_10101",  # This is a select field, not datetime
            mock_jira_fields,
        )
        assert is_valid is False
        assert error is not None
        assert "type mismatch" in error.lower() or "incompatible" in error.lower()

    def test_missing_required_mappings(self, temp_settings_file):
        """Test detection of missing required field mappings."""
        from data.field_mapper import check_required_mappings

        # Save incomplete mappings (missing some required fields)
        incomplete_mappings = {
            "dora": {
                "deployment_date": "customfield_10100",
                # Missing: code_commit_date, incident_detected_at, etc.
            }
        }

        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            save_field_mappings(incomplete_mappings)

            # Check for deployment_frequency metric
            has_all, missing = check_required_mappings("deployment_frequency")
            assert has_all is False
            assert len(missing) > 0  # Should have missing fields

    def test_empty_mappings_handling(self, temp_settings_file):
        """Test that system handles empty/no mappings gracefully."""
        with patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file):
            with patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file):
                # Save empty mappings
                success = save_field_mappings({})
                assert success is True

                # Verify can still load
                loaded_again = load_field_mappings()
                assert isinstance(loaded_again, dict)


class TestFieldMappingIntegrationWithCalculator:
    """Test field mapping integration with DORA calculator."""

    def test_calculator_uses_field_mappings(self):
        """Test that DORA calculator retrieves and uses field mappings.
        
        NOTE: This is a stub test for Phase 4.
        Full implementation will be in Phase 5 when we integrate
        field mappings with actual metric calculations.
        """
        from data.field_mapper import get_mapped_field_id

        test_mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                }
            }
        }

        with patch("data.field_mapper.load_field_mappings") as mock_load:
            mock_load.return_value = test_mappings

            # Get mapped field ID
            field_id = get_mapped_field_id("dora", "deployment_date")
            assert field_id == "customfield_10100"

            # Try to get unmapped field
            unmapped_field = get_mapped_field_id("dora", "nonexistent_field")
            assert unmapped_field is None
