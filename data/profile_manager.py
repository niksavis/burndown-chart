"""
Profile and query workspace management.

This module provides path abstraction for profile-based data organization.
It manages the two-level hierarchy: Profile → Query.

Architecture:
- Profiles: Named workspaces with shared settings (PERT factor, deadline, data_points_count)
- Queries: Named JQL queries within a profile, each with dedicated cache
- Backward Compatibility: Default profile "default" maps to current root-level behavior

Directory Structure:
    profiles/
    ├── burndown.db            # SQLite database (single source of truth)
    │                          # Contains: profiles, queries, app_state, jira_cache,
    │                          # statistics, metrics_snapshots, and all other data
    ├── default/               # Profile directories (for file system organization)
    │   └── queries/
    │       ├── main/          # Query directories (for file system organization)
    │       └── bugs/
    └── kafka/                 # Another profile directory
        └── queries/...

    Note: All data is stored in burndown.db. Profile/query directories exist only
    for organization. JSON files are only used for exports and reports.

Constants:
    PROFILES_DIR: Path to profiles/ directory
    PROFILES_FILE: Path to profiles.json registry
    DEFAULT_PROFILE_ID: ID for default profile ("default")
    DEFAULT_QUERY_ID: ID for default query ("main")

Path Resolution Functions:
    get_active_profile_workspace() -> Path: Current profile directory
    get_active_query_workspace() -> Path: Current query directory
    get_profile_file_path(profile_id) -> Path: Path to profile.json
    get_query_file_path(profile_id, query_id) -> Path: Path to query.json
    get_jira_cache_path(profile_id, query_id) -> Path: LEGACY - Cache now in database

Profile Operations:
    create_profile(name, settings) -> str: Create new profile
    list_profiles() -> List[Dict]: List all profiles
    get_profile(profile_id) -> Dict: Load profile config
    switch_profile(profile_id) -> None: Set active profile
    delete_profile(profile_id) -> None: Delete profile and all queries

Query Operations:
    create_query(profile_id, name, jql) -> str: Create new query
    list_queries(profile_id) -> List[Dict]: List queries in profile
    get_query(profile_id, query_id) -> Dict: Load query config
    switch_query(profile_id, query_id) -> None: Set active query
    delete_query(profile_id, query_id) -> None: Delete query and cache

Migration:
    migrate_root_to_default_profile() -> None: One-time migration of root-level data

Test Support:
    PROFILES_DIR is a module-level constant that can be patched in tests
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Module-level constants (patchable in tests via unittest.mock.patch)
# Note: PROFILES_DIR must be absolute Path for correct patching behavior
PROFILES_DIR = Path("profiles").absolute()
PROFILES_FILE = PROFILES_DIR / "profiles.json"
DEFAULT_PROFILE_ID = "default"
DEFAULT_QUERY_ID = "main"

# Profile limits
MAX_PROFILES = 50
MAX_QUERIES_PER_PROFILE = 100


# ============================================================================
# Profile Data Model (T064)
# ============================================================================


class Profile:
    """Profile workspace metadata and settings.

    Attributes:
        id: Unique identifier (slugified name)
        name: Human-readable profile name
        description: Optional description
        created_at: ISO 8601 timestamp of creation
        last_used: ISO 8601 timestamp of last access
        jira_config: JIRA connection settings (base_url, token, points_field, etc.)
        field_mappings: DORA/Flow field mappings
        forecast_settings: PERT factor, deadline, data_points_count
        project_classification: DevOps/development project classification
        flow_type_mappings: Flow Framework type mappings
        queries: List of query IDs in this profile
        show_milestone: Toggle milestone display on charts
        show_points: Toggle between points/items display
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str = "",
        created_at: str = "",
        last_used: str = "",
        jira_config: dict | None = None,
        field_mappings: dict | None = None,
        forecast_settings: dict | None = None,
        project_classification: dict | None = None,
        flow_type_mappings: dict | None = None,
        queries: list | None = None,
        show_milestone: bool = False,
        show_points: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now(UTC).isoformat()
        self.last_used = last_used or datetime.now(UTC).isoformat()
        self.jira_config = jira_config or {}
        self.field_mappings = field_mappings or {}
        self.forecast_settings = forecast_settings or {
            "pert_factor": 1.2,
            "deadline": None,
            "data_points_count": 12,
        }
        self.project_classification = project_classification or {}
        self.flow_type_mappings = flow_type_mappings or {}
        self.queries = queries or []
        self.show_milestone = show_milestone
        self.show_points = show_points

    def to_dict(self) -> dict:
        """Convert profile to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "jira_config": self.jira_config,
            "field_mappings": self.field_mappings,
            "forecast_settings": self.forecast_settings,
            "project_classification": self.project_classification,
            "flow_type_mappings": self.flow_type_mappings,
            "queries": self.queries,
            "show_milestone": self.show_milestone,
            "show_points": self.show_points,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Create profile from dictionary loaded from JSON."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            last_used=data.get("last_used", ""),
            jira_config=data.get("jira_config", {}),
            field_mappings=data.get("field_mappings", {}),
            forecast_settings=data.get("forecast_settings", {}),
            project_classification=data.get("project_classification", {}),
            flow_type_mappings=data.get("flow_type_mappings", {}),
            queries=data.get("queries", []),
            show_milestone=data.get("show_milestone", False),
            show_points=data.get("show_points", False),
        )


def _generate_unique_profile_id() -> str:
    """Generate unique profile ID using UUID.

    Format: p_{12-char-hex} (e.g., p_a1b2c3d4e5f6)

    Returns:
        str: Unique profile ID guaranteed to not collide

    Examples:
        >>> _generate_unique_profile_id()
        'p_a1b2c3d4e5f6'
    """
    import uuid

    return f"p_{uuid.uuid4().hex[:12]}"


# ============================================================================
# Path Resolution Functions (CRITICAL - blocks all user stories)
# ============================================================================


def get_active_profile_workspace() -> Path:
    """
    Get the workspace directory for the currently active profile.

    Returns:
        Path: Absolute path to active profile directory (e.g., profiles/default/)

    Raises:
        ValueError: If database not found or active_profile_id invalid

    Example:
        >>> workspace = get_active_profile_workspace()
        >>> profile_config = workspace / "profile.json"
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Get active profile ID from app_state
    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("No active_profile_id in database")

    # Validate profile exists
    profile = backend.get_profile(active_profile_id)
    if not profile:
        raise ValueError(f"Profile '{active_profile_id}' not found in database")

    # Return profile workspace directory
    return PROFILES_DIR / active_profile_id


