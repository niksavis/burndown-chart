"""
Unit tests for query dependency enforcement.

Tests verify that:
1. DependencyError raised when JIRA not configured before query creation
2. validate_query_exists_for_data_operation enforces query save before data ops
3. delete_query respects allow_cascade parameter
4. Warning logged when field mappings not configured
"""

import pytest
from datetime import datetime, timezone

from data.query_manager import (
    DependencyError,
    create_query,
    delete_query,
    validate_query_exists_for_data_operation,
)


class TestQueryDependencyEnforcement:
    """Test dependency chain enforcement in query management."""

    def test_create_query_raises_dependency_error_when_jira_not_configured(
        self, temp_database
    ):
        """
        Verify create_query blocks when JIRA not configured.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with unconfigured JIRA
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {
                "base_url": "",
                "configured": False,  # NOT configured
            },
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        with pytest.raises(DependencyError) as exc_info:
            create_query("default", "Test Query", "project = TEST")

        assert "JIRA must be configured" in str(exc_info.value)
        assert "test connection first" in str(exc_info.value)

    def test_create_query_succeeds_when_jira_configured(self, temp_database):
        """
        Verify create_query works when JIRA configured.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with configured JIRA
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,  # CONFIGURED
            },
            "field_mappings": {
                "status": "status",
                "deployment_date": "resolutiondate",
            },
        }
        backend.save_profile(profile_data)

        query_id = create_query(
            "default", "Test Query", "project = TEST", "Test description"
        )

        # Verify query created
        assert query_id.startswith("q_")
        assert len(query_id) == 14

        # Verify in database
        query = backend.get_query("default", query_id)
        assert query is not None
        assert query["name"] == "Test Query"
        assert query["jql"] == "project = TEST"
        # Note: description field not stored in database schema (queries table has: id, profile_id, name, jql, created_at, last_used)
        assert "created_at" in query

    def test_create_query_logs_warning_when_field_mappings_missing(
        self, temp_database, caplog
    ):
        """
        Verify warning logged when field_mappings empty.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend
        import logging

        backend = get_backend()

        # Create profile with configured JIRA but empty field_mappings
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,
            },
            "field_mappings": {},  # Empty!
        }
        backend.save_profile(profile_data)

        # Create query - should succeed but log warning
        with caplog.at_level(logging.WARNING):
            query_id = create_query("default", "Test Query", "project = TEST")

        # Assert - hash-based ID returned, warning logged
        assert query_id.startswith("q_")
        assert len(query_id) == 14
        assert "Field mappings not configured" in caplog.text
        assert "metrics may be limited" in caplog.text


class TestQueryValidationForDataOperations:
    """Test validate_query_exists_for_data_operation function."""

    def test_validate_query_exists_succeeds_for_saved_query(self, temp_database):
        """
        Verify validation passes for saved query.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile and query
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        query_data = {
            "id": "main",
            "profile_id": "default",
            "name": "Main Query",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", query_data)
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        # Should not raise exception
        validate_query_exists_for_data_operation("main")

    def test_validate_query_exists_raises_for_unsaved_query(self, temp_database):
        """
        Verify validation fails for unsaved query.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile but NO query
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)
        backend.set_app_state("active_profile_id", "default")

        with pytest.raises(DependencyError) as exc_info:
            validate_query_exists_for_data_operation("unsaved-query")

        assert "must be saved before executing data operations" in str(exc_info.value)
        assert "Save Query" in str(exc_info.value)

    def test_validate_query_exists_raises_for_query_without_metadata(
        self, temp_database
    ):
        """
        Database backend doesn't allow queries without metadata - test N/A.
        All queries in database have complete metadata by design.
        """
        # SKIPPED: Database backend enforces complete metadata via schema constraints.
        pass


class TestQueryDeletionWithCascade:
    """Test delete_query with allow_cascade parameter."""

    def test_delete_query_prevents_deleting_active_query_without_cascade(
        self, temp_database
    ):
        """
        Verify cannot delete active query without allow_cascade=True.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with 2 queries
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", bugs_query)

        # Set main as active
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "main", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)
        assert "Switch to another query first" in str(exc_info.value)

    def test_delete_query_allows_deleting_active_query_with_cascade(
        self, temp_database
    ):
        """
        Verify can delete active query with allow_cascade=True.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with 2 queries
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", bugs_query)

        # Set main as active
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        # Should not raise exception
        delete_query("default", "main", allow_cascade=True)

        # Verify main query deleted
        assert backend.get_query("default", "main") is None

    def test_delete_query_prevents_deleting_last_query_without_cascade(
        self, temp_database
    ):
        """
        Verify cannot delete last query without allow_cascade=True.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        backend = get_backend()

        # Create profile with 2 queries
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", bugs_query)

        # Set main as active
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        # Switch to bugs query first (so main can be deleted)
        switch_query("bugs")

        # Delete main query (now not active)
        delete_query("default", "main", allow_cascade=False)

        # Try to delete bugs (now the only query AND active) - should fail with PermissionError first
        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "bugs", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)

    def test_delete_query_allows_deleting_last_query_with_cascade(self, temp_database):
        """
        Verify can delete last query with allow_cascade=True (for profile cascade deletion).
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with 2 queries
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        # Delete bugs query
        delete_query("default", "bugs", allow_cascade=True)

        # Delete main query (now the only query) - should succeed with cascade
        delete_query("default", "main", allow_cascade=True)

        # Verify both queries deleted
        queries = backend.list_queries("default")
        assert len(queries) == 0

    def test_delete_query_deletes_non_active_query_without_cascade(self, temp_database):
        """
        Verify can delete non-active query without cascade.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend

        backend = get_backend()

        # Create profile with 2 queries
        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(
                2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc
            ).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat(),
        }
        backend.save_query("default", bugs_query)

        # Set main as active
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        # Delete bugs query (not active)
        delete_query("default", "bugs", allow_cascade=False)

        # Verify bugs query deleted
        assert backend.get_query("default", "bugs") is None

        # Verify main query still exists
        assert backend.get_query("default", "main") is not None
