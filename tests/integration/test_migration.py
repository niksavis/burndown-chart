"""
Integration tests for first-time migration to profiles structure.

Tests the automatic migration from root-level data files to the new
profiles/default/queries/main/ structure without data loss.

Note: All tests must import profile_manager constants AFTER changing directory
(os.chdir(tmp_path)) because PROFILES_DIR uses Path().absolute() which resolves
at import time based on current working directory.
"""

import json
import time

import pytest


@pytest.mark.integration
@pytest.mark.migration_tests
class TestMigrationBasics:
    """Test basic migration functionality (T012-T014)."""

    def test_migrate_to_profiles_moves_all_files(self, temp_profiles_dir, tmp_path):
        """
        T012: Verify all root-level files move to profiles/default/queries/main/.

        Files to migrate:
        - app_settings.json
        - jira_cache.json
        - project_data.json
        - metrics_snapshots.json
        - cache/ directory
        """
        # Arrange: Create root-level files (simulating existing installation)
        root_files = {
            "app_settings.json": {"pert_factor": 1.2, "deadline": "2025-12-31"},
            "jira_cache.json": {"version": "2.0", "issues": []},
            "project_data.json": {"statistics": []},
            "metrics_snapshots.json": {"snapshots": []},
        }

        for filename, content in root_files.items():
            file_path = tmp_path / filename
            file_path.write_text(json.dumps(content))

        # Create cache directory with sample file
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "sample_cache.json").write_text('{"data": "test"}')

        # Change directory BEFORE importing (so PROFILES_DIR resolves correctly)
        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache to force re-import with new working directory
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            # Act: Import and run migration (import AFTER chdir so paths resolve correctly)
            from data.migration import migrate_to_profiles
            from data.profile_manager import (
                PROFILES_DIR,
                PROFILES_FILE,
                DEFAULT_PROFILE_ID,
                DEFAULT_QUERY_ID,
            )

            migrate_to_profiles()

            # Assert: Files moved to default profile structure
            default_query_dir = (
                PROFILES_DIR / DEFAULT_PROFILE_ID / "queries" / DEFAULT_QUERY_ID
            )

            for filename in root_files.keys():
                migrated_file = default_query_dir / filename
                assert migrated_file.exists(), f"{filename} not migrated"

                # Verify content preserved
                original_content = root_files[filename]
                migrated_content = json.loads(migrated_file.read_text())
                assert migrated_content == original_content

            # Verify cache directory migrated
            migrated_cache_dir = default_query_dir / "cache"
            assert migrated_cache_dir.exists()
            assert (migrated_cache_dir / "sample_cache.json").exists()

            # Verify profiles.json created
            assert PROFILES_FILE.exists()
            profiles_data = json.loads(PROFILES_FILE.read_text())
            assert profiles_data["active_profile_id"] == DEFAULT_PROFILE_ID
            assert profiles_data["active_query_id"] == DEFAULT_QUERY_ID
        finally:
            os.chdir(original_cwd)

    def test_migration_creates_backup(self, temp_profiles_dir, tmp_path):
        """T013: Verify .backup copies created before migration."""
        # Arrange: Create root-level file
        app_settings = tmp_path / "app_settings.json"
        app_settings.write_text('{"pert_factor": 1.5}')

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            # Act: Run migration
            from data.migration import migrate_to_profiles

            migrate_to_profiles()

            # Assert: Backup file created
            backup_file = tmp_path / "app_settings.json.backup"
            assert backup_file.exists()

            # Verify backup content matches original
            backup_content = json.loads(backup_file.read_text())
            assert backup_content == {"pert_factor": 1.5}
        finally:
            os.chdir(original_cwd)

    def test_migration_idempotent(self, temp_profiles_dir, tmp_path):
        """T014: Verify running migration twice does nothing on second run."""
        # Arrange: Create root-level file
        app_settings = tmp_path / "app_settings.json"
        app_settings.write_text('{"pert_factor": 1.5}')

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            from data.migration import migrate_to_profiles  # Act: Run migration twice

            result1 = migrate_to_profiles()
            result2 = migrate_to_profiles()

            # Assert: First run migrates, second run skips
            assert result1 is True, "First migration should succeed"
            assert result2 is False, "Second migration should skip (already migrated)"

            # Verify only one backup created (from first run)
            backup_files = list(tmp_path.glob("*.backup"))
            assert len(backup_files) == 1
        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
