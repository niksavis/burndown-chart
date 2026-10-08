from datetime import UTC, datetime

import pytest

from data.query_manager import (
    DependencyError,
    create_query,
    delete_query,
    validate_query_exists_for_data_operation,
)


class TestQueryDependencyEnforcement:
    def test_create_query_raises_dependency_error_when_jira_not_configured(
        self, temp_database
    ):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {
                "base_url": "",
                "configured": False,
            },
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        with pytest.raises(DependencyError) as exc_info:
            create_query("default", "Test Query", "project = TEST")

        assert "JIRA must be configured" in str(exc_info.value)
        assert "test connection first" in str(exc_info.value)

    def test_create_query_succeeds_when_jira_configured(self, temp_database):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,
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

        assert query_id.startswith("q_")
        assert len(query_id) == 14

        query = backend.get_query("default", query_id)
        assert query is not None
        assert query["name"] == "Test Query"
        assert query["jql"] == "project = TEST"
        assert "created_at" in query

    def test_create_query_logs_warning_when_field_mappings_missing(
        self, temp_database, caplog
    ):
        import logging

        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {
                "base_url": "https://test.jira.com",
                "configured": True,
            },
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        with caplog.at_level(logging.WARNING):
            query_id = create_query("default", "Test Query", "project = TEST")

        assert query_id.startswith("q_")
        assert len(query_id) == 14
        assert "Field mappings not configured" in caplog.text
        assert "metrics may be limited" in caplog.text


class TestQueryValidationForDataOperations:
    def test_validate_query_exists_succeeds_for_saved_query(self, temp_database):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        query_data = {
            "id": "main",
            "profile_id": "default",
            "name": "Main Query",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", query_data)
        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        validate_query_exists_for_data_operation("main")

    def test_validate_query_exists_raises_for_unsaved_query(self, temp_database):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
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
        pass


class TestQueryDeletionWithCascade:
    def test_delete_query_prevents_deleting_active_query_without_cascade(
        self, temp_database
    ):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "main", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)
        assert "Switch to another query first" in str(exc_info.value)

    def test_delete_query_allows_deleting_active_query_with_cascade(
        self, temp_database
    ):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        delete_query("default", "main", allow_cascade=True)

        assert backend.get_query("default", "main") is None

    def test_delete_query_prevents_deleting_last_query_without_cascade(
        self, temp_database
    ):
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        switch_query("bugs")

        delete_query("default", "main", allow_cascade=False)

        with pytest.raises(PermissionError) as exc_info:
            delete_query("default", "bugs", allow_cascade=False)

        assert "Cannot delete active query" in str(exc_info.value)

    def test_delete_query_allows_deleting_last_query_with_cascade(self, temp_database):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        delete_query("default", "bugs", allow_cascade=True)

        delete_query("default", "main", allow_cascade=True)

        queries = backend.list_queries("default")
        assert len(queries) == 0

    def test_delete_query_deletes_non_active_query_without_cascade(self, temp_database):
        from data.persistence.factory import get_backend

        backend = get_backend()

        profile_data = {
            "id": "default",
            "name": "Default",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(profile_data)

        main_query = {
            "id": "main",
            "profile_id": "default",
            "name": "Main",
            "jql": "project = TEST",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", main_query)

        bugs_query = {
            "id": "bugs",
            "profile_id": "default",
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
            "last_used": datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat(),
        }
        backend.save_query("default", bugs_query)

        backend.set_app_state("active_profile_id", "default")
        backend.set_app_state("active_query_id", "main")

        delete_query("default", "bugs", allow_cascade=False)

        assert backend.get_query("default", "bugs") is None

        assert backend.get_query("default", "main") is not None
