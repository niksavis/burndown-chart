import os
import shutil
import sqlite3
import tempfile
from collections.abc import Callable, Iterator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import BinaryIO

WORKSPACE_MARKER = "burndown-synthetic-workspace-v1\n"
DATABASE_FILES = ("burndown.db", "burndown.db-wal", "burndown.db-shm")


def _claim_lock(stream: BinaryIO) -> None:
    if os.name == "nt":
        import msvcrt  # noqa: PLC0415 - Windows-only standard library

        stream.seek(0)
        stream.write(b"0")
        stream.flush()
        stream.seek(0)
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl  # noqa: PLC0415 - POSIX-only standard library

        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


@contextmanager
def exclusive_workspace(workspace: Path) -> Iterator[None]:
    workspace.mkdir(parents=True, exist_ok=True)
    _validate_workspace(workspace)
    if (workspace / ".demo.lock").is_symlink():
        raise ValueError("Refusing a symbolic-link workspace lock")
    with (workspace / ".demo.lock").open("a+b") as stream:
        try:
            _claim_lock(stream)
        except OSError as error:
            raise RuntimeError(
                "Demo workspace is in use; stop its server first"
            ) from error
        yield


def _has_database_tables(database: Path) -> bool:
    if database.is_symlink():
        raise ValueError("Refusing a symbolic-link demo database")
    if database.stat().st_size == 0:
        return False
    with closing(
        sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    ) as connection:
        return (
            connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = ? LIMIT 1", ("table",)
            ).fetchone()
            is not None
        )


def _validate_workspace(workspace: Path) -> bool:
    marker = workspace / ".demo-workspace"
    if marker.is_symlink():
        raise ValueError("Refusing a symbolic-link workspace marker")
    if marker.exists():
        if marker.read_text(encoding="utf-8") != WORKSPACE_MARKER:
            raise ValueError("Unrecognized demo workspace marker; refusing changes")
        return True
    unexpected = {entry.name for entry in workspace.iterdir()} - {
        ".demo.lock",
        "burndown.db",
    }
    database = workspace / "burndown.db"
    if unexpected or (database.exists() and _has_database_tables(database)):
        raise ValueError(
            "Refusing an unmarked populated workspace; choose a new directory"
        )
    return False


def claim_demo_workspace(workspace: Path) -> None:
    if not _validate_workspace(workspace):
        (workspace / ".demo-workspace").write_text(WORKSPACE_MARKER, encoding="utf-8")


def publish_demo_database(workspace: Path, build: Callable[[Path], None]) -> bool:
    claim_demo_workspace(workspace)
    database = workspace / "burndown.db"
    if database.exists() and _has_database_tables(database):
        with closing(
            sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
        ) as connection:
            marker = connection.execute(
                "SELECT value FROM app_state WHERE key = ?", ("demo_seed_version",)
            ).fetchone()
        if marker is None:
            raise ValueError(
                "Demo database has no completed seed marker; use guarded reset"
            )
        return False
    with tempfile.TemporaryDirectory(prefix=".demo-build-", dir=workspace) as directory:
        candidate = Path(directory)
        build(candidate)
        candidate_database = candidate / "burndown.db"
        with closing(sqlite3.connect(candidate_database)) as connection:
            marker = connection.execute(
                "SELECT value FROM app_state WHERE key = ?", ("demo_seed_version",)
            ).fetchone()
            if marker is None:
                raise ValueError("Seed did not complete; database was not published")
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise ValueError("Seed database failed integrity verification")
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        candidate_database.replace(database)
    return True


def reset_demo_workspace(workspace: Path) -> None:
    marker = workspace / ".demo-workspace"
    if not marker.is_file() or marker.read_text(encoding="utf-8") != WORKSPACE_MARKER:
        raise ValueError("Reset requires a marked demo workspace; refusing changes")
    cache = workspace / "cache"
    if cache.is_symlink():
        raise ValueError("Refusing to reset a symbolic-link cache")
    for filename in DATABASE_FILES:
        (workspace / filename).unlink(missing_ok=True)
    if cache.exists():
        shutil.rmtree(cache)
