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


def get_active_query_id() -> str:
    """
    Get the currently active query ID.

    Returns:
        str: Active query ID (e.g., "main", "bugs", "12w") or None if no active query

    Raises:
        ValueError: If profiles.json not found or malformed

    Example:
        >>> get_active_query_id()
        'main'
        >>> get_active_query_id()  # No active query in profile
        None
    """
    if not PROFILES_FILE.exists():
        raise ValueError(f"profiles.json not found at {PROFILES_FILE}")

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        active_query_id = profiles_data.get("active_query_id")
        # Return None if no active query (valid state for empty profile)
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
        - Creates profiles/{profile_id}/queries/{query_id}/ directory
        - Creates query.json with metadata

    Example:
        >>> query_id = create_query("p_abc123", "High Priority Bugs!", "project = KAFKA AND priority = High")
        >>> assert query_id.startswith("q_") and len(query_id) == 14
    """
    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    # DEPENDENCY CHECK: JIRA must be configured before creating queries
    profile_file = profile_dir / "profile.json"
    if profile_file.exists():
        with open(profile_file, "r", encoding="utf-8") as f:
            profile_data = json.load(f)

        jira_config = profile_data.get("jira_config", {})
        if not jira_config.get("configured"):
            raise DependencyError(
                "JIRA must be configured before creating queries. "
                "Go to 'JIRA Configuration' section and test connection first."
            )

        # Optional warning if field mappings not configured
        field_mappings = profile_data.get("field_mappings", {})
        if not field_mappings:
            logger.warning(
                f"[Query] Field mappings not configured in profile '{profile_id}' - "
                "metrics may be limited. Configure field mappings for full DORA/Flow metrics."
            )
    else:
        raise ValueError(f"Profile configuration not found at {profile_file}")

    # Generate unique query ID using UUID
    query_id = _generate_unique_query_id()

    # Create query directory (UUID guarantees no collision)
    query_dir = profile_dir / "queries" / query_id

    # Create directory
    query_dir.mkdir(parents=True, exist_ok=True)

    # Create query.json
    query_data = {
        "name": name,
        "jql": jql,
        "description": description,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    query_file = query_dir / "query.json"
    with open(query_file, "w", encoding="utf-8") as f:
        json.dump(query_data, f, indent=2)

    # Update profiles.json to add query to profile's queries list
    if PROFILES_FILE.exists():
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        if profile_id in profiles_data.get("profiles", {}):
            if "queries" not in profiles_data["profiles"][profile_id]:
                profiles_data["profiles"][profile_id]["queries"] = []
            if query_id not in profiles_data["profiles"][profile_id]["queries"]:
                profiles_data["profiles"][profile_id]["queries"].append(query_id)

        # Atomic write
        temp_file = PROFILES_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2)
        temp_file.replace(PROFILES_FILE)

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
        description: New description (optional, keeps existing if None)

    Returns:
        bool: True if update successful, False otherwise

    Raises:
        ValueError: If profile or query doesn't exist

    Side Effects:
        - Updates query.json atomically
        - Adds updated_at timestamp
        - Logs update operation

    Example:
        >>> update_query("kafka", "main", jql="project = KAFKA AND priority > Medium")
        True
    """
    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    query_dir = profile_dir / "queries" / query_id
    if not query_dir.exists():
        raise ValueError(f"Query '{query_id}' not found in profile '{profile_id}'")

    query_file = query_dir / "query.json"
    if not query_file.exists():
        raise ValueError(f"Query metadata file not found at {query_file}")

    try:
        # Load existing query data
        with open(query_file, "r", encoding="utf-8") as f:
            query_data = json.load(f)

        # Track what changed for logging
        changes = []

        # Update fields if provided
        if name is not None and name != query_data.get("name"):
            query_data["name"] = name
            changes.append(f"name: '{query_data.get('name')}' -> '{name}'")

        if jql is not None and jql != query_data.get("jql"):
            query_data["jql"] = jql
            changes.append("jql updated")

        if description is not None and description != query_data.get("description"):
            query_data["description"] = description
            changes.append("description updated")

        # If no changes, return early
        if not changes:
            logger.info(f"No changes to query '{query_id}' in profile '{profile_id}'")
            return True

        # Add updated timestamp
        query_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Atomic write
        temp_file = query_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(query_data, f, indent=2)
        temp_file.replace(query_file)

        logger.info(
            f"Updated query '{query_id}' in profile '{profile_id}': {', '.join(changes)}"
        )

        return True

    except Exception as e:
        logger.error(
            f"Failed to update query '{query_id}' in profile '{profile_id}': {e}"
        )
        return False


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
        - Deletes profiles/{profile_id}/queries/{query_id}/ directory and all contents

    Example:
        >>> delete_query("kafka", "old-query")  # Normal deletion with safety checks
        >>> delete_query("kafka", "main", allow_cascade=True)  # Cascade deletion (no safety checks)
    """
    import shutil

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

    profile_dir = PROFILES_DIR / profile_id
    if not profile_dir.exists():
        raise ValueError(f"Profile '{profile_id}' not found at {profile_dir}")

    query_dir = profile_dir / "queries" / query_id
    if not query_dir.exists():
        raise ValueError(
            f"Query '{query_id}' not found in profile '{profile_id}' at {query_dir}"
        )

    # Allow deletion of last query when allow_cascade=True
    # (No restriction - users can delete the last query)

    # Delete directory and all contents
    shutil.rmtree(query_dir)

    # Update profiles.json to remove query from profile's queries list
    if PROFILES_FILE.exists():
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            profiles_data = json.load(f)

        if profile_id in profiles_data.get("profiles", {}):
            if "queries" in profiles_data["profiles"][profile_id]:
                if query_id in profiles_data["profiles"][profile_id]["queries"]:
                    profiles_data["profiles"][profile_id]["queries"].remove(query_id)

        # Atomic write
        temp_file = PROFILES_FILE.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(profiles_data, f, indent=2)
        temp_file.replace(PROFILES_FILE)

    logger.info(f"Deleted query '{query_id}' from profile '{profile_id}'")


def validate_query_exists_for_data_operation(query_id: str) -> None:
    """
    Ensure query exists and is saved before allowing data fetch/calculation.

    This enforces the dependency chain: Query must be saved before data operations.

    Args:
        query_id: Query ID to validate

    Raises:
        DependencyError: If query doesn't exist (not saved yet)
        ValueError: If profiles.json malformed or active profile not set

    Example:
        >>> validate_query_exists_for_data_operation("main")
        # No exception - query exists, data operations allowed

        >>> validate_query_exists_for_data_operation("unsaved-query")
        # Raises DependencyError - query not saved
    """
    try:
        active_profile_id = get_active_profile_id()
    except ValueError as e:
        raise ValueError(f"Cannot validate query: {e}")

    # Check if query directory exists
    query_dir = PROFILES_DIR / active_profile_id / "queries" / query_id
    if not query_dir.exists():
        raise DependencyError(
            f"Query '{query_id}' must be saved before executing data operations. "
            "Click 'Save Query' first, then 'Update Data'."
        )

    # Check if query.json exists (ensures query is properly initialized)
    query_file = query_dir / "query.json"
    if not query_file.exists():
        raise DependencyError(
            f"Query '{query_id}' is not properly initialized. "
            "Re-save the query with name and JQL, then try again."
        )

    logger.debug(f"[Query] Validated query '{query_id}' exists for data operation")
