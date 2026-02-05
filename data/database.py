"""
Database connection management for SQLite persistence.

This module provides connection management, integrity checks, and
database initialization utilities for the Burndown application.

Architecture:
- Connection-per-request pattern (no global connections)
- WAL mode for concurrent access
- Context manager for automatic cleanup
- Integrity validation on startup

Usage:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles")
        results = cursor.fetchall()
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from data.installation_context import get_installation_context

logger = logging.getLogger(__name__)

# Database file location - uses InstallationContext to determine correct path
_installation_context = get_installation_context()
DB_PATH = _installation_context.database_path


@contextmanager
def get_db_connection(
    db_path: Path = DB_PATH,
) -> Generator[sqlite3.Connection, None, None]:
    """
    Get SQLite database connection with WAL mode and automatic cleanup.

    Connection-per-request pattern ensures no stale connections.
    WAL mode enables concurrent reads during writes.

    Args:
        db_path: Path to database file (default: from InstallationContext)

    Yields:
        sqlite3.Connection: Database connection with row factory

    Raises:
        sqlite3.OperationalError: If database is locked or inaccessible

    Example:
        >>> with get_db_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT COUNT(*) FROM profiles")
        ...     count = cursor.fetchone()[0]
    """
    conn = None
    try:
        # Ensure profiles directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Connect with 10 second timeout
        conn = sqlite3.connect(str(db_path), timeout=10.0)

        # Enable WAL mode for concurrent access (US4)
        conn.execute("PRAGMA journal_mode=WAL")

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys=ON")

        # Use Row factory for dict-like access
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
    """
    Check database integrity using SQLite PRAGMA integrity_check.

    Args:
        db_path: Path to database file

    Returns:
        bool: True if database is valid, False if corrupted

    Example:
        >>> if not check_database_integrity():
        ...     logger.error("Database corrupted, recreating...")
        ...     initialize_database()
    """
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

    except Exception as e:
        logger.error(f"Integrity check failed: {e}")
        return False


def get_database_size(db_path: Path = DB_PATH) -> int:
    """
    Get database file size in bytes.

    Used for monitoring and validating SC-007 (proportional growth).

    Args:
        db_path: Path to database file

    Returns:
        int: File size in bytes, or 0 if file doesn't exist

    Example:
        >>> size_mb = get_database_size() / (1024 * 1024)
        >>> print(f"Database size: {size_mb:.2f} MB")
    """
    if db_path.exists():
        size = db_path.stat().st_size
        logger.debug(f"Database size: {size} bytes ({size / 1024:.1f} KB)")
        return size
    return 0


def database_exists(db_path: Path = DB_PATH) -> bool:
    """
    Check if database file exists.

    Args:
        db_path: Path to database file

    Returns:
        bool: True if database file exists
    """
    exists = db_path.exists()
    logger.debug(f"Database exists check: {exists} ({db_path})")
    return exists