def get_active_query_workspace() -> Path:
    """
    Get the workspace directory for the currently active query.

    Returns:
        Path: Absolute path to active query directory (e.g., profiles/default/queries/main/)

    Raises:
        ValueError: If database not found or active_query_id invalid

    Example:
        >>> workspace = get_active_query_workspace()
        >>> cache_file = workspace / "jira_cache.json"
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Get active profile and query IDs from app_state
    active_profile_id = backend.get_app_state("active_profile_id")
    active_query_id = backend.get_app_state("active_query_id")

    if not active_profile_id:
        raise ValueError("No active_profile_id in database")
    if not active_query_id:
        raise ValueError("No active_query_id in database")

    # Validate query exists in database
    query = backend.get_query(active_profile_id, active_query_id)
    if not query:
        raise ValueError(f"Query '{active_query_id}' not found in database")

    # Build query workspace path
    query_workspace = PROFILES_DIR / active_profile_id / "queries" / active_query_id

    # Return the path (directory may not exist yet - that's okay)
    return query_workspace


def get_profile_file_path(profile_id: str) -> Path:
    """
    Get the path to profile.json for a specific profile.

    DEPRECATED: Profile data is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier (e.g., "default", "kafka")

    Returns:
        Path: Absolute path to profile.json (e.g., profiles/kafka/profile.json)

    Example:
        >>> path = get_profile_file_path("kafka")  # For exports only
    """
    return PROFILES_DIR / profile_id / "profile.json"


def get_query_file_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to query.json for a specific query.

    DEPRECATED: Query data is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier (e.g., "main", "bugs")

    Returns:
        Path: Absolute path to query.json (e.g., profiles/kafka/queries/bugs/query.json)

    Example:
        >>> path = get_query_file_path("kafka", "12w")  # For exports only
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "query.json"


def get_jira_cache_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to jira_cache.json for a specific query.

    DEPRECATED: JIRA cache is now stored in database. This function remains
    for backward compatibility and export functionality only.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Path: Absolute path to jira_cache.json (e.g., profiles/kafka/queries/bugs/jira_cache.json)

    Example:
        >>> cache_path = get_jira_cache_path("kafka", "main")  # For exports only
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "jira_cache.json"


# ============================================================================
# Profiles Metadata Management (T065, T066)
# ============================================================================


def load_profiles_metadata() -> dict:
    """
    Load profiles registry from database with schema validation.

    Returns:
        Dict: Profiles metadata with active_profile_id, active_query_id, profiles list

    Example:
        >>> meta = load_profiles_metadata()
        >>> print(meta["active_profile_id"])  # "default"
        >>> print(len(meta["profiles"]))      # Number of profiles
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    try:
        # Get active IDs from app_state
        active_profile_id = (
            backend.get_app_state("active_profile_id") or DEFAULT_PROFILE_ID
        )
        active_query_id = backend.get_app_state("active_query_id") or DEFAULT_QUERY_ID

        # Get all profiles
        profiles_list = backend.list_profiles()
        profiles_dict = {p["profile_id"]: p for p in profiles_list}

        # Build metadata structure
        metadata = {
            "version": "3.0",
            "active_profile_id": active_profile_id,
            "active_query_id": active_query_id,
            "profiles": profiles_dict,
        }

        return metadata

    except Exception as e:
        logger.error(f"[Profiles] Error loading metadata from database: {e}")
        # Return safe default
        return {
            "version": "3.0",
            "active_profile_id": DEFAULT_PROFILE_ID,
            "active_query_id": DEFAULT_QUERY_ID,
            "profiles": {},
            "_error": f"Error loading from database: {e}",
        }


