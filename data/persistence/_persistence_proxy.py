"""Lazy-loading backend proxy and adapter resolver for data.persistence."""

_backend_instance = None


def _get_backend_instance():
    """Get or create the backend instance (lazy initialization)."""
    global _backend_instance
    if _backend_instance is None:
        from data.persistence.factory import get_backend

        _backend_instance = get_backend()
    return _backend_instance


class _BackendProxy:
    """Proxy object that lazy-loads the backend on first attribute access."""

    def __getattr__(self, name: str):
        return getattr(_get_backend_instance(), name)


backend = _BackendProxy()

_ADAPTER_FUNCTIONS = {
    "generate_realistic_sample_data",
    "load_app_settings",
    "load_project_data",
    "load_settings",
    "load_statistics",
    "read_and_clean_data",
    "save_app_settings",
    "save_project_data",
    "save_settings",
    "save_statistics",
    "save_statistics_from_csv_import",
    "load_jira_configuration",
    "save_jira_configuration",
    "validate_jira_config",
    "save_jira_data_unified",
    "load_unified_project_data",
    "save_unified_project_data",
    "get_project_statistics",
    "get_project_scope",
    "update_project_scope",
    "update_project_scope_from_jira",
    "calculate_project_scope_from_jira",
}


def lazy_getattr(name: str):
    """Resolve adapter or factory function by name for data.persistence.__getattr__."""
    if name in _ADAPTER_FUNCTIONS:
        from data.persistence import adapters

        return getattr(adapters, name)

    if name == "get_backend":
        from data.persistence.factory import get_backend

        return get_backend

    raise AttributeError(f"module 'data.persistence' has no attribute '{name}'")
