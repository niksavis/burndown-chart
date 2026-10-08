import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from data.installation_context import InstallationContext, get_installation_context


class TestInstallationContextDetection:
    def test_detect_source_mode(self):
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
            if original_has_meipass and original_meipass is not None:
                sys._MEIPASS = original_meipass  # type: ignore[attr-defined]
        """Test detection when running as PyInstaller executable."""
        fake_exe_path = Path("C:/Program Files/Burndown/Burndown.exe")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(sys, "executable", str(fake_exe_path)):
                    with patch.object(Path, "mkdir"):
                        context = InstallationContext.detect()

                        assert context.is_frozen is True
                        assert context.executable_dir == fake_exe_path.parent


class TestInstallationContextPaths:
    def test_source_mode_paths(self):
        original_has_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            with patch.object(sys, "frozen", False, create=True):
                context = InstallationContext.detect()

                assert "profiles" in str(context.database_path)
                assert "burndown.db" in str(context.database_path)
                assert "logs" in str(context.logs_path)

                assert context.is_portable is True
        finally:
            if original_has_meipass and original_meipass is not None:
                sys._MEIPASS = original_meipass  # type: ignore[attr-defined]
        """Test that frozen mode uses executable directory paths."""
        fake_exe_dir = Path("C:/Program Files/Burndown")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(
                    sys, "executable", str(fake_exe_dir / "Burndown.exe")
                ):
                    with patch.object(Path, "mkdir"):
                        context = InstallationContext.detect()

                        assert (
                            context.database_path
                            == fake_exe_dir / "profiles" / "burndown.db"
                        )
                        assert context.logs_path == fake_exe_dir / "logs"

    def test_database_path_structure(self):
        context = InstallationContext.detect()

        assert context.database_path.name == "burndown.db"
        assert context.database_path.parent.name == "profiles"

    def test_logs_path_structure(self):
        context = InstallationContext.detect()

        assert context.logs_path.name == "logs"


class TestInstallationContextRepresentation:
    def test_repr_contains_key_info(self):
        context = InstallationContext.detect()
        repr_str = repr(context)

        assert "InstallationContext" in repr_str
        assert "frozen=" in repr_str
        assert "portable=" in repr_str
        assert "exe_dir=" in repr_str
        assert "db=" in repr_str

    def test_repr_frozen_status(self):
        context = InstallationContext.detect()
        repr_str = repr(context)

        if context.is_frozen:
            assert "frozen=True" in repr_str
        else:
            assert "frozen=False" in repr_str


class TestInstallationContextSingleton:
    def test_get_installation_context_returns_instance(self):
        context = get_installation_context()

        assert isinstance(context, InstallationContext)
        assert context.executable_dir is not None
        assert context.database_path is not None
        assert context.logs_path is not None

    def test_get_installation_context_singleton(self):
        context1 = get_installation_context()
        context2 = get_installation_context()

        assert context1 is context2

    def test_singleton_initialized_on_first_call(self):
        import data.installation_context as ctx_module

        ctx_module._context = None

        _ = get_installation_context()
        assert _ is not None

        assert ctx_module._context is _


class TestInstallationContextDirectoryCreation:
    def test_directories_created_on_detect(self):
        with patch.object(Path, "mkdir") as mock_mkdir:
            _ = InstallationContext.detect()

            assert mock_mkdir.called

            calls = mock_mkdir.call_args_list
            for call in calls:
                assert call.kwargs.get("parents") is True
                assert call.kwargs.get("exist_ok") is True


class TestInstallationContextPortableMode:
    def test_source_mode_is_always_portable(self):
        original_has_meipass = hasattr(sys, "_MEIPASS")
        original_meipass = getattr(sys, "_MEIPASS", None)

        try:
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            with patch.object(sys, "frozen", False, create=True):
                context = InstallationContext.detect()

                assert context.is_portable is True
        finally:
            if original_has_meipass and original_meipass is not None:
                sys._MEIPASS = original_meipass  # type: ignore[attr-defined]
        """Test portable mode detection in frozen mode."""
        fake_exe_dir = Path("C:/Users/Test/Burndown")

        with patch.object(sys, "frozen", True, create=True):
            with patch.object(sys, "_MEIPASS", "/tmp/_MEI123", create=True):
                with patch.object(
                    sys, "executable", str(fake_exe_dir / "Burndown.exe")
                ):
                    with patch.object(Path, "mkdir"):
                        context = InstallationContext.detect()

                        assert isinstance(context.is_portable, bool)


class TestInstallationContextEdgeCases:
    def test_frozen_without_meipass(self):
        with patch.object(sys, "frozen", True, create=True):
            if hasattr(sys, "_MEIPASS"):
                delattr(sys, "_MEIPASS")

            context = InstallationContext.detect()

            assert context.is_frozen is False

    def test_paths_are_path_objects(self):
        context = InstallationContext.detect()

        assert isinstance(context.executable_dir, Path)
        assert isinstance(context.database_path, Path)
        assert isinstance(context.logs_path, Path)

    def test_paths_are_absolute(self):
        context = InstallationContext.detect()

        assert context.executable_dir.is_absolute()
        assert context.database_path.is_absolute()
        assert context.logs_path.is_absolute()


class TestInstallationContextConsistency:
    def test_database_under_executable_dir(self):
        context = InstallationContext.detect()

        try:
            context.database_path.relative_to(context.executable_dir)
        except ValueError:
            pytest.fail("Database path is not under executable directory")

    def test_logs_under_executable_dir(self):
        context = InstallationContext.detect()

        try:
            context.logs_path.relative_to(context.executable_dir)
        except ValueError:
            pytest.fail("Logs path is not under executable directory")

    def test_database_and_logs_separate(self):
        context = InstallationContext.detect()

        assert context.database_path.parent != context.logs_path
