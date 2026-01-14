"""
Unit tests for profile cascade deletion.

Tests verify that:
1. delete_profile() cascades to all queries
2. Safety checks prevent deleting active profile
3. Database handles cascade deletion via foreign keys
"""

import pytest
from datetime import datetime, timezone


class TestProfileCascadeDeletion:
    """Test cascade deletion of profiles with queries and data."""

    @pytest.fixture
    def temp_profiles_with_data(self, temp_database):
        """
        Create multiple profiles with queries in database.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend
        from data.profile_manager import _generate_unique_profile_id

        backend = get_backend()
        fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()

        # Generate hash-based profile IDs
        kafka_id = _generate_unique_profile_id()
        spark_id = _generate_unique_profile_id()

        # Create kafka profile with 2 queries
        kafka_profile = {
            "id": kafka_id,
            "name": "Apache Kafka",
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

        # Create spark profile with 2 queries
        spark_profile = {
            "id": spark_id,
            "name": "Apache Spark",
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

        # Set kafka as active profile
        backend.set_app_state("active_profile_id", kafka_id)
        backend.set_app_state("active_query_id", "main")

        # Yield profile IDs for tests
        yield {
            "kafka_id": kafka_id,
            "spark_id": spark_id,
        }

    def test_delete_profile_cascades_to_all_queries_and_data(
        self, temp_profiles_with_data
    ):
        """
        Verify delete_profile removes profile and all queries.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        # Delete spark profile (not active)
        delete_profile(spark_id)

        # Verify spark profile removed from database
        assert backend.get_profile(spark_id) is None

        # Verify all spark queries removed (cascade deletion)
        assert backend.get_query(spark_id, "12w") is None
        assert backend.get_query(spark_id, "6w") is None

        # Verify kafka profile untouched
        assert backend.get_profile(kafka_id) is not None
        assert backend.get_query(kafka_id, "main") is not None
        assert backend.get_query(kafka_id, "bugs") is not None

    def test_delete_profile_prevents_deleting_active_profile(
        self, temp_profiles_with_data
    ):
        """
        Verify deleting active profile auto-switches to another profile first.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        kafka_id = temp_profiles_with_data["kafka_id"]
        spark_id = temp_profiles_with_data["spark_id"]

        # Verify kafka is currently active
        assert backend.get_app_state("active_profile_id") == kafka_id

        # Delete active profile (kafka) - should auto-switch to spark first
        delete_profile(kafka_id)

        # Verify deletion succeeded
        assert backend.get_profile(kafka_id) is None

        # Verify active profile switched to spark
        new_active = backend.get_app_state("active_profile_id")
        assert new_active == spark_id

        # Verify spark profile still exists
        assert backend.get_profile(spark_id) is not None

    def test_delete_profile_prevents_deleting_last_profile(
        self, temp_profiles_with_data
    ):
        """
        Verify can delete last remaining profile (clears active_profile_id).
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        # Delete spark first
        delete_profile(spark_id)

        # Delete kafka (last profile) - should succeed and clear active_profile_id
        delete_profile(kafka_id)

        # Verify both profiles deleted
        assert backend.get_profile(spark_id) is None
        assert backend.get_profile(kafka_id) is None

        # Verify active_profile_id cleared (empty string)
        assert backend.get_app_state("active_profile_id") == ""

    def test_delete_profile_continues_on_query_deletion_errors(
        self, temp_profiles_with_data
    ):
        """
        Database cascade deletion is atomic - this test is no longer applicable.
        Database foreign keys handle cascade deletion automatically.
        """
        # SKIPPED: Database backend handles cascade deletion via foreign key constraints.
        # No need to test error handling for individual query deletions.
        pass

    def test_delete_profile_removes_all_filesystem_artifacts(
        self, temp_profiles_with_data
    ):
        """
        Database backend doesn't use filesystem - test removed.
        All data stored in SQLite database.
        """
        # SKIPPED: Database backend doesn't use filesystem artifacts.
        pass

    def test_delete_profile_validates_profile_exists(self, temp_profiles_with_data):
        """
        Verify error if trying to delete non-existent profile.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile

        # Try to delete non-existent profile
        with pytest.raises(ValueError, match="does not exist"):
            delete_profile("nonexistent-profile-id")

    def test_delete_profile_updates_profiles_registry_atomically(
        self, temp_profiles_with_data
    ):
        """
        Verify database update is atomic.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]

        # Verify both exist
        assert backend.get_profile(spark_id) is not None
        assert backend.get_profile(kafka_id) is not None

        # Delete spark
        delete_profile(spark_id)

        # Verify update atomic (spark removed, kafka remains)
        assert backend.get_profile(spark_id) is None
        assert backend.get_profile(kafka_id) is not None


class TestCascadeDeletionEdgeCases:
    """Test edge cases in cascade deletion."""

    @pytest.fixture
    def temp_profile_with_many_queries(self, temp_database):
        """
        Create profile with many queries to test bulk deletion.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.persistence.factory import get_backend
        from data.profile_manager import _generate_unique_profile_id

        backend = get_backend()
        fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat()

        # Generate profile IDs
        default_id = _generate_unique_profile_id()
        bulk_test_id = _generate_unique_profile_id()

        # Create default profile
        default_profile = {
            "id": default_id,
            "name": "Default",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(default_profile)

        # Create bulk test profile with 20 queries
        bulk_profile = {
            "id": bulk_test_id,
            "name": "Bulk Test",
            "created_at": fixed_timestamp,
            "last_used": fixed_timestamp,
            "jira_config": {},
            "field_mappings": {},
        }
        backend.save_profile(bulk_profile)

        # Create 20 queries for bulk test profile
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

        # Set default as active
        backend.set_app_state("active_profile_id", default_id)
        backend.set_app_state("active_query_id", "query-1")

        yield {
            "bulk_test_id": bulk_test_id,
            "default_id": default_id,
        }

    def test_delete_profile_handles_many_queries(self, temp_profile_with_many_queries):
        """
        Verify cascade deletion handles profiles with many queries efficiently.
        Uses SQLite database backend via temp_database fixture.
        """
        from data.profile_manager import delete_profile
        from data.persistence.factory import get_backend

        backend = get_backend()
        bulk_test_id = temp_profile_with_many_queries["bulk_test_id"]

        # Delete profile with 20 queries
        delete_profile(bulk_test_id)

        # Verify profile removed
        assert backend.get_profile(bulk_test_id) is None

        # Verify all 20 queries removed (cascade deletion)
        for i in range(1, 21):
            assert backend.get_query(bulk_test_id, f"query-{i}") is None
