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
    ├── profiles.json          # Registry: active profile/query IDs, profile metadata
    ├── default/               # Default profile (migration target)
    │   ├── profile.json       # Profile settings (PERT, deadline, data_points_count)
    │   └── queries/
    │       ├── main/          # Default query (migration target)
    │       │   ├── query.json # Query metadata (JQL string)
    │       │   ├── jira_cache.json
    │       │   └── jira_changelog_cache.json
    │       └── bugs/          # Additional queries
    │           ├── query.json
    │           └── jira_cache.json
    └── kafka/                 # Another profile
        ├── profile.json
        └── queries/...

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
    get_jira_cache_path(profile_id, query_id) -> Path: Path to jira_cache.json

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

import json
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import logging

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
        jira_config: Optional[Dict] = None,
        field_mappings: Optional[Dict] = None,
        forecast_settings: Optional[Dict] = None,
        project_classification: Optional[Dict] = None,
        flow_type_mappings: Optional[Dict] = None,
        queries: Optional[list] = None,
        show_milestone: bool = False,
        show_points: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.last_used = last_used or datetime.now(timezone.utc).isoformat()
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

    def to_dict(self) -> Dict:
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
    def from_dict(cls, data: Dict) -> "Profile":
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
        ValueError: If profiles.json missing or active_profile_id invalid

    Example:
        >>> workspace = get_active_profile_workspace()
        >>> profile_config = workspace / "profile.json"
    """
    # Check if profiles.json exists
    if not PROFILES_FILE.exists():
        raise ValueError(
            "profiles.json not found - migration may not have been completed"
        )

    # Load profiles registry
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)

    # Get active profile ID
    active_profile_id = profiles_data.get("active_profile_id")
    if not active_profile_id:
        raise ValueError("No active_profile_id in profiles.json")

    # Validate profile exists in registry
    profiles = profiles_data.get("profiles", {})
    if active_profile_id not in profiles:
        raise ValueError(f"Profile '{active_profile_id}' not found in registry")

    # Return profile workspace directory
    return PROFILES_DIR / active_profile_id


def get_active_query_workspace() -> Path:
    """
    Get the workspace directory for the currently active query.

    Returns:
        Path: Absolute path to active query directory (e.g., profiles/default/queries/main/)

    Raises:
        ValueError: If profiles.json missing or active_query_id invalid

    Example:
        >>> workspace = get_active_query_workspace()
        >>> cache_file = workspace / "jira_cache.json"
    """
    # Check if profiles.json exists
    if not PROFILES_FILE.exists():
        raise ValueError(
            "profiles.json not found - migration may not have been completed"
        )

    # Load profiles registry
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        profiles_data = json.load(f)

    # Get active profile and query IDs
    active_profile_id = profiles_data.get("active_profile_id")
    active_query_id = profiles_data.get("active_query_id")

    if not active_profile_id:
        raise ValueError("No active_profile_id in profiles.json")
    if not active_query_id:
        raise ValueError("No active_query_id in profiles.json")

    # Validate profile exists
    profiles = profiles_data.get("profiles", {})
    if active_profile_id not in profiles:
        raise ValueError(f"Profile '{active_profile_id}' not found in registry")

    # Validate query exists in profile's query list
    profile_data = profiles[active_profile_id]
    queries = profile_data.get("queries", [])
    if active_query_id not in queries:
        raise ValueError(
            f"Query '{active_query_id}' not found in profile '{active_profile_id}'"
        )

    # Return query workspace directory
    return PROFILES_DIR / active_profile_id / "queries" / active_query_id


def get_profile_file_path(profile_id: str) -> Path:
    """
    Get the path to profile.json for a specific profile.

    Args:
        profile_id: Profile identifier (e.g., "default", "kafka")

    Returns:
        Path: Absolute path to profile.json (e.g., profiles/kafka/profile.json)

    Example:
        >>> path = get_profile_file_path("kafka")
        >>> with open(path) as f:
        ...     settings = json.load(f)
    """
    return PROFILES_DIR / profile_id / "profile.json"


def get_query_file_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to query.json for a specific query.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier (e.g., "main", "bugs")

    Returns:
        Path: Absolute path to query.json (e.g., profiles/kafka/queries/bugs/query.json)

    Example:
        >>> path = get_query_file_path("kafka", "12w")
        >>> with open(path) as f:
        ...     query = json.load(f)
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "query.json"


def get_jira_cache_path(profile_id: str, query_id: str) -> Path:
    """
    Get the path to jira_cache.json for a specific query.

    Args:
        profile_id: Profile identifier
        query_id: Query identifier

    Returns:
        Path: Absolute path to jira_cache.json (e.g., profiles/kafka/queries/bugs/jira_cache.json)

    Example:
        >>> cache_path = get_jira_cache_path("kafka", "main")
        >>> if cache_path.exists():
        ...     with open(cache_path) as f:
        ...         cache = json.load(f)
    """
    return PROFILES_DIR / profile_id / "queries" / query_id / "jira_cache.json"


# ============================================================================
# Profiles Metadata Management (T065, T066)
# ============================================================================


def load_profiles_metadata() -> Dict:
    """
    Load profiles registry with schema validation.

    Returns:
        Dict: Profiles metadata with active_profile_id, active_query_id, profiles list

    Example:
        >>> meta = load_profiles_metadata()
        >>> print(meta["active_profile_id"])  # "default"
        >>> print(len(meta["profiles"]))      # Number of profiles
    """
    if not PROFILES_FILE.exists():
        # Return default structure for new installations
        return {
            "version": "3.0",
            "active_profile_id": DEFAULT_PROFILE_ID,
            "active_query_id": DEFAULT_QUERY_ID,
            "profiles": {},
        }

    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Validate structure
        if not isinstance(metadata, dict):
            raise ValueError("profiles.json must contain a JSON object")

        # Ensure required fields
        metadata.setdefault("version", "3.0")
        metadata.setdefault("active_profile_id", DEFAULT_PROFILE_ID)
        metadata.setdefault("active_query_id", DEFAULT_QUERY_ID)
        metadata.setdefault("profiles", {})

        return metadata

    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"[Profiles] Corrupted profiles.json: {e}")
        # Return safe default - don't overwrite corrupted file
        return {
            "version": "3.0",
            "active_profile_id": DEFAULT_PROFILE_ID,
            "active_query_id": DEFAULT_QUERY_ID,
            "profiles": [],
            "_error": f"Corrupted profiles.json: {e}",
        }


def save_profiles_metadata(metadata: Dict) -> bool:
    """
    Atomic write to profiles.json using temp file + rename pattern.

    Args:
        metadata: Profiles registry to save

    Returns:
        bool: True if successful, False on error

    Example:
        >>> meta = load_profiles_metadata()
        >>> meta["active_profile_id"] = "new-profile"
        >>> save_profiles_metadata(meta)
    """
    try:
        # Ensure profiles directory exists
        PROFILES_DIR.mkdir(exist_ok=True)

        # Atomic write pattern: write to temp file, then rename
        temp_file = PROFILES_FILE.with_suffix(".tmp")

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Atomic rename (Windows requires removing existing file first)
        if PROFILES_FILE.exists():
            PROFILES_FILE.unlink()
        temp_file.rename(PROFILES_FILE)

        logger.debug(f"[Profiles] Metadata saved to {PROFILES_FILE}")
        return True

    except Exception as e:
        logger.error(f"[Profiles] Error saving metadata: {e}")
        # Clean up temp file if it exists
        temp_file = PROFILES_FILE.with_suffix(".tmp")
        if temp_file.exists():
            temp_file.unlink()
        return False


def get_active_profile() -> Optional[Profile]:
    """
    Get currently active profile object.

    Returns:
        Profile object if found, None if active profile doesn't exist

    Example:
        >>> profile = get_active_profile()
        >>> if profile:
        ...     print(f"Active: {profile.name}")
    """
    metadata = load_profiles_metadata()
    active_id = metadata.get("active_profile_id")

    if not active_id:
        return None

    profiles_dict = metadata.get("profiles", {})
    if active_id in profiles_dict:
        profile_data = profiles_dict[active_id]
        profile_data["id"] = active_id  # Ensure id is included
        return Profile.from_dict(profile_data)

    logger.warning(f"[Profiles] Active profile '{active_id}' not found in registry")
    return None


def is_profiles_mode_enabled() -> bool:
    """
    Check if profiles mode is enabled (profiles.json exists).

    Returns:
        bool: True if profiles.json exists, False for legacy mode

    Example:
        >>> if is_profiles_mode_enabled():
        ...     path = get_active_query_workspace() / "jira_cache.json"
        ... else:
        ...     path = Path("jira_cache.json")  # Legacy root-level
    """
    return PROFILES_FILE.exists()


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


# ============================================================================
# Profile Operations (T008-T009)
# ============================================================================


def create_profile(name: str, settings: Dict) -> str:
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

    # Load current metadata
    metadata = load_profiles_metadata()

    # Check for duplicate names (case-insensitive)
    profiles_dict = metadata.get("profiles", {})
    existing_names = [p["name"].lower() for p in profiles_dict.values()]
    if name.lower() in existing_names:
        raise ValueError(f"Profile name '{name}' already exists")

    # Check max profiles limit
    if len(profiles_dict) >= MAX_PROFILES:
        raise ValueError(f"Maximum {MAX_PROFILES} profiles allowed")

    # Generate unique profile ID using UUID
    profile_id = _generate_unique_profile_id()

    # Create profile directory structure
    profile_dir = PROFILES_DIR / profile_id
    queries_dir = profile_dir / "queries"

    try:
        profile_dir.mkdir(parents=True, exist_ok=True)
        queries_dir.mkdir(exist_ok=True)

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

        # Save profile.json
        profile_config_file = profile_dir / "profile.json"
        with open(profile_config_file, "w", encoding="utf-8") as f:
            json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)

        # Add to profiles registry
        metadata["profiles"][profile_id] = profile.to_dict()

        # Save updated metadata
        if not save_profiles_metadata(metadata):
            raise OSError("Failed to update profiles registry")

        logger.info(f"[Profiles] Created profile: {name} ({profile_id})")
        return profile_id

    except Exception as e:
        # Cleanup on failure
        if profile_dir.exists():
            shutil.rmtree(profile_dir, ignore_errors=True)
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
    # Load metadata
    metadata = load_profiles_metadata()

    # Validate profile exists
    profiles_dict = metadata.get("profiles", {})
    if profile_id not in profiles_dict:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    # Update last_used timestamp for the profile
    profiles_dict[profile_id]["last_used"] = datetime.now(timezone.utc).isoformat()

    # Update active profile
    old_profile_id = metadata.get("active_profile_id")
    metadata["active_profile_id"] = profile_id

    # Load most recent query from target profile
    try:
        profile_dir = PROFILES_DIR / profile_id
        profile_config_file = profile_dir / "profile.json"

        if profile_config_file.exists():
            with open(profile_config_file, "r", encoding="utf-8") as f:
                _ = json.load(f)  # Load to validate file, but don't need the content

            # Set active query to most recent query in the profile
            queries_dir = profile_dir / "queries"
            if queries_dir.exists():
                query_dirs = [d for d in queries_dir.iterdir() if d.is_dir()]
                if query_dirs:
                    # Find most recently used query
                    most_recent_query = None
                    most_recent_time = None

                    for query_dir in query_dirs:
                        query_file = query_dir / "query.json"
                        if query_file.exists():
                            try:
                                with open(query_file, "r", encoding="utf-8") as qf:
                                    query_data = json.load(qf)
                                last_used = query_data.get(
                                    "last_used", query_data.get("created_at", "")
                                )
                                if not most_recent_time or last_used > most_recent_time:
                                    most_recent_time = last_used
                                    most_recent_query = query_dir.name
                            except (json.JSONDecodeError, FileNotFoundError):
                                continue

                    if most_recent_query:
                        metadata["active_query_id"] = most_recent_query
                    else:
                        metadata["active_query_id"] = DEFAULT_QUERY_ID
                else:
                    metadata["active_query_id"] = DEFAULT_QUERY_ID
            else:
                metadata["active_query_id"] = DEFAULT_QUERY_ID

    except Exception as e:
        logger.warning(
            f"[Profiles] Could not determine most recent query for profile '{profile_id}': {e}"
        )
        metadata["active_query_id"] = DEFAULT_QUERY_ID

    # Save updated metadata
    if not save_profiles_metadata(metadata):
        raise OSError("Failed to update profiles registry")

    logger.info(
        f"[Profiles] Switched from '{old_profile_id}' to '{profile_id}', active query: '{metadata['active_query_id']}'"
    )


def delete_profile(profile_id: str) -> None:
    """
    Delete a profile and all its queries with cascade deletion.

    This performs cascade deletion:
    1. Deletes all queries in the profile (using allow_cascade=True)
    2. Deletes profile directory and all remaining files
    3. Removes profile from profiles.json registry

    Args:
        profile_id: Profile to delete

    Raises:
        ValueError: If trying to delete active profile or last remaining profile
        OSError: If deletion fails

    Example:
        >>> delete_profile("old-project")
        >>> # Removes profiles/old-project/ directory entirely
    """
    from data.query_manager import delete_query, list_queries_for_profile

    # Load metadata
    metadata = load_profiles_metadata()

    # Validate profile exists
    profiles_dict = metadata.get("profiles", {})
    if profile_id not in profiles_dict:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    profile_name = profiles_dict[profile_id].get("name", profile_id)

    # If deleting active profile, switch to another one first (or set to None if last profile)
    if profile_id == metadata.get("active_profile_id"):
        # Find another profile to switch to
        other_profile_id = next(
            (pid for pid in profiles_dict.keys() if pid != profile_id), None
        )
        if other_profile_id:
            logger.info(
                f"[Profiles] Auto-switching from '{profile_id}' to '{other_profile_id}' before deletion"
            )
            switch_profile(other_profile_id)
            # CRITICAL: Reload metadata after switch_profile saved it
            # Otherwise we'd overwrite the new active_profile_id when saving later
            metadata = load_profiles_metadata()
        else:
            # Last profile - set active to None
            logger.info(
                f"[Profiles] Deleting last profile '{profile_id}' - setting active_profile_id to None"
            )
            metadata["active_profile_id"] = None
            save_profiles_metadata(metadata)

    try:
        # Step 1: CASCADE DELETE all queries (best-effort - continue on errors)
        logger.info(f"[Profiles] Cascade deleting queries for profile '{profile_id}'")
        try:
            queries = list_queries_for_profile(profile_id)
            for query in queries:
                try:
                    # Use allow_cascade=True to bypass safety checks
                    delete_query(profile_id, query["id"], allow_cascade=True)
                    logger.debug(f"[Profiles] Deleted query '{query['id']}'")
                except Exception as e:
                    # Log error but continue deleting other queries
                    logger.error(
                        f"[Profiles] Error deleting query '{query['id']}': {e}"
                    )
        except Exception as e:
            logger.error(f"[Profiles] Error listing queries for deletion: {e}")
            # Continue with profile deletion even if query deletion fails

        # Step 2: Delete profile directory (removes profile.json and any remaining files)
        profile_dir = PROFILES_DIR / profile_id
        if profile_dir.exists():
            shutil.rmtree(profile_dir)
            logger.info(f"[Profiles] Deleted profile directory: {profile_dir}")

        # Step 3: Remove from profiles registry
        del metadata["profiles"][profile_id]

        # Save updated metadata
        if not save_profiles_metadata(metadata):
            raise OSError("Failed to update profiles registry")

        logger.info(f"[Profiles] Deleted profile: {profile_name} ({profile_id})")

    except Exception as e:
        logger.error(f"[Profiles] Error deleting profile '{profile_id}': {e}")
        raise OSError(f"Failed to delete profile: {e}") from e


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

    # Load current metadata
    metadata = load_profiles_metadata()
    profiles_dict = metadata.get("profiles", {})

    # Validate profile exists
    if profile_id not in profiles_dict:
        raise ValueError(f"Profile '{profile_id}' does not exist")

    current_name = profiles_dict[profile_id]["name"]

    # Check if name actually changed
    if new_name.lower() == current_name.lower():
        logger.info(
            f"[Profiles] Rename skipped - new name '{new_name}' same as current"
        )
        return

    # Check for duplicate names (case-insensitive)
    for pid, profile_data in profiles_dict.items():
        if pid != profile_id and profile_data["name"].lower() == new_name.lower():
            raise ValueError(f"Profile name '{new_name}' already exists")

    try:
        # Step 1: Update profile.json
        profile_file = get_profile_file_path(profile_id)
        if profile_file.exists():
            with open(profile_file, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            profile_data["name"] = new_name

            with open(profile_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

            logger.info(f"[Profiles] Updated profile.json for '{profile_id}'")

        # Step 2: Update profiles registry
        metadata["profiles"][profile_id]["name"] = new_name

        # Save updated metadata
        if not save_profiles_metadata(metadata):
            raise OSError("Failed to update profiles registry")

        logger.info(
            f"[Profiles] Renamed profile '{current_name}' to '{new_name}' ({profile_id})"
        )

    except Exception as e:
        logger.error(f"[Profiles] Error renaming profile '{profile_id}': {e}")
        raise OSError(f"Failed to rename profile: {e}") from e


def duplicate_profile(
    source_profile_id: str, new_name: str, description: str = ""
) -> str:
    """
    Duplicate a profile with all its settings, queries, and data files.

    Creates a complete copy of the source profile including:
    - profile.json (JIRA config, field mappings, forecast settings, etc.)
    - All queries with their query.json files
    - All query data files (jira_cache.json, project_data.json, metrics_snapshots.json, etc.)

    Args:
        source_profile_id: Profile ID to duplicate
        new_name: Name for the new profile
        description: Optional description for the new profile

    Returns:
        str: New profile ID

    Raises:
        ValueError: If source profile doesn't exist, name is invalid/duplicate, or max profiles reached
        OSError: If file operations fail

    Example:
        >>> new_id = duplicate_profile("p_abc123", "Production Copy", "Backup of production")
        >>> # Creates complete copy with new ID and timestamps
    """
    from data.query_manager import _generate_unique_query_id

    # Validate inputs
    if not new_name or not new_name.strip():
        raise ValueError("Profile name cannot be empty")

    new_name = new_name.strip()
    if len(new_name) > 100:
        raise ValueError("Profile name cannot exceed 100 characters")

    # Load current metadata
    metadata = load_profiles_metadata()

    # Validate source profile exists
    profiles_dict = metadata.get("profiles", {})
    if source_profile_id not in profiles_dict:
        raise ValueError(f"Source profile '{source_profile_id}' does not exist")

    # Check for duplicate names (case-insensitive)
    existing_names = [p["name"].lower() for p in profiles_dict.values()]
    if new_name.lower() in existing_names:
        raise ValueError(f"Profile name '{new_name}' already exists")

    # Check max profiles limit
    if len(profiles_dict) >= MAX_PROFILES:
        raise ValueError(f"Maximum {MAX_PROFILES} profiles allowed")

    # Generate unique profile ID
    new_profile_id = _generate_unique_profile_id()

    # Source and destination directories
    source_profile_dir = PROFILES_DIR / source_profile_id
    new_profile_dir = PROFILES_DIR / new_profile_id

    # Initialize variables that will be set from profile.json
    profile_data: Dict = {}
    new_query_ids: List[str] = []

    try:
        # Step 1: Copy entire profile directory tree
        shutil.copytree(source_profile_dir, new_profile_dir)
        logger.info(
            f"[Profiles] Copied directory tree from '{source_profile_id}' to '{new_profile_id}'"
        )

        # Step 2: Update profile.json with new ID, name, description, timestamps
        new_profile_config_file = new_profile_dir / "profile.json"
        if new_profile_config_file.exists():
            with open(new_profile_config_file, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            # Update profile metadata
            now = datetime.now(timezone.utc).isoformat()
            profile_data["id"] = new_profile_id
            profile_data["name"] = new_name
            profile_data["description"] = description
            profile_data["created_at"] = now
            profile_data["last_used"] = now

            # Step 3: Rename query directories and update query.json files
            queries_dir = new_profile_dir / "queries"
            if queries_dir.exists():
                for old_query_dir in list(queries_dir.iterdir()):
                    if old_query_dir.is_dir():
                        old_query_id = old_query_dir.name

                        # Generate new query ID
                        new_query_id = _generate_unique_query_id()

                        # Rename directory
                        new_query_dir = queries_dir / new_query_id
                        old_query_dir.rename(new_query_dir)

                        # Update query.json with new ID and timestamps
                        query_file = new_query_dir / "query.json"
                        if query_file.exists():
                            with open(query_file, "r", encoding="utf-8") as f:
                                query_data = json.load(f)

                            query_data["id"] = new_query_id
                            query_data["created_at"] = now
                            query_data["last_used"] = now

                            with open(query_file, "w", encoding="utf-8") as f:
                                json.dump(query_data, f, indent=2, ensure_ascii=False)

                        new_query_ids.append(new_query_id)
                        logger.debug(
                            f"[Profiles] Renamed query '{old_query_id}' to '{new_query_id}'"
                        )

            profile_data["queries"] = new_query_ids
            profile_data["active_query_id"] = (
                new_query_ids[0] if new_query_ids else None
            )

            # Save updated profile.json
            with open(new_profile_config_file, "w", encoding="utf-8") as f:
                json.dump(profile_data, f, indent=2, ensure_ascii=False)

        # Step 4: Add to profiles registry
        # Create registry entry from profile data
        registry_entry = {
            "id": new_profile_id,
            "name": new_name,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "jira_config": {},  # Summary only - full config in profile.json
            "field_mappings": {},  # Summary only - full mappings in profile.json
            "forecast_settings": profile_data.get(
                "forecast_settings",
                {
                    "pert_factor": 1.2,
                    "deadline": "",
                    "data_points_count": 20,
                },
            ),
            "project_classification": {},
            "flow_type_mappings": {},
            "queries": new_query_ids,
            "show_milestone": profile_data.get("show_milestone", False),
            "show_points": profile_data.get("show_points", False),
        }

        metadata["profiles"][new_profile_id] = registry_entry

        # Save updated metadata
        if not save_profiles_metadata(metadata):
            raise OSError("Failed to update profiles registry")

        logger.info(
            f"[Profiles] Duplicated profile '{source_profile_id}' to '{new_name}' ({new_profile_id}) with {len(new_query_ids)} queries"
        )
        return new_profile_id

    except Exception as e:
        # Cleanup on failure
        if new_profile_dir.exists():
            shutil.rmtree(new_profile_dir, ignore_errors=True)
        logger.error(f"[Profiles] Error duplicating profile: {e}")
        raise OSError(f"Failed to duplicate profile: {e}") from e


def list_profiles() -> List[Dict]:
    """
    List all available profiles.

    Returns:
        List[Dict]: Profile summaries with id, name, query_count, created_at

    Example:
        >>> profiles = list_profiles()
        >>> for p in profiles:
        ...     print(f"{p['name']} ({p['query_count']} queries)")
    """
    metadata = load_profiles_metadata()
    profiles = []

    # Iterate over profiles dictionary - key is profile_id, value is profile_data
    for profile_id, profile_data in metadata.get("profiles", {}).items():
        # Count queries in this profile
        query_count = 0
        queries_dir = PROFILES_DIR / profile_id / "queries"
        if queries_dir.exists():
            query_count = len([d for d in queries_dir.iterdir() if d.is_dir()])

        profiles.append(
            {
                "id": profile_id,
                "name": profile_data["name"],
                "description": profile_data.get("description", ""),
                "query_count": query_count,
                "created_at": profile_data.get("created_at", ""),
                "last_used": profile_data.get("last_used", ""),
                "jira_url": profile_data.get("jira_config", {}).get("base_url", ""),
                "pert_factor": profile_data.get("forecast_settings", {}).get(
                    "pert_factor", 1.2
                ),
            }
        )

    # Sort by last_used (most recent first)
    profiles.sort(key=lambda p: p["last_used"], reverse=True)
    return profiles


def get_profile(profile_id: str) -> Dict:
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


def list_queries(profile_id: str) -> List[Dict]:
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


def get_query(profile_id: str, query_id: str) -> Dict:
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
