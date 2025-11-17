"""
Unit tests for Profile settings integration with persistence layer.

Tests verify that:
1. Profile class serializes/deserializes all settings correctly
2. save_app_settings() writes to profile.json with correct structure
3. load_app_settings() reads from profile.json and flattens correctly
4. ensure_default_profile_exists() creates valid default profile
"""

import json
import tempfile
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from data.profile_manager import (
    Profile,
    ensure_default_profile_exists,
)
from data.persistence import save_app_settings, load_app_settings


class TestProfileSerialization:
    """Test Profile class to_dict/from_dict methods."""

    def test_profile_to_dict_includes_all_fields(self):
        """Verify to_dict serializes all new fields."""
        profile = Profile(
            id="test-profile",
            name="Test Profile",
            description="Test description",
            jira_config={"base_url": "https://test.jira.com"},
            field_mappings={"deployment_date": "resolutiondate"},
            forecast_settings={"pert_factor": 1.5, "deadline": "2025-12-31"},
            project_classification={"devops_projects": ["OPS"]},
            flow_type_mappings={"Feature": {"issue_types": ["Story"]}},
            queries=["main", "bugs"],
            active_query_id="main",
            show_milestone=True,
            show_points=False,
        )

        data = profile.to_dict()

        assert data["id"] == "test-profile"
        assert data["name"] == "Test Profile"
        assert data["description"] == "Test description"
        assert data["jira_config"]["base_url"] == "https://test.jira.com"
        assert data["field_mappings"]["deployment_date"] == "resolutiondate"
        assert data["forecast_settings"]["pert_factor"] == 1.5
        assert data["project_classification"]["devops_projects"] == ["OPS"]
        assert data["flow_type_mappings"]["Feature"]["issue_types"] == ["Story"]
        assert data["queries"] == ["main", "bugs"]
        assert data["active_query_id"] == "main"
        assert data["show_milestone"] is True
        assert data["show_points"] is False

    def test_profile_from_dict_deserializes_all_fields(self):
        """Verify from_dict deserializes all new fields with defaults."""
        data = {
            "id": "kafka-project",
            "name": "Apache Kafka",
            "description": "Kafka development",
            "created_at": "2025-01-01T00:00:00",
            "last_used": "2025-01-02T00:00:00",
            "jira_config": {"base_url": "https://kafka.jira.com"},
            "field_mappings": {"status": "status"},
            "forecast_settings": {"pert_factor": 2.0},
            "project_classification": {"bug_types": ["Bug"]},
            "flow_type_mappings": {"Defect": {"issue_types": ["Bug"]}},
            "queries": ["12w", "6w"],
            "active_query_id": "12w",
            "show_milestone": False,
            "show_points": True,
        }

        profile = Profile.from_dict(data)

        assert profile.id == "kafka-project"
        assert profile.name == "Apache Kafka"
        assert profile.description == "Kafka development"
        assert profile.jira_config["base_url"] == "https://kafka.jira.com"
        assert profile.field_mappings["status"] == "status"
        assert profile.forecast_settings["pert_factor"] == 2.0
        assert profile.project_classification["bug_types"] == ["Bug"]
        assert profile.flow_type_mappings["Defect"]["issue_types"] == ["Bug"]
        assert profile.queries == ["12w", "6w"]
        assert profile.active_query_id == "12w"
        assert profile.show_milestone is False
        assert profile.show_points is True

    def test_profile_from_dict_with_missing_fields_uses_defaults(self):
        """Verify from_dict uses empty defaults for missing optional fields."""
        minimal_data = {
            "id": "minimal",
            "name": "Minimal Profile",
        }

        profile = Profile.from_dict(minimal_data)

        assert profile.id == "minimal"
        assert profile.name == "Minimal Profile"
        assert profile.description == ""
        assert profile.jira_config == {}
        assert profile.field_mappings == {}
        # forecast_settings has hardcoded defaults in Profile.__init__
        assert profile.forecast_settings == {
            "pert_factor": 1.2,
            "deadline": None,
            "data_points_count": 12,
        }
        assert profile.project_classification == {}
        assert profile.flow_type_mappings == {}
        assert profile.queries == []
        assert profile.active_query_id is None
        assert profile.show_milestone is False
        assert profile.show_points is False


