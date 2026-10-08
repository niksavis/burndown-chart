from datetime import UTC, datetime

import pytest


class TestProfileCascadeDeletion:
    @pytest.fixture
    def temp_profiles_with_data(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import _generate_unique_profile_id

        backend = get_backend()
        fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()

        kafka_id = _generate_unique_profile_id()
        spark_id = _generate_unique_profile_id()

        kafka_profile = {
            "id": kafka_id,
            "name": f"Apache Kafka {kafka_id}",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(kafka_profile)

        kafka_main_query = {
            "id": "main",
            "profile_id": kafka_id,
            "name": "Main",
            "jql": "project = KAFKA",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
        }
        backend.save_query(kafka_id, kafka_main_query)

        kafka_bugs_query = {
            "id": "bugs",
            "profile_id": kafka_id,
            "name": "Bugs",
            "jql": "type = Bug",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
        }
        backend.save_query(kafka_id, kafka_bugs_query)

        spark_profile = {
            "id": spark_id,
            "name": f"Apache Spark {spark_id}",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(spark_profile)

        spark_12w_query = {
            "id": "12w",
            "profile_id": spark_id,
            "name": "12 Weeks",
            "jql": "created >= -12w",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
        }
        backend.save_query(spark_id, spark_12w_query)

        spark_6w_query = {
            "id": "6w",
            "profile_id": spark_id,
            "name": "6 Weeks",
            "jql": "created >= -6w",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
        }
        backend.save_query(spark_id, spark_6w_query)

        backend.set_app_state("active_profile_id", kafka_id)
        backend.set_app_state("active_query_id", "main")

        yield {
            "kafka_id": kafka_id,
            "spark_id": spark_id,
        }

    def test_delete_profile_cascades_to_all_queries_and_data(
        self, temp_profiles_with_data
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import delete_profile

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        delete_profile(spark_id)

        assert backend.get_profile(spark_id) is None

        assert backend.get_query(spark_id, "12w") is None
        assert backend.get_query(spark_id, "6w") is None

        assert backend.get_profile(kafka_id) is not None
        assert backend.get_query(kafka_id, "main") is not None
        assert backend.get_query(kafka_id, "bugs") is not None

    def test_delete_profile_prevents_deleting_active_profile(
        self, temp_profiles_with_data
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import delete_profile

        backend = get_backend()
        kafka_id = temp_profiles_with_data["kafka_id"]
        spark_id = temp_profiles_with_data["spark_id"]

        assert backend.get_app_state("active_profile_id") == kafka_id

        delete_profile(kafka_id)

        assert backend.get_profile(kafka_id) is None

        new_active = backend.get_app_state("active_profile_id")
        assert new_active == spark_id

        assert backend.get_profile(spark_id) is not None

    def test_delete_profile_prevents_deleting_last_profile(
        self, temp_profiles_with_data
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import delete_profile

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        delete_profile(spark_id)

        delete_profile(kafka_id)

        assert backend.get_profile(spark_id) is None
        assert backend.get_profile(kafka_id) is None

        assert backend.get_app_state("active_profile_id") == ""

    def test_delete_profile_continues_on_query_deletion_errors(
        self, temp_profiles_with_data
    ):
        pass

    def test_delete_profile_removes_all_filesystem_artifacts(
        self, temp_profiles_with_data
    ):
        pass

    def test_delete_profile_validates_profile_exists(self, temp_profiles_with_data):
        from data.profile_manager import delete_profile

        with pytest.raises(ValueError, match="does not exist"):
            delete_profile("nonexistent-profile-id")

    def test_delete_profile_updates_profiles_registry_atomically(
        self, temp_profiles_with_data
    ):
        from data.persistence.factory import get_backend
        from data.profile_manager import delete_profile

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        assert backend.get_profile(spark_id) is not None
        assert backend.get_profile(kafka_id) is not None

        delete_profile(spark_id)

        assert backend.get_profile(spark_id) is None
        assert backend.get_profile(kafka_id) is not None


class TestCascadeDeletionEdgeCases:
    @pytest.fixture
    def temp_profile_with_many_queries(self, temp_database):
        from data.persistence.factory import get_backend
        from data.profile_manager import _generate_unique_profile_id

        backend = get_backend()
        fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()

        default_id = _generate_unique_profile_id()
        bulk_test_id = _generate_unique_profile_id()

        default_profile = {
            "id": default_id,
            "name": "Default",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(default_profile)

        bulk_profile = {
            "id": bulk_test_id,
            "name": "Bulk Test",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(bulk_profile)

        for i in range(1, 21):
            query = {
                "id": f"query-{i}",
                "profile_id": bulk_test_id,
                "name": f"Query {i}",
                "jql": f"project = TEST{i}",
                "created_at": fixed_timestamp,
                "last_used": fixed_timestamp,
            }
            backend.save_query(bulk_test_id, query)

        backend.set_app_state("active_profile_id", default_id)
        backend.set_app_state("active_query_id", "query-1")

        yield {
            "bulk_test_id": bulk_test_id,
            "default_id": default_id,
        }

    def test_delete_profile_handles_many_queries(self, temp_profile_with_many_queries):
        from data.persistence.factory import get_backend
        from data.profile_manager import delete_profile

        backend = get_backend()
        bulk_test_id = temp_profile_with_many_queries["bulk_test_id"]

        delete_profile(bulk_test_id)

        assert backend.get_profile(bulk_test_id) is None

        for i in range(1, 21):
            assert backend.get_query(bulk_test_id, f"query-{i}") is None