@pytest.mark.migration_tests
class TestMigrationDataIntegrity:
    """Test data preservation during migration (T015-T016)."""

    def test_migration_data_preservation(self, temp_profiles_dir, tmp_path):
        """T015: Verify checksums match before/after migration."""
        # Arrange: Create file with known content
        import hashlib

        original_data = {
            "statistics": [{"date": "2025-11-01", "completed_items": 5}] * 100,
            "metadata": {"version": "1.0", "last_updated": "2025-11-13"},
        }

        project_data_file = tmp_path / "project_data.json"
        project_data_file.write_text(json.dumps(original_data))

        # Calculate original checksum
        original_checksum = hashlib.sha256(project_data_file.read_bytes()).hexdigest()

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            # Act: Run migration
            from data.migration import migrate_to_profiles
            from data.profile_manager import (
                PROFILES_DIR,
                DEFAULT_PROFILE_ID,
                DEFAULT_QUERY_ID,
            )

            migrate_to_profiles()

            # Assert: Migrated file has same checksum
            migrated_file = (
                PROFILES_DIR
                / DEFAULT_PROFILE_ID
                / "queries"
                / DEFAULT_QUERY_ID
                / "project_data.json"
            )
            migrated_checksum = hashlib.sha256(migrated_file.read_bytes()).hexdigest()

            assert migrated_checksum == original_checksum, (
                "Data corrupted during migration"
            )
        finally:
            os.chdir(original_cwd)

    def test_migration_rollback_on_failure(self, temp_profiles_dir, tmp_path):
        """T016: Verify rollback from backup if migration fails."""
        # Arrange: Create root-level files
        app_settings = tmp_path / "app_settings.json"
        app_settings.write_text('{"pert_factor": 1.5}')

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            from data.migration import migrate_to_profiles, rollback_migration
            from data.profile_manager import PROFILES_FILE
            from unittest.mock import patch

            # Act: Simulate failure during migration
            with patch(
                "data.migration.move_root_files_to_default_profile"
            ) as mock_move:
                mock_move.side_effect = IOError("Disk full")

                with pytest.raises(IOError):
                    migrate_to_profiles()

            # Act: Perform rollback
            rollback_migration()

            # Assert: Original file restored from backup
            assert app_settings.exists()
            restored_content = json.loads(app_settings.read_text())
            assert restored_content == {"pert_factor": 1.5}

            # Assert: profiles.json not created (migration failed)
            assert not PROFILES_FILE.exists()
        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
@pytest.mark.migration_tests
@pytest.mark.performance
class TestMigrationPerformance:
    """Test migration performance requirements (T017)."""

    def test_migration_completes_under_5_seconds(self, temp_profiles_dir, tmp_path):
        """T017: Verify migration completes <5s with 50MB cache data."""
        # Arrange: Create large cache file (~50MB)
        large_cache_data = {
            "version": "2.0",
            "jql_query": "project = TEST",
            "issues": [
                {
                    "key": f"TEST-{i}",
                    "fields": {
                        "summary": "Test issue " + ("x" * 2000),  # Pad to increase size
                        "description": "Long description " * 200,
                        "created": "2025-11-01T10:00:00.000+0000",
                        "customfield_10001": "Extra field " * 50,
                        "customfield_10002": "More data " * 50,
                    },
                }
                for i in range(10000)  # ~50MB of data
            ],
        }

        jira_cache = tmp_path / "jira_cache.json"
        jira_cache.write_text(json.dumps(large_cache_data))

        # Verify file is ~50MB
        file_size_mb = jira_cache.stat().st_size / (1024 * 1024)
        assert file_size_mb >= 45, f"Test file too small: {file_size_mb:.1f}MB"

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            # Act: Measure migration time
            from data.migration import migrate_to_profiles
            from data.profile_manager import (
                PROFILES_DIR,
                DEFAULT_PROFILE_ID,
                DEFAULT_QUERY_ID,
            )

            start_time = time.time()
            migrate_to_profiles()
            elapsed_time = time.time() - start_time

            # Assert: Completed in under 5 seconds
            assert elapsed_time < 5.0, (
                f"Migration took {elapsed_time:.2f}s (target: <5s)"
            )

            # Verify file migrated successfully
            migrated_file = (
                PROFILES_DIR
                / DEFAULT_PROFILE_ID
                / "queries"
                / DEFAULT_QUERY_ID
                / "jira_cache.json"
            )
            assert migrated_file.exists()
            assert migrated_file.stat().st_size >= 45 * 1024 * 1024  # ~50MB
        finally:
            os.chdir(original_cwd)