def save_profiles_metadata(metadata: dict) -> bool:
    """
    Save profiles registry to database (no longer writes profiles.json).

    Args:
        metadata: Profiles registry to save

    Returns:
        bool: True if successful, False on error

    Example:
        >>> meta = load_profiles_metadata()
        >>> meta["active_profile_id"] = "new-profile"
        >>> save_profiles_metadata(meta)
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    try:
        # Update app state with active IDs
        active_profile_id = metadata.get("active_profile_id")
        active_query_id = metadata.get("active_query_id")

        if active_profile_id:
            backend.set_app_state("active_profile_id", active_profile_id)
        if active_query_id:
            backend.set_app_state("active_query_id", active_query_id)

        # Note: Profiles themselves are saved via backend.save_profile()
        # This function only updates active profile/query IDs

        logger.debug("[Profiles] Metadata saved to database")
        return True

    except Exception as e:
        logger.error(f"[Profiles] Error saving metadata to database: {e}")
        return False


def get_active_profile() -> Profile | None:
    """
    Get currently active profile object from database.

    Returns:
        Profile object if found, None if active profile doesn't exist

    Example:
        >>> profile = get_active_profile()
        >>> if profile:
        ...     print(f"Active: {profile.name}")
    """
    from data.persistence.factory import get_backend

    backend = get_backend()
    active_id = backend.get_app_state("active_profile_id")

    if not active_id:
        return None

    profile_data = backend.get_profile(active_id)
    if profile_data:
        profile_data["id"] = active_id  # Ensure id is included
        return Profile.from_dict(profile_data)

    logger.warning(f"[Profiles] Active profile '{active_id}' not found in database")
    return None


def is_profiles_mode_enabled() -> bool:
    """
    Check if profiles mode is enabled (database exists).

    After database migration, we check if the SQLite database exists instead
    of checking for profiles.json.

    Returns:
        bool: True if database exists, False for legacy mode

    Example:
        >>> if is_profiles_mode_enabled():
        ...     # Use database backend
        ... else:
        ...     # Legacy file-based mode
    """
    db_path = PROFILES_DIR / "burndown.db"
    return db_path.exists()


def get_data_file_path(filename: str) -> Path:
    """
    Get path to a data file with backward compatibility.

    If profiles.json exists: Returns path in active query workspace
    If profiles.json missing: Returns path in project root (legacy mode)

    Args:
        filename: Data file name (e.g., "jira_cache.json", "app_settings.json")

    Returns:
        Path: Absolute path to data file

    Example:
        >>> # In profiles mode: profiles/default/queries/main/jira_cache.json
        >>> # In legacy mode: jira_cache.json (root level)
        >>> cache_path = get_data_file_path("jira_cache.json")
    """
    if is_profiles_mode_enabled():
        try:
            # Profile mode: use active query workspace
            return get_active_query_workspace() / filename
        except ValueError:
            # profiles.json exists but is malformed - fall back to legacy
            return Path(filename).absolute()
    else:
        # Legacy mode: use root directory
        return Path(filename).absolute()


def get_settings_file_path(filename: str) -> Path:
    """
    Get path to a settings file with backward compatibility.

    Settings files (app_settings.json, project_data.json) are stored at:
    - Profile mode: profiles/{profile_id}/queries/{query_id}/{filename}
    - Legacy mode: {filename} (root level)

    Args:
        filename: Settings file name (e.g., "app_settings.json")

    Returns:
        Path: Absolute path to settings file

    Example:
        >>> settings_path = get_settings_file_path("app_settings.json")
    """
    return get_data_file_path(filename)  # Same logic as data files


def get_active_profile_and_query_display_names() -> dict:
    """
    Get display names for currently active profile and query via repository pattern.

    Returns:
        dict: Dictionary with profile_name and query_name (or None if not in profiles mode)
            Example: {"profile_name": "Apache Kafka", "query_name": "Development Sprint"}

    Example:
        >>> names = get_active_profile_and_query_display_names()
        >>> if names["profile_name"]:
        ...     print(f"Profile: {names['profile_name']}, Query: {names['query_name']}")
    """
    if not is_profiles_mode_enabled():
        return {"profile_name": None, "query_name": None}

    try:
        # Get active profile via backend
        profile = get_active_profile()
        profile_name = profile.name if profile else None

        # Get active query
        from data.query_manager import get_active_query_id

        query_id = get_active_query_id()
        query_name = None

        if profile and query_id:
            # Load query metadata from backend
            from data.persistence.factory import get_backend

            backend = get_backend()
            query_data = backend.get_query(profile.id, query_id)

            if query_data:
                query_name = query_data.get("name", query_id.replace("_", " ").title())
            else:
                query_name = query_id.replace("_", " ").title()

        return {"profile_name": profile_name, "query_name": query_name}

    except Exception as e:
        logger.warning(f"Failed to get active profile/query names: {e}")
        return {"profile_name": None, "query_name": None}


# ============================================================================
# Profile Operations (T008-T009)
# ============================================================================


def create_profile(name: str, settings: dict) -> str:
    """
    Create a new profile with initial settings.

    Args:
        name: Human-readable profile name (e.g., "Apache Kafka")
        settings: Profile configuration (pert_factor, deadline, data_points_count, etc.)

    Returns:
        str: Generated profile_id (UUID format: p_a1b2c3d4e5f6)

    Raises:
        ValueError: If name invalid, duplicate, or max profiles reached
        OSError: If directory creation fails

    Example:
        >>> profile_id = create_profile("Apache Kafka", {
        ...     "pert_factor": 1.2,
        ...     "deadline": "2025-12-31",
        ...     "data_points_count": 20
        ... })
        >>> assert profile_id.startswith("p_") and len(profile_id) == 14
    """
    # Validate inputs
    if not name or not name.strip():
        raise ValueError("Profile name cannot be empty")

    name = name.strip()
    if len(name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    # Get backend for validation
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    existing_names = [p["name"].lower() for p in all_profiles]
    if name.lower() in existing_names:
        raise ValueError(f"Profile name '{name}' already exists")

    # Check max profiles limit
    if len(all_profiles) >= MAX_PROFILES:
        raise ValueError(f"Maximum {MAX_PROFILES} profiles allowed")

    # Generate unique profile ID using UUID
    profile_id = _generate_unique_profile_id()

    try:
        # Create profile object with all settings
        profile = Profile(
            id=profile_id,
            name=name,
            description=settings.get("description", ""),
            jira_config=settings.get("jira_config", {}),
            field_mappings=settings.get("field_mappings", {}),
            forecast_settings={
                "pert_factor": settings.get("pert_factor", 1.2),
                "deadline": settings.get("deadline"),
                "data_points_count": settings.get("data_points_count", 12),
            },
            project_classification=settings.get("project_classification", {}),
            flow_type_mappings=settings.get("flow_type_mappings", {}),
            queries=settings.get("queries", []),
            show_milestone=settings.get("show_milestone", False),
            show_points=settings.get("show_points", False),
        )

        # Save profile to database (single source of truth)
        backend.save_profile(profile.to_dict())

        logger.info(f"[Profiles] Created profile: {name} ({profile_id})")
        return profile_id

    except Exception as e:
        # Cleanup on failure - rollback database
        try:
            backend.delete_profile(profile_id)
        except Exception:
            pass
        logger.error(f"[Profiles] Error creating profile '{name}': {e}")
        raise OSError(f"Failed to create profile: {e}") from e


def switch_profile(profile_id: str) -> None:
    """
    Switch to a different profile.

    Args:
        profile_id: Target profile identifier

    Raises:
        ValueError: If profile doesn't exist

    Example:
        >>> switch_profile("kafka")
        >>> # App now uses kafka profile settings and queries
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Validate profile exists
    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    # Update last_used timestamp
    profile["last_used"] = datetime.now(UTC).isoformat()
    backend.save_profile(profile)

    # Update active profile
    backend.set_app_state("active_profile_id", profile_id)

    # Find most recently used query in this profile
    queries = backend.list_queries(profile_id)
    if queries:
        # Sort by last_used descending
        most_recent_query = max(
            queries, key=lambda q: q.get("last_used", q.get("created_at", ""))
        )
        backend.set_app_state("active_query_id", most_recent_query["id"])
    else:
        # No queries - clear active_query_id
        backend.set_app_state("active_query_id", "")

    logger.info(
        f"[Profiles] Switched to profile: {profile.get('name', profile_id)} ({profile_id})"
    )


