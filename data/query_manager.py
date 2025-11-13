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
    Each query has dedicated directory with isolated cache:
    - jira_cache.json (JIRA API responses)
    - jira_changelog_cache.json (changelog data)
    - project_data.json (statistics, scope, metadata)
    - metrics_snapshots.json (historical metrics)
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone

from data.profile_manager import PROFILES_DIR, PROFILES_FILE

logger = logging.getLogger(__name__)


def get_active_query_id() -> str:
    """
    Get the currently active query ID.

    Returns:
        str: Active query ID (e.g., "main", "bugs", "12w")

    Raises:
        ValueError: If profiles.json not found or malformed

    Example:
        >>> get_active_query_id()
        'main'
    """
    if not PROFILES_FILE.exists():
        raise ValueError(f"profiles.json not found at {PROFILES_FILE}")

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        active_query_id = profiles_data.get("active_query_id")
        if not active_query_id:
            raise ValueError("active_query_id not found in profiles.json")

        return active_query_id

    except json.JSONDecodeError as e:
        raise ValueError(f"profiles.json is malformed: {e}")


def get_active_profile_id() -> str:
    """
    Get the currently active profile ID.

    Returns:
        str: Active profile ID (e.g., "default", "kafka")

    Raises:
        ValueError: If profiles.json not found or malformed

    Example:
        >>> get_active_profile_id()
        'default'
    """
    if not PROFILES_FILE.exists():
        raise ValueError(f"profiles.json not found at {PROFILES_FILE}")

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        active_profile_id = profiles_data.get("active_profile_id")
        if not active_profile_id:
            raise ValueError("active_profile_id not found in profiles.json")

        return active_profile_id

    except json.JSONDecodeError as e:
        raise ValueError(f"profiles.json is malformed: {e}")


def switch_query(query_id: str) -> None:
    """
    Switch to a different query within the active profile.

    Performance: Target <50ms (atomic JSON update).

    Args:
        query_id: ID of query to switch to (e.g., "bugs", "12w")

    Raises:
        ValueError: If query doesn't exist or profiles.json malformed
        IOError: If profiles.json cannot be written

    Side Effects:
        - Updates profiles.json with new active_query_id
        - Subsequent get_active_query_workspace() calls return new path
        - UI callbacks will reload data from new query workspace

    Example:
        >>> switch_query("bugs")
        # Now all data operations use profiles/kafka/queries/bugs/
    """
    if not PROFILES_FILE.exists():
        raise ValueError(f"profiles.json not found at {PROFILES_FILE}")

    try:
        # Read current state
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        active_profile_id = profiles_data.get("active_profile_id")
        if not active_profile_id:
            raise ValueError("active_profile_id not found in profiles.json")

        # Validate query exists
        profile_queries_dir = PROFILES_DIR / active_profile_id / "queries"
        query_dir = profile_queries_dir / query_id
        if not query_dir.exists():
            available_queries = [
                d.name for d in profile_queries_dir.iterdir() if d.is_dir()
            ]
            raise ValueError(
                f"Query '{query_id}' not found in profile '{active_profile_id}'. "
                f"Available queries: {available_queries}"
            )

        # Update active_query_id
        profiles_data["active_query_id"] = query_id

        # Write atomically (write to temp file, then rename)
        temp_file = PROFILES_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2)

        temp_file.replace(PROFILES_FILE)

        logger.info(f"Switched to query '{query_id}' in profile '{active_profile_id}'")

    except json.JSONDecodeError as e:
        raise ValueError(f"profiles.json is malformed: {e}")
    except IOError as e:
        raise IOError(f"Failed to update profiles.json: {e}")