@pytest.mark.integration
@pytest.mark.migration_tests
class TestMigrationEdgeCases:
    """Test migration edge cases and error handling."""

    def test_migration_skips_if_no_files_to_migrate(self, temp_profiles_dir, tmp_path):
        """Verify migration handles empty root directory gracefully."""
        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            from data.migration import migrate_to_profiles
            from data.profile_manager import PROFILES_FILE, DEFAULT_PROFILE_ID

            # Act: Run migration with no root files
            result = migrate_to_profiles()

            # Assert: Migration completes but does nothing
            assert result is True or result is None  # Depends on implementation

            # Profiles structure may still be created
            if PROFILES_FILE.exists():
                profiles_data = json.loads(PROFILES_FILE.read_text())
                assert profiles_data["active_profile_id"] == DEFAULT_PROFILE_ID
        finally:
            os.chdir(original_cwd)

    def test_migration_handles_partial_file_set(self, temp_profiles_dir, tmp_path):
        """Verify migration works with only some files present."""
        # Arrange: Create only jira_cache.json (no app_settings.json)
        jira_cache = tmp_path / "jira_cache.json"
        jira_cache.write_text('{"version": "2.0", "issues": []}')

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            from data.migration import migrate_to_profiles
            from data.profile_manager import (
                PROFILES_DIR,
                PROFILES_FILE,
                DEFAULT_PROFILE_ID,
                DEFAULT_QUERY_ID,
            )

            # Act: Run migration
            migrate_to_profiles()

            # Assert: jira_cache.json migrated
            migrated_file = (
                PROFILES_DIR
                / DEFAULT_PROFILE_ID
                / "queries"
                / DEFAULT_QUERY_ID
                / "jira_cache.json"
            )
            assert migrated_file.exists()

            # Assert: Other files don't cause errors
            assert PROFILES_FILE.exists()
        finally:
            os.chdir(original_cwd)

    def test_migration_preserves_jira_changelog_cache(
        self, temp_profiles_dir, tmp_path
    ):
        """Verify jira_changelog_cache.json is also migrated."""
        # Arrange: Create changelog cache
        changelog_cache = tmp_path / "jira_changelog_cache.json"
        changelog_cache.write_text('{"version": "1.0", "changelogs": []}')

        import os
        import sys

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        # Clear import cache
        if "data.migration" in sys.modules:
            del sys.modules["data.migration"]
        if "data.profile_manager" in sys.modules:
            del sys.modules["data.profile_manager"]

        try:
            from data.migration import migrate_to_profiles
            from data.profile_manager import (
                PROFILES_DIR,
                DEFAULT_PROFILE_ID,
                DEFAULT_QUERY_ID,
            )

            # Act: Run migration
            migrate_to_profiles()

            # Assert: Changelog cache migrated
            migrated_file = (
                PROFILES_DIR
                / DEFAULT_PROFILE_ID
                / "queries"
                / DEFAULT_QUERY_ID
                / "jira_changelog_cache.json"
            )
            assert migrated_file.exists()
        finally:
            os.chdir(original_cwd)
