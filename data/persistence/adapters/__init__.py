"""Data persistence adapters - public API."""

# Re-export all public functions for backwards compatibility
from data.persistence.adapters.core import (
    DateTimeEncoder,
    convert_timestamps_to_strings,
    should_sync_jira,
)
from data.persistence.adapters.app_settings import (
    save_app_settings,
    load_app_settings,
)
from data.persistence.adapters.project_data import (
    save_project_data,
    load_project_data,
)
from data.persistence.adapters.settings import (
    save_settings,
    load_settings,
)
from data.persistence.adapters.statistics import (
    save_statistics,
    save_statistics_from_csv_import,
    load_statistics,
)
from data.persistence.adapters.sample_data import (
    generate_realistic_sample_data,
    read_and_clean_data,
)
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)
from data.persistence.adapters.legacy_data import (
    save_jira_data_unified,
    load_statistics_legacy,
    load_project_data_legacy,
)
from data.persistence.adapters.jira_config import (
    migrate_csv_to_json,
)
from data.persistence.adapters.jira_config import (
    get_default_jira_config,
    load_jira_configuration,
    save_jira_configuration,
    validate_jira_config,
    migrate_jira_config,
    cleanup_legacy_jira_fields,
)
from data.persistence.adapters.metrics_history import (
    load_metrics_history,
    save_metrics_snapshot,
    get_metric_trend_data,
)
from data.persistence.adapters.parameter_panel import (
    load_parameter_panel_state,
    save_parameter_panel_state,
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
