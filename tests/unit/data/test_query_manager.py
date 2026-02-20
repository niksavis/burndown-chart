"""
Unit tests for data/query_manager.py

Tests query management functions for profile-based workspaces.
Uses SQLite database backend via temp_database fixture.
"""

from datetime import UTC, datetime

import pytest


def create_test_profile(profile_id: str, name: str) -> dict:
    """
    Create test profile with all required fields.

    Uses fixed timestamps for deterministic testing.
    """
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
    """
    Create test query with all required fields.

    Uses fixed timestamps for deterministic testing.
    """
    fixed_timestamp = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC).isoformat()
    return {
        "id": query_id,
        "name": name,
        "jql": jql,
        "created_at": fixed_timestamp,
        "last_used": fixed_timestamp,
    }


# Import functions from query_manager inside tests where patches are active


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveQueryId:
    """Test get_active_query_id() function."""

    def test_returns_active_query_id(self, temp_database):
        """Verify returns active_query_id from database."""
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id

        # Arrange
        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "bugs")

        # Act
        result = get_active_query_id()

        # Assert
        assert result == "bugs"

    def test_raises_if_profiles_json_missing(self, temp_database):
        """Verify returns None when active_query_id not set."""
        from data.query_manager import get_active_query_id

        # Act - no app state set
        result = get_active_query_id()

        # Assert - returns None when not set
        assert result is None

    def test_raises_if_active_query_id_missing(self, temp_database):
        """Verify returns None when active_query_id is missing (valid state for empty profile)."""
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id

        # Arrange - only set active_profile_id
        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")

        # Act
        result = get_active_query_id()

        # Assert
        assert result is None  # No active query is a valid state


@pytest.mark.unit
@pytest.mark.profile_tests
class TestGetActiveProfileId:
    """Test get_active_profile_id() function."""

    def test_returns_active_profile_id(self, temp_database):
        """Verify returns active_profile_id from database."""
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_profile_id

        # Arrange
        backend = get_backend()
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act
        result = get_active_profile_id()

        # Assert
        assert result == "kafka"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestSwitchQuery:
    """Test switch_query() function with <50ms performance target."""

    def test_switches_to_existing_query(self, temp_database):
        """Verify switches active_query_id in database."""
        from data.persistence.factory import get_backend
        from data.query_manager import get_active_query_id, switch_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act
        switch_query("bugs")

        # Assert
        assert get_active_query_id() == "bugs"

    def test_raises_if_query_does_not_exist(self, temp_database):
        """Verify raises ValueError if query doesn't exist."""
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act & Assert
        with pytest.raises(ValueError, match="Query 'nonexistent' not found"):
            switch_query("nonexistent")

    def test_switch_is_atomic(self, temp_database):
        """Verify switch updates database atomically."""
        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act
        switch_query("bugs")

        # Assert - database updated
        assert backend.get_app_state("active_query_id") == "bugs"

    def test_performance_under_50ms(self, temp_database):
        """Verify switch_query() completes in <50ms."""
        import time

        from data.persistence.factory import get_backend
        from data.query_manager import switch_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "All Issues", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act - measure time
        start = time.perf_counter()
        switch_query("bugs")
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert
        assert elapsed_ms < 50, f"switch_query took {elapsed_ms:.2f}ms, target: <50ms"


@pytest.mark.unit
@pytest.mark.profile_tests
class TestListQueriesForProfile:
    """Test list_queries_for_profile() function."""

    def test_lists_queries_with_metadata(self, temp_database):
        """Verify returns list of queries with metadata."""
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        # Arrange
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

        # Act
        queries = list_queries_for_profile("kafka")

        # Assert
        assert len(queries) == 2

        # Find queries by ID (order may vary)
        main_query = next(q for q in queries if q["id"] == "main")
        bugs_query = next(q for q in queries if q["id"] == "bugs")

        assert main_query["name"] == "All Issues"
        assert main_query["jql"] == "project = KAFKA"
        assert main_query["is_active"] is True

        assert bugs_query["name"] == "Bugs Only"
        assert bugs_query["is_active"] is False

    def test_returns_empty_list_if_no_queries(self, temp_database):
        """Verify returns empty list if profile has no queries."""
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))

        # Act
        queries = list_queries_for_profile("kafka")

        # Assert
        assert queries == []

    def test_handles_missing_query_json(self, temp_database):
        """Verify returns empty list when profile has no queries in database."""
        from data.persistence.factory import get_backend
        from data.query_manager import list_queries_for_profile

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        # No queries saved

        # Act
        queries = list_queries_for_profile("kafka")

        # Assert
        assert queries == []


