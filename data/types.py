"""Shared TypedDict definitions for core data-layer shapes."""

from typing import Any, NotRequired, Required, TypedDict


class AppSettings(TypedDict, total=False):
    """Application settings payload used across persistence and callbacks."""

    profile_id: str
    query_id: str
    jira_url: str
    jira_token: str
    jira_project: str
    jql: str
    data_window_weeks: int
    sprint_length_weeks: int
    working_days_per_week: int
    points_field: str
    sprint_field: str
    pert_factor: int
    deadline: str | None
    milestone: str | None
    data_points_count: int
    show_milestone: bool
    show_points: bool
    jql_query: str
    last_used_data_source: str
    active_jql_profile_id: str
    jira_config: "JiraConfig"
    field_mappings: dict[str, str]
    devops_projects: list[str]
    development_projects: list[str]
    devops_task_types: list[str]
    bug_types: list[str]
    story_types: list[str]
    task_types: list[str]
    production_environment_values: list[str]
    flow_end_statuses: list[str]
    active_statuses: list[str]
    flow_start_statuses: list[str]
    wip_statuses: list[str]
    flow_type_mappings: dict[str, str]
    cache_metadata: dict[str, str | None]
    field_mapping_notes: str


class JiraConfig(TypedDict, total=False):
    """JIRA integration configuration persisted in profile settings."""

    api_endpoint: str
    base_url: Required[str]
    api_version: str
    token: str
    jql: str
    custom_fields: dict[str, str]
    projects: list[str]
    points_field: str
    cache_size_mb: int
    max_results_per_call: int
    configured: bool
    last_test_timestamp: str | None
    last_test_success: bool | None


class MetricsResult(TypedDict, total=False):
    """Dashboard/report metrics produced by report calculations."""

    has_data: bool
    completed_items: int
    completed_points: float
    remaining_items: int
    remaining_points: float
    total_items: int
    total_points: float
    items_completion_pct: float
    points_completion_pct: float
    health_score: int
    health_status: str
    deadline: str | None
    deadline_months: int | None
    milestone: str | None
    forecast_date: str | None
    forecast_date_items: str | None
    forecast_date_points: str | None
    forecast_months: int | None
    forecast_metric: str
    velocity_items: float
    velocity_points: float
    velocity_items_recent_4w: float
    velocity_points_recent_4w: float
    weeks_count: int
    pert_time_items: float
    pert_time_points: float
    pert_time_items_weeks: float
    pert_time_points_weeks: float
    show_points: bool
    health_dimensions: dict[str, Any]
    velocity_cv: float
    trend_direction: str
    recent_velocity_change: float
    schedule_variance_days: float
    completion_confidence: int
    scope_change_rate: float
    forecast_weeks_items: float


class StatusBreakdownEntry(TypedDict):
    """Per-status counts and points captured in sprint snapshots."""

    count: int
    points: float


class SprintSnapshot(TypedDict):
    """Daily sprint snapshot used by burnup and CFD visualizations."""

    date: str
    completed_points: float
    total_scope: float
    status_breakdown: dict[str, StatusBreakdownEntry]
    completed_count: int
    total_count: int


class QueryProfile(TypedDict):
    """Persisted JQL query profile for reusable search definitions."""

    id: str
    name: str
    jql: str
    description: NotRequired[str]
    created_at: NotRequired[str]
    last_used: NotRequired[str]
    is_default: NotRequired[bool]
