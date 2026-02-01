"""
SQLite persistence backend implementation (DEPRECATED - imports from new location).

This module is deprecated and exists only for backwards compatibility.
The implementation has been refactored into a mixin-based architecture.

Import SQLiteBackend from this module as before - it now delegates to the new implementation:
    from data.persistence.sqlite_backend import SQLiteBackend

New mixin-based structure (for reference):
    data/persistence/sqlite/
    ├── backend.py          # SQLiteBackend composition class
    ├── profiles.py         # ProfilesMixin
    ├── queries.py          # QueriesMixin
    ├── issues.py           # IssuesMixin
    ├── changelog.py        # ChangelogMixin
    ├── statistics.py       # StatisticsMixin
    ├── metrics.py          # MetricsMixin
    ├── app_state.py        # AppStateMixin
    ├── budget.py           # BudgetMixin
    ├── tasks.py            # TasksMixin
    └── helpers.py          # Utility functions

All imports from 'data.persistence.sqlite_backend' continue to work.
"""

from data.persistence.sqlite.backend import SQLiteBackend

__all__ = ["SQLiteBackend"]