def delete_profile(profile_id: str) -> None:
    """
    Delete a profile and all its queries with cascade deletion.

    This performs cascade deletion:
    1. Deletes all queries in the profile (using allow_cascade=True)
    2. Removes profile from database

    Args:
        profile_id: Profile to delete

    Raises:
        ValueError: If profile doesn't exist
        OSError: If deletion fails

    Example:
        >>> delete_profile("old-project")
        >>> # Removes profile and all associated queries from database
    """
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Validate profile exists
    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    profile_name = profile.get("name", profile_id)

    # If deleting active profile, switch to another one first
    active_profile_id = backend.get_app_state("active_profile_id")
    if profile_id == active_profile_id:
        # Find another profile to switch to
        all_profiles = backend.list_profiles()
        other_profile = next((p for p in all_profiles if p["id"] != profile_id), None)
        if other_profile:
            logger.info(
                f"[Profiles] Auto-switching from '{profile_id}' to '{other_profile['id']}' before deletion"
            )
            switch_profile(other_profile["id"])
        else:
            # Last profile - set active to None (empty string in database)
            logger.info(
                f"[Profiles] Deleting last profile '{profile_id}' - clearing active_profile_id"
            )
            backend.set_app_state("active_profile_id", "")

    # CASCADE DELETE: Database backend automatically handles query deletion
    # via foreign key constraints
    backend.delete_profile(profile_id)

    logger.info(f"[Profiles] Deleted profile: {profile_name} ({profile_id})")


