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
    def __init__(self, db_path: str) -> None:

        self.db_path = Path(db_path)
        logger.info(
            f"SQLiteBackend initialized with database: {self.db_path.absolute()}"
        )

    def begin_transaction(self) -> None:

        logger.warning(
            "begin_transaction() called but not needed - use context managers instead"
        )

    def commit_transaction(self) -> None:

        logger.warning(
            "commit_transaction() called but not needed - use context managers instead"
        )

    def rollback_transaction(self) -> None:

        logger.warning(
            "rollback_transaction() called but not needed - "
            "use context managers instead"
        )

    def close(self) -> None:

        logger.debug("close() called but no-op in connection-per-request pattern")
