import logging
from pathlib import Path

from data.database import check_database_integrity, database_exists, get_db_connection
from data.migration.schema import (
    create_schema,
    drop_jira_cache_table,
    ensure_budget_velocity_columns,
    get_schema_version,
    set_schema_version,
)

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.0"
DEFAULT_DB_PATH = Path("profiles/burndown.db")


def initialize_schema(db_path: Path = DEFAULT_DB_PATH, force: bool = False) -> bool:

    logger.info(f"Initializing database schema at {db_path}")

    try:
        with get_db_connection(db_path) as conn:
            existing_version = get_schema_version(conn)

            if existing_version == "0.0":
                logger.info("No existing schema found, creating new schema")
                create_schema(conn)
                set_schema_version(conn, CURRENT_SCHEMA_VERSION)
                logger.info(f"Schema {CURRENT_SCHEMA_VERSION} created successfully")
                return True

            elif existing_version == CURRENT_SCHEMA_VERSION:
                if force:
                    logger.warning(
                        "FORCE flag set - recreating schema (DATA WILL BE LOST)"
                    )
                    create_schema(conn)
                    set_schema_version(conn, CURRENT_SCHEMA_VERSION)
                    return True
                else:
                    logger.info(
                        f"Schema {CURRENT_SCHEMA_VERSION} already exists and is current"
                    )
                    return True

            else:
                logger.warning(
                    "Schema version mismatch: "
                    f"existing={existing_version}, "
                    f"current={CURRENT_SCHEMA_VERSION}"
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

    logger.info(f"Verifying database schema at {db_path}")

    try:
        if not database_exists(db_path):
            logger.error("Database file does not exist")
            return False

        with get_db_connection(db_path) as conn:
            version = get_schema_version(conn)
            if version == "0.0":
                logger.error("Schema version not set - database not initialized")
                return False

            logger.info(f"Schema version: {version}")

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

    return CURRENT_SCHEMA_VERSION