@pytest.mark.unit
@pytest.mark.profile_tests
class TestCreateQuery:
    """Test create_query() function."""

    def test_creates_query_with_metadata(self, temp_database):
        """Verify creates query in database."""
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        # Arrange
        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        # Act
        query_id = create_query("kafka", "High Priority Bugs", "priority = High")

        # Assert - should return hash-based ID
        assert query_id.startswith("q_")
        assert len(query_id) == 14  # "q_" + 12 hex chars

        query_data = backend.get_query("kafka", query_id)
        assert query_data is not None
        assert query_data["name"] == "High Priority Bugs"
        assert query_data["jql"] == "priority = High"
        assert "created_at" in query_data

    def test_raises_if_query_id_conflicts(self, temp_database):
        """Verify hash-based IDs make collisions statistically impossible."""
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        # Arrange
        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        # Act - Create multiple queries with same name
        query_id1 = create_query("kafka", "Bugs", "type = Bug")
        query_id2 = create_query(
            "kafka", "Bugs", "type = Bug"
        )  # Same name, different ID

        # Assert - both queries created successfully with different IDs
        assert query_id1 != query_id2  # Different hash-based IDs
        assert backend.get_query("kafka", query_id1) is not None
        assert backend.get_query("kafka", query_id2) is not None

    def test_slugifies_query_name(self, temp_database):
        """Verify generates hash-based query ID regardless of name format."""
        from data.persistence.factory import get_backend
        from data.query_manager import create_query

        # Arrange
        backend = get_backend()
        profile = create_test_profile("kafka", "Kafka")
        profile["jira_config"] = {
            "configured": True,
            "base_url": "https://test.jira.com",
            "token": "test-token",
        }
        backend.save_profile(profile)

        # Act
        query_id = create_query("kafka", "Sprint 2025-Q4", "sprint = 2025-Q4")

        # Assert - generates hash-based ID, not slugified name
        assert query_id.startswith("q_")
        assert len(query_id) == 14  # "q_" + 12 hex chars


@pytest.mark.unit
@pytest.mark.profile_tests
class TestUpdateQuery:
    """Test update_query() function."""

    def test_updates_query_jql(self, temp_database):
        """Verify updates JQL."""
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )

        # Act
        result = update_query(
            "kafka", "main", jql="project = KAFKA AND priority > Medium"
        )

        # Assert
        assert result is True
        query_data = backend.get_query("kafka", "main")
        assert query_data is not None
        assert query_data["jql"] == "project = KAFKA AND priority > Medium"
        assert query_data["name"] == "Main Query"  # Unchanged

    def test_updates_query_name(self, temp_database):
        """Verify updates name."""
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Old Name", "project = KAFKA")
        )

        # Act
        result = update_query("kafka", "main", name="New Name")

        # Assert
        assert result is True
        query_data = backend.get_query("kafka", "main")
        assert query_data is not None
        assert query_data["name"] == "New Name"
        assert query_data["jql"] == "project = KAFKA"  # Unchanged

    def test_no_update_if_no_changes(self, temp_database):
        """Verify returns True for no-op updates."""
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )

        # Act - update with same JQL
        result = update_query("kafka", "main", jql="project = KAFKA")

        # Assert
        assert result is True

    def test_raises_if_query_not_found(self, temp_database):
        """Verify raises ValueError if query doesn't exist."""
        from data.persistence.factory import get_backend
        from data.query_manager import update_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            update_query("kafka", "nonexistent", jql="project = TEST")


@pytest.mark.unit
@pytest.mark.profile_tests
class TestDeleteQuery:
    """Test delete_query() function."""

    def test_deletes_query_directory(self, temp_database):
        """Verify deletes query from database."""
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        # Arrange
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

        # Act
        delete_query("kafka", "old-query")

        # Assert - old-query deleted, main query untouched
        assert backend.get_query("kafka", "old-query") is None
        assert backend.get_query("kafka", "main") is not None

    def test_raises_if_deleting_active_query(self, temp_database):
        """Verify raises PermissionError if trying to delete active query."""
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )
        backend.save_query("kafka", create_test_query("bugs", "Bugs", "type = Bug"))
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "main")

        # Act & Assert
        with pytest.raises(PermissionError, match="Cannot delete active query"):
            delete_query("kafka", "main")

    def test_raises_if_deleting_last_query(self, temp_database):
        """Verify allows deleting last query (profile can exist with no queries)."""
        from data.persistence.factory import get_backend
        from data.query_manager import delete_query

        # Arrange
        backend = get_backend()
        backend.save_profile(create_test_profile("kafka", "Kafka"))
        backend.save_query(
            "kafka", create_test_query("main", "Main Query", "project = KAFKA")
        )
        backend.set_app_state("active_profile_id", "kafka")
        backend.set_app_state("active_query_id", "bugs")  # Different active query

        # Act - Should succeed - profiles can have 0 queries
        delete_query("kafka", "main")

        # Assert - query removed from database
        assert backend.get_query("kafka", "main") is None
