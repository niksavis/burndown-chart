"""
Query management for profile workspaces.

This module provides fast query switching within profiles (<50ms target).
Queries are named JQL configurations within a profile, each with isolated data cache.

Key Functions:
    get_active_query_id() -> str: Get current active query ID
    switch_query(query_id: str) -> None: Switch to different query (<50ms)
    list_queries_for_profile(profile_id: str) -> List[Dict]: List all queries
    create_query(profile_id: str, name: str, jql: str) -> str: Create new query
    delete_query(profile_id: str, query_id: str) -> None: Delete query

Performance Requirements:
    - switch_query(): <50ms (updates profiles.json active_query_id)
    - list_queries_for_profile(): <100ms (reads directory + metadata)

Data Isolation:
    Each query has dedicated data in SQLite database:
    - jira_issues table (JIRA API responses)
    - jira_changelog table (changelog data)
    - project_statistics table (statistics, scope, metadata)
    - metrics_snapshots table (historical metrics)

    Legacy JSON files (jira_cache.json, project_data.json) are deprecated.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when dependency chain is not satisfied (e.g., JIRA not configured before query creation)."""

    pass


def _generate_unique_query_id() -> str:
    """
    Generate unique query ID using UUID.

    Format: q_{12-char-hex} (e.g., q_a1b2c3d4e5f6)

    Returns:
        str: Unique query ID guaranteed to not collide

    Examples:
        >>> _generate_unique_query_id()
        'q_a1b2c3d4e5f6'
    """
    import uuid

    return f"q_{uuid.uuid4().hex[:12]}"


def get_active_query_id() -> Optional[str]:
    """
    Get the currently active query ID.

    Returns:
        Optional[str]: Active query ID (e.g., "main", "bugs", "12w") or None if no active query

    Raises:
        ValueError: If app state not accessible

    Example:
        >>> get_active_query_id()
        'main'
        >>> get_active_query_id()  # No active query in profile
        None
    """
    backend = get_backend()
    active_query_id = backend.get_app_state("active_query_id")
    return active_query_id


def get_active_profile_id() -> str:
    """
    Get the currently active profile ID.

    Returns:
        str: Active profile ID (e.g., "default", "kafka")

    Raises:
        ValueError: If app state not accessible

    Example:
        >>> get_active_profile_id()
        'default'
    """
    backend = get_backend()
    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("active_profile_id not found in app state")
    return active_profile_id


def switch_query(query_id: str) -> None:
    """
    Switch to a different query within the active profile.

    Performance: Target <50ms (atomic database update).

    Args:
        query_id: ID of query to switch to (e.g., "bugs", "12w")

    Raises:
        ValueError: If query doesn't exist
        IOError: If database update fails

    Side Effects:
        - Updates app_state with new active_query_id
        - Subsequent get_active_query_workspace() calls return new path
        - UI callbacks will reload data from new query workspace

    Example:
        >>> switch_query("bugs")
        # Now all data operations use profiles/kafka/queries/bugs/
    """
    backend = get_backend()

    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("active_profile_id not found in app state")

    # Validate query exists
    query = backend.get_query(active_profile_id, query_id)
    if not query:
        available_queries = backend.list_queries(active_profile_id)
        available_ids = [q["id"] for q in available_queries]
        raise ValueError(
            f"Query '{query_id}' not found in profile '{active_profile_id}'. "
            f"Available queries: {available_ids}"
        )

    # Update active_query_id
    backend.set_app_state("active_query_id", query_id)

    logger.info(f"Switched to query '{query_id}' in profile '{active_profile_id}'")


def list_queries_for_profile(profile_id: Optional[str] = None) -> List[Dict]:
    """
    List all queries in a profile.

    Performance: Target <100ms (database query).

    Args:
        profile_id: Profile ID to list queries for (defaults to active profile)

    Returns:
        List[Dict]: Query metadata dicts with keys:
            - id (str): Query ID
            - name (str): Display name
            - jql (str): JQL query string
            - created_at (str): ISO timestamp
            - is_active (bool): Whether this is the active query

    Raises:
        ValueError: If profile doesn't exist

    Example:
        >>> list_queries_for_profile("kafka")
        [
            {"id": "main", "name": "All Issues", "jql": "project = KAFKA", "is_active": True},
            {"id": "bugs", "name": "Bugs Only", "jql": "project = KAFKA AND type = Bug", "is_active": False},
        ]
    """
    backend = get_backend()

    if profile_id is None:
        profile_id = get_active_profile_id()

    # Get queries from backend
    queries = backend.list_queries(profile_id)

    # Get active query for is_active flag
    try:
        active_query_id = get_active_query_id()
    except ValueError:
        active_query_id = None

    # Add is_active flag to each query
    for query in queries:
        query["is_active"] = query["id"] == active_query_id

    return queries


