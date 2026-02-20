"""
SQLite persistence backend implementation using mixin-based architecture.

This module implements PersistenceBackend interface for SQLite storage.
Provides normalized database operations with connection-per-request pattern.

Architecture:
- Uses context managers from data.database module
- Implements full PersistenceBackend interface via mixins
- Provides both normalized operations (get_issues, get_statistics)
  and legacy JSON blob methods (get_jira_cache, get_project_data) for migration

Performance:
- Connection pooling via get_db_connection()
- WAL mode for concurrent reads during writes
- Batch operations with ON CONFLICT DO UPDATE
- Indexed queries for <50ms response times

Concurrency:
- Automatic retry logic for database lock scenarios (up to 3 retries with exponential backoff)
- Graceful handling of OperationalError: database is locked
- WAL mode enables concurrent reads

Usage:
    from data.persistence.sqlite_backend import SQLiteBackend

    backend = SQLiteBackend("profiles/burndown.db")
    profile = backend.get_profile("kafka")
"""

import logging
from pathlib import Path

from data.persistence import PersistenceBackend
from data.persistence.sqlite.app_state import AppStateMixin
from data.persistence.sqlite.budget import BudgetMixin
from data.persistence.sqlite.changelog import ChangelogMixin
from data.persistence.sqlite.issues import IssuesMixin
from data.persistence.sqlite.metrics import MetricsMixin
from data.persistence.sqlite.profiles import ProfilesMixin
from data.persistence.sqlite.queries import QueriesMixin
from data.persistence.sqlite.statistics import StatisticsMixin
from data.persistence.sqlite.tasks import TasksMixin

logger = logging.getLogger(__name__)


class SQLiteBackend(
    ProfilesMixin,
    QueriesMixin,
    AppStateMixin,
    BudgetMixin,
    TasksMixin,
    IssuesMixin,
    ChangelogMixin,
    StatisticsMixin,
    MetricsMixin,
    PersistenceBackend,
):
    """
    SQLite implementation of persistence backend composed from mixins.

    Inherits from all domain-specific mixins to provide full persistence API.
    Each mixin encapsulates operations for a specific domain (profiles, issues, etc.).

    Attributes:
        db_path (str): Path to SQLite database file
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize SQLite backend.

        Args:
            db_path: Path to SQLite database file (e.g., "profiles/burndown.db")
        """
        self.db_path = Path(db_path)
        logger.info(
            f"SQLiteBackend initialized with database: {self.db_path.absolute()}"
        )

    def begin_transaction(self) -> None:
        """
        Begin a transaction (deprecated - use context managers instead).

        WARNING: This method is deprecated. Use get_db_connection() context managers
        for proper transaction management and connection cleanup.

        Context managers automatically:
        - Handle transactions (BEGIN/COMMIT/ROLLBACK)
        - Close connections
        - Ensure proper resource cleanup

        Example:
            from data.database import get_db_connection
            with get_db_connection(self.db_path) as conn:
                # Operations here are in a transaction
                cursor.execute("INSERT ...")
                conn.commit()
        """
        logger.warning(
            "begin_transaction() called but not needed - use context managers instead"
        )

    def commit_transaction(self) -> None:
        """
        Commit a transaction (deprecated - use context managers instead).

        WARNING: This method is deprecated. Use get_db_connection() context managers
        which automatically commit on successful exit.
        """
        logger.warning(
            "commit_transaction() called but not needed - use context managers instead"
        )

    def rollback_transaction(self) -> None:
        """
        Rollback a transaction (deprecated - use context managers instead).

        WARNING: This method is deprecated. Use get_db_connection() context managers
        which automatically rollback on exception.
        """
        logger.warning(
            "rollback_transaction() called but not needed - use context managers instead"
        )

    def close(self) -> None:
        """
        Close database connection (no-op in connection-per-request pattern).

        NOTE: This is a no-op because SQLiteBackend uses connection-per-request pattern.
        Each operation opens and closes its own connection via context managers.
        This prevents connection state issues and enables concurrent access via WAL mode.
        """
        logger.debug("close() called but no-op in connection-per-request pattern")
