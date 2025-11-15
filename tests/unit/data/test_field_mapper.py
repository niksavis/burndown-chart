"""Unit tests for field_mapper module.

Tests field mapping validation, Jira field fetching, and configuration persistence
with proper test isolation using temporary files.
"""

import json
import os
import pytest
import tempfile
from unittest.mock import patch, Mock
from data.field_mapper import (
    fetch_available_jira_fields,
    validate_field_mapping,
    save_field_mappings,
    load_field_mappings,
    get_field_mappings_hash,
)


@pytest.fixture
def temp_settings_file():
    """Create isolated temporary settings file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        # Write minimal valid settings structure
        initial_settings = {
            "pert_factor": 1.5,
            "deadline": "2025-12-31",
        }
        json.dump(initial_settings, f)
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sample_jira_fields():
    """Sample Jira fields response for testing."""
    return [
        {
            "id": "customfield_10100",
            "name": "Deployment Date",
            "schema": {"type": "datetime"},
        },
        {
            "id": "customfield_10101",
            "name": "Target Environment",
            "schema": {"type": "option"},
        },
        {
            "id": "customfield_10200",
            "name": "Work Type",
            "schema": {"type": "option"},
        },
        {
            "id": "status",
            "name": "Status",
            "schema": {"type": "status"},
        },
    ]


@pytest.fixture
def sample_field_metadata():
    """Sample field metadata for validation testing."""
    return {
        "customfield_10100": {"field_type": "datetime"},
        "customfield_10101": {"field_type": "select"},
        "customfield_10200": {"field_type": "select"},
        "customfield_10300": {"field_type": "text"},
    }


class TestFetchAvailableJiraFields:
    """Test Jira fields API fetching."""

    @patch("data.field_mapper.load_jira_configuration")
    @patch("data.field_mapper.requests.get")
    def test_fetch_fields_success(self, mock_get, mock_config, sample_jira_fields):
        """Test successful fetch of Jira fields."""
        # Setup mocks
        mock_config.return_value = {
            "base_url": "https://test.jira.com",
            "token": "test-token",
            "api_version": "v2",
        }
        mock_response = Mock()
        mock_response.json.return_value = sample_jira_fields
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Execute
        fields = fetch_available_jira_fields()

        # Verify
        assert len(fields) == 4
        assert fields[0]["field_id"] == "customfield_10100"
        assert fields[0]["field_name"] == "Deployment Date"
        assert fields[0]["field_type"] == "datetime"
        assert fields[0]["is_custom"] is True

        # Verify standard field
        assert fields[3]["field_id"] == "status"
        assert fields[3]["is_custom"] is False

    @patch("data.field_mapper.load_jira_configuration")
    @patch("data.field_mapper.requests.get")
    def test_fetch_fields_api_error(self, mock_get, mock_config):
        """Test API error handling."""
        mock_config.return_value = {
            "base_url": "https://test.jira.com",
            "token": "test-token",
            "api_version": "v2",
        }
        mock_get.side_effect = Exception("Connection error")

        with pytest.raises(Exception):
            fetch_available_jira_fields()


class TestValidateFieldMapping:
    """Test field mapping validation logic."""

    def test_valid_datetime_mapping(self, sample_field_metadata):
        """Test valid datetime field mapping."""
        is_valid, error_msg = validate_field_mapping(
            "deployment_date", "customfield_10100", sample_field_metadata
        )

        assert is_valid is True
        assert error_msg is None

    def test_valid_select_mapping(self, sample_field_metadata):
        """Test valid select field mapping."""
        is_valid, error_msg = validate_field_mapping(
            "target_environment", "customfield_10101", sample_field_metadata
        )

        assert is_valid is True
        assert error_msg is None

    def test_field_not_found(self, sample_field_metadata):
        """Test validation for non-existent field."""
        is_valid, error_msg = validate_field_mapping(
            "deployment_date", "customfield_99999", sample_field_metadata
        )

        assert is_valid is False
        assert error_msg is not None
        assert "not found" in error_msg.lower()

    def test_unknown_internal_field(self, sample_field_metadata):
        """Test handling of unknown internal field (should allow for flexibility)."""
        is_valid, error_msg = validate_field_mapping(
            "unknown_field", "customfield_10100", sample_field_metadata
        )

        # Should allow unknown fields for future extensibility
        assert is_valid is True
        assert error_msg is None


class TestSaveAndLoadFieldMappings:
    """Test field mapping persistence."""

    def test_save_and_load_mappings(self, temp_settings_file):
        """Test saving and loading field mappings."""
        mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                    "target_environment": "customfield_10101",
                },
                "flow": {"flow_item_type": "customfield_10200"},
            },
            "field_metadata": {
                "customfield_10100": {
                    "name": "Deployment Date",
                    "type": "datetime",
                    "required": True,
                }
            },
        }

        # Patch APP_SETTINGS_FILE to use temp file
        with (
            patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file),
            patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file),
        ):
            # Save mappings
            result = save_field_mappings(mappings)
            assert result is True

            # Load and verify
            loaded_mappings = load_field_mappings()
            assert "field_mappings" in loaded_mappings
            # Note: Testing dora_flow_config structure, not old dora structure
            assert (
                "dora_flow_config" in loaded_mappings
                or "dora" in loaded_mappings["field_mappings"]
            )

    @pytest.mark.skip(
        reason="Obsolete: Tests old app_settings.json pattern. Field mappings storage tested in test_profile_settings_integration.py"
    )
    def test_save_preserves_existing_settings(self, temp_settings_file):
        """Test that saving mappings preserves other settings - DEPRECATED"""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial settings file
            settings_file = Path(tmpdir) / "app_settings.json"
            initial_settings = {
                "pert_factor": 1.5,
                "deadline": "2025-12-31",
            }
            settings_file.write_text(json.dumps(initial_settings))

            # Patch both persistence and field_mapper
            with (
                patch(
                    "data.persistence.get_active_query_workspace",
                    return_value=Path(tmpdir),
                ),
                patch(
                    "data.field_mapper.get_active_query_workspace",
                    return_value=Path(tmpdir),
                ),
            ):
                # Save mappings
                mappings = {
                    "field_mappings": {"dora": {"deployment_date": "customfield_10100"}}
                }
                save_field_mappings(mappings)

                # Verify existing settings are preserved
                settings = json.loads(settings_file.read_text())

                assert settings["pert_factor"] == 1.5
                assert settings["deadline"] == "2025-12-31"
                # field_mappings should be saved in flat structure
                assert "field_mappings" in settings


class TestFieldMappingsHash:
    """Test cache invalidation hash generation."""

    def test_hash_generation(self, temp_settings_file):
        """Test hash is generated correctly."""
        mappings = {
            "field_mappings": {"dora": {"deployment_date": "customfield_10100"}}
        }

        with (
            patch("data.field_mapper.APP_SETTINGS_FILE", temp_settings_file),
            patch("data.persistence.APP_SETTINGS_FILE", temp_settings_file),
        ):
            save_field_mappings(mappings)
            hash1 = get_field_mappings_hash()

            assert len(hash1) == 8
            assert hash1 != "00000000"

            # Hash should be consistent for same mappings
            hash2 = get_field_mappings_hash()
            assert hash1 == hash2

    @pytest.mark.skip(
        reason="Obsolete: Tests old app_settings.json pattern. Field mappings storage tested in test_profile_settings_integration.py"
    )
    def test_hash_changes_on_mapping_change(self, temp_settings_file):
        """Test hash changes when mappings change - DEPRECATED"""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch both persistence and field_mapper
            with (
                patch(
                    "data.persistence.get_active_query_workspace",
                    return_value=Path(tmpdir),
                ),
                patch(
                    "data.field_mapper.get_active_query_workspace",
                    return_value=Path(tmpdir),
                ),
            ):
                # Save first mapping
                mappings1 = {
                    "field_mappings": {"dora": {"deployment_date": "customfield_10100"}}
                }
                save_field_mappings(mappings1)
                hash1 = get_field_mappings_hash()

                # Save different mapping
                mappings2 = {
                    "field_mappings": {
                        "dora": {
                            "deployment_date": "customfield_10101"
                        }  # Different field
                    }
                }
                save_field_mappings(mappings2)
                hash2 = get_field_mappings_hash()

                assert hash1 != hash2
