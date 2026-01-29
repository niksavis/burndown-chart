"""
Schema initialization and management.

Provides high-level functions to create and verify database schema.
Used by migration orchestrator and app startup.

Usage:
    from data.migration.schema_manager import initialize_schema, verify_schema

    # Initialize database with schema
    initialize_schema()

    # Verify schema integrity
    if verify_schema():
        print("Schema valid")
"""

import logging
from pathlib import Path

from data.database import get_db_connection, check_database_integrity, database_exists
from data.migration.schema import (
    create_schema,
    get_schema_version,
    set_schema_version,
    ensure_budget_velocity_columns,
    drop_jira_cache_table,
)

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.0"
DEFAULT_DB_PATH = Path("profiles/burndown.db")


def initialize_schema(db_path: Path = DEFAULT_DB_PATH, force: bool = False) -> bool:
    """
    Initialize database schema (idempotent).

    Creates all 10 normalized tables, indexes, and sets schema version.
    Safe to call multiple times - uses CREATE TABLE IF NOT EXISTS.

    Args:
        db_path: Path to database file
        force: If True, recreate schema even if exists (WARNING: destroys data)

    Returns:
        bool: True if schema created/verified successfully

    Raises:
        sqlite3.Error: If schema creation fails

    Example:
        >>> from data.migration.schema_manager import initialize_schema
        >>> initialize_schema()  # Creates schema if not exists
        True
    """
    logger.info(f"Initializing database schema at {db_path}")

    try:
        with get_db_connection(db_path) as conn:
            # Check if schema already exists
            existing_version = get_schema_version(conn)

            if existing_version == "0.0":
                # Schema doesn't exist - create it
                logger.info("No existing schema found, creating new schema")
                create_schema(conn)
                set_schema_version(conn, CURRENT_SCHEMA_VERSION)
                logger.info(f"Schema {CURRENT_SCHEMA_VERSION} created successfully")
                return True

            elif existing_version == CURRENT_SCHEMA_VERSION:
                # Schema exists and matches current version
                if force:
                    logger.warning(
                        "FORCE flag set - recreating schema (DATA WILL BE LOST)"
                    )
                    # TODO: Add DROP TABLE statements if force=True needed
                    create_schema(conn)
                    set_schema_version(conn, CURRENT_SCHEMA_VERSION)
                    return True
                else:
                    logger.info(
                        f"Schema {CURRENT_SCHEMA_VERSION} already exists and is current"
                    )
                    return True

            else:
                # Schema exists but version mismatch - run migrations
                logger.warning(
                    f"Schema version mismatch: existing={existing_version}, current={CURRENT_SCHEMA_VERSION}"
                )
                logger.info("Running schema migrations")
                ensure_budget_velocity_columns(conn)
                drop_jira_cache_table(conn)
                set_schema_version(conn, CURRENT_SCHEMA_VERSION)
                logger.info("Schema migrations completed")
                return True

    except Exception as e:
        logger.error(
            f"Failed to initialize schema: {e}", extra={"error_type": type(e).__name__}
        )
        raise


def verify_schema(db_path: Path = DEFAULT_DB_PATH) -> bool:
    """
    Verify database schema integrity.

    Checks:
    1. Database file exists
    2. Schema version is set
    3. Database integrity (PRAGMA integrity_check)

    Args:
        db_path: Path to database file

    Returns:
        bool: True if schema valid, False otherwise

    Example:
        >>> from data.migration.schema_manager import verify_schema
        >>> if not verify_schema():
        ...     print("Schema corruption detected")
    """
    logger.info(f"Verifying database schema at {db_path}")

    try:
        # Check 1: Database file exists
        if not database_exists(db_path):
            logger.error("Database file does not exist")
            return False

        with get_db_connection(db_path) as conn:
            # Check 2: Schema version is set
            version = get_schema_version(conn)
            if version == "0.0":
                logger.error("Schema version not set - database not initialized")
                return False

            logger.info(f"Schema version: {version}")

        # Check 3: Database integrity (needs db_path, not connection)
        if not check_database_integrity(db_path):
            logger.error("Database integrity check FAILED")
            return False

        logger.info("Schema verification passed")
        return True

    except Exception as e:
        logger.error(
            f"Schema verification failed: {e}", extra={"error_type": type(e).__name__}
        )
        return False


def get_current_schema_version() -> str:
    """
    Get expected current schema version.

    Returns:
        str: Current schema version constant

    Example:
        >>> from data.migration.schema_manager import get_current_schema_version
        >>> print(f"Expected schema version: {get_current_schema_version()}")
    """
    return CURRENT_SCHEMA_VERSION