def get_query_dropdown_options(profile_id: Optional[str] = None) -> List[Dict]:
    """
    Build dropdown options with timestamps for query selector.

    Formats queries as dropdown options with:
    - "→ Create New Query" at top
    - Query name with [Active] postfix
    - Timestamp after [Active] (e.g., "Query Name [Active] (2h ago)")

    Args:
        profile_id: Profile ID (defaults to active profile)

    Returns:
        List[Dict]: Dropdown options with 'label' and 'value' keys

    Example:
        >>> get_query_dropdown_options("kafka")
        [
            {"label": "→ Create New Query", "value": "__create_new__"},
            {"label": "Main Query [Active] (2h ago)", "value": "q_123"},
            {"label": "Bug Queries (Jan 28)", "value": "q_456"}
        ]
    """
    from data.persistence.factory import get_backend
    from data.time_formatting import get_relative_time_string
    from data.database import get_db_connection
    import logging

    logger = logging.getLogger(__name__)

    backend = get_backend()
    if profile_id is None:
        profile_id = backend.get_app_state("active_profile_id")

    if not profile_id:
        return [{"label": "→ Create New Query", "value": "__create_new__"}]

    # Get base queries
    queries = list_queries_for_profile(profile_id)

    # Build dropdown options
    options = [{"label": "→ Create New Query", "value": "__create_new__"}]

    for query in queries:
        label = query.get("name", "Unnamed Query")
        query_id = query.get("id", "")

        logger.info(
            f"[DROPDOWN] Processing query: id={query_id}, name='{label}', is_active={query.get('is_active', False)}"
        )

        # Add [Active] postfix
        if query.get("is_active", False):
            label += " [Active]"

        # Add timestamp for ALL queries (not just active)
        try:
            from pathlib import Path

            db_path = getattr(backend, "db_path", Path("profiles/burndown.db"))

            with get_db_connection(Path(db_path)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT fetched_at
                    FROM jira_issues
                    WHERE profile_id = ? AND query_id = ?
                    ORDER BY fetched_at DESC
                    LIMIT 1
                    """,
                    (profile_id, query_id),
                )
                row = cursor.fetchone()

                if row:
                    timestamp_iso = row[0]
                    logger.info(
                        f"[DROPDOWN] Found timestamp for {query_id}: {timestamp_iso}"
                    )
                    relative_time = get_relative_time_string(timestamp_iso)
                    label += f" ({relative_time})"
                else:
                    logger.debug(f"[DROPDOWN] No data fetched yet for query {query_id}")
        except Exception as e:
            logger.error(
                f"[DROPDOWN] Failed to get timestamp for query {query_id}: {e}",
                exc_info=True,
            )

        options.append({"label": label, "value": query_id})

    return options


def create_query(profile_id: str, name: str, jql: str, description: str = "") -> str:
    """
    Create a new query in a profile.

    Args:
        profile_id: Profile to create query in
        name: Display name for query (can contain ANY characters)
        jql: JQL query string
        description: Optional description for the query

    Returns:
        str: Generated query ID (UUID format: q_a1b2c3d4e5f6)

    Raises:
        ValueError: If profile doesn't exist
        DependencyError: If JIRA not configured (dependency chain violation)

    Side Effects:
        - Creates query in database
        - Adds query metadata

    Example:
        >>> query_id = create_query("p_abc123", "High Priority Bugs!", "project = KAFKA AND priority = High")
        >>> assert query_id.startswith("q_") and len(query_id) == 14
    """
    backend = get_backend()

    # Validate profile exists
    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' not found")

    # DEPENDENCY CHECK: JIRA must be configured before creating queries
    jira_config = profile.get("jira_config", {})
    if not jira_config.get("configured"):
        raise DependencyError(
            "JIRA must be configured before creating queries. "
            "Go to 'JIRA Configuration' section and test connection first."
        )

    # Optional warning if field mappings not configured
    field_mappings = profile.get("field_mappings", {})
    if not field_mappings:
        logger.warning(
            f"[Query] Field mappings not configured in profile '{profile_id}' - "
            "metrics may be limited. Configure field mappings for full DORA/Flow metrics."
        )

    # Generate unique query ID using UUID
    query_id = _generate_unique_query_id()

    # Create query data
    query_dict = {
        "id": query_id,
        "name": name,
        "jql": jql,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_used": datetime.now(timezone.utc).isoformat(),
    }

    # Save query using backend
    backend.save_query(profile_id, query_dict)

    logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

    return query_id


def update_query(
    profile_id: str,
    query_id: str,
    name: Optional[str] = None,
    jql: Optional[str] = None,
    description: Optional[str] = None,
) -> bool:
    """
    Update an existing query's metadata.

    Args:
        profile_id: Profile containing the query
        query_id: Query to update
        name: New display name (optional, keeps existing if None)
        jql: New JQL query string (optional, keeps existing if None)
        description: New description (optional, keeps existing if None - NOTE: not yet persisted in database)

    Returns:
        bool: True if update successful

    Raises:
        ValueError: If profile or query doesn't exist

    Side Effects:
        - Updates query in database atomically
        - Logs update operation

    Example:
        >>> update_query("kafka", "main", jql="project = KAFKA AND priority > Medium")
        True
    """
    # Use repository pattern - get backend and load query
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Load existing query data from database
    query_data = backend.get_query(profile_id, query_id)
    if not query_data:
        raise ValueError(f"Query '{query_id}' not found in profile '{profile_id}'")

    # Track what changed for logging
    changes = []

    # Update fields if provided
    if name is not None and name != query_data.get("name"):
        old_name = query_data.get("name")
        query_data["name"] = name
        changes.append(f"name: '{old_name}' -> '{name}'")

    if jql is not None and jql != query_data.get("jql"):
        query_data["jql"] = jql
        changes.append("jql updated")

    if description is not None and description != query_data.get("description"):
        query_data["description"] = description
        changes.append("description updated (not persisted)")

    # If no changes, return early
    if not changes:
        logger.info(f"No changes to query '{query_id}' in profile '{profile_id}'")
        return True

    # Ensure id is in query_data
    query_data["id"] = query_id

    # Save via backend (expects profile_id and query dict)
    # Note: only name, jql, last_used are persisted (schema limitation)
    backend.save_query(profile_id, query_data)

    logger.info(
        f"Updated query '{query_id}' in profile '{profile_id}': {', '.join(changes)}"
    )

    return True


def delete_query(profile_id: str, query_id: str, allow_cascade: bool = False) -> None:
    """
    Delete a query and all its cached data.

    Args:
        profile_id: Profile containing the query
        query_id: Query to delete
        allow_cascade: If True, allow deletion even if it's the last query or active query
                       (used during profile cascade deletion). Default: False for safety.

    Raises:
        ValueError: If query doesn't exist or is the only query in profile (unless allow_cascade=True)
        PermissionError: If query is currently active (must switch first, unless allow_cascade=True)

    Side Effects:
        - Deletes query from database (CASCADE DELETE handled by backend)

    Example:
        >>> delete_query("kafka", "old-query")  # Normal deletion with safety checks
        >>> delete_query("kafka", "main", allow_cascade=True)  # Cascade deletion (no safety checks)
    """
    backend = get_backend()

    # Prevent deleting active query (unless cascading)
    if not allow_cascade:
        try:
            active_query_id = get_active_query_id()
            if query_id == active_query_id:
                raise PermissionError(
                    f"Cannot delete active query '{query_id}'. Switch to another query first."
                )
        except ValueError:
            pass  # No active query, safe to delete

    # Validate query exists
    query = backend.get_query(profile_id, query_id)
    if not query:
        raise ValueError(f"Query '{query_id}' not found in profile '{profile_id}'")

    # Delete query using backend (CASCADE DELETE to all related data)
    backend.delete_query(profile_id, query_id)

    logger.info(f"Deleted query '{query_id}' from profile '{profile_id}'")


def validate_query_exists_for_data_operation(query_id: str) -> None:
    """
    Ensure query exists and is saved before allowing data fetch/calculation.

    This enforces the dependency chain: Query must be saved before data operations.

    Args:
        query_id: Query ID to validate

    Raises:
        DependencyError: If query doesn't exist (not saved yet)
        ValueError: If active profile not set

    Example:
        >>> validate_query_exists_for_data_operation("main")
        # No exception - query exists, data operations allowed

        >>> validate_query_exists_for_data_operation("unsaved-query")
        # Raises DependencyError - query not saved
    """
    backend = get_backend()

    try:
        active_profile_id = get_active_profile_id()
    except ValueError as e:
        raise ValueError(f"Cannot validate query: {e}")

    # Check if query exists in database
    query = backend.get_query(active_profile_id, query_id)
    if not query:
        raise DependencyError(
            f"Query '{query_id}' must be saved before executing data operations. "
            "Click 'Save Query' first, then 'Update Data'."
        )

    # Verify query has required fields (name and jql)
    if not query.get("name") or not query.get("jql"):
        raise DependencyError(
            f"Query '{query_id}' is not properly initialized. "
            "Re-save the query with name and JQL, then try again."
        )

    logger.debug(f"[Query] Validated query '{query_id}' exists for data operation")
