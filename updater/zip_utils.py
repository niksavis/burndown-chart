"""ZIP extraction and integrity verification helpers for the updater."""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path
from typing import Callable, Optional

StatusFn = Callable[[str], None]

CHECKSUM_FILE_NAME = "BURNDOWN_CHECKSUMS.txt"


def extract_update(zip_path: Path, extract_dir: Path, status: StatusFn) -> bool:
    """Extract update ZIP to directory with path traversal protection.

    Args:
        zip_path: Path to ZIP file
        extract_dir: Directory where to extract files
        status: Callback for status output

    Returns:
        True if extraction succeeded, False otherwise
    """
    try:
        status(f"Extracting update from {zip_path.name}")

        if extract_dir.exists():
            status(
                f"WARNING: Extraction directory already exists (UUID collision?): {extract_dir}"
            )
            try:
                shutil.rmtree(extract_dir)
                status("Removed existing directory")
            except Exception as e:
                status(f"ERROR: Failed to remove existing directory: {e}")
                return False

        try:
            extract_dir.mkdir(parents=True, exist_ok=True)
            status(f"Created extraction directory: {extract_dir}")
        except PermissionError as e:
            status(f"ERROR: Permission denied creating directory: {extract_dir}")
            status(f"Details: {e}")
            return False
        except Exception as e:
            status(f"ERROR: Could not create temporary directory: {extract_dir}")
            status(f"Details: {e}")
            return False

        extract_root = extract_dir.resolve()

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for info in zip_ref.infolist():
                member_path = extract_dir / info.filename
                resolved_path = member_path.resolve()
                if not resolved_path.is_relative_to(extract_root):
                    status(f"ERROR: Unsafe path in update package: {info.filename}")
                    return False

                if info.is_dir():
                    resolved_path.mkdir(parents=True, exist_ok=True)
                    continue

                resolved_path.parent.mkdir(parents=True, exist_ok=True)
                with zip_ref.open(info) as source, resolved_path.open("wb") as target:
                    shutil.copyfileobj(source, target)

        extracted_files = list(extract_dir.rglob("*"))
        status(f"Extracted {len(extracted_files)} files")
        return True
    except zipfile.BadZipFile as e:
        status(f"ERROR: Invalid ZIP file: {e}")
        return False
    except Exception as e:
        status(f"ERROR: Failed to extract update: {e}")
        return False


def find_executable_in_extract(
    extract_dir: Path,
    names: list[str],
) -> Optional[Path]:
    """Find a matching executable in an extracted update directory.

    Args:
        extract_dir: Directory containing extracted update files.
        names: Candidate executable names to search for.

    Returns:
        Path to the first matching executable, or None if not found.
    """
    for name in names:
        direct_path = extract_dir / name
        if direct_path.exists():
            return direct_path
        matches = list(extract_dir.glob(f"**/{name}"))
        if matches:
            return matches[0]
    return None


def verify_checksums(
    extract_dir: Path,
    expected_files: list[str],
    status: StatusFn,
) -> bool:
    """Verify SHA256 checksums for required files in the update package.

    Args:
        extract_dir: Directory containing extracted update files.
        expected_files: Filenames that must be present in checksum file.
        status: Callback for status output

    Returns:
        True if checksums are valid, False otherwise
    """
    checksum_path = extract_dir / CHECKSUM_FILE_NAME
    if not checksum_path.exists():
        status(f"ERROR: Missing checksum file: {CHECKSUM_FILE_NAME}")
        return False

    checksum_map: dict[str, str] = {}
    try:
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.split(None, 1)
            if len(parts) != 2:
                continue
            digest, filename = parts
            filename = filename.strip()
            if not filename:
                continue
            path = Path(filename)
            if path.is_absolute() or ".." in path.parts:
                continue
            checksum_map[filename.lower()] = digest.lower()
    except Exception as e:
        status(f"ERROR: Failed to read checksum file: {e}")
        return False

    for filename in expected_files:
        digest = checksum_map.get(filename.lower())
        if not digest:
            status(f"ERROR: Missing checksum entry for {filename}")
            return False
        file_path = extract_dir / filename
        if not file_path.exists():
            status(f"ERROR: Expected file missing from update: {filename}")
            return False
        if not _verify_file_hash(file_path, digest):
            status(f"ERROR: Checksum mismatch for {filename}")
            return False

    status("Checksum verification successful")
    return True


def _verify_file_hash(file_path: Path, expected_digest: str) -> bool:
    hasher = hashlib.sha256()
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest().lower() == expected_digest.lower()
