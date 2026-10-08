from . import (
    core_settings,
    data_update,
    jira_scope,
    jql_test,
    metrics,
    parameter_panel,
    query_profiles,
)


def register(app):

    core_settings.register(app)

    data_update.register(app)

    metrics.register(app)

    jira_scope.register(app)

    query_profiles.register(app)

    jql_test.register(app)

    parameter_panel.register(app)