def list_queries_for_profile(profile_id: Optional[str] = None) -> List[Dict]:
    """
    List all queries in a profile.

    Performance: Target <100ms (directory scan + metadata reads).

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
    if profile_id is None:
        profile_id = get_active_profile_id()

    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    queries_dir = profile_dir / "queries"
    if not queries_dir.exists():
        return []

    # Get active query for is_active flag
    try:
        active_query_id = get_active_query_id()
    except ValueError:
        active_query_id = None

    queries = []
    for query_dir in queries_dir.iterdir():
        if not query_dir.is_dir():
            continue

        query_id = query_dir.name
        query_file = query_dir / "query.json"

        # Load metadata if exists, otherwise use defaults
        if query_file.exists():
            try:
                with open(query_file, "r", encoding="utf-8") as f:
                    query_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {query_file}: {e}")
                query_data = {}
        else:
            query_data = {}

        queries.append(
            {
                "id": query_id,
                "name": query_data.get("name", query_id.replace("_", " ").title()),
                "jql": query_data.get("jql", ""),
                "created_at": query_data.get(
                    "created_at", datetime.now(timezone.utc).isoformat()
                ),
                "is_active": query_id == active_query_id,
            }
        )

    # Sort by created_at (oldest first)
    queries.sort(key=lambda q: q["created_at"])

    return queries


def create_query(profile_id: str, name: str, jql: str) -> str:
    """
    Create a new query in a profile.

    Args:
        profile_id: Profile to create query in
        name: Display name for query
        jql: JQL query string

    Returns:
        str: Generated query ID (slugified name)

    Raises:
        ValueError: If profile doesn't exist or query ID conflicts

    Side Effects:
        - Creates profiles/{profile_id}/queries/{query_id}/ directory
        - Creates query.json with metadata

    Example:
        >>> create_query("kafka", "High Priority Bugs", "project = KAFKA AND priority = High")
        'high-priority-bugs'
    """
    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    # Generate query ID from name (slugify)
    query_id = name.lower().replace(" ", "-")
    query_id = "".join(c for c in query_id if c.isalnum() or c == "-")
    query_id = query_id.strip("-")

    if not query_id:
        raise ValueError(f"Cannot generate valid query ID from name '{name}'")

    # Check for conflicts
    query_dir = profile_dir / "queries" / query_id
    if query_dir.exists():
        raise ValueError(f"Query '{query_id}' already exists in profile '{profile_id}'")

    # Create directory
    query_dir.mkdir(parents=True, exist_ok=True)

    # Create query.json
    query_data = {
        "name": name,
        "jql": jql,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    query_file = query_dir / "query.json"
    with open(query_file, "w", encoding="utf-8") as f:
        json.dump(query_data, f, indent=2)

    logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

    return query_id


def delete_query(profile_id: str, query_id: str) -> None:
    """
    Delete a query and all its cached data.

    Args:
        profile_id: Profile containing the query
        query_id: Query to delete

    Raises:
        ValueError: If query doesn't exist or is the only query in profile
        PermissionError: If query is currently active (must switch first)

    Side Effects:
        - Deletes profiles/{profile_id}/queries/{query_id}/ directory and all contents

    Example:
        >>> delete_query("kafka", "old-query")
    """
    import shutil

    # Prevent deleting active query
    try:
        active_query_id = get_active_query_id()
        if query_id == active_query_id:
            raise PermissionError(
                f"Cannot delete active query '{query_id}'. Switch to another query first."
            )
    except ValueError:
        pass  # No active query, safe to delete

    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    query_dir = profile_dir / "queries" / query_id
    if not query_dir.exists():
        raise ValueError(
            f"Query '{query_id}' not found in profile '{profile_id}' at {query_dir}"
        )

    # Ensure at least one query remains
    queries_dir = profile_dir / "queries"
    remaining_queries = [
        d for d in queries_dir.iterdir() if d.is_dir() and d != query_dir
    ]
    if not remaining_queries:
        raise ValueError(
            f"Cannot delete last query '{query_id}' in profile '{profile_id}'. "
            "Create another query first."
        )

    # Delete directory and all contents
    shutil.rmtree(query_dir)

    logger.info(f"Deleted query '{query_id}' from profile '{profile_id}'")
