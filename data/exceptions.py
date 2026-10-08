class BurndownBaseError(Exception):
    pass


class JiraError(BurndownBaseError):
    pass


class JiraAuthError(JiraError):
    pass


class JiraQueryError(JiraError):
    pass


class PersistenceError(BurndownBaseError):
    pass


class MetricsError(BurndownBaseError):
    pass


class ConfigurationError(BurndownBaseError):
    pass


class CacheError(BurndownBaseError):
    pass
