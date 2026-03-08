"""Domain exception hierarchy for data-layer operations."""


class BurndownBaseError(Exception):
    """Base class for all burndown-chart domain exceptions."""


class JiraError(BurndownBaseError):
    """JIRA API connectivity, auth, or query errors."""


class JiraAuthError(JiraError):
    """JIRA authentication failed."""


class JiraQueryError(JiraError):
    """JIRA JQL query failed or returned unexpected data."""


class PersistenceError(BurndownBaseError):
    """Database or file persistence failures."""


class MetricsError(BurndownBaseError):
    """Calculation or data processing errors in metrics."""


class ConfigurationError(BurndownBaseError):
    """Invalid or missing configuration."""


class CacheError(BurndownBaseError):
    """Cache read/write/invalidation errors."""