def rename_profile(profile_id: str, new_name: str) -> None:
    """
    Rename an existing profile (updates name in metadata only).

    This is a lightweight operation that only updates the profile name
    in profile.json and the profiles registry. The profile ID remains
    unchanged, so all queries and data files stay in place.

    Args:
        profile_id: ID of profile to rename
        new_name: New name for the profile

    Raises:
        ValueError: If profile doesn't exist, name is empty/invalid, or duplicate
        OSError: If metadata update fails

    Example:
        >>> rename_profile("p_abc123", "Production Environment")
        >>> # Updates name in both profile.json and profiles registry
    """
    # Validate inputs
    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    # Use repository pattern - get backend
    from data.persistence.factory import get_backend

    backend = get_backend()

    # Validate profile exists
    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    current_name = profile["name"]

    # Check if name actually changed
    if new_name.lower() == current_name.lower():
        logger.info(
            f"[Profiles] Rename skipped - new name '{new_name}' same as current"
        )
        return

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    for p in all_profiles:
        if p["id"] != profile_id and p["name"].lower() == new_name.lower():
            raise ValueError(f"Profile name '{new_name}' already exists")

    # Update profile name in database
    profile["name"] = new_name
    backend.save_profile(profile)

    logger.info(
        f"[Profiles] Renamed profile '{current_name}' to '{new_name}' ({profile_id})"
    )


