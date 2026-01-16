"""
Unit tests for installation_context module.

Tests path resolution for frozen vs source modes.
"""

import sys
from pathlib import Path
from unittest.mock import patch
import pytest

from data.installation_context import InstallationContext, get_installation_context


class TestInstallationContextDetection:
    """Test installation context detection logic."""

    def test_detect_source_mode(self):
        """Test detection when running from source (not frozen)."""
        # Ensure _MEIPASS doesn't exist in source mode
        original_has_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            with patch.object(sys, "frozen", False, create=True):
                context = InstallationContext.detect()

                assert context.is_frozen is False
                assert context.executable_dir.exists()
                assert context.executable_dir.name == "burndown-chart"
                assert context.is_portable is True
        finally:
            # Restore original state
            if original_has_meipass and original_meipass is not None:
                setattr(sys, "_MEIPASS", original_meipass)
        """Test detection when running as PyInstaller executable."""
        fake_exe_path = Path("C:/Program Files/BurndownChart/BurndownChart.exe")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(sys, "executable", str(fake_exe_path)):
                    with patch.object(
                        Path, "mkdir"
                    ):  # Prevent actual directory creation
                        context = InstallationContext.detect()

                        assert context.is_frozen is True
                        assert context.executable_dir == fake_exe_path.parent


class TestInstallationContextPaths:
    """Test path resolution for different scenarios."""

    def test_source_mode_paths(self):
        """Test that source mode uses project root paths."""
        # Ensure _MEIPASS doesn't exist in source mode
        original_has_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            with patch.object(sys, "frozen", False, create=True):
                context = InstallationContext.detect()

                # Paths should be relative to project root
                assert "profiles" in str(context.database_path)
                assert "burndown.db" in str(context.database_path)
                assert "logs" in str(context.logs_path)

                # Source mode is always portable
                assert context.is_portable is True
        finally:
            # Restore original state
            if original_has_meipass and original_meipass is not None:
                setattr(sys, "_MEIPASS", original_meipass)
        """Test that frozen mode uses executable directory paths."""
        fake_exe_dir = Path("C:/Program Files/BurndownChart")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(
                    sys, "executable", str(fake_exe_dir / "BurndownChart.exe")
                ):
                    with patch.object(Path, "mkdir"):
                        context = InstallationContext.detect()

                        # Paths should be relative to executable directory
                        assert (
                            context.database_path
                            == fake_exe_dir / "profiles" / "burndown.db"
                        )
                        assert context.logs_path == fake_exe_dir / "logs"

    def test_database_path_structure(self):
        """Test database path follows expected structure."""
        context = InstallationContext.detect()

        # Database should always be in profiles/burndown.db
        assert context.database_path.name == "burndown.db"
        assert context.database_path.parent.name == "profiles"

    def test_logs_path_structure(self):
        """Test logs path follows expected structure."""
        context = InstallationContext.detect()

        # Logs should be in logs/ directory
        assert context.logs_path.name == "logs"


class TestInstallationContextRepresentation:
    """Test string representation and debugging output."""

    def test_repr_contains_key_info(self):
        """Test __repr__ includes essential debugging info."""
        context = InstallationContext.detect()
        repr_str = repr(context)

        # Should contain key fields
        assert "InstallationContext" in repr_str
        assert "frozen=" in repr_str
        assert "portable=" in repr_str
        assert "exe_dir=" in repr_str
        assert "db=" in repr_str

    def test_repr_frozen_status(self):
        """Test __repr__ shows correct frozen status."""
        context = InstallationContext.detect()
        repr_str = repr(context)

        # Should show frozen status
        if context.is_frozen:
            assert "frozen=True" in repr_str
        else:
            assert "frozen=False" in repr_str


