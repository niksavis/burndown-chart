from datetime import UTC, datetime

import pytest


def create_test_profile(profile_id: str, name: str) -> dict:

    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
    return {
        "id": profile_id,
        "name": name,
        "description": "",
        "created_at": fixed_timestamp,
        "last_used": fixed_timestamp,
        "jira_config": {},
        "field_mappings": {},
        "forecast_settings": {
            "pert_factor": 1.2,
            "deadline": None,
            "data_points_count": 12,
        },
        "project_classification": {},
        "flow_type_mappings": {},
    }


def create_test_query(query_id: str, name: str, jql: str) -> dict:

    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
    return {
        "id": query_id,
        "name": name,
        "jql": jql,
        "created_at": fixed_timestamp,
        "last_used": fixed_timestamp,
    }


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveQueryId:
    def test_returns_active_query_id(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id

        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "bugs")

        result = get_active_query_id()

        assert result == "bugs"

    def test_raises_if_profiles_json_missing(self, temp_database):
        from data.query_manager import get_active_query_id

        result = get_active_query_id()

        assert result is None

    def test_raises_if_active_query_id_missing(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id

        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")

        result = get_active_query_id()

        assert result is None


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveProfileId:
    def test_returns_active_profile_id(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_profile_id

        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        result = get_active_profile_id()

        assert result == "kafka"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestSwitchQuery:
    def test_switches_to_existing_query(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id, switch_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        switch_query("bugs")

        assert get_active_query_id() == "bugs"

    def test_raises_if_query_does_not_exist(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        with pytest.raises(ValueError, match="Query 'nonexistent' not found"):
            switch_query("nonexistent")

    def test_switch_is_atomic(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        switch_query("bugs")

        assert backend.get_app_state("active_query_id") == "bugs"

    @pytest.mark.performance
    def test_performance_under_50ms(self, temp_database):
        import time

        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        start = time.perf_counter()
        switch_query("bugs")
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 200, f"switch_query took {elapsed_ms:.2f}ms, target: <200ms"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestListQueriesForProfile:
    def test_lists_queries_with_metadata(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query(
            "kafka",
            create_test_query("bugs", "Bugs Only", "project = KAFKA AND type = Bug"),
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        queries = list_queries_for_profile("kafka")

        assert len(queries) == 2

        main_query = next(q for q in queries if q["id"] == "main")
        bugs_query = next(q for q in queries if q["id"] == "bugs")

        assert main_query["name"] == "All Issues"
        assert main_query["jql"] == "project = KAFKA"
        assert main_query["is_active"] is True

        assert bugs_query["name"] == "Bugs Only"
        assert bugs_query["is_active"] is False

    def test_returns_empty_list_if_no_queries(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))

        queries = list_queries_for_profile("kafka")

        assert queries == []

    def test_handles_missing_query_json(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))

        queries = list_queries_for_profile("kafka")

        assert queries == []


@pytest.mark.unit
@pytest.mark.profile_tests
class TestCreateQuery:
    def test_creates_query_with_metadata(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        query_id = create_query("kafka", "High Priority Bugs", "priority = High")

        assert query_id.startswith("q_")
        assert len(query_id) == 14

        query_data = backend.get_query("kafka", query_id)
        assert query_data is not None
        assert query_data["name"] == "High Priority Bugs"
        assert query_data["jql"] == "priority = High"
        assert "created_at" in query_data

    def test_raises_if_query_id_conflicts(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        query_id1 = create_query("kafka", "Bugs", "type = Bug")
        query_id2 = create_query("kafka", "Bugs", "type = Bug")

        assert query_id1 != query_id2
        assert backend.get_query("kafka", query_id1) is not None
        assert backend.get_query("kafka", query_id2) is not None

    def test_slugifies_query_name(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        query_id = create_query("kafka", "Sprint 2025-Q4", "sprint = 2025-Q4")

        assert query_id.startswith("q_")
        assert len(query_id) == 14


@pytest.mark.unit
@pytest.mark.profile_tests
class TestUpdateQuery:
    def test_updates_query_jql(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )

        result = update_query(
            "kafka", "main", jql="project = KAFKA AND priority > Medium"
        )

        assert result is True
        query_data = backend.get_query("kafka", "main")
        assert query_data is not None
        assert query_data["jql"] == "project = KAFKA AND priority > Medium"
        assert query_data["name"] == "Main Query"

    def test_updates_query_name(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Old Name", "project = KAFKA")
        )

        result = update_query("kafka", "main", name="New Name")

        assert result is True
        query_data = backend.get_query("kafka", "main")
        assert query_data is not None
        assert query_data["name"] == "New Name"
        assert query_data["jql"] == "project = KAFKA"

    def test_no_update_if_no_changes(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )

        result = update_query("kafka", "main", jql="project = KAFKA")

        assert result is True

    def test_raises_if_query_not_found(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))

        with pytest.raises(ValueError, match="not found"):
            update_query("kafka", "nonexistent", jql="project = TEST")


@pytest.mark.unit
@pytest.mark.profile_tests
class TestDeleteQuery:
    def test_deletes_query_directory(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )
        backend.save_query(
            "kafka",
            create_test_query(
                "old-query", "Old Query", "project = KAFKA AND status = Closed"
            ),
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        delete_query("kafka", "old-query")

        assert backend.get_query("kafka", "old-query") is None
        assert backend.get_query("kafka", "main") is not None

    def test_raises_if_deleting_active_query(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        with pytest.raises(PermissionError, match="Cannot delete active query"):
            delete_query("kafka", "main")

    def test_raises_if_deleting_last_query(self, temp_database):
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "bugs")

        delete_query("kafka", "main")

        assert backend.get_query("kafka", "main") is None