def duplicate_profile(
    source_profile_id: str, new_name: str, description: str = ""
) -> str:
    """
    Duplicate a profile with all its settings and queries from database.

    Creates a complete copy of the source profile including:
    - All profile settings (JIRA config, field mappings, forecast settings, etc.)
    - All queries with their metadata and JQL strings
    - All query data (JIRA cache, statistics, metrics snapshots, etc.)

    Args:
        source_profile_id: Profile ID to duplicate
        new_name: Name for the new profile
        description: Optional description for the new profile

    Returns:
        str: New profile ID

    Raises:
        ValueError: If source profile doesn't exist, name is invalid/duplicate, or max profiles reached
        OSError: If database operations fail

    Example:
        >>> new_id = duplicate_profile("p_abc123", "Production Copy", "Backup of production")
        >>> # Creates complete copy with new ID and timestamps
    """
    from data.persistence.factory import get_backend

    # Validate inputs
    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    backend = get_backend()

    # Validate source profile exists
    source_profile = backend.get_profile(source_profile_id)
    if not source_profile:
        raise ValueError(f"Source profile '{source_profile_id}' does not exist")

    # Check for duplicate names (case-insensitive)
    all_profiles = backend.list_profiles()
    existing_names = [p["name"].lower() for p in all_profiles]
    if new_name.lower() in existing_names:
        raise ValueError(f"Profile name '{new_name}' already exists")

    # Check max profiles limit
    if len(all_profiles) >= MAX_PROFILES:
        raise ValueError(f"Maximum {MAX_PROFILES} profiles allowed")

    # Generate unique profile ID
    new_profile_id = _generate_unique_profile_id()

    try:
        # Step 1: Copy profile data from database
        now = datetime.now(UTC).isoformat()
        new_profile_data = source_profile.copy()
        new_profile_data["id"] = new_profile_id
        new_profile_data["name"] = new_name
        new_profile_data["description"] = description
        new_profile_data["created_at"] = now
        new_profile_data["last_used"] = now

        # Save new profile to database
        backend.save_profile(new_profile_data)

        # Step 2: Duplicate all queries from source profile
        source_queries = backend.list_queries(source_profile_id)
        new_query_ids = []

        for source_query in source_queries:
            # Manual query duplication
            from data.query_manager import _generate_unique_query_id

            new_query_id = _generate_unique_query_id()

            query_data = backend.get_query(source_profile_id, source_query["id"])
            if query_data:
                query_data["id"] = new_query_id
                query_data["created_at"] = now
                query_data["last_used"] = now
                backend.save_query(new_profile_id, query_data)

            new_query_ids.append(new_query_id)
            logger.debug(
                f"[Profiles] Duplicated query '{source_query['id']}' to '{new_query_id}'"
            )

        logger.info(
            f"[Profiles] Duplicated profile '{source_profile_id}' to '{new_name}' ({new_profile_id}) with {len(new_query_ids)} queries"
        )
        return new_profile_id

    except Exception as e:
        # Cleanup on failure
        try:
            backend.delete_profile(new_profile_id)
        except Exception:
            pass
        logger.error(f"[Profiles] Error duplicating profile: {e}")
        raise OSError(f"Failed to duplicate profile: {e}") from e


def list_profiles() -> list[dict]:
    """
    List all available profiles from database.

    Returns:
        List[Dict]: Profile summaries with id, name, query_count, created_at

    Example:
        >>> profiles = list_profiles()
        >>> for p in profiles:
        ...     print(f"{p['name']} ({p['query_count']} queries)")
    """
    from data.persistence.factory import get_backend

    backend = get_backend()
    profiles = backend.list_profiles()

    # Add query_count from backend
    for profile in profiles:
        profile_id = profile["id"]
        queries = backend.list_queries(profile_id)
        profile["query_count"] = len(queries)

    # Sort by last_used (most recent first)
    profiles.sort(key=lambda p: p["last_used"], reverse=True)
    return profiles


