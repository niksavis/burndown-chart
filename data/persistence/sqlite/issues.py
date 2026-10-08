from data.persistence.sqlite.issues_cache import IssuesCacheMixin
from data.persistence.sqlite.issues_crud import IssuesCRUDMixin


class IssuesMixin(IssuesCRUDMixin, IssuesCacheMixin):
    pass


__all__ = ["IssuesMixin"]
