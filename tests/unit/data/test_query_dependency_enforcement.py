"""
Unit tests for query dependency enforcement.

Tests verify that:
1. DependencyError raised when JIRA not configured before query creation
2. validate_query_exists_for_data_operation enforces query save before data ops
3. delete_query respects allow_cascade parameter
4. Warning logged when field mappings not configured
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from data.query_manager import (
    DependencyError,
    create_query,
    delete_query,
    validate_query_exists_for_data_operation,
)


class TestQueryDependencyEnforcement:
    """Test dependency chain enforcement in query management."""

    @pytest.fixture
    def temp_profile_with_unconfigured_jira(self):
        """Create profile with JIRA not configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            default_profile_dir = temp_profiles_dir / "default"
            default_profile_dir.mkdir(parents=True)

            # Create profile.json with unconfigured JIRA
            profile_data = {
                "id": "default",
                "name": "Default",
                "jira_config": {
                    "base_url": "",
                    "configured": False,  # NOT configured
                },
                "field_mappings": {},
                "queries": [],
            }
            profile_file = default_profile_dir / "profile.json"
            with open(profile_file, "w") as f:
                json.dump(profile_data, f, indent=2)

            with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                yield temp_profiles_dir

    @pytest.fixture
    def temp_profile_with_configured_jira(self):
        """Create profile with JIRA configured."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            default_profile_dir = temp_profiles_dir / "default"
            default_profile_dir.mkdir(parents=True)

            # Create profile.json with configured JIRA
            profile_data = {
                "id": "default",
                "name": "Default",
                "jira_config": {
                    "base_url": "https://test.jira.com",
                    "configured": True,  # CONFIGURED
                },
                "field_mappings": {
                    "status": "status",
                    "deployment_date": "resolutiondate",
                },
                "queries": [],
            }
            profile_file = default_profile_dir / "profile.json"
            with open(profile_file, "w") as f:
                json.dump(profile_data, f, indent=2)

            with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                yield temp_profiles_dir

    def test_create_query_raises_dependency_error_when_jira_not_configured(
        self, temp_profile_with_unconfigured_jira
    ):
        """Verify create_query blocks when JIRA not configured."""
        with pytest.raises(DependencyError) as exc_info:
            create_query("default", "Test Query", "project = TEST")

        assert "JIRA must be configured" in str(exc_info.value)
        assert "test connection first" in str(exc_info.value)

    def test_create_query_succeeds_when_jira_configured(
        self, temp_profile_with_configured_jira
    ):
        """Verify create_query works when JIRA configured."""
        query_id = create_query(
            "default", "Test Query", "project = TEST", "Test description"
        )

        assert query_id == "test-query"

        # Verify query directory created
        query_dir = (
            temp_profile_with_configured_jira / "default" / "queries" / "test-query"
        )
        assert query_dir.exists()

        # Verify query.json created with correct data
        query_file = query_dir / "query.json"
        assert query_file.exists()

        with open(query_file, "r") as f:
            query_data = json.load(f)

        assert query_data["name"] == "Test Query"
        assert query_data["jql"] == "project = TEST"
        assert query_data["description"] == "Test description"
        assert "created_at" in query_data

    def test_create_query_logs_warning_when_field_mappings_missing(
        self, temp_profile_with_configured_jira, caplog
    ):
        """Verify warning logged when field_mappings empty."""
        # Update profile to have empty field_mappings
        profile_file = temp_profile_with_configured_jira / "default" / "profile.json"
        with open(profile_file, "r") as f:
            profile_data = json.load(f)

        profile_data["field_mappings"] = {}

        with open(profile_file, "w") as f:
            json.dump(profile_data, f)

        # Create query - should succeed but log warning
        import logging

        with caplog.at_level(logging.WARNING):
            query_id = create_query("default", "Test Query", "project = TEST")

        assert query_id == "test-query"
        assert "Field mappings not configured" in caplog.text
        assert "metrics may be limited" in caplog.text


class TestQueryValidationForDataOperations:
    """Test validate_query_exists_for_data_operation function."""

    @pytest.fixture
    def temp_profile_with_query(self):
        """Create profile with saved query."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            profiles_file = temp_profiles_dir / "profiles.json"
            temp_profiles_dir.mkdir(parents=True)

            # Create profiles.json
            profiles_data = {
                "version": "3.0",
                "active_profile_id": "default",
                "active_query_id": "main",
                "profiles": {
                    "default": {
                        "id": "default",
                        "name": "Default",
                        "queries": ["main"],
                    }
                },
            }
            with open(profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            # Create profile with query
            query_dir = temp_profiles_dir / "default" / "queries" / "main"
            query_dir.mkdir(parents=True)

            query_data = {
                "name": "Main Query",
                "jql": "project = TEST",
                "created_at": "2025-01-01T00:00:00",
            }
            query_file = query_dir / "query.json"
            with open(query_file, "w") as f:
                json.dump(query_data, f, indent=2)

            with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                with patch("data.query_manager.PROFILES_FILE", profiles_file):
                    yield temp_profiles_dir

    def test_validate_query_exists_succeeds_for_saved_query(
        self, temp_profile_with_query
    ):
        """Verify validation passes for saved query."""
        # Should not raise exception
        validate_query_exists_for_data_operation("main")

    def test_validate_query_exists_raises_for_unsaved_query(
        self, temp_profile_with_query
    ):
        """Verify validation fails for unsaved query."""
        with pytest.raises(DependencyError) as exc_info:
            validate_query_exists_for_data_operation("unsaved-query")

        assert "must be saved before executing data operations" in str(exc_info.value)
        assert "Save Query" in str(exc_info.value)

    def test_validate_query_exists_raises_for_query_without_metadata(
        self, temp_profile_with_query
    ):
        """Verify validation fails for query without query.json."""
        # Create query directory but no query.json
        malformed_query_dir = (
            temp_profile_with_query / "default" / "queries" / "malformed"
        )
        malformed_query_dir.mkdir(parents=True)

        with pytest.raises(DependencyError) as exc_info:
            validate_query_exists_for_data_operation("malformed")

        assert "not properly initialized" in str(exc_info.value)
        assert "Re-save the query" in str(exc_info.value)


class TestQueryDeletionWithCascade:
    """Test delete_query with allow_cascade parameter."""

    @pytest.fixture
    def temp_profile_with_multiple_queries(self):
        """Create profile with multiple queries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            profiles_file = temp_profiles_dir / "profiles.json"
            temp_profiles_dir.mkdir(parents=True)

            # Create profiles.json
            profiles_data = {
                "version": "3.0",
                "active_profile_id": "default",
                "active_query_id": "main",
                "profiles": {
                    "default": {
                        "id": "default",
                        "name": "Default",
                        "queries": ["main", "bugs"],
                    }
                },
            }
            with open(profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            # Create main query
            main_query_dir = temp_profiles_dir / "default" / "queries" / "main"
            main_query_dir.mkdir(parents=True)
            (main_query_dir / "query.json").write_text(
                json.dumps({"name": "Main", "jql": "project = TEST"})
            )

            # Create bugs query
            bugs_query_dir = temp_profiles_dir / "default" / "queries" / "bugs"
            bugs_query_dir.mkdir(parents=True)
            (bugs_query_dir / "query.json").write_text(
                json.dumps({"name": "Bugs", "jql": "type = Bug"})
            )

            with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                with patch("data.query_manager.PROFILES_FILE", profiles_file):
                    yield temp_profiles_dir

    def test_delete_query_prevents_deleting_active_query_without_cascade(
        self, temp_profile_with_multiple_queries
    ):
        """Verify cannot delete active query without allow_cascade=True."""
        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "main", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)
        assert "Switch to another query first" in str(exc_info.value)

    def test_delete_query_allows_deleting_active_query_with_cascade(
        self, temp_profile_with_multiple_queries
    ):
        """Verify can delete active query with allow_cascade=True."""
        # Should not raise exception
        delete_query("default", "main", allow_cascade=True)

        # Verify query deleted
        main_query_dir = (
            temp_profile_with_multiple_queries / "default" / "queries" / "main"
        )
        assert not main_query_dir.exists()

    def test_delete_query_prevents_deleting_last_query_without_cascade(
        self, temp_profile_with_multiple_queries
    ):
        """Verify cannot delete last query without allow_cascade=True."""
        # Switch to bugs query first (so main can be deleted)
        from data.query_manager import switch_query

        switch_query("bugs")

        # Delete main query (now not active)
        delete_query("default", "main", allow_cascade=False)

        # Try to delete bugs (now the only query AND active) - should fail with PermissionError first
        # (active query check happens before last query check)
        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "bugs", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)

    def test_delete_query_allows_deleting_last_query_with_cascade(
        self, temp_profile_with_multiple_queries
    ):
        """Verify can delete last query with allow_cascade=True (for profile cascade deletion)."""
        # Delete bugs query
        delete_query("default", "bugs", allow_cascade=True)

        # Delete main query (now the only query) - should succeed with cascade
        delete_query("default", "main", allow_cascade=True)

        # Verify both queries deleted
        queries_dir = temp_profile_with_multiple_queries / "default" / "queries"
        remaining_queries = list(queries_dir.iterdir())
        assert len(remaining_queries) == 0

    def test_delete_query_deletes_non_active_query_without_cascade(
        self, temp_profile_with_multiple_queries
    ):
        """Verify can delete non-active query without cascade."""
        # Delete bugs query (not active)
        delete_query("default", "bugs", allow_cascade=False)

        # Verify bugs query deleted
        bugs_query_dir = (
            temp_profile_with_multiple_queries / "default" / "queries" / "bugs"
        )
        assert not bugs_query_dir.exists()

        # Verify main query still exists
        main_query_dir = (
            temp_profile_with_multiple_queries / "default" / "queries" / "main"
        )
        assert main_query_dir.exists()
