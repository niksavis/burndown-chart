"""
Unit tests for data/query_manager.py

Tests query management functions for profile-based workspaces.
"""

import json
import pytest

# Import functions from query_manager inside tests where patches are active


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveQueryId:
    """Test get_active_query_id() function."""

    def test_returns_active_query_id(self, temp_profiles_dir_with_default):
        """Verify returns active_query_id from profiles.json."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "bugs",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act - patch query_manager constants, then import
        with patch("data.query_manager.PROFILES_FILE", profiles_file):
            from data.query_manager import get_active_query_id

            result = get_active_query_id()

        # Assert
        assert result == "bugs"

    def test_raises_if_profiles_json_missing(self, temp_profiles_dir):
        """Verify raises ValueError if profiles.json doesn't exist."""
        from unittest.mock import patch

        # Act & Assert - patch constants, then import
        profiles_file = temp_profiles_dir / "profiles.json"
        with patch("data.query_manager.PROFILES_FILE", profiles_file):
            from data.query_manager import get_active_query_id

            with pytest.raises(ValueError, match="profiles.json not found"):
                get_active_query_id()

    def test_raises_if_active_query_id_missing(self, temp_profiles_dir_with_default):
        """Verify raises ValueError if active_query_id key missing."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            # Missing active_query_id
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act & Assert - patch constants, then import
        with patch("data.query_manager.PROFILES_FILE", profiles_file):
            from data.query_manager import get_active_query_id

            with pytest.raises(ValueError, match="active_query_id not found"):
                get_active_query_id()


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveProfileId:
    """Test get_active_profile_id() function."""

    def test_returns_active_profile_id(self, temp_profiles_dir_with_default):
        """Verify returns active_profile_id from profiles.json."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Act - patch constants, then import
        with patch("data.query_manager.PROFILES_FILE", profiles_file):
            from data.query_manager import get_active_profile_id

            result = get_active_profile_id()

        # Assert
        assert result == "kafka"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestSwitchQuery:
    """Test switch_query() function with <50ms performance target."""

    def test_switches_to_existing_query(self, temp_profiles_dir_with_default):
        """Verify switches active_query_id in profiles.json."""
        from unittest.mock import patch

        # Arrange: Create profiles.json with two queries
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Create query directories
        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)
        (kafka_dir / "bugs").mkdir(parents=True)

        # Act - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import switch_query, get_active_query_id

            switch_query("bugs")

            # Assert
            assert get_active_query_id() == "bugs"

        # Verify profiles.json updated
        with open(profiles_file, "r") as f:
            updated_data = json.load(f)
        assert updated_data["active_query_id"] == "bugs"

    def test_raises_if_query_does_not_exist(self, temp_profiles_dir_with_default):
        """Verify raises ValueError if query directory doesn't exist."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        # Create only main query
        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)

        # Act & Assert - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import switch_query

            with pytest.raises(ValueError, match="Query 'nonexistent' not found"):
                switch_query("nonexistent")

    def test_switch_is_atomic(self, temp_profiles_dir_with_default):
        """Verify switch uses atomic write (temp file + rename)."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)
        (kafka_dir / "bugs").mkdir(parents=True)

        # Act - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import switch_query

            switch_query("bugs")

        # Assert: Temp file should not exist after successful switch
        temp_file = profiles_file.with_suffix(".tmp")
        assert not temp_file.exists()

    def test_performance_under_50ms(self, temp_profiles_dir_with_default):
        """Verify switch_query() completes in <50ms."""
        import time
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)
        (kafka_dir / "bugs").mkdir(parents=True)

        # Act: Measure time - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import switch_query

            start = time.perf_counter()
            switch_query("bugs")
            elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert elapsed_ms < 50, f"switch_query took {elapsed_ms:.2f}ms, target: <50ms"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestListQueriesForProfile:
    """Test list_queries_for_profile() function."""

    def test_lists_queries_with_metadata(self, temp_profiles_dir_with_default):
        """Verify returns list of queries with metadata."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        main_dir = kafka_dir / "main"
        bugs_dir = kafka_dir / "bugs"
        main_dir.mkdir(parents=True)
        bugs_dir.mkdir(parents=True)

        # Create query.json files
        main_query = {
            "name": "All Issues",
            "jql": "project = KAFKA",
            "created_at": "2025-11-01T10:00:00Z",
        }
        (main_dir / "query.json").write_text(json.dumps(main_query))

        bugs_query = {
            "name": "Bugs Only",
            "jql": "project = KAFKA AND type = Bug",
            "created_at": "2025-11-10T14:30:00Z",
        }
        (bugs_dir / "query.json").write_text(json.dumps(bugs_query))

        # Act - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import list_queries_for_profile

            queries = list_queries_for_profile("kafka")

        # Assert
        assert len(queries) == 2
        assert queries[0]["id"] == "main"
        assert queries[0]["name"] == "All Issues"
        assert queries[0]["jql"] == "project = KAFKA"
        assert queries[0]["is_active"] is True

        assert queries[1]["id"] == "bugs"
        assert queries[1]["name"] == "Bugs Only"
        assert queries[1]["is_active"] is False

    def test_returns_empty_list_if_no_queries(self, temp_profiles_dir_with_default):
        """Verify returns empty list if profile has no queries."""
        from unittest.mock import patch

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        kafka_dir.mkdir(parents=True)

        # Act - patch constants, then import and call
        with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default):
            from data.query_manager import list_queries_for_profile

            queries = list_queries_for_profile("kafka")

        # Assert
        assert queries == []

    def test_handles_missing_query_json(self, temp_profiles_dir_with_default):
        """Verify gracefully handles queries without query.json."""
        from unittest.mock import patch

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "orphan").mkdir(parents=True)
        # No query.json created

        # Act - patch constants, then import and call
        with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default):
            from data.query_manager import list_queries_for_profile

            queries = list_queries_for_profile("kafka")

        # Assert
        assert len(queries) == 1
        assert queries[0]["id"] == "orphan"
        assert queries[0]["name"] == "Orphan"  # Titleized from ID


@pytest.mark.unit
@pytest.mark.profile_tests
class TestCreateQuery:
    """Test create_query() function."""

    def test_creates_query_with_metadata(self, temp_profiles_dir_with_default):
        """Verify creates query directory and query.json."""
        from unittest.mock import patch

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        kafka_dir.mkdir(parents=True)

        # Act - patch constants, then import and call
        with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default):
            from data.query_manager import create_query

            query_id = create_query("kafka", "High Priority Bugs", "priority = High")

        # Assert
        assert query_id == "high-priority-bugs"

        query_dir = kafka_dir / "queries" / "high-priority-bugs"
        assert query_dir.exists()

        query_file = query_dir / "query.json"
        assert query_file.exists()

        with open(query_file, "r") as f:
            query_data = json.load(f)

        assert query_data["name"] == "High Priority Bugs"
        assert query_data["jql"] == "priority = High"
        assert "created_at" in query_data

    def test_raises_if_query_id_conflicts(self, temp_profiles_dir_with_default):
        """Verify raises ValueError if query ID already exists."""
        from unittest.mock import patch

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries" / "bugs"
        kafka_dir.mkdir(parents=True)

        # Act & Assert - patch constants, then import and call
        with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default):
            from data.query_manager import create_query

            with pytest.raises(ValueError, match="already exists"):
                create_query("kafka", "Bugs", "type = Bug")

    def test_slugifies_query_name(self, temp_profiles_dir_with_default):
        """Verify converts name to valid query ID."""
        from unittest.mock import patch

        # Arrange
        kafka_dir = temp_profiles_dir_with_default / "kafka"
        kafka_dir.mkdir(parents=True)

        # Act - patch constants, then import and call
        with patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default):
            from data.query_manager import create_query

            query_id = create_query("kafka", "Sprint 2025-Q4", "sprint = 2025-Q4")

        # Assert
        assert query_id == "sprint-2025-q4"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestDeleteQuery:
    """Test delete_query() function."""

    def test_deletes_query_directory(self, temp_profiles_dir_with_default):
        """Verify deletes query directory and all contents."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)
        old_query_dir = kafka_dir / "old-query"
        old_query_dir.mkdir(parents=True)
        (old_query_dir / "jira_cache.json").write_text("{}")

        # Act - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import delete_query

            delete_query("kafka", "old-query")

        # Assert
        assert not old_query_dir.exists()
        assert (kafka_dir / "main").exists()  # Other query untouched

    def test_raises_if_deleting_active_query(self, temp_profiles_dir_with_default):
        """Verify raises PermissionError if trying to delete active query."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "main",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)
        (kafka_dir / "bugs").mkdir(parents=True)

        # Act & Assert - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import delete_query

            with pytest.raises(PermissionError, match="Cannot delete active query"):
                delete_query("kafka", "main")

    def test_raises_if_deleting_last_query(self, temp_profiles_dir_with_default):
        """Verify raises ValueError if trying to delete only query."""
        from unittest.mock import patch

        # Arrange
        profiles_file = temp_profiles_dir_with_default / "profiles.json"
        profiles_data = {
            "active_profile_id": "kafka",
            "active_query_id": "bugs",
            "profiles": {},
        }
        profiles_file.write_text(json.dumps(profiles_data))

        kafka_dir = temp_profiles_dir_with_default / "kafka" / "queries"
        (kafka_dir / "main").mkdir(parents=True)

        # Act & Assert - patch constants, then import and call
        with (
            patch("data.query_manager.PROFILES_FILE", profiles_file),
            patch("data.query_manager.PROFILES_DIR", temp_profiles_dir_with_default),
        ):
            from data.query_manager import delete_query

            with pytest.raises(ValueError, match="Cannot delete last query"):
                delete_query("kafka", "main")