class TestPersistenceIntegration:
    """Test integration between persistence.py and profile.json structure."""

    @pytest.fixture
    def temp_profile_workspace(self):
        """Create temporary profile workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            temp_profiles_dir.mkdir(parents=True)

            # Create profiles.json
            profiles_file = temp_profiles_dir / "profiles.json"
            profiles_data = {
                "version": "3.0",
                "active_profile_id": "default",
                "active_query_id": None,
                "profiles": {
                    "default": {
                        "id": "default",
                        "name": "Default",
                        "created_at": datetime.now().isoformat(),
                    }
                },
            }
            with open(profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            # Create default profile directory
            default_profile_dir = temp_profiles_dir / "default"
            default_profile_dir.mkdir(parents=True)

            # Patch PROFILES_DIR to point to temp directory
            with patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir):
                with patch(
                    "data.persistence.get_active_profile_workspace",
                    return_value=default_profile_dir,
                ):
                    yield default_profile_dir

    def test_save_app_settings_creates_profile_json(self, temp_profile_workspace):
        """Verify save_app_settings writes to profile.json with correct structure."""
        profile_file = temp_profile_workspace / "profile.json"

        # Save settings
        save_app_settings(
            pert_factor=1.8,
            deadline="2025-06-30",
            data_points_count=20,
            show_milestone=True,
            milestone=None,
            show_points=True,
            jql_query="project = TEST",
            jira_config={"base_url": "https://test.jira.com", "configured": True},
            field_mappings={"status": "status", "deployment_date": "resolutiondate"},
            devops_projects=["OPS"],
            development_projects=["DEV"],
            flow_type_mappings={"Feature": {"issue_types": ["Story"]}},
        )

        # Verify profile.json was created
        assert profile_file.exists()

        # Load and verify structure
        with open(profile_file, "r") as f:
            profile_data = json.load(f)

        # Check profile metadata
        assert profile_data["id"] == "default"
        assert profile_data["name"] == "Default"
        assert "created_at" in profile_data
        assert "last_used" in profile_data

        # Check forecast_settings
        assert profile_data["forecast_settings"]["pert_factor"] == 1.8
        assert profile_data["forecast_settings"]["deadline"] == "2025-06-30"
        assert profile_data["forecast_settings"]["data_points_count"] == 20

        # Check jira_config
        assert profile_data["jira_config"]["base_url"] == "https://test.jira.com"
        assert profile_data["jira_config"]["configured"] is True

        # Check field_mappings
        assert profile_data["field_mappings"]["status"] == "status"
        assert profile_data["field_mappings"]["deployment_date"] == "resolutiondate"

        # Check project_classification
        assert profile_data["project_classification"]["devops_projects"] == ["OPS"]
        assert profile_data["project_classification"]["development_projects"] == ["DEV"]

        # Check flow_type_mappings
        assert profile_data["flow_type_mappings"]["Feature"]["issue_types"] == ["Story"]

        # Check display toggles
        assert profile_data["show_milestone"] is True
        assert profile_data["show_points"] is True

    def test_load_app_settings_reads_profile_json(self, temp_profile_workspace):
        """Verify load_app_settings reads from profile.json and flattens correctly."""
        profile_file = temp_profile_workspace / "profile.json"

        # Create profile.json directly
        profile_data = {
            "id": "default",
            "name": "Default",
            "description": "Default profile",
            "created_at": "2025-01-01T00:00:00",
            "last_used": "2025-01-02T00:00:00",
            "jira_config": {"base_url": "https://example.com", "token": "secret"},
            "field_mappings": {"status": "status"},
            "forecast_settings": {
                "pert_factor": 2.5,
                "deadline": "2025-12-31",
                "data_points_count": 15,
            },
            "project_classification": {
                "devops_projects": ["INFRA"],
                "development_projects": ["APP"],
                "bug_types": ["Bug", "Defect"],
            },
            "flow_type_mappings": {
                "Feature": {"issue_types": ["Story", "Epic"]},
            },
            "queries": [],
            "active_query_id": None,
            "show_milestone": False,
            "show_points": True,
        }

        with open(profile_file, "w") as f:
            json.dump(profile_data, f, indent=2)

        # Load settings
        settings = load_app_settings()

        # Verify flattened structure (backward compatibility)
        assert settings["pert_factor"] == 2.5
        assert settings["deadline"] == "2025-12-31"
        assert settings["data_points_count"] == 15
        assert settings["show_milestone"] is False
        assert settings["show_points"] is True

        # Verify JIRA config preserved
        assert settings["jira_config"]["base_url"] == "https://example.com"
        assert settings["jira_config"]["token"] == "secret"

        # Verify field_mappings preserved
        assert settings["field_mappings"]["status"] == "status"

        # Verify project_classification flattened
        assert settings["devops_projects"] == ["INFRA"]
        assert settings["development_projects"] == ["APP"]
        assert settings["bug_types"] == ["Bug", "Defect"]

        # Verify flow_type_mappings preserved
        assert settings["flow_type_mappings"]["Feature"]["issue_types"] == [
            "Story",
            "Epic",
        ]


class TestDefaultProfileCreation:
    """Test ensure_default_profile_exists function."""

    @pytest.fixture
    def temp_profiles_dir(self):
        """Create temporary profiles directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            temp_profiles_dir.mkdir(parents=True)

            # Patch PROFILES_DIR globally
            with patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir):
                with patch(
                    "data.profile_manager.PROFILES_FILE",
                    temp_profiles_dir / "profiles.json",
                ):
                    yield temp_profiles_dir

    def test_ensure_default_profile_creates_when_none_exist(self, temp_profiles_dir):
        """Verify ensure_default_profile_exists creates default profile."""
        profile_id = ensure_default_profile_exists()

        # Should return hash-based profile ID (e.g., "p_0ffed6eb03d4")
        assert profile_id.startswith("p_")
        assert len(profile_id) == 14  # "p_" + 12 hex chars

        # Verify profiles.json created
        profiles_file = temp_profiles_dir / "profiles.json"
        assert profiles_file.exists()

        with open(profiles_file, "r") as f:
            metadata = json.load(f)

        assert metadata["active_profile_id"] == profile_id
        assert profile_id in metadata["profiles"]

        # Verify profile.json created with correct defaults
        profile_file = temp_profiles_dir / profile_id / "profile.json"
        assert profile_file.exists()

        with open(profile_file, "r") as f:
            profile_data = json.load(f)

        assert profile_data["id"] == profile_id  # Use generated ID
        assert profile_data["name"] == "Default"
        assert (
            profile_data["forecast_settings"]["pert_factor"] == 6
        )  # DEFAULT_PERT_FACTOR
        assert profile_data["jira_config"]["configured"] is False
        assert "field_mappings" in profile_data
        assert "project_classification" in profile_data
        assert "flow_type_mappings" in profile_data

    def test_ensure_default_profile_skips_when_profiles_exist(self, temp_profiles_dir):
        """Verify ensure_default_profile_exists does nothing when profiles exist."""
        # Create existing profile
        profiles_file = temp_profiles_dir / "profiles.json"
        existing_data = {
            "version": "3.0",
            "active_profile_id": "kafka",
            "active_query_id": None,
            "profiles": {
                "kafka": {
                    "id": "kafka",
                    "name": "Kafka Project",
                }
            },
        }
        with open(profiles_file, "w") as f:
            json.dump(existing_data, f)

        # Call ensure_default_profile_exists
        profile_id = ensure_default_profile_exists()

        # Should return existing active profile, not create "default"
        assert profile_id == "kafka"

        # Verify profiles.json unchanged
        with open(profiles_file, "r") as f:
            metadata = json.load(f)

        assert metadata["active_profile_id"] == "kafka"
        assert "default" not in metadata["profiles"]