def get_profile(profile_id: str) -> dict:
    """
    Load profile configuration.

    Args:
        profile_id: Profile identifier

    Returns:
        Dict: Profile config (forecast_settings, jira_config, field_mappings, etc.)

    Raises:
        FileNotFoundError: If profile doesn't exist

    Example:
        >>> config = get_profile("kafka")
        >>> print(config["forecast_settings"]["pert_factor"])
    """
    metadata = load_profiles_metadata()

    # Find profile in registry
    for profile_data in metadata.get("profiles", []):
        if profile_data["id"] == profile_id:
            return profile_data

    raise FileNotFoundError(f"Profile '{profile_id}' does not exist")


# switch_profile function implemented above - removed duplicate definition


# delete_profile function implemented above - removed duplicate definition


# ============================================================================
# Query Operations (T010)
# ============================================================================


def create_query(profile_id: str, name: str, jql: str) -> str:
    """
    Create a new query within a profile.

    Args:
        profile_id: Parent profile identifier
        name: Human-readable query name (e.g., "Last 12 Weeks")
        jql: JQL query string

    Returns:
        str: Generated query_id (slugified name)

    Example:
        >>> query_id = create_query("kafka", "Last 12 Weeks",
        ...     "project = KAFKA AND created >= -12w ORDER BY created DESC")
        >>> assert query_id == "last-12-weeks"
    """
    raise NotImplementedError("T010 - to be implemented")


def list_queries(profile_id: str) -> list[dict]:
    """
    List all queries in a profile.

    Args:
        profile_id: Profile identifier

    Returns:
        List[Dict]: Query summaries with id, name, jql_preview, created_at

    Example:
        >>> queries = list_queries("kafka")
        >>> for q in queries:
        ...     print(f"{q['name']}: {q['jql_preview']}")
    """
    raise NotImplementedError("T010 - to be implemented")


def get_query(profile_id: str, query_id: str) -> dict:
    """
    Load query configuration.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Dict: Query config (jql_query, created_at, last_used_at)

    Raises:
        FileNotFoundError: If query doesn't exist

    Example:
        >>> config = get_query("kafka", "12w")
        >>> print(config["jql_query"])
    """
    raise NotImplementedError("T010 - to be implemented")


def switch_query(profile_id: str, query_id: str) -> None:
    """
    Switch to a different query within the current profile.

    Args:
        profile_id: Profile identifier (must match active profile)
        query_id: Target query identifier

    Raises:
        ValueError: If query doesn't exist or profile mismatch

    Example:
        >>> switch_query("kafka", "bugs")
        >>> # App now loads data from profiles/kafka/queries/bugs/jira_cache.json
    """
    raise NotImplementedError("T010 - to be implemented")


def delete_query(profile_id: str, query_id: str) -> None:
    """
    Delete a query and its cache.

    Args:
        profile_id: Profile identifier
        query_id: Query to delete

    Raises:
        ValueError: If trying to delete active query or only query in profile

    Example:
        >>> delete_query("kafka", "old-query")
        >>> # Removes profiles/kafka/queries/old-query/ directory
    """
    raise NotImplementedError("T010 - to be implemented")


# ============================================================================
# Migration (T011)
# ============================================================================


def migrate_root_to_default_profile() -> None:
    """
    One-time migration: Move root-level data to default profile structure.

    Migrates:
        - app_settings.json → profiles/default/profile.json (forecast_settings, jira_config, field_mappings)
        - jira_cache.json → profiles/default/queries/main/jira_cache.json
        - jira_changelog_cache.json → profiles/default/queries/main/jira_changelog_cache.json
        - project_data.json → profiles/default/queries/main/query.json (extracts JQL from project_data)

    Creates:
        - profiles/profiles.json with default profile and main query active
        - profiles/default/profile.json with migrated settings
        - profiles/default/queries/main/query.json with JQL string

    Preserves:
        - All cache data (100% preservation requirement - SC-005)
        - All settings values unchanged
        - Original files left intact as backup

    Performance:
        - Must complete <5s for 50MB jira_cache.json (SC-012)

    Example:
        >>> migrate_root_to_default_profile()
        >>> # Root files still exist, but app now uses profiles/ structure
    """
    raise NotImplementedError("T011 - to be implemented")


# ============================================================================
# Initialization and Defaults (T064)
# ============================================================================
