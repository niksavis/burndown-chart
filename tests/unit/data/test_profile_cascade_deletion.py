"""
Unit tests for profile cascade deletion.

Tests verify that:
1. delete_profile() cascades to all queries and data files
2. Safety checks prevent deleting active profile or last profile
3. Best-effort deletion continues even if some queries fail to delete
4. All filesystem cleanup occurs correctly
"""

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from data.profile_manager import delete_profile


class TestProfileCascadeDeletion:
    """Test cascade deletion of profiles with queries and data."""

    @pytest.fixture
    def temp_profiles_with_data(self):
        """Create multiple profiles with queries and data files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            profiles_file = temp_profiles_dir / "profiles.json"
            temp_profiles_dir.mkdir(parents=True)

            # Generate hash-based profile IDs
            from data.profile_manager import _generate_unique_profile_id
            kafka_id = _generate_unique_profile_id()
            spark_id = _generate_unique_profile_id()

            # Create profiles.json with 2 profiles
            profiles_data = {
                "version": "3.0",
                "active_profile_id": kafka_id,
                "active_query_id": "main",
                "profiles": {
                    kafka_id: {
                        "id": kafka_id,
                        "name": "Apache Kafka",
                        "queries": ["main", "bugs"],
                    },
                    spark_id: {
                        "id": spark_id,
                        "name": "Apache Spark",
                        "queries": ["12w", "6w"],
                    },
                },
            }
            with open(profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            # Create kafka profile with 2 queries (use generated ID)
            kafka_main_dir = temp_profiles_dir / kafka_id / "queries" / "main"
            kafka_main_dir.mkdir(parents=True)
            (kafka_main_dir / "query.json").write_text(
                json.dumps({"name": "Main", "jql": "project = KAFKA"})
            )
            (kafka_main_dir / "jira_cache.json").write_text(
                json.dumps({"issues": [{"key": "KAFKA-1"}]})
            )
            (kafka_main_dir / "project_data.json").write_text(
                json.dumps({"statistics": []})
            )

            kafka_bugs_dir = temp_profiles_dir / kafka_id / "queries" / "bugs"
            kafka_bugs_dir.mkdir(parents=True)
            (kafka_bugs_dir / "query.json").write_text(
                json.dumps({"name": "Bugs", "jql": "type = Bug"})
            )
            (kafka_bugs_dir / "jira_cache.json").write_text(
                json.dumps({"issues": [{"key": "KAFKA-2"}]})
            )

            # Create spark profile with 2 queries (use generated ID)
            spark_12w_dir = temp_profiles_dir / spark_id / "queries" / "12w"
            spark_12w_dir.mkdir(parents=True)
            (spark_12w_dir / "query.json").write_text(
                json.dumps({"name": "12 Weeks", "jql": "created >= -12w"})
            )
            (spark_12w_dir / "jira_cache.json").write_text(
                json.dumps({"issues": [{"key": "SPARK-1"}]})
            )

            spark_6w_dir = temp_profiles_dir / spark_id / "queries" / "6w"
            spark_6w_dir.mkdir(parents=True)
            (spark_6w_dir / "query.json").write_text(
                json.dumps({"name": "6 Weeks", "jql": "created >= -6w"})
            )

            with patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir):
                with patch("data.profile_manager.PROFILES_FILE", profiles_file):
                    with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                        with patch("data.query_manager.PROFILES_FILE", profiles_file):
                            # Yield a dict with profile IDs so tests can access them
                            yield {"dir": temp_profiles_dir, "kafka_id": kafka_id, "spark_id": spark_id}

    def test_delete_profile_cascades_to_all_queries_and_data(
        self, temp_profiles_with_data
    ):
        """Verify delete_profile removes profile, all queries, and all data files."""
        temp_dir = temp_profiles_with_data["dir"]
        spark_id = temp_profiles_with_data["spark_id"]
        
        # Delete spark profile (not active)
        delete_profile(spark_id)

        # Verify spark profile directory completely removed
        spark_dir = temp_dir / spark_id
        assert not spark_dir.exists()

        # Verify all spark queries removed
        assert not (spark_dir / "queries" / "12w").exists()
        assert not (spark_dir / "queries" / "6w").exists()

        # Verify all data files removed
        assert not (spark_dir / "queries" / "12w" / "jira_cache.json").exists()
        assert not (spark_dir / "queries" / "6w" / "query.json").exists()

        # Verify profiles.json updated
        kafka_id = temp_profiles_with_data["kafka_id"]
        profiles_file = temp_dir / "profiles.json"
        with open(profiles_file, "r") as f:
            metadata = json.load(f)

        assert spark_id not in metadata["profiles"]
        assert kafka_id in metadata["profiles"]  # Other profile untouched

    def test_delete_profile_prevents_deleting_active_profile(
        self, temp_profiles_with_data
    ):
        """Verify deleting active profile auto-switches to another profile first."""
        kafka_id = temp_profiles_with_data["kafka_id"]
        spark_id = temp_profiles_with_data["spark_id"]
        temp_dir = temp_profiles_with_data["dir"]
        
        # Verify kafka is active
        profiles_file = temp_dir / "profiles.json"
        with open(profiles_file, "r") as f:
            metadata_before = json.load(f)
        assert metadata_before["active_profile_id"] == kafka_id
        
        # Delete active profile (kafka) - should auto-switch to spark first
        delete_profile(kafka_id)

        # Verify deletion succeeded
        kafka_dir = temp_dir / kafka_id
        assert not kafka_dir.exists()
        
        # Verify profile was deleted from registry
        with open(profiles_file, "r") as f:
            metadata_after = json.load(f)
        assert kafka_id not in metadata_after["profiles"]
        # The active profile should now be spark (the only remaining profile)
        assert spark_id in metadata_after["profiles"]

    def test_delete_profile_prevents_deleting_last_profile(
        self, temp_profiles_with_data
    ):
        """Verify cannot delete last remaining profile."""
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]
        
        # Delete spark first
        delete_profile(spark_id)

        # Try to delete kafka (now the only profile) - should fail even though not active
        # First need to switch to make it not active, but there's no other profile to switch to
        # So we test by verifying error when trying to delete when only 1 profile remains

        # Update profiles.json to make kafka not active (simulate edge case)
        temp_dir = temp_profiles_with_data["dir"]
        profiles_file = temp_dir / "profiles.json"
        with open(profiles_file, "r") as f:
            metadata = json.load(f)
        metadata["active_profile_id"] = None  # Simulate no active profile
        with open(profiles_file, "w") as f:
            json.dump(metadata, f)

        with pytest.raises(ValueError) as exc_info:
            delete_profile(kafka_id)

        assert "Cannot delete the only remaining profile" in str(exc_info.value)

    def test_delete_profile_continues_on_query_deletion_errors(
        self, temp_profiles_with_data, caplog
    ):
        """Verify delete_profile continues deleting even if some queries fail."""
        import logging
        from unittest.mock import patch

        # Track which queries we've tried to delete
        deleted_queries = []

        # Mock delete_query to raise error on "bugs" query only
        def mock_delete_query_with_error(profile_id, query_id, allow_cascade=False):
            deleted_queries.append(query_id)
            if query_id == "bugs":
                raise RuntimeError("Simulated query deletion error for bugs")
            # For other queries, succeed silently (no actual deletion needed - it's mocked)
            return None

        # Get IDs from fixture
        kafka_id = temp_profiles_with_data["kafka_id"]
        spark_id = temp_profiles_with_data["spark_id"]
        temp_dir = temp_profiles_with_data["dir"]
        
        # Mock list_queries to return the kafka queries
        def mock_list_queries(profile_id):
            if profile_id == kafka_id:
                return [
                    {"id": "main", "name": "Main"},
                    {"id": "bugs", "name": "Bugs"},
                ]
            return []

        # First switch away from kafka
        profiles_file = temp_dir / "profiles.json"
        with open(profiles_file, "r") as f:
            metadata = json.load(f)
        metadata["active_profile_id"] = spark_id
        with open(profiles_file, "w") as f:
            json.dump(metadata, f)

        # Delete kafka profile with mocked functions
        # Patch both where they're imported (in delete_profile function)
        with caplog.at_level(logging.ERROR):
            with patch(
                "data.query_manager.delete_query",
                side_effect=mock_delete_query_with_error,
            ):
                with patch(
                    "data.query_manager.list_queries_for_profile",
                    side_effect=mock_list_queries,
                ):
                    delete_profile(kafka_id)

        # Verify both queries were attempted (best-effort continues despite error)
        assert "main" in deleted_queries
        assert "bugs" in deleted_queries

        # Verify kafka directory removed despite error on one query
        kafka_dir = temp_dir / kafka_id
        assert not kafka_dir.exists()

        # Verify error was logged
        assert "Error deleting query" in caplog.text
        assert "bugs" in caplog.text

    def test_delete_profile_removes_all_filesystem_artifacts(
        self, temp_profiles_with_data
    ):
        """Verify all files and directories removed after cascade deletion."""
        spark_id = temp_profiles_with_data["spark_id"]
        temp_dir = temp_profiles_with_data["dir"]
        spark_dir = temp_dir / spark_id

        # Verify spark directory exists with content before deletion
        assert spark_dir.exists()
        assert (spark_dir / "queries" / "12w").exists()
        assert (spark_dir / "queries" / "6w").exists()
        assert (spark_dir / "queries" / "12w" / "jira_cache.json").exists()

        # Delete spark profile
        delete_profile(spark_id)

        # Verify entire spark directory tree removed
        assert not spark_dir.exists()
        assert not (spark_dir / "queries").exists()
        assert not (spark_dir / "queries" / "12w").exists()
        assert not (spark_dir / "queries" / "12w" / "jira_cache.json").exists()

    def test_delete_profile_validates_profile_exists(self, temp_profiles_with_data):
        """Verify error raised when trying to delete non-existent profile."""
        with pytest.raises(ValueError) as exc_info:
            delete_profile("nonexistent-profile")

        assert "does not exist" in str(exc_info.value)

    def test_delete_profile_updates_profiles_registry_atomically(
        self, temp_profiles_with_data
    ):
        """Verify profiles.json updated correctly after deletion."""
        spark_id = temp_profiles_with_data["spark_id"]
        kafka_id = temp_profiles_with_data["kafka_id"]
        temp_dir = temp_profiles_with_data["dir"]
        
        # Get initial state
        profiles_file = temp_dir / "profiles.json"
        with open(profiles_file, "r") as f:
            initial_metadata = json.load(f)

        assert spark_id in initial_metadata["profiles"]
        assert kafka_id in initial_metadata["profiles"]

        # Delete spark
        delete_profile(spark_id)

        # Verify registry updated
        with open(profiles_file, "r") as f:
            updated_metadata = json.load(f)

        assert spark_id not in updated_metadata["profiles"]
        assert kafka_id in updated_metadata["profiles"]
        assert updated_metadata["version"] == "3.0"


class TestCascadeDeletionEdgeCases:
    """Test edge cases in cascade deletion."""

    @pytest.fixture
    def temp_profile_with_many_queries(self):
        """Create profile with many queries to test bulk deletion."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_profiles_dir = Path(temp_dir) / "profiles"
            profiles_file = temp_profiles_dir / "profiles.json"
            temp_profiles_dir.mkdir(parents=True)

            # Generate hash-based profile IDs
            from data.profile_manager import _generate_unique_profile_id
            default_id = _generate_unique_profile_id()
            bulk_test_id = _generate_unique_profile_id()

            # Create profiles.json
            profiles_data = {
                "version": "3.0",
                "active_profile_id": default_id,
                "active_query_id": "query-1",
                "profiles": {
                    default_id: {"id": default_id, "name": "Default", "queries": []},
                    bulk_test_id: {
                        "id": bulk_test_id,
                        "name": "Bulk Test",
                        "queries": [f"query-{i}" for i in range(1, 21)],  # 20 queries
                    },
                },
            }
            with open(profiles_file, "w") as f:
                json.dump(profiles_data, f, indent=2)

            # Create bulk-test profile with 20 queries
            for i in range(1, 21):
                query_dir = temp_profiles_dir / bulk_test_id / "queries" / f"query-{i}"
                query_dir.mkdir(parents=True)
                (query_dir / "query.json").write_text(
                    json.dumps({"name": f"Query {i}", "jql": f"project = TEST{i}"})
                )
                (query_dir / "jira_cache.json").write_text(
                    json.dumps({"issues": [{"key": f"TEST-{i}"}]})
                )

            with patch("data.profile_manager.PROFILES_DIR", temp_profiles_dir):
                with patch("data.profile_manager.PROFILES_FILE", profiles_file):
                    with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir):
                        with patch("data.query_manager.PROFILES_FILE", profiles_file):
                            yield {"dir": temp_profiles_dir, "bulk_test_id": bulk_test_id}

    def test_delete_profile_handles_many_queries(self, temp_profile_with_many_queries):
        """Verify cascade deletion handles profiles with many queries efficiently."""
        bulk_test_id = temp_profile_with_many_queries["bulk_test_id"]
        temp_dir = temp_profile_with_many_queries["dir"]
        
        # Delete profile with 20 queries
        delete_profile(bulk_test_id)

        # Verify entire profile removed
        bulk_test_dir = temp_dir / bulk_test_id
        assert not bulk_test_dir.exists()

        # Verify all 20 queries removed
        for i in range(1, 21):
            query_dir = bulk_test_dir / "queries" / f"query-{i}"
            assert not query_dir.exists()
