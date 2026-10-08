import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from utils.license_extractor import extract_license_on_first_run


class TestLicenseExtractor:
    def test_extract_license_not_frozen(self, caplog):
        with (
            patch.object(sys, "frozen", False, create=True),
            caplog.at_level("DEBUG"),
        ):
            extract_license_on_first_run()

        assert "Not running as frozen executable" in caplog.text

    def test_extract_license_already_exists(self, caplog):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            license_file = temp_path / "LICENSE.txt"
            license_file.write_text("Existing license")

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(temp_path), create=True),
                patch.object(sys, "executable", str(temp_path / "app.exe")),
                caplog.at_level("DEBUG"),
            ):
                extract_license_on_first_run()

            assert "LICENSE.txt already exists" in caplog.text

    def test_extract_license_success(self, caplog):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exe_dir = temp_path / "exe"
            bundle_dir = temp_path / "bundle"
            exe_dir.mkdir()
            bundle_dir.mkdir()

            source_license = bundle_dir / "LICENSE"
            license_text = "MIT License\n\nCopyright (c) 2025 Test"
            source_license.write_text(license_text, encoding="utf-8")

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle_dir), create=True),
                caplog.at_level("INFO"),
                patch.object(sys, "executable", str(exe_dir / "app.exe")),
            ):
                extract_license_on_first_run()

            extracted_license = exe_dir / "LICENSE.txt"
            assert extracted_license.exists()
            assert extracted_license.read_text(encoding="utf-8") == license_text
            assert "LICENSE.txt extracted" in caplog.text

    def test_extract_license_source_not_found(self, caplog):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exe_dir = temp_path / "exe"
            bundle_dir = temp_path / "bundle"
            exe_dir.mkdir()
            bundle_dir.mkdir()

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle_dir), create=True),
                patch.object(sys, "executable", str(exe_dir / "app.exe")),
            ):
                extract_license_on_first_run()

            assert "LICENSE file not found in bundle" in caplog.text
            assert not (exe_dir / "LICENSE.txt").exists()

    def test_extract_license_write_error(self, caplog):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exe_dir = temp_path / "exe"
            bundle_dir = temp_path / "bundle"
            exe_dir.mkdir()
            bundle_dir.mkdir()

            source_license = bundle_dir / "LICENSE"
            source_license.write_text("Test license")

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "_MEIPASS", str(bundle_dir), create=True),
                patch.object(sys, "executable", str(exe_dir / "app.exe")),
                patch("pathlib.Path.write_text", side_effect=OSError("Write failed")),
            ):
                extract_license_on_first_run()

            assert "Failed to extract LICENSE.txt" in caplog.text
