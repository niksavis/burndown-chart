import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from data.installation_context import get_installation_context

logger = logging.getLogger(__name__)

_installation_context = get_installation_context()
DB_PATH = _installation_context.database_path


@contextmanager
def get_db_connection(
    db_path: Path = DB_PATH,
) -> Generator[sqlite3.Connection]:

    conn = None
    try:
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(db_path), timeout=10.0)

        conn.execute("PRAGMA journal_mode=WAL")

        conn.execute("PRAGMA foreign_keys=ON")

        conn.row_factory = sqlite3.Row

        logger.debug(f"Database connection opened: {db_path}")

        yield conn

    except sqlite3.OperationalError as e:
        logger.error(
            f"Database connection failed: {e}",
            extra={"db_path": str(db_path), "error_type": type(e).__name__},
        )
        raise

    finally:
        if conn:
            conn.close()
            logger.debug(f"Database connection closed: {db_path}")


def check_database_integrity(db_path: Path = DB_PATH) -> bool:

    try:
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            if result and result[0] == "ok":
                logger.info("Database integrity check: PASS")
                return True
            else:
                logger.error(
                    "Database integrity check: FAIL",
                    extra={"result": result[0] if result else "no result"},
                )
                return False

    except (sqlite3.Error, OSError, ValueError, TypeError) as e:
        logger.error(f"Integrity check failed: {e}")
        return False


def get_database_size(db_path: Path = DB_PATH) -> int:

    if db_path.exists():
        size = db_path.stat().st_size
        logger.debug(f"Database size: {size} bytes ({size / 1024:.1f} KB)")
        return size
    return 0


def database_exists(db_path: Path = DB_PATH) -> bool:

    exists = db_path.exists()
    logger.debug(f"Database exists check: {exists} ({db_path})")
    return exists
