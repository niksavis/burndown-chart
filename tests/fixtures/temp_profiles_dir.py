"""
Temporary profiles directory fixture for test isolation.

This fixture creates a temporary profiles directory that automatically
cleans up after tests, preventing test pollution in the project root.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def temp_profiles_dir():
    """
    Create temporary profiles directory for test isolation.

    Automatically patches the PROFILES_DIR constant in data/profile_manager.py
    to use the temporary directory instead of the project root.

    Yields:
        Path: Absolute path to temporary profiles directory

    Example:
        def test_create_profile(temp_profiles_dir):
            # profiles_dir automatically points to temp location
            result = create_profile("Test Profile")
            assert result[0] is True
            # Cleanup happens automatically
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        profiles_dir = Path(temp_dir) / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        # Patch the profiles directory and file constants
        profiles_file = profiles_dir / "profiles.json"

        with (
            patch("data.profile_manager.PROFILES_DIR", profiles_dir),
            patch("data.profile_manager.PROFILES_FILE", profiles_file),
        ):
            yield profiles_dir


@pytest.fixture
def temp_profiles_dir_with_default():
    """
    Create temporary profiles directory with default profile already migrated.

    Useful for testing scenarios where migration has already occurred.
    Also initializes SQLite database schema to avoid "no such table" errors.

    Yields:
        Path: Temporary profiles directory with default profile structure

    Example:
        def test_switch_to_default(temp_profiles_dir_with_default):
            # Default profile already exists
            default_dir = temp_profiles_dir_with_default / "default"
            assert default_dir.exists()
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        profiles_dir = Path(temp_dir) / "profiles"
        profiles_dir.mkdir(parents=True, exist_ok=True)

        # Create default profile structure
        default_profile_dir = profiles_dir / "default"
        default_queries_dir = default_profile_dir / "queries"
        default_query_dir = default_queries_dir / "default"
        default_query_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        db_path = profiles_dir / "burndown.db"
        from data.migration.schema_manager import initialize_schema

        initialize_schema(db_path=db_path)

        # Patch constants
        profiles_file = profiles_dir / "profiles.json"

        with (
            patch("data.profile_manager.PROFILES_DIR", profiles_dir),
            patch("data.profile_manager.PROFILES_FILE", profiles_file),
            patch("data.database.DB_PATH", db_path),
            patch("data.persistence.factory.DEFAULT_SQLITE_PATH", str(db_path)),
        ):
            # Clear backend singleton to force recreation with new path
            import data.persistence.factory as factory

            factory._backend_instance = None

            yield profiles_dir