class TestInstallationContextSingleton:
    """Test singleton pattern for global context instance."""

    def test_get_installation_context_returns_instance(self):
        """Test get_installation_context returns valid instance."""
        context = get_installation_context()

        assert isinstance(context, InstallationContext)
        assert context.executable_dir is not None
        assert context.database_path is not None
        assert context.logs_path is not None

    def test_get_installation_context_singleton(self):
        """Test get_installation_context returns same instance."""
        context1 = get_installation_context()
        context2 = get_installation_context()

        # Should return the exact same object
        assert context1 is context2

    def test_singleton_initialized_on_first_call(self):
        """Test singleton is initialized on first call."""
        # Reset global state
        import data.installation_context as ctx_module

        ctx_module._context = None

        # First call should initialize
        _ = get_installation_context()
        assert _ is not None

        # Global should be set
        assert ctx_module._context is _


class TestInstallationContextDirectoryCreation:
    """Test directory creation behavior."""

    def test_directories_created_on_detect(self):
        """Test that necessary directories are created during detection."""
        with patch.object(Path, "mkdir") as mock_mkdir:
            _ = InstallationContext.detect()

            # Should have called mkdir for database parent and logs
            assert mock_mkdir.called

            # Verify mkdir was called with proper arguments
            calls = mock_mkdir.call_args_list
            for call in calls:
                # Should use parents=True and exist_ok=True
                assert call.kwargs.get("parents") is True
                assert call.kwargs.get("exist_ok") is True


class TestInstallationContextPortableMode:
    """Test portable mode detection."""

    def test_source_mode_is_always_portable(self):
        """Test that source mode is always considered portable."""
        # Ensure _MEIPASS doesn't exist in source mode
        original_has_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            with patch.object(sys, "frozen", False, create=True):
                context = InstallationContext.detect()

                assert context.is_portable is True
        finally:
            # Restore original state
            if original_has_meipass and original_meipass is not None:
                setattr(sys, "_MEIPASS", original_meipass)
        """Test portable mode detection in frozen mode."""
        fake_exe_dir = Path("C:/Users/Test/BurndownChart")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(
                    sys, "executable", str(fake_exe_dir / "BurndownChart.exe")
                ):
                    with patch.object(Path, "mkdir"):
                        context = InstallationContext.detect()

                        # Portable status depends on whether profiles dir exists
                        # In test environment, it will be True due to exist check
                        assert isinstance(context.is_portable, bool)


class TestInstallationContextEdgeCases:
    """Test edge cases and error handling."""

    def test_frozen_without_meipass(self):
        """Test handling when frozen is True but _MEIPASS is missing."""
        with patch.object(sys, "frozen", True, create=True):
            # Don't set _MEIPASS
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            context = InstallationContext.detect()

            # Should detect as not frozen
            assert context.is_frozen is False

    def test_paths_are_path_objects(self):
        """Test that all paths are pathlib.Path objects."""
        context = InstallationContext.detect()

        assert isinstance(context.executable_dir, Path)
        assert isinstance(context.database_path, Path)
        assert isinstance(context.logs_path, Path)

    def test_paths_are_absolute(self):
        """Test that all paths are absolute."""
        context = InstallationContext.detect()

        assert context.executable_dir.is_absolute()
        assert context.database_path.is_absolute()
        assert context.logs_path.is_absolute()


class TestInstallationContextConsistency:
    """Test consistency of context attributes."""

    def test_database_under_executable_dir(self):
        """Test that database path is under executable directory."""
        context = InstallationContext.detect()

        # Database should be a subdirectory of executable_dir
        try:
            context.database_path.relative_to(context.executable_dir)
        except ValueError:
            pytest.fail("Database path is not under executable directory")

    def test_logs_under_executable_dir(self):
        """Test that logs path is under executable directory."""
        context = InstallationContext.detect()

        # Logs should be a subdirectory of executable_dir
        try:
            context.logs_path.relative_to(context.executable_dir)
        except ValueError:
            pytest.fail("Logs path is not under executable directory")

    def test_database_and_logs_separate(self):
        """Test that database and logs are in separate directories."""
        context = InstallationContext.detect()

        # Database is in profiles/, logs in logs/ - they should be different
        assert context.database_path.parent != context.logs_path
