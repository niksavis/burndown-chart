"""JIRA issues and cache operations mixin for SQLiteBackend (REFACTORED).

This module is refactored and split for maintainability.
Import IssuesMixin from this module as before - it now delegates to focused mixins:
    from data.persistence.sqlite.issues import IssuesMixin

New focused structure:
    data/persistence/sqlite/
    ├── issues_crud.py      # IssuesCRUDMixin - get/save/delete/renormalize
    ├── issues_cache.py     # IssuesCacheMixin - cache operations & changelog extraction

All imports from 'data.persistence.sqlite.issues' continue to work.
"""

from data.persistence.sqlite.issues_cache import IssuesCacheMixin
from data.persistence.sqlite.issues_crud import IssuesCRUDMixin


class IssuesMixin(IssuesCRUDMixin, IssuesCacheMixin):
    """Combined mixin for JIRA issues operations (delegates to focused mixins)."""

    pass


__all__ = ["IssuesMixin"]
