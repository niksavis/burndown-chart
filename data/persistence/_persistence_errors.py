class PersistenceError(Exception):
    pass


class ProfileNotFoundError(PersistenceError):
    pass


class QueryNotFoundError(PersistenceError):
    pass


class ValidationError(PersistenceError):
    pass


class DatabaseCorruptionError(PersistenceError):
    pass
