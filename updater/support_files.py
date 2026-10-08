from __future__ import annotations

import shutil
import time
from collections.abc import Callable
from pathlib import Path

StatusFn = Callable[[str], None]

SUPPORT_FILE_NAMES = [
    "LICENSE.txt",
    "README.txt",
    "THIRD_PARTY_LICENSES.txt",
]


def find_file_in_extract(extract_dir: Path, filename: str) -> Path | None:

    target = filename.lower()
    direct_path = extract_dir / filename
    if direct_path.exists():
        return direct_path
    for path in extract_dir.rglob("*"):
        if path.is_file() and path.name.lower() == target:
            return path
    return None


def replace_support_file(
    source_path: Path,
    target_path: Path,
    description: str,
    status: StatusFn,
) -> bool:

    max_retries = 10
    retry_delay = 0.5

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 3.0)

            if target_path.exists():
                target_path.unlink()

            shutil.copy2(source_path, target_path)
            status(f"Updated {description}: {target_path.name}")
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                status(f"WARNING: Failed to update {description} due to file lock")
                return False
        except Exception as e:
            status(f"WARNING: Failed to update {description}: {e}")
            return False

    return False


def replace_support_files(
    extract_dir: Path,
    install_dir: Path,
    status: StatusFn,
) -> None:
    status("Updating README and license files")
    for filename in SUPPORT_FILE_NAMES:
        source_path = find_file_in_extract(extract_dir, filename)
        if not source_path:
            status(f"WARNING: {filename} not found in update package")
            continue
        target_path = install_dir / filename
        replace_support_file(source_path, target_path, filename, status)
