from callbacks import (
    about_dialog,  # noqa: F401
    active_work_timeline,
    ai_prompt_generation,  # noqa: F401
    app_update,  # noqa: F401
    banner_status_icons,  # noqa: F401
    budget_settings,  # noqa: F401
    bug_analysis,
    dora_flow_metric_details,  # noqa: F401
    dora_flow_metrics,  # noqa: F401
    field_mapping,  # noqa: F401
    field_value_fetch,  # noqa: F401
    flow_metrics_callbacks,  # noqa: F401
    import_export,  # noqa: F401
    integrated_query_management,  # noqa: F401
    jira_config,  # noqa: F401
    jira_data_store,  # noqa: F401
    jira_metadata,  # noqa: F401
    jql_editor,
    metrics_refresh_callbacks,  # noqa: F401
    migration,  # noqa: F401
    mobile_navigation,
    namespace_autocomplete,  # noqa: F401
    profile_management,  # noqa: F401
    progress_bar,  # noqa: F401
    query_management,  # noqa: F401
    query_switching,  # noqa: F401
    report_generation,  # noqa: F401
    settings,
    sprint_filters,  # noqa: F401
    sprint_selector,  # noqa: F401
    sprint_tracker,  # noqa: F401
    statistics,
    version_update_notification,  # noqa: F401
    visualization,
)
from ui.layout import USE_ACCORDION_SETTINGS

if USE_ACCORDION_SETTINGS:
    from callbacks import accordion_settings  # noqa: F401
else:
    from callbacks import tabbed_settings  # noqa: F401

from callbacks import settings_panel  # noqa: F401


def register_all_callbacks(app):
    statistics.register(app)
    visualization.register(app)
    active_work_timeline.register(app)

    settings.register(app)

    settings_panel.register_clientside_callbacks(app)

    mobile_navigation.register(app)
    jql_editor.register_jql_editor_callbacks(app)
    bug_analysis.register(app)
