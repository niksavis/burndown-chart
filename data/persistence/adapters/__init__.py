"""Data persistence adapters - public API."""

# Re-export all public functions for backwards compatibility
from data.persistence.adapters.app_settings import (
    load_app_settings,
    save_app_settings,
)
from data.persistence.adapters.core import (
    DateTimeEncoder,
    convert_timestamps_to_strings,
    should_sync_jira,
)
from data.persistence.adapters.jira_config import (
    cleanup_legacy_jira_fields,
    get_default_jira_config,
    load_jira_configuration,
    migrate_csv_to_json,
    migrate_jira_config,
    save_jira_configuration,
    validate_jira_config,
)
from data.persistence.adapters.legacy_data import (
    load_project_data_legacy,
    load_statistics_legacy,
    save_jira_data_unified,
)
from data.persistence.adapters.metrics_history import (
    get_metric_trend_data,
    load_metrics_history,
    save_metrics_snapshot,
)
from data.persistence.adapters.parameter_panel import (
    load_parameter_panel_state,
    save_parameter_panel_state,
)
from data.persistence.adapters.project_data import (
    load_project_data,
    save_project_data,
)
from data.persistence.adapters.sample_data import (
    generate_realistic_sample_data,
    read_and_clean_data,
)
from data.persistence.adapters.scope import (
    add_project_statistic,
    calculate_project_scope_from_jira,
    get_project_scope,
    get_project_statistics,
    update_project_scope,
    update_project_scope_from_jira,
)
from data.persistence.adapters.settings import (
    load_settings,
    save_settings,
)
from data.persistence.adapters.statistics import (
    load_statistics,
    save_statistics,
    save_statistics_from_csv_import,
)
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)

__all__ = [
    "DateTimeEncoder",
    "convert_timestamps_to_strings",
    "should_sync_jira",
    "save_app_settings",
    "load_app_settings",
    "save_project_data",
    "load_project_data",
    "save_settings",
    "load_settings",
    "save_statistics",
    "save_statistics_from_csv_import",
    "load_statistics",
    "generate_realistic_sample_data",
    "read_and_clean_data",
    "load_unified_project_data",
    "save_unified_project_data",
    "save_jira_data_unified",
    "migrate_csv_to_json",
    "load_statistics_legacy",
    "load_project_data_legacy",
    "get_project_statistics",
    "get_project_scope",
    "update_project_scope",
    "update_project_scope_from_jira",
    "calculate_project_scope_from_jira",
    "add_project_statistic",
    "get_default_jira_config",
    "load_jira_configuration",
    "save_jira_configuration",
    "validate_jira_config",
    "migrate_jira_config",
    "cleanup_legacy_jira_fields",
    "load_metrics_history",
    "save_metrics_snapshot",
    "get_metric_trend_data",
    "load_parameter_panel_state",
    "save_parameter_panel_state",
]
