"""
Database schema initialization for SQLite persistence.

This module defines the 12-table normalized schema per data-model.md.
Implements all CREATE TABLE statements, indexes, and foreign key constraints.

Tables:
1. profiles - Profile configurations
2. queries - Saved JQL queries
3. app_state - Application state (key-value)
4. jira_issues - Normalized JIRA issues (replaces jira_cache JSON blob)
5. jira_changelog_entries - Normalized changelog (replaces jira_changelog_cache JSON blob)
6. project_statistics - Normalized weekly stats (replaces project_data.statistics array)
7. project_scope - Project scope data (small JSON)
8. metrics_data_points - Normalized metrics (replaces metrics_snapshots JSON blob)
9. budget_settings - Profile-level budget configuration
10. budget_revisions - Budget change event log
11. task_progress - Runtime task progress
12. (future tables can be added here)

Usage:
    from data.migration.schema import create_schema

    with get_db_connection() as conn:
        create_schema(conn)
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create all database tables and indexes.

    Implements 10-table normalized schema from data-model.md.
    Safe to call multiple times (uses IF NOT EXISTS).

    Args:
        conn: Active database connection

    Raises:
        sqlite3.Error: If table creation fails

    Example:
        >>> from data.database import get_db_connection
        >>> with get_db_connection() as conn:
        ...     create_schema(conn)
    """
    cursor = conn.cursor()

    logger.info("Creating database schema (12 normalized tables)")

    # Table 1: app_state (key-value for application settings)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    # Table 2: profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            last_used TEXT NOT NULL,
            jira_config TEXT NOT NULL DEFAULT '{}',
            field_mappings TEXT NOT NULL DEFAULT '{}',
            forecast_settings TEXT NOT NULL DEFAULT '{"pert_factor": 1.2, "deadline": null, "data_points_count": 12}',
            project_classification TEXT NOT NULL DEFAULT '{}',
            flow_type_mappings TEXT NOT NULL DEFAULT '{}',
            show_milestone INTEGER DEFAULT 0,
            show_points INTEGER DEFAULT 0
        )
    """)

    # Indexes for profiles
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_profiles_last_used ON profiles(last_used DESC)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_name ON profiles(name)")

    # Table 3: queries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            name TEXT NOT NULL,
            jql TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_used TEXT NOT NULL,
            PRIMARY KEY (profile_id, id),
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
    """)

    # Indexes for queries
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_queries_profile ON queries(profile_id, last_used DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_queries_name ON queries(profile_id, name)"
    )

    # Table 4: jira_issues (normalized - replaces jira_cache JSON blob)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jira_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            cache_key TEXT NOT NULL,
            issue_key TEXT NOT NULL,
            summary TEXT,
            status TEXT,
            assignee TEXT,
            issue_type TEXT,
            priority TEXT,
            resolution TEXT,
            created TEXT,
            updated TEXT,
            resolved TEXT,
            points REAL,
            project_key TEXT,
            project_name TEXT,
            fix_versions TEXT,
            labels TEXT,
            components TEXT,
            custom_fields TEXT,
            expires_at TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
            UNIQUE(profile_id, query_id, issue_key)
        )
    """)

    # Indexes for jira_issues (9 indexes per data-model.md)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_query ON jira_issues(profile_id, query_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_key ON jira_issues(profile_id, query_id, issue_key)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_status ON jira_issues(profile_id, query_id, status)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_assignee ON jira_issues(profile_id, query_id, assignee)"
    )

    # Table 4b: jira_cache (metadata for cache validation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jira_cache (
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            cache_key TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            config_hash TEXT NOT NULL,
            issue_count INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            PRIMARY KEY (profile_id, query_id, cache_key),
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE
        )
    """)

    # Index for jira_cache
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_cache_key ON jira_cache(profile_id, query_id, cache_key)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_type ON jira_issues(profile_id, query_id, issue_type)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_resolved ON jira_issues(resolved DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_project ON jira_issues(project_key)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_expiry ON jira_issues(expires_at)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_jira_issues_cache ON jira_issues(cache_key)"
    )

    # Table 5: jira_changelog_entries (normalized - replaces jira_changelog_cache JSON blob)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jira_changelog_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            issue_key TEXT NOT NULL,
            change_date TEXT NOT NULL,
            author TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT DEFAULT 'jira',
            old_value TEXT,
            new_value TEXT,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
            FOREIGN KEY (profile_id, query_id, issue_key) REFERENCES jira_issues(profile_id, query_id, issue_key) ON DELETE CASCADE
        )
    """)

    # Indexes for jira_changelog_entries (6 indexes per data-model.md)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_query ON jira_changelog_entries(profile_id, query_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_issue ON jira_changelog_entries(profile_id, query_id, issue_key)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_field ON jira_changelog_entries(field_name)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_date ON jira_changelog_entries(change_date DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_status ON jira_changelog_entries(field_name, new_value) WHERE field_name='status'"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_changelog_expiry ON jira_changelog_entries(expires_at)"
    )

    # Table 6: project_statistics (normalized - replaces project_data.statistics array)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            stat_date TEXT NOT NULL,
            week_label TEXT,
            remaining_items INTEGER,
            remaining_total_points REAL,
            items_added INTEGER DEFAULT 0,
            items_completed INTEGER DEFAULT 0,
            completed_items INTEGER DEFAULT 0,
            completed_points REAL DEFAULT 0.0,
            created_items INTEGER DEFAULT 0,
            created_points REAL DEFAULT 0.0,
            velocity_items REAL DEFAULT 0.0,
            velocity_points REAL DEFAULT 0.0,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
            UNIQUE(profile_id, query_id, stat_date)
        )
    """)

    # Indexes for project_statistics (3 indexes per data-model.md)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_stats_query ON project_statistics(profile_id, query_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_stats_date ON project_statistics(profile_id, query_id, stat_date DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_stats_week ON project_statistics(week_label)"
    )

    # Table 7: project_scope (small JSON aggregate data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS project_scope (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            scope_data TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
            UNIQUE(profile_id, query_id)
        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_project_scope_query ON project_scope(profile_id, query_id)"
    )

    # Table 8: metrics_data_points (normalized - replaces metrics_snapshots JSON blob)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metrics_data_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            query_id TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            metric_category TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            metric_unit TEXT,
            excluded_issue_count INTEGER DEFAULT 0,
            calculation_metadata TEXT,
            forecast_value REAL,
            forecast_confidence_low REAL,
            forecast_confidence_high REAL,
            calculated_at TEXT NOT NULL,
            FOREIGN KEY (profile_id, query_id) REFERENCES queries(profile_id, id) ON DELETE CASCADE,
            UNIQUE(profile_id, query_id, snapshot_date, metric_category, metric_name)
        )
    """)

    # Indexes for metrics_data_points (5 indexes per data-model.md)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_query ON metrics_data_points(profile_id, query_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics_data_points(profile_id, query_id, snapshot_date DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics_data_points(profile_id, query_id, metric_name, snapshot_date DESC)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_category ON metrics_data_points(metric_category)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metrics_value ON metrics_data_points(metric_name, metric_value)"
    )

    # Table 9: budget_settings (profile-level budget configuration)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL UNIQUE,
            time_allocated_weeks INTEGER NOT NULL,
            team_cost_per_week_eur REAL,
            cost_rate_type TEXT DEFAULT 'weekly',
            currency_symbol TEXT DEFAULT '€',
            budget_total_eur REAL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_budget_settings_profile ON budget_settings(profile_id)"
    )

    # Table 10: budget_revisions (budget change event log)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_revisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT NOT NULL,
            revision_date TEXT NOT NULL,
            week_label TEXT NOT NULL,
            time_allocated_weeks_delta INTEGER DEFAULT 0,
            team_cost_delta REAL DEFAULT 0,
            budget_total_delta REAL DEFAULT 0,
            revision_reason TEXT,
            created_at TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
        )
    """)

    # Indexes for budget_revisions
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_budget_revisions_profile ON budget_revisions(profile_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_budget_revisions_week ON budget_revisions(profile_id, week_label)"
    )

    # Table 11: task_progress (runtime state)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_progress (
            task_name TEXT PRIMARY KEY,
            progress_percent REAL NOT NULL,
            status TEXT NOT NULL,
            message TEXT DEFAULT '',
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()

    logger.info("Database schema created successfully (12 tables, 35+ indexes)")


def get_schema_version(conn: sqlite3.Connection) -> str:
    """
    Get current schema version from app_state table.

    Args:
        conn: Active database connection

    Returns:
        str: Schema version (e.g., "1.0"), or "0.0" if not set
    """
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM app_state WHERE key = 'schema_version'")
        result = cursor.fetchone()
        return result[0] if result else "0.0"
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return "0.0"


def set_schema_version(conn: sqlite3.Connection, version: str) -> None:
    """
    Set schema version in app_state table.

    Args:
        conn: Active database connection
        version: Version string (e.g., "1.0")
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO app_state (key, value)
        VALUES ('schema_version', ?)
    """,
        (version,),
    )
    conn.commit()
    logger.info(f"Schema version set to {version}")
