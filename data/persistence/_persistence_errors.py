"""Persistence layer exception hierarchy."""


class PersistenceError(Exception):
    """Base exception for persistence layer errors."""

    pass


class ProfileNotFoundError(PersistenceError):
    """Raised when profile doesn't exist."""

    pass


class QueryNotFoundError(PersistenceError):
    """Raised when query doesn't exist."""

    pass


class ValidationError(PersistenceError):
    """Raised when data validation fails."""

    pass


class DatabaseCorruptionError(PersistenceError):
    """Raised when database integrity check fails."""

    pass
